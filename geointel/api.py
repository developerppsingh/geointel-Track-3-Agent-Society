import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS

from kb_loader import KnowledgeBase
from simulate.engine import SimulationEngine

app = Flask(__name__)
CORS(app)

kb = KnowledgeBase()


def _build_engine(verbose, enable_search, horizon, api_key=None):
    """Build a fresh SimulationEngine, optionally with an overridden API key."""
    if api_key:
        os.environ["DASHSCOPE_API_KEY"] = api_key

    # Rebuild config module so agents read the new key
    import importlib
    import config
    importlib.reload(config)

    # Re-import agent modules so they pick up the new config
    from agents import base, historian, strategist, economist, baseline, synthesis
    importlib.reload(base)
    importlib.reload(historian)
    importlib.reload(strategist)
    importlib.reload(economist)
    importlib.reload(baseline)
    importlib.reload(synthesis)

    return SimulationEngine(verbose=verbose, enable_search=enable_search, horizon=horizon)


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    try:
        data = request.get_json(force=True)
        conflict = data.get("conflict", "")
        verbose = data.get("verbose", False)
        enable_search = data.get("enable_search", False)
        horizon = data.get("horizon", "long")

        # Allow API key override via header
        override_key = request.headers.get("X-API-Key", "")

        if not conflict:
            return jsonify({"error": "Missing 'conflict' parameter"}), 400

        engine = _build_engine(verbose, enable_search, horizon, api_key=override_key or None)
        result = engine.run(conflict)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/query/country", methods=["GET"])
def api_query_country():
    name = request.args.get("name", "")
    results = kb.search_country(name)
    return jsonify(results), 200


@app.route("/api/query/pattern", methods=["GET"])
def api_query_pattern():
    q = request.args.get("q", "")
    results = kb.search_patterns(q)
    return jsonify(results), 200


@app.route("/api/index", methods=["GET"])
def api_index():
    return jsonify({
        "summary": kb.summary(),
        "countries": [c.get("name", "") for c in kb.countries],
        "conflicts": [c.get("name", "") for c in kb.conflicts],
        "patterns": [p.get("name", "") for p in kb.patterns],
    }), 200


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "status": "ok",
        "kb": kb.summary(),
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
