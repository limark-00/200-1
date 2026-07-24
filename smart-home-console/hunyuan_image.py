# -*- coding: utf-8 -*-
"""混元文生图客户端 — HY-Image-3.0 提交/轮询接口。"""

from __future__ import annotations

import time
from typing import Any

import requests


class HunyuanImageClient:
    """HY-Image-3.0 文生图客户端。

    协议: 提交任务 → 轮询查询 → 返回结果图片 URL。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://tokenhub.tencentmaas.com/v1",
        model: str = "hy-image-v3.0",
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        poll_interval: float = 2.0,
        max_retries: int = 30,
    ) -> dict[str, Any]:
        """提交文生图任务并轮询结果。

        Returns:
            {"ok": True, "image_url": "...", "task_id": "..."}
            或 {"ok": False, "error": "..."}
        """
        # 1. 提交任务
        submit_url = f"{self.base_url}/api/image/submit"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "width": width,
            "height": height,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        try:
            resp = requests.post(submit_url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            return {"ok": False, "error": f"提交失败: {exc}"}

        task_id = data.get("id") or data.get("task_id")
        if not task_id:
            return {"ok": False, "error": f"未获取到任务 ID: {data}"}

        # 2. 轮询结果
        query_url = f"{self.base_url}/api/image/query"
        for i in range(max_retries):
            time.sleep(poll_interval)
            try:
                resp = requests.post(
                    query_url,
                    headers=headers,
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
                    return {"ok": True, "image_url": image_url, "task_id": task_id}
                return {"ok": False, "error": f"任务完成但无图片: {result}"}

            if status in {"failed", "error"}:
                err = result.get("error", {})
                return {
                    "ok": False,
                    "error": err.get("message") if isinstance(err, dict) else str(err),
                }

        return {"ok": False, "error": f"轮询超时，已等待 {max_retries * poll_interval}s"}
