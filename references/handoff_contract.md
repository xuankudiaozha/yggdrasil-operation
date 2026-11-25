<!-- SENTINEL: 简洁保留综述三级职责、存储格式 6、科学锁及真实作者和双编辑回执，脚本随 Yggdrasil 调用。 -->
# 既有综述状态及数据合同

## 规范文件与启动

以下原生文件适用于明确启动或继续四轮综述证据工作的项目。遵守实际工作区和项目治理指令，变更证据和按需参数文件维持同级附件。

| 文件 | 职责 |
| --- | --- |
| `rra_v6_handoff.md` | 唯一当前科学状态、完成阶段、待执行动作和规范索引位置。 |
| `rra_v6_evidence.json` | Round 1起的检索回执、去重身份、筛选规则与状态、证据结果、Anchor、命题、大纲及段落映射；同一机器索引更新，已执行检索记录不覆盖。 |
| `rra_v6_search_provenance.md` | 从同一JSON派生的简短检索概况与筛选／映射统计；明细按Search ID或文献ID读取JSON，不复制逐篇状态、全文检索式或原始回执。 |
| `anchor_refine_input.md` | Round 4 的内部证据映射导出。该文件派生自科学锁，正文与当前表达安排遵循已批准计划。 |

Zotero仍是书目/PDF权威；JSON只存科学提取、检索事实和必要标识，服务不可用时暂存实际取得元数据供恢复导入。原始检索返回／导出保留在被引用的原位置作为必要凭据；原始响应与规范提取各有用途，不再复制成多份书目或PDF库。完整检索式、限制、用途、原始凭据位置和逐篇状态均通过JSON按ID查询；仅在明确交付需要时按需导出明细，不长期并存JSON、表格和Markdown等重复明细。成功更新并验证后清理临时输入、测试输出和探索图；仅保留能显著减少昂贵重算的缓存，放在明确的cache目录。不另建逐篇Markdown、平行决策记忆或历史handoff。实质规范变更先写既有等效历史；原生记录不能承载该次变化、理由和依据时，在同目录 history.jsonl 按 id、time、target、change、reason、evidence 六字段追加一次，再通过既有 CLI 更新相应当前状态。time 使用真实含时区时间；证据按ID引用，不复制检索返回、逐篇索引或整份新旧正文。日常只读当前规范，追溯时仅检索相关事件；无变化和纯排版不记。历史写入不代表变更已生效，中断后先核对并修复未写回部分，不能据日志绕过研究者选择、科学锁或重新授权。

`rra.py` 只依赖Python标准库，CLI的首个位置参数始终为研究目录。引用技能脚本、Anchor资料和拟用图表等本地文件时用实际绝对路径，不按当前shell目录猜相对位置。使用当前环境实际可用的 Python 解释器，建议加 `-B -X utf8`。从 Yggdrasil 技能目录调用 `scripts/rra.py`。

交接文件采用 `---` 包围的**JSON对象作为YAML frontmatter**，之后是简短可读摘要。JSON是YAML兼容子集，供标准库可靠读取；不要手改成任意YAML语法。通过脚本更新，避免摘要和机器字段分歧。加载损坏/缺失状态时明确报错，不创建默认上游。旧6.0索引的新增来源字段只能据原始回执补齐，缺少真实时间、完整检索式或原始返回时保持未核验，不自动回填或假造历史。

始终存在 `rra_version:6`、`project_id`、`mode:live|fixture`、`research_domain`、`active_round`、`completed_round`、`next_round`、`session`、`status`、`title_status`、`next_actions`。状态是当前值，不是事件流。交接每轮覆盖当前有效科学问题、范围、关键证据、约束及下游动作，不保留讨论史；真实检索时间与来源在规范JSON中长期保留，独立Markdown仅派生概况。Round 1选定后增加 `core_question`、`research_scope`、`working_title` 及选定科学简报 `rqe_summary`；Round 2增加 `selected_anchors`、`zotero_collection`、`evidence_inventory` 和充分性判断；Round 3增加 `formal_title`、`central_thesis`、`selected_outline`；Round 4增加 `anchor_refine_input`。尚不存在的结果字段不提前填充。

