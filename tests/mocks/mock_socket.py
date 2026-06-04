"""Mock socket module for testing TCP communications"""

import socket
from unittest.mock import MagicMock, patch


class MockSocket:
    """Mock socket implementation for testing"""
    
    def __init__(self):
        self._connected = False
        self._sent_data = []
        self._closed = False
    
    def connect(self, address):
        self._connected = True
        self._address = address
    
    def sendall(self, data):
        if not self._connected:
            raise socket.error("Not connected")
        self._sent_data.append(data)
    
    def close(self):
        self._connected = False
        self._closed = True


class MockSocketModule:
    """Mock socket module"""
    
    AF_INET = socket.AF_INET
    SOCK_STREAM = socket.SOCK_STREAM
    SO_REUSEADDR = socket.SO_REUSEADDR
    
    def __init__(self):
        self._sockets = []
        self._connect_error = False
        self._send_error = False
    
    def socket(self, family=None, type=None, proto=0):
        sock = MagicMock()
        sock._real_socket = MockSocket()
        
        def connect(address):
            if self._connect_error:
                raise socket.error("Connection refused")
            sock._real_socket.connect(address)
        
        def sendall(data):
            if self._send_error:
                raise socket.error("Send failed")
            sock._real_socket.sendall(data)
        
        def close():
            sock._real_socket.close()
        
        sock.connect = connect
        sock.sendall = sendall
        sock.close = close
        sock.settimeout = MagicMock()
        
        self._sockets.append(sock)
        return sock
    
    def set_connect_error(self, value=True):
        """Simulate connection errors"""
        self._connect_error = value
    
    def set_send_error(self, value=True):
        """Simulate send errors"""
        self._send_error = value
    
    def get_sent_data(self):
        """Get all data sent through mock sockets"""
        all_data = []
        for sock in self._sockets:
            all_data.extend(sock._real_socket._sent_data)
        return all_data
    
    def reset(self):
        """Reset mock state"""
        self._sockets = []
        self._connect_error = False
        self._send_error = False


def patch_socket():
    """Create a patch for socket module"""
    mock_module = MockSocketModule()
    patcher = patch("socket.socket", mock_module.socket)
    return patcher, mock_module
