"""Absolute-path entry point for MCP clients with an unrelated working directory."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vayrshemon.__main__ import main

if __name__ == '__main__':
    raise SystemExit(main())
