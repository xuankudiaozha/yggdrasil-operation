#!/usr/bin/env python3
# SENTINEL: Retains legacy evidence locks, schema 6 and receipt commands while routing the internal evidence map to Yggdrasil writing.
"""Yggdrasil planning and writing-receipt helpers (storage schema 6); scientific generation belongs to Codex."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from zotero_sync import deduplicate, sync_inventory, verify_inventory
import search_provenance as provenance

HANDOFF = "rra_v6_handoff.md"
INVENTORY = "rra_v6_evidence.json"
OUTPUT = "anchor_refine_input.md"
PROVENANCE = provenance.PROVENANCE
QUESTIONS = {
    "phenomenon": "这个领域中，你最希望解释清楚的现象是什么？",
    "explanation": "目前最常见的科学解释中，你认为哪一部分不充分？",
    "mechanism": "你认为已有研究忽略了什么机制、过程或科学联系？",
    "prediction": "如果你的解释成立，还应该能够解释哪些现象？",
    "falsifier": "什么证据可能推翻你的判断？",
    "evidence": "现有直接证据与间接证据分别支持什么？",
    "conflict": "不同研究之间的矛盾是科学分歧，还是研究条件不同？",
    "scope": "哪些相关内容应该排除在这篇综述之外？",
    "contribution": "读者阅读后，应该改变哪一种既有认识？",
    "thread": "最适合组织这些证据的科学主线是什么？",
    "overlap": "最接近的既有综述为什么不能替代我们的工作？",
}

class WorkflowError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise WorkflowError(message)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def write_text(path, text):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)

def write_inventory(project, inventory):
    write_text(Path(project) / INVENTORY, json.dumps(inventory, ensure_ascii=False, indent=2) + "\n")

def save(project, state):
    if state.get("writing") and state["writing"]["status"] != "stale":
        if (state["completed_round"] != 4 or state.get("pending_scientific_change")
                or state["writing"]["mapping_lock"] != state.get("mapping_lock")):
            state["writing"]["status"] = "stale"
    lines = ["# Yggdrasil 当前研究状态（存储格式 6）",
             f"模式：{state['mode']}；已完成 Round {state['completed_round']}；下一阶段：{state['next_round']}。",
             f"研究领域：{state['research_domain']}。"]
    for key, label in (("core_question", "核心问题"), ("central_thesis", "中心论点"),
                       ("working_title", "暂定标题"), ("formal_title", "锁定标题")):
        if state.get(key):
            lines.append(f"{label}：{state[key]}")
    if state.get("pending_scientific_change"):
        lines.append("需研究者重新确认：" + state["pending_scientific_change"])
    if state.get("rqe_summary"):
        lines.append("RQE科学简报：" + json.dumps(state["rqe_summary"], ensure_ascii=False))
    if state.get("search_provenance"):
        lines.append("检索来源与筛选表：" + PROVENANCE)
    if state.get("capacity_review"):
        lines.append("映射容量：" + json.dumps(state["capacity_review"], ensure_ascii=False))
    if state.get("writing"):
        lines.append("当前写作回执：" + json.dumps(state["writing"], ensure_ascii=False))
    lines.append("下一步：" + state.get("next_actions", "读取本轮技能说明。"))
    write_text(Path(project) / HANDOFF,
               "---\n" + json.dumps(state, ensure_ascii=False, indent=2) + "\n---\n\n" +
               "\n\n".join(lines) + "\n")

def load(project):
    path = Path(project) / HANDOFF
    require(path.is_file(), "交接文档不存在；新研究先 init，已有研究请恢复规范交接文件。")
    text = path.read_text(encoding="utf-8-sig")
    require(text.startswith("---\n") and "\n---\n" in text[4:], "交接元数据损坏；不可推断默认状态。")
    state = json.loads(text[4:].split("\n---\n", 1)[0])
    require(state["rra_version"] == 6, "交接存储格式不是 version 6。")
    if state.get("search_lock"):
        inv = load_json(Path(project) / INVENTORY)
        require(state["search_lock"] == digest(inv["searches"]), "历史检索事实被外部改变；恢复原始凭据，重跑须追加新Search ID。")
    if state.get("core_lock"):
        require(state["core_lock"] == digest([state["core_question"], state["research_scope"], state["working_title"]]),
                "核心科学合同已被外部改变；需研究者确认后 reopen。")
    if state.get("selected_outline"):
        inv = load_json(Path(project) / INVENTORY)
        require(state["selected_outline"]["sha256"] == digest(inv["outline"]), "正式大纲已改变；需重新确认。")
        require(state["outline_lock"] == digest([state["formal_title"], state["central_thesis"]]),
                "正式标题或论点已改变；需重新确认。")
        require(state["claims_lock"] == digest(claim_contract(inv["claims"])), "科学命题已改变；恢复已批准内容或经研究者重新确认。")
    return state

def inventory_for(project, state):
    inv = load_json(Path(project) / INVENTORY)
    require(inv["mode"] == state["mode"], "Fixture 与真实模式不能混用。")
    require(inv["core_question"] == state["core_question"], "检索未对应当前核心问题；重新执行或重审检索。")
    return inv

def active(project, number):
    state = load(project)
    require(state["active_round"] == number and state["completed_round"] == number - 1,
            f"阶段不匹配；当前须从 Round {state['next_round']} 的有效入口继续。")
    require(not state.get("pending_scientific_change"), "重大科学问题待重新确认；先呈现研究者并 reopen。")
    return state

def complete(project, state, number):
    state["completed_round"] = number
    state["next_round"] = number + 1 if number < 4 else "writing"
    state["status"] = "fixture_complete" if state["mode"] == "fixture" else "complete"
    state["next_actions"] = (f"在新的真实会话中启动 Round {number + 1}。" if number < 4 else
                             f"获授权后用内部 INITIAL / ITERATE 读取 {OUTPUT}；先处理 Researcher TODO。")
    save(project, state)
    return state

def init(project, project_id, domain, session, mode="live"):
    project = Path(project)
    require(mode in ("live", "fixture") and all((project_id, domain, session)), "研究ID、领域、会话和有效模式均必需。")
    require(not (project / HANDOFF).exists(), "研究交接已存在；使用 status/start，不覆盖。")
    project.mkdir(parents=True, exist_ok=True)
    state = dict(rra_version=6, project_id=project_id, mode=mode, research_domain=domain,
                 active_round=1, completed_round=0, next_round=1, session=session,
                 status="eliciting", title_status="unselected",
                 next_actions="小规模探索后展示可追溯证据，围绕当前不确定性提出一个核心反问。")
    save(project, state)
    return state

def check_anchors(inv):
    for anchor in inv["anchors"]:
        material = anchor["material"]
        require(material["kind"] in ("abstract", "full_text") and material["location"], "Anchor资料缺失。")
        if not urlsplit(material["location"]).scheme or Path(material["location"]).is_absolute():
            require(Path(material["location"]).is_file(), "Anchor资料失效：" + material["location"])

def start(project, round_no, session):
    state = load(project)
    require(round_no in (1, 2, 3, 4), "Round 必须为1–4。")
    same_round = round_no == state["active_round"] and state["completed_round"] == round_no - 1
    require(session, "恢复必须指明当前真实会话。")
    if not same_round:
        require(round_no == state["next_round"] and state["completed_round"] == round_no - 1, "不能跳过未完成阶段。")
        require(session != state["session"], "跨Round必须使用新会话；CLI标签本身不证明真实聊天切换。")
    require(not state.get("pending_scientific_change"), "重大证据问题待研究者重新确认。")
    if round_no >= 3:
        inv = inventory_for(project, state)
        checked = verify_inventory(inv)
        require(checked["zotero_collection"]["status"] in ("verified", "fixture"), "Zotero集合或条目失效；先恢复连接/归属。")
        check_anchors(inv)
    state.update(active_round=round_no, session=session, status="in_progress")
    save(project, state)
    return state

def question(project, uncertainty, briefs=None):
    state = active(project, 1)
    require(uncertainty in QUESTIONS, "选择当前最能推进判断的不确定性，不按问题编号遍历。")
    briefs = briefs or []
    for brief in briefs:
        require(brief["status"] in ("verified", "hypothesis", "speculation"), "区分证据、假说与模型推测。")
        if brief["status"] == "verified":
            require(brief.get("uri"), "事实性结论须提供可追溯出处。")
    state["rqe"] = {"uncertainty": uncertainty, "question": QUESTIONS[uncertainty], "briefs": briefs}
    save(project, state)
    return state["rqe"]

def claim_contract(claims):
    return [{k: claim.get(k) for k in ("id", "statement", "inference", "required_study_types")} for claim in claims]

def finding_index(inv):
    result = {}
    for record in inv["records"]:
        for finding in record.get("findings", []):
            key = (record["id"], finding["id"])
            require(key not in result, "重复的研究内结果ID。")
            result[key] = (record, finding)
    return result

def validate_claims(inv, claims):
    findings = finding_index(inv)
    require(len({c["id"] for c in claims}) == len(claims), "命题ID重复。")
    for claim in claims:
        require(claim["statement"] and claim["inference"] in ("association", "causal", "descriptive"),
                "命题需明确内容及推断类型。")
        require(claim.get("evidence") or claim.get("gap"), "无可靠证据的命题必须标记证据缺口。")
        for ref in claim.get("evidence", []):
            require((ref["record_id"], ref["finding_id"]) in findings, "命题引用了不存在的研究结果。")
            record, finding = findings[(ref["record_id"], ref["finding_id"])]
            require(record["screening"] == "include", "排除或待复核文献不可作为已纳入命题支持。")
            require(ref["relation"] in ("support", "conflict", "context", "condition"), "命题关系无效。")
            if claim["inference"] == "causal" and ref["relation"] == "support":
                require(record["source_type"] == "primary" and finding["inference"] == "causal" and finding["basis"] == "original",
                        "不能将关联或综述性陈述升级为原始因果证据。")

def section_nodes(outline):
    for section in outline["sections"]:
        yield section
        yield from section.get("subsections", [])


def validate_reasoning(option):
    """Require an inspectable scientific brief, never a private reasoning transcript."""
    nearest = option.get("closest_review", {})
    require(nearest.get("uri") or nearest.get("gap"), "最近综述须有可核查出处，或如实说明未核实的范围。")
    reasoning = option.get("reasoning", {})
    require(all(reasoning.get(k) for k in ("tension", "competing_explanations", "epistemic_gain", "overlap_assessment", "status")),
            "候选须给出有来源的认知张力、竞争解释、反证及相对既有综述的认知增量。")
    require(reasoning["status"] in ("viable", "tentative", "unsupported"), "如实标注方向是否已获得证据支持。")
    for tension in reasoning["tension"]:
        require(tension.get("statement") and tension.get("uri"), "认知张力须有可核查来源。")
    explanations = reasoning["competing_explanations"]
    require(len(explanations) >= 2, "比较至少两种合理解释，而不是强化单一假设。")
    for explanation in explanations:
        require(explanation.get("explanation") and explanation.get("evidence_level") in ("direct", "indirect", "speculation"),
                "解释须区分直接证据、间接证据和推测。")
        require(explanation["evidence_level"] == "speculation" or explanation.get("sources"), "有证据的解释须保留出处。")
        counter = explanation.get("counterevidence", {})
        require(counter.get("statement") and (counter.get("uri") or counter.get("gap")) and explanation.get("discriminating_evidence"),
                "每个解释须主动比较最强反证，并说明区分解释的证据或当前缺口。")
    if reasoning["status"] == "viable":
        require(any(e["evidence_level"] != "speculation" for e in explanations), "纯推测不能作为成熟科学问题。")


def capacity_feedback(count, target=(50, 250)):
    if count is None:
        return {"status": "unknown", "target": list(target), "message": "尚未完成映射，不能报告确定容量。"}
    status = "below_target" if count < target[0] else "above_target" if count > target[1] else "within_target"
    messages = {
        "below_target": "核查领域聚焦程度、检索覆盖及直接证据；说明窄范围的科学价值，不为凑数加入文献。",
        "above_target": "核查重复证据、外围主题和标题承诺；说明必要范围及缩减的解释代价，不机械排除研究。",
        "within_target": "容量处于规划区间；仍按科学问题和证据判断范围。",
    }
    return {"status": status, "target": list(target), "message": messages[status]}


def reference_target(inv):
    target = inv.get("reference_target")
    if target is None:
        return [50, 250]
    values = target.get("range", [])
    require(len(values) == 2 and all(type(v) is int and v >= 0 for v in values) and values[0] <= values[1] and target.get("basis"),
            "期刊或文章类型容量目标须提供区间及依据，不能作为纳入排除标准。")
    return values


def validate_capacity(option, inv, selecting=False):
    capacity = option.get("capacity", {})
    require(all(capacity.get(k) for k in ("basis", "search_ids", "risks", "scope_adjustment", "scientific_cost")) and
            all(k in capacity for k in ("estimated_range", "dense_sections", "direct_evidence_gaps", "scope_agreement")),
            "每套论证须说明容量区间、真实检索/初筛依据、密集与缺证章节、范围调整及科学代价。")
    require(set(capacity["search_ids"]) <= {s["id"] for s in inv["searches"] if s["executed"]}, "容量依据必须引用已执行Search ID。")
    nodes = {n["id"] for n in section_nodes(option)}
    require(set(capacity["dense_sections"] + capacity["direct_evidence_gaps"]) <= nodes, "容量说明引用了不存在的章节。")
    estimate = capacity["estimated_range"]
    if estimate is None:
        require(not selecting, "容量尚未知；先完成必要检索/初筛与范围协商，再锁定标题和大纲。")
        return
    require(len(estimate) == 2 and all(type(v) is int and v >= 0 for v in estimate) and estimate[0] <= estimate[1], "容量估计应为诚实区间。")
    target = reference_target(inv)
    if selecting and (estimate[0] < target[0] or estimate[1] > target[1]):
        require(capacity["scope_agreement"], "范围外容量须先说明与研究者达成的科学范围及容量理由。")


def update_provenance(project, inv, state, mapping_complete=False):
    provenance.validate_searches(inv["searches"], inv["records"])
    provenance.validate_screening(inv["records"], inv.get("screening_rules", []))
    scope = state.get("research_scope", state["research_domain"])
    stats = provenance.summary(inv, mapping_complete=mapping_complete)
    write_text(Path(project) / PROVENANCE, provenance.render(inv, scope, mapping_complete=mapping_complete))
    state["search_provenance"] = {"path": PROVENANCE, "status": stats["status"]}
    return stats


def reset_scope(inv):
    """Prior relevance decisions cannot silently stand for a different scientific scope."""
    inv["screening_scope"] = None
    for record in inv["records"]:
        record.update(screening="uncertain", screening_reason="科学范围变化，待按当前统一规则复核。")
        record.pop("screening_stage", None)
        record.pop("exclusion_rule_id", None)
    for key in ("paragraphs", "assets", "options"):
        inv.pop(key, None)


def propose(project, payload):
    state = load(project)
    number = state["active_round"]
    require(number in (1, 3), "仅Round1/3生成候选。")
    active(project, number)
    options = payload["options"]
    if number == 1 and not options:
        require(payload.get("assessment") and payload.get("next_search"), "没有成熟问题时明确证据局限与下一步探索目标。")
        state.pop("options", None)
        state.update(status="eliciting", rqe_summary={"assessment": payload["assessment"], "next_search": payload["next_search"]},
                     next_actions=payload["next_search"])
        save(project, state)
        return []
    require(len(options) == 3 and {o["id"] for o in options} == {"A", "B", "C"}, "需同时提供有科学差异的ABC三方案。")
    require(len({o["title"].strip().casefold() for o in options}) == 3, "三方案不能只是同一标题。")
    if number == 1:
        require(len({o["core_question"].strip().casefold() for o in options}) == 3, "三方向必须有不同的核心科学问题。")
        for option in options:
            validate_reasoning(option)
            require(all(option.get(k) for k in ("title", "core_question", "research_scope", "contribution", "evidence_risk", "closest_review")),
                    "Round1候选缺少科学信息。")
            require(option["closest_review"].get("uri") or option["closest_review"].get("gap"),
                    "最近综述须提供真实来源，未查到须明确未知，不能据此声称新颖。")
        state["options"] = options
    else:
        inv = inventory_for(project, state)
        claims = payload["claims"]
        validate_claims(inv, claims)
        claim_ids = {c["id"] for c in claims}
        paths = set()
        for option in options:
            validate_capacity(option, inv)
            require(all(option.get(k) for k in ("title", "central_thesis", "argument_path", "anchor_difference", "advantages", "risks", "sections")),
                    "Round3必须为标题与完整大纲绑定的组合。")
            nodes = list(section_nodes(option))
            require(len({n["id"] for n in nodes}) == len(nodes), "章节ID重复。")
            for node in nodes:
                require(node["heading"] and node["question"] and node["claim_ids"], "章节须有科学任务和命题映射。")
                require(set(node["claim_ids"]) <= claim_ids, "章节引用了不存在的命题。")
            paths.add((option["central_thesis"].casefold(), option["argument_path"].casefold()))
        require(len(paths) == 3, "不能仅变更章节顺序来制造三个论证方案。")
        inv["claims"], inv["options"] = claims, options
        write_inventory(project, inv)
        state["options_location"] = INVENTORY + "#options"
    state.update(status="awaiting_researcher_choice", next_actions="展示ABC科学差异、推荐及风险，等待研究者明确选择；混合方案先整理再确认。")
    save(project, state)
    return options

def select(project, choice, confirmation):
    state = load(project)
    number = state["active_round"]
    require(number in (1, 3), "当前阶段不需要选题/大纲选择。")
    active(project, number)
    require(confirmation.strip(), "研究者尚未明确选择；不能自动代选。")
    options = state.get("options", []) if number == 1 else inventory_for(project, state).get("options", [])
    if isinstance(choice, dict):
        # A merged or fourth proposal is explicit, not an automatic ABC fallback.
        chosen = copy.deepcopy(choice)
        required = ("title", "core_question", "research_scope", "contribution", "evidence_risk", "closest_review") if number == 1 else (
            "title", "central_thesis", "argument_path", "anchor_difference", "advantages", "risks", "sections")
        require(all(chosen.get(k) for k in required), "自定义/混合方案需先整理为完整单一方案。")
    else:
        chosen = next((o for o in options if o["id"] == choice), None)
        require(chosen is not None, "研究者选择不存在；先提出候选。")
    if number == 1:
        validate_reasoning(chosen)
        require(chosen["reasoning"]["status"] == "viable", "尚未获得支持的方向应继续检索、修订或放弃，不能包装成成熟选题。")
    else:
        validate_capacity(chosen, inventory_for(project, state), selecting=True)
    state["researcher_confirmation"] = confirmation.strip()
    if number == 1:
        state.update(core_question=chosen["core_question"], research_scope=chosen["research_scope"],
                     working_title=chosen["title"], title_status="working")
        state["core_lock"] = digest([state["core_question"], state["research_scope"], state["working_title"]])
        state["rqe_summary"] = copy.deepcopy(chosen["reasoning"])
        state["rqe_summary"]["closest_review"] = copy.deepcopy(chosen["closest_review"])
        state["rqe_summary"]["next_search"] = chosen.get("next_search", chosen["core_question"])
        path = Path(project) / INVENTORY
        if path.exists():
            inv = load_json(path)
            inv["core_question"] = chosen["core_question"]
            reset_scope(inv)
            write_inventory(project, inv)
            update_provenance(project, inv, state)
        state.pop("rqe", None)
        state.pop("options", None)
    else:
        inv = inventory_for(project, state)
        scope = chosen.get("research_scope", state["research_scope"])
        if scope != state["research_scope"]:
            state["research_scope"] = copy.deepcopy(scope)
            state["core_lock"] = digest([state["core_question"], scope, state["working_title"]])
            reset_scope(inv)
            write_inventory(project, inv)
            update_provenance(project, inv, state)
            state.pop("options_location", None)
            state.update(status="evidence_incomplete", next_actions="已确认范围变化；acquire按新范围统一复筛，再propose并确认正式标题—大纲。")
            save(project, state)
            return state
        require(inv.get("screening_scope") == scope, "当前证据尚未按锁定范围复筛。")
        validate_claims(inv, inv["claims"])
        ids = {c["id"] for c in inv["claims"]}
        nodes = list(section_nodes(chosen))
        require(nodes and len({n["id"] for n in nodes}) == len(nodes), "正式大纲章节为空或重复。")
        for node in nodes:
            require(node["heading"] and node["question"] and node["claim_ids"] and set(node["claim_ids"]) <= ids, "混合大纲科学任务或命题引用无效。")
        inv["outline"] = chosen
        inv.pop("options", None)
        write_inventory(project, inv)
        state.update(formal_title=chosen["title"], central_thesis=chosen["central_thesis"], title_status="locked",
                     selected_outline={"path": INVENTORY, "key": "outline", "sha256": digest(chosen)},
                     outline_lock=digest([chosen["title"], chosen["central_thesis"]]),
                     claims_lock=digest(claim_contract(inv["claims"])))
        state.pop("options_location", None)
    return complete(project, state, number)

def acquire(project, inventory):
    state = load(project)
    require(not state.get("pending_scientific_change"), "重大科学问题待研究者重新确认。")
    number = state["active_round"]
    inv = copy.deepcopy(inventory)
    require(inv["mode"] == state["mode"] and inv["core_question"] == state.get("core_question"), "检索模式或核心问题与当前轮不一致。")
    scope = state.get("research_scope", state["research_domain"])
    require(inv.get("screening_scope") == scope, "须明确按当前科学范围提交筛选，旧范围结果不能冒充已复核。")
    old_path = Path(project) / INVENTORY
    previous = load_json(old_path) if old_path.exists() else None
    if previous and previous.get("screening_scope") != scope:
        supplied = {r["id"] for r in inv["records"]}
        require(all(supplied & ({r["id"]} | set(r.get("source_record_ids", []))) for r in previous["records"]),
                "范围变化后须按统一规则复核全部现有记录，不能只提交部分文献以沿用旧判断。")
    saved_searches = {s["id"]: s for s in previous["searches"]} if previous else {}
    for search in inv["searches"]:
        search["round"] = saved_searches[search["id"]]["round"] if search["id"] in saved_searches else number

    require(inv.get("searches") is not None and inv.get("records") is not None, "检索与记录列表必需，真实零结果也应登记。")
    require(len({r["id"] for r in inv["records"]}) == len(inv["records"]), "来源记录ID重复。")
    try:
        inv = provenance.merge_inventory(previous, inv) if previous else inv
        provenance.validate_searches(inv["searches"], inv["records"])
        provenance.validate_screening(inv["records"], inv.get("screening_rules", []))
        reference_target(inv)
    except ValueError as error:
        raise WorkflowError(str(error)) from error
    for record in inv["records"]:
        require(record["title"] and record["uri"] and record["source_type"] in ("primary", "review", "methods"), "文献来源或类型缺失。")
        if state["mode"] == "live":
            require(not record.get("fixture_item_key") and not record["uri"].startswith(("fixture:", "urn:fixture:")), "测试文献不能进入真实研究模式。")
        require(record.get("categories"), "文献须有初步主题分类。")
        for finding in record.get("findings", []):
            require(all(finding.get(k) for k in ("id", "statement", "locator", "study_design", "population", "methods", "scope", "limitations")), "证据抽取缺少定位、设计、对象、方法、范围或推断限制。")
            require(finding["inference"] in ("association", "causal", "descriptive") and finding["basis"] in ("original", "synthesis"), "结果推断或来源类型无效。")
            require(record["source_type"] == "primary" or finding["basis"] == "synthesis", "综述不能伪装为原始实验结果。")
    inv["records"] = deduplicate(inv["records"])
    aliases = {alias: r["id"] for r in inv["records"] for alias in r["source_record_ids"]}
    included_ids = {r["id"] for r in inv["records"] if r.get("screening") == "include"}
    for anchor in inv.get("anchors", []):
        anchor["record_id"] = aliases[anchor["record_id"]]
        require(anchor["record_id"] in included_ids and anchor["role"] in ("scientific", "structural") and anchor["purpose"], "Anchor须经当前范围确认相关并明确角色用途。")
        if anchor["role"] == "structural":
            require(all(anchor["observations"].get(k) for k in ("title_style", "heading_hierarchy", "argument_order", "evidence_density", "macro_local_balance")), "结构Anchor须记录实际结构观察。")
    if state.get("selected_outline"):
        require(digest(inv["outline"]) == state["selected_outline"]["sha256"], "补充检索不能替换锁定大纲；重大变更先issue并由研究者reopen。")
    if number >= 3 and "claims_lock" in state:
        require(digest(claim_contract(inv["claims"])) == state["claims_lock"], "补充引用不能静默改变锁定科学命题。")
    if number >= 2:
        inv = sync_inventory(inv, state["project_id"])
        state.update(zotero_collection=inv["zotero_collection"], selected_anchors=[{"record_id": a["record_id"], "role": a["role"], "purpose": a["purpose"]} for a in inv.get("anchors", [])])
    write_inventory(project, inv)
    state["search_lock"] = digest(inv["searches"])
    stats = update_provenance(project, inv, state)
    state["evidence_inventory"] = {"path": INVENTORY, "records": len(inv["records"]), "retrieved": stats["global"]["imported"]}
    state.pop("mapping_lock", None)
    state.pop("capacity_review", None)
    state.pop("anchor_refine_input", None)
    (Path(project) / OUTPUT).unlink(missing_ok=True)
    if state["completed_round"] == 4:
        state.update(completed_round=3, next_round=4)
    state.update(status="eliciting" if number == 1 else "evidence_incomplete",
                 next_actions="探索记录已保存；继续RQE。" if number == 1 else "检索来源已追加；复核当前范围、Zotero及证据充分性；补充引用后重新map。")
    save(project, state)
    return inv


def finish_evidence(project, assessment):
    state = active(project, 2)
    inv = inventory_for(project, state)
    require(any(s["executed"] and s["retrieved_count"] and s["round"] == 2 for s in inv["searches"]), "尚无实际取得的正式证据检索。")
    checked = verify_inventory(inv)
    require(checked["zotero_collection"]["status"] in ("verified", "fixture"), "Zotero未完成；真实检索结果已保存，恢复后重新 acquire。")
    require(assessment.strip(), "需基于证据判断能否支撑结构设计，不使用固定篇数阈值。")
    require(any(r.get("screening") == "include" and r.get("findings") for r in inv["records"]), "尚无纳入且有可追溯结果的证据。")
    require({"scientific", "structural"} <= {a["role"] for a in inv["anchors"]}, "需分别识别科学与结构Anchor；同一论文可兼任。")
    check_anchors(inv)
    update_provenance(project, inv, state)
    state["evidence_assessment"] = assessment
    return complete(project, state, 2)

def map_paragraphs(project, paragraphs, assets=None):
    state = load(project)
    require(state["active_round"] == 4 and state["completed_round"] in (3, 4) and not state.get("pending_scientific_change"),
            "自然段映射须从已锁定大纲的Round4进入。")
    inv = inventory_for(project, state)
    validate_claims(inv, inv["claims"])
    claims = {c["id"]: c for c in inv["claims"]}
    nodes = {s["id"]: s for s in section_nodes(inv["outline"])}
    # Parents with subsections are containers; each leaf must have a paragraph or an explicit gap paragraph.
    leaves = {s["id"] for s in section_nodes(inv["outline"]) if not s.get("subsections")}
    require(paragraphs and len({p["id"] for p in paragraphs}) == len(paragraphs), "自然段为空或ID重复。")
    finding_lookup = finding_index(inv)
    covered = set()
    for paragraph in paragraphs:
        sid = paragraph["section_id"]
        require(sid in nodes, "自然段引用了正式大纲外章节。")
        require(all(paragraph.get(k) for k in ("claim", "function", "argument_path", "claim_ids")), "自然段需明确命题、科学功能及论证路径。")
        require(set(paragraph["claim_ids"]) <= set(nodes[sid]["claim_ids"]), "自然段命题不属于该正式章节。")
        allowed = {(e["record_id"], e["finding_id"]) for cid in paragraph["claim_ids"] for e in claims[cid].get("evidence", [])}
        refs = paragraph.get("evidence", [])
        require(refs or paragraph.get("gap"), "无可靠证据的段落须明确留下缺口。")
        require(len({(r["record_id"], r["finding_id"]) for r in refs}) == len(refs), "段内重复证据引用。")
        for ref in refs:
            key = (ref["record_id"], ref["finding_id"])
            require(key in finding_lookup and key in allowed, "段落引文不匹配所属科学命题。")
        covered.add(sid)
    require(leaves <= covered, "正式大纲仍有部分未映射；用明确缺口段落保留待补证据任务。")
    inv["paragraphs"], inv["assets"] = paragraphs, assets or {}
    update_provenance(project, inv, state, mapping_complete=True)
    relevant = {r["id"] for r in inv["records"] if r.get("screening") == "include"}
    mapped = {e["record_id"] for p in paragraphs for e in p.get("evidence", [])}
    by_section = {}
    for section in inv["outline"]["sections"]:
        section_ids = {section["id"]} | {child["id"] for child in section.get("subsections", [])}
        by_section[section["id"]] = len({e["record_id"] for p in paragraphs if p["section_id"] in section_ids for e in p.get("evidence", [])})
    uses = {rid: [p["id"] for p in paragraphs if any(e["record_id"] == rid for e in p.get("evidence", []))] for rid in mapped}
    direct = {r["id"] for r in inv["records"] if r["source_type"] == "primary" and "direct" in r.get("categories", [])}
    missing_direct = []
    for paragraph in paragraphs:
        support = {(e["record_id"], e["finding_id"]) for cid in paragraph["claim_ids"] for e in claims[cid].get("evidence", []) if e["relation"] == "support"}
        if not any(e["record_id"] in direct and (e["record_id"], e["finding_id"]) in support for e in paragraph.get("evidence", [])):
            missing_direct.append(paragraph["id"])
    state["capacity_review"] = {"total": len(mapped), "per_section": by_section,
        "relevant_unmapped": len(relevant - mapped), "reused_references": {rid: locations for rid, locations in uses.items() if len(locations) > 1},
        "direct_evidence_gaps": missing_direct,
        "feedback": capacity_feedback(len(mapped), reference_target(inv))}
    write_inventory(project, inv)
    state.update(status="mapped", completed_round=3, next_round=4,
                 mapping_lock=digest([inv["claims"], inv["records"], inv["paragraphs"]]),
                 next_actions="检查段落推断边界、冲突和缺口。用 export 输出内部证据映射。")
    state.pop("anchor_refine_input", None)
    (Path(project) / OUTPUT).unlink(missing_ok=True)
    save(project, state)
    return paragraphs

def export_anchor(project):
    state = active(project, 4)
    inv = inventory_for(project, state)
    require(inv.get("paragraphs"), "尚未建立自然段骨架。")
    require(state.get("mapping_lock") == digest([inv["claims"], inv["records"], inv["paragraphs"]]),
            "映射后的证据或段落已变动；先重新map核查引用，不改变已批准科学命题。")
    update_provenance(project, inv, state, mapping_complete=True)
    checked = verify_inventory(inv)
    require(checked["zotero_collection"]["status"] in ("verified", "fixture"), "Zotero集合或条目不可访问，不能宣称有效下游交接。")
    check_anchors(inv)
    assets = inv.get("assets", {})
    structural = [a for a in inv["anchors"] if a["role"] == "structural" and a["record_id"] == assets.get("primary_anchor")]
    full = [a for a in structural if a["material"]["kind"] == "full_text"]
    todo = []
    if not full:
        todo.append("提供并确认可访问的完整主结构Anchor；摘要不足以执行INITIAL全文结构映射。")
    intended = assets.get("figures_tables", [])
    for asset in intended:
        if not Path(asset).is_file():
            todo.append("补充拟用图表或信息充分的示意材料：" + asset)
    if not intended and not assets.get("no_figures_tables_intended"):
        todo.append("提供拟用图表/示意材料；若本综述无拟用图表，请明确该范围。")
    readiness = "fixture_only" if state["mode"] == "fixture" else ("needs_input" if todo else "ready")
    records = {r["id"]: r for r in inv["records"]}
    findings = finding_index(inv)
    lines = ["# Yggdrasil internal evidence map", "",
             f"Execution mode: {state['mode']}; INITIAL readiness: {readiness}.",
             "This export records the evidence behind the paragraph skeleton. Use the approved HTML for the current manuscript layout when available. Fixture records and choices are for tests only.",
             "", "## Frozen scientific contract", "", f"Title: {state['formal_title']}",
             f"Core question: {state['core_question']}", f"Thesis: {state['central_thesis']}",
             "Scope and exclusions: " + json.dumps(state["research_scope"], ensure_ascii=False),
             "Argument: " + inv["outline"]["argument_path"],
             f"Authority: {HANDOFF}; canonical evidence: {INVENTORY}; search provenance: {PROVENANCE}.",
             "Mapped reference capacity: " + json.dumps(state["capacity_review"], ensure_ascii=False),
             "Register every downstream added citation with acquire in the same evidence index, retain its Search ID/raw receipt, update its mapping, then map/export again.",
             "Approved review findings are scientific fact cards; no statistical models/SIL results are invented.",
             "Abstract and Conclusion remain unchanged or blank unless current or existing project authorization includes them.", "", "## Anchors", ""]
    for anchor in inv["anchors"]:
        lines.append(f"- {anchor['role']}: {anchor['record_id']} — {anchor['purpose']}; {anchor['material']['kind']}: {anchor['material']['location']}")
        if anchor["role"] == "structural":
            lines.append("  Observed structure: " + json.dumps(anchor["observations"], ensure_ascii=False))
    lines += ["", "## Locked outline and paragraph tasks", ""]
    for section in section_nodes(inv["outline"]):
        lines += [f"### {section['id']} {section['heading']}", "", "Scientific task: " + section["question"], ""]
        for paragraph in (p for p in inv["paragraphs"] if p["section_id"] == section["id"]):
            lines += [f"Paragraph {paragraph['id']}", "Claim: " + paragraph["claim"],
                      "Function: " + paragraph["function"], "Argument path: " + paragraph["argument_path"]]
            for ref in paragraph.get("evidence", []):
                record, finding = findings[(ref["record_id"], ref["finding_id"])]
                identity = record.get("zotero_item_key", record.get("fixture_item_key", "UNVERIFIED"))
                lines += [f"- {record['id']} / {finding['id']} / Zotero: {identity}; DOI: {record.get('doi', '')}; source: {record['uri']}",
                          f"  Result ({finding['basis']}, {finding['inference']}): {finding['statement']}; locator: {finding['locator']}",
                          "  Claim relations: " + ", ".join(e["relation"] for cid in paragraph["claim_ids"] for e in next(c for c in inv["claims"] if c["id"] == cid).get("evidence", []) if e["record_id"] == ref["record_id"] and e["finding_id"] == ref["finding_id"]),
                          f"  Design: {finding['study_design']}; population: {finding['population']}; methods: {finding['methods']}",
                          f"  Scope: {finding['scope']}; limitations: {finding['limitations']}",
                          "  Available materials: " + json.dumps(record.get("materials", []), ensure_ascii=False)]
            for field in ("gap", "limitations", "conflict", "next_relation"):
                if paragraph.get(field):
                    lines.append(field + ": " + paragraph[field])
            lines.append("")
    lines += ["## Inference boundaries and Researcher TODO", "",
              "Reviews synthesize primary studies and are not additional independent experiments.",
              "Association does not establish causation; preserve study conditions, sample dependencies and evidence gaps.",
              "Use the internal Yggdrasil INITIAL module and its Word/Zotero contract. Read the approved HTML plan when present and reuse the verified project collection."]
    lines += ["- " + item for item in todo] or ["- No missing local asset declared; verify accessibility in the downstream session."]
    for issue in state.get("unresolved_scientific_issues", []):
        lines.append("- " + issue)
    lines += ["", "Intended assets: " + json.dumps(intended, ensure_ascii=False)]
    write_text(Path(project) / OUTPUT, "\n".join(lines) + "\n")
    if state.get("writing"):
        state["writing"]["status"] = "stale"
    state["anchor_refine_input"] = {"path": OUTPUT, "initial_readiness": readiness, "todo": todo}
    complete(project, state, 4)
    return state["anchor_refine_input"]

def refresh_library(project):
    """Repair only the current dedicated library binding, preserving scientific choices."""
    state = load(project)
    require(state.get("evidence_inventory"), "尚未取得规范证据；先完成Round2 acquire。")
    inv = sync_inventory(inventory_for(project, state), state["project_id"])
    write_inventory(project, inv)
    state["zotero_collection"] = inv["zotero_collection"]
    state.pop("mapping_lock", None)
    state.pop("capacity_review", None)
    update_provenance(project, inv, state)
    state.pop("anchor_refine_input", None)
    (Path(project) / OUTPUT).unlink(missing_ok=True)
    if state["completed_round"] == 4:
        state.update(completed_round=3, next_round=4)
    state["status"] = "library_refreshed" if inv["zotero_collection"]["status"] in ("verified", "fixture") else "service_unavailable"
    state["next_actions"] = "建库恢复情况见zotero_collection；继续当前轮，已有段落须重新map后再export。"
    save(project, state)
    return inv["zotero_collection"]

def issue(project, message):
    state = load(project)
    require(message.strip(), "需明确指出可能推翻主线的证据/科学冲突。")
    state.update(pending_scientific_change=message, status="needs_reconfirmation",
                 next_actions="向研究者呈现重大科学问题；经授权 reopen Round1或Round3，保留已验证抽取结果。")
    state.pop("mapping_lock", None)
    state.pop("capacity_review", None)
    if (Path(project) / INVENTORY).exists():
        update_provenance(project, load_json(Path(project) / INVENTORY), state)
    # A previously exported writing plan must no longer appear current.
    (Path(project) / OUTPUT).unlink(missing_ok=True)
    save(project, state)
    return state

def reopen(project, round_no, session, confirmation):
    state = load(project)
    require(round_no in (1, 3) and confirmation.strip(), "只有研究者授权才重开选题/正式结构。")
    require(session and session != state["session"], "修订轮应在新的真实会话中启动。")
    if round_no == 3:
        require(state.get("evidence_assessment") and state["completed_round"] >= 2, "正式证据阶段尚未完成，不能借reopen跳过。")
    for key in ("selected_outline", "outline_lock", "claims_lock", "mapping_lock", "formal_title", "central_thesis", "anchor_refine_input", "options_location", "options", "capacity_review"):
        state.pop(key, None)
    if round_no == 1:
        for key in ("core_lock", "core_question", "research_scope", "working_title", "evidence_inventory", "selected_anchors", "zotero_collection"):
            state.pop(key, None)
    inv_path = Path(project) / INVENTORY
    if inv_path.exists():
        inv = load_json(inv_path)
        for key in ("outline", "options", "paragraphs", "assets"):
            inv.pop(key, None)
        if round_no == 1:
            inv["core_question"] = None
            reset_scope(inv)
            state.pop("rqe_summary", None)
            state.pop("evidence_assessment", None)
        write_inventory(project, inv)
        update_provenance(project, inv, state)
    state.pop("pending_scientific_change", None)
    state.update(active_round=round_no, completed_round=round_no - 1, next_round=round_no,
                 session=session, researcher_confirmation=confirmation, title_status="unselected" if round_no == 1 else "working",
                 status="in_progress", next_actions="根据已获授权的科学修订生成候选，重新确认单一有效合同。")
    (Path(project) / OUTPUT).unlink(missing_ok=True)
    save(project, state)
    return state


def writing_receipt(project, payload):
    """Store an actual execution receipt; do not certify manuscript or citation content."""
    state = load(project)
    require(state["mode"] == "live", "Fixture 不得登记真实写作回执。")
    require(state["completed_round"] == 4 and not state.get("pending_scientific_change"),
            "先恢复当前有效段落映射及导出；重大科学问题须先解决。")
    inv = inventory_for(project, state)
    require(state.get("mapping_lock") == digest([inv["claims"], inv["records"], inv["paragraphs"]]),
            "映射已变化；先重新 map/export。")
    require(state.get("anchor_refine_input") and (Path(project) / OUTPUT).is_file(), "缺当前内部证据映射。先执行 export。")
    require(payload["mode"] in ("INITIAL", "ITERATE", "EDIT") and payload["status"] in ("partial", "complete", "blocked"),
            "写作模式或实际完成状态无效。")
    require(type(payload["run"]) is int and payload["run"] > 0, "写作 run 必须为正整数。")
    require(payload["mode"] != "INITIAL" or payload["run"] == 1, "INITIAL run 必须为 1。")
    for key in ("manuscript", "changes", "citations", "revision"):
        require(isinstance(payload[key], str) and payload[key].strip(), "回执缺少实际字段：" + key)
    require(isinstance(payload["anchor"], str) and (payload["mode"] == "EDIT" or payload["anchor"].strip()),
            "INITIAL/ITERATE 须给本轮实际 Anchor；无新锚的局部编辑用 EDIT。")
    manuscript = Path(payload["manuscript"])
    require(manuscript.is_absolute() and manuscript.suffix.lower() == ".docx", "须给实际绝对 DOCX 路径。")
    require(payload["status"] == "blocked" or manuscript.is_file(), "当前权威 DOCX 不存在。")
    require(isinstance(payload["todo"], list) and all(isinstance(x, str) and x.strip() for x in payload["todo"]),
            "Researcher TODO 必须为实际未完成项列表。")
    require(payload["status"] != "complete" or not payload["todo"], "仍有未完成任务时用 partial/blocked。")
    receipt = {key: copy.deepcopy(payload[key]) for key in
               ("mode", "run", "manuscript", "anchor", "status", "changes", "citations", "revision", "todo")}
    receipt["mapping_lock"] = state["mapping_lock"]
    state["writing"] = receipt
    state["next_actions"] = ("研究者审阅当前权威稿；按新请求继续。" if receipt["status"] == "complete" else
                             "继续当前写作回执中的 Researcher TODO；保留权威稿和已完成操作。")
    save(project, state)
    return receipt


def main():
    parser = argparse.ArgumentParser(description="Yggdrasil deterministic planning and writing-receipt helpers (storage schema 6)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "start", "question", "propose", "select", "acquire", "finish-evidence", "map", "export", "status", "issue", "reopen", "refresh-library", "writing-receipt"):
        p = sub.add_parser(name)
        p.add_argument("project", type=Path)
        if name == "init":
            p.add_argument("--id", required=True); p.add_argument("--domain", required=True)
            p.add_argument("--mode", choices=("live", "fixture"), default="live")
        if name in ("init", "start", "reopen"):
            p.add_argument("--session", required=True)
        if name in ("start", "reopen"):
            p.add_argument("--round", type=int, required=True)
        if name == "question":
            p.add_argument("--uncertainty", choices=QUESTIONS, required=True)
            p.add_argument("--input", type=Path, help="JSON list of verified/hypothesis/speculation evidence briefs")
        if name in ("propose", "acquire", "map", "writing-receipt"):
            p.add_argument("--input", type=Path, required=True)
        if name == "select":
            g = p.add_mutually_exclusive_group(required=True)
            g.add_argument("--choice"); g.add_argument("--input", type=Path, help="Single complete custom/merged option")
        if name in ("select", "reopen"):
            p.add_argument("--confirmation", required=True)
        if name == "finish-evidence":
            p.add_argument("--assessment", required=True)
        if name == "issue":
            p.add_argument("--message", required=True)
    args = parser.parse_args()
    c, project = args.command, args.project
    if c == "init": result = init(project, args.id, args.domain, args.session, args.mode)
    elif c == "start": result = start(project, args.round, args.session)
    elif c == "question": result = question(project, args.uncertainty, load_json(args.input) if args.input else None)
    elif c == "propose": result = propose(project, load_json(args.input))
    elif c == "select": result = select(project, load_json(args.input) if args.input else args.choice, args.confirmation)
    elif c == "acquire": result = acquire(project, load_json(args.input))
    elif c == "finish-evidence": result = finish_evidence(project, args.assessment)
    elif c == "map":
        payload = load_json(args.input); result = map_paragraphs(project, payload["paragraphs"], payload.get("assets"))
    elif c == "export": result = export_anchor(project)
    elif c == "writing-receipt": result = writing_receipt(project, load_json(args.input))
    elif c == "status": result = load(project)
    elif c == "issue": result = issue(project, args.message)
    elif c == "refresh-library": result = refresh_library(project)
    else: result = reopen(project, args.round, args.session, args.confirmation)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except (WorkflowError, OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit("INCOMPLETE: " + str(exc))
