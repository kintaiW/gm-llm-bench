#!/usr/bin/env python3
"""GM-Bench 主评估入口"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from datetime import datetime
from importlib.metadata import version as _pkg_version, PackageNotFoundError
from pathlib import Path
from typing import Any

try:
    _BENCH_VER = _pkg_version("gm-llm-bench")
except PackageNotFoundError:
    _BENCH_VER = "dev"

ROOT = Path(__file__).parent.parent

# 各类别题库路径
QUESTION_FILES = {
    "C1": ROOT / "data/questions/c1_clause_attribution.json",
    "C2": ROOT / "data/questions/c2_standard_mapping.json",
    "C3": ROOT / "data/questions/c3_skod_scoring.json",
    "C4": ROOT / "data/questions/c4_nonconformity.json",
    "C5": ROOT / "data/questions/c5_code_rewriting.json",
    "C6": ROOT / "data/questions/c6_tool_use.json",
}


def load_questions(categories: list[str]) -> list[dict]:
    questions = []
    for cat in categories:
        path = QUESTION_FILES.get(cat)
        if not path or not path.exists():
            print(f"[WARN] 题库文件不存在: {cat} → {path}", file=sys.stderr)
            continue
        with open(path, encoding="utf-8") as f:
            qs = json.load(f)
        questions.extend(qs)
    return questions


def get_provider(model: str, base_url: str = ""):
    """根据模型名称返回对应的 LLM provider"""
    from harness.providers.openai_provider import OpenAIProvider
    from harness.providers.anthropic_provider import AnthropicProvider
    from harness.providers.deepseek_provider import DeepSeekProvider

    if "gpt" in model or "o1" in model or "o3" in model:
        return OpenAIProvider(model=model, base_url=base_url or "")
    elif "claude" in model:
        return AnthropicProvider(model=model)
    elif "deepseek" in model:
        return DeepSeekProvider(model=model)
    else:
        # 默认尝试 OpenAI 兼容接口（支持 --base-url 透传）
        return OpenAIProvider(model=model, base_url=base_url or "")


def get_evaluator(category: str, svs_mock_url: str = ""):
    """返回对应类别的评估器"""
    from harness.evaluators.c1_c2_evaluator import C1C2Evaluator
    from harness.evaluators.c3_evaluator import C3Evaluator
    from harness.evaluators.c4_evaluator import C4Evaluator
    from harness.evaluators.c5_evaluator import C5Evaluator
    from harness.evaluators.c6_evaluator import C6Evaluator

    evaluators = {
        "C1": C1C2Evaluator(),
        "C2": C1C2Evaluator(),
        "C3": C3Evaluator(),
        "C4": C4Evaluator(),
        "C5": C5Evaluator(svs_mock_url=svs_mock_url),
        "C6": C6Evaluator(svs_mock_url=svs_mock_url),
    }
    return evaluators[category]


def build_prompt(question: dict) -> str:
    """将题目数据构建为 LLM prompt"""
    cat = question["category"]
    if cat == "C1":
        opts = "\n".join(f"{k}. {v}" for k, v in question["options"].items())
        return f"{question['question']}\n\n{opts}\n\n请只回答选项字母（A/B/C/D）。"
    elif cat == "C2":
        opts = "\n".join(f"- {o}" for o in question["options"])
        return f"{question['question']}\n\n候选答案：\n{opts}\n\n请只回答标准编号（如 GM/T 0003-2012）。"
    elif cat == "C3":
        return (
            f"场景：{question['scenario']}\n\n"
            f"{question['question']}\n\n"
            "请严格输出 JSON 格式，如 {\"S\": 3, \"K\": 2, \"O\": 3, \"D\": 2}，不要包含任何其他文字。"
        )
    elif cat == "C4":
        opts = "\n".join(f"{k}. {v}" for k, v in question["options"].items())
        return (
            f"场景：{question['scenario']}\n\n"
            f"{question['question']}\n\n"
            f"{opts}\n\n"
            "请输出 JSON 格式，如 {\"answers\": [\"A\", \"B\"], \"severity\": {\"A\": \"严重\", \"B\": \"一般\"}}。"
        )
    elif cat == "C5":
        return (
            f"任务：{question['description']}\n\n"
            f"现有代码：\n```python\n{question['input_code']}\n```\n\n"
            "请改写上述代码，使用国密算法（SM2/SM3/SM4）替代非国密实现。"
            "只输出改写后的 Python 代码，不要包含解释文字。"
        )
    elif cat == "C6":
        return (
            f"场景：{question['scenario']}\n\n"
            "你有以下 MCP 工具可用：svs_digest, svs_sign, svs_verify, svs_export_cert, "
            "svs_validate_cert, svs_parse_cert, svs_envelope_enc, svs_envelope_dec, "
            "sdf_device_info, sdf_session_manage, sdf_gen_sm2_keypair, sdf_sm2_sign, "
            "sdf_sm2_verify, sdf_sm2_crypt, sdf_sm4_crypt, sdf_sm4_mac, sdf_sm3_hash, "
            "sdf_key_wrap, skf_enum_devices, skf_device_info, skf_open_application, "
            "skf_manage_pin, skf_list_containers, skf_gen_ecc_keypair, skf_import_cert, "
            "skf_export_cert, skf_sm2_sign, skf_sm2_verify, skf_sm4_crypt, skf_sm3_digest。\n\n"
            "请输出完成任务所需的工具调用序列，JSON 格式：{\"tools\": [\"tool1\", \"tool2\", ...]}。"
        )
    return question.get("question", "")


def _write_checkpoint(output_path: Path, summary: dict) -> None:
    """将当前进度写入输出文件"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def _call_with_retry(provider: Any, prompt: str, max_retries: int = 3) -> str:
    """带指数退避的 LLM 调用"""
    last_exc: Exception = RuntimeError("unreachable")
    for attempt in range(max_retries):
        try:
            return provider.complete(prompt)
        except Exception as exc:
            last_exc = exc
            err_str = str(exc).lower()
            # 只对速率限制和网络超时做退避重试
            if any(kw in err_str for kw in ("rate limit", "429", "timeout", "connection")):
                wait = 2 ** attempt * 2  # 2, 4, 8 秒
                print(f" [retry {attempt+1}/{max_retries} in {wait}s]", end="", flush=True)
                time.sleep(wait)
            else:
                raise  # 其他错误直接上抛
    raise last_exc


