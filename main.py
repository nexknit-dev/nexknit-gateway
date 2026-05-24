#!/usr/bin/env python3
"""Nexknit Gateway - Minimal Single File Version"""

# URL 解析逻辑已完成：自动去除末尾反斜杠



import argparse
import asyncio
import json
import logging
import random
import string
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


# === Version Info ===


# === Configuration ===
CONFIG: Dict[str, Any] = {
    "gateway": {
        "log_level": "INFO",
        "node_name": "Nexknit_Dev",
        "max_queue_size": 2000,
    },
    "tcp_server": {
        "host": "127.0.0.1",
        "port": 12345,
        "read_timeout": 1.0,
        "max_read_size": 1024,
    },
    "cloudflare": {
        "worker_url": "",
        "api_key": "",
        "interval": 5,
        "history_depth": 2,
        "heartbeat_interval": 6,
        "request_timeout": 5.0,
        "shutdown_timeout": 10.0,
    },
}


def print_banner():
    """Print startup banner."""
    banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    Nexknit Gateway                               ║
║══════════════════════════════════════════════════════════════════║
║ A lightweight TCP-to-Cloudflare gateway for real-time metrics    ║
║ If you find this project useful, please give us a star!          ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def load_config(path: str = None, url: str = None, api_key: str = None) -> tuple[Dict[str, Any], bool]:
    """Load configuration from file and apply overrides.

    If command line parameters differ from config file, persist them to file.
    
    Returns:
        tuple: (config, is_first_start) where is_first_start is True if config file was just created
    """
    script_dir = Path(__file__).parent
    default_config_path = script_dir / "config.json"

    if not path:
        path = default_config_path

    path = Path(path)
    config_modified = False
    is_first_start = False

    if not path.exists():
        is_first_start = True
        logging.info(f"Config file not found at {path}, creating default config")
        # Create a copy to avoid modifying the global CONFIG
        result = CONFIG.copy()
        result["gateway"] = CONFIG["gateway"].copy()
        result["tcp_server"] = CONFIG["tcp_server"].copy()
        result["cloudflare"] = CONFIG["cloudflare"].copy()

        if url:
            result["cloudflare"]["worker_url"] = url
            config_modified = True
        if api_key:
            result["cloudflare"]["api_key"] = api_key
            config_modified = True

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            logging.info(f"Config file created at {path}")
        except IOError as e:
            logging.warning(f"Failed to create config file: {e}")

        return result, is_first_start

    # Load existing config file
    try:
        with open(path, "r", encoding="utf-8") as f:
            file_config: Dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse config file: {e}, using default config")
        file_config = {}
    except IOError as e:
        logging.error(f"Failed to read config file: {e}, using default config")
        file_config = {}

    # Create a copy to avoid modifying the global CONFIG
    result = CONFIG.copy()
    result["gateway"] = CONFIG["gateway"].copy()
    result["tcp_server"] = CONFIG["tcp_server"].copy()
    result["cloudflare"] = CONFIG["cloudflare"].copy()

    # Update with file config (deep merge)
    if "gateway" in file_config:
        result["gateway"].update(file_config["gateway"])
    if "tcp_server" in file_config:
        result["tcp_server"].update(file_config["tcp_server"])
    if "cloudflare" in file_config:
        result["cloudflare"].update(file_config["cloudflare"])

    # Check if command line parameters differ from config file
    if url and url != result["cloudflare"].get("worker_url", ""):
        # Auto-remove trailing slash from URL
        result["cloudflare"]["worker_url"] = url.rstrip("/")
        config_modified = True
        logging.info(f"Updating Worker URL from command line")

    if api_key and api_key != result["cloudflare"].get("api_key", ""):
        result["cloudflare"]["api_key"] = api_key
        config_modified = True
        logging.info(f"Updating API Key from command line")

    # Persist changes if any
    if config_modified:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            logging.info(f"Config file updated at {path}")
        except IOError as e:
            logging.warning(f"Failed to write config file: {e}")

    return result, is_first_start


# === Utils ===
def get_ts() -> int:
    """Get current timestamp in milliseconds."""
    return int(datetime.now().timestamp() * 1000)


# === Protocol Parser ===
def parse_message(raw: str) -> Dict[str, Any]:
    """Parse protocol message: type|name|content"""
    parts = raw.strip().split("|", 2)
    if len(parts) != 3:
        return {"type": "Log", "name": "WrongLog", "content": raw, "time": get_ts()}

    mtype, name, content = parts[0].strip().capitalize(), parts[1].strip(), parts[2].strip()
    
    if not name:
        return {"type": "Log", "name": "WrongLog", "content": raw, "time": get_ts()}

    if mtype in ("I", "Index", "T", "Trend"):
        try:
            content = float(content)
            mtype = "Index" if mtype in ("I", "Index") else "Trend"
        except ValueError:
            return {"type": "Log", "name": "WrongLog", "content": raw, "time": get_ts()}
    elif mtype in ("S", "Status"):
        mtype = "Status"
    else:
        mtype = "Log"

    return {"type": mtype, "name": name, "content": content, "time": get_ts()}

# === Data Aggregation ===
def aggregate(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[List[Any]]]]:
    """Aggregate items by type and name."""
    result: Dict[str, Dict[str, List[List[Any]]]] = {}
    for item in items:
        t = item["type"]
        n = item["name"]
        if t not in result:
            result[t] = {}
        if n not in result[t]:
            result[t][n] = []
        result[t][n].append([item["time"], item["content"]])
    return result


