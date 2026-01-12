def needs_agent(answer: str) -> bool:
    markers = [
        "not sure",
        "need a specialist",
        "needs a specialist",
        "can't help",
        "cannot help",
    ]
    return any(m in answer.lower() for m in markers)
