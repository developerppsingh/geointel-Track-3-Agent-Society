import os

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

AGENT_MODEL = "qwen-max"
FAST_MODEL  = "qwen-turbo"

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge")

MAX_TOKENS        = 4096
AGENT_TEMPERATURE = 0.7
MAX_DEBATE_ROUNDS = 2
