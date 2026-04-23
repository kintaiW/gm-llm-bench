from __future__ import annotations
"""C6 评估器：MCP 工具调用序列对比"""
import json
import re


class C6Evaluator:
    def __init__(self, svs_mock_url: str = ""):
        self.svs_mock_url = svs_mock_url

    def evaluate(self, question: dict, response: str) -> tuple[float, dict]:
        expected_seq = question.get("expected_tool_sequence", [])
        alternatives = question.get("acceptable_alternatives", [])
        scoring = question.get("scoring", {})

        # 解析 LLM 输出的工具序列
        predicted_seq = self._parse_tool_sequence(response)

        if not predicted_seq:
            return 0.0, {"error": "未找到工具调用序列", "response": response[:200]}

        # 精确匹配
        if predicted_seq == expected_seq:
            return float(scoring.get("exact_match", 10)), {
                "match": "exact",
                "predicted": predicted_seq,
                "expected": expected_seq,
            }

        # 可接受的替代序列
        for alt in alternatives:
            if predicted_seq == alt:
                return float(scoring.get("acceptable", 8)), {
                    "match": "acceptable_alternative",
                    "predicted": predicted_seq,
                    "expected": expected_seq,
                }

        # 部分匹配：检查覆盖率
        partial_score = self._partial_match_score(predicted_seq, expected_seq)
        if partial_score > 0:
            score = float(scoring.get("partial_sequence", 5)) * partial_score
            return round(score, 1), {
                "match": "partial",
                "coverage": round(partial_score, 2),
                "predicted": predicted_seq,
                "expected": expected_seq,
            }

        return float(scoring.get("wrong_tool", 0)), {
            "match": "none",
            "predicted": predicted_seq,
            "expected": expected_seq,
        }

    def _parse_tool_sequence(self, response: str) -> list[str]:
        """从 LLM 响应中提取工具名称列表"""
        # 尝试解析 JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                tools = parsed.get("tools", [])
                if isinstance(tools, list):
                    return [str(t).strip() for t in tools]
            except (json.JSONDecodeError, AttributeError):
                pass

        # 回退：提取所有已知的 tool 名称
        all_tools = [
            "svs_digest", "svs_sign", "svs_verify", "svs_export_cert",
            "svs_validate_cert", "svs_parse_cert", "svs_envelope_enc", "svs_envelope_dec",
            "sdf_device_info", "sdf_session_manage", "sdf_gen_sm2_keypair", "sdf_sm2_sign",
            "sdf_sm2_verify", "sdf_sm2_crypt", "sdf_sm4_crypt", "sdf_sm4_mac", "sdf_sm3_hash",
            "sdf_key_wrap", "skf_enum_devices", "skf_device_info", "skf_open_application",
            "skf_manage_pin", "skf_list_containers", "skf_gen_ecc_keypair", "skf_import_cert",
            "skf_export_cert", "skf_sm2_sign", "skf_sm2_verify", "skf_sm4_crypt", "skf_sm3_digest",
        ]
        found = []
        for tool in all_tools:
            if tool in response:
                found.append(tool)
        return found

    def _partial_match_score(self, predicted: list[str], expected: list[str]) -> float:
        """计算序列覆盖率（expected 中有多少被预测到）"""
        if not expected:
            return 0.0
        expected_set = set(expected)
        predicted_set = set(predicted)
        overlap = len(predicted_set & expected_set)
        return overlap / len(expected_set)
