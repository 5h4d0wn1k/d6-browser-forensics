#!/usr/bin/env python3
"""D6 - Browser Forensics

Chrome/Firefox SQLite history/bookmark/download parsing, artifact timeline, category breakdown.
Uses stdlib sqlite3, os, json only.
"""

import sqlite3
import os
import sys
import json
from datetime import datetime, timedelta


def chrome_epoch(us):
    """Chrome microseconds since 1601-01-01."""
    try:
        return datetime(1601, 1, 1) + timedelta(microseconds=us)
    except Exception:
        return None


def _open_ro(path):
    return sqlite3.connect("file:%s?mode=ro" % path, uri=True)


def chrome_history(db_path):
    conn = _open_ro(db_path)
    cur = conn.cursor()
    rows = []
    try:
        cur.execute(
            "SELECT u.id, u.url, u.title, u.visit_count, u.last_visit_time "
            "FROM urls u ORDER BY u.last_visit_time DESC LIMIT 1000"
        )
        for url_id, url, title, vc, last in cur.fetchall():
            ts = chrome_epoch(last)
            rows.append({
                "type": "url",
                "id": url_id,
                "url": url,
                "title": title,
                "visit_count": vc,
                "last_visit": chrome_epoch(last).isoformat() if last else None,
            })
        cur.execute(
            "SELECT v.id, v.url, v.visit_time, v.from_visit, v.visit_duration "
            "FROM visits v ORDER BY v.visit_time DESC LIMIT 1000"
        )
        for vid, urn, vt, fromv, dur in cur.fetchall():
            rows.append({
                "type": "visit",
                "id": vid,
                "url": urn,
                "visit_time": chrome_epoch(vt).isoformat() if vt else None,
                "from_visit": fromv,
                "visit_duration_s": dur / 1_000_000 if dur else 0,
            })
    except sqlite3.Error as e:
        conn.close()
        raise ValueError("History query failed: %s" % e)
    conn.close()
    return rows


def chrome_downloads(db_path):
    conn = _open_ro(db_path)
    cur = conn.cursor()
    rows = []
    try:
        cur.execute(
            "SELECT d.id, d.current_path, d.target_path, d.start_time, "
            "d.received_bytes, d.total_bytes, du.url "
            "FROM downloads d LEFT JOIN downloads_url_chains du ON du.download_id=d.id "
            "ORDER BY d.start_time"
        )
        for did, cpath, tpath, start, recv, tot, url in cur.fetchall():
            rows.append({
                "id": did,
                "current_path": cpath,
                "target_path": tpath,
                "url": url,
                "start_time": chrome_epoch(start).isoformat() if start else None,
                "received_bytes": recv,
                "total_bytes": tot,
            })
    except sqlite3.Error as e:
        conn.close()
        raise ValueError("Downloads query failed: %s" % e)
    conn.close()
    return rows


def chrome_artifacts(db_path):
    history = chrome_history(db_path)
    downloads = chrome_downloads(db_path)
    return {"history": history, "downloads": downloads}


def categorize(url):
    cat = "other"
    if "google.com/search" in url or "bing.com/search" in url:
        cat = "search"
    elif "facebook.com" in url or "twitter.com" in url or "instagram.com" in url:
        cat = "social"
    elif "youtube.com" in url or "netflix.com" in url:
        cat = "media"
    elif "mail." in url or "gmail.com" in url:
        cat = "email"
    elif "bank" in url or "paypal.com" in url or "stripe.com" in url:
        cat = "finance"
    return cat


def analyze(history):
    urls = [h for h in history if h.get("url")]
    by_cat = {}
    for u in urls:
        by_cat.setdefault(categorize(u.get("url", "")), []).append(u)
    return by_cat


def visited_url_timeline(history):
    """Build a visited-URL timeline merged from url and visit records."""
    events = []
    for h in history:
        if h["type"] == "visit" and h.get("visit_time"):
            events.append({
                "timestamp": h["visit_time"],
                "kind": "visit",
                "url": h.get("url", ""),
            })
        elif h["type"] == "url" and h.get("last_visit"):
            events.append({
                "timestamp": h["last_visit"],
                "kind": "url_record",
                "url": h.get("url", ""),
                "title": h.get("title", ""),
                "visit_count": h.get("visit_count"),
            })
    events.sort(key=lambda e: e["timestamp"] or "")
    return events


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="D6 - Browser Forensics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", "-i", help="Path to Chrome History (or profile) SQLite file")
    parser.add_argument("--output", "-o", help="JSON artifacts output path")
    parser.add_argument("--demo", action="store_true", help="Analyze built-in fixture")
    args = parser.parse_args()

    if args.demo:
        base = os.path.dirname(os.path.abspath(sys.argv[0]))
        if os.path.basename(base) == "firmware":
            base = os.path.dirname(base)
        db = os.path.join(base, "tests", "fixtures", "chrome_history.sqlite")
        if not os.path.isfile(db):
            print("[ERROR] Fixture not found: %s" % db)
            sys.exit(1)
        artifacts = chrome_artifacts(db)
        history = artifacts["history"]
        downloads = artifacts["downloads"]
        out_dir = os.path.join(base, "reports")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "d6_artifacts.json")
        with open(out_path, "w") as f:
            json.dump(artifacts, f, indent=2, default=str)

        print("=== D6 - Browser Forensics (Demo) ===")
        print("History records: %d" % len(history))
        print("Downloads: %d" % len(downloads))
        by_cat = analyze(history)
        print("\n-- Category breakdown --")
        for c, items in sorted(by_cat.items()):
            print("  %-10s %d" % (c, len(items)))
        print("\n-- Visited URL timeline (%d events) --" % len(visited_url_timeline(history)))
        for e in visited_url_timeline(history)[:15]:
            print("  %s %s" % (e["timestamp"], e["url"][:60]))
        if downloads:
            print("\n-- Downloads --")
            for d in downloads:
                print("  %s %s (%d bytes)" % (d["start_time"], d["url"], d["received_bytes"]))
        print("\nArtifacts JSON written to %s" % out_path)
        sys.exit(0)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    if not os.path.isfile(args.input):
        print("Error: file not found: %s" % args.input)
        sys.exit(1)

    artifacts = chrome_artifacts(args.input)
    history = artifacts["history"]
    downloads = artifacts["downloads"]
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(artifacts, f, indent=2, default=str)
        print("Artifacts written to %s" % args.output)

    print("=== D6 - Browser Forensics ===")
    print("History records: %d" % len(history))
    print("Downloads: %d" % len(downloads))
    by_cat = analyze(history)
    print("\n-- Category breakdown --")
    for c, items in sorted(by_cat.items()):
        print("  %-10s %d" % (c, len(items)))
    sys.exit(0)


if __name__ == "__main__":
    main()
