# Changelog

All notable changes to J.A.N.E.T. Seed are documented here.

---

## [Unreleased]

### Added

- **Menu bar control surface (CLI):** `--ctl status|config-get|config-set|start-server` for scriptable control and E2E tests (no GUI).
- **E2E tests:** `tests/test_e2e_ctl.py` (control surface), `tests/test_e2e_api.py` (API health, models, "What can you do?" when server running).
- **INSTALL.md:** Single install guide (dependencies, run, Homebrew path, local WiFi).
- **CHANGELOG.md:** This file.

### Changed

- Menu bar: config in `~/.janet/menubar_config.json`; Settings submenu (API URL, Memory: inactivity flush, save context when idle); last model persistence; quick actions ("What can you do?", "Open Janet docs").
- Green Vault (AC-GV1): `chat_id` in conversation storage and retrieval; inactivity-based flush; config from menubar config or env (`JANET_INACTIVITY_FLUSH_SEC`, `JANET_SAVE_CONTEXT_WHEN_IDLE`).
- Green Vault (AC-GV2): Abilities store from `abilities.json` + goal_personas; "What can you do?" answered from store only (no hallucination); tests in `tests/test_abilities_store.py`.
- Orchestration module: scaffold (API, router, adaptors, JACK dispatcher); Formula/janet-all.rb; menu bar documented as first-class client of janet-seed.
- Branding: canonical image and palette in BRANDING.md (janet_orchestration_module); AC-BRAND in acceptance criteria.

---

## [0.1.0] and earlier

- Initial janet-seed: constitution, memory vaults, delegation, expansion, IDE API server, menu bar (model switch).
- OpenAI-compatible API (`/v1/chat/completions`, `/v1/models`, `/health`).
- Green Vault, Blue Vault, Red Vault; learning manager; MzNN/JanetMedia integration paths.
