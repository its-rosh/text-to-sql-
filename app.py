"""
Entry point for Hugging Face Spaces & Streamlit deployments.
Delegates execution to app/main.py.
"""
from pathlib import Path
import runpy
import sys

# Ensure repository root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Target the primary Streamlit application
MAIN_APP_PATH = PROJECT_ROOT / "app" / "main.py"

if __name__ == "__main__" or "streamlit" in sys.modules:
    runpy.run_path(str(MAIN_APP_PATH), run_name="__main__")
