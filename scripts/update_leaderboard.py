from __future__ import annotations
#!/usr/bin/env python3
"""从 leaderboard/results/*.json 生成排行榜数据，更新 leaderboard/index.html"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / "leaderboard/results"
INDEX_HTML = ROOT / "leaderboard/index.html"

CATEGORIES = ["C1", "C2", "C3", "C4", "C5", "C6"]


def load_results() -> list[dict]:
    rows = []
    for f in sorted(RESULTS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            row = {
                "model": data["model"],
                "timestamp": data.get("timestamp", ""),
                "total_pct": data.get("total_pct", 0),
                "total_score": data.get("total_score", 0),
                "total_max": data.get("total_max", 0),
            }
            for cat in CATEGORIES:
                info = data.get("categories", {}).get(cat, {})
                row[cat] = info.get("pct", "-")
            rows.append(row)
        except Exception as e:
            print(f"[WARN] 跳过 {f.name}: {e}")
    rows.sort(key=lambda r: r["total_pct"], reverse=True)
    return rows


def render_html(rows: list[dict]) -> str:
    def pct_cell(v) -> str:
        if v == "-":
            return "<td>—</td>"
        color = "#22c55e" if v >= 80 else "#f59e0b" if v >= 60 else "#ef4444"
        return f'<td style="color:{color}">{v}%</td>'

    rows_html = ""
    for i, row in enumerate(rows):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else str(i + 1)
        cat_cells = "".join(pct_cell(row.get(cat, "-")) for cat in CATEGORIES)
        rows_html += f"""
        <tr>
          <td>{medal}</td>
          <td><strong>{row['model']}</strong></td>
          {cat_cells}
          <td><strong>{row['total_pct']}%</strong></td>
          <td style="font-size:0.8em;color:#6b7280">{row['timestamp'][:10]}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GM-Bench Leaderboard</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1rem; }}
    h1 {{ font-size: 2rem; font-weight: 700; text-align: center; margin-bottom: 0.5rem; }}
    .subtitle {{ text-align: center; color: #94a3b8; margin-bottom: 2rem; }}
    table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }}
    thead tr {{ background: #334155; }}
    th, td {{ padding: 12px 16px; text-align: center; border-bottom: 1px solid #334155; }}
    th {{ font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
    td:nth-child(2) {{ text-align: left; }}
    tr:hover {{ background: #243347; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;
              background: #0ea5e9; color: white; margin-left: 4px; }}
    .footer {{ text-align: center; margin-top: 2rem; color: #64748b; font-size: 0.85rem; }}
    .stats {{ display: flex; gap: 1rem; justify-content: center; margin-bottom: 2rem; flex-wrap: wrap; }}
    .stat {{ background: #1e293b; border-radius: 8px; padding: 1rem 1.5rem; text-align: center; }}
    .stat-num {{ font-size: 1.5rem; font-weight: 700; color: #38bdf8; }}
    .stat-label {{ font-size: 0.8rem; color: #94a3b8; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>🔐 GM-Bench Leaderboard</h1>
    <p class="subtitle">The first benchmark for LLMs on China's commercial cryptography compliance (密评)</p>

    <div class="stats">
      <div class="stat"><div class="stat-num">{len(rows)}</div><div class="stat-label">Models Evaluated</div></div>
      <div class="stat"><div class="stat-num">300</div><div class="stat-label">MVP Questions</div></div>
      <div class="stat"><div class="stat-num">C1–C6</div><div class="stat-label">Categories</div></div>
    </div>

    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Model</th>
          <th>C1 条款</th>
          <th>C2 标准</th>
          <th>C3 SKOD</th>
          <th>C4 整改</th>
          <th>C5 代码</th>
          <th>C6 工具</th>
          <th>Total</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        {rows_html if rows_html else '<tr><td colspan="10" style="text-align:center;padding:2rem;color:#64748b">暂无评测结果 — 运行 harness/run_eval.py 开始评测</td></tr>'}
      </tbody>
    </table>

    <div class="footer">
      <p>GM-Bench · Apache-2.0 · <a href="https://github.com/yourusername/gm-llm-bench" style="color:#38bdf8">GitHub</a></p>
      <p style="margin-top:0.5rem">⚠️ For research purposes only. Scores do not constitute official compliance certification.</p>
    </div>
  </div>
</body>
</html>"""


def main():
    rows = load_results()
    html = render_html(rows)
    INDEX_HTML.write_text(html, encoding="utf-8")
    print(f"[update_leaderboard] 已更新 {INDEX_HTML}，共 {len(rows)} 条记录")


if __name__ == "__main__":
    main()
