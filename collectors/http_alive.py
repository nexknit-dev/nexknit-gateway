#!/usr/bin/env python3
"""Nexknit HTTP Alive Collector - Monitors HTTP endpoints"""

import urllib.request
import time
from typing import Any, Dict, List

from collectors.base import BaseCollector


class HttpAliveCollector(BaseCollector):
    """HTTP Alive Collector - Monitor health status of specified URLs"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 12345,
        interval: int = 30,
        urls: List[str] = None,
        timeout: int = 10,
    ):
        super().__init__(host, port, interval)
        self._urls = urls or ["https://www.google.com"]
        self._timeout = timeout
        self._alert_threshold = 2

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract main domain from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    def collect(self) -> Dict[str, Any]:
        """Collect status for all URLs - each URL has independent status"""
        results = {}
        all_failed = True
        
        for idx, url in enumerate(self._urls):
            status, latency_ms = self._check_url(url)
            domain = self._extract_domain(url)
            
            if status == 0:
                results[f"http_{idx}_status"] = f"{domain}\n⚠️ Network Error\nNetwork may be unavailable"
                print(f"[WARN] HTTP Alive Collector: Cannot reach {url} - network may be unavailable")
            else:
                results[f"http_{idx}_status"] = f"{domain}\n{status}\n{latency_ms}ms"
                if status == 200:
                    all_failed = False

            if status != 200:
                self._check_alert(url, status)

        return results

    def _check_url(self, url: str) -> tuple:
        """Check status of single URL"""
        try:
            start = time.time()
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                latency_ms = int((time.time() - start) * 1000)
                return resp.status, latency_ms
        except Exception as e:
            latency_ms = -1
            return 0, latency_ms

    def _check_alert(self, url: str, status: int):
        """Check if alert needs to be sent"""
        if status == 0:
            self.alert(
                level="ERROR",
                title="HTTP Service Unavailable",
                message=f"URL {url} is unreachable",
                metric_name=f"http_{url}",
                metric_value="DOWN",
            )
        elif status >= 500:
            self.alert(
                level="WARNING",
                title="HTTP Server Error",
                message=f"URL {url} returned status code {status}",
                metric_name=f"http_{url}",
                metric_value=status,
            )

    def metrics_to_lines(self, metrics: Dict[str, Any]) -> list:
        """Convert metrics to protocol lines"""
        lines = []
        for name, value in metrics.items():
            if "_status" in name:
                mtype = "S"
            elif "_latency" in name:
                mtype = "T"
            elif "_url" in name:
                mtype = "S"
            else:
                mtype = "S"
            lines.append(self.format_metric(mtype, name, value))
        return lines

    def _on_success(self, metrics: Dict[str, Any]):
        """Callback when sending succeeds"""
        status_info = []
        for name, value in metrics.items():
            if "_status" in name:
                status_info.append(f"{name.split('_')[1]}:{value}")
        if status_info:
            print(f"[SEND] HTTP Status: {', '.join(status_info)}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Nexknit HTTP Alive Collector")
    parser.add_argument("--host", default="127.0.0.1", help="Gateway address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=12345, help="Gateway port (default: 12345)")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds (default: 30)")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
    parser.add_argument("--url", action="append", help="URL to monitor (can be used multiple times)")
    parser.add_argument(
        "--output", choices=["tcp", "stdout"], default="tcp", help="Output mode (default: tcp)"
    )
    args = parser.parse_args()

    urls = args.url if args.url else ["https://www.google.com"]

    print(f"╔══════════════════════════════════════════════════════════════════╗")
    print(f"║              Nexknit HTTP Alive Collector                         ║")
    print(f"╠══════════════════════════════════════════════════════════════════╣")
    print(f"║ Monitored URLs: {', '.join(urls):<50}                           ║")
    print(f"╚══════════════════════════════════════════════════════════════════╝\n")

    collector = HttpAliveCollector(
        host=args.host,
        port=args.port,
        interval=args.interval,
        urls=urls,
        timeout=args.timeout,
    )
    collector._output_mode = args.output
    collector.run()


if __name__ == "__main__":
    main()