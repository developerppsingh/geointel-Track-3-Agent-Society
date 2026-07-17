# GeoIntel — Multi-Agent Geopolitical Intelligence System

> **Agent Society Hackathon Project** — A multi-agent AI system that simulates geopolitical conflict outcomes through structured debate between three specialist AI agents.

[![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

## Overview

GeoIntel answers complex geopolitical questions by deploying a society of specialized AI agents that reason independently, debate each other, and converge on a probability-weighted forecast. Rather than asking a single model to be a historian, strategist, and economist simultaneously, GeoIntel assigns each role to a dedicated agent, then runs a structured multi-round debate protocol to surface and resolve disagreements before synthesizing a final prediction.

### The Four Agents

| Agent | Role | Analytical Framework |
|---|---|---|
| **HistorianAgent** | Pattern-matching across conflict history | Cliodynamics, imperial overstretch, insurgency base rates, civilizational fatigue |
| **StrategistAgent** | Military balance assessment | DIME matrix, A2/AD, nuclear escalation, logistics, terrain multipliers |
| **EconomistAgent** | War finance & economic sustainability | FIRE ratio, debt-to-GDP, energy independence, sanctions resilience |
| **SynthesisAgent** | Orchestrator & judge | Task decomposition, disagreement detection, cross-examination, weighted synthesis |

### How It Works

```
1. BaselineAgent → single-agent baseline prediction (no KB)
2. SynthesisAgent → decomposes query into 3 role-specific sub-questions
3-5. Round 1 → Historian, Strategist, Economist each analyze independently
6. SynthesisAgent → detects genuine disagreements between agents
7. Cross-examination → agents defend or revise positions
8. SynthesisAgent → produces final probability-weighted forecast
```

### Why Multi-Agent?

| Metric | Single Agent | Agent Society |
|---|---|---|
| Analytical lenses | 1 (general) | 3 (specialist) |
| Key factors identified | 3-5 | 12-18 |
| Disagreements surfaced | 0 | 2-4 per simulation |
| Knowledge base context | None | Role-filtered |
| Confidence calibration | Unchecked | Debate-validated |

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Qwen (DashScope) API key** 

### Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd geointel

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
export DASHSCOPE_API_KEY=sk-your-key-here
```

### Run a Simulation (CLI)

```bash
# Full multi-agent simulation
python main.py simulate --conflict "Iran vs Israel"

# With real-time web search grounding
python main.py simulate --conflict "Iran vs Israel" --search

# Verbose output (see all debate rounds)
python main.py simulate --conflict "China Taiwan invasion" --verbose --search

# JSON output for downstream processing
python main.py simulate --conflict "Iran vs Israel" --output result.json

# Single-agent baseline (for comparison)
python main.py baseline --conflict "Iran vs Israel"
```

### Query the Knowledge Base

```bash
# Country profiles (military + economic)
python main.py query --country "Russia"

# Civilizational patterns
python main.py query --pattern "overstretch"

# List all KB contents
python main.py index
```

### Start the Web API Server

```bash
python api.py
# Server runs at http://0.0.0.0:5000
```

Then open `frontend/index.html` in your browser.

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/simulate` | POST | Run a full simulation. Body: `{"conflict": "...", "verbose": false, "enable_search": false}` |
| `/api/query/country` | GET | Search country profiles. Param: `?name=Russia` |
| `/api/query/pattern` | GET | Search civilizational patterns. Param: `?q=overstretch` |
| `/api/index` | GET | List KB summary and contents |
| `/api/health` | GET | Health check |

Example API call:

```bash
curl -X POST http://localhost:5000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"conflict": "Iran vs Israel", "enable_search": false}'
```

## Project Structure

```
geointel/
├── main.py              # CLI entry point (argparse)
├── api.py               # Flask REST API server
├── config.py            # Central configuration (models, API endpoint, settings)
├── kb_loader.py         # Knowledge base loader
├── requirements.txt     # Python dependencies
├── LICENSE              # GPL-3.0
├── agents/
│   ├── __init__.py
│   ├── base.py          # BaseAgent class (Qwen API client, JSON parsing)
│   ├── historian.py     # HistorianAgent — conflict history & patterns
│   ├── strategist.py    # StrategistAgent — military balance
│   ├── economist.py     # EconomistAgent — war finance & economics
│   ├── baseline.py      # BaselineAgent — single-agent comparison
│   └── synthesis.py     # SynthesisAgent — orchestration & debate
├── simulate/
│   ├── __init__.py
│   └── engine.py        # 8-step simulation pipeline
├── knowledge/
│   └── seed_data.json   # Embedded knowledge corpus (18 countries, 18 conflicts, 17 patterns, 23 demographics, 12 religious/cultural drivers)
├── frontend/
│   └── index.html       # Single-page web UI (no external dependencies)
└── design/              # Architecture docs, diagrams, demo script
```

## Knowledge Base

The system ships with an embedded JSON knowledge corpus — no database or indexing pipeline required:

- **18 Country Profiles** — military capabilities, economic indicators, alliance structures
- **18 Historical Conflicts** — outcomes, lessons learned, probability models
- **17 Civilizational Patterns** — imperial overstretch, elite overproduction, nuclear deterrence, etc.
- **23 Demographic Records** — population, age, TFR, military-age %, GDP per capita
- **12 Religious/Cultural Drivers** — eschatology, honor culture, nationalism — with deterrence implications

Each agent receives role-filtered context from the KB, ensuring they reason from their own evidence base.

## Alibaba Cloud Integration

This project uses **Qwen AI models** via Alibaba Cloud's DashScope platform:

- **qwen-max** — primary model for all specialist agent analysis
- **qwen-turbo** — fast model for orchestration tasks (decomposition, disagreement detection)

The system can be deployed on Alibaba Cloud ECS, Function Compute, or App Service. See [design/DEPLOYMENT_GUIDE.md](design/DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## Technical Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| AI API | Qwen (DashScope) — OpenAI-compatible endpoint |
| Web Framework | Flask + Flask-CORS |
| CLI Formatting | Rich |
| Knowledge Storage | JSON (no database) |
| Frontend | Vanilla HTML/CSS/JS (no dependencies) |

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
