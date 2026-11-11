"""Refresh the profile README assets from the self-hosted API.

Keeps whatever is already committed if the API is unreachable or has no data,
so the profile never shows a broken image.
"""
import json
import pathlib
import re
import sys
import urllib.request

API = "https://api.li-xiang.xyz"
ROOT = pathlib.Path(__file__).resolve().parents[2]


def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": "profile-readme-refresh"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def refresh_stats():
    if not json.loads(get("/stats/coding")).get("available"):
        print("stats unavailable, keeping current cards")
        return
    for theme in ("light", "dark"):
        svg = get(f"/stats/coding.svg?theme={theme}&lang=en")
        if not svg.lstrip().startswith(b"<svg"):
            raise ValueError("unexpected SVG response")
        (ROOT / "assets" / f"coding-stats-{theme}.svg").write_bytes(svg)


def refresh_posts():
    posts = json.loads(get("/posts/latest?lang=en&limit=5")).get("posts", [])
    if not posts:
        print("no posts returned, keeping current list")
        return
    lines = "\n".join(
        "- [{}]({}) <sub>{}</sub>".format(p["title"].replace("[", "(").replace("]", ")"), p["url"], p["date"])
        for p in posts
    )
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    new, n = re.subn(
        r"(<!-- BLOG-POSTS:START -->).*?(<!-- BLOG-POSTS:END -->)",
        lambda m: f"{m.group(1)}\n{lines}\n{m.group(2)}",
        text,
        flags=re.S,
    )
    if n == 1:
        readme.write_text(new, encoding="utf-8")


for step in (refresh_stats, refresh_posts):
    try:
        step()
    except Exception as err:  # API down: leave the committed files alone
        print(f"{step.__name__} skipped: {err}")
sys.exit(0)
