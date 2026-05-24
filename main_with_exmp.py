#!/usr/bin/env python3
"""Nexknit - Run Gateway with Example Collector

Starts both the Nexknit gateway and the example collector.
"""

import subprocess
import sys
import os
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GATEWAY_SCRIPT = os.path.join(SCRIPT_DIR, "main.py")
COLLECTOR_SCRIPT = os.path.join(SCRIPT_DIR, "test_collector.py")


def main():
    parser = argparse.ArgumentParser(description="Run Nexknit Gateway with Example Collector")
    parser.add_argument("--url", type=str, help="Cloudflare Worker URL")
    parser.add_argument("--api-key", type=str, help="API Key")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║ Nexknit - Starting Gateway & Collector                           ║ ")
    print("╚══════════════════════════════════════════════════════════════════╝\n")

    # Build gateway command with optional url and api-key
    gateway_cmd = [sys.executable, GATEWAY_SCRIPT]
    if args.url:
        gateway_cmd.extend(["--url", args.url])
    if args.api_key:
        gateway_cmd.extend(["--api-key", args.api_key])

    gateway_process = subprocess.Popen(
        gateway_cmd,
        cwd=SCRIPT_DIR,
    )

    collector_process = subprocess.Popen(
        [sys.executable, COLLECTOR_SCRIPT],
        cwd=SCRIPT_DIR,
    )

    print(f"[START] Gateway started (PID: {gateway_process.pid})")
    print(f"[START] Collector started (PID: {collector_process.pid})")
    print("\nPress Ctrl+C to stop both processes\n")

    try:
        gateway_process.wait()
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")
        gateway_process.terminate()
        collector_process.terminate()
        gateway_process.wait()
        collector_process.wait()
        print("[STOP] All processes stopped")


if __name__ == "__main__":
    main()
