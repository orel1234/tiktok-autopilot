"""YouTube login from GitHub Actions, same two-run flow as tiktok-login.
Run 1 (empty input): writes the Google login link to the summary. Run 2 (paste the URL you landed on):
writes the refresh token to the summary."""
import json, os, pathlib, urllib.parse, requests

CID, CS = os.environ["YOUTUBE_CLIENT_ID"].strip(), os.environ["YOUTUBE_CLIENT_SECRET"].strip()
R = json.loads(pathlib.Path("brand.json").read_text())["redirect_uri"]
landed = os.getenv("REDIRECTED_URL", "").strip()
summary = open(os.environ.get("GITHUB_STEP_SUMMARY", "/dev/stdout"), "a")
if not landed:
    enc = "".join(f"%{b:02X}" for b in CID.encode())  # avoid GitHub masking the (public) client id
    link = "https://accounts.google.com/o/oauth2/v2/auth?client_id=" + enc + "&" + urllib.parse.urlencode({
        "redirect_uri": R, "response_type": "code", "access_type": "offline", "prompt": "consent",
        "scope": "https://www.googleapis.com/auth/youtube.upload"})
    summary.write(f"## Step 1\n\n[Click here to log in to YouTube and approve]({link})\n\n"
                  "Pick the channel's Google account. If Google warns the app is unverified, choose Advanced, then continue. "
                  "On the page you land on press Copy, then within a few minutes run this workflow again pasting it in `redirected_url`.\n")
    print("Login link written to the run summary.")
else:
    code = urllib.parse.parse_qs(urllib.parse.urlparse(landed).query).get("code", [""])[0]
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": CID, "client_secret": CS, "code": code, "grant_type": "authorization_code", "redirect_uri": R}).json()
    if "refresh_token" not in r:
        summary.write(f"## Failed\n\n`{r.get('error')}`: {r.get('error_description', '')}\n\nStart again from step 1.\n")
        raise SystemExit("token exchange failed")
    summary.write("## Step 2: done\n\nSave this as the repository secret `YOUTUBE_REFRESH_TOKEN`, then delete this run.\n\n"
                  f"```\n{r['refresh_token']}\n```\n")
    print("Refresh token written to the run summary (not to this log).")
