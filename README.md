# TikTok Autopilot

Fully automatic "fun facts" TikTok videos: Claude writes the script → edge-tts voice → Pexels vertical stock footage →
ffmpeg render with word-highlight captions → TikTok Content Posting API. Runs on a GitHub Actions cron.

## Setup (once)
1. Keys: `ANTHROPIC_API_KEY`, `PIXABAY_API_KEY` (free at pixabay.com/api/docs; Pexels also supported).
2. Create an app at developers.tiktok.com, add **Content Posting API** (Direct Post) + Login Kit,
   redirect URI `http://localhost:8080/cb`. Run `python src/auth.py` once -> `TIKTOK_REFRESH_TOKEN`.
3. Put all keys in repo Secrets (see `.env.example`). Variable `TIKTOK_PRIVACY` = `SELF_ONLY` (default).
4. Submit the app for TikTok audit; until approved, API posts are private only. Then set `TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE`.

## Run locally
```
pip install -r requirements.txt && sudo apt install ffmpeg fonts-dejavu-core
python src/main.py --no-publish    # render only -> out/*.mp4
python src/main.py                 # render + post
```
## Money reality
Creator Rewards needs 1k followers, 10k views/30d, videos >1 min, US/eligible region, original content.
Mass-produced repetitive content is demonetized. Posts are flagged `is_aigc`. Add affiliate links in your bio.