def make_payload(node_name: str, batches: Dict[str, Any]) -> Dict[str, Any]:
    """Create final payload structure."""
    return {"n": node_name, "t": get_ts(), "p": batches}


# === HTTP Sender ===
def http_post(url: str, api_key: str, payload: Dict[str, Any], timeout: float = 5.0):
    """Send payload to Cloudflare Worker."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "X-Nexknit-Key": api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status not in (200, 201):
            raise RuntimeError(f"Server returned {resp.status}")


async def send_async(url: str, api_key: str, payload: Dict[str, Any], timeout: float):
    """Async wrapper for HTTP POST."""
    await asyncio.to_thread(http_post, url, api_key, payload, timeout)


# === TCP Collector ===
async def tcp_server(host: str, port: int, max_size: int, timeout: float, queue: asyncio.Queue):
    """Simple TCP server that parses and queues messages."""
    async def handle_client(reader, writer):
        try:
            data = await asyncio.wait_for(reader.read(max_size), timeout=timeout)
            if data:
                msg = data.decode("utf-8", errors="replace")
                parsed = parse_message(msg)
                if not queue.full():
                    await queue.put(parsed)
                else: 
                    logging.warning("Queue full, dropping message")
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            logging.warning(f"TCP error: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    server = await asyncio.start_server(handle_client, host, port)
    addr = server.sockets[0].getsockname()
    logging.info(f"Listening on {addr[0]}:{addr[1]}")
    async with server:
        await server.serve_forever()


# === Sync Loop ===
async def sync_loop(queue: asyncio.Queue, config: dict):
    """Periodically sync data to Cloudflare."""
    cf = config["cloudflare"]
    gateway = config["gateway"]
    batch_history = []
    send_counter = cf["heartbeat_interval"] - 1
    running = True

    while running:
        await asyncio.sleep(cf["interval"])
        
        # Collect items from queue
        items = []
        while not queue.empty():
            try:
                items.append(queue.get_nowait())
            except asyncio.QueueEmpty:
                break

        # Add heartbeat
        send_counter += 1
        if send_counter % cf["heartbeat_interval"] == 0:
            send_counter = 0
            items.append({"type": "Status", "name": "heartbeat", "content": "Online", "time": get_ts()})

        # Always process items if there are any (including heartbeat-only)
        if items:
            # Aggregate and send
            batch_key = f"{get_ts()}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
            batch_history.append((batch_key, aggregate(items)))
            
            # Keep only recent batches
            while len(batch_history) > cf["history_depth"] + 1:
                batch_history.pop(0)

        # Send combined payload
        payload = make_payload(gateway["node_name"], dict(reversed(batch_history)))
        payload_size = len(json.dumps(payload).encode("utf-8"))
        
        try:
            await send_async(f"{cf['worker_url']}/api/push", cf["api_key"], payload, cf["request_timeout"])
            logging.info(
                f"[SEND] Batches: {len(batch_history)} | Items: {len(items)} | "
                f"Size: {payload_size} bytes | Time: {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            logging.error(f"[SEND FAILED] {e}")


# === Main ===
def main():
    parser = argparse.ArgumentParser(description="Nexknit Gateway")
    parser.add_argument("--config", type=str, help="Config file path")
    parser.add_argument("--url", type=str, help="Cloudflare Worker URL")
    parser.add_argument("--api-key", type=str, help="API Key")
    args = parser.parse_args()

    # Initialize logging FIRST before loading config
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    config, is_first_start = load_config(args.config, args.url, args.api_key)

    # Update log level from config
    logging.getLogger().setLevel(getattr(logging, config["gateway"]["log_level"]))

    print_banner()

    # Check for first start and show welcome message
    if is_first_start:
        logging.info("=" * 60)
        logging.info("[WELCOME] First start detected!")
        logging.info("[WELCOME] Please visit GitHub QA.1 for detailed quota calculation and usage guide")
        logging.info("[WELCOME] GitHub: https://github.com/your-repo/docs/QA.1.md")
        logging.info("=" * 60)

    if not config["cloudflare"]["worker_url"]:
        logging.error("No Worker URL configured")
        sys.exit(1)

    tcp_cfg = config["tcp_server"]
    cf_cfg = config["cloudflare"]
    gw_cfg = config["gateway"]
    
    logging.info("=" * 60)
    logging.info(f"[CONFIG] Node Name: {gw_cfg['node_name']}")
    logging.info(f"[CONFIG] TCP Server: {tcp_cfg['host']}:{tcp_cfg['port']}")
    logging.info(f"[CONFIG] Worker URL: {cf_cfg['worker_url']}")
    logging.info(f"[CONFIG] Sync Interval: {cf_cfg['interval']}s")
    logging.info(f"[CONFIG] History Depth: {cf_cfg['history_depth']}")
    logging.info(f"[CONFIG] Heartbeat: Every {cf_cfg['heartbeat_interval']} cycles")
    logging.info(f"[CONFIG] Max Queue Size: {gw_cfg['max_queue_size']}")
    logging.info("=" * 60)

    queue = asyncio.Queue(maxsize=gw_cfg["max_queue_size"])

    async def run():
        await asyncio.gather(
            tcp_server(
                host=tcp_cfg["host"],
                port=tcp_cfg["port"],
                max_size=tcp_cfg["max_read_size"],
                timeout=tcp_cfg["read_timeout"],
                queue=queue,
            ),
            sync_loop(queue, config),
        )

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logging.info("Received interrupt, exiting...")


if __name__ == "__main__":
    main()
