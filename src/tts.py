"""TTS with word timings for captions. edge-tts first (retries), Piper (offline) as fallback."""
import asyncio, os, pathlib, subprocess, wave, edge_tts

VOICE = "en-US-AndrewNeural"
PIPER_MODEL = os.getenv("PIPER_MODEL", "models/en_US-lessac-medium.onnx")

async def _edge(text, path):
    words, dur = [], 0.0
    comm = edge_tts.Communicate(text, VOICE, rate="+8%", boundary="WordBoundary")
    with open(path, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                s, d = ch["offset"] / 1e7, ch["duration"] / 1e7
                words.append((ch["text"], s, s + d)); dur = s + d
    if not words:
        raise RuntimeError("edge-tts returned no words")
    return words, dur

def _piper(text, path):
    wav = pathlib.Path(path).with_suffix(".wav")
    subprocess.run(["python", "-m", "piper", "-m", PIPER_MODEL, "--length-scale", "0.9", "-f", str(wav)],
                   input=text.encode(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(str(wav)) as w:
        dur = w.getnframes() / w.getframerate()
    toks = text.split(); total = sum(len(t) for t in toks); t0, words = 0.0, []
    for t in toks:  # estimate word timing proportional to length
        d = dur * len(t) / total; words.append((t, t0, t0 + d)); t0 += d
    return words, dur, wav

def speak(text, path):
    """Returns (words, duration, audio_path)."""
    for _ in range(3):
        try:
            w, d = asyncio.run(_edge(text, path)); return w, d, path
        except Exception as e:
            err = e
    print("edge-tts failed, using Piper:", type(err).__name__)
    return _piper(text, path)
