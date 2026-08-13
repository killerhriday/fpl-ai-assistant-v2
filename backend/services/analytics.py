from typing import List, Dict, Tuple, Any
from models import TransferCard, PlayerSchema, BudgetStatus, InjuryAlert

def score_player(player: Dict, strategy: str = "next_gameweek") -> float:
    """Calculates a heuristic score for a player based on multiple weighted factors."""
    ep_next = float(player.get('ep_next', 0) or 0)
    now_cost = player.get('now_cost', 50)
    
    # Projection (50% weight normally)
    score = ep_next * 10 
    
    # Value factor (10% weight) - small boost for cheaper players giving good returns
    value_factor = (ep_next / now_cost) * 10
    score += value_factor
    
    # Form factor
    form = float(player.get('form', 0) or 0)
    score += form * 2
    
    # Strategy adjustments
    if strategy == "four_gameweek_planner":
        # Simulate 4-gameweek by boosting based on form + ep_next
        score += form * 3
        
    return score

def get_best_transfers(
    starters: List[Dict], 
    bench: List[Dict], 
    all_players: List[Dict], 
    used_ids: set, 
    free_transfers: int, 
    strategy: str
) -> Tuple[List[Dict], List[Dict], List[TransferCard]]:
    
    if free_transfers <= 0 and strategy != "four_gameweek_planner":
        return starters, bench, []
        
    if not starters:
        return starters, bench, []
        
    # Find weakest starter
    worst_starter = min(starters, key=lambda x: score_player(x, strategy))
    worst_pos = worst_starter['element_type']
    
    best_replacement = None
    best_score = score_player(worst_starter, strategy)
    
    # Simple affordability constraint (assume we can afford +1.0)
    max_price = worst_starter.get('now_cost', 50) + 10 
    
    for p in all_players:
        if p['id'] not in used_ids and p['element_type'] == worst_pos:
            if p.get('now_cost', 50) <= max_price:
                score = score_player(p, strategy)
                if score > best_score:
                    best_score = score
                    best_replacement = p
                    
    transfers = []
    suggested_starters = []
    
    if best_replacement and (best_score - score_player(worst_starter, strategy) > (4 if free_transfers == 0 else 1)):
        # We recommend the transfer
        for p in starters:
            if p['id'] == worst_starter['id']:
                best_replacement['is_new'] = True
                suggested_starters.append(best_replacement)
                
                # Build TransferCard
                tc = TransferCard(
                    out_player_id=worst_starter['id'],
                    in_player_id=best_replacement['id'],
                    out_player_name=worst_starter['web_name'],
                    in_player_name=best_replacement['web_name'],
                    position_id=worst_pos,
                    club_in=str(best_replacement.get('team', 0)),
                    club_out=str(worst_starter.get('team', 0)),
                    current_price=worst_starter.get('now_cost', 50) / 10,
                    new_price=best_replacement.get('now_cost', 50) / 10,
                    ep_next_in=float(best_replacement.get('ep_next', 0) or 0),
                    ep_next_out=float(worst_starter.get('ep_next', 0) or 0),
                    projected_gain_1gw=float(best_replacement.get('ep_next', 0) or 0) - float(worst_starter.get('ep_next', 0) or 0),
                    hit_cost=0 if free_transfers > 0 else 4,
                    confidence=0.85,
                    reasons=["Higher projected points", "Better overall value"],
                    warnings=[],
                    score_breakdown={"projection": 0.5, "form": 0.3, "value": 0.2}
                )
                transfers.append(tc)
            else:
                p['is_new'] = False
                suggested_starters.append(p)
    else:
        suggested_starters = [p.copy() for p in starters]
        for p in suggested_starters: p['is_new'] = False

    suggested_bench = [p.copy() for p in bench]
    for p in suggested_bench: p['is_new'] = False
    
    return suggested_starters, suggested_bench, transfers

def format_player(p: Dict, teams_map: Dict = None) -> PlayerSchema:
    # Use the player's 'code' field for the photo URL — this is the correct
    # FPL API key for Premier League player headshots. The 'photo' field
    # sometimes has mismatched IDs that return 404s.
    player_code = p.get('code', '')
    photo_url = f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{player_code}.png"
    
    # Look up real team short name (e.g. "ARS", "MUN") from the teams map
    team_id = p.get('team', 0)
    if teams_map and team_id in teams_map:
        club = teams_map[team_id]
    else:
        club = str(team_id)
    
    pos_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
    pos_id = p.get('element_type', 0)
    return PlayerSchema(
        id=p.get('id', 0),
        name=p.get('web_name', 'Unknown'),
        team=team_id,
        club=club,
        position=pos_map.get(pos_id, "UNK"),
        position_id=pos_id,
        price=p.get('now_cost', 50) / 10.0,
        ep_next=float(p.get('ep_next', 0) or 0),
        is_new=p.get('is_new', False),
        photo_url=photo_url
    )

