"""
Contract and Schema Validator for Pluggable Skills.
KISS Principle: Zero external dependencies, pure standard library.
"""
from typing import Dict, Any, List, Tuple


class ContractValidator:
    """
    负责检查插件产物是否符合流水线槽位预期的输出契约。
    若存在缺失字段或格式异常，自动触发默认兜底与补全，确保流程绝不崩溃。
    """

    @staticmethod
    def validate_and_repair(
        slot_id: str,
        output_data: Dict[str, Any],
        expected_fields: List[str],
        default_fallback: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        校验输出数据。若缺失字段，用 fallback 补齐，并返回修复日志。
        """
        repaired_data = dict(output_data)
        warnings = []

        for field in expected_fields:
            if field not in repaired_data or repaired_data[field] is None:
                fallback_val = default_fallback.get(field, f"[自动兜底] 默认 {field}")
                repaired_data[field] = fallback_val
                warnings.append(
                    f"槽位 '{slot_id}' 产物缺少预期字段 '{field}'，已触发自愈兜底补齐。"
                )

        return repaired_data, warnings
