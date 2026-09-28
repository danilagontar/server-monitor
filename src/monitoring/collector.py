import csv
import os
import time
from datetime import datetime

import psutil


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_FILE = os.path.join(DATA_DIR, "metrics.csv")
NETWORK_CSV_FILE = os.path.join(
    DATA_DIR,
    "network_metrics.csv",
)


def ensure_csv():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(CSV_FILE):
        with open(
            CSV_FILE,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)

            writer.writerow([
                "timestamp",
                "cpu",
                "ram_percent",
                "ram_used",
                "ram_total",
                "disk_percent",
                "disk_used",
                "disk_total",
            ])

    if not os.path.exists(NETWORK_CSV_FILE):
        with open(
            NETWORK_CSV_FILE,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)

            writer.writerow([
                "timestamp",
                "received",
                "sent",
                "rx_speed",
                "tx_speed",
            ])


def collect_metrics():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "cpu": psutil.cpu_percent(interval=1),
        "ram_percent": memory.percent,
        "ram_used": memory.used,
        "ram_total": memory.total,
        "disk_percent": disk.percent,
        "disk_used": disk.used,
        "disk_total": disk.total,
    }


def collect_network_metrics(previous):
    counters = psutil.net_io_counters()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    received = counters.bytes_recv
    sent = counters.bytes_sent

    if previous is None:
        rx_speed = 0
        tx_speed = 0
    else:
        rx_speed = max(
            0,
            received - previous["received"],
        )
        tx_speed = max(
            0,
            sent - previous["sent"],
        )

    return {
        "timestamp": timestamp,
        "received": received,
        "sent": sent,
        "rx_speed": rx_speed,
        "tx_speed": tx_speed,
    }


def save_metrics(metrics):
    with open(
        CSV_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        writer.writerow([
            metrics["timestamp"],
            metrics["cpu"],
            metrics["ram_percent"],
            metrics["ram_used"],
            metrics["ram_total"],
            metrics["disk_percent"],
            metrics["disk_used"],
            metrics["disk_total"],
        ])


def save_network_metrics(metrics):
    with open(
        NETWORK_CSV_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        writer.writerow([
            metrics["timestamp"],
            metrics["received"],
            metrics["sent"],
            metrics["rx_speed"],
            metrics["tx_speed"],
        ])


def collect_loop():
    ensure_csv()

    previous_network = None

    while True:
        metrics = collect_metrics()
        network_metrics = collect_network_metrics(
            previous_network
        )

        save_metrics(metrics)
        save_network_metrics(network_metrics)

        previous_network = network_metrics

        time.sleep(59)