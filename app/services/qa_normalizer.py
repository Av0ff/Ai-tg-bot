import json
from dataclasses import dataclass
from typing import List

from app.services.gpt_client import GPTClient


@dataclass(frozen=True)
class QAPair:
    question: str
    answer: str


SYSTEM_PROMPT = (
    "You normalize documents into FAQ pairs.\n"
    "Return only Q/A pairs in this exact format:\n"
    "Q: <question>\n"
    "A: <answer>\n"
    "\n"
    "Rules:\n"
    "- Extract only clear question/answer pairs.\n"
    "- If the text is not Q/A, convert it into short Q/A pairs.\n"
    "- Keep answers concise but complete.\n"
    "- Do not include any extra commentary or JSON.\n"
)


async def normalize_text_to_pairs(text: str) -> List[QAPair]:
    client = GPTClient()
    output, _meta = await client.chat(user_text=text, system_prompt=SYSTEM_PROMPT)
    pairs = _parse_pairs(output)
    if pairs:
        return pairs
    return _parse_pairs_from_json(output)


def _parse_pairs(output: str) -> List[QAPair]:
    pairs: List[QAPair] = []
    current_q = None
    current_a = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            if current_q and current_a:
                pairs.append(QAPair(question=current_q, answer=current_a))
                current_q = None
                current_a = None
            continue
        lower = line.lower()
        if lower.startswith("q:") or lower.startswith("question:"):
            current_q = line.split(":", 1)[1].strip()
            continue
        if lower.startswith("a:") or lower.startswith("answer:"):
            current_a = line.split(":", 1)[1].strip()
            continue
        if current_a is not None:
            current_a = f"{current_a} {line}".strip()
        elif current_q is not None:
            current_q = f"{current_q} {line}".strip()
    if current_q and current_a:
        pairs.append(QAPair(question=current_q, answer=current_a))
    return pairs


def _parse_pairs_from_json(output: str) -> List[QAPair]:
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return []
    pairs: List[QAPair] = []
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            q = str(item.get("question", "")).strip()
            a = str(item.get("answer", "")).strip()
            if q and a:
                pairs.append(QAPair(question=q, answer=a))
    return pairs
