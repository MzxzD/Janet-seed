# Native Engram (in-weight) — model acceptance criteria for Janet

Janet’s **PhraseMemory** ([`src/core/phrase_memory.py`](../src/core/phrase_memory.py)) implements **conditional memory at orchestration layer** (hashed lookup + gate + prompt fuse). This doc defines when to adopt a **native** DeepSeek-style Engram (third block inside the transformer) in Ollama or another local runtime.

## Track decision: hybrid (H)

- **Now:** Orchestration PhraseMemory + Green Vault ([`/api/learn`](../janet_api_server.py)) for static / factual recall patterns.
- **Later:** Swap or add a **local checkpoint** that includes Engram (or equivalent conditional memory) when tooling catches up.

## Acceptance criteria (must have)

1. **Local runtime** — Loads under **Ollama** (or Janet’s existing LiteLLM path) with **no required cloud** inference.
2. **Documented architecture** — Paper-equivalent or release notes state **O(1) addressing**, **conditional memory** separate from MoE, and **end-to-end** training (not a bolt-on adapter unless Janet explicitly adopts adapter training).
3. **Deterministic lookup path** — Same token history → same table indices (supports **prefetch** and host-RAM tables, per Engram paper).
4. **License** — Compatible with Janet distribution (e.g. MIT / Apache / clearly open weights with acceptable terms).

## Strongly preferred

- **Host offloading** — Table in DRAM with measured **low single-digit %** (or better) throughput loss vs. on-device table at Janet’s target context length.
- **Gating** — Learned or explicit **contextual gate** so retrieval noise does not dominate (maps to Janet’s “untrusted recall” policy).
- **Open weights + reproducible eval** — Public benchmarks or scripts for MMLU-class factual, reasoning (BBH/ARC), code (HumanEval), and **long-context needle** tasks.

## Benchmarks Janet cares about

| Area | Why |
|------|-----|
| **Factual / static knowledge** | Engram targets repeated pattern and knowledge offload. |
| **Reasoning (BBH, ARC)** | Paper reports gains beyond rote QA; Janet should confirm no regression. |
| **Code / math** | IDE and researcher workflows (HumanEval, MATH-style). |
| **Long-context retrieval** | NIAH / multi-hop in long prompts (Constitution + vault + chat). |
| **Offline latency** | Tokens/s on Apple Silicon / cluster targets with **phrase memory disabled** vs. enabled. |

## References

- [Conditional Memory via Scalable Lookup (arXiv:2601.07372)](https://arxiv.org/abs/2601.07372)
- [deepseek-ai/Engram](https://github.com/deepseek-ai/Engram) (reference implementation / weights when published)

## Environment (orchestration)

| Variable | Meaning |
|----------|---------|
| `JANET_PHRASE_MEMORY` | `1` (default) / `0` to disable PhraseMemory |
| `JANET_PHRASE_MEMORY_TAIL` | Tokens in tail for hashing (default `3`) |
| `JANET_PHRASE_MEMORY_MIN_CONF` | Minimum stored confidence to inject (default `0.0`) |
| `JANET_PHRASE_MEMORY_MAX_CHARS` | Cap on injected text (default `4000`) |

API: `GET /api/phrase-memory/stats`, `POST /api/phrase-memory/entry`, `POST /api/phrase-memory/delete`.

## Context fusion (SEED)

All user-prompt augmentation for `JanetBrain` runs through [`src/core/context_fusion.py`](../src/core/context_fusion.py) in fixed order: **memories → tone → PhraseMemory**.

| Request `context` key | Effect |
|------------------------|--------|
| `skip_context_fusion` | Skip **all** augmentations (raw user text only) |
| `skip_relevant_memories` | Skip Green-Vault-style memory block only |
| `skip_tone_context` | Skip tone line only |
| `phrase_memory` / `skip_phrase_memory` | Skip PhraseMemory only (legacy + explicit) |
