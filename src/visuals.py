"""Download a stock clip for a search query. Pixabay (free key) by default, Pexels if only that key is set."""
import os, random, requests

def _pixabay(query, used):
    r = requests.get("https://pixabay.com/api/videos/",
        params={"key": os.environ["PIXABAY_API_KEY"], "q": query, "per_page": 50, "safesearch": "true"}, timeout=30)
    r.raise_for_status()
    hits = r.json().get("hits", [])
    hits = [h for h in hits if h["id"] not in used] or hits
    if not hits:
        return None, None
    def best(h):  # largest available rendition
        for size in ("large", "medium", "small"):
            f = h["videos"].get(size, {})
            if f.get("url"):
                return f
        return {}
    # prefer vertical clips (they fill a phone screen without cropping), then the sharpest ones
    portrait = [h for h in hits if best(h).get("height", 0) > best(h).get("width", 1)]
    pool = portrait[:8] or sorted(hits[:15], key=lambda h: -best(h).get("width", 0))[:6]
    h = random.choice(pool)
    return h["id"], best(h).get("url")

def _pexels(query, used):
    r = requests.get("https://api.pexels.com/videos/search",
        headers={"Authorization": os.environ["PEXELS_API_KEY"]},
        params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 15}, timeout=30)
    r.raise_for_status()
    vids = r.json().get("videos", [])
    vids = [v for v in vids if v["id"] not in used] or vids
    if not vids:
        return None, None
    v = random.choice(vids[:8])
    files = sorted((f for f in v["video_files"] if f.get("height", 0) >= 1080 and f["file_type"] == "video/mp4"),
                   key=lambda f: f["height"]) or v["video_files"]
    return v["id"], files[0]["link"]

def fetch_clip(query, path, used):
    vid, url = (_pixabay if os.getenv("PIXABAY_API_KEY") else _pexels)(query, used)
    if not url:
        return False
    used.add(vid)
    data = requests.get(url, timeout=180); data.raise_for_status()
    open(path, "wb").write(data.content)
    return True
