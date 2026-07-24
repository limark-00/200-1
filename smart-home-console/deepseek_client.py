# -*- coding: utf-8 -*-
"""混元大模型客户端 — 基于 OpenAI SDK 的封装，支持对话、图生文、流式输出。"""

from __future__ import annotations

import base64
from typing import Any

from openai import OpenAI


class HunyuanClient:
    """混元 Chat API 客户端（OpenAI 兼容格式）。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.hunyuan.cloud.tencent.com/v1",
        model: str = "hunyuan-turbos-latest",
        vision_model: str = "hunyuan-vision",
        timeout: float = 30.0,
    ) -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.model = model
        self.vision_model = vision_model

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> dict[str, Any]:
        """发送对话请求。返回 {"reply": str, "usage": dict} 或 {"error": str}。

        stream=True 时，reply 字段为生成器。
        """
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                extra_body={"enable_enhancement": True},
            )

            if stream:
                return {"reply": _stream_generator(resp), "usage": {}}

            reply = resp.choices[0].message.content or ""
            return {"reply": reply, "usage": resp.usage.model_dump() if resp.usage else {}}
        except Exception as exc:
            return {"error": f"混元请求失败: {exc}"}

    def chat_with_image(
        self,
        image_path: str,
        prompt: str = "请描述这张图片的内容",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """图生文：将本地图片转 base64，发送给混元 vision 模型分析。

        image_path: 本地图片路径（jpg/png）
        prompt: 对图片的提问
        返回 {"reply": str, "usage": dict} 或 {"error": str}
        """
        try:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            ext = image_path.rsplit(".", 1)[-1].lower()
            mime = "image/jpeg" if ext in {"jpg", "jpeg"} else f"image/{ext}"
            data_url = f"data:{mime};base64,{img_b64}"

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                    ],
                }
            ]

            resp = self.client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            reply = resp.choices[0].message.content or ""
            return {"reply": reply, "usage": resp.usage.model_dump() if resp.usage else {}}
        except FileNotFoundError:
            return {"error": f"图片文件不存在: {image_path}"}
        except Exception as exc:
            return {"error": f"图生文请求失败: {exc}"}


def _stream_generator(response):
    """流式响应生成器：逐个 token yield。"""
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
