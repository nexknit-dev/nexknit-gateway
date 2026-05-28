#!/usr/bin/env python3
"""Nexknit Collectors - Base Collector with Local Storage"""

import json
import os
import time
from typing import Any, Dict, List, Optional

from .base_collector import BaseCollector


class StorageCollector(BaseCollector):
    """Base collector class with local storage capability

    Features:
    - Save collected data to local files
    - Automatically cache failed messages locally
    - Support configurable storage path and format
    - Support automatic retry of cached data
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 12345,
        interval: int = 5,
        storage_path: str = "./data",
        storage_format: str = "json",
        max_cache_size: int = 1000,
        retry_on_start: bool = True,
    ):
        super().__init__(host, port, interval)
        self._storage_path = storage_path
        self._storage_format = storage_format.lower()
        self._max_cache_size = max_cache_size
        self._retry_on_start = retry_on_start
        self._cache_file = os.path.join(storage_path, "failed_cache.json")
        self._history_file = os.path.join(storage_path, "history.json")
        self._ensure_storage_dir()

        if self._retry_on_start:
            self._retry_failed_data()

    def _ensure_storage_dir(self):
        """Ensure storage directory exists"""
        os.makedirs(self._storage_path, exist_ok=True)

    def _retry_failed_data(self):
        """Retry previously failed data on startup"""
        if os.path.exists(self._cache_file):
            try:
                with open(self._cache_file, "r") as f:
                    cached_data = json.load(f)
                    if cached_data:
                        print(f"[RETRY] Found {len(cached_data)} cached records to retry")
                        for record in cached_data[:10]:
                            message = record.get("message", "")
                            if message:
                                success = self.send_tcp_message(message)
                                if success:
                                    cached_data.remove(record)
                        with open(self._cache_file, "w") as f:
                            json.dump(cached_data, f)
                        print(f"[RETRY] Retry completed, {len(cached_data)} records remaining")
            except Exception as e:
                print(f"[ERROR] Failed to load cache: {e}")

    def _cache_failed_data(self, message: str):
        """Cache failed message to local storage"""
        try:
            cached_data = []
            if os.path.exists(self._cache_file):
                with open(self._cache_file, "r") as f:
                    cached_data = json.load(f)

            record = {
                "message": message,
                "timestamp": time.time(),
                "collector": self.__class__.__name__,
            }
            cached_data.append(record)

            if len(cached_data) > self._max_cache_size:
                cached_data = cached_data[-self._max_cache_size:]

            with open(self._cache_file, "w") as f:
                json.dump(cached_data, f, indent=2)

            print(f"[CACHE] Failed message cached")
        except Exception as e:
            print(f"[ERROR] Failed to cache data: {e}")

    def _save_to_history(self, metrics: Dict[str, Any]):
        """Save collected data to history file"""
        try:
            history = []
            if os.path.exists(self._history_file):
                with open(self._history_file, "r") as f:
                    history = json.load(f)

            record = {
                "timestamp": time.time(),
                "metrics": metrics,
                "collector": self.__class__.__name__,
            }
            history.append(record)

            max_history = 1000
            if len(history) > max_history:
                history = history[-max_history:]

            with open(self._history_file, "w") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to save history: {e}")

    def send_tcp_message(self, message: str) -> bool:
        """Send message, cache locally if failed"""
        success = super().send_tcp_message(message)
        if not success:
            self._cache_failed_data(message)
        return success

    def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send metrics and save to history"""
        self._save_to_history(metrics)
        return super().send_metrics(metrics)

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical data"""
        if os.path.exists(self._history_file):
            try:
                with open(self._history_file, "r") as f:
                    history = json.load(f)
                    return history[-limit:]
            except Exception as e:
                print(f"[ERROR] Failed to read history: {e}")
        return []

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        if os.path.exists(self._cache_file):
            try:
                with open(self._cache_file, "r") as f:
                    cached_data = json.load(f)
                    return {"count": len(cached_data)}
            except Exception as e:
                print(f"[ERROR] Failed to read cache: {e}")
        return {"count": 0}