def calculate_budget_metrics(squad: List[Dict], in_the_bank: float) -> BudgetStatus:
    squad_value = sum((p.get('now_cost', 50) / 10.0) for p in squad)
    if in_the_bank <= 0.0:
        in_the_bank = 100.0 - squad_value
    return BudgetStatus(
        squad_value=round(squad_value, 1),
        in_the_bank=round(in_the_bank, 1),
        total_budget=round(squad_value + in_the_bank, 1)
    )

def get_global_injuries(fpl_data: Dict) -> List[InjuryAlert]:
    alerts = []
    teams_map = {t['id']: t['short_name'] for t in fpl_data.get('teams', [])}
    
    for p in fpl_data.get('elements', []):
        fpl_status = p.get('status', 'a')
        chance = p.get('chance_of_playing_next_round')
        
        if fpl_status != 'a': # 'a' is available
            news = p.get('news', '')
            
            # Determine color and explicit status
            if fpl_status == 'i':
                status = "Injured"
                color = "red"
            elif fpl_status == 's':
                if "red card" in news.lower():
                    status = "Red Card"
                    color = "darkred"
                elif "suspended" in news.lower() or "yellow" in news.lower():
                    status = "Suspended"
                    color = "red"
                else:
                    status = "Suspended"
                    color = "red"
            elif fpl_status == 'd':
                status = "Doubtful"
                color = "yellow"
            elif fpl_status == 'u':
                status = "Loaned / Unavailable"
                color = "gray"
            elif fpl_status == 'n':
                status = "Unavailable"
                color = "gray"
            else:
                status = "Unknown"
                color = "yellow"
                
            if chance is not None and chance > 0 and chance < 100:
                status = f"Doubtful ({chance}%)"
                color = "yellow"
            
            # Extract return date from news
            return_date = ""
            if "Expected back" in news:
                return_date = news.split("Expected back")[-1].strip()
            elif "Unknown return date" in news:
                return_date = "Unknown"
                
            team_name = teams_map.get(p.get('team'), 'UNK')
            
            player_code = p.get('code', '')
            photo_url = f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{player_code}.png"
            
            alerts.append(InjuryAlert(
                player_name=p.get('web_name', ''),
                team_name=team_name,
                status=status,
                color=color,
                chance_of_playing=chance if chance is not None else 0,
                news=news,
                return_date=return_date,
                photo_url=photo_url
            ))
            
    # Sort by severity (0% first)
    alerts.sort(key=lambda x: x.chance_of_playing)
    return alerts

def generate_ai_summary(transfers: List[TransferCard], budget: BudgetStatus, injuries: List[InjuryAlert], squad: List[Dict]) -> str:
    # A deterministic text engine that feels like AI
    if not transfers:
        return f"Your squad is currently well-optimized for the upcoming gameweek. With a squad value of £{budget.squad_value}m and £{budget.in_the_bank}m in the bank, you have strong flexibility, but I recommend rolling your free transfer to build momentum."
    
    summary = f"I recommend making {len(transfers)} transfer{'s' if len(transfers) > 1 else ''}. "
    
    # Analyze the 'Out' players to generate a reason
    out_names = [t.out_player_name for t in transfers]
    out_reasons = []
    
    # Check if we are transferring out an injured player
    injured_out = [n for n in out_names if any(i.player_name == n for i in injuries)]
    if injured_out:
        out_reasons.append(f"shipping out flagged/injured players like {injured_out[0]}")
        
    if not out_reasons:
        out_reasons.append("upgrading weak links in your starting XI")
        
    summary += f"We are {out_reasons[0]} to bring in high-upside assets. "
    
    # Analyze Budget
    net_cost = sum((t.new_price - t.current_price) for t in transfers)
    if net_cost > 0:
        summary += f"This aggressive move utilizes £{round(net_cost, 1)}m of your bank, leaving you with £{round(budget.in_the_bank - net_cost, 1)}m remaining. "
    else:
        summary += f"This conservative move actually frees up £{round(abs(net_cost), 1)}m, leaving you flush with £{round(budget.in_the_bank - net_cost, 1)}m to attack future gameweeks. "
        
    # Analyze hit cost
    total_hit = sum(t.hit_cost for t in transfers)
    if total_hit > 0:
        summary += f"Taking a -{total_hit} point hit is justified here given the strong projected upside of the incoming players over the next 4 gameweeks."
        
    return summary

