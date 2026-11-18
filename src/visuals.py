"""Download a stock clip for a search query. Pixabay (free key) by default, Pexels if only that key is set."""
import os, random, re, subprocess, requests

def _pixabay(query, used):
    """Return candidate (id, url) pairs: vertical clips first, then the sharpest ones."""
    r = requests.get("https://pixabay.com/api/videos/",
        params={"key": os.environ["PIXABAY_API_KEY"], "q": query, "per_page": 50, "safesearch": "true"}, timeout=30)
    r.raise_for_status()
    hits = [h for h in r.json().get("hits", []) if h["id"] not in used]
    def best(h):  # largest available rendition
        for size in ("large", "medium", "small"):
            f = h["videos"].get(size, {})
            if f.get("url"):
                return f
        return {}
    portrait = [h for h in hits if best(h).get("height", 0) > best(h).get("width", 1)]
    pool = portrait[:8] or sorted(hits[:15], key=lambda h: -best(h).get("width", 0))[:8]
    random.shuffle(pool)
    return [(h["id"], best(h)["url"]) for h in pool if best(h).get("url")]

def _pexels(query, used):
    r = requests.get("https://api.pexels.com/videos/search",
        headers={"Authorization": os.environ["PEXELS_API_KEY"]},
        params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 15}, timeout=30)
    r.raise_for_status()
    out = []
    for v in r.json().get("videos", []):
        if v["id"] in used:
            continue
        files = sorted((f for f in v["video_files"] if f.get("height", 0) >= 1080 and f["file_type"] == "video/mp4"),
                       key=lambda f: f["height"]) or v["video_files"]
        out.append((v["id"], files[0]["link"]))
    random.shuffle(out)
    return out[:8]

def brightness(path):
    """Average luma (0-255) of a frame one second in; None if it cannot be measured."""
    p = subprocess.run(["ffmpeg", "-ss", "1", "-i", str(path), "-frames:v", "1", "-vf", "signalstats,metadata=print",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"lavfi.signalstats.YAVG=([\d.]+)", p.stderr)
    return float(m.group(1)) if m else None

MAX_BRIGHTNESS = float(os.getenv("MAX_CLIP_BRIGHTNESS", "105"))

def fetch_clip(query, path, used):
    """Download the first candidate that is dark enough for a night-time horror mood."""
    cands = (_pixabay if os.getenv("PIXABAY_API_KEY") else _pexels)(query, used)
    fallback = None
    for vid, url in cands[:5]:
        data = requests.get(url, timeout=180); data.raise_for_status()
        open(path, "wb").write(data.content)
        used.add(vid)
        b = brightness(path)
        if b is None or b <= MAX_BRIGHTNESS:
            return True
        print(f"  skipped bright clip for '{query}' (brightness {b:.0f})")
        fallback = fallback or data.content
    if fallback:  # nothing dark enough: keep a bright one, the colour grade darkens it
        open(path, "wb").write(fallback)
        return True
    return False
