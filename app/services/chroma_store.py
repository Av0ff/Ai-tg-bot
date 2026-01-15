import asyncio
import logging
import os
import shutil
import uuid
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.api import ClientAPI


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChunkRecord:
    embedding: List[float]
    text: str
    source: str
    chunk_id: Optional[str] = None


class ChromaStore:
    def __init__(
        self,
        path: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        self._path = path or os.getenv("CHROMA_PATH", "./data/chroma")
        self._collection_name = collection_name or os.getenv(
            "CHROMA_COLLECTION", "faq_chunks"
        )
        self._client: Optional[ClientAPI] = None

    async def ensure_collection(self, drop_existing: bool = False) -> None:
        await asyncio.to_thread(self._ensure_collection_sync, drop_existing)

    async def insert_chunks(self, records: Iterable[ChunkRecord]) -> List[str]:
        return await asyncio.to_thread(self._insert_chunks_sync, list(records))

    async def search(
        self,
        embedding: List[float],
        top_k: int = 5,
    ) -> List[Dict[str, object]]:
        return await asyncio.to_thread(self._search_sync, embedding, top_k)

    def _get_client(self) -> ClientAPI:
        if self._client is None:
            os.makedirs(self._path, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self._path,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False,
                    chroma_product_telemetry_impl=(
                        "app.services.chroma_telemetry.NoopTelemetry"
                    ),
                    chroma_telemetry_impl=(
                        "app.services.chroma_telemetry.NoopTelemetry"
                    ),
                ),
            )
        return self._client

    def _ensure_collection_sync(self, drop_existing: bool = False) -> None:
        if drop_existing:
            self._hard_reset_persist_dir()
        client = self._get_client()
        client.get_or_create_collection(
            self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _insert_chunks_sync(self, items: List[ChunkRecord]) -> List[str]:
        if not items:
            return []
        collection = self._get_client().get_or_create_collection(
            self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        ids = [item.chunk_id or str(uuid.uuid4()) for item in items]
        documents = [item.text for item in items]
        metadatas = [{"source": item.source} for item in items]
        embeddings = [item.embedding for item in items]
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return ids

    def _search_sync(
        self,
        embedding: List[float],
        top_k: int,
    ) -> List[Dict[str, object]]:
        collection = self._get_client().get_or_create_collection(
            self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        hits: List[Dict[str, object]] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for idx, doc, meta, dist in zip(ids, documents, metadatas, distances):
            hits.append(
                {
                    "id": idx,
                    "score": dist,
                    "text": doc,
                    "source": (meta or {}).get("source"),
                }
            )
        return hits

    def _hard_reset_persist_dir(self) -> None:
        if self._client is not None:
            try:
                self._client.reset()
            except Exception:
                logger.exception("Chroma reset failed before hard reset")
            self._client = None
        if os.path.isdir(self._path):
            try:
                shutil.rmtree(self._path)
                logger.info("Removed Chroma directory: path=%s", self._path)
                return
            except Exception as exc:
                logger.warning(
                    "Failed to delete Chroma directory: path=%s error=%s",
                    self._path,
                    exc,
                )
        try:
            client = self._get_client()
            client.reset()
            logger.info("Fallback reset completed: path=%s", self._path)
        except Exception:
            logger.exception("Fallback Chroma reset failed")
