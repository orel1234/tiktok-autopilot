"""Publish an mp4 via TikTok Content Posting API (Direct Post, FILE_UPLOAD)."""
import os, requests

API = "https://open.tiktokapis.com/v2"

def access_token():
    r = requests.post(f"{API}/oauth/token/", data={
        "client_key": os.environ["TIKTOK_CLIENT_KEY"].strip(), "client_secret": os.environ["TIKTOK_CLIENT_SECRET"].strip(),
        "grant_type": "refresh_token", "refresh_token": os.environ["TIKTOK_REFRESH_TOKEN"].strip()}, timeout=30)
    r.raise_for_status(); j = r.json()
    if "access_token" not in j:
        raise RuntimeError(f"token refresh failed: {j}")
    return j["access_token"]

def _check(resp, step):
    """Raise with TikTok's own error code and message (not just the HTTP status)."""
    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text[:500]}
    err = body.get("error", {})
    if resp.status_code >= 400 or err.get("code") not in (None, "ok"):
        raise RuntimeError(f"{step} failed: HTTP {resp.status_code}, code={err.get('code')}, message={err.get('message')}")
    return body

def post(path, caption):
    tok = access_token(); size = os.path.getsize(path)
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
    # Ask TikTok which privacy levels this account allows (required by the Direct Post guidelines)
    info = _check(requests.post(f"{API}/post/publish/creator_info/query/", headers=h, timeout=30), "creator info")["data"]
    allowed = info.get("privacy_level_options", [])
    want = os.getenv("TIKTOK_PRIVACY", "SELF_ONLY")
    privacy = want if want in allowed else ("SELF_ONLY" if "SELF_ONLY" in allowed else allowed[0])
    print(f"Posting as @{info.get('creator_username')} with privacy {privacy} (allowed: {allowed})")
    d = _check(requests.post(f"{API}/post/publish/video/init/", headers=h, timeout=30, json={
        "post_info": {"title": caption[:2200], "privacy_level": privacy,
                      "disable_comment": False, "disable_duet": False, "disable_stitch": False,
                      "is_aigc": True},  # label AI-generated content, required by TikTok policy
        "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}}),
        "upload init")
    up = requests.put(d["data"]["upload_url"], data=open(path, "rb"), timeout=300, headers={
        "Content-Type": "video/mp4", "Content-Length": str(size), "Content-Range": f"bytes 0-{size-1}/{size}"})
    if up.status_code >= 400:
        raise RuntimeError(f"video upload failed: HTTP {up.status_code} {up.text[:300]}")
    return d["data"]["publish_id"]
