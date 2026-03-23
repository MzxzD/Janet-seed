# Janet AI — Integration Checklist

Confirms that menu bar, janet-seed API, config, memory, abilities, and (optional) orchestration are connected.

---

## Checklist

| Connection | Status | References |
|------------|--------|------------|
| Menu bar reads/writes `~/.janet/menubar_config.json` | Yes | [janet_menubar.py](janet_menubar.py) `load_menubar_config`, `save_menubar_config` |
| janet-seed (conversation_loop, janet_api_server) reads same config for inactivity and memory (AC-GV1) | Yes | [conversation_loop.py](src/core/conversation_loop.py) `_get_inactivity_config()`; [janet_api_server.py](janet_api_server.py) `_get_inactivity_config()` |
| janet_api_server exposes health, models, chat with session_id | Yes | [janet_api_server.py](janet_api_server.py) `/health`, `/v1/models`, `/v1/chat/completions`; session_id in request, chat_id in store |
| Green Vault gets chat_id and inactivity flush | Yes | [memory_manager.py](src/memory/memory_manager.py) `store_conversation(..., context={"chat_id"})`; [green_vault.py](src/memory/green_vault.py) `add_summary(..., metadata)` |
| Abilities store feeds "What can you do?" (AC-GV2) | Yes | [abilities_store.py](src/memory/abilities_store.py) `get_what_can_you_do_response()`; [janet_brain.py](src/core/janet_brain.py) and [conversation_loop.py](src/core/conversation_loop.py) route to it |
| Orchestration module (if used) calls janet-seed | Yes | [ARCHITECTURE.md](../../janet_orchestration_module/ARCHITECTURE.md) — orchestrator uses JANET_API_URL |
| Menu bar is first-class client of janet-seed only | Yes | [ARCHITECTURE.md](../../janet_orchestration_module/ARCHITECTURE.md) section 5.1 — no direct orchestration dependency |

---

## Local WiFi

- API server binds `0.0.0.0:8080` by default (`JANET_API_HOST`).
- Clients set `JANET_API_URL` or `apiBase` to `http://<Mac-IP>:8080`.
- Optional: [mdns_advertiser.py](mdns_advertiser.py) for `_janet._tcp` discovery.
- See [INSTALL.md](INSTALL.md) and [OPERATOR_RUNBOOK.md](../../janet_orchestration_module/OPERATOR_RUNBOOK.md).