`research_scope` 是含研究对象、纳入范围与排除边界的对象或简洁文字，必须由研究者选择的方案确定。`selected_outline` 是指向JSON中 `outline` 的路径/键及内容摘要，不复制大纲全文。核心合同、历史检索事实和锁定大纲的摘要检测外部改动，不是科学有效性评分。若外部编辑破坏锁定内容，先恢复已确认合同，再经研究者授权重开；不要改摘要来绕过确认。

真实完成状态为 `complete`；测试为 `fixture_complete`。未选择用 `awaiting_researcher_choice`；未完成建库用 `evidence_incomplete`；重大问题用 `needs_reconfirmation`。完成Round 1–3后下轮只能在新的真实聊天启动。session字符串仅防止明显复用，四个新Python进程不等于四次真实研究会话。同一未完成轮次可用 `start --round <当前轮次> --session <新真实会话>` 恢复；切换下一轮仍须新真实聊天。

需要独立说明的多组科学接口、参数或模型差异妨碍当前规范阅读时，可按当前工作区参数细则按需建立并绑定一份 Parameters.md；显式启用及既有绑定继续有效，禁用或封存不自动恢复。两节为 Scientific interfaces & parameters、Custom algorithms，人口、变量、模型定义及科学理由仍由当前规范及其精确引用拥有。纯综述或写作不因此建立空参数文件，也不获得新分析授权。

## 文件保留与停止选题

- 仍在推进的项目保留完整规范记录及必要凭据；未选A/B/C、暂时中断或更换检索范围不构成删除独立选题资料的依据。
- 研究者明确停止或废弃独立选题时，保留原目录的一份简短 `rra_v6_handoff.md` 及未被明确授权删除的既有变更证据，记录问题／范围、已尝试的工作、停止原因、未完成限制、停止状态及必要的Zotero集合或条目标识；不保留大段JSON元数据、逐篇明细或讨论史，该文件不再作为CLI可恢复的活动状态。
- 清理前核对当前项目记忆、其他推进项目的引用和共享依赖；将仍被使用的必要资料留给其所属项目，仅删除该停止选题独占的详细索引、方案、图谱、检索明细、缓存、临时文件及派生输出，不再另存ZIP或镜像备份；可用时移入回收站。
- 删除范围仅覆盖研究者授权的本地选题资料，保留Zotero条目、附件、笔记和集合；其他项目、共享工具或软件研发资料不随选题停止自动删除。
- 清理完成后原位更新所属项目记忆、链接及保留声明，检查剩余交接可读且活动项目依赖完整；恢复已停止选题须由研究者重新授权，不能因发现最简交接就自动重启。

## Round 1 输入

`question --uncertainty <当前不确定性> [--input <briefs.json>]` 读取可选的证据简报列表。每项为 `{statement,status,uri?}`，status为 `verified|hypothesis|speculation`，事实必须有真实uri。该命令提供一个核心问题支架；Codex根据上下文提出实际科学反问，不依序执行整个问题池。简报覆盖当前轮的有效信息，不累积聊天。

`propose --input <候选.json>` 的输入：

```json
{
  "options": [
    {
      "id": "A",
      "title": "A concise provisional English title",
      "core_question": "A scientific question",
      "research_scope": {"include": "Defined scope", "exclude": "Defined boundary"},
      "contribution": "The intended change in scientific understanding",
      "evidence_risk": "The main evidential uncertainty",
      "closest_review": {"uri": "a verified source location", "relationship": "its actual overlap"},
      "reasoning": {
        "tension": [{"statement": "An unresolved scientific observation", "uri": "Verified evidence location"}],
        "competing_explanations": [
          {
            "explanation": "A bounded explanatory model",
            "evidence_level": "direct",
            "sources": ["Verified source location"],
            "counterevidence": {"statement": "The strongest located counterexample", "uri": "Verified counterevidence location"},
            "discriminating_evidence": "What evidence distinguishes this explanation from its rival"
          },
          {
            "explanation": "A competing model of the same observation",
            "evidence_level": "indirect",
            "sources": ["Verified rival-model source"],
            "counterevidence": {"statement": "The strongest challenge to this rival", "gap": "No decisive counterexample located; state actual search coverage"},
            "discriminating_evidence": "A contrasting prediction or condition that separates the models"
          }
        ],
        "epistemic_gain": "What a reader would understand differently after the nearest review",
        "overlap_assessment": "Which substantive argument is already covered and what remains unresolved",
        "status": "viable"
      }
    }
  ]
}
```

