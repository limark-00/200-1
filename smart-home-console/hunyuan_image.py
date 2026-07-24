# -*- coding: utf-8 -*-
"""混元文生图客户端 — HY-Image-3.0 + HY-Image-Lite。"""

from __future__ import annotations

import base64
import time
from typing import Any

import requests


class HunyuanImageClient:
    """混元文生图客户端。

    - HY-Image-3.0: 提交 → 轮询（质量高，0.2元/张，免费50张）
    - HY-Image-Lite: 同步返回（速度快，0.099元/张，免费50张）
    """

    LITE_MODEL = "hy-image-lite"
    PRO_MODEL = "hy-image-v3.0"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://tokenhub.tencentmaas.com/v1",
        model: str = "hy-image-lite",
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        poll_interval: float = 2.0,
        max_retries: int = 30,
        reference_b64: str = "",
    ) -> dict[str, Any]:
        """文生图，根据 self.model 自动选协议。

        - hy-image-lite: 同步 POST /v1/api/image/lite
        - hy-image-v3.0: 异步 submit → poll（可选参考图）

        reference_b64: 参考图 base64 (data:image/...;base64,xxx)，仅 v3.0 支持
        """
        if self.model == self.LITE_MODEL:
            return self._generate_lite(prompt)

        return self._generate_pro(prompt, negative_prompt, width, height, poll_interval, max_retries, reference_b64)

    def _generate_lite(self, prompt: str) -> dict[str, Any]:
        """Lite 版：单次请求同步返回图片 URL。"""
        try:
            resp = requests.post(
                f"{self.base_url}/api/image/lite",
                headers=self._headers,
                json={
                    "model": self.LITE_MODEL,
                    "prompt": prompt,
                    "rsp_img_type": "url",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            image_url = data.get("url") or data.get("image_url")
            # data 可能是列表
            if not image_url and isinstance(data.get("data"), list) and data["data"]:
                image_url = data["data"][0].get("url")
            if not image_url and isinstance(data.get("data"), dict):
                image_url = data["data"].get("url")

            if image_url:
                return {"ok": True, "image_url": image_url, "model": self.LITE_MODEL}
            return {"ok": False, "error": f"未获取到图片 URL: {data}"}
        except requests.RequestException as exc:
            return {"ok": False, "error": f"请求失败: {exc}"}

    def _generate_pro(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        poll_interval: float,
        max_retries: int,
        reference_b64: str = "",
    ) -> dict[str, Any]:
        """专业版：异步提交 + 轮询结果。reference_b64: 参考图 base64（图生图模式）."""
        submit_url = f"{self.base_url}/api/image/submit"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "width": width,
            "height": height,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if reference_b64:
            payload["reference_image"] = reference_b64

        try:
            resp = requests.post(submit_url, headers=self._headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            return {"ok": False, "error": f"提交失败: {exc}"}

        task_id = data.get("id") or data.get("task_id")
        if not task_id:
            return {"ok": False, "error": f"未获取到任务 ID: {data}"}

        query_url = f"{self.base_url}/api/image/query"
        for i in range(max_retries):
            time.sleep(poll_interval)
            try:
                resp = requests.post(
                    query_url,
                    headers=self._headers,
                    json={"model": self.model, "id": task_id},
                    timeout=30,
                )
                resp.raise_for_status()
                result = resp.json()
            except requests.RequestException as exc:
                return {"ok": False, "error": f"轮询失败: {exc}"}

            status = result.get("status", "").lower()
            if status in {"success", "succeeded", "completed", "done"}:
                data = result.get("data", {})
                if isinstance(data, list) and data:
                    image_url = data[0].get("url") if isinstance(data[0], dict) else None
                elif isinstance(data, dict):
                    image_url = data.get("url")
                else:
                    image_url = None
                image_url = image_url or result.get("url") or result.get("image_url")
                if image_url:
                    return {"ok": True, "image_url": image_url, "task_id": task_id, "model": self.model}
                return {"ok": False, "error": f"任务完成但无图片: {result}"}

            if status in {"failed", "error"}:
                err = result.get("error", {})
                return {
                    "ok": False,
                    "error": err.get("message") if isinstance(err, dict) else str(err),
                }

        return {"ok": False, "error": f"轮询超时，已等待 {max_retries * poll_interval}s"}


def image_path_to_b64(path: str) -> str:
    """本地图片 → data:image/xxx;base64,..."""
    ext = path.rsplit(".", 1)[-1].lower()
    mime = "image/jpeg" if ext in {"jpg", "jpeg"} else f"image/{ext}"
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"
