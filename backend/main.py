import os
import io
import json
import uuid
import time
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
from models import ProcessResponse, PrivacyStatus
from services.ocr import ocr_service
from services.analytics import get_best_transfers, format_player, calculate_budget_metrics, get_global_injuries, generate_ai_summary, generate_fpl_news
from services.ml_engine import ml_engine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for jobs and FPL cache
jobs = {}
fpl_cache = {"data": None, "timestamp": 0}

import urllib.request
def get_fpl_data():
    global fpl_cache
    if time.time() - fpl_cache["timestamp"] > 3600: # 1 hour cache
        try:
            req_data = urllib.request.Request(
                'https://fantasy.premierleague.com/api/bootstrap-static/', 
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0'}
            )
            with urllib.request.urlopen(req_data, timeout=5) as response:
                fpl_cache["data"] = json.loads(response.read())
            
            req_fix = urllib.request.Request(
                'https://fantasy.premierleague.com/api/fixtures/', 
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0'}
            )
            try:
                with urllib.request.urlopen(req_fix, timeout=5) as response:
                    fpl_cache["fixtures"] = json.loads(response.read())
            except Exception:
                try:
                    with open('fixtures_cache.json', 'r') as f:
                        fpl_cache["fixtures"] = json.load(f)
                except Exception:
                    fpl_cache["fixtures"] = []
                
            fpl_cache["timestamp"] = time.time()
        except Exception as e:
            print("ERROR FETCHING LIVE FPL DATA:", str(e))
            if not fpl_cache["data"]:
                try:
                    with open('fpl_data_cache.json', 'r') as f:
                        fpl_cache["data"] = json.load(f)
                    with open('fixtures_cache.json', 'r') as f:
                        fpl_cache["fixtures"] = json.load(f)
                    fpl_cache["timestamp"] = time.time()
                except Exception:
                    raise Exception("EXTERNAL_DATA_UNAVAILABLE")
    return fpl_cache["data"], fpl_cache.get("fixtures", [])

