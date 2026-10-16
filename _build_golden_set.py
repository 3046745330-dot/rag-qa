# -*- coding: utf-8 -*-
"""生成并【验证】RAG 黄金集（ground truth）。

为什么这个脚本要验证：
  黄金集是评测的基准。如果标准答案写错了，整个评测结论都是垃圾。
  所以每道题都给「答案必须包含的关键片段」，脚本会去源文档里检查
  这些片段**真的存在**。不存在就报错，不让它进黄金集。

这是本项目和「随便做做的 RAG」最大的区别：
  **评测集本身是被验证过的，不是拍脑袋写的。**

题目类型（故意制造检索难点）：
  easy     —— 一问一答，向量检索应该能过
  trap     —— 有相似文档干扰（如三个文档都提"开放时间"）
  buried   —— 答案藏在长文档中间，考验切分策略
  multi    —— 需要跨文档或跨段落综合
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(HERE, "docs")


def load_doc(doc_id: str) -> str:
    path = os.path.join(DOCS_DIR, f"{doc_id}.md")
    with open(path, encoding="utf-8") as f:
        return f.read()


# ============================================================
# 黄金集定义
#   q         问题
#   doc       应该被召回的文档 id（标准答案）
#   must      答案必须包含的关键片段（用于验证 ground truth 正确性）
#   type      难度类型
# ============================================================
GOLDEN = [
    # ---------- easy：直接问答 ----------
    dict(q="图书馆周末几点开门？", doc="library-hours", must=["09:00 - 21:00"], type="easy",
         note="周末时间明确写在第一段"),
    dict(q="本科生一次最多能借几本书？", doc="library-borrow", must=["10 册"], type="easy",
         note="数字型答案"),
    dict(q="图书借阅期限是多久？", doc="library-borrow", must=["30 天"], type="easy",
         note="注意本科生和研究生不同，容易答错对象"),
    dict(q="校园网一个月多少钱？", doc="network", must=["20 元"], type="easy",
         note="清晰单值"),
    dict(q="国家奖学金的金额是多少？", doc="scholarship", must=["8000"], type="easy",
         note="数字型"),

    # ---------- trap：相似文档干扰 ----------
    dict(q="图书馆开放时间是什么？", doc="library-hours",
         must=["08:00 - 22:00"], type="trap",
         note="干扰项：lab-hours.md 和 gym-hours.md 也讲「开放时间」，且标题都含「时间」"),
    dict(q="实验室几点开门？", doc="lab-hours", must=["08:30-17:30"], type="trap",
         note="干扰项：library-hours.md 有更详细的时段表，向量检索容易误召回"),
    dict(q="游泳馆什么时候开放？", doc="gym-hours", must=["14:00-21:00", "周一闭馆"], type="trap",
         note="干扰项：同一文档里的羽毛球馆时间，容易混淆"),
    dict(q="食堂早餐几点开始？", doc="canteen", must=["06:30"], type="trap",
         note="干扰项：三个食堂时间不同，答案是区间不是单值"),

    # ---------- buried：藏在长文档中间 ----------
    dict(q="军训要多久？", doc="freshman", must=["两周"], type="buried",
         note="527 字的长文档，「关于军训」在小节倒数第二段。按固定长度切分容易切散"),
    dict(q="学位英语还是硬性要求吗？", doc="graduation", must=["不再将学位英语"], type="buried",
         note="长文档末尾才有，前面全是学分和毕设要求"),
    dict(q="宿舍晚上几点要求安静？", doc="dorm-power", must=["23:30"], type="buried",
         note="夹在第 3 条，前后是电费和大功率电器"),

    # ---------- multi：需要综合 ----------
    dict(q="图书馆闭馆前多久停止借还书？", doc="library-hours",
         must=["30 分钟"], type="multi",
         note="需要从多个时段中提取出「闭馆前 30 分钟」这条通用规则"),
    dict(q="校园卡丢了怎么办？", doc="card",
         must=["挂失", "20 元"], type="multi",
         note="答案含两个要点，单句检索可能只捞到一半"),
    dict(q="宿舍电费怎么交？", doc="dorm-power",
         must=["校园卡 APP"], type="multi",
         note="card.md 也提「校园卡充值」，存在混淆可能"),

    # ---------- 刻意设计的「困难题」：用来暴露朴素 RAG 的弱点 ----------
    dict(q="图书馆自习座位可以提前几天预约？", doc="library-seat", must=["3 天"], type="buried",
         note="library-seat.md 与 library-hours.md 主题相近，且这题答案藏在第二条"),
    dict(q="考试作弊会怎么处理？", doc="exam", must=["留校察看", "开除学籍"], type="multi",
         note="答案是两个并列后果"),
    dict(q="校医院周末能看门诊吗？", doc="medical", must=["仅急诊"], type="trap",
         note="关键限定词是「仅急诊」，漏掉就会答错"),
    dict(q="毕业设计查重率要求多少？", doc="graduation", must=["30%"], type="buried",
         note="长文档中部"),
]


def main():
    print("=" * 78)
    print("生成 RAG 黄金集（含 ground truth 验证）")
    print("=" * 78)
    print()

    verified = []
    errors = []

    for i, item in enumerate(GOLDEN, start=1):
        q, doc_id, must = item["q"], item["doc"], item["must"]
        try:
            text = load_doc(doc_id)
        except FileNotFoundError:
            errors.append(f"[{i}] {q}\n     源文档不存在：{doc_id}")
            continue

        # 核心验证：must 里的关键片段必须真的在源文档里
        missing = [m for m in must if m not in text]
        if missing:
            errors.append(
                f"[{i}] {q}\n     文档 {doc_id} 里找不到这些片段：{missing}"
            )
            continue

        verified.append(dict(
            id=f"q{i:02d}",
            question=item["q"],
            source_doc=doc_id,
            must_contain=must,
            type=item["type"],
            note=item["note"],
        ))

    if errors:
        print("✗ ground truth 校验失败，以下题目有问题：\n")
        for e in errors:
            print(f"  {e}\n")
        print("不予导出黄金集 —— 错误的评测集比没有评测集更糟。")
        sys.exit(1)

    # ---- 统计 ----
    by_type = {}
    for v in verified:
        by_type.setdefault(v["type"], []).append(v)
    print(f"✓ 全部 {len(verified)} 道题的答案已在源文档中验证通过\n")
    for t, items in sorted(by_type.items()):
        print(f"  {t:8} {len(items):2} 题   " + "、".join(x["id"] for x in items))

    # ---- 检查文档覆盖：哪些文档没被考到 ----
    all_docs = {f[:-3] for f in os.listdir(DOCS_DIR) if f.endswith(".md")}
    covered = {v["source_doc"] for v in verified}
    uncovered = sorted(all_docs - covered)
    print(f"\n  语料覆盖：{len(covered)}/{len(all_docs)} 个文档被考到")
    if uncovered:
        print(f"  未覆盖：{', '.join(uncovered)}")
        print("  （未覆盖不是错误，但这些文档会成为检索干扰项）")

    # ---- 导出 ----
    out = {
        "version": "1.0",
        "description": "校园问答 RAG 评测黄金集。每题的答案已在源文档中验证存在。",
        "total": len(verified),
        "types": {t: len(v) for t, v in by_type.items()},
        "items": verified,
    }
    out_path = os.path.join(HERE, "golden_set.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\n已导出：{out_path}")

    # ---- 给每题一个「应答要点」的展示 ----
    print()
    print("=" * 78)
    print("黄金集内容预览（这些答案都在源文档里被验证过）")
    print("=" * 78)
    for v in verified:
        print(f"\n  {v['id']} [{v['type']}] {v['question']}")
        print(f"      应召回：{v['source_doc']}")
        print(f"      必含：  {' / '.join(v['must_contain'])}")
        print(f"      设计意图：{v['note']}")


if __name__ == "__main__":
    main()
