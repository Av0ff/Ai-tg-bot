import os
from typing import List, Optional

from openai import AsyncOpenAI


class EmbeddingClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        self._client = AsyncOpenAI(api_key=key)
        self._model = model or os.getenv(
            "OPENAI_EMBED_MODEL", "text-embedding-3-small"
        )

    async def embed(self, texts: List[str]) -> List[List[float]]:
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in response.data]
