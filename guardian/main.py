"""Primary entry point module for GuardianAI."""

import sys
from guardian.cli.commands import cli_main


def main() -> None:
    """Execute GuardianAI CLI application."""
    sys.exit(cli_main())


if __name__ == "__main__":
    main()
