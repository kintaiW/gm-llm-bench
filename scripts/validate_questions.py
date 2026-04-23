from __future__ import annotations
#!/usr/bin/env python3
"""GM-Bench 题库校验脚本：JSON Schema + 跨题一致性检查"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUESTIONS_DIR = ROOT / "data/questions"
SCHEMAS_DIR = ROOT / "data/schemas"

VALID_TOOLS = {
    "svs_digest", "svs_sign", "svs_verify", "svs_export_cert",
    "svs_validate_cert", "svs_parse_cert", "svs_envelope_enc", "svs_envelope_dec",
    "sdf_device_info", "sdf_session_manage", "sdf_gen_sm2_keypair", "sdf_sm2_sign",
    "sdf_sm2_verify", "sdf_sm2_crypt", "sdf_sm4_crypt", "sdf_sm4_mac", "sdf_sm3_hash",
    "sdf_key_wrap", "skf_enum_devices", "skf_device_info", "skf_open_application",
    "skf_manage_pin", "skf_list_containers", "skf_gen_ecc_keypair", "skf_import_cert",
    "skf_export_cert", "skf_sm2_sign", "skf_sm2_verify", "skf_sm4_crypt", "skf_sm3_digest",
}

CATEGORY_FILES = {
    "C1": "c1_clause_attribution.json",
    "C2": "c2_standard_mapping.json",
    "C3": "c3_skod_scoring.json",
    "C4": "c4_nonconformity.json",
    "C5": "c5_code_rewriting.json",
    "C6": "c6_tool_use.json",
}


def red(msg: str) -> str:
    return f"\033[91m{msg}\033[0m"


def green(msg: str) -> str:
    return f"\033[92m{msg}\033[0m"


def validate_with_schema(data: list, schema: dict, filename: str) -> list[str]:
    """用 jsonschema 校验，返回错误列表"""
    try:
        import jsonschema
        errors = []
        # 兼容 jsonschema 3.x 和 4.x
        validator_cls = getattr(jsonschema, "Draft202012Validator", jsonschema.Draft7Validator)
        validator = validator_cls(schema)
        for err in validator.iter_errors(data):
            path = " → ".join(str(p) for p in err.absolute_path) or "root"
            errors.append(f"  [{filename}] {path}: {err.message}")
        return errors
    except ImportError:
        print("[WARN] jsonschema 未安装，跳过 Schema 校验（pip install jsonschema）")
        return []


def check_c1(questions: list[dict], filename: str) -> list[str]:
    errors = []
    for q in questions:
        opts = set(q.get("options", {}).keys())
        ans = q.get("answer", "")
        if ans and ans not in opts:
            errors.append(f"  [{filename}] {q.get('id')}: answer={ans!r} 不在 options 键集 {opts}")
    return errors


def check_c2(questions: list[dict], filename: str) -> list[str]:
    errors = []
    for q in questions:
        opts = q.get("options", [])
        ans = q.get("answer", "")
        if ans and opts and ans not in opts:
            errors.append(f"  [{filename}] {q.get('id')}: answer={ans!r} 不在 options 列表中")
    return errors


def check_c4(questions: list[dict], filename: str) -> list[str]:
    errors = []
    for q in questions:
        opts = set(q.get("options", {}).keys())
        answers = q.get("answer", [])
        severity = q.get("severity", {})
        for a in answers:
            if a not in opts:
                errors.append(f"  [{filename}] {q.get('id')}: answer 项 {a!r} 不在 options 键集")
        for k in severity:
            if k not in answers:
                errors.append(f"  [{filename}] {q.get('id')}: severity 键 {k!r} 不在 answer 列表中")
    return errors


def check_c6(questions: list[dict], filename: str) -> list[str]:
    errors = []
    for q in questions:
        for tool in q.get("expected_tool_sequence", []):
            if tool not in VALID_TOOLS:
                errors.append(f"  [{filename}] {q.get('id')}: expected_tool_sequence 包含未知工具 {tool!r}")
        for alt in q.get("acceptable_alternatives", []):
            for tool in alt:
                if tool not in VALID_TOOLS:
                    errors.append(f"  [{filename}] {q.get('id')}: acceptable_alternatives 包含未知工具 {tool!r}")
    return errors


def main() -> int:
    all_ids: list[str] = []
    total_errors: list[str] = []
    category_counts: dict[str, int] = {}

    for cat, filename in CATEGORY_FILES.items():
        path = QUESTIONS_DIR / filename
        if not path.exists():
            print(f"[WARN] 题库文件不存在: {path}")
            continue

        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                total_errors.append(f"  [{filename}] JSON 解析失败: {e}")
                continue

        if not isinstance(data, list):
            total_errors.append(f"  [{filename}] 顶层不是数组")
            continue

        schema_path = SCHEMAS_DIR / f"{cat.lower()}.schema.json"
        if schema_path.exists():
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            total_errors.extend(validate_with_schema(data, schema, filename))

        # 收集 ID（跨文件去重用）
        for q in data:
            qid = q.get("id", "")
            if qid:
                all_ids.append(qid)

        # 类别专项校验
        if cat == "C1":
            total_errors.extend(check_c1(data, filename))
        elif cat == "C2":
            total_errors.extend(check_c2(data, filename))
        elif cat == "C4":
            total_errors.extend(check_c4(data, filename))
        elif cat == "C6":
            total_errors.extend(check_c6(data, filename))

        category_counts[cat] = len(data)

    # 全局 ID 去重
    seen: set[str] = set()
    for qid in all_ids:
        if qid in seen:
            total_errors.append(f"  [全局] 重复 ID: {qid!r}")
        seen.add(qid)

    # 输出结果
    total_q = sum(category_counts.values())
    for cat, count in category_counts.items():
        print(f"  {cat}: {count} 题")
    print(f"  合计: {total_q} 题\n")

    if total_errors:
        print(red(f"发现 {len(total_errors)} 个错误："))
        for e in total_errors:
            print(red(e))
        return 1

    print(green(f"所有题库校验通过（共 {total_q} 题）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
