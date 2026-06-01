"""Full CLI agent with pydantic-ai integration.

This is the main example showing how to build a CLI coding assistant
using LocalBackend with pydantic-ai.

Requires: pip install pydantic-ai-backend[console]
"""

import argparse
import asyncio
import os
from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import Agent

from pydantic_ai_backends import LocalBackend, create_console_toolset, get_console_system_prompt


@dataclass
class AgentDeps:
    """Dependencies for the CLI agent."""

    backend: LocalBackend
    working_dir: str


SYSTEM_PROMPT = f"""You are a helpful coding assistant that can read, write, and execute code.

{get_console_system_prompt()}

## Guidelines

1. Always read a file before editing it
2. Use glob to find files when you don't know exact paths
3. Use grep to search for code patterns
4. Execute tests after making changes
5. Explain what you're doing and why

When the user asks you to do something:
- First understand the current state (read files, list directories)
- Then make the necessary changes
- Finally verify the changes worked
"""


def create_cli_agent(
    model: str = "openai:gpt-4o-mini",
    enable_execute: bool = True,
    ignore_hidden: bool = True,
) -> Agent[AgentDeps, str]:
    """Create a CLI agent with console tools.

    Args:
        model: The model to use (e.g., "openai:gpt-4o-mini", "anthropic:claude-3-haiku")
        enable_execute: Whether to allow shell command execution
        ignore_hidden: Default grep behavior for hidden files.
    """
    toolset = create_console_toolset(
        include_execute=enable_execute,
        require_write_approval=False,
        require_execute_approval=False,
        default_ignore_hidden=ignore_hidden,
    )

    agent: Agent[AgentDeps, str] = Agent(
        model,
        system_prompt=SYSTEM_PROMPT,
        deps_type=AgentDeps,
    )

    return agent.with_toolset(toolset)


async def run_single_task(
    agent: Agent[AgentDeps, str],
    deps: AgentDeps,
    task: str,
) -> str:
    """Run a single task and return the result."""
    result = await agent.run(task, deps=deps)
    return result.output


async def run_interactive(
    agent: Agent[AgentDeps, str],
    deps: AgentDeps,
) -> None:
    """Run an interactive session with the agent."""
    print(f"CLI Agent ready! Working directory: {deps.working_dir}")
    print("Type 'quit' to exit, 'help' for examples.\n")

    examples = """
Example commands:
- "List all Python files"
- "Read the README.md file"
- "Create a hello.py that prints 'Hello World'"
- "Find all TODO comments in the code"
- "Run the tests"
- "Show me the project structure"
"""

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if user_input.lower() == "help":
            print(examples)
            continue

        if not user_input:
            continue

        print("\nAgent: ", end="", flush=True)
        result = await agent.run(user_input, deps=deps)
        print(f"{result.output}\n")


def main() -> None:
    """Main entry point."""

    parser = argparse.ArgumentParser(description="CLI Agent with file operations")
    parser.add_argument(
        "--dir",
        "-d",
        default=".",
        help="Working directory (default: current)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="openai:gpt-4o-mini",
        help="Model to use (default: openai:gpt-4o-mini)",
    )
    parser.add_argument(
        "--no-execute",
        action="store_true",
        help="Disable shell command execution",
    )
    parser.add_argument(
        "--task",
        "-t",
        help="Run a single task instead of interactive mode",
    )
    parser.add_argument(
        "--restrict",
        "-r",
        action="store_true",
        help="Restrict file access to working directory only",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files when searching with grep",
    )

    args = parser.parse_args()

    # Resolve working directory
    working_dir = str(Path(args.dir).resolve())

    if not os.path.isdir(working_dir):
        print(f"Error: {working_dir} is not a directory")
        return

    # Create backend
    allowed_dirs = [working_dir] if args.restrict else None
    backend = LocalBackend(
        root_dir=working_dir,
        allowed_directories=allowed_dirs,
        enable_execute=not args.no_execute,
    )

    deps = AgentDeps(backend=backend, working_dir=working_dir)
    agent = create_cli_agent(
        model=args.model,
        enable_execute=not args.no_execute,
        ignore_hidden=not args.include_hidden,
    )

    # Run
    if args.task:
        result = asyncio.run(run_single_task(agent, deps, args.task))
        print(result)
    else:
        asyncio.run(run_interactive(agent, deps))


if __name__ == "__main__":
    main()
