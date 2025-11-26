"""Configuration defaults and environment handling for Mind."""
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("MIND_DATA_DIR", BASE_DIR.parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(os.getenv("MIND_DB_PATH", DATA_DIR / "mind.db"))
SQLITE_VEC_PATH = os.getenv("SQLITE_VEC_PATH", "/usr/local/lib/vec0")

OPENROUTER_BASE = os.getenv("OPENROUTER_BASE", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MIND_EMBEDDING_MODEL = os.getenv("MIND_EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")
MIND_LLM_MODEL = os.getenv("MIND_LLM_MODEL", "qwen/qwen-2.5-7b-instruct")
MIND_EMBEDDING_DIM = int(os.getenv("MIND_EMBEDDING_DIM", "4096"))

AI_ASSIST_ENABLED = os.getenv("MIND_AI_ASSIST", "true").lower() == "true"
AUTO_CLUSTER_ENABLED = os.getenv("MIND_AUTO_CLUSTER", "true").lower() == "true"

SERVER_NAME = os.getenv("MIND_SERVER_NAME", "0.0.0.0")
SERVER_PORT = int(os.getenv("MIND_SERVER_PORT", "7860"))
