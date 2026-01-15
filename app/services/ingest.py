import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List

from app.services.chroma_store import ChromaStore, ChunkRecord
from app.services.doc_parser import load_documents_from_dir
from app.services.embedding_client import EmbeddingClient
from app.services.qa_normalizer import QAPair, normalize_text_to_pairs


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedQA:
    source: str
    pairs: List[QAPair]


def default_docs_dir() -> str:
    return os.getenv("DOCS_DIR", "./data/docs")


def default_pairs_path() -> str:
    return os.getenv("PAIRS_JSON", "./data/parsed/faq_pairs.json")


async def parse_documents(
    docs_dir: str,
    output_path: str,
) -> List[ParsedQA]:
    logger.info("Parsing documents: dir=%s", docs_dir)
    documents = load_documents_from_dir(docs_dir)
    logger.info("Found documents: count=%s", len(documents))
    results: List[ParsedQA] = []
    for doc in documents:
        pairs = await normalize_text_to_pairs(doc.text)
        results.append(ParsedQA(source=doc.source, pairs=pairs))
        logger.info(
            "Normalized document: source=%s pairs=%s",
            doc.source,
            len(pairs),
        )
    _write_pairs_json(results, output_path)
    logger.info("Saved Q/A pairs: path=%s", output_path)
    return results


async def index_pairs(
    pairs_path: str,
    reset: bool = False,
) -> int:
    logger.info("Indexing pairs: path=%s reset=%s", pairs_path, reset)
    parsed = _load_pairs_json(pairs_path)
    logger.info("Loaded sources: count=%s", len(parsed))
    store = ChromaStore()
    await store.ensure_collection(drop_existing=reset)
    embedder = EmbeddingClient()

    total = 0
    texts: List[str] = []
    sources: List[str] = []
    for item in parsed:
        for text in _pairs_to_texts(item):
            texts.append(text)
            sources.append(item.source)
            if len(texts) >= _embed_batch_size():
                total += await _flush_batch(store, embedder, texts, sources)
                texts = []
                sources = []
    if texts:
        total += await _flush_batch(store, embedder, texts, sources)
    logger.info("Indexed chunks: total=%s", total)
    return total


def _pairs_to_texts(item: ParsedQA) -> Iterable[str]:
    max_words = _max_words_per_chunk()
    overlap = _overlap_words()
    for pair in item.pairs:
        combined = f"Q: {pair.question}\nA: {pair.answer}".strip()
        if max_words and _word_count(combined) > max_words:
            for chunk in _split_words(combined, max_words, overlap):
                yield chunk
        else:
            yield combined


async def _flush_batch(
    store: ChromaStore,
    embedder: EmbeddingClient,
    texts: List[str],
    sources: List[str],
) -> int:
    embeddings = await embedder.embed(texts)
    records = [
        ChunkRecord(embedding=emb, text=text, source=source)
        for emb, text, source in zip(embeddings, texts, sources)
    ]
    await store.insert_chunks(records)
    return len(records)


def _write_pairs_json(parsed: List[ParsedQA], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    payload: Dict[str, List[Dict[str, str]]] = {}
    for item in parsed:
        payload[item.source] = [
            {"q": pair.question, "a": pair.answer} for pair in item.pairs
        ]
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _load_pairs_json(path: str) -> List[ParsedQA]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    results: List[ParsedQA] = []
    for source, pairs in payload.items():
        items: List[QAPair] = []
        if isinstance(pairs, list):
            for pair in pairs:
                if not isinstance(pair, dict):
                    continue
                q = str(pair.get("q", "")).strip()
                a = str(pair.get("a", "")).strip()
                if q and a:
                    items.append(QAPair(question=q, answer=a))
        results.append(ParsedQA(source=source, pairs=items))
    return results


def _word_count(text: str) -> int:
    return len(text.split())


def _split_words(text: str, max_words: int, overlap: int) -> Iterable[str]:
    words = text.split()
    if not words:
        return []
    chunks: List[str] = []
    step = max(1, max_words - overlap)
    for start in range(0, len(words), step):
        chunk_words = words[start : start + max_words]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
    return chunks


def _max_words_per_chunk() -> int:
    return int(os.getenv("MAX_WORDS_PER_CHUNK", "300"))


def _overlap_words() -> int:
    return int(os.getenv("CHUNK_OVERLAP_WORDS", "50"))


def _embed_batch_size() -> int:
    return int(os.getenv("EMBED_BATCH_SIZE", "32"))