def process_job(request_id: str, image_bytes: bytes, transfers: int, strategy: str, bank_balance: float):
    job = jobs[request_id]
    temp_files = []
    
    try:
        start_time = time.time()
        
        # Stage 2 & 3: Validating and OCR
        job.stage = "Reading player names"
        job.message = "Identifying players from your screenshot."
        ocr_start = time.time()
        
        # ── NEW: Spatial OCR extraction ──
        # Returns candidate items with XY coordinates + detected powerups
        candidate_items, detected_powerups = ocr_service.process_image(image_bytes)
        
        job.powerups = detected_powerups
        
        # Override transfers if Wildcard or Free Hit is active
        for p in detected_powerups:
            if p['name'] in ['Wildcard', 'Free Hit'] and p['status'] == 'Active':
                transfers = 99
                break
        
        job.performance['ocr_ms'] = (time.time() - ocr_start) * 1000
        
        # Stage 4: Matching with spatial row analysis
        job.stage = "Matching players with FPL data"
        job.message = "Analyzing pitch layout to detect formation and player positions."
        
        fpl_start = time.time()
        fpl_data, fpl_fixtures = get_fpl_data()
        job.performance['fpl_data_ms'] = (time.time() - fpl_start) * 1000
        
        players = fpl_data['elements']
        teams = fpl_data['teams']
        
        # ── NEW: ML Predictive Engine Injection ──
        # Predict "True Score" for all players based on deep data and override the default FPL ep_next
        try:
            ml_predictions = ml_engine.predict(players)
            for p in players:
                player_id = p.get('id')
                if player_id in ml_predictions:
                    p['ep_next'] = str(ml_predictions[player_id])
        except Exception as e:
            print(f"ML Engine warning: {e}")
        
        analysis_start = time.time()
        
        # ── NEW: Spatial matching — positions come from WHERE players
        # appear on the pitch image, NOT from the FPL database ──
        spatial_result = ocr_service.match_players_spatial(candidate_items, players)
        
        starters = spatial_result['starters']      # 11 players with correct positions
        bench = spatial_result['bench']             # 4 bench players
        formation = spatial_result['formation']     # e.g. "3-4-3"
        row_counts = spatial_result['row_counts']   # e.g. [1, 3, 4, 3]
        
        # Store formation on the job response
        job.formation = formation
        
        job.ocr_summary = {
            "players_detected": len(candidate_items),
            "players_matched": len(starters) + len(bench),
            "average_confidence": 0.85,
            "powerups_detected": detected_powerups,
            "formation_detected": formation,
            "row_counts": row_counts,
            "needs_review": len(starters) < 11
        }
        
        # Stage 6: Reconstructing squad — positions already set by spatial analysis
        job.stage = "Checking squad constraints"
        job.message = f"Formation detected: {formation}. Verifying squad rules."
                
        # Stage 7 & 8: Recommendations
        job.stage = "Ranking transfer candidates"
        job.message = "Testing transfer options for your team."
        
        used_ids = set([p['id'] for p in starters + bench])
        sug_starters, sug_bench, t_cards = get_best_transfers(starters, bench, players, used_ids, transfers, strategy, bank_balance)
        
        # Build teams lookup for club short names (e.g. 1 → "ARS", 16 → "MUN")
        teams_map = {t['id']: t['short_name'] for t in teams}
        teams_map_code = {t['id']: t['code'] for t in teams}
        
        # Fallback: assign original squad captain/vice based on projected points
        cap_candidates = sorted(starters, key=lambda x: float(x.get('ep_next', 0) or 0), reverse=True)
        if len(cap_candidates) >= 2:
            for p in starters + bench:
                p['is_captain'] = False
                p['is_vice_captain'] = False
            cap_candidates[0]['is_captain'] = True
            cap_candidates[1]['is_vice_captain'] = True

        job.original_team = {
            "starters": [format_player(p, teams_map, teams_map_code) for p in starters],
            "bench": [format_player(p, teams_map, teams_map_code) for p in bench]
        }
        
        job.suggested_team = {
            "starters": [format_player(p, teams_map, teams_map_code, True) for p in sug_starters],
            "bench": [format_player(p, teams_map, teams_map_code, True) for p in sug_bench]
        }
        
        job.transfers = t_cards
        
        # Build Fixtures
        # Map team IDs to team objects for easy lookup
        team_map = {t['id']: t['short_name'] for t in teams}
        
        fixtures_to_show = []
        # Get next 3 gameweeks from fpl_fixtures
        if fpl_fixtures:
            current_event = next((e['id'] for e in fpl_data['events'] if e['is_next']), None)
            if current_event:
                next_fixtures = [f for f in fpl_fixtures if f.get('event') and current_event <= f['event'] <= current_event + 2]
                
                # For suggested players, show their next fixture
                for p in sug_starters:
                    if p.get('is_new'):
                        team_id = p['team']
                        p_fixtures = []
                        for fix in next_fixtures:
                            if fix['team_h'] == team_id:
                                p_fixtures.append(f"vs {team_map.get(fix['team_a'], '?')} (H)")
                            elif fix['team_a'] == team_id:
                                p_fixtures.append(f"vs {team_map.get(fix['team_h'], '?')} (A)")
                        
                        fixtures_to_show.append({
                            "player_name": p['web_name'],
                            "upcoming": p_fixtures[:3]
                        })
                        
        job.fixtures = fixtures_to_show
        
        # ── Build Gameweek Fixtures board (live scores + upcoming) ──
        gameweek_fixtures = []
        if fpl_fixtures:
            # Find the current or next gameweek
            current_event = next((e for e in fpl_data['events'] if e.get('is_current')), None)
            next_event = next((e for e in fpl_data['events'] if e.get('is_next')), None)
            
            # Prefer current (for live scores), fall back to next
            target_event = current_event or next_event
            
            if target_event:
                gw_id = target_event['id']
                gw_fixtures = [f for f in fpl_fixtures if f.get('event') == gw_id]
                team_full = {t['id']: t for t in teams}
                
                for fix in gw_fixtures:
                    home_team = team_full.get(fix['team_h'], {})
                    away_team = team_full.get(fix['team_a'], {})
                    
                    home_name = home_team.get('name', '?')
                    away_name = away_team.get('name', '?')
                    
                    home_logo = f"https://resources.premierleague.com/premierleague/badges/t{home_team.get('code', '')}.png"
                    away_logo = f"https://resources.premierleague.com/premierleague/badges/t{away_team.get('code', '')}.png"
                    
                    # Determine match status
                    started = fix.get('started', False)
                    finished = fix.get('finished', False) or fix.get('finished_provisional', False)
                    
                    if finished:
                        status = 'FT'
                    elif started:
                        status = 'LIVE'
                    else:
                        status = 'upcoming'
                    
                    gameweek_fixtures.append({
                        'home_team': home_name,
                        'away_team': away_name,
                        'home_logo': home_logo,
                        'away_logo': away_logo,
                        'home_score': fix.get('team_h_score'),
                        'away_score': fix.get('team_a_score'),
                        'kickoff_time': fix.get('kickoff_time', ''),
                        'status': status,
                    })
                
                # Sort: LIVE first, then upcoming (by kickoff), then FT
                status_order = {'LIVE': 0, 'upcoming': 1, 'FT': 2}
                gameweek_fixtures.sort(key=lambda x: (status_order.get(x['status'], 1), x['kickoff_time']))
        
        job.gameweek_fixtures = gameweek_fixtures
        
        # Calculate new dashboard metrics
        job.budget = calculate_budget_metrics(starters + bench, bank_balance)
        job.global_injuries = get_global_injuries(fpl_data)
        job.ai_summary = generate_ai_summary(t_cards, job.budget, job.global_injuries, starters + bench)
        job.news = generate_fpl_news(fpl_data)
        
        age = time.time() - fpl_cache["timestamp"]
        job.data_freshness = {
            "age_seconds": int(age),
            "is_stale": age > 3600,
            "source": "official"
        }
        
        if t_cards:
            job.message = f"Make {len(t_cards)} transfer(s)."
        else:
            job.message = "Hold this week."
            
        job.performance['analysis_ms'] = (time.time() - analysis_start) * 1000
        job.performance['total_ms'] = (time.time() - start_time) * 1000
        
        # Stage 9: Deleting
        job.stage = "Deleting temporary data"
        job.privacy = PrivacyStatus(input_persisted=False, temporary_files_deleted=True, deletion_status="deleted")
        
        # Stage 10
        job.status = "complete"
        job.completed_at = datetime.utcnow().isoformat()
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.privacy = PrivacyStatus(input_persisted=False, temporary_files_deleted=True, deletion_status="cleanup_failed")
    finally:
        # Guarantee cleanup of memory
        del image_bytes
        if 'img' in locals() and img is not None:
            del img

