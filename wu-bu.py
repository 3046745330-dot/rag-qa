"""
看见 RAG 五步的数据流动
=======================

为什么做这个：
  用户把 chunk_text 和 embed_texts 搞混了 ——
  这是 RAG 里最典型的一对混淆。

  光讲「chunk 是切、embed 是变」不够，得让他**看见**每一步的产物长什么样：
  切分后的产物还是文字；向量化后的产物才是数字。

这个脚本：
  用真实的语料，把 5 步依次跑一遍，每步都打印「输入长什么样 → 输出长什么样」。
  向量部分用假数据（不调 API），因为目的是看**形状**，不是看真实数值。
"""
import math
import sys

sys.stdout.reconfigure(encoding="utf-8")


def banner(step, name, title):
    print()
    print("=" * 68)
    print(f"  第 {step} 步：{name}")
    print(f"  {title}")
    print("=" * 68)


def arrow(label, value, note=""):
    print(f"\n  {label}")
    if note:
        print(f"    {note}")
    if isinstance(value, list):
        for i, x in enumerate(value):
            if isinstance(x, dict):
                print(f"      [{i}] {x}")
            elif isinstance(x, list):
                vs = str(x)
                if len(vs) > 56:
                    vs = vs[:56] + "...]"
                print(f"      [{i}] {vs}")
            else:
                s = str(x)
                if len(s) > 62:
                    s = s[:62] + "..."
                print(f"      [{i}] {s}")
    else:
        print(f"      {value}")


# ============================================================
# 真实的语料（短一点，方便展示）
# ============================================================
ARTICLE = (
    "图书馆开放时间安排如下：\n"
    "周一至周五：08:00 - 22:00\n"
    "周六至周日：09:00 - 21:00\n\n\n"
    "闭馆前 30 分钟停止借还书服务。"
)

QUESTION = "图书馆周末几点开门？"


def fake_embed(text):
    """假向量：用文字长度生成一串确定的数字，只为展示形状。

    真向量是 2048 个浮点数，这里用 5 个数字代替，
    因为目的是让用户看清「形状」，不是看真实数值。
    """
    h = sum(ord(c) for c in text) % 100
    return [round((h + i * 7) / 100, 3) for i in range(5)]


