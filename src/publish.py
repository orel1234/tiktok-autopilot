"""Publish an mp4 via TikTok Content Posting API (Direct Post, FILE_UPLOAD)."""
import os, requests

API = "https://open.tiktokapis.com/v2"

def access_token():
    r = requests.post(f"{API}/oauth/token/", data={
        "client_key": os.environ["TIKTOK_CLIENT_KEY"], "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
        "grant_type": "refresh_token", "refresh_token": os.environ["TIKTOK_REFRESH_TOKEN"]}, timeout=30)
    r.raise_for_status(); j = r.json()
    if "access_token" not in j:
        raise RuntimeError(f"token refresh failed: {j}")
    return j["access_token"]

def post(path, caption):
    tok = access_token(); size = os.path.getsize(path)
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
    init = requests.post(f"{API}/post/publish/video/init/", headers=h, timeout=30, json={
        "post_info": {"title": caption[:2200], "privacy_level": os.getenv("TIKTOK_PRIVACY", "SELF_ONLY"),
                      "disable_comment": False, "disable_duet": False, "disable_stitch": False,
                      "is_aigc": True},  # label AI-generated content, required by TikTok policy
        "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}})
    init.raise_for_status(); d = init.json()
    if d.get("error", {}).get("code") != "ok":
        raise RuntimeError(f"init failed: {d}")
    up = requests.put(d["data"]["upload_url"], data=open(path, "rb"), timeout=300, headers={
        "Content-Type": "video/mp4", "Content-Length": str(size), "Content-Range": f"bytes 0-{size-1}/{size}"})
    up.raise_for_status()
    return d["data"]["publish_id"]
