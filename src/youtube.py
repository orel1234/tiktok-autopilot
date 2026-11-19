"""Upload videos to YouTube with the Data API v3 (resumable upload, OAuth refresh token)."""
import json, os, requests

def enabled():
    return all(os.getenv(k, "").strip() for k in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"))

def _token():
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": os.environ["YOUTUBE_CLIENT_ID"].strip(), "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"].strip(),
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"].strip(), "grant_type": "refresh_token"})
    j = r.json()
    if "access_token" not in j:
        raise RuntimeError(f"YouTube token refresh failed: {j.get('error')} {j.get('error_description', '')}")
    return j["access_token"]

def upload(path, title, description, tags, short=False):
    """Upload one video; returns its YouTube id. Shorts: vertical and under 3 minutes, tagged #Shorts."""
    if short and "#shorts" not in title.lower():
        title = (title[:90] + " #Shorts")
    meta = {
        "snippet": {"title": title[:100], "description": description[:4900], "tags": tags[:15], "categoryId": "24"},
        "status": {"privacyStatus": os.getenv("YOUTUBE_PRIVACY", "private"), "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": True},  # AI-generated voice and story, disclosed as YouTube requires
    }
    size = os.path.getsize(path)
    h = {"Authorization": f"Bearer {_token()}"}
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                         headers={**h, "Content-Type": "application/json; charset=UTF-8",
                                  "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
                         data=json.dumps(meta), timeout=60)
    if init.status_code >= 400:
        raise RuntimeError(f"YouTube upload init failed: HTTP {init.status_code} {init.text[:300]}")
    with open(path, "rb") as f:
        up = requests.put(init.headers["Location"], headers={**h, "Content-Type": "video/mp4", "Content-Length": str(size)},
                          data=f, timeout=900)
    if up.status_code >= 400:
        raise RuntimeError(f"YouTube upload failed: HTTP {up.status_code} {up.text[:300]}")
    vid = up.json()["id"]
    print(f"YouTube: uploaded https://youtu.be/{vid} ({meta['status']['privacyStatus']})")
    return vid
