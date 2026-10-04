# meristem

> A tree of human work: **people recurse, the model works inside one line.**

[中文](README.md) · English

> **Status: alpha.** Structure and protocol still move; it runs as an application (`private: true`, not published).

---

## What this is

An agent runtime that lives in the terminal. Work is **not** decomposed automatically: both
splitting and converging are the human's.

- **The human splits and converges**: say something to open a line (`enter`), fork from a line
  (`ctrl+b`), wind it up (`ctrl+x`).
- **A line is an angle**: a conversation plus the role (prompt + tools) for that angle. The human
  can step in and keep talking at any time.
- **A fork is a new line**: its context grows out of the fork point, it is not a copy of the history.
- **Writes leave through one exit**: speak / fork / stop. The interface touches nothing else.
- **The ledger is the result**: append-only JSONL, written as it happens. No separate result store,
  no separate index.

Why a human does the recursing rather than the model: `docs/DESIGN.md` §1 carries the verdict from
the previous implementation -- 2443 nodes in one night with 86% never finished, self-reported fields
gamed 69% of the time, and only 3% of the criteria below the root still mentioning the original goal.

## Three design tradeoffs

**1. The human is the subject of recursion; the model is the subject of execution.**
Drift happens in every automatic hand-off, and human involvement restricted to the two ends is too
coarse. So forks are made by the human, and attention splits where the fork happens.

**2. The system prompt is named data, not an assembled string.**
One XML tag per section, sections always present and fixed for the lifetime of a role. Tool schemas
are the single source of tool semantics -- every hand is grown from its schema and description, with
no second definition to keep in sync.

**3. Screen, loop, capability and ledger each live in their own package.**
`tui` holds only **generic parts** (tree strip / status bar / key shapes / renderer lifecycle / one
palette): reusable in any app, and **anything OpenTUI already ships is not written again** (its
editor, its scrolling, its wrapping). How a screen is arranged and how domain words (hand / thought
/ line) are drawn belong to `terminal`. `harness` owns the single Loop and the transport, `roles`
owns roles and hands (including the job mechanism), and `atree` owns the ledger (append-only,
resumable). Assembly belongs to `terminal`.

## Code map

```
packages/
  atree/      ledger: node shape + append-only JSONL (written as it happens, resumable)
  harness/    the single Loop + transport (model words and hand results) + the defect node
  roles/      roles (one xml per role), hands (tools), skills, job table, MCP (not wired yet)
  tui/        generic parts: tree strip / status bar / key shapes / renderer and terminal restore / one palette
  terminal/   assembly and interaction: config (.env) -> ledger -> roles -> transport -> tree -> UI (one file per region)
docs/DESIGN.md    the design of this tree (why it looks like this, what is invariant)
AGENTS.md         this repo's hard constraints
```

## Running it

Put `.env` at the **repo root** (key names and format in `.env.example`; `.env` is not tracked):

```bash
export MERISTEM_BASE_URL='https://…'    # OpenAI-compatible endpoint (omit to use the provider's own)
export MERISTEM_API_KEY='…'             # the key value itself
export MERISTEM_MODEL='provider/model'
export MERISTEM_WORKSPACE='/abs/path'   # the agent's working directory; the ledger lands in <it>/.tree/ledger.jsonl
```

```bash
bun install
bun start            # for real. An empty ledger is fine: with no root yet, the first sentence is the first line
bun start --at <id>  # stand on one node's line
```

`.env` is loaded from the directory you start the process in (Bun does not search upwards), so from
anywhere else put the variables in the environment first. A missing required key fails at the entry
point naming the variable -- no fallback, no silent swap for a fake model.

## Tests

```bash
bun run typecheck    # both tsconfigs
bun test             # headless; the one test needing a real process ships its own child fixture
```

## License

MIT
