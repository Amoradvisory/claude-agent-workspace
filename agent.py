import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


async def main():
    async for message in query(
        prompt="Hello! What can you help me with?",
        options=ClaudeAgentOptions(
            cwd=".",
            allowed_tools=["Read", "Glob", "Grep", "Bash", "Edit", "Write"],
        ),
    ):
        if isinstance(message, ResultMessage):
            print(message.result)


anyio.run(main)
