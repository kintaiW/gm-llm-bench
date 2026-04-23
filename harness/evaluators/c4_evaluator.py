from __future__ import annotations
"""C4 评估器：多选 + 严重程度分级，使用 F1 分数"""
import json
import re


class C4Evaluator:
    def evaluate(self, question: dict, response: str) -> tuple[float, dict]:
        expected_answers = set(question.get("answer", []))
        expected_severity = question.get("severity", {})

        # 解析 LLM 输出的 JSON
        predicted_answers: set[str] = set()
        predicted_severity: dict[str, str] = {}

        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                predicted_answers = set(parsed.get("answers", []))
                predicted_severity = parsed.get("severity", {})
            except (json.JSONDecodeError, AttributeError):
                # 回退：直接提取字母
                letters = re.findall(r'\b([A-D])\b', response)
                predicted_answers = set(letters)

        if not predicted_answers:
            letters = re.findall(r'\b([A-D])\b', response)
            predicted_answers = set(letters)

        # F1 分数（选项准确性）
        tp = len(predicted_answers & expected_answers)
        fp = len(predicted_answers - expected_answers)
        fn = len(expected_answers - predicted_answers)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        # 严重程度匹配（仅对正确选中的选项加分）
        severity_score = 0.0
        severity_count = 0
        for opt in predicted_answers & expected_answers:
            if opt in expected_severity and opt in predicted_severity:
                severity_count += 1
                if predicted_severity[opt] == expected_severity[opt]:
                    severity_score += 1
        severity_pct = severity_score / severity_count if severity_count > 0 else 0.0

        # 综合评分：选项 F1 占 70%，严重程度 30%
        final_score = (f1 * 0.7 + severity_pct * 0.3) * 10.0

        return round(final_score, 2), {
            "f1": round(f1, 3),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "severity_pct": round(severity_pct, 3),
            "predicted": sorted(predicted_answers),
            "expected": sorted(expected_answers),
        }
