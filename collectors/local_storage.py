#!/usr/bin/env python3
"""Nexknit Local Storage Collector - System Stats with Storage"""

from typing import Any, Dict

from collectors.base import StorageCollector


# Check psutil availability
HAS_PSUTIL = False
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    pass


class SystemStatsCollector(StorageCollector):
    """System stats collector with local storage"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cpu_usage = 0.0
        self._mem_usage = 0.0
        self._warned_psutil = False

    def collect(self) -> Dict[str, Any]:
        """Collect system stats"""
        if not HAS_PSUTIL:
            if not self._warned_psutil:
                warning_msg = "[WARN] psutil library not installed. Please install it with 'pip install psutil' to use SystemStatsCollector."
                print(warning_msg)
                self._warned_psutil = True
            return {
                "cpu_percent": 0.0,
                "mem_percent": 0.0,
                "mem_total_mb": 0.0,
                "mem_used_mb": 0.0,
                "status": "⚠️ System stats unavailable - Install psutil: pip install psutil"
            }

        try:
            self._cpu_usage = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            self._mem_usage = mem.percent

            return {
                "cpu_percent": self._cpu_usage,
                "mem_percent": self._mem_usage,
                "mem_total_mb": round(mem.total / (1024**2), 2),
                "mem_used_mb": round(mem.used / (1024**2), 2),
            }
        except Exception as e:
            error_msg = f"[ERROR] Failed to collect system stats: {e}"
            print(error_msg)
            return {
                "cpu_percent": 0.0,
                "mem_percent": 0.0,
                "mem_total_mb": 0.0,
                "mem_used_mb": 0.0,
                "status": f"⚠️ Error collecting system stats: {str(e)}"
            }

    def _on_success(self, metrics: Dict[str, Any]):
        """Callback when sending succeeds"""
        if "cpu_percent" in metrics and "mem_percent" in metrics:
            print(f"[SEND] CPU: {metrics['cpu_percent']}%, Mem: {metrics['mem_percent']}%")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Nexknit Local Storage Collector")
    parser.add_argument("--host", default="127.0.0.1", help="Gateway address")
    parser.add_argument("--port", type=int, default=12345, help="Gateway port")
    parser.add_argument("--interval", type=int, default=5, help="Collection interval")
    parser.add_argument("--storage-path", default="./data", help="Local storage path")
    parser.add_argument("--output", choices=["tcp", "stdout"], default="tcp", help="Output mode")
    args = parser.parse_args()

    print(f"╔══════════════════════════════════════════════════════════════════╗")
    print(f"║         Nexknit Local Storage Collector                          ║")
    print(f"╠══════════════════════════════════════════════════════════════════╣")
    print(f"║ Storage Path: {args.storage_path:<50}                           ║")
    print(f"╚══════════════════════════════════════════════════════════════════╝\n")

    if not HAS_PSUTIL:
        print("[WARN] psutil not installed. Collector will return default values.\n")

    collector = SystemStatsCollector(
        host=args.host,
        port=args.port,
        interval=args.interval,
        storage_path=args.storage_path,
    )
    collector._output_mode = args.output
    collector.run()


if __name__ == "__main__":
    main()