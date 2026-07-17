import json
import os
import sys
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, AGENT_MODEL, MAX_TOKENS, AGENT_TEMPERATURE


class BaseAgent:
    name: str = "base"
    role: str = "base"
    system_prompt: str = "You are a geopolitical analyst."

    def __init__(self, kb=None):
        self.kb = kb
        self.client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_BASE_URL,
        )

    def call_qwen(self, messages: list[dict], model: str = None, max_tokens: int = None, enable_search: bool = False) -> str:
        m = model or AGENT_MODEL
        mt = max_tokens or MAX_TOKENS
        full_messages = [{"role": "system", "content": self.system_prompt}] + messages
        response = self.client.chat.completions.create(
            model=m,
            messages=full_messages,
            temperature=AGENT_TEMPERATURE,
            max_tokens=mt,
            extra_body={"enable_search": enable_search} if enable_search else {},
        )
        return response.choices[0].message.content or ""

    def _parse_json_response(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            inner = lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:]
            text = "\n".join(inner).strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end   = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    parsed = json.loads(text[start:end])
                except json.JSONDecodeError:
                    return {"raw_text": text}
            else:
                return {"raw_text": text}
        return {k: (v if v is not None else "") for k, v in parsed.items()}

    def analyze(self, sub_question: str, kb_context: dict = None, round_num: int = 1, enable_search: bool = False, horizon: str = "long") -> dict:
        context_str = ""
        if kb_context:
            context_str = f"\n\nKnowledge base context (role-filtered):\n{json.dumps(kb_context, indent=2)}"

        horizon_labels = {
            "short":  "Focus on the next 0–30 days. What immediate actions, escalations, or responses are likely?",
            "medium": "Focus on the next 1–6 months. How will the situation evolve in the near-to-medium term?",
            "long":   "For uncertain or future events, extrapolate from your expertise and the historical base rates above.",
        }
        horizon_text = horizon_labels.get(horizon, horizon_labels["long"])

        prompt = (
            f"{context_str}\n\n"
            f"Question: {sub_question}\n\n"
            "Respond with ONLY a JSON object. All fields required — never use null.\n"
            f"{horizon_text}\n"
            "{\n"
            '  "prediction": "your expert prediction of the conflict outcome",\n'
            '  "confidence": 0.0-1.0,\n'
            '  "reasoning": "detailed analytical reasoning citing specific evidence or historical precedents",\n'
            '  "key_factors": ["factor 1", "factor 2", "factor 3", "factor 4"],\n'
            '  "timeline": "estimated conflict duration and resolution path",\n'
            '  "position_at_round": ' + str(round_num) + "\n"
            "}"
        )
        raw = self.call_qwen([{"role": "user", "content": prompt}], enable_search=enable_search)
        result = self._parse_json_response(raw)
        result.setdefault("agent", self.name)
        result.setdefault("role", self.role)
        result.setdefault("position_at_round", round_num)
        return result
