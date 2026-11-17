"""Ask Claude for a fresh "fun facts" script, avoiding topics already used."""
import json, os, pathlib, random
import anthropic

HISTORY = pathlib.Path("history.json")
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")

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

PROMPT = """You write viral 60-75 second TikTok scripts for the US audience in the "fun facts / explainer" style.
Niche for this video: {niche}.

Step 1: brainstorm 10 candidate hooks. A great hook is specific, makes the viewer feel they
might be personally affected or missing a secret, and creates an open loop. Examples of the
feel: "You would NOT want to find this out the hard way", "Never do this with your phone at night",
"This is why hotels really remove...". Avoid generic trivia like "Did you know space is big".
Step 2: pick the single most clickable hook and write the script for it:
the hook as the first sentence, 4-6 surprising TRUE verifiable facts that escalate, a payoff,
and a last line inviting comments. Original wording. No medical/financial advice, nothing you are unsure of.

Topics already used (do NOT repeat or paraphrase): {used}

Return ONLY JSON:
{{"candidates": [str x10], "topic": str, "title": str (<=90 chars, no hashtags),
 "hashtags": [str, ...] (4-5, no #),
 "scenes": [{{"narration": str (1-2 short sentences), "query": str (2-3 word stock-footage search, concrete & visual)}}]}}
Use 10-14 scenes."""

def load_history():
    return json.loads(HISTORY.read_text()) if HISTORY.exists() else []

def save_history(topic):
    h = load_history(); h.append(topic); HISTORY.write_text(json.dumps(h[-300:], indent=1))

def new_script():
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL, max_tokens=8000,
        messages=[{"role": "user", "content": PROMPT.format(niche=random.choice(NICHES), used=load_history()[-60:])}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    return json.loads(text[text.index("{"): text.rindex("}") + 1])
