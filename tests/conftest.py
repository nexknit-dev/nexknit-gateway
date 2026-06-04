"""Shared fixtures and configuration for all tests"""

import pytest
import socket
import threading
import time
import asyncio
from unittest.mock import patch, MagicMock


@pytest.fixture(scope="session")
def event_loop():
    """Create a shared event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def mock_server():
    """Create a mock TCP server for testing"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("127.0.0.1", 0))
    server_socket.listen(5)
    
    received_messages = []
    server_thread = None
    running = True
    
    def handle_client(conn, addr):
        buffer = b""
        while running:
            try:
                conn.settimeout(1.0)
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data
                if b"\n" in buffer:
                    lines = buffer.split(b"\n")
                    for line in lines[:-1]:
                        received_messages.append(line.decode("utf-8"))
                    buffer = lines[-1]
            except socket.timeout:
                continue
            except Exception:
                break
        conn.close()
    
    def server_loop():
        while running:
            try:
                server_socket.settimeout(1.0)
                conn, addr = server_socket.accept()
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue
    
    server_thread = threading.Thread(target=server_loop, daemon=True)
    server_thread.start()
    
    host, port = server_socket.getsockname()
    
    yield {
        "host": host,
        "port": port,
        "messages": received_messages,
        "clear": lambda: received_messages.clear()
    }
    
    running = False
    if server_thread:
        time.sleep(0.1)
    server_socket.close()


@pytest.fixture
def mock_nvidia_smi():
    """Mock nvidia-smi output"""
    return {
        "available": True,
        "output": """NVIDIA-SMI 535.104.05   Driver Version: 535.104.05   CUDA Version: 12.2

Attached GPUs:
0: NVIDIA GeForce RTX 4090
1: NVIDIA GeForce RTX 3080
"""
    }


@pytest.fixture
def mock_psutil():
    """Mock psutil module"""
    mock = MagicMock()
    mock.cpu_percent.return_value = 42.5
    mock.virtual_memory.return_value = MagicMock(
        percent=65.2,
        total=16 * 1024**3,
        used=10 * 1024**3
    )
    mock.disk_usage.return_value = MagicMock(percent=45.0)
    return mock


@pytest.fixture
def alert_config():
    """Default alert configuration for testing"""
    return {
        "enabled": True,
        "type": "stdout",
        "target": "test@example.com",
        "webhook_url": ""
    }
