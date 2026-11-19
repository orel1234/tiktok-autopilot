"""Keep each part of a running series as an asset on a GitHub release, so the last run can join them."""
import os, requests

API = "https://api.github.com"

def _h(extra=None):
    return {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json", **(extra or {})}

def _repo():
    return os.environ["GITHUB_REPOSITORY"]

def enabled():
    return bool(os.getenv("GITHUB_TOKEN") and os.getenv("GITHUB_REPOSITORY"))

def create_release(tag, title):
    r = requests.post(f"{API}/repos/{_repo()}/releases", headers=_h(), timeout=30, json={
        "tag_name": tag, "name": title, "body": "Parts of a running series (deleted after the full video is made).",
        "draft": False, "prerelease": True})
    r.raise_for_status()
    return r.json()["id"]

def upload_part(release_id, path, name):
    with open(path, "rb") as f:
        r = requests.post(f"https://uploads.github.com/repos/{_repo()}/releases/{release_id}/assets?name={name}",
                          headers=_h({"Content-Type": "video/mp4"}), data=f, timeout=600)
    r.raise_for_status()
    return r.json()["id"]

def download_part(asset_id, dest):
    r = requests.get(f"{API}/repos/{_repo()}/releases/assets/{asset_id}", timeout=600, stream=True,
                     headers=_h({"Accept": "application/octet-stream"}))
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(1 << 20):
            f.write(chunk)

def delete_release(release_id, tag):
    requests.delete(f"{API}/repos/{_repo()}/releases/{release_id}", headers=_h(), timeout=30)
    requests.delete(f"{API}/repos/{_repo()}/git/refs/tags/{tag}", headers=_h(), timeout=30)
