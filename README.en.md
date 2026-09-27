# meristem

> A recursively working LLM tree: nodes decide for themselves whether to branch, the root converges to a conclusion.

[中文](README.md) · English

> **Status: alpha.** The system-prompt structure and the protocol are still moving; no stability guarantees. Not published to PyPI (`[tool.uv] package = false`) — run it as an application.

---

## What it is

An agent runtime that lives in the terminal. The task is **not** pre-orchestrated into a DAG; the model expands it recursively over a tree:

- A node spawns children with `create_children`; each child is its own independent conversation.
- Each node's dialogue is flat and has its own ledger (`core/runtime/dialogue.py`).
- Nodes talk through `communicate`: a parent asks / demands rework / re-tasks a child, a child reports progress and conclusions to the parent — task information settles hierarchically on each node, so no conversation ever bloats.
- **There is exactly one control flow — a single Loop** (`core/runtime/loop.py`). It is the only thing that advances a tree.
- A session = one tree + one append-only record (`core/runtime/store.py`). **Writing is the ledger.**
- The verdict is not the code's to make: `core/protocol/gate.py` only validates field shape; whether something is done is judged by the parent (ultimately a human) from the messages.

## Three design decisions

**1. The system prompt is not a built string — it is a named-section data structure.**

`system = Record<section name, content>`: one same-named XML tag per section, and six sections are always present (no conditional sections under the communication model), frozen for a node's lifetime. Prose, discipline, the skill list and the tool list are each a section (`core/prompts/`). The invariants live in `docs/PROMPTS.md`.

**2. The tool schema is the single source of tool semantics.**

The `rules` section is derived from the tool list, the `tools` section is one line per tool (`core/prompts/tools.py`), and that list itself is derived from each tool's scope declaration. A tool is just an `@mcp.tool` function — schema and implementation in one place, with no second definition to keep in sync (`tools/defs.py`). The verdict is not the code's to make: `communicate` only delivers the message; whether something is done is judged by whoever receives it (the parent, ultimately a human).

**3. The bash tool does not fork/exec.**

Commands run on [`llmbash`](https://pypi.org/project/llmbash/) — an in-process bash-compatible shell outside this repo (Rust, 50+ common commands with no dependency on system binaries). Output is slimmed per command type before it enters the context (`tools/bash.py`).

## Code map

```
cli.py              the only executable entry point: parses arguments
main.py             initialisation (workspace / API key / trace root), then dispatch to the terminal session

core/
  config.py         deployment config: where the workspace is, where past sessions are scanned
  events.py         event outlet: dispatch (type, payload) to consumers in registration order
  llm.py            LLM adapter: messages in, Message out (text + tool calls)
  prompts/          the named-section structure of system (prose / rules / skills / tools)
  protocol/         form fields + shape validation + rendering node state / communication messages
  runtime/          the single Loop + protocol ops + scheduling rules + session store
tools/              the only channel between the model and the program
  defs.py           @mcp.tool functions: schema and implementation in one place
  bash.py           commands run on the llmbash in-process shell
  skills.py         */SKILL.md under SKILLS_DIRS -> fastmcp resources, read on demand
terminal/           a Textual app: tree on the left, stream in the middle, five regions (docs/TERMINAL.md)
```

## Running it

Four values in `.env`:

```bash
export TREE_BASE_URL='...'        # model endpoint (OpenAI-compatible)
export TREE_API_KEY='...'
export TREE_MODEL='...'
export TREE_WORKSPACE='/path/to/workspace'   # everything produced lands here
```

```bash
uv run python cli.py        # real run: the task and its acceptance criteria are agreed inside the terminal
uv run python cli.py -r     # resume: pick a past session from a list and load it as the current one
```

Without `TREE_API_KEY` the entry point fails immediately — it will not silently fall back to a fake model.

## Tests

```bash
uv run python tests/test_<module>.py     # cli / intake / llm / protocol / resume / terminal_pty / tools / tty
uv run ruff check                        # code discipline, see AGENTS.md §12
```

The tests are driven by a fake model (`FakeLLM`) and need no real API key.

## Docs

| Document | What it covers |
|---|---|
| `docs/PROMPTS.md` | the design and **invariants** of the system prompt |
| `docs/TERMINAL.md` | the design and **invariants** of the terminal layout |
| `AGENTS.md` | this repo's hard-constraint rule list; the machine-decidable parts are enforced by ruff |

## License

MIT
