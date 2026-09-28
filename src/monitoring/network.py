import csv
import os
import time
from datetime import datetime, timedelta

import psutil

from src.utils.utils import (
    current_time,
    format_bytes,
)


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

NETWORK_CSV_FILE = os.path.join(
    BASE_DIR,
    "data",
    "network_metrics.csv",
)


def get_network_stats():
    total = psutil.net_io_counters()
    interfaces = psutil.net_io_counters(pernic=True)

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

    time.sleep(interval)

    second = psutil.net_io_counters()

    return {
        "rx_speed": max(
            0,
            (second.bytes_recv - first.bytes_recv)
            / interval,
        ),
        "tx_speed": max(
            0,
            (second.bytes_sent - first.bytes_sent)
            / interval,
        ),
    }


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


def calculate_network_stats(metrics):
    if not metrics:
        return {
            "received": 0,
            "sent": 0,
            "rx_avg": 0,
            "tx_avg": 0,
        }

    received = (
        metrics[-1]["received"]
        - metrics[0]["received"]
    )

    sent = (
        metrics[-1]["sent"]
        - metrics[0]["sent"]
    )

    rx_values = [
        item["rx_speed"]
        for item in metrics
        if item["rx_speed"] > 0
    ]

    tx_values = [
        item["tx_speed"]
        for item in metrics
        if item["tx_speed"] > 0
    ]

    return {
        "received": max(0, received),
        "sent": max(0, sent),
        "rx_avg": (
            sum(rx_values) / len(rx_values)
            if rx_values
            else 0
        ),
        "tx_avg": (
            sum(tx_values) / len(tx_values)
            if tx_values
            else 0
        ),
    }


def build_network_message():
    network = get_network_stats()
    speed = get_current_speed()

    return (
        "🌐 СЕТЬ\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🟢 Интернет\n\n"
        "Latency: измеряется отдельно\n\n"
        f"📥 Получено: "
        f"{format_bytes(network['total']['received'])}\n"
        f"📤 Отправлено: "
        f"{format_bytes(network['total']['sent'])}\n\n"
        f"📥 Скорость: "
        f"{format_bytes(speed['rx_speed'])}/s\n"
        f"📤 Скорость: "
        f"{format_bytes(speed['tx_speed'])}/s\n\n"
        f"🕐 Обновлено: {current_time()}"
    )