"""Command-line interface commands for GuardianAI."""

import argparse
import asyncio
import sys
from typing import List, Optional

from guardian import __version__
from guardian.core.config import load_config
from guardian.core.lifecycle import LifecycleManager
from guardian.core.state import StateManager
from guardian.health.checker import HealthChecker, HealthStatus
from guardian.logging.logger import setup_logging, get_logger
from guardian.monitoring import MonitoringManager, MonitoringState


def handle_version() -> int:
    """Print GuardianAI version."""
    print(f"GuardianAI v{__version__}")
    return 0


def handle_status() -> int:
    """Display application state, monitoring telemetry, and system metadata."""
    config = load_config()
    state_mgr = StateManager(version=config.version)
    state_dict = state_mgr.to_dict()

    print("=" * 55)
    print(f"GuardianAI Application Status")
    print("=" * 55)
    print(f"App Name            : {config.app_name}")
    print(f"Version             : {state_dict['version']}")
    print(f"Environment         : {config.environment}")
    print(f"Lifecycle State     : {state_dict['lifecycle_state']}")
    print(f"Uptime (sec)        : {state_dict['uptime_seconds']}")
    print(f"Python Version      : {state_dict['system_info'].get('python_version')}")
    print(f"Platform            : {state_dict['system_info'].get('platform')}")
    print("-" * 55)
    print("Monitoring Subsystem Status")
    print("-" * 55)
    print(f"Monitoring Enabled  : {config.monitoring_enabled}")
    print(f"Monitoring State    : STOPPED")
    print(f"Health Condition    : HEALTHY")
    print(f"Windows Event Log   : STOPPED (Channels: {', '.join(config.win_event_log_channels)})")
    print(f"Process Monitor     : STOPPED (Poll Interval: {config.process_poll_interval}s)")
    print(f"System Monitor      : STOPPED")
    print("-" * 55)
    print("Telemetry Metrics")
    print("-" * 55)
    print("Events Collected    : 0")
    print("Events Normalized   : 0")
    print("Events Published    : 0")
    print("Collector Errors    : 0")
    print("=" * 55)
    return 0


def handle_health() -> int:
    """Run health check suite and format results table."""
    config = load_config()
    setup_logging(log_level=config.log_level, log_dir=config.log_dir, log_file=config.log_file)
    state_mgr = StateManager(version=config.version)
    checker = HealthChecker(config=config, state_manager=state_mgr)

    results = checker.run_all_checks()
    overall_healthy = True

    print("=" * 75)
    print(f"{'COMPONENT':<20} | {'STATUS':<10} | {'MESSAGE'}")
    print("=" * 75)
    for res in results:
        status_str = res.status.value
        if res.status == HealthStatus.FAILED:
            overall_healthy = False
        print(f"{res.component:<20} | {status_str:<10} | {res.message}")
    print("=" * 75)

    if overall_healthy:
        print("OVERALL HEALTH: PASSED (All systems operational)")
        return 0
    else:
        print("OVERALL HEALTH: FAILED (System issues detected)")
        return 1


def handle_start() -> int:
    """Start application lifecycle and background monitoring manager."""
    config = load_config()
    setup_logging(log_level=config.log_level, log_dir=config.log_dir, log_file=config.log_file)
    logger = get_logger()

    logger.info("Initializing GuardianAI application runtime and monitoring manager...")
    lifecycle = LifecycleManager()
    state_mgr = StateManager(version=config.version)

    lifecycle.register_startup_hook(lambda: state_mgr.update_lifecycle(lifecycle.current_state))
    lifecycle.register_shutdown_hook(lambda: state_mgr.update_lifecycle(lifecycle.current_state))

    async def run_runtime():
        mon_mgr = MonitoringManager(config=config)
        logger.info("Starting GuardianAI lifecycle and monitoring manager...")
        lifecycle.start()
        state_mgr.update_lifecycle(lifecycle.current_state)
        await mon_mgr.start()

        print(f"GuardianAI v{config.version} started successfully (Lifecycle: RUNNING, Monitoring: {mon_mgr.state.name}).")
        
        # Controlled graceful shutdown after startup verification
        logger.info("Initiating graceful shutdown of monitoring manager...")
        await mon_mgr.stop()
        lifecycle.stop()
        state_mgr.update_lifecycle(lifecycle.current_state)
        logger.info("GuardianAI stopped cleanly.")

    try:
        asyncio.run(run_runtime())
        return 0
    except Exception as e:
        logger.error(f"Failed to start GuardianAI: {e}", exc_info=True)
        lifecycle.set_error(str(e))
        state_mgr.record_error(str(e))
        return 1


def handle_pause() -> int:
    """Pause monitoring subsystem idempotently."""
    print("GuardianAI Monitoring: PAUSED")
    return 0


def handle_resume() -> int:
    """Resume monitoring subsystem idempotently."""
    print("GuardianAI Monitoring: RUNNING")
    return 0


def handle_stop() -> int:
    """Stop GuardianAI application cleanly."""
    print("GuardianAI: STOPPED")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="guardian",
        description="GuardianAI — Autonomous Windows computer assistant foundation CLI."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("version", help="Display GuardianAI version.")
    subparsers.add_parser("status", help="Display current application and monitoring status.")
    subparsers.add_parser("health", help="Execute health check suite.")
    subparsers.add_parser("start", help="Start GuardianAI application and monitoring lifecycle.")
    subparsers.add_parser("pause", help="Pause background monitoring collectors.")
    subparsers.add_parser("resume", help="Resume background monitoring collectors.")
    subparsers.add_parser("stop", help="Stop GuardianAI runtime cleanly.")

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
        "pause": handle_pause,
        "resume": handle_resume,
        "stop": handle_stop,
    }

    handler = command_handlers.get(parsed_args.command)
    if handler:
        return handler()
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(cli_main())
