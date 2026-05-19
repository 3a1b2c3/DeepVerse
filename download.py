"""Download the DeepVerse 1.1 checkpoint snapshot.

If the HF repo is gated, set HF_TOKEN (or HUGGINGFACE_HUB_TOKEN) in the env
before running — snapshot_download picks it up automatically. No need to
hardcode an access key here.
"""

import os
from pathlib import Path

from huggingface_hub import snapshot_download

REPO_ID = "SOTAMak1r/DeepVerse1.1"
LOCAL_DIR = Path(os.environ.get("DEEPVERSE_CKPT_DIR", Path(__file__).resolve().parent / "checkpoint"))

LOCAL_DIR.mkdir(parents=True, exist_ok=True)
print(f"Downloading {REPO_ID} -> {LOCAL_DIR}")
snapshot_download(
    repo_id=REPO_ID,
    local_dir=str(LOCAL_DIR),
    resume_download=True,
)
print(f"Done. {LOCAL_DIR}")
