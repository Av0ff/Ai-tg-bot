from app.services.assistant_profile import load_assistant_profile


def build_system_prompt() -> str:
    profile = load_assistant_profile()
    return (
        f"{profile}\n\n"
        "Use the conversation history and the provided context to answer. "
        "Do not assume the current question is in-scope just because earlier messages were. "
        "Evaluate the current user question on its own.\n\n"
        "If you can give a reasonable answer (even partial or general), do so and "
        "do NOT include the marker.\n\n"
        "Only add the marker if you truly cannot answer, for example:\n"
        "- The question is outside the domain of this assistant.\n"
        "- The context/history does not contain the required information and you "
        "cannot provide a safe generic answer.\n"
        "- The user message is nonsensical or too ambiguous even after asking a "
        "clarifying question.\n\n"
        "If the question is clearly outside the domain or unrelated to the provided "
        "context, you must add the marker even if you give a brief refusal or guidance.\n\n"
        "When you must escalate, first write a brief reply or clarifying question, "
        "then add a new line with exactly: [[NEEDS_SPECIALIST]]. "
        "Do not mention this token to the user."
    )
