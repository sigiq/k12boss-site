# K12 BOSS landing page

Static site for k12boss.com. Launch: November 15, 2026.

- `src/page.html`: the page (copy, styles, script)
- `assets/`: logos, icons, share image, podcast cover art (`cover-3000.png`, `cover-1400.png`)
- `tools/build.py`: builds `dist/` for hosting
- `tools/deploy.sh`: deploys `dist/` to AWS (S3 + CloudFront + HTTPS certificate)
- `tools/signup-sheet.gs`: Google Apps Script that saves form signups to the "K12 BOSS — Website Signups" sheet
- `tools/make_logos.py`, `tools/render_art.js`: regenerate the brand assets

## Deploying

Push or merge to `main`. The GitHub Action in `.github/workflows/deploy.yml` builds the site and deploys it
to AWS (S3 + CloudFront, DNS in Route 53). It signs in to AWS through an IAM role that trusts only this
repo's `main` branch, so there are no AWS keys in GitHub.

`tools/deploy.sh` is what the Action runs. It can also be run by hand with AWS credentials that have the
`K12BossSiteDeploy` policy. `.deploy-state/` holds the IDs of the live AWS resources; keep it committed.
