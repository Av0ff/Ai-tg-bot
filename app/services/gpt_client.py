import os
from typing import Optional

from openai import AsyncOpenAI


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

    async def chat(self, user_text: str, system_prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        )

        message = response.choices[0].message
        return message.content or ""
