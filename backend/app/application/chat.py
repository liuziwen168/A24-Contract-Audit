from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的合同审核 AI 助手，名字叫 AILEX。"""

# Built-in knowledge base - used as fallback when Qwen is unreachable
KNOWLEDGE: dict[str, str] = {
    "违约金": "关于违约金条款，根据《民法典》第585条：\n\n当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金，也可以约定因违约产生的损失赔偿额的计算方法。\n\n**关键注意事项**：\n- 违约金不应超过实际损失的30%，过高的违约金法院可能不予支持\n- 建议明确约定违约情形、计算方式和支付期限\n- 同时约定\"违约金不足以弥补损失的，守约方仍可主张赔偿\"",

    "无限责任": "无限责任条款是合同审核中需要高度警惕的高风险条款。\n\n**风险分析**：\n- 无限责任意味着责任方需承担全部损失，没有赔偿上限\n- 可能导致企业面临远超合同金额的赔偿风险\n- 尤其在与大型企业签订合同时需特别注意\n\n**修改建议**：\n1. 设定责任上限，通常以合同金额的1-3倍为宜\n2. 明确排除间接损失、利润损失等\n3. 约定免责情形（不可抗力、对方过错等）",

    "保密": "保密协议（NDA）核心条款：\n\n**必备条款**：\n1. 保密信息定义 —— 明确哪些信息属于保密范围\n2. 保密义务 —— 接收方的保密责任和使用限制\n3. 保密期限 —— 通常为合同期内+终止后2-5年\n4. 例外情形 —— 已公开信息、依法披露等不视为违约\n5. 违约责任 —— 明确泄密的法律后果",

    "采购": "规范采购合同应包含以下核心条款：\n\n1. 合同主体 —— 双方准确名称、地址、联系方式\n2. 标的物描述 —— 产品名称、规格、型号、数量、质量标准\n3. 价款与支付 —— 单价、总价、币种、付款方式与期限\n4. 交付与验收 —— 交货时间、地点、运输方式、验收标准\n5. 质保与售后 —— 质保期限、售后服务内容\n6. 违约责任 —— 延迟交货、质量不合格等违约处理\n7. 争议解决 —— 协商、仲裁或诉讼的管辖约定",

    "争议解决": "争议解决条款影响维权成本和效率：\n\n**常见方式**：\n- 协商 —— 成本最低，但执行力弱\n- 仲裁 —— 一裁终局、保密性好，适合商事纠纷\n- 诉讼 —— 程序公开、可上诉，适合复杂案件\n\n**注意事项**：\n- 管辖地约定在对方所在地会大幅增加维权成本\n- 建议争取约定在己方所在地或合同履行地\n- 仲裁机构应明确全称，避免约定不明",

    "竞业限制": "竞业限制条款受法律严格限制：\n\n**法律要求（劳动合同法第23-24条）**：\n- 仅适用于高管、高级技术人员和负有保密义务的人员\n- 期限不得超过2年\n- 必须支付经济补偿，标准不低于离职前12个月平均工资的30%\n- 范围应合理限定\n\n**风险提示**：\n- 未支付补偿金的竞业限制条款可能被认定无效\n- 范围过宽可能被法院调整",

    "不可抗力": "不可抗力条款在合同中有重要作用：\n\n**法律依据（民法典第180条、第590条）**：\n- 不可抗力指不能预见、不能避免且不能克服的客观情况\n- 因不可抗力不能履行民事义务的，不承担民事责任\n\n**建议约定内容**：\n1. 明确列举不可抗力情形（自然灾害、战争、政府行为等）\n2. 约定通知义务和时限\n3. 约定不可抗力持续期间的合同处理方式\n4. 明确不可抗力结束后双方的权利义务恢复方式",

    "知识产权": "知识产权归属条款在服务外包和技术合同中尤为重要：\n\n**关键约定**：\n- 明确委托开发成果的知识产权归属（甲方/乙方/共有）\n- 区分背景知识产权和前景知识产权\n- 约定知识产权使用范围和许可方式\n- 明确侵权责任承担\n\n**常见风险**：\n- 知识产权归属约定不明导致后续纠纷\n- 未约定第三方知识产权侵权责任\n- 缺乏对开源软件使用的限制条款",

    "验收标准": "验收标准条款应确保客观可衡量：\n\n**建议约定**：\n1. 明确验收依据（国家标准、行业标准或双方确认的技术规格书）\n2. 约定验收程序和期限\n3. 约定验收不合格的处理方式（整改期限、违约责任）\n4. 明确视为验收合格的情形（如对方无正当理由拖延验收）\n\n**常见问题**：\n- 标准过于模糊（如\"符合甲方要求\"）\n- 验收期限不合理\n- 缺少第三方检测机制",

    "合同金额": "合同金额大小写不一致时，根据《民法典》及司法实践：\n\n**处理原则**：\n- 大写金额和小写金额不一致的，以大写金额为准\n- 这是基于\"大写金额不易篡改、更为慎重\"的立法精神\n\n**建议做法**：\n1. 签订前仔细核对大小写一致性\n2. 发现不一致立即修正，并要求双方在修改处签章\n3. 建议在合同中增加\"合同金额以大写为准\"的条款\n4. 电子合同中建议设置金额自动校验功能",

    "单方解除": "单方解除权条款需谨慎对待：\n\n**高风险识别**：\n- 赋予对方单方任意解除权（无需理由即可解除）\n- 解除通知期限过短\n- 解除后不承担任何责任\n\n**修改建议**：\n1. 限定解除条件（对方违约、不可抗力等特定情形）\n2. 约定合理的通知期限（通常15-30天）\n3. 明确解除后的清算和返还义务\n4. 约定单方解除的违约责任",
}

DEFAULT_REPLY = "这是一个很好的合同相关问题。\n\n根据《中华人民共和国民法典》及相关司法实践，建议在合同审核中重点关注：\n\n1. **条款合法性**：确保条款不违反法律强制性规定\n2. **权利义务对等性**：检查双方权利义务是否基本均衡\n3. **风险可控性**：评估条款可能带来的商业风险\n4. **表述明确性**：避免模糊、歧义的用语\n\n如需详细分析具体合同条款，建议上传合同后使用本系统的 AI 审核功能，系统会自动识别风险条款并给出修改建议。"


def _local_answer(message: str) -> str:
    """Keyword-based local answer when Qwen is unavailable."""
    for keyword, answer in KNOWLEDGE.items():
        if keyword in message:
            return answer
    return DEFAULT_REPLY


async def _try_qwen(payload: dict) -> Optional[str]:
    """Try calling Qwen API directly. Returns None if unreachable."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(65, connect=5)) as client:
            response = await client.post(
                f"{settings.qwen_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.qwen_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if response.status_code != 200:
                return None
            data = response.json()
            choice = (data.get("choices") or [{}])[0]
            content = (choice.get("message") or {}).get("content", "")
            return content.strip() if content else None
    except Exception:
        return None


async def chat(message: str, history: Optional[list[dict[str, str]]] = None) -> str:
    # Try Qwen first
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": message})

    payload = {
        "model": settings.qwen_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800,
    }

    qwen_reply = await _try_qwen(payload)
    if qwen_reply:
        return qwen_reply

    # Fallback to local knowledge base
    return _local_answer(message)