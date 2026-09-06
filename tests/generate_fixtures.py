#!/usr/bin/env python3
"""Generate a Chrome-format Places SQLite database fixture for D6 Browser Forensics."""
import os
import sqlite3
from datetime import datetime, timedelta

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def chrome_epoch_us(dt_utc):
    """Convert a UTC datetime to Chrome epoch microseconds (from 1601-01-01)."""
    epoch = datetime(1601, 1, 1)
    return int((dt_utc - epoch).total_seconds() * 1_000_000)


def main():
    path = os.path.join(FIXTURE_DIR, "chrome_history.sqlite")
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT NOT NULL, "
                "title TEXT, visit_count INTEGER, typed_count INTEGER, "
                "last_visit_time INTEGER, hidden INTEGER)")
    cur.execute("CREATE TABLE visits (id INTEGER PRIMARY KEY, url TEXT NOT NULL, "
                "visit_time INTEGER, from_visit INTEGER, transition INTEGER, "
                "visit_duration INTEGER)")
    cur.execute("CREATE TABLE downloads (id INTEGER PRIMARY KEY, "
                "current_path TEXT, target_path TEXT, start_time INTEGER, "
                "received_bytes INTEGER, total_bytes INTEGER)")
    cur.execute("CREATE TABLE downloads_url_chains (id INTEGER PRIMARY KEY, "
                "download_id INTEGER, url TEXT)")

    base = datetime(2024, 1, 15, 8, 0, 0)
    urls = [
        ("https://example.com/", "Example Domain", 3, base),
        ("https://google.com/search?q=browser+forensics", "Search", 1, base + timedelta(minutes=2)),
        ("https://docs.example.com/howto.html", "How To", 2, base + timedelta(minutes=5)),
        ("https://github.com/example/project", "Project", 4, base + timedelta(minutes=10)),
        ("https://www.example.net/forge/download.exe", "Download Page", 1, base + timedelta(minutes=11)),
        ("https://banking.example.com/login", "Login", 2, base + timedelta(minutes=15)),
    ]
    for i, (url, title, vc, last) in enumerate(urls, 1):
        cur.execute(
            "INSERT INTO urls VALUES (?,?,?,?,?,?,?)",
            (i, url, title, vc, 0, chrome_epoch_us(last), 0),
        )

    visit_pairs = [
        (1, base, 0),
        (2, base + timedelta(minutes=2), 1),
        (3, base + timedelta(minutes=5), 2),
        (4, base + timedelta(minutes=10), 3),
        (5, base + timedelta(minutes=11), 4),
        (6, base + timedelta(minutes=15), 5),
    ]
    for vid, (url_id, ts, fromv) in enumerate(visit_pairs, 1):
        cur.execute(
            "INSERT INTO visits VALUES (?,?,?,?,?,?)",
            (vid, urls[url_id - 1][0], chrome_epoch_us(ts), fromv, 1, 0),
        )

    dls = [
        (1, "/home/user/Downloads/forge.exe", "https://www.example.net/forge/download.exe",
         base + timedelta(minutes=11), 1024576, 1024576),
    ]
    for dl_id, cpath, url, ts, recv, tot in dls:
        cur.execute(
            "INSERT INTO downloads VALUES (?,?,?,?,?,?)",
            (dl_id, cpath, cpath.replace("/home/user/Downloads", "/home/user/Downloads"),
             chrome_epoch_us(ts), recv, tot),
        )
        cur.execute("INSERT INTO downloads_url_chains VALUES (?,?,?)", (dl_id, dl_id, url))

    conn.commit()
    conn.close()
    print("Wrote %s" % path)


if __name__ == "__main__":
    main()
