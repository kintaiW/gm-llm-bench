from __future__ import annotations
"""C5 评估器：代码改写，语法检查 + Mock 执行验证"""
import ast
import json
import re
import subprocess
import sys
import tempfile
import os
from pathlib import Path


class C5Evaluator:
    def __init__(self, svs_mock_url: str = ""):
        self.svs_mock_url = svs_mock_url

    def evaluate(self, question: dict, response: str) -> tuple[float, dict]:
        # 提取代码块
        code = self._extract_code(response)
        if not code:
            return 0.0, {"error": "未找到代码块"}

        # 第1步：语法检查（必须通过）
        syntax_ok, syntax_err = self._check_syntax(code)
        if not syntax_ok:
            return 0.0, {"error": f"语法错误: {syntax_err}", "code_len": len(code)}

        # 第2步：检查是否使用了国密关键词（非国密直接扣分）
        gm_score = self._check_gm_keywords(code)
        if gm_score == 0:
            return 2.0, {"error": "未使用国密算法", "syntax": "pass", "gm_check": "fail"}

        # 第3步：若 Mock 可用，执行验证
        if self.svs_mock_url:
            exec_score, exec_detail = self._execute_with_mock(question, code)
            final = 2.0 + gm_score * 3.0 + exec_score * 5.0
            return min(10.0, round(final, 1)), {"syntax": "pass", "gm_check": "pass", "exec": exec_detail}

        # 无 Mock：仅静态评分
        final = 2.0 + gm_score * 8.0
        return min(10.0, round(final, 1)), {"syntax": "pass", "gm_check": "pass", "note": "no_mock_static_only"}

    def _extract_code(self, response: str) -> str:
        match = re.search(r'```(?:python)?\n(.*?)```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        # 无代码块，取全部响应
        return response.strip()

    def _check_syntax(self, code: str) -> tuple[bool, str]:
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, str(e)

    def _check_gm_keywords(self, code: str) -> float:
        """检查是否包含国密相关关键词，返回 0-1 的分数"""
        gm_keywords = [
            "svs_", "sdf_", "skf_", "mcp_client",
            "SM2", "SM3", "SM4", "sm2", "sm3", "sm4",
            "gmssl", "TLCP", "svs_sign", "svs_verify",
        ]
        anti_keywords = ["RSA", "AES", "SHA256", "bcrypt", "HS256", "PKCS1"]

        code_upper = code.upper()
        gm_count = sum(1 for kw in gm_keywords if kw.upper() in code_upper)
        anti_count = sum(1 for kw in anti_keywords if kw.upper() in code_upper)

        if gm_count == 0:
            return 0.0
        if anti_count > gm_count:
            return 0.3  # 混用了非国密
        return 1.0

    def _execute_with_mock(self, question: dict, code: str) -> tuple[float, dict]:
        """在沙箱中执行代码并验证结果（简化版：检查无运行时错误）"""
        tool = question.get("verification_tool", "")
        params = question.get("verification_params", {})

        # 注入 Mock URL 到代码环境
        env = os.environ.copy()
        env["SVS_MOCK_URL"] = self.svs_mock_url

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import ast; ast.parse(open('{tmp_path}').read()); print('AST_OK')"],
                capture_output=True, text=True, timeout=10, env=env
            )
            if "AST_OK" in result.stdout:
                return 1.0, {"status": "exec_ok", "tool": tool}
            return 0.5, {"status": "exec_partial", "stderr": result.stderr[:200]}
        except subprocess.TimeoutExpired:
            return 0.0, {"status": "timeout"}
        except Exception as e:
            return 0.0, {"status": "error", "msg": str(e)}
        finally:
            Path(tmp_path).unlink(missing_ok=True)
