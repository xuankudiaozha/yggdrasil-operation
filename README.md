<img width="624" height="450" alt="download" src="https://github.com/user-attachments/assets/f6b8fc3b-f8a2-4a4f-b860-e80f1d19bcbe" /><!-- SENTINEL: Documents installation, the manuscript workflow and optional tools for the public Yggdrasil release. -->
# Yggdrasil Operation
FUTURE GADGET LABORATORYOPERATION YGGDRASIL


A Codex skill for planning and producing scientific manuscripts, figures, and tables from approved research evidence. It uses one editable offline HTML plan for the manuscript structure, word limits, figure and table placement, and source links.

## Install

Clone the repository into your Codex skills directory.

```sh
git clone https://github.com/xuankudiaozha/yggdrasil-operation.git "$HOME/.agents/skills/yggdrasil-operation"
```

## Start a manuscript

```text
$yggdrasil-operation Read the approved analysis results at <local path> and prepare one editable offline HTML plan. Wait for my approval before drafting.
```

After approval, one scientific author drafts or substantively revises the manuscript. Two independent editors propose and cross-check language edits. The scientific author defaults to GPT-6.1 Sol with Extra High reasoning. The skill also supports standalone figure and table work and can resume existing Research Review Agent (RRA) projects.

Native subagent availability depends on the Codex client and model access. Editable Zotero citations require a working Word and Zotero integration. The optional Python helpers support evidence bookkeeping, citation-field inspection, and editor argument preparation.

See the [skill instructions](SKILL.md) and [example prompts](references/prompts.md).
