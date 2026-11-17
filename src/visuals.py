"""Download a vertical stock clip from Pexels for a search query."""
import os, random, requests

def fetch_clip(query, path, used):
    r = requests.get("https://api.pexels.com/videos/search",
        headers={"Authorization": os.environ["PEXELS_API_KEY"]},
        params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 15}, timeout=30)
    r.raise_for_status()
    vids = [v for v in r.json().get("videos", []) if v["id"] not in used] or r.json().get("videos", [])
    if not vids:
        return False
    v = random.choice(vids[:8]); used.add(v["id"])
    files = sorted((f for f in v["video_files"] if f.get("height", 0) >= 1080 and f["file_type"] == "video/mp4"),
                   key=lambda f: f["height"]) or v["video_files"]
    data = requests.get(files[0]["link"], timeout=120); data.raise_for_status()
    open(path, "wb").write(data.content)
    return True
