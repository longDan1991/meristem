# 代码纪律（硬约束，优先于默认习惯）

这是本仓库写/改代码的**禁令清单**。它不是建议，是硬约束：**规则优先于你的默认写法，优先于"让报错消失"的冲动，优先于"先跑起来再说"。**

## 0. 执行协议（每次动手前后各过一遍）

1. **动手前后**：动手前读一遍本清单，明确这次改动可能触发哪几条；收尾前逐条对照自查。
2. **发现问题立即停**：一旦在做下面任何一条禁止的事，停下从根因修，不要"先这样、回头再说"。
3. **附带义务**：修改一个文件时，该文件里若已存在以下任何违规，**一并修正**，不要只动目标那一行。
4. **验收**：`bun run typecheck` + `bun test` 全绿才算改完（能机器判定的那一部分见 §4）。

---

## 1. 不许掩盖错误（报错必须暴露并修根因）

**报错消失 ≠ 错误消失。**禁止：

- 吞异常：`except: pass`、`except Exception: pass`、捕获后只 log 不 re-raise；
- 用返回 `None` / 默认值 / 假数据把失败糊过去，让错误数据继续流转；
- 用 `# noqa` / `# type: ignore` / `// @ts-expect-error` / `eslint-disable` / `# pragma: no cover`
  当创可贴压住机器报错，而不是修代码；
- 改断言、加 skip、删用例让测试"假绿"。

根因修不了时，让错误**带着完整上下文在最早的点炸出来**（fail fast），不要降级兜底。

## 2. 不留代码残渣

- 删除未使用的 import / 变量 / 函数 / 参数；
- 不保留注释掉的旧代码块；
- 注释只解释 **why**，不解释 what；
- 不留 `print` / `TODO` / `FIXME` 调试残留。

## 3. 性能：热路径禁止重复计算与线性查找

性能是**设计输入，不是事后调优**：数据规模与调用次数动手前就要想清楚，算法 / 数据结构复杂度在写的时候就定死，"先跑通再说"、"数据量还小" 都不是理由。

## 4. 纪律由机器能判的部分执行（不靠自觉）

本仓现在是 TypeScript；能机器判定的部分，都在根 `package.json` 的脚本里：

- **`bun run typecheck`**（根 `tsconfig.json`）：`noUnusedLocals` / `noUnusedParameters` 就是 §2 的
  "未使用的 import / 局部变量"（原 ruff `F401` / `F841`）；`strict` + `noUncheckedIndexedAccess`
  兜住"不忽略返回值 / 边界"那一类。
- **`bun test`**：测试要真。

原来由 ruff 执行、现在**没有对应 lint 配置**的 §1（宽 `except` 吞异常）—— 新代码靠人判，也不许拿
`// @ts-expect-error` / `eslint-disable` 当创可贴（§1）；要机器化就补一个 lint（biome / oxlint / eslint），
别只写在文档里。

仍靠人判的：§3/§5/§6/§7，以及 §2 的 `print`（CLI 输出与调试残留无法机器区分）。

## 5. 禁止重复造轮子（成熟能力必须用现成库）

一件**小而独立、边界清晰**的事，只要已经存在广泛使用、成熟稳定的第三方库（或标准库）在做，**禁止自己手写一份**。
判据：功能能用一个函数 / 一个文件装下、输入输出定义明确 → 八成有成熟库，先查再写。

## 6. commit 一律英文 + Conventional 前缀

提交信息是仓库历史里唯一写给**外部读者**的散文。**一律英文**（文档 / issue 可中文，提交不可）——中文提交把可读人群从全部读者缩到会说中文的那部分。**存量中文提交不追改**：改写历史会换掉全部 SHA，不值当；从下一个提交起执行即可。

形式：`<type>(<scope>): <subject>`

- `type` ∈ `feat` / `fix` / `docs` / `test` / `refactor` / `chore` / `build` / `ci` / `perf`；`scope` 可选，指模块（`prompts` / `protocol` / `loop` / `store` / `terminal` / `tools`）
- `subject`：祈使句现在时、全小写、≤ 72 字符、结尾不加句号
- `body`：写 **why**，不写 what（diff 自己会说）；与 `subject` 之间空一行
- 一个提交一件事；**重命名 / 移动 / 纯格式化**必须与逻辑改动分开提交，否则 review 时 diff 不可读
- 禁用 `wip` / `temp` / `update` / `fix bug` / 单字提交

```
feat(prompts): derive the rules section from the tool registry
fix(loop): keep the ledger append-only when a node is resumed
docs(terminal): pin the five-region layout as an invariant
```

