from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int


ERRORS = {
    "PARAM_INVALID": ("请求参数不合法", 400),
    "AUTH_LOGIN_FAILED": ("用户名或密码错误", 401),
    "AUTH_TOKEN_MISSING": ("缺少登录凭证", 401),
    "AUTH_TOKEN_INVALID": ("登录凭证无效或已过期", 401),
    "PERMISSION_DENIED": ("无权执行此操作", 403),
    "USER_NOT_FOUND": ("用户不存在", 404),
    "USER_USERNAME_EXISTS": ("用户名已存在", 409),
    "USER_SELF_UPDATE_FORBIDDEN": ("管理员不能降级或禁用自己", 409),
    "CONTRACT_NOT_FOUND": ("合同不存在或无权访问", 404),
    "CONTRACT_FILE_NOT_FOUND": ("合同文件不存在或不属于该合同", 404),
    "CONTRACT_DELETED": ("合同已删除", 409),
    "FILE_TYPE_UNSUPPORTED": ("文件类型不受支持", 400),
    "FILE_TOO_LARGE": ("文件超过大小限制", 413),
    "REVIEW_NOT_FOUND": ("审核任务不存在或无权访问", 404),
    "REVIEW_ALREADY_RUNNING": ("该合同已有进行中的审核", 409),
    "REVIEW_RESULT_NOT_READY": ("AI初审结果尚未就绪", 409),
    "REVIEW_FAILED": ("审核处理失败", 422),
    "REVIEW_ALREADY_CLAIMED": ("审核任务已被其他审核员领取", 409),
    "REVIEW_ROLE_NOT_ALLOWED": ("当前角色不允许执行该审核操作", 403),
    "REVIEW_STAGE_INVALID": ("当前审核阶段不能执行该操作", 409),
    "REVIEW_LEGAL_NOT_COMPLETED": ("法务审核尚未完成", 409),
    "RISK_NOT_FOUND": ("风险记录不存在或无权访问", 404),
    "STANDARD_CLAUSE_NOT_FOUND": ("标准条款不存在", 404),
    "STANDARD_CLAUSE_EXISTS": ("相同合同类型、条款类型和名称的标准条款已存在", 409),
    "RISK_RULE_NOT_FOUND": ("风险规则不存在", 404),
    "RISK_RULE_EXISTS": ("规则代码已存在", 409),
    "CONTRACT_ELEMENT_NOT_FOUND": ("合同要素不存在或不属于该审核", 404),
    "FEEDBACK_INVALID": ("反馈内容或关联对象无效", 400),
    "IDEMPOTENCY_CONFLICT": ("幂等键与已有请求不匹配", 409),
    "AI_SERVICE_UNAVAILABLE": ("AI服务暂不可用", 503),
    "AI_RESPONSE_INVALID": ("AI初审结果无效", 502),
    "LLM_API_FAILED": ("大模型调用失败", 502),
    "FILE_PARSE_FAILED": ("文件无法用于审核", 422),
    "REPORT_FORMAT_UNSUPPORTED": ("报告格式不受支持", 400),
    "REPORT_NOT_FOUND": ("报告不存在或无权访问", 404),
    "REPORT_NOT_READY": ("报告尚未生成完成", 409),
    "REPORT_GENERATION_FAILED": ("报告生成失败", 422),
    "REPORT_FILE_NOT_FOUND": ("报告文件不存在", 404),
    "DATABASE_ERROR": ("数据存储失败", 500),
    "INTERNAL_ERROR": ("服务内部错误", 500),
}


def fail(code: str) -> AppError:
    message, status = ERRORS[code]
    return AppError(code, message, status)
