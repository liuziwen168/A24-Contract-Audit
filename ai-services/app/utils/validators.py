# app/utils/validators.py

import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class ContractValidator:
    """合同数据验证器"""
    
    # 合同类型枚举
    CONTRACT_TYPES = [
        "采购合同", "销售合同", "劳动合同", 
        "保密协议", "服务外包合同", "其他合同"
    ]
    
    RISK_LEVELS = ["高", "中", "低"]
    
    @staticmethod
    def validate_contract_type(contract_type: str) -> str:
        """验证合同类型"""
        if not contract_type:
            return "其他合同"
        
        contract_type = contract_type.strip()
        
        # 如果不在枚举中，返回"其他合同"
        if contract_type not in ContractValidator.CONTRACT_TYPES:
            return "其他合同"
        
        return contract_type
    
    @staticmethod
    def validate_party_name(name: str) -> str:
        """验证合同主体名称"""
        if not name:
            return ""
        
        name = name.strip()
        
        # 移除可能的公司后缀格式问题
        # 例如: "甲方：北京科技" -> "北京科技"
        name = re.sub(r'^(甲方|乙方)[：:]\s*', '', name)
        
        # 长度限制
        if len(name) > 200:
            name = name[:200]
        
        return name
    
    @staticmethod
    def validate_amount(amount: str) -> str:
        """验证合同金额"""
        if not amount:
            return ""
        
        amount = amount.strip()
        
        # 移除金额单位前的空格
        amount = re.sub(r'\s+', '', amount)
        
        # 验证金额格式（数字 + 可选单位）
        # 匹配: 100, 100万, 100万元, 100.5万, 100.50万元
        pattern = r'^[\d,]+(\.\d+)?(万|亿)?(元|人民币)?$'
        if re.match(pattern, amount.replace(',', '')):
            return amount
        
        # 如果包含数字，尝试提取
        number_match = re.search(r'[\d,]+(\.\d+)?', amount)
        if number_match:
            number = number_match.group()
            unit = ''
            # 查找单位
            unit_match = re.search(r'(万|亿|元|人民币)', amount)
            if unit_match:
                unit = unit_match.group()
            return f"{number}{unit}"
        
        return amount
    
    @staticmethod
    def validate_date(date_str: str) -> str:
        """验证日期格式"""
        if not date_str:
            return ""
        
        date_str = date_str.strip()
        
        # 尝试多种日期格式
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%Y.%m.%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                # 统一转换为 YYYY-MM-DD
                if ' ' in date_str:
                    return date_str.split(' ')[0]
                return date_str
            except ValueError:
                continue
        
        # 尝试提取日期
        date_pattern = r'(\d{4})[-/年.](\d{1,2})[-/月.](\d{1,2})'
        match = re.search(date_pattern, date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return date_str
    
    @staticmethod
    def validate_risk_level(level: str) -> str:
        """验证风险等级"""
        if not level:
            return "低"
        
        level = level.strip()
        
        if level in ContractValidator.RISK_LEVELS:
            return level
        
        # 模糊匹配
        if "高" in level:
            return "高"
        elif "中" in level:
            return "中"
        else:
            return "低"
    
    @staticmethod
    def validate_risk_score(score: Any) -> int:
        """验证风险评分"""
        try:
            score = int(score)
            if 0 <= score <= 100:
                return score
            elif score < 0:
                return 0
            else:
                return 100
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def validate_contract_period(period: str) -> str:
        """验证合同期限"""
        if not period:
            return ""
        
        period = period.strip()
        
        # 验证期限格式
        # 支持: 2024-01-01至2024-12-31, 1年, 12个月等
        patterns = [
            r'\d{4}[-/年.]\d{1,2}[-/月.]\d{1,2}\s*[至到]\s*\d{4}[-/年.]\d{1,2}[-/月.]\d{1,2}',
            r'\d+\s*年',
            r'\d+\s*个月?',
            r'长期',
            r'永久',
            r'无固定期限'
        ]
        
        for pattern in patterns:
            if re.search(pattern, period):
                return period
        
        # 如果包含数字，尝试提取
        number_match = re.search(r'\d+', period)
        if number_match:
            number = number_match.group()
            if '年' in period:
                return f"{number}年"
            elif '月' in period:
                return f"{number}个月"
        
        return period
    
    @staticmethod
    def validate_risk_items(risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证风险列表"""
        if not risks:
            return []
        
        validated_risks = []
        
        for risk in risks:
            if not isinstance(risk, dict):
                continue
            
            validated_risk = {
                "type": risk.get("type", risk.get("riskType", "其他风险")),
                "level": ContractValidator.validate_risk_level(
                    risk.get("level", risk.get("riskLevel", "低"))
                ),
                "content": risk.get("content", risk.get("description", "")),
                "basis": risk.get("basis", ""),
                "suggestion": risk.get("suggestion", "")
            }
            
            # 过滤空风险
            if validated_risk["content"] or validated_risk["suggestion"]:
                validated_risks.append(validated_risk)
        
        return validated_risks