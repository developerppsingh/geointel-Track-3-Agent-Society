import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.base import BaseAgent
from config import FAST_MODEL


class SynthesisAgent(BaseAgent):
    name = "SynthesisAgent"
    role = "synthesis"
    system_prompt = """You are a senior intelligence analyst who synthesizes multi-source assessments into actionable forecasts. You moderate debates between specialist analysts, identify genuine disagreements, and produce probability-weighted consensus predictions.

Your output must always be structured JSON. Be precise about probabilities and timelines. When analysts disagree, explicitly state what is in dispute and who makes the stronger evidentiary case."""

    def decompose_query(self, conflict_query: str, enable_search: bool = False) -> dict:
        """Criterion 1: Task Decomposition — split query into 3 role-specific sub-questions."""
        prompt = (
            f'Decompose this conflict scenario into three specialist sub-questions:\n\n"{conflict_query}"\n\n'
            "Return a JSON object with exactly these keys. Customize each question for the specific parties and context:\n"
            "{\n"
            '  "historian_question": "What historical precedents, civilizational patterns, and base rates apply? Which analogous conflicts are most instructive for likely outcomes?",\n'
            '  "strategist_question": "Assess the military balance: force ratios, terrain, A2AD capabilities, alliance structures, nuclear thresholds, and logistical sustainability across 6-month and 18-month horizons.",\n'
            '  "economist_question": "Can each party sustain a prolonged conflict economically? Analyze debt levels, FIRE ratio, manufacturing capacity, energy independence, sanctions resilience, and war finance mode.",\n'
            '  "conflict_parties": ["party1", "party2"],\n'
            '  "conflict_type": "direct war / proxy war / hybrid / sanctions / naval"\n'
            "}\n\n"
            "Make each sub-question specific and rich — not just the template above."
        )
        raw = self.call_qwen([{"role": "user", "content": prompt}], model=FAST_MODEL, enable_search=enable_search)
        return self._parse_json_response(raw)

    def detect_disagreements(self, assessments: dict, enable_search: bool = False) -> list:
        """Criterion 2: Disagreement Detection — identify genuine substantive disputes."""
        agents = list(assessments.keys())
        if len(agents) < 2:
            return []

        summaries = {
            a: {
                "prediction": assessments[a].get("prediction", ""),
                "confidence": assessments[a].get("confidence", 0.5),
                "key_factors": assessments[a].get("key_factors", [])[:3],
            }
            for a in agents
        }

        prompt = (
            "These specialist analysts produced independent assessments of the same conflict scenario.\n\n"
            f"Assessments:\n{json.dumps(summaries, indent=2)}\n\n"
            "Identify genuine substantive disagreements. A disagreement exists when:\n"
            "- Two agents predict different outcomes, OR\n"
            "- Confidence scores differ by more than 0.15, OR\n"
            "- Agents cite directly contradictory key factors\n\n"
            "Return a JSON array (can be empty []):\n"
            "[\n"
            "  {\n"
            '    "agents": ["AgentName1", "AgentName2"],\n'
            '    "topic": "brief topic label",\n'
            '    "agent1_position": "what AgentName1 claims",\n'
            '    "agent2_position": "what AgentName2 claims",\n'
            '    "stakes": "why this disagreement matters for the forecast"\n'
            "  }\n"
            "]\n\n"
            "Return [] if no genuine disagreements exist. Do not invent disagreements."
        )
        raw = self.call_qwen([{"role": "user", "content": prompt}], model=FAST_MODEL, enable_search=enable_search)
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:])
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            if isinstance(result, dict) and "disagreements" in result:
                return result["disagreements"]
        except json.JSONDecodeError:
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
        return []

    def build_cross_examination_prompt(self, agent_name: str, disagreements: list, all_assessments: dict) -> str:
        """Build targeted cross-examination prompt for a specific agent."""
        relevant = [d for d in disagreements if agent_name in d.get("agents", [])]
        if not relevant:
            return ""

        lines = [f"You are {agent_name}. Address the following specific disagreements raised about your analysis:\n"]
        for d in relevant:
            other_agent = next((a for a in d["agents"] if a != agent_name), "")
            other_position = (
                d.get("agent2_position") if d["agents"][0] == agent_name else d.get("agent1_position")
            )
            lines.append(
                f"DISAGREEMENT: {d['topic']}\n"
                f"{other_agent} argues: {other_position}\n"
                f"Stakes: {d.get('stakes', '')}\n"
                f"Defend your position with specific evidence from the knowledge base or historical precedents, or explicitly revise it.\n"
            )

        lines.append(
            "\nRespond with ONLY JSON:\n"
            "{\n"
            '  "revised_prediction": "updated prediction (or unchanged if held firm)",\n'
            '  "confidence": 0.0-1.0,\n'
            '  "position_changed": true or false,\n'
            '  "change_reason": "why you revised, or why you held firm with what evidence",\n'
            '  "key_factors": ["updated factor list"],\n'
            '  "rebuttal": "your direct response to the specific challenge raised"\n'
            "}"
        )
        return "\n".join(lines)

    def synthesize_final(self, conflict_query: str, round1: dict, round2: dict, disagreements: list, enable_search: bool = False) -> dict:
        """Produce final probability-weighted forecast from all debate positions."""
        all_positions = {}
        for agent, r1 in round1.items():
            all_positions[agent] = {
                "round1_prediction": r1.get("prediction", ""),
                "round1_confidence": r1.get("confidence", 0.5),
                "round1_factors": r1.get("key_factors", []),
            }
        for agent, r2 in round2.items():
            if agent in all_positions:
                all_positions[agent]["round2_prediction"] = r2.get("revised_prediction", r2.get("prediction", ""))
                all_positions[agent]["round2_confidence"] = r2.get("confidence", 0.5)
                all_positions[agent]["position_changed"]  = r2.get("position_changed", False)
                all_positions[agent]["round2_factors"]    = r2.get("key_factors", [])
                all_positions[agent]["rebuttal"]          = r2.get("rebuttal", "")

        prompt = (
            f"Conflict scenario: {conflict_query}\n\n"
            f"Multi-round debate results:\n{json.dumps(all_positions, indent=2)}\n\n"
            f"Number of disagreements identified and addressed: {len(disagreements)}\n\n"
            "Synthesize a final probability-weighted forecast. Apply these weighting rules:\n"
            "- Positions that changed after cross-examination: lower weight (agent was less confident)\n"
            "- Positions defended with specific evidence: higher weight\n"
            "- Points all three agents agreed on: highest weight (strongest signal)\n\n"
            "Return ONLY JSON:\n"
            "{\n"
            '  "outcome": "concise outcome prediction",\n'
            '  "probability": 0.0-1.0,\n'
            '  "probability_breakdown": {"Outcome A label": 0.X, "Outcome B label": 0.Y},\n'
            '  "key_factors": [\n'
            '    {"factor": "description", "source_agent": "AgentName", "weight": "high/medium/low"}\n'
            '  ],\n'
            '  "timeline": "estimated conflict duration and resolution",\n'
            '  "global_impact": "broader geopolitical implications",\n'
            '  "confidence": 0.0-1.0,\n'
            '  "consensus_areas": ["claim all agents agreed on"],\n'
            '  "unresolved_disagreements": ["what remained disputed after cross-examination"]\n'
            "}"
        )
        raw = self.call_qwen([{"role": "user", "content": prompt}], enable_search=enable_search)
        return self._parse_json_response(raw)
