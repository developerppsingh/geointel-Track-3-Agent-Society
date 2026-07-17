import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb_loader         import KnowledgeBase
from agents.historian  import HistorianAgent
from agents.strategist import StrategistAgent
from agents.economist  import EconomistAgent
from agents.baseline   import BaselineAgent
from agents.synthesis  import SynthesisAgent


class SimulationEngine:
    def __init__(self, verbose: bool = False, enable_search: bool = False, horizon: str = "long"):
        self.verbose       = verbose
        self.enable_search = enable_search
        self.horizon       = horizon
        self.kb            = KnowledgeBase()
        self.historian     = HistorianAgent( kb=self.kb)
        self.strategist    = StrategistAgent(kb=self.kb)
        self.economist     = EconomistAgent( kb=self.kb)
        self.synthesis     = SynthesisAgent( kb=self.kb)
        self.baseline      = BaselineAgent(  kb=None)

    def _progress(self, step: int, total: int, msg: str):
        print(f"  [{step}/{total}] {msg}", flush=True)

    def run(self, conflict_query: str) -> dict:
        TOTAL = 8
        result = {"conflict": conflict_query}
        search_label = " (with web search)" if self.enable_search else ""
        horizon_label = f" [{self.horizon}-term]" if self.horizon != "long" else ""

        # Step 1: Baseline
        self._progress(1, TOTAL, f"Running single-agent baseline (no knowledge base){search_label}{horizon_label}...")
        result["baseline"] = self.baseline.analyze(conflict_query, enable_search=self.enable_search, horizon=self.horizon)

        # Step 2: Task Decomposition
        self._progress(2, TOTAL, "Decomposing query into role-specific sub-questions...")
        decomposition = self.synthesis.decompose_query(conflict_query, enable_search=self.enable_search)
        result["decomposition"] = decomposition

        historian_q  = decomposition.get("historian_question",  conflict_query)
        strategist_q = decomposition.get("strategist_question", conflict_query)
        economist_q  = decomposition.get("economist_question",  conflict_query)

        parties   = decomposition.get("conflict_parties", [])
        query_str = " ".join(parties) or conflict_query

        # Step 3-5: Round 1 — Independent Assessments
        historian_ctx  = self.kb.get_context_for("historian",  query_str)
        strategist_ctx = self.kb.get_context_for("strategist", query_str)
        economist_ctx  = self.kb.get_context_for("economist",  query_str)

        self._progress(3, TOTAL, f"Round 1: HistorianAgent — historical precedents and base rates{search_label}...")
        round1 = {"HistorianAgent": self.historian.analyze(historian_q, historian_ctx, round_num=1, enable_search=self.enable_search, horizon=self.horizon)}

        self._progress(4, TOTAL, f"Round 1: StrategistAgent — military balance and operational assessment{search_label}...")
        round1["StrategistAgent"] = self.strategist.analyze(strategist_q, strategist_ctx, round_num=1, enable_search=self.enable_search, horizon=self.horizon)

        self._progress(5, TOTAL, f"Round 1: EconomistAgent — economic sustainability and war finance{search_label}...")
        round1["EconomistAgent"] = self.economist.analyze(economist_q, economist_ctx, round_num=1, enable_search=self.enable_search, horizon=self.horizon)

        result["round1"] = round1

        # Step 6: Disagreement Detection
        self._progress(6, TOTAL, "Detecting disagreements between specialist assessments...")
        disagreements = self.synthesis.detect_disagreements(round1, enable_search=self.enable_search)
        result["disagreements"] = disagreements

        # Step 7: Round 2 — Cross-Examination
        self._progress(7, TOTAL, f"Round 2: Cross-examination of disputed positions{search_label}...")
        round2 = {}
        agent_map = [
            ("HistorianAgent",  self.historian),
            ("StrategistAgent", self.strategist),
            ("EconomistAgent",  self.economist),
        ]
        for agent_name, agent_obj in agent_map:
            prompt = self.synthesis.build_cross_examination_prompt(agent_name, disagreements, round1)
            if prompt:
                raw = agent_obj.call_qwen([{"role": "user", "content": prompt}], enable_search=self.enable_search)
                r2  = agent_obj._parse_json_response(raw)
                r2["agent"] = agent_name
                round2[agent_name] = r2
            else:
                round2[agent_name] = {
                    "agent": agent_name,
                    "revised_prediction": round1[agent_name].get("prediction", ""),
                    "confidence": round1[agent_name].get("confidence", 0.5),
                    "position_changed": False,
                    "change_reason": "No disagreements to address — position unchanged.",
                    "key_factors": round1[agent_name].get("key_factors", []),
                }
        result["round2"] = round2

        # Step 8: Final Synthesis
        self._progress(8, TOTAL, "Synthesizing final probability-weighted forecast...")
        result["final"] = self.synthesis.synthesize_final(conflict_query, round1, round2, disagreements, enable_search=self.enable_search)

        # Metrics (for baseline comparison)
        all_society_factors = []
        for r in round1.values():
            all_society_factors.extend(r.get("key_factors", []))
        for r in round2.values():
            all_society_factors.extend(r.get("key_factors", []))

        positions_changed = sum(1 for r in round2.values() if r.get("position_changed", False))

        result["metrics"] = {
            "baseline_factors":       len(result["baseline"].get("key_factors", [])),
            "society_factors":        len(set(all_society_factors)),
            "dimensions_covered":     3,
            "disagreements_detected": len(disagreements),
            "positions_changed":      positions_changed,
            "debate_rounds_run":      2,
            "baseline_confidence":    result["baseline"].get("confidence", 0.5),
            "society_confidence":     result["final"].get("confidence", 0.5),
            "web_search_enabled":     self.enable_search,
            "horizon":                self.horizon,
        }

        return result
