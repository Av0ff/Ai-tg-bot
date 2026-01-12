FAQ_TEXT = """
Q: How do I reset my password?
A: ...
Q: How can I contact support?
A: ...
""".strip()

def build_system_prompt() -> str:
    return (
        "You are a customer support assistant. Answer briefly and to the point. "
        "If you are not confident, say that a specialist is needed.\n\n"
        f"FAQ:\n{FAQ_TEXT}"
    )