上例只说明单项结构；正式候选比较同时含A/B/C，各重要解释接受最强反证与区分证据检查。解释的 `evidence_level` 为 `direct|indirect|speculation`，`reasoning.status` 为 `viable|tentative|unsupported`；不得将推测或跨文献关联写成已成立机制。未找到反证时用 `counterevidence:{statement:实际已检索内容,gap:尚未找到及覆盖局限}`，不宣称没有反证。假设拆解和时间／多尺度／反事实推理根据问题灵活使用，不增加必填问卷字段。没有找到最近综述时使用 `closest_review:{"gap":"实际检索范围内尚未核实"}`，不得据此声称不存在综述。三方向的科学区别、证据支持和认知增量由Codex阅读和研究者判断，程序只核查结构、出处及明显相同的标题／问题。证据尚不足时允许 `{"options":[],"assessment":"尚未找到足够强的综述问题及其依据","next_search":"下一步要查的证据或竞争解释"}`；保持Round 1探索。不得制造三个虚假成熟题目；tentative／unsupported可展示比较但不能锁定，选定后仅保留选定的 `rqe_summary` 和当前下游检索目标。

`select --choice A --confirmation "研究者实际确认的必要原话"` 完成选择。研究者提出第四/混合方案时用 `select --input <单一完整方案.json> --confirmation ...`；其输入是完整单项对象，先展示整理后的版本再确认。不能由模型生成确认原话，测试除外。

## 检索、筛选与来源表输入

`acquire --input <已取得证据.json>` 是Round 1探索、Round 2正式检索及后续补充的同一入口，接受规范化结构而非原始搜索响应。Round 1尚未选题时 `core_question:null`，`screening_scope` 为当前 `research_domain` 字符串；Round 2起 `core_question` 必须等于当前锁定问题，`screening_scope` 必须等于当前 `research_scope`。以下为字段示例，日期和数值仅作结构说明：

```json
{
  "mode": "live",
  "core_question": "Exactly the selected core question",
  "screening_scope": {"include": "Current approved scope", "exclude": "Current boundary"},
  "screening_rules": [{"id": "E1", "description": "A specific question-dependent exclusion rule"}],
  "searches": [
    {
      "id": "S001",
      "source": "Actual database or real acquisition method",
      "platform": "Actual interface or tool",
      "query": "The exact executed query",
      "date": "2026-10-31T10:00:00+08:00",
      "limits": "Actual date, language, publication type and other filters; explicitly none if none",
      "raw_location": "Actual raw return or export location",
      "status": "executed",
      "purpose": "How this search addresses the selected scientific question",
      "executed": true,
      "hit_count": 12,
      "retrieved_count": 1,
      "record_ids": ["R1"]
    }
  ],
  "records": [
    {
      "id": "R1",
      "title": "Actual returned title",
      "doi": "Actual DOI when present",
      "pmid": "Actual PMID when present",
      "uri": "Actual stable source URL or identifier",
      "source_type": "primary",
      "screening": "include",
      "screening_reason": "Why it answers or informs the question",
      "source_search_ids": ["S001"],
      "categories": ["direct", "core"],
      "materials": [{"kind": "abstract", "location": "Actual accessed source"}],
      "findings": [
        {
          "id": "F1",
          "statement": "The actual reported finding, without stronger inference",
          "locator": "Abstract Results, table/figure/page or source locator",
          "inference": "association",
          "basis": "original",
          "study_design": "Actual design",
          "population": "Actual participants/specimens and sample when known",
          "methods": "Relevant measurement or experimental method",
          "scope": "Conditions under which the finding applies",
          "limitations": "Design/read-depth and inference limitations"
        }
      ]
    }
  ],
  "anchors": [
    {
      "record_id": "R1",
      "role": "scientific",
      "purpose": "Specific scientific use",
      "material": {"kind": "abstract", "location": "Actually accessed source"}
    }
  ]
}
```

