#!/usr/bin/env python3
"""Nexknit One-Shot Pusher

SIMPLE PROTOCOL: Type|Name|Value
- I = Index: numeric, changes sometimes (disk, memory)
- T = Trend: numeric, changes often (CPU, temperature) 
- S = Status: text (hostname, phase, state)
- L = Log: log entry (events, results)

USAGE:
python push.py T cpu_temp 42.5
python push.py S phase training
python push.py L epoch "loss=0.34, acc=0.91"

MULTI-LANGUAGE EXAMPLES:

# Python
import socket
sock = socket.socket(); sock.connect(("127.0.0.1", 12345))
sock.sendall(b"T|cpu|42.5\n")

# Bash
echo "T|cpu|42.5" | nc -w 1 127.0.0.1 12345

# Node.js
const net = require('net');
const socket = new net.Socket();
socket.connect(12345, '127.0.0.1', () => {
  socket.write('T|cpu|42.5\n'); socket.end();
});

# Go
package main
import "net"
func main() {
  conn, _ := net.Dial("tcp", "127.0.0.1:12345")
  conn.Write([]byte("T|cpu|42.5\n"))
}

# Java
Socket socket = new Socket("127.0.0.1", 12345);
socket.getOutputStream().write("T|cpu|42.5\n".getBytes());

# C#
using System.Net.Sockets;
TcpClient client = new TcpClient("127.0.0.1", 12345);
client.GetStream().Write(Encoding.UTF8.GetBytes("T|cpu|42.5\n"));

# PHP
$sock = fsockopen("127.0.0.1", 12345);
fwrite($sock, "T|cpu|42.5\n"); fclose($sock);

# Ruby
require 'socket'
TCPSocket.open('127.0.0.1', 12345) { |s| s.write("T|cpu|42.5\n") }

# Rust
use std::net::TcpStream;
let mut stream = TcpStream::connect("127.0.0.1:12345").unwrap();
stream.write_all(b"T|cpu|42.5\n").unwrap();

# Swift
import Foundation
let host = "127.0.0.1"; let port: UInt16 = 12345
let socket = Socket.create(family: .inet, type: .stream, proto: .tcp)
socket?.connect(to: host, port: port)
socket?.write(from: "T|cpu|42.5\n")

# PowerShell
$tcp = New-Object System.Net.Sockets.TCPClient("127.0.0.1",12345)
$stream = $tcp.GetStream()
$bytes = [System.Text.Encoding]::UTF8.GetBytes("T|cpu|42.5`n")
$stream.Write($bytes,0,$bytes.Length)
"""

import argparse
import socket
import sys


def push(host: str, port: int, msg_type: str, name: str, value: str) -> bool:
    """Send one metric to Nexknit gateway via TCP."""
    message = f"{msg_type}|{name}|{value}\n"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            sock.connect((host, port))
            sock.sendall(message.encode("utf-8"))
        return True
    except Exception as e:
        print(f"Push failed: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Nexknit One-Shot Pusher")
    parser.add_argument("type", default="S", choices=["I", "T", "S", "L"], help="Metric type")
    parser.add_argument("name", default="OneShotTest", help="Metric name")
    parser.add_argument("value", default="Im Here", help="Metric value")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=12345)
    args = parser.parse_args()

    if not push(args.host, args.port, args.type, args.name, args.value):
        sys.exit(1)


if __name__ == "__main__":
    main()