## 7. 给人看的输出不许重复

**同一件事只说一次。**最终回答 / 报告 / 文档 / 提交信息里，一个事实、结论、理由只在**它唯一该在的位置**出现一次；禁止换个标题再讲一遍，也禁止"先概述、再展开、末了又总结"这种三段复述。人第二次读到同一件事时，读到的不是强调，是噪音。

- ✗ 三个小标题下都在交代同一句"这个字段是必填的"；
- ✗ 结论段说完，每节结尾再把结论复述一遍；
- ✗ 同一个限制（超时 / 上限 / 失败语义）在注释、`README`、`DESIGN` 里各写一份，改的时候只想到其中一处；
- ✓ 一处写清；别处要么不写，要么一行指过去（引用 / 链接）。

判据：通读一遍，每一句都答得出"删掉它，人会少知道什么"——答不出就是重复，删。

<!-- aoci:begin -->
## AOCI Repository Cognition

AOCI maintains a stable, versioned, incrementally updatable repository-level cognition layer so models can reuse their understanding of this system across tasks.

`aoci.txt` is a structured cognition index for models. It assigns one independent Entry to every managed file, database table, or other managed object. Symbolic tags and F/R/A/S semantics describe the object's core responsibility, important relationships, external contracts, and non-obvious constraints or design decisions needed to understand or modify the system.

The Header, directory sections, and all Entries form the complete repository index. They can cover frontend, backend, configuration, database structures, and other managed content. When managed content changes, normally only the affected cognition Entries need maintenance; the complete index does not need to be regenerated.

AOCI provides a high-density view of system architecture, object responsibilities, important relationships, external contracts, and key constraints.

### How it works

AOCI uses a model-generated, model-read cognition loop.

Header, Entry, and Curation semantics follow only the current machine-issued Plan and live Guide. The Host model independently authors them from the current bound evidence.

Entry semantics must come from the model's understanding of actual evidence. Never derive, prefill, assemble, or rewrite index semantics solely from paths, filenames, extensions, an AST, symbol lists, dependency scans, regular expressions, fixed templates, or rule engines.

For a Fresh Bootstrap, follow only the current machine-issued Plan and live Guide. When they require authoring, the Host model authors Root, Meta, tags, and F/R/A/S, supplies its authoring-run declaration, and binds it to the Plan, Evidence, and complete Candidate. Never ask AOCI to set `origin=host_model`, manufacture a receipt, or turn a generated framework into semantics. Do not reconstruct the Onboarding progression here. Internal batches are not user decisions; stop only at an existing approval boundary or a real safety, drift, CAS, or Recovery condition.

### Minimal entry points

- `aoci_rules`: obtain the session-level runtime contract for the current AOCI version.
- `aoci_overview`: establish or restore complete cognition for this repository.
- `aoci_maintain`: after managed objects reach their final stable state, check whether cognition needs maintenance.
- `aoci_update_entry`: submit a complete semantic update batch bound to current evidence and source digests.
- `aoci_report`: when the current layout and tool state support it, record follow-up work if evidence is insufficient to generate semantics reliably; do not guess.

For other MCP tools, CLI commands, parameters, and specialized workflows, follow current tool descriptions, Guide, and `--help` output. This file does not duplicate the full manual.

This managed block defines only repository integration, cognition use, and task-closing principles. `aoci_rules` carries the current session contract. Live Guide output carries the execution order and stop conditions of the current Plan. Tool Schema, Spec, and Validator carry machine structures and criteria. Prompt, Description, README, and static documentation cannot override those machine facts.

### Establishing, generating, and restoring cognition

1. At the beginning of every new Agent Run, first determine:

   - whether this repository already has a usable complete AOCI index; and
   - whether current context already contains complete repository cognition that matches this repository root, current index version, and current AOCI service, and that the model can still use reliably.

