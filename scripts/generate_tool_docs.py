"""Generate MCP tool documentation by introspecting the live server registration.

Usage:
    python scripts/generate_tool_docs.py                 # print the sorted tool list
    python scripts/generate_tool_docs.py --write-readme  # also regenerate the README tool table
"""

import argparse
import asyncio
from pathlib import Path

from gdm.mcp.server import create_server

README_PATH = Path(__file__).resolve().parent.parent / "README.md"
MARKER_START = "<!-- MCP-TOOLS:START -->"
MARKER_END = "<!-- MCP-TOOLS:END -->"


def get_registered_tools() -> list[tuple[str, str]]:
    """Return sorted (name, description) pairs from the live server registration."""
    server = create_server()
    tools = asyncio.run(server.list_tools())
    return sorted((tool.name, tool.description) for tool in tools)


def render_tool_table(tools: list[tuple[str, str]]) -> str:
    """Render the README markdown table for the given tools."""
    lines = [
        "| Tool | Description |",
        "| --- | --- |",
    ]
    for name, description in tools:
        # Escape pipe characters in descriptions for markdown table safety.
        safe_description = description.replace("|", "\\|")
        lines.append(f"| `{name}` | {safe_description} |")
    return "\n".join(lines)


def update_readme(tools: list[tuple[str, str]]) -> None:
    """Replace the tool table block in README.md in place."""
    if not README_PATH.exists():
        raise FileNotFoundError(f"README not found: {README_PATH}")

    block = (
        f"{MARKER_START}\n\n### MCP Tools ({len(tools)})\n\n"
        f"{render_tool_table(tools)}\n\n{MARKER_END}"
    )
    content = README_PATH.read_text(encoding="utf-8")

    if MARKER_START in content and MARKER_END in content:
        start = content.index(MARKER_START)
        end = content.index(MARKER_END) + len(MARKER_END)
        content = content[:start] + block + content[end:]
    else:
        content = content.rstrip() + "\n\n" + block + "\n"

    README_PATH.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-readme",
        action="store_true",
        help="Regenerate the MCP tool table in README.md in place.",
    )
    args = parser.parse_args()

    tools = get_registered_tools()
    print(f"Registered MCP tools ({len(tools)}):")
    for name, description in tools:
        print(f"  {name}: {description}")

    if args.write_readme:
        update_readme(tools)
        print(f"Updated {README_PATH}")


if __name__ == "__main__":
    main()
