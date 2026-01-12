import os
from typing import Optional, TypedDict

from openai import AsyncOpenAI


class GPTMeta(TypedDict, total=False):
    status_code: int
    request_id: Optional[str]
    model: str
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]


class GPTClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        self._client = AsyncOpenAI(api_key=key)
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def chat(self, user_text: str, system_prompt: str) -> tuple[str, GPTMeta]:
        raw_response = await self._client.chat.completions.with_raw_response.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        )

        response = raw_response.parse()
        message = response.choices[0].message
        usage = response.usage

        meta: GPTMeta = {
            "status_code": raw_response.status_code,
            "request_id": raw_response.headers.get("x-request-id"),
            "model": response.model,
        }
        if usage:
            meta["prompt_tokens"] = usage.prompt_tokens
            meta["completion_tokens"] = usage.completion_tokens
            meta["total_tokens"] = usage.total_tokens

        return message.content or "", meta
