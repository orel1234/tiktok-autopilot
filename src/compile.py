"""Join the parts of a series into one long video, cutting the per-part recap at the start and the
'follow for part N' outro at the end so it plays as one continuous story."""
import subprocess

def join(parts, out_path):
    """parts: list of dicts {path, total, first, last} in order (seconds)."""
    n = len(parts)
    inputs, filters = [], []
    for i, p in enumerate(parts):
        start = p["first"] if i > 0 else 0.0          # drop the "Last time..." recap from parts 2..n
        end = p["total"] - p["last"] if i < n - 1 else p["total"]   # drop the "follow for part N" outro
        inputs += ["-i", str(p["path"])]
        filters.append(f"[{i}:v]trim={start:.2f}:{end:.2f},setpts=PTS-STARTPTS[v{i}];"
                       f"[{i}:a]atrim={start:.2f}:{end:.2f},asetpts=PTS-STARTPTS[a{i}]")
    concat = "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
    subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters) + ";" + concat,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out_path)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return out_path
