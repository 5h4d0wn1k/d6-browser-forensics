#!/usr/bin/env python3
"""D6 - Browser Forensics

Chrome/Firefox SQLite history extraction, bookmark analysis.
Uses sqlite3, os, json only.
"""

import sqlite3
import os
import sys
import json
from datetime import datetime, timedelta

CHROME_HISTORY_SCHEMA = "urls, visits"
FIREFOX_SCHEMA = "moz_places, moz_historyvisits"


def chrome_epoch(us):
    """Chrome uses microseconds since 1601-01-01."""
    try:
        epoch = datetime(1601, 1, 1)
        return epoch + timedelta(microseconds=us)
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
            "SELECT u.id, u.url, u.title, u.visit_count, "
            "u.last_visit_time FROM urls u ORDER BY u.last_visit_time DESC LIMIT 500"
        )
        for url_id, url, title, vc, last in cur.fetchall():
            ts = chrome_epoch(last)
            rows.append({
                "type": "url",
                "id": url_id,
                "url": url,
                "title": title,
                "visit_count": vc,
                "last_visit": ts.isoformat() if ts else None,
            })
        cur.execute(
            "SELECT v.id, v.url, v.visit_time, v.from_visit FROM visits v "
            "ORDER BY v.visit_time DESC LIMIT 500"
        )
        for vid, urn, vt, fromv in cur.fetchall():
            ts = chrome_epoch(vt)
            rows.append({
                "type": "visit",
                "id": vid,
                "visit_time": ts.isoformat() if ts else None,
                "from_visit": fromv,
            })
    except sqlite3.Error as e:
        conn.close()
        raise ValueError("History query failed: %s" % e)
    conn.close()
    return rows


def chrome_bookmarks(db_path):
    conn = _open_ro(db_path)
    cur = conn.cursor()
    rows = []
    try:
        cur.execute(
            "SELECT b.id, b.type, b.title, b.url, b.date_added, "
            "(SELECT title FROM bookmarks p WHERE p.id=b.parent_id) AS parent "
            "FROM bookmarks b"
        )
        for bid, btype, title, url, added, parent in cur.fetchall():
            ts = chrome_epoch(added)
            rows.append({
                "id": bid,
                "type": btype,
                "title": title,
                "url": url,
                "parent": parent,
                "date_added": ts.isoformat() if ts else None,
            })
    except sqlite3.Error as e:
        conn.close()
        raise ValueError("Bookmark query failed: %s" % e)
    conn.close()
    return rows


def firefox_history(db_path):
    conn = _open_ro(db_path)
    cur = conn.cursor()
    rows = []
    try:
        cur.execute(
            "SELECT p.id, p.url, p.title, "
            "(SELECT COUNT(*) FROM moz_historyvisits v WHERE v.place_id=p.id) AS visits, "
            "(SELECT MAX(v.visit_date) FROM moz_historyvisits v WHERE v.place_id=p.id) AS last "
            "FROM moz_places p ORDER BY last DESC LIMIT 500"
        )
        for pid, url, title, visits, last in cur.fetchall():
            ts = None
            if last:
                try:
                    ts = (datetime(1970, 1, 1) + timedelta(microseconds=last)).isoformat()
                except Exception:
                    ts = None
            rows.append({
                "type": "place",
                "id": pid,
                "url": url,
                "title": title,
                "visit_count": visits,
                "last_visit": ts,
            })
        cur.execute(
            "SELECT v.id, v.place_id, v.visit_date, v.from_visit "
            "FROM moz_historyvisits v ORDER BY v.visit_date DESC LIMIT 500"
        )
        for vid, pid, vd, fromv in cur.fetchall():
            ts = None
            if vd:
                try:
                    ts = (datetime(1970, 1, 1) + timedelta(microseconds=vd)).isoformat()
                except Exception:
                    ts = None
            rows.append({
                "type": "visit",
                "id": vid,
                "place_id": pid,
                "visit_time": ts,
                "from_visit": fromv,
            })
    except sqlite3.Error as e:
        conn.close()
        raise ValueError("Firefox history query failed: %s" % e)
    conn.close()
    return rows


