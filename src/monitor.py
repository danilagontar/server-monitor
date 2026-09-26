import platform
import time

import psutil


def get_uptime():
    uptime = time.time() - psutil.boot_time()

    days = int(uptime // 86400)
    hours = int((uptime % 86400) // 3600)
    minutes = int((uptime % 3600) // 60)

    return f"{days}d {hours}h {minutes}m"


def get_cpu_usage():
    return psutil.cpu_percent(interval=1)


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


def get_server_status():
    memory = get_memory_usage()
    disk = get_disk_usage()

    return {
        "hostname": platform.node(),
        "cpu": get_cpu_usage(),
        "memory": memory,
        "disk": disk,
        "uptime": get_uptime(),
    }