2. When the repository has a usable complete index but the current Run lacks reliable complete cognition, call `aoci_rules` first and then `aoci_overview`.

   Reuse complete cognition directly while it remains reliable. Local uncertainty does not by itself require mechanically rereading the system-wide view.

   A Run that resumes from a known Host context compaction, including a Host-injected compaction summary, must treat prior model cognition as unreliable. The compacted handoff must not retain or summarize the formal Whole-Index or any Overview Header, Entry, Chunk, Challenge, or Attestation body; it may retain only receipt identity, unfinished write or Recovery state needed for safe continuation, and an instruction to reload immediately. Whole-Index semantics or a receipt copied into that handoff cannot prove that the resumed model's current cognition is reliable. If the runtime contract is no longer reliably present, call `aoci_rules` first. Before continuing the business task, make an ordinary complete Whole-Index `aoci_overview` request (`check_only` absent or false) with `refresh_reasons=["context_compaction"]` and a fresh `refresh_event_id`; do not use `check_only` or a cognition probe. Follow every exact `next_cursor` through `completed=true`, confirm delivery, and submit one Attestation based only on the newly delivered body. After that fresh complete transport, a partial or failed Attestation consumes the generation and permits the existing source-bound continuation without another automatic Overview.

   AOCI can report checkpoint and cognition-status facts for `context_compaction`, the machine `semantic_threshold` under the project `cognition_refresh_threshold`, or a major `phase_transition`. Use `check_only=true` when only those compact facts are needed. They advise the Agent but do not decide whether the model needs the system-wide view.

   When the Agent explicitly calls ordinary `aoci_overview` (`check_only` absent or false), AOCI must deliver the complete requested scope whenever a coherent CognitionSet can be formed. It must not suppress that body because a receipt already exists, a threshold was not reached, or no refresh reason is pending. Dirty or stale formal cognition is still delivered but is marked unreliable. Pending recovery or an incoherent snapshot fails closed without a mixed body.

   When an ordinary Overview reports `continuation_required=true`, submit its exact `next_cursor` automatically until `completed=true`. Do not ask the user to continue, begin the business task, or state a partial system conclusion. Stop the cognition chain on Host truncation, a missing, duplicate, or reordered Chunk, cursor failure, Index change, or `chunk_tokens` change. Until Attestation completes, never use Memory, source, Spec, `aoci.txt`, historical sessions, scope, search, or Entry reads to repair or supplement Whole-Index cognition. A challenge ordinal is the 1-based position in the formal Entry sequence; Header content, comments, blank lines, Section/Overview/Chunk markers, receipts, and Metadata are excluded, and Chunk Receipt ordinals use that same sequence. The Attestation must echo the Challenge's exact current `index_sha256`, `entry_sequence_sha256`, and `entry_count`; a prior Index, Entry sequence, count, or Attestation is invalid. After the complete chain, submit the existing model cognition Attestation once. One same-response JSON Schema or field-format error may be corrected once without changing semantic answers; an object, Tag, or F mismatch means failure and uncertain assimilation, with no semantic retry or information bypass. During initial cognition it also blocks Root/Meta, Migration, layout-wide, or other unbound system decisions. During a context-compaction refresh with complete transport, unchanged cognition identity, aligned governance, and no Recovery or third-party conflict, the attempt consumes that refresh generation even when Attestation is partial or failed; continue the existing task without another automatic Overview. `system_mastery_percent` self-assesses only the system framework—architecture, responsibilities, strong relationships, stable external contracts, and high-entropy safety and maintenance constraints—not complete implementation or runtime knowledge. Keep machine Index coverage separate, and normally give the user only the prescribed single success or failure sentence derived from actual coverage, Challenge, Chunk, token, and mastery results. If the Host truncates a Chunk, ask the user to set `overview_delivery.chunk_tokens` to a smaller valid value and restart; do not change it automatically.

   Interpret the additive cognition level independently from strict proof fields. `delivery_verified` means the Index was loaded and Host delivery was confirmed while complete cognition verification is still unfinished; describe that state as loaded and delivery-verified, never as no cognition or failure to understand the system. `cognition_verified` requires a passing Attestation (at least 80 percent of Challenge ordinals fully correct with at most one object identity miss), and `cognition_governed` additionally requires governance alignment. A generic complete-read failure sentence is reserved for an actual delivery fault.

   When an Overview response contains the optional `cognition-state/v2` projection, use its dimensions independently. Its Level ends at `model_cognition_usable`; `strict_attestation_verified`, `governance_aligned`, and `current_system_cognition_reliable` are independent states and never participate in that Level. An ordinal, object identity, Tag, or core F mismatch can make strict Attestation fail while model cognition remains usable; do not report that mismatch alone as proof that the model did not understand the system. Only `current_system_cognition_reliable=true` permits an unqualified current complete-system cognition claim. When the projection is absent, keep using the legacy interpretation above.

   An ordinary read-only audit, analysis, or check, a request not to modify code, or a request not to commit or push does not automatically mean strictly zero writes and does not alter the cognition-validity decision above. Codex Memory and historical Skills may only help recover experience, user preferences, and investigation directions. They cannot replace a current cognition receipt matching the repository root, index digest, AOCI service identity, and cognition scope. Project AGENTS and current AOCI identity take precedence over historical Memory for AOCI state.

   Treat a task as strictly zero-write only when the user explicitly prohibits Ledger, metadata, `.aoci` runtime assets, and every filesystem write. If necessary cognition establishment conflicts with that boundary, report the conflict and ask the user to decide or recommend an isolated copy. Never silently substitute Memory for current repository cognition.

