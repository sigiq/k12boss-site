"""Assemble dist/ for static hosting from src/page.html and assets/.

src/page.html is written so it can also be previewed on its own: it starts with
<title> and <style>, then the body markup. Here we wrap it in a full document
with production meta tags.
"""
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "page.html")
DIST = os.path.join(ROOT, "dist")
SITE_URL = os.environ.get("SITE_URL", "https://k12boss.com")
NOTIFY_ENDPOINT = os.environ.get("NOTIFY_ENDPOINT", "")

TITLE = "K12 BOSS · A podcast about K-12 students building with AI"
DESCRIPTION = (
    "The ceiling is gone. K12 BOSS is a podcast for educators about the biggest "
    "opportunity for student success right now: building real software with AI. "
    "Hosted by Dr. Kartik Mangalam and Dr. Matt Callison. Episode 1 drops November 15, 2026."
)

HEAD = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{TITLE}</title>
<meta name="description" content="{DESCRIPTION}">
<link rel="canonical" href="{SITE_URL}/">
<meta name="theme-color" content="#FFC21A">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="K12 BOSS">
<meta property="og:url" content="{SITE_URL}/">
<meta property="og:title" content="K12 BOSS · The ceiling is gone.">
<meta property="og:description" content="{DESCRIPTION}">
<meta property="og:image" content="{SITE_URL}/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="K12 BOSS · The ceiling is gone.">
<meta name="twitter:description" content="{DESCRIPTION}">
<meta name="twitter:image" content="{SITE_URL}/assets/og-image.png">
"""


def main():
    page = open(SRC, encoding="utf-8").read()
    page = re.sub(r"<title>.*?</title>\s*", "", page, count=1, flags=re.S)
    page = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\s*', "", page, count=1)
    if NOTIFY_ENDPOINT:
        page = re.sub(r'var NOTIFY_ENDPOINT = "[^"]*";', f'var NOTIFY_ENDPOINT = "{NOTIFY_ENDPOINT}";', page, count=1)
    split = page.index("<header")
    head_extra, body = page[:split], page[split:]
    html = HEAD + head_extra + "</head>\n<body>\n" + body + "</body>\n</html>\n"

    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "assets"))
    with open(os.path.join(DIST, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    for name in os.listdir(os.path.join(ROOT, "assets")):
        if name.startswith("cover-"):
            continue  # podcast cover art is for directories, not the site
        shutil.copy(os.path.join(ROOT, "assets", name), os.path.join(DIST, "assets", name))
    with open(os.path.join(DIST, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    with open(os.path.join(DIST, "sitemap.xml"), "w") as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"<url><loc>{SITE_URL}/</loc></url></urlset>\n"
        )
    print("built", os.path.relpath(DIST, ROOT), sorted(os.listdir(os.path.join(DIST, "assets"))))


if __name__ == "__main__":
    main()
