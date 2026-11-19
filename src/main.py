import argparse, json, pathlib, random, re, time
from ideas import new_script, save_history, FORMATS, BRAND
from render import build
from publish import post
import series, youtube, storage, compile as joiner

ap = argparse.ArgumentParser()
ap.add_argument("--no-publish", action="store_true", help="render only")
ap.add_argument("--format", default="random", choices=["random", "all", *FORMATS])
a = ap.parse_args()

out = pathlib.Path("out"); out.mkdir(exist_ok=True)

def make(script, tag):
    mp4 = out / f"{tag}-{int(time.time())}.mp4"
    total, durs = build(script, out / f"work-{tag}", str(mp4))
    print(f"Rendered {mp4} ({total:.0f}s)")
    (out / f"{tag}.json").write_text(json.dumps(script, indent=1))
    return mp4, {"total": total, "first": durs[0], "last": durs[-1]}

def hashtags(script):
    return " ".join("#" + h.lstrip("#") for h in script["hashtags"])

def publish(script, mp4):
    print("Published, id:", post(str(mp4), script["title"] + " " + hashtags(script)))

def to_youtube(path, title, description, tags, short):
    """YouTube is optional: skipped without keys, and a failure there never stops the TikTok post."""
    if not youtube.enabled():
        return
    try:
        youtube.upload(str(path), title, description, tags, short=short)
    except Exception as e:
        print("YouTube upload failed (TikTok post is not affected):", e)

def full_description(plan):
    return (f"{plan['title']}: the full story in one video. Original horror fiction, narrated.\n\n"
            f"Follow {BRAND['watermark']} for a new story every night.\n#horrorstory #scarystories #storytime")

fmts = list(FORMATS) if a.format == "all" else [random.choice(BRAND["enabled_formats"]) if a.format == "random" else a.format]
for fmt in fmts:
    if fmt == "horror" and a.no_publish:
        # test mode: render the WHOLE story (all parts) and the joined full video; nothing is posted or saved
        plan = series.new_plan(); print("[horror] Story:", plan["title"]); last = ""; parts = []
        for k in range(1, plan["n"] + 1):
            s = series.write_part(plan, k, last); last = s["last_narration"]
            mp4, info = make(s, f"horror-part{k}")
            parts.append({**info, "path": mp4})
        full = joiner.join(parts, out / "horror-full-story.mp4")
        print("Joined full story:", full)
    elif fmt == "horror":
        st = series.load_state() or {}
        plan, k = (st["plan"], st["next_part"]) if st else (series.new_plan(), 1)
        last, parts, release = st.get("last_narration", ""), st.get("parts", []), st.get("release")
        s = series.write_part(plan, k, last)
        print(f"[horror] {plan['title']} part {k}/{plan['n']}")
        mp4, info = make(s, f"horror-part{k}")
        publish(s, mp4)
        to_youtube(mp4, s["title"], f"{s['title']}\n\nFollow {BRAND['watermark']} for the next part. {hashtags(s)}",
                   s["hashtags"], short=True)
        if k == 1:
            save_history(plan["title"])
        # keep this part so the last run can join the whole story into one long video
        if storage.enabled() and youtube.enabled():
            try:
                if not release:
                    tag = "series-" + re.sub(r"[^a-z0-9]+", "-", plan["title"].lower()).strip("-")[:40] + f"-{int(time.time())}"
                    release = {"id": storage.create_release(tag, plan["title"]), "tag": tag}
                info["asset"] = storage.upload_part(release["id"], mp4, f"part{k}.mp4")
            except Exception as e:
                print("Could not store the part for the full video:", e)
        parts.append(info)
        if k < plan["n"]:
            series.save_state(plan, k + 1, s["last_narration"], parts, release)
        else:
            if release and all("asset" in p for p in parts):
                try:
                    for i, p in enumerate(parts):
                        p["path"] = out / f"stored-part{i+1}.mp4"
                        storage.download_part(p["asset"], p["path"])
                    full = joiner.join(parts, out / "horror-full-story.mp4")
                    to_youtube(full, f"{plan['title']} | Full Horror Story", full_description(plan),
                               plan["hashtags"] + ["horror story", "scary stories"], short=False)
                    storage.delete_release(release["id"], release["tag"])
                except Exception as e:
                    print("Full video failed:", e)
            series.clear_state()
    else:
        script = new_script(fmt)
        print(f"[{fmt}] Topic:", script["topic"])
        mp4, _ = make(script, fmt)
        if not a.no_publish:
            publish(script, mp4)
        save_history(script["topic"])
