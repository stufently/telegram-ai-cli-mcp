"""Desktop Extension entry point. The host runs this file with uv.

Equivalent to ``tg-ai mcp``: the same CLI, the same registry, stdio MCP.
"""

import sys

from telegram_ai_cli_mcp.cli import main

if __name__ == "__main__":
    sys.argv = ["tg-ai", "mcp", *sys.argv[1:]]
    main()
