"""Colab GPU Remote Runner for Jina OCR and Batch Inference."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional


class ColabOCRRunner:
    """Manages ephemeral Google Colab GPU sessions to run jina-ocr-v1 for zero cost."""

    REMOTE_SCRIPT_TEMPLATE = r'''
import sys, os, json, base64
from pathlib import Path

def main():
    import torch
    print(f"Colab GPU active: {torch.cuda.is_available()}, device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
    
    # Process batch images passed as arguments or payload
    # Uses HuggingFace transformers with jina-ocr-v1 or vLLM in bfloat16
    print("Colab GPU runner initialized successfully.")

if __name__ == "__main__":
    main()
'''

    def __init__(self, gpu_type: str = "T4"):
        self.gpu_type = gpu_type

    def is_colab_available(self) -> bool:
        """Check if colab CLI is installed and configured."""
        try:
            res = subprocess.run(["colab", "usage"], capture_output=True, text=True, timeout=10)
            return "Current balance:" in res.stdout
        except Exception:
            return False

    def get_balance(self) -> Optional[float]:
        """Query remaining Colab compute units."""
        try:
            res = subprocess.run(["colab", "usage"], capture_output=True, text=True, timeout=10)
            for line in res.stdout.splitlines():
                if "Current balance:" in line:
                    val = line.split(":", 1)[1].replace("compute units", "").strip()
                    return float(val)
        except Exception:
            pass
        return None

    def run_ephemeral_script(self, script_path: Path, timeout_sec: float = 120.0) -> subprocess.CompletedProcess:
        """Execute a local Python script on a fresh Colab VM and auto-terminate."""
        cmd = [
            "colab", "run",
            "--gpu", self.gpu_type,
            "--timeout", str(timeout_sec),
            str(script_path)
        ]
        return subprocess.run(cmd, capture_output=True, text=True)
