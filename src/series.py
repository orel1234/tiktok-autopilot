"""Multi-part horror stories: plan the whole arc first (so it pays off), then write one part per run."""
import json, os, pathlib, random
import anthropic
from ideas import MODEL, BRAND, load_history

STATE = pathlib.Path("series.json")

PLAN_PROMPT = """Plan a short horror story told in first person by one narrator, to be released as {n} TikTok parts
(each part about 75-85 seconds when narrated, around 210 words). Setting seed: {seed}.
Topics already used (do not repeat): {used}

The story MUST have real substance and a satisfying payoff:
- a named narrator and 1-2 other named characters, a concrete place, and a clear central mystery or threat
- events that escalate in each part with specific, concrete incidents (not vague dread)
- a real reveal in the last part that explains what was actually happening, followed by a conclusive ending
  (what happens to the narrator) and a chilling last line. Do NOT end on an open question.
- parts 1..{m} must each end on a strong cliffhanger; the final part resolves everything
- original fiction, no gore, no real people or places, nothing graphic

Return ONLY JSON:
{{"title": str (<=70 chars, no hashtags), "hashtags": [str x4 no #],
 "characters": str, "setting": str,
 "parts": [{{"events": str (what happens, concrete, 3-5 beats), "cliffhanger": str (last beat; for the final part: the ending)}} x {n}],
 "reveal": str}}"""

PART_PROMPT = """You are writing part {k} of {n} of a first-person horror TikTok story, narrated calmly, getting darker.
Title: {title}. Characters: {characters}. Setting: {setting}. Secret reveal (final part only): {reveal}

Full plan:
{plan}

{prev}
Write part {k} following its plan exactly, with concrete incidents and dialogue snippets.
{opening}
{ending}
About 200-220 words of narration in total (roughly 75-85 seconds spoken), in 8-10 scenes. Each scene: 1-2 short sentences of narration + a 2-3 word stock-footage search that is moody and
concrete (dark hallway, foggy forest, empty street at night). Do not add any sign-off line; it is added automatically.
Return ONLY JSON: {{"scenes": [{{"narration": str, "query": str}}]}}"""

def _ask(prompt, max_tokens=16000, tries=3):
    """Call Claude and parse the JSON object in its reply; retry if the reply has no usable JSON."""
    for i in range(tries):
        msg = anthropic.Anthropic().messages.create(model=MODEL, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}])
        t = "".join(b.text for b in msg.content if b.type == "text")
        try:
            return json.loads(t[t.index("{"): t.rindex("}") + 1])
        except ValueError:
            print(f"Claude reply #{i+1} had no valid JSON (stop_reason={msg.stop_reason}): {t[:300]!r}")
    raise RuntimeError("Claude did not return valid JSON")

def new_plan(n=5):
    seed = random.choice(["a night-shift job with strange rules", "a house I just moved into", "a road trip detour",
        "a baby monitor / smart home device", "an old family video tape", "a remote cabin rental",
        "a hospital or hotel at night", "a neighbour who never leaves the house"])
    plan = _ask(PLAN_PROMPT.format(n=n, m=n - 1, seed=seed, used=load_history()[-40:]))
    plan["n"] = n
    return plan

def write_part(plan, k, last_narration=""):
    n = plan["n"]
    prev = (f"Part {k-1} ended with: \"{last_narration}\"" if k > 1 else "")
    opening = ("Open with a very strong, unsettling hook in the first sentence." if k == 1 else
               f"Open with one short recap sentence ('Last time...') then continue straight away. Part {k-1} cliffhanger: {plan['parts'][k-2]['cliffhanger']}")
    ending = ("This is the FINAL part: deliver the full reveal, resolve the mystery and the narrator's fate, "
              "and end on a conclusive chilling last line." if k == n else
              "End on the cliffhanger from the plan: stop right at the most suspenseful moment.")
    s = _ask(PART_PROMPT.format(k=k, n=n, title=plan["title"], characters=plan["characters"], setting=plan["setting"],
        reveal=plan["reveal"], plan=json.dumps(plan["parts"], indent=1), prev=prev, opening=opening, ending=ending))
    outro = (f"Follow so you don't miss part {k+1}." if k < n else "And that's how it ended. Follow for the next story.")
    s["scenes"].append({"narration": outro, "query": "dark forest night"})
    s["format"] = "horror"
    s["topic"] = plan["title"] if k == 1 else None
    s["title"] = f"{plan['title']} (Part {k}/{n})"
    s["hashtags"] = list(dict.fromkeys(plan["hashtags"] + ["horror", "storytime", f"part{k}"]))
    s["last_narration"] = s["scenes"][-2]["narration"]
    return s

def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else None

def save_state(plan, next_part, last_narration):
    STATE.write_text(json.dumps({"plan": plan, "next_part": next_part, "last_narration": last_narration}, indent=1))

def clear_state():
    STATE.unlink(missing_ok=True)
