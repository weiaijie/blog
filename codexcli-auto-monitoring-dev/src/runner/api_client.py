from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from typing import Any


class RunApiClient:
    def __init__(self, api_base: str) -> None:
        self.api_base = api_base.rstrip("/")
        self.is_mock = self.api_base == "mock" or self.api_base.startswith("mock://")

    def _post_json(self, url: str, payload: dict[str, Any], timeout: float = 20) -> dict[str, Any]:
        if self.is_mock:
            return {
                "ok": True,
                "mock": True,
                "url": url,
                "received_keys": sorted(payload.keys()),
            }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_data = resp.read().decode("utf-8")
                if not resp_data:
                    return {}
                return json.loads(resp_data)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"POST {url} failed ({exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"POST {url} network error: {exc.reason}") from exc

    def create_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.api_base}/v1/runs"
        return self._post_json(url=url, payload=payload, timeout=20)

    def post_events_batch(self, run_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
        url = f"{self.api_base}/v1/runs/{run_id}/events:batch"
        payload = {"events": events}
        return self._post_json(url=url, payload=payload, timeout=20)

    def init_artifact(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.api_base}/v1/artifacts/init"
        return self._post_json(url=url, payload=payload, timeout=20)

    def complete_artifact(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.api_base}/v1/artifacts/complete"
        return self._post_json(url=url, payload=payload, timeout=20)


def create_offline_run(payload: dict[str, Any]) -> dict[str, Any]:
    run_id = str(uuid.uuid4())
    return {
        "run_id": run_id,
        "stream_url": None,
        "offline": True,
        "echo": payload,
    }
