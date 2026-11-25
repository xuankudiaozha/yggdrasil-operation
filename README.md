<img width="208" height="150" alt="download" src="https://github.com/user-attachments/assets/f6b8fc3b-f8a2-4a4f-b860-e80f1d19bcbe" /><!-- SENTINEL: Documents installation, the manuscript workflow and optional tools for the public Yggdrasil release. -->
# Yggdrasil Operation
FUTURE GADGET LABORATORYOPERATION YGGDRASIL
![Uploading downl<svg font-family="&quot;Microsoft YaHei UI&quot;, -apple-system, BlinkMacSystemFont, &quot;Segoe UI&quot;, sans-serif" font-weight="430" data-d-component="svg" fill="currentColor" style="color:rgb(74, 35, 95)" viewBox="0 0 340 245" width="100%" xmlns="http://www.w3.org/2000/svg"><circle cx="170" cy="112" r="96" fill="none" stroke="#A68E61" stroke-width=".7" stroke-dasharray="3 5" opacity=".65"/><circle cx="170" cy="112" r="83" fill="none" stroke="#A68E61" stroke-width=".6" opacity=".35"/><g stroke="#A68E61" stroke-width="1.5" fill="none" stroke-linecap="round"><path d="M170 185 Q160 152 170 114 Q181 87 170 34"/><path d="M170 145 Q132 115 91 109 L55 81 M91 109 L71 124 M128 120 Q116 80 87 56 M116 80 L117 40"/><path d="M172 115 Q207 92 239 103 L283 77 M239 103 L265 130 M207 95 Q219 62 248 47 M219 62 L211 29"/><path d="M171 88 Q151 65 143 30 M174 77 Q192 53 194 19"/><path d="M170 178 Q139 194 110 217 L66 224 M138 198 L130 236"/><path d="M170 178 Q200 194 230 217 L274 224 M202 198 L210 236"/><path d="M170 177 L170 238"/></g><circle cx="55" cy="81" r="3" fill="#B8A175"/><circle cx="71" cy="124" r="3" fill="#B8A175"/><circle cx="87" cy="56" r="3" fill="#B8A175"/><circle cx="117" cy="40" r="3" fill="#B8A175"/><circle cx="143" cy="30" r="3" fill="#B8A175"/><circle cx="170" cy="34" r="3" fill="#B8A175"/><circle cx="194" cy="19" r="3" fill="#B8A175"/><circle cx="211" cy="29" r="3" fill="#B8A175"/><circle cx="248" cy="47" r="3" fill="#B8A175"/><circle cx="283" cy="77" r="3" fill="#B8A175"/><circle cx="265" cy="130" r="3" fill="#B8A175"/><circle cx="170" cy="146" r="12" fill="#A68E61" fill-opacity=".12" stroke="#A68E61"/><circle cx="170" cy="146" r="4" fill="#A68E61"/><text x="18" y="160" font-size="8" fill="#A68E61" letter-spacing="2">TRUTH</text><text x="273" y="160" font-size="8" fill="#A68E61" letter-spacing="2">ORDER</text></svg>oad.svg…]()

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