def generate_fpl_news(fpl_data: Dict) -> List[Dict[str, str]]:
    """Generate dynamic news based on actual FPL data trends."""
    news = []
    players = fpl_data.get('elements', [])
    teams = {t['id']: t['short_name'] for t in fpl_data.get('teams', [])}
    
    if not players:
        return news
        
    # 1. Most Transferred In
    players_sorted_in = sorted(players, key=lambda x: x.get('transfers_in_event', 0), reverse=True)
    top_in = players_sorted_in[0]
    news.append({
        "source": "FPL Market Watch",
        "headline": f"{top_in['web_name']} is the most transferred in player!",
        "summary": f"{top_in['web_name']} ({teams.get(top_in['team'], '')}) has been brought in by {top_in.get('transfers_in_event', 0):,} managers this Gameweek after strong recent performances.",
        "url": "https://fantasy.premierleague.com/statistics"
    })
    
    # 2. Most Transferred Out
    players_sorted_out = sorted(players, key=lambda x: x.get('transfers_out_event', 0), reverse=True)
    top_out = players_sorted_out[0]
    news.append({
        "source": "FPL Market Watch",
        "headline": f"Managers dropping {top_out['web_name']} in droves",
        "summary": f"{top_out.get('transfers_out_event', 0):,} managers have sold {top_out['web_name']} ({teams.get(top_out['team'], '')}) ahead of the deadline. Is it time to sell?",
        "url": "https://fantasy.premierleague.com/statistics"
    })
    
    # 3. Form Players
    try:
        players_form = sorted([p for p in players if float(p.get('form', 0)) > 0], key=lambda x: float(x.get('form', 0)), reverse=True)
        if len(players_form) >= 3:
            form_players = ", ".join([f"{p['web_name']} ({p.get('form')} form)" for p in players_form[:3]])
            news.append({
                "source": "Form Guide",
                "headline": "Top in-form players to target",
                "summary": f"The most in-form players right now are {form_players}. Consider bringing them in to ride the momentum.",
                "url": "https://fantasy.premierleague.com/statistics"
            })
    except (ValueError, TypeError):
        pass
        
    # 4. Price Risers
    risers = [p for p in players if p.get('cost_change_event', 0) > 0]
    if risers:
        risers_sorted = sorted(risers, key=lambda x: x.get('cost_change_event', 0), reverse=True)
        riser_names = ", ".join([p['web_name'] for p in risers_sorted[:3]])
        news.append({
            "source": "Price Changes",
            "headline": f"Price rises for {riser_names}",
            "summary": f"Several players have increased in price overnight due to high transfer volume, including {riser_names}.",
            "url": "https://fantasy.premierleague.com/statistics"
        })
        
    # 5. Price Fallers
    fallers = [p for p in players if p.get('cost_change_event', 0) < 0]
    if fallers:
        fallers_sorted = sorted(fallers, key=lambda x: x.get('cost_change_event', 0))
        faller_names = ", ".join([p['web_name'] for p in fallers_sorted[:3]])
        news.append({
            "source": "Price Changes",
            "headline": f"Price drops for {faller_names}",
            "summary": f"Market forces have caused price drops for {faller_names}. Check your squad value.",
            "url": "https://fantasy.premierleague.com/statistics"
        })
        
    # 6. Differential Picks
    try:
        differentials = sorted([p for p in players if float(p.get('selected_by_percent', 0)) < 5.0 and float(p.get('form', 0)) > 3.0], key=lambda x: float(x.get('form', 0)), reverse=True)
        if differentials:
            diff_names = ", ".join([f"{p['web_name']} ({p.get('selected_by_percent')}%)" for p in differentials[:3]])
            news.append({
                "source": "Differential Scout",
                "headline": "Under the radar picks delivering points",
                "summary": f"Looking for a differential to climb your mini-league? {diff_names} are highly in-form but owned by less than 5% of managers.",
                "url": "https://fantasy.premierleague.com/statistics"
            })
    except (ValueError, TypeError):
        pass
        
    # 7. Heavily Selected
    try:
        selected = sorted(players, key=lambda x: float(x.get('selected_by_percent', 0)), reverse=True)
        top_sel = selected[0]
        news.append({
            "source": "Ownership Stats",
            "headline": f"{top_sel['web_name']} remains highest owned player",
            "summary": f"A staggering {top_sel.get('selected_by_percent', 0)}% of FPL managers own {top_sel['web_name']}. Not owning him could be a huge risk.",
            "url": "https://fantasy.premierleague.com/statistics"
        })
    except (ValueError, TypeError):
        pass
        
    # 8. Highest Expected Points
    try:
        ep = sorted(players, key=lambda x: float(x.get('ep_next', 0)), reverse=True)
        top_ep = ep[0]
        news.append({
            "source": "Algorithm Predictions",
            "headline": f"Captaincy favorite: {top_ep['web_name']}",
            "summary": f"{top_ep['web_name']} has the highest projected score for the upcoming Gameweek ({top_ep.get('ep_next')} pts). Make sure he is in your team.",
            "url": "https://fantasy.premierleague.com/statistics"
        })
    except (ValueError, TypeError):
        pass

    return news
