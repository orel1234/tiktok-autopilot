"""One-time: get a TikTok refresh token (no local server needed).
Needs TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET in the environment. brand.json "redirect_uri" must be registered
in your TikTok app. After you approve, the browser lands on that URL (a 404 page is fine): copy the FULL address
from the address bar and paste it here."""
import json, os, pathlib, urllib.parse, requests
K, S = os.environ["TIKTOK_CLIENT_KEY"], os.environ["TIKTOK_CLIENT_SECRET"]
R = json.loads(pathlib.Path("brand.json").read_text())["redirect_uri"]
print("1) Open this link, log in with the TikTok account and approve:\n\n" + "https://www.tiktok.com/v2/auth/authorize/?" +
      urllib.parse.urlencode({"client_key": K, "scope": "user.info.basic,video.publish,video.upload",
                              "response_type": "code", "redirect_uri": R, "state": "x"}))
url = input("\n2) Paste the full URL you were redirected to: ").strip()
code = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["code"][0]
r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={"client_key": K, "client_secret": S,
    "code": code, "grant_type": "authorization_code", "redirect_uri": R}).json()
print("\nTIKTOK_REFRESH_TOKEN =", r.get("refresh_token", r))
