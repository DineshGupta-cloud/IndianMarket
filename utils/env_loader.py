"""Load local .env once so GROQ_API_KEY / LLM_API_KEY work automatically."""
from pathlib import Path


def load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    # Project root (parent of utils/)
    root = Path(__file__).resolve().parent.parent
    env_path = root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # still pick up process env / cwd .env