@app.post("/api/process-team", response_model=ProcessResponse)
async def upload_team(background_tasks: BackgroundTasks, squadImage: UploadFile = File(...), transfers: int = Form(1), strategy: str = Form("next_gameweek"), bank_balance: float = Form(0.0)):
    request_id = str(uuid.uuid4())
    contents = await squadImage.read()
    
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="IMAGE_TOO_LARGE")
        
    job = ProcessResponse(
        request_id=request_id,
        status="accepted",
        created_at=datetime.utcnow().isoformat(),
        input_metadata={"free_transfers": transfers, "image_persisted": False, "bank_balance": bank_balance},
        strategy=strategy,
        stage="Screenshot received",
        message="Your screenshot was received securely."
    )
    jobs[request_id] = job
    
    # Process job in background
    background_tasks.add_task(process_job, request_id, contents, transfers, strategy, bank_balance)
    
    return job

@app.get("/api/process-team/{request_id}", response_model=ProcessResponse)
async def get_team_status(request_id: str):
    if request_id not in jobs:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return jobs[request_id]

@app.get("/api/metadata")
async def get_metadata():
    try:
        fpl_data, fpl_fixtures = get_fpl_data()
        current_event = next((e for e in fpl_data['events'] if e.get('is_current')), None)
        next_event = next((e for e in fpl_data['events'] if e.get('is_next')), None)
        target_event = current_event or next_event
        
        fdr_table = []
        if fpl_fixtures and target_event:
            start_gw = target_event['id']
            teams = fpl_data['teams']
            team_dict = {t['id']: t for t in teams}
            
            for t in teams:
                team_id = t['id']
                team_fixtures = []
                
                # Get next 5 matches
                upcoming = [f for f in fpl_fixtures if f.get('event') and f['event'] >= start_gw and (f['team_h'] == team_id or f['team_a'] == team_id)]
                upcoming.sort(key=lambda x: x['event'])
                
                for f in upcoming[:5]:
                    is_home = (f['team_h'] == team_id)
                    opp_id = f['team_a'] if is_home else f['team_h']
                    opp_name = team_dict.get(opp_id, {}).get('short_name', 'UNK')
                    diff = f['team_h_difficulty'] if is_home else f['team_a_difficulty']
                    team_fixtures.append({
                        "opponent": opp_name,
                        "is_home": is_home,
                        "difficulty": diff,
                        "event": f['event']
                    })
                
                fdr_table.append({
                    "id": team_id,
                    "name": t['name'],
                    "short_name": t['short_name'],
                    "code": t['code'],
                    "logo": f"https://resources.premierleague.com/premierleague/badges/t{t['code']}.png",
                    "fixtures": team_fixtures
                })
                
            metadata = {}
            metadata["fdr_table"] = sorted(fdr_table, key=lambda x: sum(f['difficulty'] for f in x['fixtures']))
            
            # --- NEW: Team Attacking Stats ---
            team_stats = []
            for t in teams:
                atk_score = (t.get('strength_attack_home', 1000) + t.get('strength_attack_away', 1000)) / 2
                def_score = (t.get('strength_defence_home', 1000) + t.get('strength_defence_away', 1000)) / 2
                team_stats.append({
                    "name": t['name'],
                    "short_name": t['short_name'],
                    "attack_strength": atk_score,
                    "defense_strength": def_score,
                    # Normalize for UI progress bar (max is usually ~1350)
                    "attack_rating": round(min(100, max(0, (atk_score - 1000) / 350 * 100))),
                    "defense_rating": round(min(100, max(0, (def_score - 1000) / 350 * 100)))
                })
            # Sort by attacking rating desc
            team_stats.sort(key=lambda x: x['attack_rating'], reverse=True)
            metadata["team_stats"] = team_stats[:10]  # Send top 10 attacking teams
            
        if next_event:
            return {
                "gameweek": next_event['name'],
                "deadline": next_event['deadline_time'],
                "fdr_table": fdr_table,
                "team_stats": team_stats[:10]
            }
        return {"gameweek": "Unknown", "deadline": "", "fdr_table": fdr_table, "team_stats": team_stats[:10] if 'team_stats' in locals() else []}
    except Exception as e:
        return {"gameweek": "Unknown", "deadline": "", "fdr_table": [], "error": str(e)}

