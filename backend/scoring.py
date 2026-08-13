from typing import List, Dict, Tuple, Any
from models import TransferCard, PlayerSchema

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

def format_player(p: Dict) -> PlayerSchema:
    photo_id = str(p['photo']).replace('.jpg', '').replace('.png', '')
    club = "Club " + str(p.get('team', '?'))
    return PlayerSchema(
        id=p['id'],
        name=p['web_name'],
        position_id=p['element_type'],
        club=club,
        price=p.get('now_cost', 50) / 10.0,
        ep_next=float(p.get('ep_next', 0) or 0),
        is_new=p.get('is_new', False),
        photo_url=f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{photo_id}.png"
    )
