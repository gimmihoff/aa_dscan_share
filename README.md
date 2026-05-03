# AA D-Scan Share

AllianceAuth child plugin for submitting, viewing, and sharing D-scans through AA Core Hub.

## Features

- Paste a D-scan and link it to an EVE solar system
- Select systems by name from Core's geography cache
- Reuse the last 10 systems submitted by the current user
- Store scans through `aa_core_hub.api.create_dscan`
- Redirect immediately to a shareable result page using `DScan.public_id`
- Display parsed scan rows with known Core structure standing badges
- Optionally save detected structures into Core as hostile, neutral, or friendly
- Show fleet composition summaries for each shared scan
- Show historic system D-scan timelines from Core data

## Requirements

- AllianceAuth 4.11.2
- AA Core Hub `>=1.3.6`

## Install

1. Install this package in your AllianceAuth environment.
2. Add `aa_dscan_share` to `INSTALLED_APPS`.
3. Add URLs:

```python
path("dscan-share/", include("aa_dscan_share.urls")),
```

4. Ensure `aa_core_hub` migrations are applied.

## Core Contract

This plugin intentionally stores all shared data in Core:

- `create_dscan`
- `get_dscan_by_public_id`
- `create_or_update_structure`