# ── NEW UNRESTRICTED ML & DATA APIs ──

@app.get("/api/v2/players")
async def get_all_players():
    fpl_data, _ = get_fpl_data()
    return fpl_data.get('elements', [])

@app.get("/api/v2/players/{player_id}")
async def get_player_details(player_id: int):
    fpl_data, _ = get_fpl_data()
    player = next((p for p in fpl_data.get('elements', []) if p['id'] == player_id), None)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@app.get("/api/v2/teams")
async def get_all_teams():
    fpl_data, _ = get_fpl_data()
    return fpl_data.get('teams', [])

@app.get("/api/v2/teams/{team_id}")
async def get_team_details(team_id: int):
    fpl_data, _ = get_fpl_data()
    team = next((t for t in fpl_data.get('teams', []) if t['id'] == team_id), None)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@app.get("/api/v2/fixtures")
async def get_all_fixtures():
    _, fpl_fixtures = get_fpl_data()
    return fpl_fixtures

@app.get("/api/v2/fixtures/live")
async def get_live_fixtures():
    _, fpl_fixtures = get_fpl_data()
    return [f for f in fpl_fixtures if f.get('started') and not f.get('finished')]

@app.get("/api/v2/market/price-changes")
async def get_price_changes():
    fpl_data, _ = get_fpl_data()
    players = fpl_data.get('elements', [])
    risers = [p for p in players if p.get('cost_change_event', 0) > 0]
    fallers = [p for p in players if p.get('cost_change_event', 0) < 0]
    return {"risers": risers, "fallers": fallers}

@app.get("/api/v2/market/transfers-in")
async def get_transfers_in():
    fpl_data, _ = get_fpl_data()
    players = sorted(fpl_data.get('elements', []), key=lambda x: x.get('transfers_in_event', 0), reverse=True)
    return players[:20]

@app.get("/api/v2/market/transfers-out")
async def get_transfers_out():
    fpl_data, _ = get_fpl_data()
    players = sorted(fpl_data.get('elements', []), key=lambda x: x.get('transfers_out_event', 0), reverse=True)
    return players[:20]

@app.get("/api/v2/injuries")
async def get_injuries():
    fpl_data, _ = get_fpl_data()
    return get_global_injuries(fpl_data)

@app.get("/api/v2/dream-team")
async def get_dream_team():
    fpl_data, _ = get_fpl_data()
    players = sorted(fpl_data.get('elements', []), key=lambda x: float(x.get('event_points', 0)), reverse=True)
    return players[:11]

@app.get("/api/v2/stats/xg-xa")
async def get_xg_xa_stats():
    fpl_data, _ = get_fpl_data()
    players = fpl_data.get('elements', [])
    stats = []
    for p in players:
        stats.append({
            "id": p['id'],
            "name": p['web_name'],
            "xG": p.get('expected_goals', 0),
            "xA": p.get('expected_assists', 0),
            "xGI": p.get('expected_goal_involvements', 0)
        })
    return sorted(stats, key=lambda x: float(x['xGI'] or 0), reverse=True)[:50]

@app.get("/api/v2/ml/projections")
async def get_ml_projections():
    fpl_data, _ = get_fpl_data()
    players = fpl_data.get('elements', [])
    predictions = ml_engine.predict(players)
    results = []
    for p in players:
        pid = p['id']
        results.append({
            "id": pid,
            "name": p['web_name'],
            "ml_projected_points": predictions.get(pid, 0)
        })
    return sorted(results, key=lambda x: x['ml_projected_points'], reverse=True)[:100]

@app.get("/api/v2/system/health")
async def system_health():
    return {
        "status": "healthy",
        "cache_age_seconds": time.time() - fpl_cache["timestamp"],
        "ml_engine_trained": ml_engine.is_trained
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3001, reload=True)
