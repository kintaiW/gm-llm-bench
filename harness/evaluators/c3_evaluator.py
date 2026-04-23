from __future__ import annotations
"""C3 评估器：SKOD 四维评分，允许容差"""
import json
import re


class C3Evaluator:
    def evaluate(self, question: dict, response: str) -> tuple[float, dict]:
        ref = question.get("reference_scores", {})
        tol = question.get("scoring_tolerance", 2)

        # 提取 JSON
        predicted = {}
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            try:
                predicted = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        if not predicted:
            return 0.0, {"error": "无法解析 JSON", "response": response[:200]}

        dims = ["S", "K", "O", "D"]
        dim_results = {}
        correct_count = 0
        for dim in dims:
            ref_val = ref.get(dim)
            pred_val = predicted.get(dim)
            if ref_val is None or pred_val is None:
                dim_results[dim] = {"expected": ref_val, "predicted": pred_val, "pass": False}
                continue
            passed = abs(int(pred_val) - int(ref_val)) <= tol
            dim_results[dim] = {"expected": ref_val, "predicted": pred_val, "pass": passed}
            if passed:
                correct_count += 1

        score = (correct_count / len(dims)) * 10.0
        return score, {"dims": dim_results, "correct": correct_count}
