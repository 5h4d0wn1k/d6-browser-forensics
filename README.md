# D6 — Browser Forensics

Chrome/SQLite history, visits, downloads and bookmark artifact parsing with visited-URL timeline reconstruction.

## IMPORTANT: Read before use.

This tool is for **authorized educational and blue-team analysis only**. Analyze browser artifacts only on systems/profiles you own or are permitted to examine. The bundled fixture is fully synthetic (fictional domains). No real personal data is stored.

## Features

- **Chrome SQLite parsing** via stdlib `sqlite3`: `urls`, `visits`, `downloads`, `downloads_url_chains`
- **Chrome epoch decoding**: microseconds since 1601-01-01 → ISO datetime
- **Visited-URL timeline**: merges url records and visit events, time-ordered
- **Category breakdown**: search, social, media, email, finance, other
- **Download artifact extraction**: path, source URL, size, start time
- **Artifacts JSON output**

## Quick Start

```bash
# Analyze the bundled synthetic Chrome history fixture
python3 cli.py --demo

# Analyze a real profile's History file (read-only)
python3 cli.py --input /path/to/Chrome/History --output reports/artifacts.json
```

## Parsed Formats

| Table | Data Extracted |
|-------|----------------|
| `urls` | url, title, visit_count, last_visit_time |
| `visits` | url, visit_time, from_visit, visit_duration |
| `downloads` | path, start_time, received/total bytes |
| `downloads_url_chains` | download → source URL mapping |

## Testing

```bash
python3 -m unittest discover -s tests
```

Fixtures regenerated with:

```bash
python3 tests/generate_fixtures.py
```

## Live Lab Test Plan

1. Run `python3 cli.py --demo` — should exit 0, print history/downloads, write `reports/d6_artifacts.json`
2. Run `python3 -m unittest discover -s tests` — all tests pass
3. Verify the visited-URL timeline is time-ordered and downloads include source URLs

## Metrics

- Formats parsed: Chrome SQLite (`urls`, `visits`, `downloads`, `downloads_url_chains`)
- Artifact types: 3 (url records, visits, downloads)
- Test count: 10
- Demo exit code: 0

## License

MIT License — see [LICENSE](LICENSE).
