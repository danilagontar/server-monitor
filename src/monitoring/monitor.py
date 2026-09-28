import platform
import socket
import subprocess
import time
from datetime import datetime

import psutil
import requests

from config import BOT_TOKEN, PROXY_URL
from services import load_services


def get_uptime():
    uptime = time.time() - psutil.boot_time()

    days = int(uptime // 86400)
    hours = int((uptime % 86400) // 3600)
    minutes = int((uptime % 3600) // 60)

    return f"{days}d {hours}h {minutes}m"


def get_memory_usage():
    memory = psutil.virtual_memory()

    return {
        "used": memory.used,
        "total": memory.total,
        "percent": memory.percent,
    }


def get_disk_usage():
    disk = psutil.disk_usage("/")

    return {
        "used": disk.used,
        "total": disk.total,
        "percent": disk.percent,
    }


def get_processes(limit=10):
    processes = []
    process_objects = []

    for process in psutil.process_iter(
        [
            "pid",
            "name",
            "cmdline",
            "memory_percent",
        ],
    ):
        try:
            process.cpu_percent(None)
            process_objects.append(process)

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    time.sleep(1)

    for process in process_objects:
        try:
            info = process.info
            cpu = process.cpu_percent(None)

            processes.append({
                "pid": info["pid"],
                "name": info["name"] or "unknown",
                "cmdline": " ".join(info["cmdline"] or []),
                "cpu": cpu,
                "memory": info["memory_percent"] or 0,
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    cpu_processes = sorted(
        processes,
        key=lambda process: process["cpu"],
        reverse=True,
    )

    ram_processes = sorted(
        processes,
        key=lambda process: process["memory"],
        reverse=True,
    )

    total_cpu = sum(
        process["cpu"]
        for process in processes
    )

    cpu_count = psutil.cpu_count() or 1

    total_cpu_percent = min(
        total_cpu / cpu_count,
        100,
    )

    return {
        "all": processes,
        "cpu": cpu_processes[:limit],
        "memory": ram_processes[:limit],
        "total_cpu": total_cpu_percent,
    }


def get_server_status():
    memory = get_memory_usage()
    disk = get_disk_usage()
    processes = get_processes()

    return {
        "hostname": platform.node(),
        "cpu": processes["total_cpu"],
        "memory": memory,
        "disk": disk,
        "uptime": get_uptime(),
    }


def get_docker_status():
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--format",
                "{{.Names}}|{{.Status}}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode != 0:
            return {
                "available": False,
                "error": result.stderr.strip(),
                "containers": [],
            }

        containers = []

        for line in result.stdout.splitlines():
            if not line.strip():
                continue

            name, status = line.split("|", 1)

            containers.append({
                "name": name,
                "status": status,
            })

        return {
            "available": True,
            "error": "",
            "containers": containers,
        }

    except FileNotFoundError:
        return {
            "available": False,
            "error": "Docker не установлен",
            "containers": [],
        }

    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "error": "Docker не отвечает",
            "containers": [],
        }


def get_service_status(service):
    try:
        result = subprocess.run(
            [
                "systemctl",
                "show",
                service,
                "--property=ActiveState",
                "--property=ActiveEnterTimestamp",
                "--value",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        lines = result.stdout.strip().splitlines()

        if len(lines) < 2:
            return {
                "status": "unknown",
                "started_at": None,
            }

        return {
            "status": lines[0],
            "started_at": lines[1],
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "started_at": None,
        }

    except Exception:
        return {
            "status": "unknown",
            "started_at": None,
        }


def get_service_uptime(started_at):
    if not started_at:
        return None

    try:
        parts = started_at.split()

        if len(parts) < 3:
            return None

        started = datetime.strptime(
            f"{parts[1]} {parts[2]}",
            "%Y-%m-%d %H:%M:%S",
        )

        uptime = datetime.now() - started
        total_seconds = int(
            uptime.total_seconds()
        )

        if total_seconds < 0:
            return None

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days > 0:
            return f"Up {days}d {hours}h"

        if hours > 0:
            return f"Up {hours}h {minutes}m"

        return f"Up {minutes}m"

    except (ValueError, IndexError):
        return None


def get_services_status():
    services = []

    for service in load_services():
        data = get_service_status(service)

        services.append({
            "name": service,
            "status": data["status"],
            "uptime": get_service_uptime(
                data["started_at"]
            ),
        })

    return services


def check_internet(host="1.1.1.1", port=443, timeout=3):
    start = time.perf_counter()

    try:
        with socket.create_connection(
            (host, port),
            timeout=timeout,
        ):
            latency = (
                time.perf_counter() - start
            ) * 1000

        return {
            "available": True,
            "latency": latency,
        }

    except OSError:
        return {
            "available": False,
            "latency": None,
        }


def check_telegram_proxy():
    if not PROXY_URL:
        return {
            "available": False,
            "latency": None,
            "error": "PROXY_URL не настроен",
        }

    if not BOT_TOKEN:
        return {
            "available": False,
            "latency": None,
            "error": "BOT_TOKEN не настроен",
        }

    url = (
        "https://api.telegram.org/"
        f"bot{BOT_TOKEN}/getMe"
    )

    proxies = {
        "http": PROXY_URL,
        "https": PROXY_URL,
    }

    start = time.perf_counter()

    try:
        response = requests.get(
            url,
            proxies=proxies,
            timeout=10,
        )

        latency = (
            time.perf_counter() - start
        ) * 1000

        if response.status_code != 200:
            return {
                "available": False,
                "latency": latency,
                "error": f"HTTP {response.status_code}",
            }

        data = response.json()

        if not data.get("ok"):
            return {
                "available": False,
                "latency": latency,
                "error": "Telegram API вернул ошибку",
            }

        return {
            "available": True,
            "latency": latency,
            "error": "",
        }

    except requests.exceptions.ProxyError:
        return {
            "available": False,
            "latency": None,
            "error": "Ошибка подключения к SOCKS5/VLESS",
        }

    except requests.exceptions.ConnectTimeout:
        return {
            "available": False,
            "latency": None,
            "error": "Таймаут подключения к Telegram",
        }

    except requests.exceptions.RequestException as error:
        return {
            "available": False,
            "latency": None,
            "error": str(error),
        }


def get_monitored_processes():
    processes = get_processes()["all"]

    keywords = [
        "emias",
        "tickets",
        "python",
        "xray",
        "chromium",
        "docker",
        "telegram",
    ]

    found = []

    for process in processes:
        text = (
            f"{process['name']} "
            f"{process['cmdline']}"
        ).lower()

        if any(
            keyword in text
            for keyword in keywords
        ):
            found.append(process)

    return found