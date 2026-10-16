"""
第 01 课作业：从零实现朴素 RAG
================================

目标：不借助任何框架，手写 RAG 的五个环节。
      先做出"能跑但不够好"的版本 —— 它是你后面所有优化的对比基准。

规则：
  1. 只准用标准库：json / os / math / re / urllib
  2. cosine_similarity **不许用 numpy** —— 手写循环
  3. embed_texts 必须批量调用（一次多段文本）
  4. 五个 TODO 全部填完

讲义：../讲义/01-朴素RAG.md
验收：python ../验收/check_hw01.py
"""

import json
import math
import os
import re
import sys
import urllib.error
import urllib.request

# ============================================================
# 样板代码：.env 读取 + 路径常量
# ============================================================

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENV_PATH = os.path.join(ROOT, ".env")
DOCS_DIR = os.path.join(ROOT, "docs")
GOLDEN_PATH = os.path.join(ROOT, "golden_set.json")


def _load_env(path: str) -> dict:
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


_ENV = _load_env(ENV_PATH)

CHAT_KEY = _ENV.get("ZHIPU_API_KEY", "")
CHAT_URL = _ENV.get("ZHIPU_BASE", "")
CHAT_MODEL = _ENV.get("ZHIPU_MODEL", "glm-4-air")

EMB_KEY = _ENV.get("ZHIPU_API_KEY", "")
EMB_URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"
EMB_MODEL = "embedding-3"
EMB_DIM = 2048


# ============================================================
# 工具函数（已写好）
# ============================================================
def load_corpus() -> list[dict]:
    """读 docs/ 下所有 .md，返回 [{'doc_id':..., 'title':..., 'text':...}]"""
    out = []
    for name in sorted(os.listdir(DOCS_DIR)):
        if not name.endswith(".md"):
            continue
        doc_id = name[:-3]
        with open(os.path.join(DOCS_DIR, name), encoding="utf-8") as f:
            raw = f.read()
        lines = raw.strip().split("\n")
        title = lines[0].lstrip("# ").strip() if lines else doc_id
        body = "\n".join(lines[1:]).strip()
        out.append({"doc_id": doc_id, "title": title, "text": body})
    return out


def load_golden() -> dict:
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)


class APIError(Exception):
    """API 调用失败。必须带上状态码和响应体。"""

    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}: {body}")


def _post(url: str, key: str, payload: dict, timeout: int = 90) -> dict:
    """发一个 POST，返回解析后的 JSON。已替你写好，直接用。"""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise APIError(e.code, e.read().decode("utf-8", errors="replace")) from e
    except urllib.error.URLError as e:
        raise APIError(0, f"网络层失败: {e.reason}") from e


# ============================================================
# TODO 1 —— 切分
# ============================================================
def chunk_text(text: str, doc_id: str, size: int = 200, overlap: int = 50) -> list[dict]:
    """把一篇文档按固定长度切成块。

    要求：
      1. 每块最多 size 个字符，块之间重叠 overlap 个字符
      2. 返回 [{'doc_id':..., 'chunk_id':..., 'text':...}, ...]
         chunk_id 形如 "library-hours#0"、"library-hours#1"
      3. text 为空时返回空列表
      4. **切分前先清理空白**：把连续空行压成一个（用 re.sub）
         —— 否则空白会浪费掉宝贵的 size 预算
      5. 最后一块即使不足 size 也要保留（别丢掉尾巴）

    提示：
      - 用 while 循环 + 起始下标推进，步长是 (size - overlap)
      - 如果 overlap >= size，步长会变成 0 或负数 → 死循环！
        这种情况要处理（抛 ValueError 或强制 overlap = size // 2）

    讲义第三节 ①
    """
    # TODO 1: 在这里写你的实现
    raise NotImplementedError("TODO 1 还没写")


# ============================================================
# TODO 2 —— 向量化（批量）
# ============================================================
def embed_texts(texts: list[str]) -> list[list[float]]:
    """调 embedding API，返回向量列表。

    要求：
      1. **批量调用** —— 一次把所有 texts 传过去（input 是数组）
         ⚠️ 但注意：单次请求最多 64 条，超过要分批
      2. 返回顺序必须和输入顺序一致
      3. 返回的数量必须等于 len(texts)，否则抛 APIError
      4. 请求体格式：{"model": EMB_MODEL, "input": [...]}
      5. 响应里向量在 data[i]["embedding"]

    提示：
      - 用上面写好的 _post(EMB_URL, EMB_KEY, payload)
      - 分批：每批 64 条，循环发，结果按顺序 extend 到总列表

    讲义第三节 ②
    """
    # TODO 2: 在这里写你的实现
    raise NotImplementedError("TODO 2 还没写")


