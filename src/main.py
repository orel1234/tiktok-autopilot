import argparse, json, pathlib, random, time
from ideas import new_script, save_history, FORMATS, BRAND
from render import build
from publish import post
import series

ap = argparse.ArgumentParser()
ap.add_argument("--no-publish", action="store_true", help="render only")
ap.add_argument("--format", default="random", choices=["random", "all", *FORMATS])
a = ap.parse_args()

out = pathlib.Path("out"); out.mkdir(exist_ok=True)

def make(script, tag):
    mp4 = out / f"{tag}-{int(time.time())}.mp4"
    dur = build(script, out / f"work-{tag}", str(mp4))
    print(f"Rendered {mp4} ({dur:.0f}s)")
    (out / f"{tag}.json").write_text(json.dumps(script, indent=1))
    return mp4

def publish(script, mp4):
    caption = script["title"] + " " + " ".join("#" + h.lstrip("#") for h in script["hashtags"])
    print("Published, id:", post(str(mp4), caption))

fmts = list(FORMATS) if a.format == "all" else [random.choice(BRAND["enabled_formats"]) if a.format == "random" else a.format]
for fmt in fmts:
    if fmt == "horror" and a.no_publish:
        # test mode: render the WHOLE story arc (all parts) so you can judge the ending; no state is saved
        plan = series.new_plan(); print("[horror] Story:", plan["title"]); last = ""
        for k in range(1, plan["n"] + 1):
            s = series.write_part(plan, k, last); last = s["last_narration"]
            make(s, f"horror-part{k}")
    elif fmt == "horror":
        st = series.load_state()
        plan, k, last = (st["plan"], st["next_part"], st["last_narration"]) if st else (series.new_plan(), 1, "")
        s = series.write_part(plan, k, last)
        print(f"[horror] {plan['title']} part {k}/{plan['n']}")
        publish(s, make(s, f"horror-part{k}"))
        if k == 1: save_history(plan["title"])
        series.save_state(plan, k + 1, s["last_narration"]) if k < plan["n"] else series.clear_state()
    else:
        script = new_script(fmt)
        print(f"[{fmt}] Topic:", script["topic"])
        mp4 = make(script, fmt)
        if not a.no_publish:
            publish(script, mp4)
        save_history(script["topic"])
