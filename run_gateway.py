#!/usr/bin/env python3
"""Nexknit - Gateway and Collectors Orchestrator

Starts the Nexknit gateway along with configured collectors.
"""

import subprocess
import sys
import os
import argparse
from typing import List, Dict, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GATEWAY_SCRIPT = os.path.join(SCRIPT_DIR, "gateway.py")

DEFAULT_PORT = 12345

ALERT_CONFIG: Dict[str, Any] = {
    # Enable alert functionality
    # Set to False to disable all alerts
    "enabled": True,

    # Alert output type:
    # - "stdout": Output to console (suitable for debugging and local use)
    # - "webhook": Send via HTTP POST to the specified webhook URL
    #              Supports WeCom, DingTalk, Feishu bots and other IM webhooks
    "type": "stdout",

    # Alert target (used to identify recipient, e.g., phone number or email)
    # When type="webhook", this field will be sent as the target field in payload
    # Examples: "admin@example.com", "13800138000", "ops-team"
    "target": "admin@example.com",

    # Webhook URL (only effective when type="webhook")
    # Example configurations:
    # - WeCom Bot: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
    # - DingTalk Bot: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
    # - Feishu Bot: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
    # - Custom Service: "https://your-alert-service.com/webhook"
    "webhook_url": "",
}

COLLECTORS: List[Dict[str, Any]] = [
    {
        "name": "system",
        "module": "collectors.system",
        "class": "SystemCollector",
        "enabled": True,
        "kwargs": {
            "interval": 5,
        },
    },
    {
        "name": "http_alive",
        "module": "collectors.http_alive",
        "class": "HttpAliveCollector",
        "enabled": True,
        "kwargs": {
            "interval": 30,
            "timeout": 10,
            "urls": [
                "https://www.google.com",
                "https://github.com",
            ],
        },
    },
    {
        "name": "system_storage",
        "module": "collectors.local_storage",
        "class": "SystemStatsCollector",
        "enabled": False,
        "kwargs": {
            "interval": 10,
            "storage_path": "./data",
            "max_cache_size": 1000,
            "retry_on_start": True,
        },
    },
    {
        "name": "gpu",
        "module": "collectors.gpu",
        "class": "GPUCollector",
        "enabled": True,
        "kwargs": {
            "interval": 5,
            "process_log_interval": 60,
        },
    },
]


def get_collector_processes(port: int) -> List[subprocess.Popen]:
    """Start all enabled collectors and return their processes."""
    processes = []
    for collector in COLLECTORS:
        if not collector.get("enabled", True):
            continue
        module_name = collector["module"]
        class_name = collector["class"]
        kwargs = collector.get("kwargs", {})
        kwargs["port"] = port

        alert_config_str = str(ALERT_CONFIG).replace("'", '"')

        cmd = f"""
from {module_name} import {class_name}
import json
collector = {class_name}(**{kwargs})
collector.set_alert_config({alert_config_str})
collector.run()
"""
        proc = subprocess.Popen(
            [sys.executable, "-c", cmd],
            cwd=SCRIPT_DIR,
        )
        processes.append((collector["name"], proc))
    return processes


def main():
    parser = argparse.ArgumentParser(description="Run Nexknit Gateway with Collectors")
    parser.add_argument("--url", type=str, help="Cloudflare Worker URL")
    parser.add_argument("--api-key", type=str, help="API Key")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Gateway port (default: {DEFAULT_PORT})")
    parser.add_argument("--alert-target", type=str, default=ALERT_CONFIG["target"], help="Alert target (email/phone)")
    parser.add_argument("--alert-type", type=str, choices=["stdout", "webhook"], default="stdout", help="Alert type")
    parser.add_argument("--alert-webhook", type=str, default="", help="Webhook URL for alerts")
    args = parser.parse_args()

    if args.alert_target:
        ALERT_CONFIG["target"] = args.alert_target
    if args.alert_type:
        ALERT_CONFIG["type"] = args.alert_type
    if args.alert_webhook:
        ALERT_CONFIG["webhook_url"] = args.alert_webhook

    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║ Nexknit - Starting Gateway & Collectors                          ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")

    gateway_cmd = [sys.executable, GATEWAY_SCRIPT]
    if args.url:
        gateway_cmd.extend(["--url", args.url])
    if args.api_key:
        gateway_cmd.extend(["--api-key", args.api_key])

    gateway_process = subprocess.Popen(
        gateway_cmd,
        cwd=SCRIPT_DIR,
    )

    collector_processes = get_collector_processes(args.port)

    print(f"[START] Gateway started (PID: {gateway_process.pid})")
    print(f"[INFO] Gateway listening on port {args.port}")
    print(f"[INFO] Alert target: {ALERT_CONFIG['target']}")
    print(f"[INFO] Alert type: {ALERT_CONFIG['type']}")
    for name, proc in collector_processes:
        print(f"[START] Collector '{name}' started (PID: {proc.pid})")
    print("\nPress Ctrl+C to stop all processes\n")

    try:
        gateway_process.wait()
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")
        gateway_process.terminate()
        for name, proc in collector_processes:
            proc.terminate()
            proc.wait()
            print(f"[STOP] Collector '{name}' stopped")
        gateway_process.wait()
        print("[STOP] All processes stopped")


if __name__ == "__main__":
    main()