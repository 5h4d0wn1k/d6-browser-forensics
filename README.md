> **⚠️ EDUCATIONAL USE ONLY — AUTHORIZED TESTING ONLY.**
> This project exists for education, research, and **defense of systems you own
> or hold explicit written authorization to assess**. Unauthorized use is
> prohibited and may be illegal. Read [ETHICS.md](ETHICS.md) and
> [SCOPE.md](SCOPE.md) before use. Use at your own risk; **AS IS**, no warranty.

# D6 — Browser Forensics Collector

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![GitHub stars](https://img.shields.io/github/stars/5h4d0wn1k/d6-browser-forensics)
![Last commit](https://img.shields.io/github/last-commit/5h4d0wn1k/d6-browser-forensics)
![GitHub issues](https://img.shields.io/github/issues/5h4d0wn1k/d6-browser-forensics)

**Browser forensics** collector for DFIR and blue-team analysis — parses Chrome/SQLite history, visits, downloads, and bookmark artifacts into a time-ordered visited-URL timeline with category classification (stdlib-only, read-only).

## Why

Browser artifacts are among the richest sources of user-activity evidence in **digital forensics and incident response**. D6 turns a Chrome profile's SQLite tables (`urls`, `visits`, `downloads`, `downloads_url_chains`) into a forensic timeline: Chrome-epoch timestamps decoded to ISO datetime, search/social/finance categories, and download provenance (path, source URL, size). Designed for **authorized educational and blue-team analysis only**, it is strictly read-only, bundles a fully synthetic fixture so you can practice without real personal data, and emits artifacts as JSON for downstream tools.

## Features

- **Chrome SQLite parsing** via stdlib `sqlite3` — `urls`, `visits`, `downloads`, `downloads_url_chains`.
- **Chrome epoch decoding** — microseconds since 1601-01-01 to ISO datetime.
- **Visited-URL timeline** — merges URL records and visit events, time-ordered.
- **Category breakdown** — search, social, media, email, finance, other.
- **Download artifact extraction** — path, source URL, size, start time.
- **JSON artifacts output** — `-o` for pipeline integration.

## Quickstart

```bash
# Analyze the bundled synthetic Chrome history fixture (offline demo)
python3 cli.py --demo

# Analyze a real profile's History file (read-only)
python3 cli.py --input /path/to/Chrome/History --output reports/artifacts.json
```

```bash
# Regenerate fixtures (not needed for normal use)
python3 tests/generate_fixtures.py

# Run the offline test suite
python3 -m unittest discover -s tests -v
```

## Project structure

```
d6-browser-forensics/
├── cli.py               # CLI entry point
├── firmware/browser.py  # parsing engine
├── tests/               # fixtures generator + unittest suite (13 tests)
└── ETHICS.md, SCOPE.md  # authorized-use rules
```

## Documentation

- [ETHICS.md](ETHICS.md) — authorized-use policy
- [SCOPE.md](SCOPE.md) — analysis scope
- [SECURITY.md](SECURITY.md) — security policy
- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution guide

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Analyze only systems/profiles you own or are permitted to examine.

## License

MIT. See [LICENSE](LICENSE).