from huggingface_hub import snapshot_download

repo_id  = "SOTAMak1r/DeepVerse1.1"
ak = "your ak"

snapshot_download(
        local_dir=r"C:\workspace\world\DeepVerse\checkpoint",
        repo_id=repo_id,
        local_dir_use_symlinks=False,
        resume_download=True,
        use_auth_token=ak,
    )