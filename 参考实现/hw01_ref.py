"""
第 01 课 参考实现
==================

⚠ 规则：卡住 20 分钟以上才看这个。看完关掉，自己重写一遍。

对照点（本课全部知识点）：
  - chunk_text:  清理空白、固定步长、overlap 边界保护、不丢尾巴
  - embed_texts: 批量 + 分批（64 上限）+ 顺序一致
  - cosine:      手写、零模长保护、长度校验
  - retrieve:    查询也 embed、降序排序、top_k
  - answer:      带来源标识的上下文 + 「找不到就说找不到」
"""

import json
import math
import os
import re
import sys
import urllib.error
import urllib.request

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


def load_corpus() -> list[dict]:
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
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}: {body}")


def _post(url: str, key: str, payload: dict, timeout: int = 90) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise APIError(e.code, e.read().decode("utf-8", errors="replace")) from e
    except urllib.error.URLError as e:
        raise APIError(0, f"网络层失败: {e.reason}") from e


# ---------- TODO 1 ----------
def chunk_text(text: str, doc_id: str, size: int = 200, overlap: int = 50) -> list[dict]:
    if not text or not text.strip():
        return []
    if overlap >= size:
        raise ValueError(f"overlap({overlap}) 必须小于 size({size})，否则步长为 0 会死循环")

    # 清理空白：连续空行压成一个，行首尾去空白
    cleaned = re.sub(r"\n\s*\n+", "\n", text.strip())
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    step = size - overlap
    chunks = []
    start = 0
    idx = 0
    while start < len(cleaned):
        piece = cleaned[start:start + size].strip()
        if piece:
            chunks.append({
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}#{idx}",
                "text": piece,
            })
            idx += 1
        start += step
    return chunks


# ---------- TODO 2 ----------
def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    out: list[list[float]] = []
    batch = 64  # 智谱单次上限
    for i in range(0, len(texts), batch):
        part = texts[i:i + batch]
        resp = _post(EMB_URL, EMB_KEY, {"model": EMB_MODEL, "input": part})
        data = resp.get("data") or []
        if len(data) != len(part):
            raise APIError(0, f"返回向量数({len(data)})与请求数({len(part)})不一致")
        # data 里每项有 index，按它排序保证顺序
        data = sorted(data, key=lambda d: d.get("index", 0))
        for d in data:
            out.append(d["embedding"])
    return out


# ---------- TODO 3 ----------
def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError(f"向量长度不一致: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:      # 关键边界：零模长
        return 0.0
    return dot / (na * nb)


# ---------- TODO 4 ----------
def retrieve(question: str, chunks: list[dict],
             chunk_vecs: list[list[float]], top_k: int = 3) -> list[dict]:
    if len(chunks) != len(chunk_vecs):
        raise ValueError(f"chunks({len(chunks)}) 与向量({len(chunk_vecs)}) 数量不一致")
    if not chunks:
        return []
    qv = embed_texts([question])[0]
    scored = []
    for c, v in zip(chunks, chunk_vecs):
        scored.append({
            "doc_id": c["doc_id"],
            "chunk_id": c["chunk_id"],
            "text": c["text"],
            "score": cosine_similarity(qv, v),
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


# ---------- TODO 5 ----------
SYSTEM_PROMPT = """你是校园问答助手。请严格根据提供的资料回答问题。

规则：
1. 只使用资料中的信息，不要编造
2. 如果资料中找不到答案，明确回答"资料中没有相关信息"
3. 回答要简洁，直接给结论
"""


def answer(question: str, retrieved: list[dict]) -> str:
    if retrieved:
        parts = []
        for i, r in enumerate(retrieved, start=1):
            parts.append(f"【片段 {i}｜来源：{r['doc_id']}】\n{r['text']}")
        context = "\n\n".join(parts)
    else:
        context = "（没有检索到任何相关资料）"

    user = f"资料：\n{context}\n\n问题：{question}"
    resp = _post(CHAT_URL, CHAT_KEY, {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        "max_tokens": 500,
        "temperature": 0,
    })
    msg = resp["choices"][0]["message"]
    return msg.get("content") or ""


def _normalize(s: str) -> str:
    """归一化文本，用于答案匹配。

    为什么必须做这一步（本课实测踩到的坑）：
      黄金集里写的是 "10 册"（带空格），模型回答 "10册"（不带空格）。
      直接 `in` 匹配会把它判成错的 —— 但答案明明是对的。

      这是真实 RAG 评测里最经典的假阴性来源。评测器本身也需要被验证。
    """
    if not s:
        return ""
    # 去掉所有空白（含全角空格）、常见标点，统一大小写
    s = re.sub(r"[\s\u3000]+", "", s)
    s = re.sub(r"[，。、；：！？,.;:!?\"'`（）()【】\[\]]", "", s)
    return s.lower()


def evaluate(verbose: bool = True) -> dict:
    golden = load_golden()
    corpus = load_corpus()
    chunks, chunk_vecs = [], []
    for doc in corpus:
        chunks.extend(chunk_text(doc["text"], doc["doc_id"]))
    if not chunks:
        raise RuntimeError("chunk_text 返回了空列表")
    chunk_vecs = embed_texts([c["text"] for c in chunks])

    if verbose:
        print(f"语料 {len(corpus)} 篇 → 切成 {len(chunks)} 块，已全部向量化")

    hits, correct, top1_hits, details = 0, 0, 0, []
    for item in golden["items"]:
        ret = retrieve(item["question"], chunks, chunk_vecs, top_k=3)
        got_docs = [r["doc_id"] for r in ret]
        hit = item["source_doc"] in got_docs
        top1 = bool(got_docs) and got_docs[0] == item["source_doc"]

        ans = answer(item["question"], ret)
        norm_ans = _normalize(ans)
        must = item["must_contain"]
        # 关键：两边都归一化后再匹配
        ok = all(_normalize(m) in norm_ans for m in must)

        hits += 1 if hit else 0
        top1_hits += 1 if top1 else 0
        correct += 1 if ok else 0
        details.append({
            "id": item["id"], "question": item["question"], "type": item["type"],
            "want_doc": item["source_doc"], "got_docs": got_docs,
            "hit": hit, "top1": top1,
            "must_contain": must, "correct": ok, "answer": (ans or "")[:150],
        })
    total = len(golden["items"])
    return {"total": total, "hits": hits, "correct": correct, "top1_hits": top1_hits,
            "hit_rate": hits / total, "accuracy": correct / total,
            "top1_rate": top1_hits / total, "details": details}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    r = evaluate()
    print(f"\n检索命中率(top3)： {r['hit_rate']:.1%}  ({r['hits']}/{r['total']})")
    print(f"检索命中率(top1)： {r['top1_rate']:.1%}  ({r['top1_hits']}/{r['total']})")
    print(f"答案准确率：       {r['accuracy']:.1%}  ({r['correct']}/{r['total']})")
    print("\n--- 失败案例 ---")
    for d in r["details"]:
        if not d["hit"] or not d["correct"]:
            flag = ("检索错" if not d["hit"] else "") + ("/答案错" if not d["correct"] else "")
            print(f"\n  {d['id']} [{d['type']}] {d['question']}  ({flag})")
            print(f"      应召回 {d['want_doc']}，实际 {d['got_docs'][:3]}")
            print(f"      必含 {d['must_contain']}")
            print(f"      回答：{d['answer']!r}")
