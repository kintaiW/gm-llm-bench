# GM-Bench：国密 LLM 能力评测基准

> **全球首个面向中国商用密码合规（密评）的大模型评测集**

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Questions](https://img.shields.io/badge/questions-176%20MVP-blue.svg)](data/questions/)
[![Categories](https://img.shields.io/badge/categories-C1--C6-orange.svg)](data/questions/)
[![Part of](https://img.shields.io/badge/part%20of-gm--agent--stack-purple.svg)](https://github.com/kintaiW/gm-agent-stack)

---

## 这是什么？为什么需要它？

### 背景：50,000+ 系统的密评困境

中国《密码法》和 GB/T 39786-2021 标准要求，所有等保三级及以上信息系统必须通过**商用密码应用安全性评估（密评）**。这意味着：

- 系统中的身份认证必须使用 SM2 数字证书，而非 RSA
- 数据传输必须使用 TLCP 协议，而非普通 HTTPS/TLS
- 数据加密必须使用 SM4，而非 AES
- 哈希算法必须使用 SM3，而非 SHA-256
- 密钥必须由经认证的 HSM/UKey 管理，而非软件存储

**问题在于：** 当开发者或甲方向 GPT-4、Claude、DeepSeek 等大模型咨询"如何整改密评不符合项"时，这些 AI 能回答得多准确、多专业？

GM-Bench 就是为了量化回答这个问题而生的。

### GM-Bench 的作用

```
你问 AI："我的系统用了 RSA-2048 做身份认证，密评不通过，怎么改？"

AI A 回答："换成 SM2 就好了。"                      ← 太模糊
AI B 回答："参考 GM/T 0003-2012 更换 SM2 算法..."   ← 标准号正确
AI C 生成了可以跑通的 SM2 迁移代码，并用 Mock 验证  ← GM-Bench C5 最高分
```

**GM-Bench 不只是选择题集，它衡量 AI 在国密领域从"知道"到"能做"的完整能力链。**

---

## 评测维度

GM-Bench 分六个类别，覆盖国密知识的完整认知层次：

| 类别 | 名称 | 题数 | 题型 | 评分方式 | 核心考察 |
|------|------|------|------|----------|----------|
| **C1** | 条款归属 | 60 题 | 单选 | 字符串匹配 | 能否将密评要求归属到正确标准条款 |
| **C2** | 标准映射 | 40 题 | 匹配 | 字符串匹配 | 能否把设备/协议/算法对应到正确 GM/T 编号 |
| **C3** | SKOD 评分 | 50 题 | 数值 JSON | 绝对误差 ≤2 | 能否对实际系统做出合理的四维密评打分 |
| **C4** | 不符合项分级 | 40 题 | 多选 + 严重程度 | F1 分数 | 能否识别不符合项并判断严重/一般/轻微 |
| **C5** | 代码改写 | 30 题 | 代码生成 | **实际运行验证** | 能否生成可跑通的国密迁移代码 |
| **C6** | 工具调用 | 80 题 | MCP 调用序列 | 序列对比 | 能否选择正确的 MCP 工具序列完成任务 |

### 关键差异化：C5 和 C6 是可执行验证的

大多数 LLM 评测靠"人工打分"或"GPT-4 评分"——这在国密领域尤其不可靠，因为 GPT-4 自己也不一定懂。

**GM-Bench 的 C5 和 C6 用代码说话：**
- C5 的改写代码会被实际执行，对接 SVS/SDF/SKF Mock 设备，验证签名/加密/摘要能否真正跑通
- C6 的工具调用序列会与参考答案做 trace diff，不允许冗余调用

---

## 评测内容详解

### C1 — 条款归属（60 题）

考察 AI 能否将一个密评场景/需求，准确归属到 GB/T 39786-2021 中对应的安全层和条款。

**示例题目：**
```
Q: 在密评中，以下哪种情况属于"不符合项"（即直接判定不合格）？

A. 系统使用 SM2-256 但密钥长度文档描述有误
B. 系统仍在使用 RSA-1024 进行用户身份认证   ← 正确答案
C. 数字证书格式使用 X.509 v3
D. SM4 使用 CBC 模式但 IV 为固定���（已知问题已记录）

参考条款：GB/T 39786-2021 附录 A
```

**评分：** AI 回答 "B" 得 10 分，其余 0 分。

---

### C2 — 标准映射（40 题）

考察 AI 能否把"要做什么"映射到"应遵循哪个 GM/T 标准"。

**示例题目：**
```
Q: 智能密码钥匙（USB Key）密码应用接口规范对应哪个 GM/T 标准？

候选答案：GM/T 0016-2012 / GM/T 0018-2023 / GM/T 0029-2014 / GM/T 0024-2014

正确答案：GM/T 0016-2012
干扰项说明：0018=服务器密码机，0029=签名验签服务器，0024=SSL VPN
```

**标准映射速查表（评测覆盖范围）：**

| 设备/协议/算法 | 对应标准 |
|----------------|----------|
| SM2 椭圆曲线算法 | GM/T 0003-2012 |
| SM3 哈希算法 | GM/T 0004-2012 |
| SM4 分组密码 | GM/T 0002-2012 |
| USB Key / UKey | GM/T 0016-2012 |
| 服务器密码机 / HSM | GM/T 0018-2023 |
| 签名验签服务器 / SVS | GM/T 0029-2014 |
| TLCP（国密 TLS） | GB/T 38636-2020 |
| 密评基本要求 | GB/T 39786-2021 |
| SM2 数字证书格式 | GM/T 0015-2012 |
| 数字信封规范 | GM/T 0010-2012 |

---

### C3 — SKOD 评分（50 题）

考察 AI 能否对一个实际系统的密码应用现状，做出合理的 SKOD 四维评分（各维 0-5 分）。

**SKOD 四维含义：**

| 维度 | 含义 | 评分要点 |
|------|------|----------|
| **S** — 完备性 | 密码应用覆盖是否完整 | 身份认证/传输/存储/日志是否全覆盖 |
| **K** — 正确性 | 算法/密钥使用是否合规 | 是否使用国密算法、正确工作模式 |
| **O** — 有效性 | 密码保护是否真实有效 | 加密是否保护了真正敏感的数据 |
| **D** — 合规性 | 与标准要求的符合程度 | 是否满足等保对应级别的密评要求 |

**示例场景（C3-001）：**
```
场景：某电商平台（等保三级系统）
- 用户登录：用户名+密码，无数字证书
- 数据传输：HTTP 明文，部分 HTTPS（RSA 证书）
- 数据存储：密码 MD5 存储，支付信息 AES-128 加密
- 密钥管理：AES 密钥硬编码在配置文件
- 密码设备：无

参考评分：{"S": 1, "K": 0, "O": 1, "D": 0}
容差：±2
说明：S=1（均未采用国密），K=0（RSA/MD5/AES 均非国密），
      O=1（保护极度不完整），D=0（完全不符合密评要求）
```

**评分规则：** 四个维度各自判断，偏差 ≤2 得该维度满分，偏差 >2 得 0 分，汇总后折算总分。

---

### C4 — 不符合项分级（40 题）

考察 AI 能否从一个场景描述中，准确选出所有不符合项，并正确判断每项的严重程度。

**严重程度定义：**
- **严重**：直接导致密评不合格，必须整改才能通过
- **一般**：影响评分，建议整改
- **轻微**：最佳实践建议，不直接影响通过

**示例题目（C4-003）：**
```
场景：数据库字段加密使用 SM4-ECB 模式，密钥硬编码在应用配置文件中，无密钥轮换机制。

A. SM4-ECB 模式不提供语义安全（相同明文→相同密文）   → 严重
B. 密钥硬编码在配置文件中                              → 严重
C. 无密钥轮换机制                                      → 一般
D. SM4 算法本身不合规                                  → ❌ 干扰项（SM4 合规，问题在用法）

正确答案：A（严重）、B（严重）、C（一般）
```

**评分：** F1 分数评选项准确性（70%）+ 严重程度匹配率（30%）。

---

### C5 — 代码改写（30 题）

给一段使用非国密算法的代码，让 AI 改写为国密版本，并实际执行验证。

**改写场景覆盖：**

| 改写方向 | 示例 |
|----------|------|
| RSA 签名 → SM2 签名 | `private_key.sign()` → `svs_sign()` |
| AES 加密 → SM4 加密 | `AES.new(CBC)` → `sdf_sm4_crypt(CBC)` |
| SHA256 摘要 → SM3 摘要 | `hashlib.sha256()` → `svs_digest()` |
| JWT HS256 → SM2 签名令牌 | `jwt.encode(HS256)` → `svs_sign(SM2)` |
| PKCS#12 密钥库 → UKey SKF | `pkcs12.load_key_and_certificates()` → `skf_open_application()` |
| GPG 信封 → SM2+SM4 数字信封 | `gpg.encrypt()` → `svs_envelope_enc()` |
| AES-ECB 数据库字段加密 → SM4-CBC+HSM密钥 | 移除硬编码 + 换算法 + 密钥托管 |

**评分机制（无 Mock 时）：**
1. 语法检查通过：+2 分
2. 包含国密关键词（svs_/sdf_/skf_/SM2/SM3/SM4）：+8 分
3. **有 Mock 时额外验证**：代码实际运行对接 SVS Mock，+5 分

**示例输入代码：**
```python
# 问题代码：RSA+SHA256 签名
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

def sign_data(private_key, data: bytes) -> bytes:
    return private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())
```

**期望改写输出：**
```python
from ccasa.llm.mcp_client import svs_sign_and_verify

def sign_data(data: bytes) -> dict:
    result = svs_sign_and_verify(data.hex())
    return result  # 包含 signature_hex 和 verified 字段
```

---

### C6 — 工具调用（80 题）

给一个密评场景，让 AI 选择正确的 MCP 工具调用序列。覆盖 gm-agent-stack 中 SVS/SDF/SKF 三类设备的 28 个工具。

**可用工具列表：**

| 设备 | 工具 | 功能 |
|------|------|------|
| SVS 签名验签服务器 | `svs_digest` | SM3 摘要 |
| | `svs_sign` | SM2 签名（SignData/SignMessage） |
| | `svs_verify` | SM2 验签 |
| | `svs_export_cert` | 导出证书 |
| | `svs_validate_cert` | 验证证书有效性（含 CRL/OCSP） |
| | `svs_parse_cert` | 解析证书字段 |
| | `svs_envelope_enc` | 数字信封加密 |
| | `svs_envelope_dec` | 数字信封解密 |
| SDF 服务器密码机 | `sdf_device_info` | 设备信息 + 随机数 |
| | `sdf_sm2_sign/verify/crypt` | SM2 签名/验签/加解密 |
| | `sdf_sm4_crypt` | SM4 加解密（CBC/GCM/CTR 等） |
| | `sdf_sm3_hash` | SM3/HMAC |
| | `sdf_key_wrap` | 密钥包装/导入/导出 |
| SKF USB Key | `skf_enum_devices` | 枚举设备 |
| | `skf_open_application` | 打开应用+PIN 验证 |
| | `skf_sm2_sign/verify` | SM2 签名/验签 |
| | `skf_sm4_crypt` | SM4 加解密 |
| | `skf_gen_ecc_keypair` | 生成/导入密钥对 |
| | `skf_import/export_cert` | 证书导入/导出 |

**示例题目：**
```
场景：实现数字信封：用接收方证书加密重要数据，然后解密验证

期望调用序列：["svs_envelope_enc", "svs_envelope_dec"]
可接受替代：  ["sdf_sm2_crypt", "sdf_sm4_crypt", "sdf_sm2_crypt"]  # 手动拼装信封
```

---

## 快速开始

### 环境要求

```
Python ≥ 3.11
```

> ⚠️ 开发机 Python 版本低于 3.11 时，harness 代码需要安装 Python 3.11+。
> C5/C6 需要额外运行 gm-agent-stack Mock 服务（见下文）。

### 1. 安装依赖

```bash
git clone https://github.com/kintaiW/gm-llm-bench
cd gm-llm-bench
pip install -r requirements.txt
```

**requirements.txt：**
```
anthropic>=0.40.0
openai>=1.50.0
httpx>=0.27.0
```

### 2. 仅评测 C1-C4（无需 Mock，最简单）

```bash
# GPT-4o
export OPENAI_API_KEY=sk-...
python harness/run_eval.py \
  --model gpt-4o \
  --categories C1,C2,C3,C4 \
  --output leaderboard/results/gpt-4o.json

# Claude Opus
export ANTHROPIC_API_KEY=sk-ant-...
python harness/run_eval.py \
  --model claude-opus-4-7 \
  --categories C1,C2,C3,C4

# DeepSeek
export DEEPSEEK_API_KEY=sk-...
python harness/run_eval.py \
  --model deepseek-chat \
  --categories C1,C2,C3,C4
```

### 3. 评测 C5/C6（需要 Mock 服务）

```bash
# 第一步：启动 SVS Mock（来自 gm-agent-stack）
cd ../mp-mock/0029-svs-mock
cargo run -- --mode both &
# Mock 默认监听 http://localhost:9000

# 第二步：运行完整评测
export SVS_MOCK_URL=http://localhost:9000/mcp
python harness/run_eval.py \
  --model gpt-4o \
  --categories C1,C2,C3,C4,C5,C6 \
  --svs-mock-url $SVS_MOCK_URL
```

### 4. 查看结果

评测完成后，结果保存在 `leaderboard/results/<model>.json`：

```json
{
  "model": "gpt-4o",
  "timestamp": "2026-04-22T10:00:00Z",
  "total_score": 1234.5,
  "total_max": 1760.0,
  "total_pct": 70.1,
  "categories": {
    "C1": {"score": 450.0, "max": 600.0, "pct": 75.0, "count": 60},
    "C2": {"score": 320.0, "max": 400.0, "pct": 80.0, "count": 40},
    "C3": {"score": 280.0, "max": 500.0, "pct": 56.0, "count": 50},
    "C4": {"score": 184.5, "max": 400.0, "pct": 46.1, "count": 40}
  }
}
```

更新排行榜页面：

```bash
python scripts/update_leaderboard.py
# 生成 leaderboard/index.html，可直接浏览器打开或部署到 GitHub Pages
```

### 5. 一键跑所有模型

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export DEEPSEEK_API_KEY=sk-...

bash scripts/run_all_models.sh
```

### 调试模式（只跑前 5 题）

```bash
python harness/run_eval.py \
  --model gpt-4o \
  --categories C1 \
  --max-questions 5 \
  --sleep 0
```

---

## 目录结构

```
gm-llm-bench/
├── data/
│   └── questions/
│       ├── c1_clause_attribution.json   # 60 题：条款归属单选
│       ├── c2_standard_mapping.json     # 40 题：标准编号匹配
│       ├── c3_skod_scoring.json         # 50 题：SKOD 四维数值评分
│       ├── c4_nonconformity.json        # 40 题：不符合项多选+严重程度
│       ├── c5_code_rewriting.json       # 30 题：国密代码改写
│       └── c6_tool_use.json             # 80 题：MCP 工具调用序列
├── harness/
│   ├── run_eval.py                      # 主入口：加载题目→调用 LLM→评分→输出
│   ├── evaluators/
│   │   ├── c1_c2_evaluator.py           # 字符串精确匹配
│   │   ├── c3_evaluator.py              # 四维数值，容差评分
│   │   ├── c4_evaluator.py              # F1 分数 + 严重程度权重
│   │   ├── c5_evaluator.py              # 语法检查 + 国密关键词 + Mock 执行
│   │   └── c6_evaluator.py              # 工具序列精确/模糊匹配
│   └── providers/
│       ├── base.py                      # Provider 基类
│       ├── openai_provider.py           # OpenAI / 兼容接口（Qwen 等）
│       ├── anthropic_provider.py        # Anthropic Claude
│       └── deepseek_provider.py         # DeepSeek
├── leaderboard/
│   ├── index.html                       # GitHub Pages 排行榜页面
│   └── results/                        # 每个模型的评测结果 JSON
├── scripts/
│   ├── run_all_models.sh                # 批量评测脚本
│   └── update_leaderboard.py           # 从 results/ 生成排行榜 HTML
└── requirements.txt
```

---

## 添加新模型

**方案一：使用现有 OpenAI 兼容 Provider（Qwen、Kimi、豆包等）**

```bash
export OPENAI_API_KEY=你的key
python harness/run_eval.py \
  --model qwen-max \
  --categories C1,C2,C3,C4
```

如果 base_url 不同（如阿里云 DashScope），在 `harness/providers/openai_provider.py` 里传入 `base_url` 参数，或新建一个 provider：

```python
# harness/providers/qwen_provider.py
from .openai_provider import OpenAIProvider
import os

class QwenProvider(OpenAIProvider):
    def __init__(self, model: str = "qwen-max"):
        import openai
        self.model = model
        self.client = openai.OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
```

**方案二：提交 PR**

1. 在 `harness/providers/` 下添加 provider 文件
2. 在 `harness/run_eval.py` 的 `get_provider()` 中加入判断
3. 运行评测，把结果 JSON 放入 `leaderboard/results/你的模型名.json`
4. 提交 PR

---

## 评分规则详解

### C1/C2 — 字符串匹配

```
正确 → 10 分
错误 → 0 分
```

C1 提取 LLM 响应中的 A/B/C/D 字母；C2 提取 GM/T 或 GB/T 标准编号。容忍空格差异（`GM/T 0016-2012` = `GM/T0016-2012`）。

### C3 — 容差评分

```
每个维度（S/K/O/D）：
  |预测值 - 参考值| ≤ 容差（默认 2）→ 该维度满分
  否则 → 0 分

最终分数 = (通过维度数 / 4) × 10
```

容差设计原因：SKOD 评分本身有主观成分，要求精确相等对 AI 不公平；但偏差超过 2 分往往说明理解有根本性错误。

### C4 — F1 + 严重程度

```
精确率 P = TP / (TP + FP)   # 预测的里有多少是对的
召回率 R = TP / (TP + FN)   # 正确答案里有多少被预测到了
F1 = 2 × P × R / (P + R)

严重程度匹配率 = 正确匹配严重程度的选项 / 正确选中的选项数

最终分数 = (F1 × 0.7 + 严重程度匹配率 × 0.3) × 10
```

### C5 — 代码改写（无 Mock）

```
基础分：
  语法可解析            → +2 分
  包含国密关键词         → +8 分
  混用了非国密算法       → 降至 3 分

有 Mock 时额外：
  代码能对接 Mock 执行   → +5 分（替代部分静态分）
```

### C6 — 工具序列

```
精确匹配（顺序完全一致） → exact_match 分（通常 10 分）
可接受替代序列           → acceptable 分（通常 8 分）
部分匹配（覆盖率 × 5）  → partial_sequence 分
完全错误                → 0 分
```

---

## 题库说明

### 题目来源

所有题目基于以下**公开发布**的国家标准和行业标准设计：

- **GB/T 39786-2021**《信息安全技术 信息系统密码应用基本要求》
- **GM/T 0002-2012** SM4 分组密码算法
- **GM/T 0003-2012** SM2 椭圆曲线公钥密码算法
- **GM/T 0004-2012** SM3 密码杂凑算法
- **GM/T 0009-2012** SM2 数字签名应用规范
- **GM/T 0010-2012** SM2 密码算法加密签名消息语法规范
- **GM/T 0015-2012** 基于 SM2 密码算法的数字证书格式规范
- **GM/T 0016-2012** 智能密码钥匙密码应用接口规范
- **GM/T 0018-2023** 密码设备应用接口规范
- **GM/T 0029-2014** 签名验签服务器技术规范
- **GB/T 38636-2020** 信息安全技术 传输层密码协议（TLCP）

### 题目数量（MVP 阶段）

当前 MVP 共 **176 题**（C1:15, C2:8, C3:3, C4:40, C5:30, C6:80），目标扩展至 **300 题**（C1:60, C2:40, C3:50）。欢迎提交 Issue 或 PR 补充题目。

### 题目格式

```json
// C1/C2 格式
{
  "id": "C1-001",
  "category": "C1",
  "question": "...",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "answer": "C",
  "clause": "6.1 物理和环境安全",
  "explanation": "..."
}

// C3 格式
{
  "id": "C3-001",
  "category": "C3",
  "scenario": "某电商平台密评情况描述...",
  "question": "请对该系统进行 SKOD 评估...",
  "reference_scores": {"S": 1, "K": 0, "O": 1, "D": 0},
  "scoring_tolerance": 2,
  "explanation": "..."
}

// C4 格式
{
  "id": "C4-001",
  "category": "C4",
  "scenario": "场景描述...",
  "question": "选出所有不符合项并标注严重程度",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "answer": ["A", "B"],
  "severity": {"A": "严重", "B": "一般"},
  "explanation": "..."
}

// C6 格式
{
  "id": "C6-001",
  "category": "C6",
  "scenario": "场景描述...",
  "expected_tool_sequence": ["svs_sign", "svs_verify"],
  "acceptable_alternatives": [["sdf_sm2_sign", "sdf_sm2_verify"]],
  "scoring": {"exact_match": 10, "acceptable": 8, "partial_sequence": 5, "wrong_tool": 0}
}
```

---

## 与 gm-agent-stack 的关系

GM-Bench 是 [gm-agent-stack](https://github.com/kintaiW/gm-agent-stack) 生态的组成部分：

```
gm-agent-stack
├── 0016-skf-mock    ← UKey 模拟器（C5/C6 验证用）
├── 0018-sdf-mock    ← HSM 密码机模拟器（C5/C6 验证用）
├── 0029-svs-mock    ← 签名验签服务器模拟器（C5/C6 验证用）
├── ccasa-harness    ← AI 密评助手（使用 gm-bench 评测它自己的能力）
└── gm-llm-bench     ← 本仓库：评测 LLM 的国密能力
```

**GM-Bench 是衡量"AI 懂不懂国密"的尺子；gm-agent-stack 是让 AI 真正能做国密的工具箱。**

---

## 免责声明

- GM-Bench 是研究性评测基准，评测分数**不构成任何官方密评认证或合规证明**
- 题目基于公开标准设计，答案经人工审核，但可能存在理解偏差
- C5 代码改写的执行验证仅针对 Mock 设备，不代表在真实密码设备上的兼容性
- 本项目不涉及任何保密信息，所有内容基于公开发布的国家标准

> ⚠️ **本项目仅用于研究与评测目的。**

---

## License

Apache-2.0 © gm-agent-stack contributors
