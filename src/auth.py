"""One-time: get a TikTok refresh token. Usage: python src/auth.py  (needs CLIENT_KEY/SECRET env,
redirect URI http://localhost:8080/cb registered in your TikTok app)."""
import os, http.server, urllib.parse, webbrowser, requests
K, S, R = os.environ["TIKTOK_CLIENT_KEY"], os.environ["TIKTOK_CLIENT_SECRET"], "http://localhost:8080/cb"
print("Open:", u := "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode(
    {"client_key": K, "scope": "user.info.basic,video.publish,video.upload", "response_type": "code", "redirect_uri": R, "state": "x"}))
webbrowser.open(u)
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(s):
        code = urllib.parse.parse_qs(urllib.parse.urlparse(s.path).query).get("code", [""])[0]
        r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={"client_key": K, "client_secret": S,
            "code": code, "grant_type": "authorization_code", "redirect_uri": R}).json()
        print("\nTIKTOK_REFRESH_TOKEN =", r.get("refresh_token", r))
        s.send_response(200); s.end_headers(); s.wfile.write(b"done, check terminal")
http.server.HTTPServer(("", 8080), H).handle_request()
