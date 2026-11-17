"""Free neural TTS (edge-tts) with word-level timings for captions."""
import asyncio, edge_tts

VOICE = "en-US-AndrewNeural"

async def _speak(text, path):
    words, dur = [], 0.0
    comm = edge_tts.Communicate(text, VOICE, rate="+8%", boundary="WordBoundary")
    with open(path, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                s, d = ch["offset"] / 1e7, ch["duration"] / 1e7
                words.append((ch["text"], s, s + d)); dur = s + d
    return words, dur

def speak(text, path):
    return asyncio.run(_speak(text, path))
