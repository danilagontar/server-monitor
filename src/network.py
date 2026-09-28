import psutil

from messages import section_header
from utils import (
    current_time,
    format_bytes,
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


def build_network_message():
    network = get_network_stats()
    total = network["total"]

    lines = [
        section_header("🌐", "СЕТЬ"),
        "",
        f"📥 Получено: "
        f"{format_bytes(total['received'])}",
        f"📤 Отправлено: "
        f"{format_bytes(total['sent'])}",
        "",
        f"📦 RX packets: "
        f"{total['rx_packets']:,}",
        f"📦 TX packets: "
        f"{total['tx_packets']:,}",
        "",
        "Интерфейсы:",
        "",
    ]

    for name, interface in network["interfaces"].items():
        lines.extend([
            name,
            f"  ↓ {format_bytes(interface['received'])}",
            f"  ↑ {format_bytes(interface['sent'])}",
            "",
        ])

    lines.append(
        f"🕐 Обновлено: {current_time()}"
    )

    return "\n".join(lines).rstrip()