# WeChat News Publisher

Daily automation for collecting public AI/game news feeds and creating a WeChat Official Account draft or publishing it through the WeChat publish API.

By default this project can create a draft and submit it for publishing when WeChat credentials are configured.

## What It Does

1. GitHub Actions runs every day at 09:00 Asia/Shanghai.
2. The script reads `sources.yml` and fetches RSS/Atom feeds.
3. Items are filtered by `keywords`, deduplicated, ranked, and rendered to HTML/Markdown.
4. The script creates a WeChat Official Account draft when credentials are configured.
5. If `wechat.auto_publish` is enabled, the script submits the draft to the WeChat publish API.
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

Create these repository secrets in GitHub:

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

The script uses the WeChat Official Account APIs for access token, permanent image material upload, draft creation, and optional publishing:

- Access token: <https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Get_access_token.html>
- Draft box: <https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html>
- Permanent material: <https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/Adding_Permanent_Assets.html>
- Publish: <https://developers.weixin.qq.com/doc/offiaccount/Publish/Publish.html>

If your official account requires an IP whitelist, GitHub-hosted runner IPs can change. The workflow prints the current runner egress IP, but a fixed-egress self-hosted runner or cloud proxy is more stable for long-term use.

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

The dry run writes `output/YYYY-MM-DD.html` and `output/YYYY-MM-DD.md` without calling WeChat.

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
