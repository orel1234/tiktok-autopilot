"""Ask Claude for a fresh script in one of several formats, avoiding topics already used."""
import json, os, pathlib, random
import anthropic

HISTORY = pathlib.Path("history.json")
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
BRAND = json.loads(pathlib.Path("brand.json").read_text())

NICHES = [
    "everyday things that are secretly dangerous or that you are doing wrong",
    "money, scams and consumer traps people fall for",
    "weird things your body and brain do (sleep, memory, pain, fear)",
    "dark or shocking true history and forgotten events",
    "internet, phones, apps and tech that quietly track or trick you",
    "animals and nature that are way more terrifying or smart than you think",
    "food and drink myths and what is really in them",
    "psychology tricks that manipulate how people think and buy",
    "unbelievable jobs, laws and rules around the world",
    "survival and what-would-happen-if scenarios",
]
HOWTO = [
    "how an everyday object or technology really works inside",
    "how a huge building, bridge, dam or machine is actually built",
    "how something you use every day is made in a factory",
    "how a famous disaster or failure happened, step by step",
    "how a common scam or trick actually works, so viewers can protect themselves",
]

FORMATS = {
    "facts": dict(
        topic=lambda: random.choice(NICHES),
        brief="""a "fun facts / explainer" video. Niche: {topic}.
Brainstorm 10 hooks, pick the most clickable one (specific, personally relevant, open loop; e.g.
"You would NOT want to find this out the hard way"). Then: hook as the first sentence, 4-6 surprising TRUE
verifiable facts that escalate, a payoff. Avoid generic trivia. No medical/financial advice."""),
    "horror": dict(
        topic=lambda: random.choice(["a creepy true-feeling story told in first person", "a short chilling story with a twist ending",
                                     "a 'something is wrong in my house' mystery", "a late-night encounter that goes wrong",
                                     "a strange rule/warning story (e.g. a night-shift job with weird rules)"]),
        brief="""a scary short story told in first person, narrated calmly, getting darker. Style: {topic}.
Brainstorm 10 opening lines, pick the most unsettling. Build tension scene by scene, end on a twist or a
chilling last line. Original fiction (do not claim it is a true story). No gore, no real people or places, nothing graphic.
Visual queries should be moody and concrete (dark hallway, foggy forest, empty street at night)."""),
    "howto": dict(
        topic=lambda: random.choice(HOWTO),
        brief="""a "how it works / how it is built" explainer. Subject area: {topic}.
Brainstorm 10 specific subjects with a surprising angle, pick the best. Explain it step by step in plain words,
with 4-6 steps that each reveal something surprising, and a payoff. Accurate and verifiable only."""),
}

PROMPT = """You write viral 75-90 second TikTok scripts (target 75-90 seconds spoken, about 220 words) for a US audience, for the brand "{brand}".
Write {brief}

Topics already used (do NOT repeat or paraphrase): {used}

Return ONLY JSON:
{{"candidates": [str x10], "topic": str, "title": str (<=90 chars, no hashtags),
 "hashtags": [str, ...] (4-5, no #),
 "scenes": [{{"narration": str (1-2 short sentences), "query": str (2-3 word stock-footage search, concrete & visual)}}]}}
Use 8-11 scenes, about 220 words of narration in total. Do not write a sign-off line: the brand outro is added automatically."""

def load_history():
    return json.loads(HISTORY.read_text()) if HISTORY.exists() else []

def save_history(topic):
    h = load_history(); h.append(topic); HISTORY.write_text(json.dumps(h[-300:], indent=1))

def new_script(fmt="facts"):
    f = FORMATS[fmt]
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL, max_tokens=8000,
        messages=[{"role": "user", "content": PROMPT.format(
            brand=BRAND["name"], brief=f["brief"].format(topic=f["topic"]()), used=load_history()[-60:])}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    s = json.loads(text[text.index("{"): text.rindex("}") + 1])
    s["format"] = fmt
    s["scenes"].append({"narration": BRAND["outro"], "query": "city night lights"})  # signature outro
    s["hashtags"] = list(dict.fromkeys(s["hashtags"] + [fmt if fmt != "howto" else "howitworks"]))
    return s
