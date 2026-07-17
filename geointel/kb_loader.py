import os
import json

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge")


class KnowledgeBase:
    def __init__(self):
        self.countries:                 list = []
        self.conflicts:                 list = []
        self.patterns:                  list = []
        self.demographics:              list = []
        self.religious_cultural:        list = []
        self._load()

    def _load(self):
        seed_path = os.path.join(KNOWLEDGE_DIR, "seed_data.json")
        if os.path.exists(seed_path):
            with open(seed_path, encoding="utf-8") as f:
                seed = json.load(f)
            self.countries          = seed.get("countries", [])
            self.conflicts          = seed.get("conflicts", [])
            self.patterns           = seed.get("patterns", [])
            self.demographics       = seed.get("demographics", [])
            self.religious_cultural = seed.get("religious_cultural_drivers", [])

    def search_country(self, name: str) -> list:
        name_lower = name.lower()
        return [c for c in self.countries if name_lower in c.get("name", "").lower()]

    def search_conflicts(self, parties: list) -> list:
        party_lower = [p.lower() for p in parties]
        results = []
        for c in self.conflicts:
            text = json.dumps(c).lower()
            if any(p in text for p in party_lower):
                results.append(c)
        return results

    def search_patterns(self, query: str) -> list:
        q = query.lower()
        return [p for p in self.patterns if q in p.get("name", "").lower() or q in p.get("description", "").lower()]

    def search_religious_cultural(self, query: str) -> list:
        q = query.lower()
        results = []
        for r in self.religious_cultural:
            text = json.dumps(r).lower()
            if q in text:
                results.append(r)
        return results if results else self.religious_cultural[:4]

    def get_demographics(self, country: str) -> list:
        c = country.lower()
        return [d for d in self.demographics if c in d.get("country", "").lower()]

    def get_context_for(self, agent_role: str, conflict_query: str) -> dict:
        query_lower = conflict_query.lower()
        words = [w.strip(".,;:?!\"'") for w in query_lower.split() if len(w) > 3]

        relevant_countries = []
        for c in self.countries:
            name = c.get("name", "").lower()
            if any(w in name or name in w for w in words):
                relevant_countries.append(c)
        if not relevant_countries:
            relevant_countries = self.countries[:6]

        relevant_conflicts = self.search_conflicts(words)
        if not relevant_conflicts:
            relevant_conflicts = self.conflicts[:5]

        relevant_religion = self.search_religious_cultural(conflict_query)

        if agent_role == "historian":
            return {
                "civilizational_patterns": self.patterns,
                "historical_conflicts": relevant_conflicts,
                "religious_cultural_drivers": relevant_religion,
            }
        elif agent_role == "strategist":
            return {
                "country_military_profiles": [
                    {k: v for k, v in c.items() if k in ("name", "military_strength", "alliances", "notes")}
                    for c in relevant_countries
                ],
                "historical_conflicts": relevant_conflicts,
                "religious_cultural_drivers": relevant_religion,
            }
        elif agent_role == "economist":
            demographics = []
            for c in relevant_countries:
                demographics.extend(self.get_demographics(c.get("name", "")))
            return {
                "country_economic_profiles": [
                    {k: v for k, v in c.items() if k in ("name", "economy", "alliances", "notes")}
                    for c in relevant_countries
                ],
                "demographics": demographics,
            }
        else:
            return {
                "countries": relevant_countries[:4],
                "conflicts": relevant_conflicts[:4],
                "patterns":  self.patterns[:4],
                "religious_cultural_drivers": relevant_religion[:3],
            }

    def summary(self) -> dict:
        return {
            "countries":                len(self.countries),
            "conflicts":                len(self.conflicts),
            "patterns":                 len(self.patterns),
            "demographics":             len(self.demographics),
            "religious_cultural":       len(self.religious_cultural),
        }
