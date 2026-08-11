"""
一键生成演示数据：风险规则 + 关联已有风险记录 + 激活预警
运行方式：cd backend && python create_demo_warnings.py
"""
from __future__ import annotations

import hashlib
from datetime import timedelta

from app.core.security import hash_password
from app.infrastructure.db import SessionLocal
from app.models.entities import (
    Contract,
    ContractFile,
    ReviewRecord,
    RiskRecord,
    RiskRule,
    RiskWarning,
    StandardClause,
    User,
    WarningAction,
    utcnow,
)

# ── 12 条标准风险规则 ──────────────────────────────────────────
RULES = [
    {
        "rule_code": "R001",
        "risk_type": "unlimitedLiability",
        "name": "无限责任",
        "risk_level": "high",
        "rule_content": "合同中出现'无限责任'、'全部责任'等无限扩大责任表述",
        "warning_enabled": True,
        "warning_due_hours": 72,
    },
    {
        "rule_code": "R002",
        "risk_type": "excessiveLiquidatedDamages",
        "name": "违约金过高",
        "risk_level": "high",
        "rule_content": "违约金比例超过合同总额30%，可能被法院认定为过高",
        "warning_enabled": True,
        "warning_due_hours": 72,
    },
    {
        "rule_code": "R003",
        "risk_type": "unilateralTermination",
        "name": "单方解除权",
        "risk_level": "high",
        "rule_content": "合同赋予一方随时、任意或无需理由的单方解除权",
        "warning_enabled": True,
        "warning_due_hours": 96,
    },
    {
        "rule_code": "R004",
        "risk_type": "unfairPaymentTerms",
        "name": "不合理付款条件",
        "risk_level": "medium",
        "rule_content": "付款条件苛刻，预付款比例过低或验收后付款周期过长",
        "warning_enabled": True,
        "warning_due_hours": 168,
    },
    {
        "rule_code": "R005",
        "risk_type": "unfavorableJurisdiction",
        "name": "管辖/争议解决不利",
        "risk_level": "medium",
        "rule_content": "争议管辖法院约定在对己方不利的地点",
        "warning_enabled": True,
        "warning_due_hours": 168,
    },
    {
        "rule_code": "R006",
        "risk_type": "missingDisputeResolution",
        "name": "缺失争议解决条款",
        "risk_level": "medium",
        "rule_content": "合同中未约定争议解决方式（诉讼或仲裁）",
        "warning_enabled": True,
        "warning_due_hours": 240,
    },
    {
        "rule_code": "R007",
        "risk_type": "overbroadConfidentiality",
        "name": "保密义务过宽",
        "risk_level": "medium",
        "rule_content": "保密义务期限为永久或无限期，范围过于宽泛",
        "warning_enabled": False,
        "warning_due_hours": None,
    },
    {
        "rule_code": "R008",
        "risk_type": "missingConfidentiality",
        "name": "缺失保密条款",
        "risk_level": "medium",
        "rule_content": "合同中未约定保密义务条款",
        "warning_enabled": True,
        "warning_due_hours": 240,
    },
    {
        "rule_code": "R009",
        "risk_type": "missingPerformanceTerm",
        "name": "缺失履行期限",
        "risk_level": "medium",
        "rule_content": "合同中未约定履行期限",
        "warning_enabled": True,
        "warning_due_hours": 240,
    },
    {
        "rule_code": "R010",
        "risk_type": "ambiguousAcceptance",
        "name": "验收标准不明确",
        "risk_level": "medium",
        "rule_content": "验收标准约定为'另行约定'或'甲方主观验收'",
        "warning_enabled": True,
        "warning_due_hours": 168,
    },
    {
        "rule_code": "R011",
        "risk_type": "intellectualPropertyUnclear",
        "name": "知识产权归属不清",
        "risk_level": "medium",
        "rule_content": "知识产权归属约定不明确，存在'共同所有'等模糊表述",
        "warning_enabled": True,
        "warning_due_hours": 168,
    },
    {
        "rule_code": "R012",
        "risk_type": "forceMajeureMissing",
        "name": "缺失不可抗力条款",
        "risk_level": "low",
        "rule_content": "合同中未约定不可抗力条款",
        "warning_enabled": True,
        "warning_due_hours": 336,
    },
]


def create_rules(db) -> dict[int, dict]:
    """创建风险规则，返回 rule_id → snapshot 映射"""
    snapshots: dict[int, dict] = {}
    for item in RULES:
        existing = db.execute(
            __import__("sqlalchemy").text(
                "SELECT id FROM risk_rule WHERE rule_code = :code"
            ), {"code": item["rule_code"]}
        ).scalar()
        if existing:
            snapshots[existing] = {
                "ruleId": existing,
                "ruleCode": item["rule_code"],
                "riskType": item["risk_type"],
                "name": item["name"],
                "riskLevel": item["risk_level"],
                "ruleContent": item["rule_content"],
                "version": "v0.1",
                "warningEnabled": item["warning_enabled"],
                "warningDueHours": item["warning_due_hours"],
            }
            print(f"  [跳过] 规则 {item['rule_code']} 已存在")
            continue
        rule = RiskRule(
            rule_code=item["rule_code"],
            risk_type=item["risk_type"],
            name=item["name"],
            risk_level=item["risk_level"],
            rule_content=item["rule_content"],
            status="active",
            warning_enabled=item["warning_enabled"],
            warning_due_hours=item["warning_due_hours"],
            version="v0.1",
        )
        db.add(rule)
        db.flush()
        snapshots[rule.id] = {
            "ruleId": rule.id,
            "ruleCode": rule.rule_code,
            "riskType": rule.risk_type,
            "name": rule.name,
            "riskLevel": rule.risk_level,
            "ruleContent": rule.rule_content,
            "version": rule.version,
            "warningEnabled": rule.warning_enabled,
            "warningDueHours": rule.warning_due_hours,
        }
        print(f"  [+] 规则 {rule.rule_code}: {rule.name} (预警={'是' if rule.warning_enabled else '否'})")
    db.commit()
    return snapshots


