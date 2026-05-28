#!/usr/bin/env python3
"""Nexknit GPU Collector - Monitors NVIDIA GPU status and processes"""

import subprocess
import json
import time
from typing import Any, Dict, List, Optional, Set

from collectors.base import BaseCollector


class GPUCollector(BaseCollector):
    """NVIDIA GPU Collector

    Features:
    - Collect memory usage (used/total)
    - Collect GPU utilization
    - Collect GPU temperature
    - Detect running process changes
    - Log process changes
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 12345,
        interval: int = 5,
        process_log_interval: int = 60,
    ):
        super().__init__(host, port, interval)
        self._process_log_interval = process_log_interval
        self._last_process_log = 0
        self._previous_processes: Set[str] = set()
        self._has_nvidia_smi = self._check_nvidia_smi()

    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_gpu_info(self) -> List[Dict[str, Any]]:
        """Get GPU information"""
        if not self._has_nvidia_smi:
            return []

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []

            gpus = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    gpus.append({
                        "index": int(parts[0]),
                        "name": parts[1],
                        "mem_used": int(parts[2]),
                        "mem_total": int(parts[3]),
                        "utilization": int(parts[4]),
                        "temperature": int(parts[5]),
                    })
            return gpus
        except Exception as e:
            print(f"[ERROR] Failed to get GPU info: {e}")
            return []

    def _get_gpu_processes(self) -> List[Dict[str, Any]]:
        """Get processes using GPU"""
        if not self._has_nvidia_smi:
            return []

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-compute-apps=pid,process_name,used_memory",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return []

            processes = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    processes.append({
                        "pid": int(parts[0]),
                        "name": parts[1],
                        "mem_used": int(parts[2]),
                    })
            return processes
        except Exception as e:
            print(f"[ERROR] Failed to get GPU processes: {e}")
            return []

    def _detect_process_changes(self, current_processes: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Detect process changes"""
        current_keys = set()
        for p in current_processes:
            key = f"{p['pid']}:{p['name']}"
            current_keys.add(key)

        added = list(current_keys - self._previous_processes)
        removed = list(self._previous_processes - current_keys)
        self._previous_processes = current_keys

        return {"added": added, "removed": removed}

    def collect(self) -> Dict[str, Any]:
        """Collect GPU data"""
        if not self._has_nvidia_smi:
            warning_msg = "[WARN] NVIDIA GPU not detected. Please install NVIDIA drivers and nvidia-smi tool to use GPU collector."
            print(warning_msg)
            return {"gpu_status": "⚠️ GPU Unavailable - Please install NVIDIA drivers"}

        gpus = self._get_gpu_info()
        processes = self._get_gpu_processes()

        result = {}

        for gpu in gpus:
            idx = gpu["index"]
            mem_used_gb = gpu["mem_used"] / 1024
            mem_total_gb = gpu["mem_total"] / 1024
            mem_percent = (gpu["mem_used"] / gpu["mem_total"]) * 100

            # Each GPU has independent status
            result[f"gpu_{idx}_status"] = (
                f"{gpu['name']}\n"
                f"Mem: {mem_used_gb:.1f}/{mem_total_gb:.1f}GB ({mem_percent:.0f}%)\n"
                f"Util: {gpu['utilization']}%\n"
                f"Temp: {gpu['temperature']}C"
            )

        # Check process changes
        now = time.time()
        if now - self._last_process_log >= self._process_log_interval:
            changes = self._detect_process_changes(processes)
            if changes["added"] or changes["removed"]:
                log_message = "GPU Process Changes: "
                if changes["added"]:
                    log_message += f"Added: {', '.join(changes['added'])}; "
                if changes["removed"]:
                    log_message += f"Removed: {', '.join(changes['removed'])}"
                self.send_tcp_message(self.format_metric("L", "GPU_Process_Changes", log_message))
                self._last_process_log = now

        # Return results, each GPU has independent status
        if result:
            return result
        else:
            return {"gpu_status": "No GPU data"}

    def metrics_to_lines(self, metrics: Dict[str, Any]) -> List[str]:
        """Convert metrics to protocol lines - Status type only"""
        lines = []
        for name, value in metrics.items():
            mtype = "S"  # All metrics are Status type
            lines.append(self.format_metric(mtype, name, value))
        return lines

    def _on_success(self, metrics: Dict[str, Any]):
        """Callback when sending succeeds"""
        if "gpu_status" in metrics:
            print(f"[SEND] {metrics['gpu_status']}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Nexknit GPU Collector")
    parser.add_argument("--host", default="127.0.0.1", help="Gateway address")
    parser.add_argument("--port", type=int, default=12345, help="Gateway port")
    parser.add_argument("--interval", type=int, default=5, help="Collection interval")
    parser.add_argument("--process-log-interval", type=int, default=60, help="Process log interval")
    parser.add_argument("--output", choices=["tcp", "stdout"], default="tcp", help="Output mode")
    args = parser.parse_args()

    print(f"╔══════════════════════════════════════════════════════════════════╗")
    print(f"║                Nexknit GPU Collector                            ║")
    print(f"╚══════════════════════════════════════════════════════════════════╝\n")

    collector = GPUCollector(
        host=args.host,
        port=args.port,
        interval=args.interval,
        process_log_interval=args.process_log_interval,
    )
    collector._output_mode = args.output
    collector.run()


if __name__ == "__main__":
    main()