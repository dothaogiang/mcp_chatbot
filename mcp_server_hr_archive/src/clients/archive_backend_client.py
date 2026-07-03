from __future__ import annotations
import asyncio
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse, unquote

import httpx

from logger import get_logger
from config.settings import Settings
from common_utils.exceptions import (
    NotFoundError, BackendError, UnauthorizedError, ForbiddenError, BadRequestError,
)

log = get_logger(__name__)

_FILENAME_STAR_RE = re.compile(r"filename\*=UTF-8''([^;]+)", re.IGNORECASE)
_FILENAME_RE = re.compile(r'filename="?([^";]+)"?', re.IGNORECASE)


class ArchiveBackendClient:
    """Async httpx client cho Public Archives API.

    - Tự lấy `X-Chatbot-Token` khi có cấu hình CHATBOT_TOKEN_URL.
    - Chuẩn hoá lỗi backend thành exception nội bộ dùng chung.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(base_url=settings.BACKEND_BASE_URL, timeout=30.0)
        self._token: Optional[str] = None
        self._lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _ensure_token(self) -> None:
        if not self.settings.CHATBOT_TOKEN_URL or self._token:
            return
        async with self._lock:
            if self._token:
                return
            resp = await self._client.post(
                self.settings.CHATBOT_TOKEN_URL,
                json={
                    "clientId": self.settings.CHATBOT_CLIENT_ID,
                    "clientSecret": self.settings.CHATBOT_CLIENT_SECRET,
                },
            )
            resp.raise_for_status()
            self._token = resp.json().get("access_token")

    def _raise_for_error(self, resp: httpx.Response, treat_500_as_not_found: bool = False) -> None:
        message = resp.text
        try:
            body = resp.json()
            if isinstance(body, dict) and body.get("message"):
                message = body["message"]
        except Exception:
            pass

        code = resp.status_code
        if code == 400:
            raise BadRequestError(message)
        if code == 401:
            raise UnauthorizedError(message)
        if code == 403:
            raise ForbiddenError(message)
        if code == 404:
            raise NotFoundError(message)
        if code == 500 and treat_500_as_not_found:
            # Đã xác nhận qua test thật: /archives/{id} trả 500 khi ID không tồn tại
            # thay vì 404 như tài liệu ghi. Chỉ áp dụng quirk này ở nơi đã quan sát được,
            # KHÔNG áp dụng toàn cục để tránh che giấu lỗi 500 thật.
            raise NotFoundError(message)
        raise BackendError(f"[{code}] {message}")

    async def _request(
        self, method: str, url: str, *, treat_500_as_not_found: bool = False, **kwargs: Any,
    ) -> Any:
        await self._ensure_token()
        headers = kwargs.pop("headers", {}) or {}
        if self._token:
            headers["X-Chatbot-Token"] = self._token

        try:
            resp = await self._client.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            log.error("HTTP error calling backend %s %s: %s", method, url, exc)
            raise BackendError(str(exc)) from exc

        if resp.status_code >= 400:
            self._raise_for_error(resp, treat_500_as_not_found=treat_500_as_not_found)

        try:
            return resp.json()
        except Exception:
            return resp.content

    async def search_archives(self, params: Dict[str, Any]) -> Any:
        return await self._request("GET", "/api/public/archives", params=params)

    async def get_archive_detail(self, archive_id: str) -> Any:
        return await self._request(
            "GET", f"/api/public/archives/{archive_id}", treat_500_as_not_found=True,
        )

    async def get_staff_profiles(self) -> Any:
        return await self._request("GET", "/api/public/ho-so-can-bo")

    async def get_file_metadata(self, key: str) -> Dict[str, Any]:
        """Chỉ đọc header, KHÔNG tải nội dung file vào bộ nhớ."""
        await self._ensure_token()
        headers = {"X-Chatbot-Token": self._token} if self._token else {}
        async with self._client.stream(
            "GET", "/api/public/files/proxy", params={"key": key}, headers=headers,
        ) as resp:
            if resp.status_code >= 400:
                await resp.aread()
                self._raise_for_error(resp)
            return {
                "key": key,
                "filename": self._parse_filename(resp.headers.get("content-disposition")),
                "content_type": resp.headers.get("content-type"),
                "content_length": resp.headers.get("content-length"),
            }

    @staticmethod
    def _parse_filename(content_disposition: Optional[str]) -> Optional[str]:
        if not content_disposition:
            return None
        # Ưu tiên filename*=UTF-8''... (RFC 5987) — bắt buộc để đọc đúng tên file tiếng Việt
        m = _FILENAME_STAR_RE.search(content_disposition)
        if m:
            return unquote(m.group(1))
        m = _FILENAME_RE.search(content_disposition)
        return m.group(1) if m else None

    @staticmethod
    def extract_key_from_url(file_url: str) -> str:
        """https://host/bucket/projects/<uuid>/<file>.pdf -> bucket/projects/<uuid>/<file>.pdf

        TODO: chưa có ví dụ `key` thành công 100% xác nhận (chỉ biết archive.id KHÔNG
        đúng). Test lại với 1 key thật lấy nguyên từ fileUrls trước khi tin tưởng logic này.
        """
        return urlparse(file_url).path.lstrip("/")