示例是字段说明，不是真实文献或有效完成证据；不要将示例值导入实际库。真实 `doi`、`pmid` 缺失时省略，不造占位值。以实际取回且进入候选库的记录为单位保留 `retrieved_count`，这是导入机器候选索引的数量，不代表Zotero写入成功或平台命中数；必须与该回执的 `record_ids` 数量一致。不同检索间重复取回可以重复计为取得，但去重后不重复计为文献/实验。命中量和取回量分开；工具不提供总命中数时设 `hit_count:null` 并给 `hit_count_note`，不得补猜。

文献类型为 `primary|review|methods`，筛选为 `include|exclude|uncertain`，类别是可解释的主题标签而非评分。排除时须有 `screening_stage:title_abstract|full_text`、`exclusion_rule_id` 指向当前 `screening_rules` 的具体规则，并由 `screening_reason` 说明主要原因；每篇只计一个主要排除原因。未筛选用 `screening:null`；已尝试判断但证据不足或未得全文用uncertain及具体理由，不能写成已确认不相关。相关但未映射保留include，不因反证或容量目标排除。结果推断为 `association|causal|descriptive`，结果来源为 `original|synthesis`。综述结果只能是synthesis。未知样本/条件应在相应字段如实说明未取得及阅读层级，不能填猜测值。摘要提取须在limitations中说明范围；Round 2只抽取结构设计所需初步结果，Round 4可更新同一结果，不必预先穷尽全部全文。

可选 `zotero_metadata` 仅携带来源真实提供的Zotero journalArticle字段：`creators,date,publicationTitle,volume,issue,pages,abstractNote`；creators使用真实Zotero作者结构。缺失字段省略，不创建作者、年份或期刊值。已有条目优先复用，不以索引覆写其元数据。首次导入是最小journalArticle原型；其他文献类型通过实际Zotero工具规范化，不能强行冒充期刊文章。

结构Anchor用 `role:"structural"`，额外给 `observations` 对象，必需键为 `title_style,heading_hierarchy,argument_order,evidence_density,macro_local_balance`，值是基于实际资料的简短观察。同文兼任时保留两条不同角色记录。结构分析须实际查看对应全文/层级，不能从摘要猜测；最终主结构Anchor应有full_text资料。

去重依据规范化DOI、PMID及精确稳定uri，不做标题模糊匹配；支持传递性的身份连接。输出保留首条规范ID与 `source_record_ids,source_uris,source_identifiers`，合并非重复资料/结果/类别。首条科学分类被保留；若同一文献的来源分类冲突，Codex须核对原文并统一，不能把顺序当作科学裁决。Anchor来源ID会被改为规范ID。检索回执仍引用原始取得ID，以保留去重依据。每篇统一文献的 `source_search_ids` 保留全部来源；不确定身份由Codex核验题名、作者及年份，不能仅靠同研究／同题名合并不同报告。

完成用 `finish-evidence --assessment "为何足以设计结构及局限"`。充分性由真实证据支持，没有固定篇数门槛。Collection、实际item身份及归属回读成功才可完成；失败时JSON保留实际取得结果，交接仍未完成。修复实际writer后，仅Web原型用 `refresh-library <研究目录>` 同步已保存证据与绑定，再继续 `finish-evidence`；需要更改本轮取得内容时重新acquire。重试先查现库，已成功导入项不重复建立。

### 来源表及统计

