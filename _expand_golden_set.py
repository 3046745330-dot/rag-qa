# -*- coding: utf-8 -*-
"""扩充黄金集：从 19 题扩到 ~40 题，适配扩大后的 37 篇语料。

为什么必须扩（这是实测驱动的决策）：
  语料扩到 37 篇后，原来 19 题只覆盖 15 篇。
  如果不补题，评测就测不出新增文档上的检索质量，
  "改进前后对比"也会失真。

设计原则（沿用第一版）：
  1. **每题都在源文档里验证过** —— must_contain 必须真的存在
  2. **按难度分层** —— easy / trap / buried / multi
  3. **优先出「朴素向量检索会失败」的题** —— 这些才是改进的空间

新增题目重点考察三类真实失败模式：
  A. 近义表述（问法 ≠ 文档措辞）—— 考验 embedding 的语义泛化
  B. 同簇干扰（多个文档共享词汇）—— 考验区分能力
  C. 跨文档综合（答案分散在多篇）—— 考验召回完整性
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(HERE, "docs")
GOLDEN_PATH = os.path.join(HERE, "golden_set.json")


def load_doc(doc_id: str) -> str:
    with open(os.path.join(DOCS_DIR, f"{doc_id}.md"), encoding="utf-8") as f:
        return f.read()


# ============================================================
# 新增题目
# ============================================================
NEW_ITEMS = [
    # ---------- A. 近义表述：问法 ≠ 文档措辞 ----------
    dict(q="图书馆的书弄丢了怎么赔？", doc="library-fine",
         must=["原价"], type="trap",
         note="文档措辞是「图书遗失需按原价赔偿」，问法用的是「弄丢」。近义泛化测试"),
    dict(q="在学校里打印一张纸多少钱？", doc="print",
         must=["0.10"], type="trap",
         note="文档措辞是「自助打印」，用户说的是「打印一张纸」。且 print.md 与 library-space.md 都提打印"),
    dict(q="宿舍能用电饭锅吗？", doc="dorm-safety",
         must=["严禁"], type="trap",
         note="dorm-safety.md 和 dorm-power.md 都提大功率电器，构成同簇干扰"),
    dict(q="心理健康咨询要花钱吗？", doc="psych",
         must=["免费"], type="easy",
         note="文档说「每次 50 分钟，免费」，问法是「要花钱吗」，需要语义反转理解"),
    dict(q="成绩不满意能改吗？", doc="course-grade",
         must=["复议"], type="trap",
         note="文档用「成绩复议」，问法用「能改吗」。近义测试"),
    dict(q="快递最多能放几天不取？", doc="post",
         must=["3 天"], type="buried",
         note="答案在 post.md 中段「超过 3 天未取的包裹将被退回」"),

    # ---------- B. 同簇干扰：多文档共享词汇 ----------
    dict(q="图书馆一共有几层？", doc="library-space",
         must=["6 层"], type="trap",
         note="图书馆相关的文档现在有 6 篇（library-*），干扰强"),
    dict(q="知网能在校外访问吗？", doc="library-database",
         must=["VPN"], type="trap",
         note="library-database 与 library-space 都讲图书馆服务"),
    dict(q="宿舍几点关门？", doc="dorm-check",
         must=["23:00"], type="trap",
         note="dorm-check 与 dorm-safety、dorm-power 主题相近，都含宿舍规定"),
    dict(q="宿舍东西坏了找谁修？", doc="dorm-facility",
         must=["后勤"], type="trap",
         note="同簇干扰：4 篇 dorm-* 文档"),
    dict(q="宿舍网口怎么用？", doc="dorm-network",
         must=["MAC"], type="trap",
         note="dorm-network 与 network.md（校园网）主题高度重叠，最难的干扰之一"),
    dict(q="大功率电器被查到会怎么样？", doc="dorm-safety",
         must=["处分"], type="multi",
         note="dorm-safety 说处分，dorm-power 说没收并通报批评 —— 需要区分是哪一篇"),
    dict(q="灭火器在哪？", doc="dorm-safety",
         must=["每层"], type="buried",
         note="答案在 dorm-safety.md 中段"),

    # ---------- C. 教学与行政类新文档 ----------
    dict(q="一门课多少人选不上会抽签？", doc="course-select",
         must=["抽签"], type="trap",
         note="course-select 讲选课机制"),
    dict(q="绩点怎么算？", doc="course-grade",
         must=["学分"], type="multi",
         note="course-grade 的 GPA 公式含多个要素"),
    dict(q="实验课缺课多少会挂？", doc="course-practice",
         must=["1/3"], type="buried",
         note="答案在 course-practice.md 第一段"),
    dict(q="毕业设计成绩怎么构成的？", doc="course-practice",
         must=["40%"], type="multi",
         note="course-practice 末尾，含三个百分比。且 graduation.md 也讲毕业设计"),
    dict(q="老师最多能调几次课？", doc="course-teacher",
         must=["3 次"], type="buried",
         note="course-teacher.md 中段"),
    dict(q="在读证明要钱吗？", doc="cert",
         must=["免费"], type="trap",
         note="cert.md 里在读证明免费，但成绩单要钱 —— 混在一起容易答错"),
    dict(q="有事请假最多能请几天？", doc="leave",
         must=["3 天"], type="multi",
         note="leave.md 有审批权限表，事假原则上不超 3 天"),
    dict(q="转专业什么条件？", doc="transfer",
         must=["绩点"], type="multi",
         note="transfer.md 列了三个条件"),
    dict(q="多久能申请入党？", doc="party",
         must=["18"], type="buried",
         note="party.md 第一段「年满 18 周岁」"),
    dict(q="预备党员多久转正？", doc="party",
         must=["1 年"], type="buried",
         note="party.md 末尾"),
    dict(q="食堂卡没钱了去哪充？", doc="canteen-card",
         must=["APP"], type="trap",
         note="canteen-card 与 card.md 都讲校园卡充值，强干扰"),
    dict(q="用校园卡买东西一次最多花多少？", doc="canteen-card",
         must=["50 元"], type="buried",
         note="答案在消费限额段"),
    dict(q="捡到东西交到哪？", doc="lost",
         must=["保卫处"], type="multi",
         note="lost.md 列了四个失物招领点"),
    dict(q="体测不合格会怎么样？", doc="sport",
         must=["不能毕业"], type="buried",
         note="sport.md 中段，且用了加粗强调"),
    dict(q="医保在校外看病能报销吗？", doc="insurance",
         must=["转诊"], type="multi",
         note="insurance.md 讲校外就医需转诊单"),
    dict(q="校医院报销要多久到账？", doc="insurance",
         must=["15"], type="buried",
         note="insurance.md 末尾"),
]


def main():
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        golden = json.load(f)

    existing_qs = {it["question"] for it in golden["items"]}
    start_id = len(golden["items"]) + 1

    added, errors = [], []
    for i, item in enumerate(NEW_ITEMS):
        q, doc_id, must = item["q"], item["doc"], item["must"]

        if q in existing_qs:
            errors.append(f"[{i+1}] 问题重复：{q}")
            continue
        try:
            text = load_doc(doc_id)
        except FileNotFoundError:
            errors.append(f"[{i+1}] {q}\n     源文档不存在：{doc_id}")
            continue
        missing = [m for m in must if m not in text]
        if missing:
            errors.append(f"[{i+1}] {q}\n     文档 {doc_id} 里找不到：{missing}")
            continue

        added.append(dict(
            id=f"q{start_id + len(added):02d}",
            question=q,
            source_doc=doc_id,
            must_contain=must,
            type=item["type"],
            note=item["note"],
        ))

    if errors:
        print("✗ 校验失败，以下题目有问题：\n")
        for e in errors:
            print(f"  {e}\n")
        print("不予写入 —— 错误的评测集比没有评测集更糟。")
        sys.exit(1)

    golden["items"].extend(added)
    golden["total"] = len(golden["items"])
    by_type = {}
    for it in golden["items"]:
        by_type[it["type"]] = by_type.get(it["type"], 0) + 1
    golden["types"] = by_type
    golden["version"] = "2.0"
    golden["description"] = (
        "校园问答 RAG 评测黄金集。每题的答案已在源文档中验证存在。"
        "难度分层：easy/trap/buried/multi。"
    )

    with open(GOLDEN_PATH, "w", encoding="utf-8") as f:
        json.dump(golden, f, ensure_ascii=False, indent=2)

    print(f"✓ 新增 {len(added)} 题，全部通过 ground truth 校验")
    print(f"黄金集总数：{golden['total']} 题")
    print(f"类型分布：{by_type}")

    # 覆盖检查
    all_docs = {f[:-3] for f in os.listdir(DOCS_DIR) if f.endswith(".md")}
    covered = {it["source_doc"] for it in golden["items"]}
    print(f"\n语料覆盖：{len(covered)}/{len(all_docs)} 篇")
    unc = sorted(all_docs - covered)
    if unc:
        print(f"未覆盖（作为干扰项存在）：{', '.join(unc)}")
    print(f"\n已更新：{GOLDEN_PATH}")


if __name__ == "__main__":
    main()
