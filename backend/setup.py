"""One-command setup script for the MONQ Procurement RAG backend.

Creates a virtual environment, installs dependencies, downloads the spaCy
model, and copies the example environment file.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent


def run(cmd: list[str], cwd: str | None = None) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=cwd or BACKEND_DIR)


def main():
    venv_dir = BACKEND_DIR / ".venv"

    # 1. Create virtual environment
    if not venv_dir.exists():
        print("Creating virtual environment...")
        run([sys.executable, "-m", "venv", str(venv_dir)])
    else:
        print("Virtual environment already exists.")

    # Determine pip/python paths
    is_windows = os.name == "nt"
    pip_cmd = str(venv_dir / ("Scripts" if is_windows else "bin") / "pip")
    python_cmd = str(venv_dir / ("Scripts" if is_windows else "bin") / "python")

    # 2. Install requirements
    print("Installing Python dependencies...")
    run([pip_cmd, "install", "-r", "requirements.txt"])

    # 3. Download spaCy model
    print("Downloading spaCy language model...")
    run([python_cmd, "-m", "spacy", "download", "en_core_web_sm"])

    # 4. Copy .env.example -> .env if not present
    env_example = BACKEND_DIR / ".env.example"
    env_file = BACKEND_DIR / ".env"
    if env_example.exists() and not env_file.exists():
        print("Creating .env from .env.example...")
        shutil.copy(env_example, env_file)
        print("  >> Don't forget to set your GROQ_API_KEY in .env")

    print("\nSetup complete! Activate the environment and start the server:")
    if is_windows:
        print(f"  {venv_dir}\\Scripts\\activate")
    else:
        print(f"  source {venv_dir}/bin/activate")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
