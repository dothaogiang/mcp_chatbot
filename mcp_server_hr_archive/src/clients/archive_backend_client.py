from __future__ import annotations
import asyncio
from typing import Any, Dict, Optional, Tuple
import httpx
from logger import get_logger
from config.settings import Settings
from common_utils.exceptions import (
    NotFoundError,
    BackendError,
    UnauthorizedError,
    ForbiddenError,
    BadRequestError,
)
from urllib.parse import urlparse

log = get_logger(__name__)


class ArchiveBackendClient:
    """Async httpx client to call the Public Archives API.

    - Automatically attaches/refreshes `X-Chatbot-Token` header when configured.
    - Normalizes common error payloads into exceptions.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(base_url=str(settings.BACKEND_BASE_URL), timeout=30.0)
        self._token: Optional[str] = None
        self._lock = asyncio.Lock()

    async def close(self) -> None:
        await self._client.aclose()

    async def _ensure_token(self) -> None:
        if not self.settings.CHATBOT_TOKEN_URL:
            return
        async with self._lock:
            if self._token:
                return
            # simple token fetch; real implementation may use client credentials
            resp = await self._client.post(str(self.settings.CHATBOT_TOKEN_URL), json={})
            if resp.status_code == 200:
                data = resp.json()
                self._token = data.get("access_token")

    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        await self._ensure_token()
        headers = kwargs.pop("headers", {}) or {}
        if self._token:
            headers["X-Chatbot-Token"] = self._token
        try:
            resp = await self._client.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            log.error("HTTP error calling backend: %s", exc)
            raise BackendError(str(exc))

        # Try parse JSON body
        body = None
        try:
            body = resp.json()
        except Exception:
            body = None

        # Common error envelope: { status: 0, message: ... }
        if body and isinstance(body, dict) and body.get("status") == 0:
            msg = body.get("message")
            code = resp.status_code
            if code == 400:
                raise BadRequestError(msg)
            if code == 401:
                raise UnauthorizedError(msg)
            if code == 403:
                raise ForbiddenError(msg)
            if code in (404, 500):
                # API sometimes returns 500 for not-found; treat both as not found
                raise NotFoundError(msg)
            raise BackendError(msg)

        # Status-based mapping when no envelope
        if resp.status_code >= 400:
            if resp.status_code == 400:
                raise BadRequestError(resp.text)
            if resp.status_code == 401:
                raise UnauthorizedError(resp.text)
            if resp.status_code == 403:
                raise ForbiddenError(resp.text)
            if resp.status_code in (404, 500):
                raise NotFoundError(resp.text)
            raise BackendError(resp.text)

        # Return JSON if available, else bytes
        return body if body is not None else resp.content

    async def search_archives(self, params: Dict[str, Any]) -> Any:
        # Map common tool params to backend query args (backend expects `keyword`, `page`, `size`)
        params = params.copy() if params else {}
        if "q" in params and "keyword" not in params:
            params["keyword"] = params.pop("q")
        # backend uses page/size; ensure defaults
        params.setdefault("page", params.get("page", 0))
        params.setdefault("size", params.get("size", 20))
        return await self._request("GET", "/api/public/archives", params=params)

    async def get_archive_detail(self, archive_id: str) -> Any:
        return await self._request("GET", f"/api/public/archives/{archive_id}")

    async def get_staff_profiles(self) -> Any:
        return await self._request("GET", "/api/public/ho-so-can-bo")

    async def get_file_metadata(self, key: str) -> Dict[str, Any]:
        """Request the proxy endpoint and return metadata (headers) without reading full body.

        Returns dict: { key, filename, content_type, content_length }
        """
        url = "/api/public/files/proxy"
        try:
            resp = await self._client.get(url, params={"key": key}, timeout=30.0)
        except httpx.HTTPError as exc:
            log.error("Error fetching file proxy metadata: %s", exc)
            raise BackendError(str(exc))

        if resp.status_code >= 400:
            # Normalize via _request logic
            # reuse _request to get consistent mapping
            await self._request("GET", url, params={"key": key})

        # Extract filename from content-disposition
        dispo = resp.headers.get("content-disposition") or ""
        filename = None
        if "filename=" in dispo:
            # simple parse
            try:
                filename = dispo.split("filename=")[-1].strip('"')
            except Exception:
                filename = None

        return {
            "key": key,
            "filename": filename,
            "content_type": resp.headers.get("content-type"),
            "content_length": resp.headers.get("content-length"),
        }

    async def get_file_stream(self, key: str) -> Tuple[httpx.Response, httpx.ByteStream]:
        """Return the response and raw stream for the caller to stream/download if needed."""
        resp = await self._client.get("/api/public/files/proxy", params={"key": key}, stream=True)
        if resp.status_code >= 400:
            # map errors
            await self._request("GET", "/api/public/files/proxy", params={"key": key})
        return resp, resp.aiter_bytes()

    @staticmethod
    def extract_key_from_url(file_url: str) -> str:
        """Given a full file URL, return the object path key expected by proxy.

        Example: https://host/.../projects/<uuid>/<file>.pdf -> projects/<uuid>/<file>.pdf
        """
        parsed = urlparse(file_url)
        # remove leading slash
        return parsed.path.lstrip("/")
