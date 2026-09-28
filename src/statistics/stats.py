import csv
import os
from datetime import datetime, timedelta

from src.monitoring.network import (
    calculate_network_stats,
    read_network_metrics,
)
from src.utils.utils import (
    current_time,
    format_bytes,
    format_period,
)


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

CSV_FILE = os.path.join(
    BASE_DIR,
    "data",
    "metrics.csv",
)


def read_metrics(hours):
    if not os.path.exists(CSV_FILE):
        return []

    since = datetime.now() - timedelta(
        hours=hours
    )

    metrics = []

    with open(
        CSV_FILE,
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
                    "cpu": float(row["cpu"]),
                    "ram_percent": float(
                        row["ram_percent"]
                    ),
                    "disk_percent": float(
                        row["disk_percent"]
                    ),
                })

            except (
                ValueError,
                KeyError,
            ):
                continue

    return metrics


def calculate_stats(metrics):
    cpu_values = [
        item["cpu"]
        for item in metrics
    ]

    ram_values = [
        item["ram_percent"]
        for item in metrics
    ]

    disk_values = [
        item["disk_percent"]
        for item in metrics
    ]

    return {
        "cpu_avg": sum(cpu_values) / len(cpu_values),
        "cpu_min": min(cpu_values),
        "cpu_max": max(cpu_values),
        "ram_avg": sum(ram_values) / len(ram_values),
        "ram_min": min(ram_values),
        "ram_max": max(ram_values),
        "disk_start": disk_values[0],
        "disk_end": disk_values[-1],
        "disk_change": (
            disk_values[-1] - disk_values[0]
        ),
    }


def build_stats_message(hours):
    metrics = read_metrics(hours)

    if not metrics:
        return (
            "📈 СТАТИСТИКА\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"За последние {format_period(hours)} "
            "данных пока нет."
        )

    stats = calculate_stats(metrics)

    network_metrics = read_network_metrics(
        hours
    )
    network_stats = calculate_network_stats(
        network_metrics
    )

    disk_change = stats["disk_change"]

    if disk_change > 0:
        disk_change_text = f"+{disk_change:.1f}%"
    else:
        disk_change_text = f"{disk_change:.1f}%"

    return (
        f"📈 СТАТИСТИКА — "
        f"{format_period(hours).upper()}\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"Период: {format_period(hours)}\n"
        f"Данных собрано: {len(metrics)}\n\n"
        "⚡ CPU\n"
        f"Среднее: {stats['cpu_avg']:.1f}%\n"
        f"Минимум: {stats['cpu_min']:.1f}%\n"
        f"Максимум: {stats['cpu_max']:.1f}%\n\n"
        "🧠 RAM\n"
        f"Среднее: {stats['ram_avg']:.1f}%\n"
        f"Минимум: {stats['ram_min']:.1f}%\n"
        f"Максимум: {stats['ram_max']:.1f}%\n\n"
        "💾 Диск\n"
        f"В начале: {stats['disk_start']:.1f}%\n"
        f"Сейчас: {stats['disk_end']:.1f}%\n"
        f"Изменение: {disk_change_text}\n\n"
        "🌐 Сеть\n"
        f"Получено: "
        f"{network_stats['received'] / 1024 / 1024:.1f} МБ\n"
        f"Отправлено: "
        f"{network_stats['sent'] / 1024 / 1024:.1f} МБ\n\n"
        "Средняя скорость\n"
        f"📥 "
        f"{network_stats['rx_avg'] / 1024 / 1024:.1f} МБ/с\n"
        f"📤 "
        f"{network_stats['tx_avg'] / 1024 / 1024:.1f} МБ/с\n\n"
        f"🕐 Обновлено: {current_time()}"
    )