def link_and_warn(db, snapshots: dict[int, dict]):
    """将已有风险记录关联到规则，并生成预警"""
    from sqlalchemy import select as sa_select
    # 获取所有未关联规则的风险记录
    risk_records = db.scalars(
        sa_select(RiskRecord).where(RiskRecord.rule_id.is_(None))
    ).all()
    print(f"\n发现 {len(risk_records)} 条未关联规则的风险记录")

    risk_type_to_rule: dict[str, int] = {}
    for rule_id, snap in snapshots.items():
        risk_type_to_rule[snap["riskType"]] = rule_id

    created_warnings = 0
    for risk in risk_records:
        # 查找匹配的规则
        rule_id = risk_type_to_rule.get(risk.risk_type)
        if rule_id is None:
            print(f"  [跳过] 风险 #{risk.id} ({risk.risk_type}): 无匹配规则")
            continue
        snapshot = snapshots.get(rule_id)
        if not snapshot or not snapshot.get("warningEnabled"):
            print(f"  [跳过] 风险 #{risk.id} ({risk.risk_type}): 规则未启用预警")
            continue

        # 更新风险记录的 rule_id
        risk.rule_id = rule_id
        risk.rule_snapshot = {
            k: v for k, v in snapshot.items()
            if k in ("ruleId", "ruleCode", "riskType", "name", "riskLevel", "ruleContent", "version")
        }

        # 检查已有预警（幂等）
        review = db.get(ReviewRecord, risk.review_id)
        if review is None:
            continue
        key_source = f"{review.id}:{risk.id}:{snapshot['ruleId']}:{snapshot['version']}"
        warning_key = hashlib.sha256(key_source.encode()).hexdigest()

        existing = db.execute(
            __import__("sqlalchemy").text(
                "SELECT id FROM risk_warning WHERE warning_key = :key"
            ), {"key": warning_key}
        ).scalar()
        if existing:
            print(f"  [跳过] 预警 {warning_key[:8]} 已存在")
            continue

        # 查找合同 owner
        contract = db.get(Contract, review.contract_id)
        owner_id = contract.owner_id if contract else 1

        due_at = utcnow() + timedelta(hours=snapshot["warningDueHours"]) if snapshot.get("warningDueHours") else None

        warning = RiskWarning(
            warning_key=warning_key,
            source_review_id=review.id,
            source_risk_id=risk.id,
            contract_id=review.contract_id,
            owner_id=owner_id,
            warning_type="riskRuleHit",
            warning_level=risk.risk_level,
            warning_status="active",  # ← 直接激活，方便演示
            source_snapshot={
                "rule": snapshot,
                "risk": {
                    "riskId": risk.id,
                    "riskType": risk.risk_type,
                    "riskName": risk.risk_name,
                    "riskLevel": risk.risk_level,
                    "clauseText": risk.clause_text,
                    "page": risk.page,
                    "paragraphIndex": risk.paragraph_index,
                    "basis": risk.basis,
                    "suggestion": risk.suggestion,
                    "confidence": str(risk.confidence) if risk.confidence is not None else None,
                },
            },
            due_at=due_at,
            acknowledged_at=None,
        )
        db.add(warning)
        db.flush()

        # 添加动作记录
        db.add(WarningAction(
            warning_id=warning.id,
            action_type="candidateCreated",
            from_status=None,
            to_status="pendingLegal",
            actor_role="system",
            comment="系统自动生成",
        ))
        db.add(WarningAction(
            warning_id=warning.id,
            action_type="legalConfirmed",
            from_status="pendingLegal",
            to_status="pendingRisk",
            actor_role="legalReviewer",
            comment="演示数据：法务自动确认",
        ))
        db.add(WarningAction(
            warning_id=warning.id,
            action_type="remediationRequired",
            from_status="pendingRisk",
            to_status="active",
            actor_role="riskReviewer",
            comment="演示数据：风控自动激活",
        ))

        created_warnings += 1
        level_cn = {"low": "低", "medium": "中", "high": "高"}.get(risk.risk_level, risk.risk_level)
        print(f"  [+] 预警 #{warning.id}: {snapshot['name']} ({level_cn}风险) → owner={owner_id}, due={due_at}")

    db.commit()
    print(f"\n共创建 {created_warnings} 条预警")


def main():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("A24 演示数据生成：风险规则 + 预警")
        print("=" * 60)
        print("\n[1/2] 创建风险规则...")
        snapshots = create_rules(db)
        print(f"\n[2/2] 关联风险记录并生成预警...")
        link_and_warn(db, snapshots)
        print("\n完成！重启后端后登录 demo_user (密码 123456) 查看预警中心。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
