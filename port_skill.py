#!/usr/bin/env python3
"""Convenience CLI entrypoint for Antigravity Skill Porter."""
import sys
from pathlib import Path

# Add skill scripts directory to path and execute main()
scripts_dir = Path(__file__).resolve().parent / "skills" / "skill-porter" / "scripts"
sys.path.insert(0, str(scripts_dir))

from port_skill import main

if __name__ == "__main__":
    main()