# ============================================================
# TODO 3 —— 余弦相似度（手写，不许 numpy）
# ============================================================
def cosine_similarity(a: list[float], b: list[float]) -> float:
    """手写余弦相似度 = (A·B) / (|A| × |B|)

    要求：
      1. 不许 import numpy，用 for 循环 / sum / 列表推导
      2. 长度不一致 → 抛 ValueError
      3. **任一向量的模长为 0 → 返回 0.0**（不能除零！）
         —— 这是必考的边界情况

    手算步骤：
      dot   = sum(x*y for x, y in zip(a, b))
      |a|   = sqrt(sum(x*x for x in a))
      |b|   = sqrt(sum(y*y for y in b))
      return dot / (|a| * |b|)

    讲义第三节 ③
    """
    # TODO 3: 在这里写你的实现
    raise NotImplementedError("TODO 3 还没写")


# ============================================================
# TODO 4 —— 检索
# ============================================================
def retrieve(question: str, chunks: list[dict],
             chunk_vecs: list[list[float]], top_k: int = 3) -> list[dict]:
    """检索与问题最相关的 top_k 个块。

    要求：
      1. 把 question 也 embed 一次（调 embed_texts([question])）
      2. 对每个 chunk 算余弦相似度
      3. 按 score **降序** 排序，取前 top_k
      4. 返回 [{'doc_id':..., 'chunk_id':..., 'text':..., 'score': float}, ...]
      5. chunks 和 chunk_vecs 长度不一致 → 抛 ValueError

    提示：用 sorted(..., key=lambda x: x["score"], reverse=True)

    讲义第三节 ③
    """
    # TODO 4: 在这里写你的实现
    raise NotImplementedError("TODO 4 还没写")


# ============================================================
# TODO 5 —— 生成答案
# ============================================================
SYSTEM_PROMPT = """你是校园问答助手。请严格根据提供的资料回答问题。

规则：
1. 只使用资料中的信息，不要编造
2. 如果资料中找不到答案，明确回答"资料中没有相关信息"
3. 回答要简洁，直接给结论
"""


def answer(question: str, retrieved: list[dict]) -> str:
    """把检索结果组装成 prompt，调模型生成答案。

    要求：
      1. 把 retrieved 拼成带来源标识的上下文，格式：
         【片段 1｜来源：library-hours】
         图书馆开放时间安排如下...

         【片段 2｜来源：library-seat】
         ...
         （为什么带来源？讲义第三节 ④）
      2. retrieved 为空时，也要能正常回答（模型应该说"没有相关信息"）
      3. 用 _post(CHAT_URL, CHAT_KEY, payload) 发请求
      4. messages 结构：[{"role":"system","content":SYSTEM_PROMPT},
                        {"role":"user","content":<拼好的prompt>}]
      5. 返回 choices[0].message.content，可能是 None，要兜底成空字符串

    讲义第三节 ⑤
    """
    # TODO 5: 在这里写你的实现
    raise NotImplementedError("TODO 5 还没写")


# ============================================================
# 评测器（已写好）—— 验收脚本会调它
# ============================================================
def evaluate(verbose: bool = True) -> dict:
    """跑完整评测，返回 {'hit_rate': float, 'accuracy': float, ...}"""
    golden = load_golden()
    corpus = load_corpus()

    # 切分 + 向量化
    chunks, chunk_vecs = [], []
    for doc in corpus:
        cs = chunk_text(doc["text"], doc["doc_id"])
        chunks.extend(cs)
    if not chunks:
        raise RuntimeError("chunk_text 返回了空列表")
    vecs = embed_texts([c["text"] for c in chunks])
    chunk_vecs = vecs

    hits, correct, details = 0, 0, []

    for item in golden["items"]:
        ret = retrieve(item["question"], chunks, chunk_vecs, top_k=3)
        got_docs = [r["doc_id"] for r in ret]
        hit = item["source_doc"] in got_docs
        ans = answer(item["question"], ret)
        must = item["must_contain"]
        ok = all(m in (ans or "") for m in must)

        if hit:
            hits += 1
        if ok:
            correct += 1

        details.append({
            "id": item["id"],
            "question": item["question"],
            "type": item["type"],
            "want_doc": item["source_doc"],
            "got_docs": got_docs,
            "hit": hit,
            "must_contain": must,
            "correct": ok,
            "answer": (ans or "")[:120],
        })

    total = len(golden["items"])
    return {
        "total": total,
        "hits": hits,
        "correct": correct,
        "hit_rate": hits / total,
        "accuracy": correct / total,
        "details": details,
    }


# ============================================================
# 自测
# ============================================================
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 72)
    print("朴素 RAG 端到端自测")
    print("=" * 72)

    try:
        result = evaluate(verbose=False)
        print(f"\n检索命中率： {result['hit_rate']:.1%}  ({result['hits']}/{result['total']})")
        print(f"答案准确率： {result['accuracy']:.1%}  ({result['correct']}/{result['total']})")
        print("\n--- 失败案例 ---")
        for d in result["details"]:
            if not d["hit"] or not d["correct"]:
                flag = []
                if not d["hit"]:
                    flag.append("检索错")
                if not d["correct"]:
                    flag.append("答案错")
                print(f"\n  {d['id']} [{d['type']}] {d['question']}")
                print(f"      应召回 {d['want_doc']}，实际 {d['got_docs'][:3]}")
                print(f"      必含 {d['must_contain']}")
                print(f"      回答了：{d['answer']!r}")
    except NotImplementedError as e:
        print(f"\n还没写完：{e}")
