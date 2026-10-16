"""
逐个符号验算：用真实数字让你看到它们到底在干什么
================================================

为什么做这个：
  你说「!= 忘记了」「raise 忘记了」「f 字符串忘记了」...
  但对比 chunk_text 那次，这些符号你其实见过 —— 说明不是"忘了"，
  而是**没形成稳定的记忆**。看真实数字跑一遍，比看文字解释有效。

这不是讲义，是"实验记录"。每一条都能自己验证。
"""
import math
import sys

sys.stdout.reconfigure(encoding="utf-8")

# 用真实的数字，别用抽象的 a、b
A = [1.0, 2.0, 3.0]
B = [4.0, 5.0, 6.0]


def head(n, title):
    print()
    print("-" * 68)
    print(f"{n}  {title}")
    print("-" * 68)


print("=" * 68)
print("逐个符号验算")
print("=" * 68)
print(f"\n先记住这两个向量：")
print(f"    a = {A}")
print(f"    b = {B}")

# ============================================================
head("①", "!=   不等于")

print(f"    a != b   →  {A != B}")
print(f"    1 != 2   →  {1 != 2}")
print(f"    2 != 2   →  {2 != 2}")
print()
print("    三个等于号，意思完全不同：")
print("        x = 5     单个 =  → 把 5 存进 x（赋值）")
print("        x == 5    双个 =  → 问「x 等于 5 吗」（判断）")
print("        x != 5    一个 ! → 问「x 不等于 5 吗」（判断）")

# ============================================================
head("②", "len()   数一数有几个东西")

print(f'    len(a)         →  {len(A)}')
print(f'    len([9, 8, 7])  →  {len([9, 8, 7])}')
print(f'    len("abc")     →  {len("abc")}')
print()
print("    你答的「算括号里面的字符长度」——对了一半：")
print("        对列表：数「有几个元素」")
print("        对字符串：数「有几个字符」")
print(f'        len("图书馆") = {len("图书馆")}  （3 个汉字算 3）')

# ============================================================
head("③", "raise   主动报错（程序当场停下）")

print("    执行到 raise，程序立刻中断，并把消息打出来。")
print()
try:
    raise ValueError("这就是报错的样子")
except ValueError as e:
    print(f"    实际效果 → ValueError: {e}")
print()
print("    raise  vs  return 的区别（你之前混淆过）：")
print("        return 0.0        → 正常结束，交出一个结果")
print("        raise ValueError  → 异常结束，程序报错停下")

# ============================================================
head("④", 'f"..."   f-string，把变量塞进文字里')

la, lb = 3, 4
msg = f"a 有 {la} 个, b 有 {lb} 个"
print(f'    代码：f"a 有 {{la}} 个, b 有 {{lb}} 个"')
print(f"    结果：{msg}")
print()
print("    记忆点：字母 f 开头 = format（格式化）")
print("    花括号 {} 里的东西会被**替换成它的值**")
print()
print(f'    对比：不加 f 就是普通文字 → "a 有 {{la}} 个"')

# ============================================================
head("⑤", "zip()   像拉链一样，把两个列表配成对")

pairs = list(zip(A, B))
print(f"    a = {A}")
print(f"    b = {B}")
print(f"    list(zip(a, b))  →  {pairs}")
print()
print("    像拉链齿咬合：第 1 个配第 1 个，第 2 个配第 2 个...")

# ============================================================
head("⑥", "x * y for x, y in zip(a, b)   生成器表达式")

print("    拆开读（从右往左）：")
print(f"    1. zip(a, b)       → 先配对：{pairs}")
print("    2. for x, y in ... → 每轮取出一对")
print("         第 1 轮：x=1.0, y=4.0")
print("         第 2 轮：x=2.0, y=5.0")
print("         第 3 轮：x=3.0, y=6.0")
print("    3. x * y           → 乘起来")
print()
prods = [x * y for x, y in zip(A, B)]
print(f"    每轮结果：{prods}")
print(f"           = [1×4, 2×5, 3×6]")
print(f"           = {prods}")

# ============================================================
head("⑦", "sum()   把一列数加起来")

