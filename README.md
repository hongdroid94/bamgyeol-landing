# 밤결 landing

Static landing page for the 밤결 sleep-sound app.

- `src/` page source, `build.py` assembles `site/` (icon sprite, sound windows, font subsets, OG image).
- `python3 build.py https://<domain>` then commit `site/`. Vercel serves `site/` as-is.