`acquire` 为每次新检索绑定当前 `round`（1探索、2正式、3–4补充）；旧Search ID保留原轮次，重新初筛不等于重新执行正式检索。`finish-evidence` 需要至少一次Round 2实际取得记录的正式检索。每次新检索分配新Search ID，即使数据库、平台和检索式相同也追加新执行时间、数量和原始凭据；重复提交同ID只能表示同一次已保存执行，不能篡改其执行事实。筛选和映射统计按当前范围更新。完整检索式保存布尔运算符、字段、主题词、通配符和实际过滤条件；API、手工、引文追溯与Anchor获取保留真实方式和用途。

`rra_v6_search_provenance.md` 仅展示每次检索的ID、轮次、带时区时间、数据库／来源、平台、命中／实际导入／相关／映射数量与状态，以及全局统计、排除规则计数和未完成限制。完整检索式、限制、用途和原始位置按Search ID读取 `rra_v6_evidence.json` 的 `searches`；逐篇身份、筛选、主要排除原因及映射位置读取 `records` 与 `paragraphs`，不再展开成Markdown长表、ID数组或完整查询代码块。计划尚未执行、未知命中或尚未完成筛选／映射用null及状态说明，和实际0区分；未执行不可填写实际确定数量。检索式或原始凭据缺失仍不能声明已核验。

汇总由底层唯一文献、全部来源ID、筛选阶段和主要规则、实际段落映射生成，不将各来源相关／映射数相加。显示实际导入总数、删除重复记录数、去重唯一数、题目／摘要排除数、深入核验排除数、待判断数、相关数、相关未映射数和最终映射数，以及所用去重方法和统计口径。在同一范围且对应阶段已完成时检查：

```text
实际导入数 - 删除重复记录数 = 去重唯一数
去重唯一数 = 题目／摘要排除数 + 深入核验排除数 + 待判断数 + 相关数
相关数 = 相关未映射数 + 最终映射数
```

未同步的源库／筛选范围或尚未映射明确状态，不伪造闭合。逐条追溯通过同一JSON中的统一文献ID、Search ID和筛选状态完成；正文交接只引用摘要及规范JSON，不复制检索历史。

## Round 3 命题与完整组合

`propose` 输入为 `{"claims":[...],"options":[A,B,C]}`。命题最小结构：

```json
{
  "id": "C1",
  "statement": "A bounded scientific proposition",
  "inference": "association",
  "required_study_types": ["The design needed to address this proposition"],
  "evidence": [{"record_id": "R1", "finding_id": "F1", "relation": "support"}]
}
```

关系为 `support|conflict|context|condition`；无可靠证据时用空evidence与明确 `gap`。不得将关联/综述转述标为原始因果支持。每项结果通过研究内 `finding_id` 与规范 `record_id` 定位。

每个方案具备 `id,title,central_thesis,argument_path,anchor_difference,advantages,risks,sections,capacity`。section含 `id,heading,question,claim_ids`，必要时增加 `subsections`，子项具有相同四键。仅支持所需的一二级层次；不用递归图数据库。章节ID在方案内唯一。

`capacity` 为 `{estimated_range:[lo,hi]或null,basis:string,search_ids:[Search ID],dense_sections:[章节ID],direct_evidence_gaps:[章节ID],risks:string,scope_adjustment:string,scientific_cost:string,scope_agreement:string}`。依据必须联系真实检索和已完成筛选，未筛部分写入basis；null表示尚不能估计，不能锁定正式结构。dense_sections和direct_evidence_gaps仅引用当前候选实际章节。

默认目标为50–250篇去重后的最终映射文献，不是候选库／相关库数量或正式纳入阈值。`reference_target:{range:[lo,hi],basis:期刊或既定文章类型的真实依据}` 可覆盖默认。预计范围超出目标时，必须在 `scope_agreement` 解释必要范围协商和科学后果；充分理由可保留更窄／更大综述，不自动删除合格研究、反证或加入无关文献。估计不使用复杂模型、评分或新的数量门。

三个方案分别对应集中主线、完整证据整合、独特解释视角；不能只是重排相同章节或改写标题。程序核查ID和明显重复，科学差异仍需实际评估。选择命令与Round 1相同；自定义/混合方案也必须是完整组合。选定后只保留唯一大纲，删除未选草案，锁定科学范围、标题、论点及结构；`claims_lock` 绑定命题的ID、statement、inference及required_study_types，不提前进入Round 4。

