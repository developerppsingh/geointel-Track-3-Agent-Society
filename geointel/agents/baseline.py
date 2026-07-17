import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.base import BaseAgent


class BaselineAgent(BaseAgent):
    name = "BaselineAgent"
    role = "baseline"
    system_prompt = "You are a general geopolitical analyst. Analyze conflicts and provide predictions based on your general knowledge."

    def analyze(self, conflict_query: str, kb_context: dict = None, round_num: int = 1, enable_search: bool = False, horizon: str = "long") -> dict:
        horizon_labels = {
            "short":  "Focus on the next 0–30 days. What immediate actions, escalations, or responses are likely?",
            "medium": "Focus on the next 1–6 months. How will the situation evolve in the near-to-medium term?",
            "long":   "Provide a general long-term prediction.",
        }
        horizon_text = horizon_labels.get(horizon, horizon_labels["long"])

        prompt = (
            f"Analyze this conflict scenario and provide a prediction:\n\n{conflict_query}\n\n"
            f"{horizon_text}\n\n"
            "Respond with a JSON object:\n"
            "{\n"
            '  "prediction": "your prediction of the conflict outcome",\n'
            '  "confidence": 0.0-1.0,\n'
            '  "reasoning": "your reasoning",\n'
            '  "key_factors": ["factor 1", "factor 2", "factor 3"],\n'
            '  "timeline": "estimated duration or timeline"\n'
            "}"
        )
        raw = self.call_qwen([{"role": "user", "content": prompt}], enable_search=enable_search)
        result = self._parse_json_response(raw)
        result.setdefault("agent", self.name)
        result.setdefault("role", self.role)
        return result
