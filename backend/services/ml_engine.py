import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from typing import List, Dict

class FPLEngine:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.is_trained = False
        
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = ['now_cost', 'selected_by_percent', 'form', 'points_per_game', 'ict_index', 'minutes']
        # Convert strings to floats
        for f in features:
            if f in df.columns:
                df[f] = pd.to_numeric(df[f], errors='coerce').fillna(0.0)
        return df[features]
        
    def train(self, players: List[Dict]):
        df = pd.DataFrame(players)
        
        # We need a target variable. In a real-world scenario, this would be actual points from the next GW.
        # Here we create a proprietary "True Value" metric based on underlying stats to train the ML model.
        # True Value = combination of Form, ICT Index (Influence, Creativity, Threat), and historical PPG.
        df['form_num'] = pd.to_numeric(df.get('form', 0), errors='coerce').fillna(0.0)
        df['ict_num'] = pd.to_numeric(df.get('ict_index', 0), errors='coerce').fillna(0.0)
        df['ppg_num'] = pd.to_numeric(df.get('points_per_game', 0), errors='coerce').fillna(0.0)
        
        target = (df['form_num'] * 0.6) + (df['ict_num'] / 10.0 * 0.3) + (df['ppg_num'] * 0.1)
        
        X = self._extract_features(df)
        y = target
        
        self.model.fit(X, y)
        self.is_trained = True
        
    def predict(self, players: List[Dict]) -> Dict[int, float]:
        if not self.is_trained:
            self.train(players)
            
        df = pd.DataFrame(players)
        X = self._extract_features(df)
        predictions = self.model.predict(X)
        
        results = {}
        for idx, p in enumerate(players):
            player_id = p.get('id')
            if player_id:
                # Add a small boost for the official ep_next to ground the predictions in reality
                ep_next = float(p.get('ep_next', 0) or 0)
                ml_score = predictions[idx]
                
                # Final hybrid ML score
                final_score = (ml_score * 0.7) + (ep_next * 0.3)
                results[player_id] = round(final_score, 2)
                
        return results

# Singleton instance
ml_engine = FPLEngine()