候选可含研究者将确认的 `research_scope`。若与当前范围有实质变化，select先采用该范围、保留全部记录和历史检索，统一重置screening为uncertain并注明范围变化待复核，`screening_scope:null` 表示新范围尚未统一复筛，清除旧映射和派生计划，停留Round 3。随后用同一acquire提交全部既有文献在新 `screening_scope` 下的统一重筛结果，重新propose并按原机制确认正式标题—大纲；不以旧筛选判断支撑新范围。Round 1选题后，已有探索记录同样重置为待重筛并绑定选定核心问题。数量超出目标本身不自动改变范围。

## Round 4 段落与输出

`map --input <段落.json>` 的精确结构：

```json
{
  "paragraphs": [
    {
      "id": "P1",
      "section_id": "S1",
      "claim_ids": ["C1"],
      "claim": "This paragraph's bounded proposition",
      "function": "Evidence comparison",
      "argument_path": "Describe A, compare B, then connect the implication to C",
      "evidence": [{"record_id": "R1", "finding_id": "F1"}],
      "next_relation": "Why the following paragraph is needed"
    }
  ],
  "assets": {
    "primary_anchor": "R2",
    "figures_tables": [],
    "no_figures_tables_intended": true
  }
}
```

`gap,limitations,conflict,next_relation` 按实际需要填写；无证据段必须有gap，不强制每段竞争解释。每个末级章节至少有一个段落或明确的缺口段落，段落只能引用该章节的命题及其结果。父章节可作为子节容器。文献允许映射多段，段内同一结果不重复列出。模型仍须检查重复样本、证据强弱与推断适配，脚本不能语义验证每句命题。

`assets.primary_anchor` 指明主结构Anchor的规范文献ID，`figures_tables` 是拟用且实际存在的图表/示意文件路径。无预期图表须明确声明；若未来需要图表，保留TODO，不把空数组当作已有图表。

Round 4精读可更新同一JSON中的资料、结果与命题证据引用；`map` 会重查引用和推断适配。命题statement、inference或required_study_types变化必须先issue，经研究者确认后reopen上游，不能手改锁定指纹。`mapping_lock` 绑定当前claims、records、paragraphs；任一变化后必须重新map再export。已完成Round 4可在同一批准大纲下重新map，旧导出失效。

`map` 从段落evidence的规范文献ID生成 `capacity_review`：去重total、per_section、relevant_unmapped、reused_references及direct_evidence_gaps、feedback，并重建来源表。跨段多引只计一篇，全局总数不等于章节数或来源数相加。映射前最终数量为未知；映射后实际0与尚未映射不同。相关未映射条目仍是相关文献。范围外显示容量与科学解释提醒，不自动删文；需要删核心章节、改问题或实质调整标题承诺时，按原issue／研究者确认／reopen回Round 3协商。

`export` 生成内部证据映射并完成四轮骨架阶段，同时引用独立来源表。已批准的 HTML 优先提供实际写作编排。下游准备状态单独为 `ready|needs_input|fixture_only`。INITIAL 仍须实际核对写作输入。详见 [内部写作输入合同](writing_input_contract.md)。

重大科学冲突用 `issue --message ...`，保留当前合同并使旧派生写作计划失效。研究者授权后 `reopen --round 1|3 --session <新会话> --confirmation ...` 重开相应选择；保留已验证的证据抽取，清除受影响的大纲/段落/派生输出。Round 3重开仍要求正式证据阶段已完成；更换选题后须重审检索相关性。不要靠手改状态跳阶段。

## Zotero与fixture边界