def main():
    print()
    print("★ 目的：看清每一步的「产物」长什么样")
    print("★ 重点：切分后的产物还是【文字】；向量化后的产物才是【数字】")

    # ------------------------------------------------------------
    banner(1, "chunk_text", "切分 —— 把长文章剪成小块")
    print(f"\n  【输入】一整篇文章（{len(ARTICLE)} 字）：")
    print(f'    "{ARTICLE[:46]}..."')

    # 真实的切分逻辑
    import re
    cleaned = re.sub(r"\n\s*\n+", "\n", ARTICLE.strip())
    size, overlap = 60, 20
    step = size - overlap
    chunks = []
    start = idx = 0
    while start < len(cleaned):
        piece = cleaned[start:start + size].strip()
        if piece:
            chunks.append({
                "doc_id": "library-hours",
                "chunk_id": f"library-hours#{idx}",
                "text": piece,
            })
            idx += 1
        start += step

    print(f"\n  【输出】{len(chunks)} 个块：")
    for c in chunks:
        print(f"    ┌─ {c['chunk_id']} ─────────────────────")
        print(f"    │ doc_id: {c['doc_id']}")
        print(f"    │ text:   {c['text'][:40]!r}")
        print(f"    └─────────────────────────────")

    print()
    print("  ⚠️ 注意：产物是【字典】，里面有 text 字段 —— 还是文字！")
    print("     这一步跟「向量」没有任何关系。")

    # ------------------------------------------------------------
    banner(2, "embed_texts", "向量化 —— 把文字变成数字")
    print(f"\n  【输入】上面那 {len(chunks)} 个块里的 text（文字）")

    vecs = [fake_embed(c["text"]) for c in chunks]

    print(f"\n  【输出】{len(vecs)} 个向量（每个是 5 个数字，真实是 2048 个）：")
    for c, v in zip(chunks, vecs):
        print(f"    {c['chunk_id']:18} → {v}")

    print()
    print("  ⚠️ 注意：产物是【数字列表】—— 文字消失了，只剩数字。")
    print("     这才是「变成向量」。")
    print()
    print("  ★ 所以：")
    print("       chunk_text  → 产物是文字   （切）")
    print("       embed_texts → 产物是数字   （变）")

    # ------------------------------------------------------------
    banner(3, "cosine_similarity", "算两个向量有多像")
    qv = fake_embed(QUESTION)

    print(f"\n  【输入】两个向量")
    print(f"    问题向量 qv = {qv}")
    print(f"    卡片向量 v  = {vecs[0]}")

    def cos(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    print(f"\n  【输出】一个分数：{cos(qv, vecs[0]):.4f}")
    print(f"    （这个脚本用的是假向量，分数没意义；")
    print(f"      真实场景下这个分数代表「问题」和「这张卡片」有多像）")

    # ------------------------------------------------------------
    banner(4, "retrieve", "检索 —— 挑出最像的 top_k 张")
    print(f"\n  【输入】")
    print(f"    问题：{QUESTION}")
    print(f"    {len(chunks)} 张卡片 + 它们的向量")
    print(f"    top_k = 2")

    print(f"\n  内部做了 4 件事：")
    print(f"    a. 把问题变成向量        ← 调用 embed_texts")
    print(f"    b. 逐个算相似度          ← 调用 cosine_similarity")
    print(f"    c. 按分数从高到低排序     ← .sort(reverse=True)")
    print(f"    d. 取前 top_k 个          ← [:top_k]")

    scored = []
    for c, v in zip(chunks, vecs):
        scored.append({
            "doc_id": c["doc_id"],
            "chunk_id": c["chunk_id"],
            "text": c["text"],
            "score": cos(qv, v),
        })
    scored.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n  排序后的分数（全部）：")
    for s in scored:
        print(f"    {s['score']:.4f}   {s['chunk_id']}")

    print(f"\n  【输出】top 2 张卡片：")
    for s in scored[:2]:
        print(f"    {s['chunk_id']}  score={s['score']:.4f}")
        print(f"        text: {s['text'][:36]!r}")

    print()
    print("  ★ 关键：retrieve 自己不干活，它调用 embed_texts 和 cosine_similarity")
    print("     它是「指挥官」，不是「工人」。")

    # ------------------------------------------------------------
    banner(5, "answer", "生成 —— 把卡片和问题交给模型")
    top2 = scored[:2]

    context_parts = []
    for i, r in enumerate(top2, 1):
        context_parts.append(f"【片段 {i}｜来源：{r['doc_id']}】\n{r['text']}")
    context = "\n\n".join(context_parts)

    print(f"\n  【输入】")
    print(f"    问题：{QUESTION}")
    print(f"    top 2 张卡片的正文")
    print(f"\n  内部：把卡片拼成一段文字，塞进 prompt")
    print(f"  ┌─ 拼好的上下文 ──────────────────────")
    for line in context.split("\n")[:8]:
        print(f"  │ {line}")
    print(f"  └──────────────────────────────────")

    print(f"\n  【输出】模型的回答（这一步真的要调 API，脚本里跳过）")
    print(f"    真实运行时会返回类似：")
    print(f'      「图书馆周末 09:00 开门，21:00 闭馆。」')

    # ------------------------------------------------------------
    print()
    print("=" * 68)
    print("  总结：五个函数的角色")
    print("=" * 68)
    print("""
  ┌──────────────┬──────────────┬──────────────┬─────────────────┐
  │ 函数         │ 输入         │ 输出         │ 一句话          │
  ├──────────────┼──────────────┼──────────────┼─────────────────┤
  │ chunk_text   │ 一篇文章     │ 一堆文本块   │ 切（产物是文字）│
  │ embed_texts  │ 一堆文本     │ 一堆向量     │ 变（产物是数字）│
  │ cosine_sim   │ 两个向量     │ 一个分数     │ 算像不像        │
  │ retrieve     │ 问题+卡片    │ 最像的top_k  │ 挑（调上面两个）│
  │ answer       │ top_k+问题   │ 回答         │ 生成            │
  └──────────────┴──────────────┴──────────────┴─────────────────┘

  ★ 最容易混的一对：
      chunk_text  → 产物是【文字】
      embed_texts → 产物是【数字】

  ★ retrieve 的角色：
      它自己不干活，调用 embed_texts + cosine_similarity 来完成工作。
""")


if __name__ == "__main__":
    main()
