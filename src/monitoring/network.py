import csv
import os
import socket
import time
from datetime import datetime, timedelta

import psutil


PROJECT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

NETWORK_CSV_FILE = os.path.join(
    PROJECT_DIR,
    "data",
    "network_metrics.csv",
)


def get_network_stats():
    total = psutil.net_io_counters()
    interfaces = psutil.net_io_counters(
        pernic=True
    )

    return {
        "total": {
            "received": total.bytes_recv,
            "sent": total.bytes_sent,
            "rx_packets": total.packets_recv,
            "tx_packets": total.packets_sent,
        },
        "interfaces": {
            name: {
                "received": stats.bytes_recv,
                "sent": stats.bytes_sent,
                "rx_packets": stats.packets_recv,
                "tx_packets": stats.packets_sent,
            }
            for name, stats in interfaces.items()
        },
    }


def get_current_speed(interval=1):
    first = psutil.net_io_counters()
    first_time = time.monotonic()

    time.sleep(interval)

    second = psutil.net_io_counters()
    second_time = time.monotonic()

    elapsed = second_time - first_time

    if elapsed <= 0:
        elapsed = interval

    return {
        "rx_speed": max(
            0,
            (second.bytes_recv - first.bytes_recv)
            / elapsed,
        ),
        "tx_speed": max(
            0,
            (second.bytes_sent - first.bytes_sent)
            / elapsed,
        ),
    }


def get_latency():
    start = time.monotonic()

    try:
        with socket.create_connection(
            ("1.1.1.1", 443),
            timeout=3,
        ):
            pass

        return round(
            (time.monotonic() - start) * 1000
        )

    except OSError:
        return None


def format_network_bytes(value):
    value = float(value)

    units = [
        "Б",
        "КБ",
        "МБ",
        "ГБ",
        "ТБ",
    ]

    for unit in units:
        if value < 1024 or unit == "ТБ":
            if unit == "Б":
                return f"{value:.0f} {unit}"

            if value >= 100:
                return f"{value:.0f} {unit}"

            if value >= 10:
                return f"{value:.1f} {unit}"

            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{value:.2f} ТБ"


def read_network_metrics(hours):
    if not os.path.exists(NETWORK_CSV_FILE):
        return []

    since = datetime.now() - timedelta(
        hours=hours
    )

    metrics = []

    with open(
        NETWORK_CSV_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                timestamp = datetime.strptime(
                    row["timestamp"],
                    "%Y-%m-%d %H:%M:%S",
                )

                if timestamp < since:
                    continue

                metrics.append({
                    "timestamp": timestamp,
                    "received": int(
                        row["received"]
                    ),
                    "sent": int(
                        row["sent"]
                    ),
                    "rx_speed": float(
                        row["rx_speed"]
                    ),
                    "tx_speed": float(
                        row["tx_speed"]
                    ),
                })

            except (
                ValueError,
                KeyError,
            ):
                continue

    return metrics


def build_network_message():
    network = get_network_stats()
    speed = get_current_speed()
    latency = get_latency()

    if latency is None:
        latency_text = "недоступен"
        internet_icon = "🔴"
        internet_text = (
            "Интернет недоступен"
        )
    else:
        latency_text = f"{latency} ms"
        internet_icon = "🟢"
        internet_text = "Интернет"

    return (
        "🌐 СЕТЬ\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{internet_icon} {internet_text}\n\n"
        f"Latency: {latency_text}\n\n"
        f"📥 Получено: "
        f"{format_network_bytes(network['total']['received'])}\n"
        f"📤 Отправлено: "
        f"{format_network_bytes(network['total']['sent'])}\n\n"
        "📡 Текущая скорость\n"
        f"📥 "
        f"{format_network_bytes(speed['rx_speed'])}/с\n"
        f"📤 "
        f"{format_network_bytes(speed['tx_speed'])}/с\n\n"
        f"🕐 Обновлено: "
        f"{datetime.now().strftime('%d.%m %H:%M:%S')}"
    )