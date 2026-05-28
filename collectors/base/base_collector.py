#!/usr/bin/env python3
"""Nexknit Collectors - Base Collector (without storage)"""

import socket
import time
import urllib.request
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class BaseCollector(ABC):
    """Base collector class that defines unified interface and data sending protocol"""

    PROTOCOL_TYPES = {
        "I": "Index",
        "Index": "Index",
        "T": "Trend",
        "Trend": "Trend",
        "L": "Log",
        "Log": "Log",
        "S": "Status",
        "Status": "Status",
    }

    ALERT_LEVELS = ["INFO", "WARNING", "ERROR", "CRITICAL"]

    def __init__(self, host: str = "127.0.0.1", port: int = 12345, interval: int = 5):
        self.host = host
        self.port = port
        self.interval = interval
        self._sock: Optional[socket.socket] = None
        self._consecutive_failures = 0
        self._max_failures = 3
        self._output_mode = "tcp"
        self._alert_history: Dict[str, float] = {}
        self._alert_cooldown = 300
        self._alert_config: Dict[str, Any] = {}

    def set_alert_config(self, config: Dict[str, Any]):
        """Set alert configuration"""
        self._alert_config = config

    def alert(
        self,
        level: str,
        title: str,
        message: str,
        metric_name: str = None,
        metric_value: Any = None,
    ):
        """Send an alert

        Args:
            level: Alert level (INFO, WARNING, ERROR, CRITICAL)
            title: Alert title
            message: Alert message
            metric_name: Associated metric name (for deduplication)
            metric_value: Associated metric value
        """
        if level not in self.ALERT_LEVELS:
            print(f"[ALERT] Invalid alert level: {level}")
            return

        if not self._alert_config.get("enabled", False):
            return

        if metric_name:
            key = f"{level}_{metric_name}"
            last_alert = self._alert_history.get(key, 0)
            if time.time() - last_alert < self._alert_cooldown:
                print(f"[ALERT] Alert cooldown active for {key}")
                return
            self._alert_history[key] = time.time()

        self._send_alert(level, title, message, metric_name, metric_value)

    def _send_alert(
        self,
        level: str,
        title: str,
        message: str,
        metric_name: str = None,
        metric_value: Any = None,
    ):
        """Internal method to send alert"""
        print(f"[{level}] {title}: {message}")

        alert_type = self._alert_config.get("type", "stdout")

        if alert_type == "webhook":
            self._send_webhook_alert(level, title, message, metric_name, metric_value)
        elif alert_type == "stdout":
            pass
        else:
            print(f"[ALERT] Unknown alert type: {alert_type}")

    def _send_webhook_alert(
        self,
        level: str,
        title: str,
        message: str,
        metric_name: str = None,
        metric_value: Any = None,
    ):
        """Send alert via webhook"""
        webhook_url = self._alert_config.get("webhook_url")
        if not webhook_url:
            print("[ALERT] Webhook URL not configured")
            return

        payload = {
            "level": level,
            "title": title,
            "message": message,
            "collector": self.__class__.__name__,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "timestamp": datetime.now().isoformat(),
            "target": self._alert_config.get("target", ""),
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    print(f"[ALERT] Webhook alert sent successfully")
                else:
                    print(f"[ALERT] Webhook alert failed: {resp.status}")
        except Exception as e:
            print(f"[ALERT] Failed to send webhook: {e}")

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Collect data and return metrics dictionary"""
        pass

    def parse_message(self, raw: str) -> Dict[str, Any]:
        """Parse protocol message: type|name|content

        Returns:
            Dict with keys: type, name, content, time
        """
        parts = raw.strip().split("|", 2)
        if len(parts) != 3:
            return {"type": "Log", "name": "WrongLog", "content": raw, "time": self._get_ts()}

        mtype, name, content = parts[0].strip().capitalize(), parts[1].strip(), parts[2].strip()

        if not name:
            return {"type": "Log", "name": "WrongLog", "content": raw, "time": self._get_ts()}

        if mtype in ("I", "Index", "T", "Trend"):
            try:
                content = float(content)
                mtype = "Index" if mtype in ("I", "Index") else "Trend"
            except ValueError:
                return {"type": "Log", "name": "WrongLog", "content": raw, "time": self._get_ts()}
        elif mtype in ("S", "Status"):
            mtype = "Status"
        else:
            mtype = "Log"

        return {"type": mtype, "name": name, "content": content, "time": self._get_ts()}

    def format_metric(self, mtype: str, name: str, value: Any) -> str:
        """Format metric to protocol string"""
        return f"{mtype}|{name}|{value}"

    def send_tcp_message(self, message: str) -> bool:
        """Send a single TCP message (short connection mode)"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                sock.connect((self.host, self.port))
                sock.sendall(message.encode("utf-8"))
            return True
        except Exception:
            return False

    def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send metrics dictionary via TCP"""
        lines = self.metrics_to_lines(metrics)
        success = True
        for line in lines:
            if not self.send_tcp_message(line + "\n"):
                success = False
        return success

    def metrics_to_lines(self, metrics: Dict[str, Any]) -> List[str]:
        """Convert metrics dictionary to protocol line list, can be overridden by subclass"""
        lines = []
        for name, value in metrics.items():
            if isinstance(value, float):
                mtype = "T"
            elif isinstance(value, int):
                mtype = "T"
            elif isinstance(value, str):
                mtype = "S"
            else:
                mtype = "S"
            lines.append(self.format_metric(mtype, name, value))
        return lines

    def run(self):
        """Run the main collection loop"""
        print(f"[INFO] Collector: {self.__class__.__name__}")
        print(f"[INFO] Target: {self.host}:{self.port}")
        print(f"[INFO] Interval: {self.interval}s")
        if self._alert_config.get("enabled", False):
            print(f"[INFO] Alerts: Enabled ({self._alert_config.get('type', 'stdout')})")
        print()

        while True:
            try:
                metrics = self.collect()
                if self._output_mode == "tcp":
                    success = self.send_metrics(metrics)
                    if success:
                        self._consecutive_failures = 0
                        self._on_success(metrics)
                    else:
                        self._consecutive_failures += 1
                        self._on_failure(self._consecutive_failures)
                        if self._consecutive_failures >= self._max_failures:
                            print(f"[WARN] Too many failures, switching to stdout mode")
                            self._output_mode = "stdout"
                else:
                    for line in self.metrics_to_lines(metrics):
                        print(line)
                    self._consecutive_failures = 0

                time.sleep(self.interval)

            except KeyboardInterrupt:
                print("\n[INFO] Collector stopped by user")
                break
            except Exception as e:
                print(f"[ERROR] {e}")
                time.sleep(self.interval)

    def _get_ts(self) -> int:
        """Get current timestamp in milliseconds"""
        return int(datetime.now().timestamp() * 1000)

    def _on_success(self, metrics: Dict[str, Any]):
        """Callback when sending succeeds, can be overridden by subclass"""
        pass

    def _on_failure(self, attempt: int):
        """Callback when sending fails, can be overridden by subclass"""
        print(f"[FAIL] Send failed (attempt {attempt}/{self._max_failures})")