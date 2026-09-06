#!/usr/bin/env python3
"""Tests for D6 Browser Forensics."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "firmware"))
from browser import chrome_history, chrome_downloads, chrome_artifacts, chrome_epoch, analyze, visited_url_timeline
from datetime import datetime

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "chrome_history.sqlite")


class TestChromeEpoch(unittest.TestCase):
    def test_epoch_conversion(self):
        dt = chrome_epoch(0)
        self.assertEqual(dt, datetime(1601, 1, 1))

    def test_epoch_conversion_now(self):
        from datetime import timedelta
        dt = chrome_epoch(1_000_000)
        self.assertEqual(dt, datetime(1601, 1, 1) + timedelta(seconds=1))


class TestChromeHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = chrome_history(FIXTURE)

    def test_history_populated(self):
        self.assertGreater(len(self.history), 0)

    def test_urls_present(self):
        urls = [h for h in self.history if h["type"] == "url"]
        self.assertEqual(len(urls), 6)
        urls_all = " ".join(u["url"] for u in urls)
        self.assertIn("https://example.com/", urls_all)
        self.assertIn("banking.example.com", urls_all)

    def test_visits_present(self):
        visits = [h for h in self.history if h["type"] == "visit"]
        self.assertGreaterEqual(len(visits), 1)

    def test_last_visit_decoded(self):
        for h in self.history:
            ts = (h.get("last_visit") or h.get("visit_time"))
            if ts:
                self.assertEqual(ts[:4], "2024")


class TestChromeDownloads(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.downloads = chrome_downloads(FIXTURE)

    def test_downloads_found(self):
        self.assertGreaterEqual(len(self.downloads), 1)

    def test_download_url(self):
        self.assertEqual(self.downloads[0]["url"], "https://www.example.net/forge/download.exe")
        self.assertEqual(self.downloads[0]["received_bytes"], 1024576)


class TestAnalyze(unittest.TestCase):
    def test_categorize(self):
        history = chrome_history(FIXTURE)
        by_cat = analyze(history)
        self.assertTrue(any(c == "search" for c in by_cat))
        self.assertTrue(any(c == "finance" for c in by_cat))


class TestTimeline(unittest.TestCase):
    def test_timeline_sorted(self):
        history = chrome_history(FIXTURE)
        tl = visited_url_timeline(history)
        for a, b in zip(tl, tl[1:]):
            self.assertLessEqual(a["timestamp"] or "", b["timestamp"] or "")


class TestArtifacts(unittest.TestCase):
    def test_full(self):
        a = chrome_artifacts(FIXTURE)
        self.assertIn("history", a)
        self.assertIn("downloads", a)


class TestCLIHelp(unittest.TestCase):
    def test_help_exits_zero(self):
        import subprocess
        cli = os.path.join(os.path.dirname(__file__), "..", "cli.py")
        r = subprocess.run([sys.executable, cli, "--help"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


class TestCLIDemo(unittest.TestCase):
    def test_demo_exits_zero(self):
        import subprocess
        cli = os.path.join(os.path.dirname(__file__), "..", "cli.py")
        r = subprocess.run([sys.executable, cli, "--demo"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Browser Forensics", r.stdout)


if __name__ == "__main__":
    unittest.main()
