from __future__ import annotations

import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


API_BASE = "https://api.weixin.qq.com/cgi-bin"


class WeChatApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class WeChatCredentials:
    app_id: str
    app_secret: str


def credentials_from_env() -> WeChatCredentials:
    app_id = os.getenv("WECHAT_APP_ID", "").strip()
    app_secret = os.getenv("WECHAT_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        raise WeChatApiError("WECHAT_APP_ID and WECHAT_APP_SECRET are required.")
    return WeChatCredentials(app_id=app_id, app_secret=app_secret)


def get_access_token(credentials: WeChatCredentials) -> str:
    query = urllib.parse.urlencode(
        {
            "grant_type": "client_credential",
            "appid": credentials.app_id,
            "secret": credentials.app_secret,
        }
    )
    payload = _request_json("GET", f"{API_BASE}/token?{query}")
    token = payload.get("access_token")
    if not token:
        raise WeChatApiError(f"WeChat token response did not include access_token: {payload}")
    return str(token)


def build_draft_payload(
    title: str,
    author: str,
    digest: str,
    html: str,
    thumb_media_id: str,
    source_url: str = "",
) -> dict[str, Any]:
    article: dict[str, Any] = {
        "title": title[:64],
        "author": author[:8],
        "digest": digest[:120],
        "content": html,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }
    if source_url:
        article["content_source_url"] = source_url
    return {"articles": [article]}


def add_draft(access_token: str, payload: dict[str, Any]) -> str:
    query = urllib.parse.urlencode({"access_token": access_token})
    response = _request_json("POST", f"{API_BASE}/draft/add?{query}", payload)
    media_id = response.get("media_id")
    if not media_id:
        raise WeChatApiError(f"WeChat draft response did not include media_id: {response}")
    return str(media_id)


def upload_permanent_image(access_token: str, image_path: Path) -> str:
    if not image_path.exists():
        raise WeChatApiError(f"Cover image does not exist: {image_path}")

    query = urllib.parse.urlencode({"access_token": access_token, "type": "image"})
    response = _request_multipart(
        f"{API_BASE}/material/add_material?{query}",
        field_name="media",
        file_path=image_path,
    )
    media_id = response.get("media_id")
    if not media_id:
        raise WeChatApiError(f"WeChat material response did not include media_id: {response}")
    return str(media_id)


def _request_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise WeChatApiError(f"WeChat API request failed: {exc}") from exc

    parsed = json.loads(body)
    _raise_for_wechat_error(parsed)
    return parsed


def _request_multipart(url: str, field_name: str, file_path: Path) -> dict[str, Any]:
    boundary = f"----wechat-news-publisher-{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    file_bytes = file_path.read_bytes()
    body = b"".join(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{file_path.name}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            file_bytes,
            f"\r\n--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise WeChatApiError(f"WeChat image upload failed: {exc}") from exc

    parsed = json.loads(response_body)
    _raise_for_wechat_error(parsed)
    return parsed


def _raise_for_wechat_error(payload: dict[str, Any]) -> None:
    error_code = int(payload.get("errcode", 0) or 0)
    if error_code != 0:
        raise WeChatApiError(f"WeChat API error {error_code}: {payload.get('errmsg', payload)}")
