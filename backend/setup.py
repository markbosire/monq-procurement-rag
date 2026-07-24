"""One-command setup script for the MONQ Procurement RAG backend.

Creates a virtual environment, installs dependencies, downloads the spaCy
model and sentence-transformers embedding model, and copies the example
environment file.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent


def run(cmd: list[str], msg: str, cwd: str | None = None) -> None:
    print(f"  {msg}", flush=True)
    subprocess.check_call(cmd, cwd=cwd or BACKEND_DIR)


def main():
    venv_dir = BACKEND_DIR / ".venv"

    # 1. Create virtual environment
    if not venv_dir.exists():
        run([sys.executable, "-m", "venv", str(venv_dir)], "Creating virtual environment...")
    else:
        print("  Virtual environment already exists.", flush=True)

    # Determine pip/python paths
    is_windows = os.name == "nt"
    pip_cmd = str(venv_dir / ("Scripts" if is_windows else "bin") / "pip")
    python_cmd = str(venv_dir / ("Scripts" if is_windows else "bin") / "python")

    # 2. Install requirements
    run([pip_cmd, "install", "-r", "requirements.txt"], "[1/5] Installing Python dependencies...")

    # 3. Download spaCy model
    run([python_cmd, "-m", "spacy", "download", "en_core_web_sm"], "[2/5] Downloading spaCy language model...")

    # 4. Pre-download sentence-transformers embedding model
    run([python_cmd, "-c", "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"], "[3/5] Downloading embedding model (all-MiniLM-L6-v2)...")

    # 5. Copy .env.example -> .env if not present
    env_example = BACKEND_DIR / ".env.example"
    env_file = BACKEND_DIR / ".env"
    if env_example.exists() and not env_file.exists():
        print("  [4/5] Creating .env from .env.example...", flush=True)
        shutil.copy(env_example, env_file)
    print("  [5/5] Don't forget to set your GROQ_API_KEY in .env", flush=True)

    print("\nSetup complete! Activate the environment and start the server:")
    if is_windows:
        print(f"  {venv_dir}\\Scripts\\activate")
    else:
        print(f"  source {venv_dir}/bin/activate")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
