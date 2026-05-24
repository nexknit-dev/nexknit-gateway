#!/usr/bin/env python3
"""Nexknit Collector Template

HOW TO USE:
1. Copy this file
2. Subclass BaseCollector
3. Override collect() method to return your metrics

PROTOCOL SIMPLE: Type|Name|Value
- I = Index: numeric value that changes sometimes (disk usage, memory)
- T = Trend: numeric value that changes often (CPU, temperature)
- S = Status: text value (hostname, phase, state)
- L = Log: log entry (events, results)

EXAMPLE METRICS:
("T", "cpu_temp", "42.5")
("S", "phase", "training")
("L", "epoch", "loss=0.34, acc=0.91")
"""

import argparse
import socket
import time
import random
from datetime import datetime


VERSION = "1.0.0"


class BaseCollector:
    """Override collect() to return your metrics.
    
    Returns: list of tuples (type_char, name, value)
    """

    def collect(self):
        """REPLACE THIS METHOD WITH YOUR CODE.
        
        Return list of metrics: [(type, name, value), ...]
        Type options: I, T, S, L
        """
        # EXAMPLE - replace with your real metrics
        return [
            ("T", "temperature", f"{random.uniform(35.0, 45.0):.1f}"),
            ("S", "status", "running"),
            ("L", "heartbeat", f"{datetime.now().isoformat()}"),
        ]


def send_message(host: str, port: int, msg_type: str, name: str, value: str) -> bool:
    """Send one metric to the Nexknit gateway (short TCP connection)."""
    message = f"{msg_type}|{name}|{value}\n"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            sock.connect((host, port))
            sock.sendall(message.encode("utf-8"))
        return True
    except Exception:
        return False


def run_collector(collector: BaseCollector, host: str, port: int, interval: int):
    """Main loop: collect and send metrics every `interval` seconds."""
    print(f"\nNexknit Collector; You can delete this log once you think its board.")
    print(f"Target: {host}:{port}  Interval: {interval}s\n")

    fail_count = 0
    max_fail = 3

    while True:
        try:
            metrics = collector.collect()

            sent = 0
            for msg_type, name, value in metrics:
                if send_message(host, port, msg_type, name, value):
                    sent += 1
                else:
                    fail_count += 1
                    break
            else:
                fail_count = 0
                if sent > 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent {sent} metrics")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] No metrics this cycle")

            if fail_count >= max_fail:
                print("[WARN] Too many failures, pausing one cycle...")
                time.sleep(interval * 2)
                fail_count = 0

            time.sleep(interval)

        except KeyboardInterrupt:
            print("\nCollector stopped.")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nexknit Collector Template")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=12345)
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()

    collector = BaseCollector()
    run_collector(collector, args.host, args.port, args.interval)