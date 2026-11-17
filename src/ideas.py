"""Ask Claude for a fresh "fun facts" script, avoiding topics already used."""
import json, os, pathlib
import anthropic

HISTORY = pathlib.Path("history.json")
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")

PROMPT = """You write viral 45-60 second TikTok scripts in the "fun facts / explainer" style:
a punchy shocking hook in the first sentence ("You would NOT want to find this out the hard way"),
3-5 surprising, TRUE, verifiable facts, a payoff, and a closing line that invites comments.
Original wording only. No medical/financial advice, no claims you are unsure of.

Topics already used (do NOT repeat): {used}

Return ONLY JSON:
{{"topic": str, "title": str (<=90 chars, no hashtags),
 "hashtags": [str, ...] (4-5, no #),
 "scenes": [{{"narration": str (1-2 short sentences), "query": str (2-3 word stock-footage search, concrete & visual)}}]}}
Use 8-12 scenes."""

def load_history():
    return json.loads(HISTORY.read_text()) if HISTORY.exists() else []

def save_history(topic):
    h = load_history(); h.append(topic); HISTORY.write_text(json.dumps(h[-300:], indent=1))

def new_script():
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL, max_tokens=2000,
        messages=[{"role": "user", "content": PROMPT.format(used=load_history()[-60:])}],
    )
    text = msg.content[0].text
    return json.loads(text[text.index("{"): text.rindex("}") + 1])
