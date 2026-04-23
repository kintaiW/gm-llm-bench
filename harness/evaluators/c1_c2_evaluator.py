from __future__ import annotations
"""C1/C2 评估器：字符串匹配"""
import re


class C1C2Evaluator:
    def evaluate(self, question: dict, response: str) -> tuple[float, dict]:
        answer = question.get("answer", "")
        resp = response.strip()

        # C1：单选题，提取字母
        if question["category"] == "C1":
            match = re.search(r'\b([A-D])\b', resp)
            predicted = match.group(1) if match else resp[:1].upper()
            correct = predicted == answer
            return (10.0 if correct else 0.0), {"predicted": predicted, "expected": answer}

        # C2：标准编号匹配，提取 GM/T 或 GB/T 编号
        match = re.search(r'(G[MB]/T\s*\d{4}(?:-\d{4})?)', resp)
        predicted = match.group(1).replace(" ", "") if match else resp.strip()
        correct = predicted.replace(" ", "") == answer.replace(" ", "")
        return (10.0 if correct else 0.0), {"predicted": predicted, "expected": answer}
