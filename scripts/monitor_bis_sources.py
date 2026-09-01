#!/usr/bin/env python3
"""
BIS Source Telemetry & Discovery Monitor CLI (Phase 5A).
Monitors the 9 BIS source families and populates discovery candidate queues.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
from ai.acquisition.monitor import SourceMonitor


def main():
    parser = argparse.ArgumentParser(description="Monitor BIS Source Families & Telemetry")
    parser.add_argument("--dry-run", action="store_true", help="Run telemetry probing only")
    args = parser.parse_args()

    monitor = SourceMonitor()
    telemetry = monitor.monitor_all_sources()
    candidates = monitor.build_candidate_queue()

    print("\n" + "=" * 80)
    print("📡 BIS SOURCE FAMILIES TELEMETRY & DISCOVERY QUEUE (PHASE 5A)")
    print("=" * 80)
    print(f"Total Sources Monitored: {len(telemetry):>5d}")
    print(f"Candidate Queue Items:   {len(candidates):>5d}")
    print("-" * 80)
    print("Source Status Summary:")
    for t in telemetry:
        status_icon = "🟢" if t["status"] == "ONLINE" else "🟡"
        print(f"  {status_icon} {t['source_name']:<48}: {t['status']:<15} (HTTP {t['http_status']}) [{t['response_time_ms']}ms]")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