def firefox_bookmarks(db_path):
    conn = _open_ro(db_path)
    cur = conn.cursor()
    rows = []
    try:
        cur.execute(
            "SELECT b.id, b.title, b.dateAdded, "
            "(SELECT title FROM moz_bookmarks p WHERE p.id=b.parent) AS parent, "
            "(SELECT url FROM moz_places pl WHERE pl.id=b.fk) AS url "
            "FROM moz_bookmarks b"
        )
        for bid, title, added, parent, url in cur.fetchall():
            ts = None
            if added:
                try:
                    ts = (datetime(1970, 1, 1) + timedelta(microseconds=added)).isoformat()
                except Exception:
                    ts = None
            rows.append({
                "id": bid,
                "title": title,
                "url": url,
                "parent": parent,
                "date_added": ts,
            })
    except sqlite3.Error as e:
        conn.close()
        raise ValueError("Bookmark query failed: %s" % e)
    conn.close()
    return rows


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
        c = categorize(u.get("url", ""))
        by_cat.setdefault(c, []).append(u)
    return by_cat


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 browser.py <chrome|firefox> <db_directory>")
        return 1
    kind = sys.argv[1].lower()
    directory = sys.argv[2]

    default_files = {
        "chrome_history": "History",
        "chrome_bookmarks": "Bookmarks",
        "firefox_history": "places.sqlite",
        "firefox_bookmarks": "places.sqlite",
    }

    if kind == "chrome":
        hist_path = os.path.join(directory, default_files["chrome_history"])
        bm_path = os.path.join(directory, default_files["chrome_bookmarks"])
        if not os.path.isfile(hist_path):
            # Chrome may place it in a profile subdir; accept the dir itself
            hist_path = directory
        print("=== D6 - Browser Forensics (Chrome) ===")
        if os.path.isfile(hist_path):
            try:
                h = chrome_history(hist_path)
                print("History entries: %d" % len(h))
                by_cat = analyze(h)
                print("\n-- Category breakdown --")
                for c, items in sorted(by_cat.items()):
                    print("  %-10s %d" % (c, len(items)))
                print("\n-- Recent history --")
                for e in h[:30]:
                    print("  %s %s" % (e.get("last_visit") or e.get("visit_time") or "?", (e.get("url") or e.get("title") or "")[:80]))
            except Exception as ex:
                print("History error: %s" % ex)
        else:
            print("History DB not found: %s" % hist_path)
        if os.path.isfile(bm_path):
            try:
                with open(bm_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print("\n-- Bookmarks --")
                print("  JSON bookmark file parsed")
                roots = data.get("roots", {})
                for rname, rval in roots.items():
                    n = _count_nodes(rval)
                    print("  Root: %s (%d nodes)" % (rname, n))
            except Exception as ex:
                print("Bookmark error: %s" % ex)
        else:
            print("Bookmarks file not found: %s" % bm_path)
    elif kind == "firefox":
        hist_path = os.path.join(directory, default_files["firefox_history"])
        if not os.path.isfile(hist_path):
            hist_path = directory
        print("=== D6 - Browser Forensics (Firefox) ===")
        if os.path.isfile(hist_path):
            try:
                h = firefox_history(hist_path)
                print("History entries: %d" % len(h))
                by_cat = analyze(h)
                print("\n-- Category breakdown --")
                for c, items in sorted(by_cat.items()):
                    print("  %-10s %d" % (c, len(items)))
                print("\n-- Recent history --")
                for e in h[:30]:
                    print("  %s %s" % (e.get("last_visit") or e.get("visit_time") or "?", (e.get("url") or e.get("title") or "")[:80]))
            except Exception as ex:
                print("History error: %s" % ex)
            try:
                bm = firefox_bookmarks(hist_path)
                print("\n-- Bookmarks (%d) --" % len(bm))
                for b in bm[:30]:
                    print("  %s %s" % (b.get("date_added") or "?", (b.get("title") or b.get("url") or "")[:70]))
            except Exception as ex:
                print("Bookmark error: %s" % ex)
        else:
            print("History DB not found: %s" % hist_path)
    else:
        print("Unknown browser: %s (use chrome or firefox)" % kind)
        return 1
    return 0


def _count_nodes(node):
    n = 1
    for child in node.get("children", []):
        n += _count_nodes(child)
    return n


# Provide a self-test generating a sample database to demonstrate without real data
def selftest():
    import tempfile
    d = tempfile.mkdtemp()
    path = os.path.join(d, "History")
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT, title TEXT, visit_count INTEGER, last_visit_time INTEGER)")
    cur.execute("CREATE TABLE visits (id INTEGER PRIMARY KEY, url TEXT, visit_time INTEGER, from_visit INTEGER)")
    epoch = datetime(1601, 1, 1)
    now_us = int((datetime.now() - epoch).total_seconds() * 1_000_000)
    cur.execute("INSERT INTO urls VALUES (1, 'https://example.com', 'Example', 2, ?)", (now_us,))
    cur.execute("INSERT INTO urls VALUES (2, 'https://google.com/search?q=test', 'Search', 1, ?)", (now_us - 1_000_000,))
    cur.execute("INSERT INTO visits VALUES (1, 'https://example.com', ?, 0)", (now_us,))
    conn.commit()
    conn.close()
    return path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("No arguments; running self-test with generated history...")
        sp = selftest()
        sys.argv = [sys.argv[0], "chrome", os.path.dirname(sp)]
    sys.exit(main())
