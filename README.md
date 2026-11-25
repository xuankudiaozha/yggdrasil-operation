<!-- SENTINEL: Documents Yggdrasil in English and Simplified Chinese with matching Codex and Git installation instructions. -->
<img width="624" height="450" alt="download" src="https://github.com/user-attachments/assets/f6b8fc3b-f8a2-4a4f-b860-e80f1d19bcbe" />
# Yggdrasil Operation
FUTURE GADGET LABORATORYOPERATION YGGDRASIL


[English](#english) · [简体中文](#简体中文)

## English

A Codex skill for planning and producing scientific manuscripts, figures, and tables from approved research evidence. It uses one editable offline HTML plan for the manuscript structure, word limits, figure and table placement, and source links.

### Install

Paste this prompt into a Codex conversation.

```text
$skill-installer Install the skill from xuankudiaozha/yggdrasil-operation with --path . --name yggdrasil-operation
```

You can also clone the repository into your Codex skills directory from a terminal.

```sh
git clone https://github.com/xuankudiaozha/yggdrasil-operation.git "$HOME/.agents/skills/yggdrasil-operation"
```

If the skill doesn't appear after installation, restart Codex.

### Start a manuscript

```text
$yggdrasil-operation Read the approved analysis results at <local path> and prepare one editable offline HTML plan. Wait for my approval before drafting.
```

After approval, one scientific author drafts or substantively revises the manuscript. Two independent editors propose and cross-check language edits. The scientific author defaults to GPT-6.1 Sol with Extra High reasoning. The skill also supports standalone figure and table work and can resume existing Research Review Agent (RRA) projects.

Native subagent availability depends on the Codex client and model access. Editable Zotero citations require a working Word and Zotero integration. The optional Python helpers support evidence bookkeeping, citation-field inspection, and editor argument preparation.

See the [skill instructions](SKILL.md) and [example prompts](references/prompts.md).

## 简体中文

Yggdrasil Operation 是一个 Codex 科研写作技能，用已确认的研究证据规划和制作论文、图和表。它把论文结构、篇幅、图表位置和证据链接汇集到一份可编辑的离线 HTML 计划里。

### 安装

将下方指令粘贴到 Codex 对话。

```text
$skill-installer 请从 xuankudiaozha/yggdrasil-operation 安装技能，参数为 --path . --name yggdrasil-operation
```

也可以在终端运行下方命令，将仓库克隆到 Codex 技能目录。

```sh
git clone https://github.com/xuankudiaozha/yggdrasil-operation.git "$HOME/.agents/skills/yggdrasil-operation"
```

如果安装后没有看到技能，请重启 Codex。

### 开始写作

```text
$yggdrasil-operation 读取 <本地路径> 中已确认的分析结果，生成一份可编辑的离线 HTML 论文计划。等我批准后再开始起草。
```

计划获批后，由一位科学写作者起草或实质性修订稿件，两位独立语言编辑分别提出修改并互相核对。科学写作者默认使用 GPT-6.1 Sol，推理级别为 Extra High。技能也支持独立制作图表，以及续作已有的 Research Review Agent（RRA）项目。

能否调用原生子代理取决于 Codex 客户端和模型访问权限。插入可编辑的 Zotero 引文需要可用的 Word 与 Zotero 集成。可选的 Python 脚本可用于管理证据记录、检查引文字段和准备编辑参数。

参见[技能说明](SKILL.md)和[调用示例](references/prompts.md)。
