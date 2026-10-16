"""
看数据长什么样：chunk_text 执行过程可视化
==========================================

为什么做这个：
  你答对了「从 start 取 size 个字符」这种单步操作，
  但答不准「chunks 是盒子还是动作」「加到哪」。
  这说明你缺的不是概念，是**数据在内存里长什么样的具象感**。

这个脚本做的事：
  不真的调 API，只是把 chunk_text 的逻辑跑一遍，
  每走一步就把变量的样子打印出来 —— 让你**看见**数据怎么变。

用法：
    python 看数据长什么样.py
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def show_box(title, value, note=""):
    """把变量打印成一个盒子。"""
    print(f"\n  ┌─ {title} " + "─" * max(0, 50 - len(title)))
    if isinstance(value, list):
        if not value:
            print("  │  【空盒子】 这就是 []，里面什么都没有")
        else:
            print(f"  │  里面装了 {len(value)} 样东西：")
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    print(f"  │    第 {i} 个（一个字典，带 3 个标签）：")
                    for k, v in item.items():
                        vs = str(v)
                        if len(vs) > 34:
                            vs = vs[:34] + "..."
                        print(f"  │        \"{k}\" → {vs}")
                else:
                    print(f"  │    第 {i} 个: {item}")
    else:
        s = str(value)
        if len(s) > 60:
            s = s[:60] + "..."
        print(f"  │  {s}")
    if note:
        print(f"  │  💡 {note}")
    print("  └" + "─" * 52)


def chunk_text_with_show(text, doc_id, size=60, overlap=20, max_rounds=4):
    """和参考实现同样的逻辑，但每步打印出来。

    size/overlap 特意调小，方便在屏幕上演示。
    """
    print("=" * 70)
    print("准备阶段")
    print("=" * 70)

    print(f"\n原始文章（{len(text)} 字）：")
    print(f'  "{text[:70]}..."' if len(text) > 70 else f'  "{text}"')

    # ---- 第 2-3 行：空值检查 ----
    print("\n" + "─" * 70)
    print("步骤 1：检查是不是空文章")
    print("─" * 70)
    print(f'  问：if not text or not text.strip()')
    print(f'  答：text 有内容 → 条件为假 → 不执行 return []，继续往下')
    if not text or not text.strip():
        print("  （如果是空文章，这里就 return [] 了，后面都不执行）")
        return []

    # ---- 第 4-5 行：参数检查 ----
    print("\n" + "─" * 70)
    print("步骤 2：检查 overlap 和 size 的关系")
    print("─" * 70)
    print(f"  overlap={overlap}, size={size}")
    print(f"  问：overlap >= size 吗？")
    print(f"  答：{overlap} >= {size} 是假 → 不报错，继续")

    # ---- 第 6-7 行：清理 ----
    print("\n" + "─" * 70)
    print("步骤 3：清理空白")
    print("─" * 70)
    cleaned = re.sub(r"\n\s*\n+", "\n", text.strip())
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    print(f"  处理前 {len(text)} 字 → 处理后 {len(cleaned)} 字")

    # ---- 第 8 行：步长 ----
    print("\n" + "─" * 70)
    print("步骤 4：算步长")
    print("─" * 70)
    step = size - overlap
    print(f"  step = size - overlap = {size} - {overlap} = {step}")
    print(f"  意思：每切完一张卡片，往后走 {step} 个字")

    # ---- 第 9-11 行：三个变量 ----
    print("\n" + "─" * 70)
    print("步骤 5：准备三个变量（重点看这个！）")
    print("─" * 70)

    chunks = []
    start = 0
    idx = 0

    show_box("chunks（空盒子）", chunks,
             "这是「装结果的盒子」。现在它是空的，等着被装东西")
    show_box("start = 0", start, "记录「现在切到文章的哪个位置」")
    show_box("idx = 0", idx, "记录「已经切出第几张卡片」，用来编号")

    # ---- 循环 ----
    print("\n" + "=" * 70)
    print("开始循环（重点：看 chunks 怎么从空盒子变成满盒子）")
    print("=" * 70)

    round_no = 0
    while start < len(cleaned):
        round_no += 1
        print(f"\n{'━' * 70}")
        print(f"第 {round_no} 轮循环")
        print(f"{'━' * 70}")

        print(f"\n  ① 判断：start < len(cleaned) ？")
        print(f"     {start} < {len(cleaned)} → 真，进入循环体")

        # 切片
        piece = cleaned[start:start + size].strip()
        print(f"\n  ② 切一刀：cleaned[{start}:{start + size}]")
        print(f"     从第 {start} 个字开始，取 {size} 个")
        pshow = piece if len(piece) <= 46 else piece[:46] + "..."
        print(f"     切出来：\"{pshow}\"")
        print(f"     （外面还套了 .strip() 去掉首尾空白）")

        # 判断非空
        print(f"\n  ③ 判断：if piece:  —— piece 不是空的吗？")
        if piece:
            print(f"     piece 有内容 → 真 → 执行 if 里面的两句")

            # append
            new_card = {
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}#{idx}",
                "text": piece,
            }
            print(f"\n  ④ chunks.append({{...}})  ← 你答「加字典」，对，但要看加到哪")
            print(f"     往 chunks 这个盒子的**末尾**，加进去一个字典：")
            print(f"        \"doc_id\"   → \"{doc_id}\"")
            print(f"        \"chunk_id\" → \"{doc_id}#{idx}\"")
            pv = piece if len(piece) <= 30 else piece[:30] + "..."
            print(f"        \"text\"     → \"{pv}\"")
            chunks.append(new_card)

            show_box(f"现在 chunks 长这样（{len(chunks)} 张卡片）", chunks)

            idx += 1
            print(f"\n  ⑤ idx += 1   →  idx 现在是 {idx}")
            print(f"     （编号 +1，下一张卡片会是 #{idx}）")
        else:
            print(f"     piece 是空的 → 假 → 跳过 if，不装卡片、编号也不动")

        start += step
        print(f"\n  ⑥ start += step  →  start 现在是 {start}")
        print(f"     （往后挪 {step} 格，准备切下一张）")

        if round_no >= max_rounds:
            print(f"\n  ...（演示到此为止，后面同理）...")
            break

    # ---- return ----
    print("\n" + "=" * 70)
    print("循环结束 → return chunks")
    print("=" * 70)

    show_box("最终结果", chunks, "这个盒子被交给调用者：cards = chunk_text(...)")

    return chunks


def main():
    print()
    print("★ 这份脚本的目的：让你「看见」数据长什么样，而不只是「知道」它在干什么")
    print()

    # 用真实项目的语料
    sample = (
        "图书馆开放时间安排如下：\n"
        "周一至周五：08:00 - 22:00\n"
        "周六至周日：09:00 - 21:00\n"
        "\n\n\n"
        "闭馆前 30 分钟停止借还书服务。"
    )

    chunk_text_with_show(sample, "library-hours", size=60, overlap=20)

    print("\n\n" + "=" * 70)
    print("现在自测：用刚才看到的画面，回答这 5 个问题")
    print("=" * 70)
    print("""
  1. chunks = [] 是干什么的？
     （提示：注意它是空的时候长什么样，谁往里面装东西）

  2. if not text or not text.strip() 在检查什么？
     （提示：什么样的情况会让它执行 return []）

  3. cleaned[start:start + size] 取出来的是什么？
     （提示：看第 1 轮循环的「② 切一刀」）

  4. chunks.append({...}) 做了什么？
     （提示：看「④」那一段，注意是往哪个盒子的什么位置加，
       以及加进去的东西有几层结构）

  5. return chunks 是谁给谁？
     （提示：看最后那个「最终结果」框下面的那句话）

  ─────────────────────────────────────────
  5 个都能用自己的话说出来 → 这个函数你就读懂了。
  读完把答案发我，我告诉你哪对哪错。

  💡 想查不认识的英文词，回菜单按 [2]
""")


if __name__ == "__main__":
    main()
