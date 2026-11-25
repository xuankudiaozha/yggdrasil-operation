<!-- SENTINEL: Defines paired independent language edits, reciprocal checks, and local request preparation against available models. -->
# Independent Scientific Language Editing

## Routing and settings

Apply Stage 2 to authorized prose after the [single-thread scientific author](writing.md#mission-and-authority) finishes the draft or substantive revision. For language-only work, use the supplied original directly. This applies to INITIAL, ITERATE, scoped EDIT and [POLISH](polishing.md). Planning, statistics discussion, result verification and internal handoffs do not start editing.

The parent reads this contract and supplies only the [editor role](../agents/scientific_language_editor.md), relevant [section profile](language_editing_profiles.json), exact target text, necessary read-only context, and short locked facts or terms. Pass the relevant language Anchor, journal requirements, preferences and budget when available. Preserve citation identifiers and panel labels. Keep unrelated project files and complete execution logs out of editor context.

[scientific_language_editor.json](../agents/scientific_language_editor.json) controls the defaults for both editors, `gpt-6.1-sol/xhigh`, automatic invocation enabled and recursion disabled. Explicit per-task model, effort and automatic-invocation settings take precedence. The supported user shorthands `6.1sol`, `5.6sol` and `exhigh` resolve to actual model and effort IDs. Keep this configuration in the skill.

## Real calls and reciprocal review

1. Spawn two actual native `collaboration.spawn_agent` threads with different task names and `fork_turns="none"`. Give both the same source version and scoped text. They separately scan every selected sentence and propose exact local replacements. Run in parallel when capacity permits. Share neither proposal set until both have finished.
2. Use `collaboration.followup_task` in each of those threads to check the other editor's proposals against the same original and nearby context. Each reviewer identifies the accepted and declined edits. For long manuscripts, reuse the pair on complete sections in order and carry only necessary term decisions forward. For a scoped revision, process the selected paragraphs together with just enough nearby context for continuity.
3. The parent merges only peer-confirmed, nonconflicting edits that pass a direct diff and semantic check. Apply identical proposals once. For competing edits to the same passage, use a peer-confirmed version that safely improves the prose. Keep the source wording when disagreement or a scientific qualification remains unresolved. Source changes invalidate the affected proposals.
4. Compare the integrated text with the actual source. Check numbers, units, comparisons, definitions, eligibility, models, evidence strength, limitations, citations and callouts. Verify semantic qualifiers even when numeric tokens match. Repair only the affected language. Send scientific conflicts to the author or researcher and preserve safe work.

Preflight the requested models and efforts against the actual runtime. Record actual writer and editor model settings, native call identities, source version, peer-check and fidelity status in the existing receipt or chat. Unavailable or failed calls leave the affected editing scope incomplete. Preserve the author draft and report the failure or an explicit user opt-out. Neither the author nor the parent simulates either editor.

## Optional request helper

`python <skill-directory>/scripts/language_editing.py <local-request.json>` prepares the arguments for one native editor call. Reuse the returned template with a distinct task name for each editor. Runtime dispatch and the reciprocal review remain the parent's work.

Input requires `text` (the complete selected section or paragraph text) and `section` (a profile key). Optional `journal`, `language_anchor`, `preferences`, `word_limit`, `locked_facts`, `purpose` and `language_editor` retain their existing meanings. `purpose` defaults to `manuscript` and also accepts `language_only`. Planning, statistics, results checks and handoffs return no request. The optional helper validates model and effort against the Codex model cache and includes only the selected profile. Use the actual runtime availability check when preparing native calls manually. A valid result prepares arguments. Failed preflight exits 2. The editor context cannot invoke the helper recursively.

## Integration

Keep the source version and accepted edits traceable in native transcripts or existing revision history. Where needed, use small local temporary proposal files and a source hash. Retain a minimal source copy only when existing history lacks a recoverable source version. Apply prose through the [field-safe Word path](word-zotero.md) when authorized, maintaining one authoritative DOCX. Clear temporary files after verification unless needed for recovery.
