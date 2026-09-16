"""Command-line interface commands for GuardianAI."""

import argparse
import sys
from typing import List, Optional

from guardian import __version__
from guardian.core.config import load_config
from guardian.core.lifecycle import LifecycleManager
from guardian.core.state import StateManager
from guardian.health.checker import HealthChecker, HealthStatus
from guardian.logging.logger import setup_logging, get_logger


def handle_version() -> int:
    """Print GuardianAI version."""
    print(f"GuardianAI v{__version__}")
    return 0


def handle_status() -> int:
    """Display application state and runtime information."""
    config = load_config()
    state_mgr = StateManager(version=config.version)
    state_dict = state_mgr.to_dict()

    print("=" * 50)
    print(f"GuardianAI Application Status")
    print("=" * 50)
    print(f"App Name        : {config.app_name}")
    print(f"Version         : {state_dict['version']}")
    print(f"Environment     : {config.environment}")
    print(f"Lifecycle State : {state_dict['lifecycle_state']}")
    print(f"Uptime (sec)    : {state_dict['uptime_seconds']}")
    print(f"Python Version  : {state_dict['system_info'].get('python_version')}")
    print(f"Platform        : {state_dict['system_info'].get('platform')}")
    print("=" * 50)
    return 0


def handle_health() -> int:
    """Run health check suite and format results table."""
    config = load_config()
    setup_logging(log_level=config.log_level, log_dir=config.log_dir, log_file=config.log_file)
    state_mgr = StateManager(version=config.version)
    checker = HealthChecker(config=config, state_manager=state_mgr)

    results = checker.run_all_checks()
    overall_healthy = True

    print("=" * 70)
    print(f"{'COMPONENT':<20} | {'STATUS':<10} | {'MESSAGE'}")
    print("=" * 70)
    for res in results:
        status_str = res.status.value
        if res.status == HealthStatus.FAILED:
            overall_healthy = False
        print(f"{res.component:<20} | {status_str:<10} | {res.message}")
    print("=" * 70)

    if overall_healthy:
        print("OVERALL HEALTH: PASSED (All systems operational)")
        return 0
    else:
        print("OVERALL HEALTH: FAILED (System issues detected)")
        return 1


def handle_start() -> int:
    """Start application lifecycle."""
    config = load_config()
    setup_logging(log_level=config.log_level, log_dir=config.log_dir, log_file=config.log_file)
    logger = get_logger()

    logger.info("Initializing GuardianAI application runtime...")
    lifecycle = LifecycleManager()
    state_mgr = StateManager(version=config.version)

    lifecycle.register_startup_hook(lambda: state_mgr.update_lifecycle(lifecycle.current_state))
    lifecycle.register_shutdown_hook(lambda: state_mgr.update_lifecycle(lifecycle.current_state))

    try:
        logger.info("Starting GuardianAI lifecycle...")
        lifecycle.start()
        state_mgr.update_lifecycle(lifecycle.current_state)
        logger.info("GuardianAI is now RUNNING.")
        print(f"GuardianAI v{config.version} started successfully (State: RUNNING).")
        
        # Controlled graceful shutdown after startup verification
        logger.info("Initiating graceful shutdown...")
        lifecycle.stop()
        state_mgr.update_lifecycle(lifecycle.current_state)
        logger.info("GuardianAI stopped cleanly.")
        return 0
    except Exception as e:
        logger.error(f"Failed to start GuardianAI: {e}", exc_info=True)
        lifecycle.set_error(str(e))
        state_mgr.record_error(str(e))
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="guardian",
        description="GuardianAI — Autonomous Windows computer assistant foundation CLI."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("version", help="Display GuardianAI version.")
    subparsers.add_parser("status", help="Display current application status.")
    subparsers.add_parser("health", help="Execute health check suite.")
    subparsers.add_parser("start", help="Start GuardianAI application lifecycle.")

    return parser


def cli_main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point dispatcher."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    command_handlers = {
        "version": handle_version,
        "status": handle_status,
        "health": handle_health,
        "start": handle_start,
    }

    handler = command_handlers.get(parsed_args.command)
    if handler:
        return handler()
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(cli_main())
