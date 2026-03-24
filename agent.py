"""
Agent Codex augmenté — Point d'entrée principal.
Usage: python agent.py "Ta question ou instruction ici"
"""
import sys
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


ALLOWED_TOOLS = [
    "Read", "Glob", "Grep", "Bash", "Edit", "Write",
    "Agent", "WebFetch", "WebSearch",
    "mcp__Claude_in_Chrome__navigate",
    "mcp__Claude_in_Chrome__read_page",
    "mcp__Claude_in_Chrome__get_page_text",
    "mcp__Claude_in_Chrome__javascript_tool",
    "mcp__Claude_Preview__preview_start",
    "mcp__Claude_Preview__preview_screenshot",
    "mcp__Claude_Preview__preview_snapshot",
]

SYSTEM_CONTEXT = """Tu es un agent augmenté francophone. Tu ne te contentes pas d'exécuter :
tu détectes les capacités manquantes et tu les ajoutes (dépendances, scripts, MCP, configs).
Consulte CLAUDE.md pour les instructions complètes.
Utilise memory/log.md pour noter ce que tu fais.
Langue par défaut : français."""


async def main():
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Bonjour ! Comment puis-je t'aider ?"

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            cwd=".",
            system_prompt=SYSTEM_CONTEXT,
            allowed_tools=ALLOWED_TOOLS,
        ),
    ):
        if isinstance(message, ResultMessage):
            print(message.result)


if __name__ == "__main__":
    anyio.run(main)
