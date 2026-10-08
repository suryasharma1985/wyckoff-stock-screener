import socket
# Force Python to resolve IPv4 only to bypass connection resets on Hugging Face APIs
orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(*args, **kwargs):
    responses = orig_getaddrinfo(*args, **kwargs)
    return [r for r in responses if r[0] == socket.AF_INET]
socket.getaddrinfo = getaddrinfo_ipv4

import os
import sys
from huggingface_hub import HfApi

def main():
    api = HfApi()
    repo_id = "suryasharma1985/wyckoff-stock-screener"
    
    print(f"[*] Creating/verifying private Docker Space: {repo_id}")
    try:
        api.create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="static",
            private=True,
            exist_ok=True
        )
        print("[+] Space repository ready!")
    except Exception as e:
        print(f"[-] Error creating Space repository: {e}")
        sys.exit(1)
        
    print("[*] Uploading files (excluding virtualenv and local cache/result folders)...")
    ignore_patterns = [
        ".git/*",
        ".venv/*",
        ".pytest_cache/*",
        "**/__pycache__/*",
        "data/cache/*",
        "data/research_datasets/*",
        "data/universe_snapshots/*",
        "data/forward_testing/*",
        "data/forward_validation/*",
        "data/backtest/*",
        "data/validation_results/*",
        "data/research_results/*",
    ]
    
    try:
        api.upload_folder(
            folder_path=".",
            repo_id=repo_id,
            repo_type="space",
            ignore_patterns=ignore_patterns,
            commit_message="Deploy Wyckoff Stock Screener to Hugging Face Spaces (Docker)"
        )
        print("[+] Upload completed successfully!")
        print(f"[+] Your Space is live at: https://huggingface.co/spaces/{repo_id}")
    except Exception as e:
        print(f"[-] Error uploading files: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