`scripts/zotero_sync.py` 的 `probe()` 使用新鲜无代理 loopback 请求，可用 `--collection-key` 探测集合响应。其同步类仍是 Web 个人库原型，要求已授权 `ZOTERO_API_KEY` 和正整数 `ZOTERO_USER_ID`。本地MCP/CLI已验证writer和现有集合按 [integration](integration.md#zotero-建库) 沿用，不强制转Web；本地用户0不是Web真实用户ID。回调超时先按真实身份/归属回读，无DOI批量CSL不能依赖if_exists整批重放。不可将其他人的库或未经核实群组替代绑定。

当前实现使用已确认原生 `data.PMID` 读写PMID，不解析猜测的extra别名。新导入保留真实元数据和分类；已有条目只增加专属集合归属，保留原标签、附件和其他集合，不清理历史重复项。Collection重名冲突、部分导入或身份回读失败均标记unavailable，并保留成功回读键供恢复。

`refresh-library <研究目录>` 是显式修复入口：同步已保存证据、修复集合与归属，必要时重建已删除的专属集合；返回实际新绑定，保留选题和大纲，清除mapping_lock及旧写作计划，已有段落须重新map。`start`／完成检查／export只读验证当前绑定，不重建集合或迁移用户库；不要把刷新失败当作科学选择失效。

fixture文献与模拟研究者选择仅存在于测试目录。fixture仅产生 `fixture_item_key:"fixture:<id>"`，不会制造看似真实的Zotero key；无Web调用，输出持续标记fixture。fixture完成不证明服务联调、正式检索、科学结论、真实会话切换或真实人工选择已发生。

## 写作回执

正式文字沿[两阶段调用合同](language_editing.md)执行。在既有 `changes` 简述实际作者与两位编辑的调用、模型和推理强度、底稿引用或哈希、互核与保真状态。未完成项进 `todo`。沿用现有存储字段。获授权的调用或互核未完成时登记实际的 partial 或 blocked。

技能版本为 8.0.0。为保证既有项目续作，沿用 `rra_v6_*` 文件名、`rra_version:6`、`anchor_refine_input` 字段与文件名、`RRA6:<project_id>` 和既有 Zotero 标识。新旧综述使用同一规范记录。新导出的 `next_round:writing` 和旧值 `anchor-refine` 均进入内部 writing 模块。`status:complete` 只说明规划轮次完成。

[POLISH](polishing.md) 复用主方案迭代润色指定段落。聊天交付沿用当前会话。明确要求并完成 Word 写回时，可按既有作用域和记忆规则登记 `EDIT`；`writing-receipt` 的 mode 和数据字段沿用原接口。

若项目已有自己的写作记忆，原位更新它，不另建本节回执。如果 RRA handoff 是唯一记忆，可在实际写作后运行 `writing-receipt <研究目录> --input <临时回执.json>`；这只保存技术／执行回执，不生成正文、不证明科学支持或代替实际 Word/Zotero 操作。临时输入成功后清理。

输入为 `{"mode":"INITIAL或ITERATE或EDIT","run":1,"manuscript":"实际绝对DOCX路径","anchor":"本轮实际Anchor路径或来源","status":"partial或complete或blocked","changes":"重要变更及适用的分节改动估计","citations":"实际证据核验、Collection、动态字段和书目刷新状态","revision":"实际revision.md状态或无重要问题","todo":["必要未完成项"]}`。所有字符串填写实际回执，不用示例当完成证据。局部语言／引文修复用 `EDIT`，没有新锚时 `anchor` 为 `""`，不伪装辅助锚迭代；run 沿用当前写作序号。run 是正整数写作序号，INITIAL 为 1；不与统计 EXP/runid 混用。blocked 可以尚无 DOCX，partial/complete 要有当前实际 DOCX。`complete` 表示本次获授权写作已完成，仍是研究者判断的工作稿；未解决任务必须列明并用 partial/blocked。

仅 live 且 Round 4 当前有效导出后可登记；fixture 不能登记真实写作完成。脚本将当前 `mapping_lock` 存在同一 handoff 的 `writing` 对象中；后续补充、重映射、重导出、issue 或 reopen 使其 `status:stale`，旧 DOCX 保留为现有稿，不自动改写或删除。完成补充证据与必要稿件同步后再登记实际回执。旧项目不需要这项字段才能读取或续作。若无 RRA 状态，使用既有项目记忆和聊天回执，不初始化假四轮。
