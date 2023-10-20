import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(verbose=True)

if "CREDENTIALS_DIRECTORY" in os.environ:
    creds_dir = Path(os.environ["CREDENTIALS_DIRECTORY"])
    print(f"Loading credentials from {creds_dir}")
    for creds_file in creds_dir.iterdir():
        os.environ[creds_file.name] = creds_file.read_text()

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.environ.get("STATE_DIRECTORY", BASE_DIR / "runtime"))

print("BASE_DIR", BASE_DIR)
print("STATE_DIR", STATE_DIR)