print(f"    要加的是：{prods}")
print(f"    sum({prods})  →  {sum(prods)}")
print(f"    手算：1×4 + 2×5 + 3×6 = 4 + 10 + 18 = {4+10+18}")
print()
print("    ★ 所以第 148 行整句：")
print("        dot = sum(x * y for x, y in zip(a, b))")
print(f"            = {sum(prods)}")
print("        这就是「点积」—— 两两相乘，再全部加起来")

# ============================================================
head("⑧", "math.sqrt()   square root，平方根")

print(f"    math.sqrt(9)   →  {math.sqrt(9)}      （因为 3×3=9）")
print(f"    math.sqrt(16)  →  {math.sqrt(16)}      （因为 4×4=16）")
print("    ✅ 你答对了")

# ============================================================
head("⑨", "x * x for x in a   每个元素自己乘自己")

print(f"    a = {A}")
print("    拆开读：")
print("        for x in a  → 每轮取一个元素：1.0，然后 2.0，然后 3.0")
print("        x * x       → 自己乘自己")
print()
sqs = [x * x for x in A]
print(f"    每轮结果：{sqs}")
print(f"           = [1×1, 2×2, 3×3] = {sqs}")
print()
print("    再看套上 sum 和 sqrt：")
print(f"        sum({sqs}) = {sum(sqs)}")
print(f"        math.sqrt({sum(sqs)}) = {math.sqrt(sum(sqs)):.4f}")
print()
print("    ★ 所以第 149 行：")
print("        na = math.sqrt(sum(x * x for x in a))")
print("        读作：把 a 的每个元素平方 → 加起来 → 再开方")
print("        这就是「模长」（向量的长度）")
print()
print("    为什么是「平方再开方」？")
print("        这就是勾股定理：√(x² + y²)")
print(f"        三维就是 √(1² + 2² + 3²) = √14 = {math.sqrt(14):.4f}")

# ============================================================
head("⑩", "if na == 0.0 or nb == 0.0:   防止除以零")

print('    == 是「判断相等」')
print(f"        0.0 == 0.0  →  {0.0 == 0.0}   （真）")
print(f"        1.0 == 0.0  →  {1.0 == 0.0}   （假）")
print()
print("    or 你已经答对了：前面为真就真，否则看后面")
print()
print("    为什么要检查零？因为下一步要除以 na 和 nb：")
try:
    _ = 1 / 0
except ZeroDivisionError as e:
    print(f"        如果 na=0，dot / (na * nb) 会 → ZeroDivisionError: {e}")
print("    所以先检查，遇到零就提前交个 0.0 回去")

# ============================================================
head("⑪", "dot / (na * nb)   除法 → 这就是余弦相似度")

dot = sum(prods)
na = math.sqrt(sum(x * x for x in A))
nb = math.sqrt(sum(y * y for y in B))

print(f"    dot = {dot}")
print(f"    na  = √14 = {na:.4f}")
print(f"    nb  = √77 = {nb:.4f}")
print()
print(f"    dot / (na * nb) = {dot} / ({na:.4f} × {nb:.4f})")
print(f"                    = {dot} / {na * nb:.4f}")
print(f"                    = {dot / (na * nb):.4f}")
print()
print("    ★ 这个数就是「a 和 b 有多像」")
print("       接近 1  = 非常像")
print("       接近 0  = 无关")
print("       接近 -1 = 意思相反")

# ============================================================
print()
print("=" * 68)
print("最后：验证一个你自己就能做的测试")
print("=" * 68)
print()
c = [2.0, 4.0, 6.0]   # c 正好是 a 的 2 倍
print(f"    a = {A}")
print(f"    c = {c}   ← c 的每个数都是 a 的 2 倍")
print()
dot_ac = sum(x * y for x, y in zip(A, c))
na_ = math.sqrt(sum(x * x for x in A))
nc_ = math.sqrt(sum(x * x for x in c))
sim = dot_ac / (na_ * nc_)
print(f"    算出来的相似度 = {sim:.4f}")
print()
print("    ★ 结果是 1.0 —— 尽管 a 和 c 的数值完全不同！")
print("      因为余弦只看「方向」，不看「长短」。")
print("      这就是为什么它能用来判断语义相似：")
print("      长句和短句只要意思一样，方向就一样。")
