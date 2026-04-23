#!/usr/bin/env bash
# GM-Bench 一键运行所有模型
set -euo pipefail

MODELS=(
  "gpt-4o"
  "gpt-4o-mini"
  "claude-opus-4-7"
  "claude-sonnet-4-6"
  "deepseek-chat"
)

CATEGORIES="${CATEGORIES:-C1,C2,C3,C4}"
SVS_MOCK_URL="${SVS_MOCK_URL:-}"

echo "[GM-Bench] 评测类别: $CATEGORIES"
echo "[GM-Bench] 模型数: ${#MODELS[@]}"
echo ""

for model in "${MODELS[@]}"; do
  echo "================================================"
  echo ">>> 评测模型: $model"
  echo "================================================"
  python harness/run_eval.py \
    --model "$model" \
    --categories "$CATEGORIES" \
    --svs-mock-url "$SVS_MOCK_URL" \
    --sleep 1.0 || echo "[WARN] $model 评测失败，跳过"
  echo ""
done

echo "[GM-Bench] 全部完成，更新排行榜..."
python scripts/update_leaderboard.py
echo "[GM-Bench] Done."
