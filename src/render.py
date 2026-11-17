"""Assemble scenes into a 1080x1920 mp4 with word-highlight burned-in captions (ffmpeg)."""
import pathlib, subprocess
from tts import speak
from visuals import fetch_clip
import json
BRAND = json.loads(pathlib.Path('brand.json').read_text())

def _t(s):  # ASS timestamp
    h, m = int(s // 3600), int(s % 3600 // 60)
    return f"{h}:{m:02d}:{s % 60:05.2f}"

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV
Style: Default,DejaVu Sans,96,&H00FFFFFF,&H00000000,&H80000000,1,1,8,2,5,60,60,0
Style: Mark,DejaVu Sans,44,&H99FFFFFF,&H00000000,&H80000000,1,1,3,1,8,40,40,150
[Events]
Format: Layer,Start,End,Style,Name,Text
"""

def run(*a):
    subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def build(script, workdir, out_path):
    wd = pathlib.Path(workdir); wd.mkdir(parents=True, exist_ok=True)
    used, segs, words_all, t0 = set(), [], [], 0.0
    for i, sc in enumerate(script["scenes"]):
        a = wd / f"a{i}.mp3"; words, dur, a = speak(sc["narration"], a); dur += 0.25
        c = wd / f"c{i}.mp4"
        if not fetch_clip(sc["query"], c, used):
            fetch_clip("abstract background", c, used)
        seg = wd / f"s{i}.mp4"
        run("ffmpeg", "-y", "-stream_loop", "-1", "-i", c, "-i", a, "-t", f"{dur:.2f}",
            "-filter_complex", "[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5[bg];"
            "[b]scale=1080:-2:force_original_aspect_ratio=decrease,setsar=1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,fps=30[v]",
            "-map", "[v]", "-map", "1:a",
            "-af", "apad", "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-ar", "44100", "-ac", "2", seg)
        segs.append(seg)
        words_all += [(w, s + t0, e + t0) for w, s, e in words]; t0 += dur
    lst = wd / "list.txt"; lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segs))
    # captions: 3-word groups, each word highlighted as spoken
    ev = []
    for g in range(0, len(words_all), 3):
        grp = words_all[g:g + 3]
        for k, (w, s, e) in enumerate(grp):
            end = grp[k + 1][1] if k + 1 < len(grp) else e
            txt = " ".join((f"{{\\c&H{BRAND['highlight_color_bgr']}&}}{x.upper()}{{\\c&HFFFFFF&}}" if j == k else x.upper())
                           for j, (x, _, _) in enumerate(grp))
            ev.append(f"Dialogue: 0,{_t(s)},{_t(end)},Default,,{txt}")
    ev.append(f"Dialogue: 1,{_t(0)},{_t(t0)},Mark,,{BRAND['watermark']}")
    ass = wd / "cap.ass"; ass.write_text(ASS_HEAD + "\n".join(ev))
    run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-vf", f"ass={ass}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "copy", "-movflags", "+faststart", out_path)
    return t0
