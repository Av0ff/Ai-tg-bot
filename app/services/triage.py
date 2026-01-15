MARKER = "[[NEEDS_SPECIALIST]]"


def needs_agent(answer: str) -> bool:
    return MARKER.lower() in answer.lower()


def strip_agent_marker(answer: str) -> str:
    if not answer:
        return answer
    cleaned_lines = [
        line for line in answer.splitlines() if MARKER.lower() not in line.lower()
    ]
    return "\n".join(cleaned_lines).strip()
