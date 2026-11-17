import argparse, json, pathlib, random, time
from ideas import new_script, save_history, FORMATS
from render import build
from publish import post

ap = argparse.ArgumentParser()
ap.add_argument("--no-publish", action="store_true", help="render only")
ap.add_argument("--format", default="random", choices=["random", "all", *FORMATS])
a = ap.parse_args()

fmts = list(FORMATS) if a.format == "all" else [random.choice(list(FORMATS)) if a.format == "random" else a.format]
out = pathlib.Path("out"); out.mkdir(exist_ok=True)
for fmt in fmts:
    script = new_script(fmt)
    print(f"[{fmt}] Topic:", script["topic"])
    mp4 = out / f"{fmt}-{int(time.time())}.mp4"
    dur = build(script, out / f"work-{fmt}", str(mp4))
    print(f"Rendered {mp4} ({dur:.0f}s)")
    (out / f"{fmt}.json").write_text(json.dumps(script, indent=1))
    if not a.no_publish:
        caption = script["title"] + " " + " ".join("#" + h.lstrip("#") for h in script["hashtags"])
        print("Published, id:", post(str(mp4), caption))
    save_history(script["topic"])
