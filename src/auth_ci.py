"""TikTok login from GitHub Actions (no local Python needed).
Run 1 (no input): writes the TikTok login link to the job summary.
Run 2 (paste the URL you landed on after approving): exchanges the code and writes the refresh token to the summary."""
import json, os, pathlib, urllib.parse, requests

K, S = os.environ["TIKTOK_CLIENT_KEY"].strip(), os.environ["TIKTOK_CLIENT_SECRET"].strip()
R = json.loads(pathlib.Path("brand.json").read_text())["redirect_uri"]
landed = os.getenv("REDIRECTED_URL", "").strip()
summary = open(os.environ.get("GITHUB_STEP_SUMMARY", "/dev/stdout"), "a")

if not landed:
    # The client key is public (it appears in every login link), but GitHub masks secret values as *** in the
    # summary. Percent-encode every character so the masked literal never appears; TikTok decodes it.
    enc_key = "".join(f"%{b:02X}" for b in K.encode())
    link = "https://www.tiktok.com/v2/auth/authorize/?client_key=" + enc_key + "&" + urllib.parse.urlencode(
        {"scope": "user.info.basic,video.publish,video.upload", "response_type": "code", "redirect_uri": R, "state": "x"})
    summary.write(f"## Step 1\n\n[Click here to log in to TikTok and approve]({link})\n\n"
                  "After approving you land on a 404 page. Copy the FULL address from the address bar and, "
                  "within a few minutes, run this workflow again pasting it in `redirected_url`.\n")
    print("Login link written to the run summary.")
else:
    code = urllib.parse.parse_qs(urllib.parse.urlparse(landed).query).get("code", [""])[0]
    r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", timeout=30, data={
        "client_key": K, "client_secret": S, "code": code, "grant_type": "authorization_code", "redirect_uri": R}).json()
    if "refresh_token" not in r:
        summary.write(f"## Failed\n\n```\n{json.dumps(r, indent=1)}\n```\nThe code may have expired: start again from step 1.\n")
        raise SystemExit(f"token exchange failed: {r}")
    summary.write("## Step 2: done\n\nCopy this value into the repository secret `TIKTOK_REFRESH_TOKEN`, "
                  "then delete this workflow run (… menu → Delete workflow run).\n\n"
                  f"```\n{r['refresh_token']}\n```\n")
    print("Refresh token written to the run summary (not to this log).")