def run_evaluation(
    model: str,
    categories: list[str],
    output_path: Path,
    svs_mock_url: str = "",
    max_questions: int = 0,
    sleep_between: float = 1.0,
    base_url: str = "",
    resume: bool = True,
) -> dict[str, Any]:
    provider = get_provider(model, base_url=base_url)
    questions = load_questions(categories)

    if max_questions > 0:
        questions = questions[:max_questions]

    # 断点续跑：读取已完成题目
    already_done: dict[str, dict] = {}
    if resume and output_path.exists():
        try:
            prev = json.loads(output_path.read_text(encoding="utf-8"))
            already_done = {r["id"]: r for r in prev.get("results", []) if r.get("score") is not None}
            if already_done:
                print(f"[GM-Bench] 续跑模式：已加载 {len(already_done)} 道已完成题目，将跳过。")
        except Exception:
            pass  # 解析失败则从头开始

    results: list[dict] = list(already_done.values())
    category_scores: dict[str, list[float]] = {c: [] for c in categories}

    # 用已完成题目初始化 category_scores
    for r in already_done.values():
        cat = r.get("category", "")
        if cat in category_scores and r.get("score") is not None:
            category_scores[cat].append(r["score"])

    remaining = [q for q in questions if q["id"] not in already_done]

    print(f"[GM-Bench] v{_BENCH_VER}")
    print(f"[GM-Bench] 模型: {model}，题目数: {len(questions)}（剩余: {len(remaining)}）")
    print(f"[GM-Bench] 类别: {', '.join(categories)}")
    if base_url:
        print(f"[GM-Bench] Base URL: {base_url}")
    print()

    for i, q in enumerate(remaining):
        cat = q["category"]
        evaluator = get_evaluator(cat, svs_mock_url)
        prompt = build_prompt(q)
        done_count = len(already_done) + i + 1
        total_count = len(questions)

        print(f"[{done_count}/{total_count}] {q['id']} ", end="", flush=True)
        t0 = time.time()

        try:
            response = _call_with_retry(provider, prompt)
            elapsed = time.time() - t0
            score, detail = evaluator.evaluate(q, response)
            print(f"→ {score:.1f}分 ({elapsed:.1f}s)")
        except Exception as e:
            elapsed = time.time() - t0
            response = ""
            score = None  # None 表示失败，与 0 分区分（断点续跑时会重试）
            detail = {"error": str(e)}
            print(f"→ ERROR: {e}")

        result_entry = {
            "id": q["id"],
            "category": cat,
            "score": score,
            "response": response[:500],
            "detail": detail,
            "elapsed": round(elapsed, 2),
        }
        results.append(result_entry)
        if score is not None:
            category_scores[cat].append(score)

        # 每 10 题写一次 checkpoint，避免崩溃丢全部进度
        if (i + 1) % 10 == 0:
            _write_checkpoint(output_path, _build_summary(model, questions, results, category_scores, categories))

        if sleep_between > 0:
            time.sleep(sleep_between)

    summary = _build_summary(model, questions, results, category_scores, categories)
    _write_checkpoint(output_path, summary)

    print()
    print("=" * 50)
    print(f"总分: {summary['total_score']}/{summary['total_max']} ({summary['total_pct']}%)")
    for cat, info in summary["categories"].items():
        print(f"  {cat}: {info['score']}/{info['max']} ({info['pct']}%)")
    print(f"结果已保存: {output_path}")
    return summary


