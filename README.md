# WeChat News Publisher

Daily automation for collecting public AI/game news feeds and publishing a static digest website.

The GitHub Actions workflow only generates the website for GitHub Pages. WeChat draft and publish support remains available for local runs or a fixed-IP server.

## What It Does

1. GitHub Actions runs every day at 09:00 Asia/Shanghai.
2. The script reads `sources.yml` and fetches RSS/Atom feeds.
3. Items are filtered by `keywords`, deduplicated, ranked, and rendered to HTML.
4. The workflow generates HTML output in dry-run mode, so it does not call WeChat APIs.
5. The latest HTML file is published as the GitHub Pages homepage for `news.gongganghao.com`.
6. Generated files are uploaded as a GitHub Actions artifact.

## Upload To GitHub

Upload the contents of this folder as the repository root:

```text
.github/
config.yml
sources.yml
src/
tests/
README.md
requirements.txt
```

If you keep this folder inside another repository as a subfolder, move `.github/workflows/daily.yml` to the repository root and adjust the workflow commands.

## GitHub Secrets

GitHub Actions does not need WeChat secrets when it is only generating the website.

For local runs or a fixed-IP server that should create/publish WeChat articles, configure these environment variables:

```text
WECHAT_APP_ID
WECHAT_APP_SECRET
```

Optional:

```text
WECHAT_THUMB_MEDIA_ID
```

`WECHAT_THUMB_MEDIA_ID` is recommended. Create or upload a reusable cover image in the WeChat Official Account backend/API and put its media id here. If it is missing, the script tries to upload a tiny default cover image as permanent image material.

Do not commit AppSecret, access tokens, cookies, QR codes, or account passwords.

## WeChat Setup Notes

WeChat publishing should run from a stable outbound IP that is in the WeChat Official Account IP whitelist. GitHub-hosted runner IPs can change, so the GitHub Actions workflow uses `--dry-run` and does not call WeChat APIs.

The script uses the WeChat Official Account APIs for access token, permanent image material upload, draft creation, and optional publishing:

- Access token: <https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Get_access_token.html>
- Draft box: <https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html>
- Permanent material: <https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/Adding_Permanent_Assets.html>
- Publish: <https://developers.weixin.qq.com/doc/offiaccount/Publish/Publish.html>

## Configure Sources

Edit `sources.yml`:

```yaml
sources:
  - name: "OpenAI News"
    url: "https://openai.com/news/rss.xml"
    category: "ai"
    enabled: true
```

Use RSS or Atom feed URLs. Normal web pages are not parsed in this version.

## Configure Ranking

Edit `config.yml`:

```yaml
max_items: 12
lookback_hours: 36
keywords:
  - AI
  - game
  - Unity
exclude_keywords:
  - giveaway
```

Items matching `exclude_keywords` are skipped. Items with more title/summary keyword matches rank higher.

## Run Locally

From this folder:

```bash
python -m unittest discover -s tests -v
python src/main.py --config config.yml --sources sources.yml --output output --dry-run
```

The dry run writes `output/YYYY-MM-DD.html` without calling WeChat.

## Enable Or Disable WeChat Publishing

In `config.yml`:

```yaml
wechat:
  create_draft: true
  auto_publish: true
```

Set `create_draft` to `false` if you only want artifacts and no WeChat API calls.
Set `auto_publish` to `false` if you want the article to stop in the draft box instead of publishing to the public article list.

## Compliance Boundary

This project does not automate login, bypass captcha, scrape private APIs, or reuse Douyin/Xiaohongshu cookies. Add those platforms only through official, authorized, or public feed/API sources.
