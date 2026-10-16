"""
第 01 课验收脚本
================

用法：
    cd rag-qa
    C:\\Users\\yyy\\Documents\\deepseek-harness\\default-workspace\\.venv\\Scripts\\python.exe 验收\\check_hw01.py

8 项检查，全 PASS 才算过。

⚠ 第 6 项会跑完整评测（48 题），需要调 API 约 48 次，预计 2-4 分钟。
   成本约 0.02 元（这是评测闭环能成立的前提：跑一轮要便宜到可以反复跑）。
"""

import importlib.util
import json
import os
import sys
import time
import traceback

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HW_PATH = os.path.join(ROOT, "作业", "hw01_naive_rag.py")

PASSED, FAILED = [], []


def ok(n, title, detail=""):
    PASSED.append(n)
    print(f"  [PASS] {n}. {title}" + (f"\n         {detail}" if detail else ""))


def fail(n, title, detail=""):
    FAILED.append(n)
    print(f"  [FAIL] {n}. {title}" + (f"\n         {detail}" if detail else ""))


def load_homework():
    if not os.path.exists(HW_PATH):
        print(f"找不到作业文件：{HW_PATH}")
        sys.exit(2)
    spec = importlib.util.spec_from_file_location("hw01", HW_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    print("=" * 74)
    print("第 01 课验收：从零实现朴素 RAG")
    print(f"作业文件：{HW_PATH}")
    print("=" * 74)
    print()

    hw = load_homework()
    if not hw.CHAT_KEY or not hw.EMB_KEY:
        print("！.env 里没读到 API key，检查 rag-qa\\.env")
        sys.exit(2)
    print(f"生成模型：{hw.CHAT_MODEL}")
    print(f"向量模型：{hw.EMB_MODEL}（{hw.EMB_DIM} 维）")
    print()

    # ---------- 1. chunk_text ----------
    print("【1】chunk_text：切分正确、有重叠、不丢尾巴")
    try:
        sample = "A" * 500
        cs = hw.chunk_text(sample, "test", size=200, overlap=50)
        assert isinstance(cs, list) and cs, "应返回非空列表"
        assert all(c["doc_id"] == "test" for c in cs), "doc_id 不对"
        assert all(len(c["text"]) <= 200 for c in cs), "有块超过 size"
        assert len({c["chunk_id"] for c in cs}) == len(cs), "chunk_id 重复"
        # 步长 150，500 字符 → 起始位置 0,150,300,450 → 4 块
        assert len(cs) == 4, f"500 字符按 size=200/overlap=50 应切出 4 块，实际 {len(cs)}"
        # overlap 校验：第 1 块尾部 50 字符应等于第 2 块首部 50 字符
        a = cs[0]["text"][-50:]
        b = cs[1]["text"][:50]
        assert a == b, "块之间没有正确重叠"
        # 空输入
        assert hw.chunk_text("", "x") == [], "空文本应返回空列表"
        assert hw.chunk_text("   ", "x") == [], "纯空白应返回空列表"
        # overlap >= size 要防死循环
        try:
            hw.chunk_text("A" * 300, "x", size=100, overlap=100)
            fail(1, "切分正确", "overlap >= size 时没有报错（会导致死循环）")
        except ValueError:
            ok(1, "切分正确", f"500 字符切出 {len(cs)} 块，重叠验证通过，overlap>=size 有防护")
    except NotImplementedError:
        fail(1, "切分正确", "TODO 1 还没写")
    except Exception as e:
        fail(1, "切分正确", f"{type(e).__name__}: {e}")

    # ---------- 2. embed_texts ----------
    print("【2】embed_texts：批量调用、维度正确、顺序一致")
    try:
        texts = ["图书馆开放时间", "食堂营业信息", "校园网费用标准"]
        vecs = hw.embed_texts(texts)
        assert isinstance(vecs, list), "应返回 list"
        assert len(vecs) == len(texts), f"返回 {len(vecs)} 个向量，应 {len(texts)} 个"
        for v in vecs:
            assert isinstance(v, list), "每个向量应是 list"
            assert len(v) == hw.EMB_DIM, f"维度应为 {hw.EMB_DIM}，实际 {len(v)}"
        # 顺序一致性：同样的文本单独 embed，结果应几乎相同
        single = hw.embed_texts(["图书馆开放时间"])[0]
        diff = max(abs(a - b) for a, b in zip(single, vecs[0]))
        assert diff < 1e-6, f"批量与单条结果不一致（差 {diff}），顺序可能错乱"
        # 空输入
        assert hw.embed_texts([]) == [], "空输入应返回空列表"
        ok(2, "向量化正确", f"{len(vecs)} 个 {hw.EMB_DIM} 维向量，顺序一致")
    except NotImplementedError:
        fail(2, "向量化正确", "TODO 2 还没写")
    except Exception as e:
        fail(2, "向量化正确", f"{type(e).__name__}: {e}")

    # ---------- 3. cosine_similarity ----------
    print("【3】cosine_similarity：手写实现正确（含零模长边界）")
    try:
        # 自己就是自己 → 1.0
        v = [1.0, 2.0, 3.0]
        assert abs(hw.cosine_similarity(v, v) - 1.0) < 1e-9, "相同向量应得 1.0"
        # 正交 → 0
        assert abs(hw.cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-9, "正交应得 0"
        # 反向 → -1
        assert abs(hw.cosine_similarity([1.0, 0.0], [-1.0, 0.0]) + 1.0) < 1e-9, "反向应得 -1"
        # 缩放不变性（这是余弦的定义性质）
        a = [1.0, 2.0, 3.0]
        b = [2.0, 4.0, 6.0]          # b = 2a
        assert abs(hw.cosine_similarity(a, b) - 1.0) < 1e-9, "同方向不同长度应得 1.0"
        # 零模长（必考边界）
        assert hw.cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0, "零向量应返回 0.0，不能除零"
        # 长度不一致
        try:
            hw.cosine_similarity([1.0], [1.0, 2.0])
            fail(3, "余弦相似度", "长度不一致时没抛 ValueError")
        except ValueError:
            ok(3, "余弦相似度正确", "含缩放不变性、正交、反向、零模长边界")
    except NotImplementedError:
        fail(3, "余弦相似度", "TODO 3 还没写")
    except ZeroDivisionError as e:
        fail(3, "余弦相似度", f"除零了 —— 零模长没防护：{e}")
    except Exception as e:
        fail(3, "余弦相似度", f"{type(e).__name__}: {e}")

    # ---------- 4. retrieve ----------
    print("【4】retrieve：返回按分数降序的 top_k")
    try:
        corpus = hw.load_corpus()
        chunks = []
        for doc in corpus[:5]:
            chunks.extend(hw.chunk_text(doc["text"], doc["doc_id"]))
        vecs = hw.embed_texts([c["text"] for c in chunks])

        ret = hw.retrieve("图书馆开放时间", chunks, vecs, top_k=3)
        assert len(ret) == 3, f"应返回 3 个，实际 {len(ret)}"
        scores = [r["score"] for r in ret]
        assert scores == sorted(scores, reverse=True), f"未按分数降序：{scores}"
        for r in ret:
            for k in ("doc_id", "text", "score"):
                assert k in r, f"缺少字段 {k}"
        assert all(isinstance(r["score"], float) for r in ret), "score 应是 float"
        # top_k 超过总数时不应报错
        many = hw.retrieve("图书馆", chunks, vecs, top_k=999)
        assert len(many) == len(chunks), "top_k 超过总数时应返回全部"
        # 长度不一致要报错
        try:
            hw.retrieve("x", chunks, vecs[:-1], top_k=1)
            fail(4, "检索逻辑", "chunks 与向量数量不匹配时没抛 ValueError")
        except ValueError:
            ok(4, "检索逻辑正确", f"top3 分数降序 = {[round(s, 3) for s in scores]}")
    except NotImplementedError:
        fail(4, "检索逻辑", "TODO 4 还没写")
    except Exception as e:
        fail(4, "检索逻辑", f"{type(e).__name__}: {e}")

    # ---------- 5. 端到端 ----------
    print("【5】端到端：单问单答能通")
    try:
        corpus = hw.load_corpus()
        chunks = []
        for doc in corpus:
            chunks.extend(hw.chunk_text(doc["text"], doc["doc_id"]))
        vecs = hw.embed_texts([c["text"] for c in chunks])
        ret = hw.retrieve("图书馆周末几点开门？", chunks, vecs, top_k=3)
        ans = hw.answer("图书馆周末几点开门？", ret)
        assert isinstance(ans, str), "answer 应返回 str"
        assert ans.strip(), "answer 返回了空字符串"
        assert "09:00" in ans or "21:00" in ans, f"答案里没有正确时间：{ans[:80]!r}"
        ok(5, "端到端通了", f"回答：{ans[:70]!r}")
    except NotImplementedError:
        fail(5, "端到端", "TODO 5 还没写")
    except Exception as e:
        fail(5, "端到端", f"{type(e).__name__}: {e}")

    # ---------- 6. 完整评测（核心）----------
    print("【6】跑完整评测 —— 输出两个核心指标")
    print("      （48 题，预计 2-4 分钟，成本约 0.02 元）")
    result = None
    try:
        t0 = time.time()
        result = hw.evaluate(verbose=False)
        elapsed = time.time() - t0
        assert "hit_rate" in result and "accuracy" in result, "返回值缺 hit_rate/accuracy"
        assert 0.0 <= result["hit_rate"] <= 1.0, f"hit_rate 超范围：{result['hit_rate']}"
        assert 0.0 <= result["accuracy"] <= 1.0, f"accuracy 超范围：{result['accuracy']}"
        assert result["total"] >= 40, f"只评了 {result['total']} 题，黄金集应有 48 题"

        top1 = result.get("top1_rate")
        top1_txt = f"{top1:.1%}" if top1 is not None else "（未统计）"
        ok(6, "完整评测跑通",
           f"耗时 {elapsed:.0f}s\n"
           f"         检索命中率 top3： {result['hit_rate']:.1%}  ({result['hits']}/{result['total']})\n"
           f"         检索命中率 top1： {top1_txt}\n"
           f"         答案准确率：       {result['accuracy']:.1%}  ({result['correct']}/{result['total']})")
    except NotImplementedError:
        fail(6, "完整评测", "TODO 还没写完")
    except Exception as e:
        fail(6, "完整评测", f"{type(e).__name__}: {e}")

    # ---------- 7. baseline 下限 ----------
    print("【7】baseline 下限检查（朴素方法不能太烂）")
    if result:
        hr, acc = result["hit_rate"], result["accuracy"]
        if hr >= 0.80 and acc >= 0.70:
            ok(7, "baseline 达标",
               f"top3={hr:.1%}（阈值 80%）、准确率={acc:.1%}（阈值 70%）\n"
               f"         ⚠️ 这两个数就是后面所有优化的对比基准，记下来")
        else:
            fail(7, "baseline 达标",
                 f"top3={hr:.1%}（应 ≥80%）、准确率={acc:.1%}（应 ≥70%）\n"
                 f"         太低了，检查切分和检索实现")
    else:
        fail(7, "baseline 达标", "跳过：第 6 项没通过")

    # ---------- 8. 找不到就说找不到 ----------
    print("【8】资料里没有的问题，不能编造")
    try:
        corpus = hw.load_corpus()
        chunks = []
        for doc in corpus:
            chunks.extend(hw.chunk_text(doc["text"], doc["doc_id"]))
        vecs = hw.embed_texts([c["text"] for c in chunks])
        q = "学校游泳池的水温是多少度？"      # 语料里没有这个信息
        ret = hw.retrieve(q, chunks, vecs, top_k=3)
        ans = hw.answer(q, ret)
        # 允许的表述
        denial_markers = ["没有", "未", "无法", "不清楚", "找不到", "未提及", "不详"]
        denied = any(m in ans for m in denial_markers)
        if denied:
            ok(8, "不编造（有拒答）", f"回答：{ans[:70]!r}")
        else:
            fail(8, "不编造",
                 f"语料里没有这个问题，但模型没拒答，而是给了具体答案：\n"
                 f"         {ans[:100]!r}\n"
                 f"         检查 answer() 的 prompt 里有没有「找不到就说找不到」")
    except NotImplementedError:
        fail(8, "不编造", "TODO 5 还没写")
    except Exception as e:
        fail(8, "不编造", f"{type(e).__name__}: {e}")

    # ---------- 汇总 ----------
    print()
    print("=" * 74)
    print(f"结果：{len(PASSED)}/8 通过")
    if FAILED:
        print(f"未通过：{FAILED}")
        print()
        print("下一步：按提示改 作业\\hw01_naive_rag.py，改完重跑。")
        print("卡住超过 20 分钟把报错贴给我，我给提示不给答案。")
        sys.exit(1)
    else:
        print("全部通过 ✓")
        print()
        if result:
            print("★ 你的 baseline（记住这两个数，它们是后面所有优化的对比基准）：")
            print(f"    检索命中率 top3：{result['hit_rate']:.1%}")
            print(f"    答案准确率：      {result['accuracy']:.1%}")
            if result.get("top1_rate") is not None:
                print(f"    检索命中率 top1： {result['top1_rate']:.1%}  ← 改进空间主要在这")
            print()
            print("★ 接下来：看失败案例（运行作业文件末尾的自测），")
            print("   找出哪些是「检索没召回」、哪些是「召回了但答错」——")
            print("   这两类的修法完全不同。")
            print()
        print("然后回答讲义最后的三个追问（Q1/Q2/Q3）。")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        print()
        print("验收脚本自己炸了：")
        traceback.print_exc()
        sys.exit(2)
