import os


DEFAULT_PROFILE = (
    "You are a helpful assistant. "
    "Use the provided context if available. "
    "If you are not confident, say that a specialist is needed."
)


def load_assistant_profile() -> str:
    path = os.getenv("ASSISTANT_PROFILE_PATH", "./data/assistant_profile.txt")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read().strip()
    except FileNotFoundError:
        return DEFAULT_PROFILE
    if not content:
        return DEFAULT_PROFILE
    return content
