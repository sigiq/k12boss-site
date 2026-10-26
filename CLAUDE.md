# K12 BOSS website

Landing page for the K12 BOSS podcast at https://k12boss.com. Hosts: Dr. Kartik Mangalam and Dr. Matt Callison.
K12 BOSS = Biggest Opportunity for Student Success. Episode 1 launches November 15, 2026.

## How changes go live
- Edit `src/page.html` (copy, styles and script are all in this one file).
- Merging or pushing to `main` deploys automatically through `.github/workflows/deploy.yml`
  (build → S3 → CloudFront cache refresh → Route 53). Live in about a minute.
- Pull requests only run the build check; nothing deploys until it's on `main`.
- Check locally: `python3 tools/build.py`, then open `dist/index.html`.

## Don't
- Don't edit `dist/` (generated) or `.deploy-state/` (IDs of the live AWS resources; deploys depend on them).
- Don't add AWS keys anywhere. CI signs in to AWS through GitHub OIDC.
- Don't change the bucket name, domain or CloudFront settings without Kartik.

## Writing rules for the page
- Plain, direct sentences. Avoid phrases that read as AI-written ("sit with it", "it's worth noting",
  em-dash asides, "not X, but Y" framing).
- Use "Dr." for both hosts. Don't use the word "equity".
- Lead with ambition and possibility, not fear.
- Signup forms post to a Google Apps Script web app (`NOTIFY_ENDPOINT` in `src/page.html`) that writes to the
  "K12 BOSS — Website Signups" sheet. `tools/signup-sheet.gs` is the script source.

## Brand
- Colors: school-bus yellow `#FFC21A`, ink `#15161B`, paper `#F3F4EF`, red pen `#CF321A`.
- Fonts: Big Shoulders Display (headlines), Atkinson Hyperlegible (body), IBM Plex Mono (labels).
- Logos and cover art in `assets/`. Regenerate with `python3 tools/make_logos.py` and `node tools/render_art.js`.
