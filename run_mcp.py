"""Lance le serveur MCP (stdio)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_server.server import cli


if __name__ == "__main__":
    cli()