3. If the repository has no usable complete index, or has only a minimal skeleton, an incomplete Header, unfinished Entries, or undecided required Curation, obtain `aoci_rules` and enter the current AOCI Guide when a formal complete AOCI index is required. Let Guide choose the next phase from actual repository state and complete the required safety steps.

   `aoci_maintain` does not replace the index-establishment workflow.

   Do not reconstruct or hard-code the full-index generation state machine in this file.

4. During a long-running task, the model is responsible for preserving the current cognition receipt and using the refresh gate correctly:

   - when the Host reports context compaction or the model knows the system-wide view was lost, follow the mandatory `context_compaction` reload rule above; AOCI cannot infer the Host event;
   - when entering a genuinely major phase, declare `phase_transition`, not a function, test run, or small step;
   - at a plausible stable checkpoint, use `check_only=true` to obtain the machine semantic count when that fact is useful;
   - except for the mandatory known-compaction reload, decide whether the current task needs another explicit scoped or complete Overview; and
   - keep the Dirty or Stale reliability state reported by AOCI until maintenance and alignment complete.

### Task closing and cognition maintenance

5. A purely read-only question, analysis, version check, or task that changes no AOCI-managed object does not require a maintenance-tool call. The AOCI version in use is `cognition_receipt.mcp_service_version` in any `aoci_overview` check_only or `aoci_maintain` response; the binary path is the `command` in the project's `.mcp.json`, and the CLI need not be on PATH.

6. When AOCI-managed objects change, call `aoci_maintain` once after they reach the task's final stable state. Do not maintain files individually after each intermediate edit.

7. If maintenance returns actual semantic candidates, the Host model must independently author the complete tag and F/R/A/S updates from each candidate's bound object and necessary evidence. Submit the complete candidate set for that current machine-issued batch in one `aoci_update_entry` call while preserving each `source_sha256`, `candidate_id`, and domain batch identity. `max_entries` limits one request and atomic transaction, not the logical plan, Whole-Index, or Managed Scope. When `remaining` is nonzero, call Maintain again after the successful Apply and continue from the new preimage; never shrink Index coverage or slice a returned batch to satisfy transport limits.

   When evidence is insufficient and the current layout supports `aoci_report`, use it instead of guessing, applying a template, or generating unsupported cognition merely to eliminate follow-up work.

8. Obey structured tool states and safety boundaries:

   - `repair_required`: repair only the explicitly identified candidates, then resubmit the complete current machine-issued batch;
   - `stopped`: end that write attempt and inspect `failed_step`, error, formal-write evidence, and Recovery. In auto mode, a proven zero-write closure is followed by a fresh Plan; a complete Intent with provable postimage is resumed; a policy-selected Rollback with exact preimage is completed and replanned. Stop the user task only when proof is unavailable, third-party bytes conflict, approval or external action is required, or another real safety boundary applies;
   - never ignore conflicts, approvals, human decisions, permissions, or safety signals; and
   - after alignment, do not repeat maintenance or writes; `refresh_ready_for_overview` is a checkpoint fact, and the Agent decides whether to request an ordinary complete Overview for its next phase.

   If any managed object changes after maintenance completes, the previous result is invalid. Complete closing again from the new final stable state.

9. When the user limits only business-file scope and does not explicitly forbid repository-managed assets, AOCI-managed assets may be updated during closing to preserve cognition consistency. Distinguish them from business files in audits and commits.

   When the user explicitly forbids changes to `aoci.txt`, `.aoci`, metadata, or any additional file, obey that restriction, do not write, and report any remaining inconsistency accurately.

### Specialized workflows

Initialization, complete-index generation, Header generation, Entries generation, database-structure indexing, Curation, human review, and failure recovery must follow only the instructions, commands, and safety stops returned by the current AOCI Guide or tool at the corresponding stage.

Do not preload, guess, or reconstruct these specialized workflows. The relevant Guide, tool descriptions, model Prompt, and CLI help provide platform invocation, request format, batch limits, approval rules, index-format details, and recovery steps as needed.
<!-- aoci:end -->