def _build_summary(
    model: str,
    questions: list[dict],
    results: list[dict],
    category_scores: dict[str, list[float]],
    categories: list[str],
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "model": model,
        "bench_version": _BENCH_VER,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_questions": len(questions),
        "categories": {},
    }
    total_score = 0.0
    total_max = 0.0
    for cat, scores in category_scores.items():
        if not scores:
            continue
        cat_score = sum(scores)
        cat_max = len(scores) * 10.0
        summary["categories"][cat] = {
            "score": round(cat_score, 1),
            "max": round(cat_max, 1),
            "pct": round(cat_score / cat_max * 100, 1) if cat_max else 0,
            "count": len(scores),
        }
        total_score += cat_score
        total_max += cat_max

    summary["total_score"] = round(total_score, 1)
    summary["total_max"] = round(total_max, 1)
    summary["total_pct"] = round(total_score / total_max * 100, 1) if total_max else 0
    summary["results"] = results
    return summary


def main():
    parser = argparse.ArgumentParser(description="GM-Bench 国密 LLM 评测")
    parser.add_argument("--version", action="version", version=f"gm-bench {_BENCH_VER}")
    parser.add_argument("--model", required=True, help="模型名称，如 gpt-4o / claude-opus-4-7")
    parser.add_argument(
        "--categories",
        default="C1,C2,C3,C4",
        help="评测类别，逗号分隔（默认 C1,C2,C3,C4；C5/C6 需要 Mock 服务）",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="结果输出路径（默认 leaderboard/results/<model>.json）",
    )
    parser.add_argument(
        "--svs-mock-url",
        default=os.getenv("SVS_MOCK_URL", ""),
        help="SVS Mock MCP URL（C5/C6 需要，默认读 SVS_MOCK_URL 环境变量）",
    )
    parser.add_argument("--max-questions", type=int, default=0, help="最多评测题目数（调试用，0=全部）")
    parser.add_argument("--sleep", type=float, default=1.0, help="每题之间休眠秒数（避免限流）")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENAI_BASE_URL", ""),
        help="OpenAI 兼容接口 base URL（如 DashScope/智谱/月之暗面等，默认读 OPENAI_BASE_URL 环境变量）",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="续跑模式：跳过已完成题目（默认开启）",
    )
    args = parser.parse_args()

    cats = [c.strip().upper() for c in args.categories.split(",")]
    output = Path(args.output) if args.output else ROOT / "leaderboard/results" / f"{args.model}.json"

    run_evaluation(
        model=args.model,
        categories=cats,
        output_path=output,
        svs_mock_url=args.svs_mock_url,
        max_questions=args.max_questions,
        sleep_between=args.sleep,
        base_url=args.base_url,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
