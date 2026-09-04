# D6 — Browser Forensics

Extracts and analyzes browser history and bookmarks from Chrome and Firefox.

## Overview

This project parses browser SQLite databases to extract:
- Chrome History / Bookmarks
- Firefox places.sqlite (history + bookmarks)
- Visit timestamps and referrer relationships
- URL categorization (social, search, media, finance, etc.)

## Features

- **Chrome**: parses `History` and JSON `Bookmarks` files
- **Firefox**: parses `places.sqlite` (history and bookmarks)
- **Timestamps**: converts Chrome (1601 epoch) and Firefox (1970 epoch) formats
- **Categorization**: groups URLs by site category
- **Self-test**: generates a sample database when no args given

## Usage

```bash
python3 browser.py chrome /path/to/chrome/Profile
python3 browser.py firefox /path/to/firefox/profile
python3 browser.py   # runs self-test with a generated DB
```

## Example Output

```
=== D6 - Browser Forensics (Chrome) ===
History entries: 2

-- Category breakdown --
  other      1
  search     1

-- Recent history --
  2024-01-15T09:30:00 https://example.com
```

## Legal Disclaimer

**IMPORTANT: Read before use.**

This project is provided for **educational and authorized security testing purposes only**. 

### Authorization Requirements
- You MUST have explicit written permission from the network owner before using this tool
- Unauthorized interception of network communications is illegal under federal and state laws
- This tool should ONLY be used on networks you own or have written authorization to test

### Legal Framework
- **Computer Fraud and Abuse Act (CFAA)**: Unauthorized access to computer systems is a federal crime
- **Wiretap Act (18 U.S.C. § 2511)**: Interception of electronic communications without consent is illegal
- **State Laws**: Many states have additional computer crime and wiretapping statutes
- **GDPR/CCPA**: Data collection may be subject to privacy regulations

### Acceptable Use
- Testing security of your own networks
- Authorized penetration testing with written scope
- Academic research in controlled lab environments
- Security education and training

### Prohibited Use
- Intercepting communications on networks you do not own
- Attacking infrastructure without authorization
- Any activity that violates applicable laws or regulations
- Commercial use without proper licensing

### No Warranty
This software is provided "AS IS" without warranty of any kind. The author is not responsible for any misuse or damage caused by this software.

### Responsible Disclosure
If you discover vulnerabilities using this tool, follow responsible disclosure practices:
1. Report to the vendor/owner privately
2. Allow reasonable time for remediation
3. Do not exploit beyond proof of concept

## License

MIT
