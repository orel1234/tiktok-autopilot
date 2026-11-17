import argparse, json, pathlib, time
from ideas import new_script, save_history
from render import build
from publish import post

ap = argparse.ArgumentParser()
ap.add_argument("--no-publish", action="store_true", help="render only")
a = ap.parse_args()

script = new_script()
print("Topic:", script["topic"])
out = pathlib.Path("out"); out.mkdir(exist_ok=True)
mp4 = out / f"{int(time.time())}.mp4"
dur = build(script, out / "work", str(mp4))
print(f"Rendered {mp4} ({dur:.0f}s)")
(out / "script.json").write_text(json.dumps(script, indent=1))
if not a.no_publish:
    caption = script["title"] + " " + " ".join("#" + h.lstrip("#") for h in script["hashtags"])
    print("Published, id:", post(str(mp4), caption))
save_history(script["topic"])
