"""
代码英文读法小工具
==================

解决什么问题：
  看到一个函数名不知道该怎么念，也不确定它什么意思。

怎么用：
  在终端里跑这个脚本，把不认识的名字打进去，回车。
  它会：
    1. 用系统语音念出来（英文）
    2. 打印拆解后的单词 + 中文意思

用法：
    # 交互模式（推荐）
    python 读代码.py

    # 直接查一个
    python 读代码.py chunk_text

    # 查多个
    python 读代码.py chunk_text embed_texts cosine_similarity
"""
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# 词库：编程里最常见的词根，按"拆分后能拼出很多东西"排列
# ============================================================
WORDS = {
    # ---- 本作业会用到的 ----
    "chunk": "块、片段（动词：切块）",
    "text": "文本",
    "texts": "文本（复数）",
    "embed": "嵌入（把东西变成向量插进一个空间）",
    "embedding": "嵌入（名词，指那串数字向量）",
    "embs": "embedding 的缩写",
    "cosine": "余弦（数学术语，cos）",
    "similarity": "相似度",
    "sim": "similarity 的缩写",
    "retrieve": "检索、取回",
    "retrieval": "检索（名词）",
    "topk": "top-k，取前 k 个",
    "query": "查询（用户提的问题）",
    "doc": "document 的缩写，文档",
    "document": "文档",
    "docs": "文档（复数）",
    "corpus": "语料库（一堆文档的集合）",
    "golden": "黄金的（golden set = 黄金集，标准答案集）",
    "answer": "回答",
    "token": "词元（模型处理文本的最小单位）",
    "tokens": "词元（复数）",
    "prompt": "提示词（发给模型的话）",
    "api": "接口（A-P-I，字母分开念）",
    "key": "密钥",
    "url": "网址（U-R-L）",
    "json": "一种数据格式（读作 jay-son）",
    "yaml": "一种配置格式（读作 yam-mel）",

    # ---- 常见动作词 ----
    "build": "构建、组装",
    "make": "做、生成",
    "create": "创建",
    "load": "加载、读取",
    "save": "保存",
    "read": "读",
    "write": "写",
    "parse": "解析（把字符串变成程序能用的结构）",
    "format": "格式化",
    "clean": "清理",
    "strip": "剥掉（去掉首尾空白）",
    "split": "分割",
    "join": "连接（把多个拼成一个）",
    "append": "追加（往末尾加）",
    "extend": "扩展（把一个列表的元素都加进另一个）",
    "insert": "插入",
    "remove": "移除",
    "delete": "删除",
    "update": "更新",
    "check": "检查",
    "validate": "校验",
    "verify": "验证",
    "test": "测试",
    "run": "运行",
    "start": "开始",
    "stop": "停止",
    "init": "初始化（initialize 缩写）",
    "execute": "执行",
    "process": "处理",
    "handle": "处理、应对",
    "call": "调用",
    "invoke": "调用（更正式的叫法）",
    "send": "发送",
    "get": "获取",
    "fetch": "抓取、获取",
    "set": "设置",
    "put": "放入",
    "push": "推入（往末尾加）",
    "pop": "弹出（从末尾取出）",
    "merge": "合并",
    "sort": "排序",
    "filter": "过滤",
    "find": "查找",
    "search": "搜索",
    "match": "匹配",
    "replace": "替换",
    "sub": "substitute 缩写，替换",

    # ---- 常见名词 ----
    "data": "数据（读作 day-ta 或 dah-ta 都行）",
    "size": "大小、尺寸",
    "length": "长度（len 是它的缩写）",
    "len": "length 缩写，长度",
    "count": "数量、计数",
    "index": "索引、下标（idx 是缩写）",
    "idx": "index 缩写，下标",
    "item": "项、条目",
    "items": "项（复数）",
    "element": "元素",
    "list": "列表",
    "dict": "dictionary 缩写，字典",
    "array": "数组",
    "string": "字符串（一串文字）",
    "str": "string 缩写，字符串",
    "int": "integer 缩写，整数",
    "float": "浮点数（带小数的数字）",
    "bool": "boolean 缩写，布尔值（真/假）",
    "none": "空、没有（None 表示「什么都没有」）",
    "null": "空值",
    "true": "真",
    "false": "假",
    "result": "结果",
    "res": "result 缩写，结果",
    "output": "输出",
    "input": "输入",
    "param": "参数（parameter 缩写）",
    "parameter": "参数",
    "args": "arguments 缩写，参数们",
    "argument": "参数、实参",
    "option": "选项",
    "config": "配置（configuration 缩写）",
    "setting": "设置",
    "value": "值",
    "val": "value 缩写，值",
    "key": "键（字典里「名字」那一半）",
    "name": "名字",
    "path": "路径",
    "file": "文件",
    "dir": "directory 缩写，目录、文件夹",
    "folder": "文件夹",
    "line": "行",
    "row": "行",
    "col": "column 缩写，列",
    "column": "列",
    "table": "表格",
    "field": "字段",
    "record": "记录",
    "id": "标识（读作 eye-dee，字母分开念）",
    "type": "类型",
    "class": "类",
    "object": "对象",
    "obj": "object 缩写，对象",
    "method": "方法（类里面的函数）",
    "function": "函数",
    "func": "function 缩写，函数",
    "module": "模块",
    "package": "包",
    "library": "库",
    "lib": "library 缩写，库",
    "error": "错误",
    "err": "error 缩写，错误",
    "exception": "异常（一种错误）",
    "warning": "警告",
    "warn": "warning 缩写，警告",
    "message": "消息",
    "msg": "message 缩写，消息",
    "log": "日志",
    "debug": "调试",
    "info": "信息（information 缩写）",
    "status": "状态",
    "state": "状态",
    "level": "级别",
    "mode": "模式",
    "flag": "标志（开关，真/假）",
    "temp": "临时（temporary 缩写）",
    "tmp": "临时",
    "cache": "缓存",
    "buffer": "缓冲区（临时存放数据的地方）",
    "queue": "队列（排队的队伍）",
    "stack": "栈（堆叠）",
    "pool": "池（资源池）",
    "map": "映射（也指「字典」这种结构）",
    "pair": "一对、配对",
    "tuple": "元组",
    "loop": "循环",
    "iterate": "遍历、迭代",
    "iter": "iterate 缩写",
    "range": "范围",
    "step": "步长（每次走多远）",
    "start": "起点",
    "end": "终点",
    "begin": "开始",
    "offset": "偏移量",
    "overlap": "重叠（两部分搭在一起）",
    "limit": "限制、上限",
    "max": "最大（maximum 缩写）",
    "min": "最小（minimum 缩写）",
    "sum": "总和",
    "avg": "average 缩写，平均",
    "total": "总共",
    "rate": "比率、速率",
    "score": "分数",
    "rank": "排名",
    "order": "顺序",
    "sort": "排序",
    "group": "分组",
    "batch": "批（一批处理多个）",
    "bulk": "批量",
    "single": "单个",
    "multi": "多个",
    "all": "全部",
    "any": "任意",
    "none": "没有",
    "empty": "空的",
    "valid": "有效的",
    "invalid": "无效的",
    "default": "默认",
    "custom": "自定义",
    "main": "主要的（程序入口）",
    "core": "核心",
    "base": "基础、基类",
    "sub": "子、下级",
    "sync": "同步（synchronize 缩写）",
    "async": "异步（a-sync）",
    "await": "等待",
    "try": "尝试（用于捕获错误）",
    "except": "除外、捕获（接住错误）",
    "finally": "最终（无论对错都执行）",
    "raise": "抛出（主动报错）",
    "throw": "抛出（其他语言的说法）",
    "catch": "捕获（接住错误）",
    "assert": "断言（我确信这是真的）",

    # ---- RAG / 模型相关 ----
    "rag": "检索增强生成（R-A-G，字母分开念）",
    "llm": "大语言模型（L-L-M）",
    "chaos": "混沌",
    "fine": "微调（fine-tune）",
    "tune": "调",
    "lora": "低秩适配（一种省显存的微调方法）",
    "epoch": "轮次（训练时把数据过一遍）",
    "loss": "损失（模型错得多离谱的度量）",
    "grad": "gradient 缩写，梯度",
    "vector": "向量（一串数字）",
    "vectors": "向量（复数）",
    "dim": "dimension 缩写，维度",
    "dimension": "维度",
    "norm": "范数（向量的长度）",
    "dot": "点积（两两相乘再相加）",
    "prod": "product 缩写，积",
    "product": "积",
    "matrix": "矩阵",
    "agent": "智能体（读作 ay-jent）",
    "tool": "工具",
    "tools": "工具（复数）",
    "loop": "循环",
    "trace": "追踪（记录每一步）",
    "span": "跨度、片段",
    "eval": "评估（evaluate 缩写）",
    "score": "分数",
    "metric": "指标",
    "hit": "命中",
    "miss": "未命中",
    "recall": "召回（该找到的找到了多少）",
    "precision": "精确度（找到的里面有多少是对的）",
    "accuracy": "准确率",
    "f1": "F1 分数（精确和召回的调和平均）",
    "baseline": "基线（改动前的水平，用来对比）",
    "benchmark": "基准测试",
    "regression": "回归（也指「改坏了以前好的功能」）",
}


def speak(text):
    """用系统语音念出来（Windows 自带，无需装东西）。"""
    try:
        ps = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Rate = -2; "
            f'$s.Speak("{text}");'
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, timeout=20)
        return True
    except Exception:
        return False


def split_name(name):
    """把 chunk_text / cosineSimilarity / getWeather 拆成单词。"""
    # 先按非字母分割
    parts = re.split(r"[^A-Za-z]+", name)
    out = []
    for p in parts:
        if not p:
            continue
        # camelCase / PascalCase 拆分
        pieces = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[A-Z]", p)
        out.extend(pieces if pieces else [p])
    return [w for w in out if w]


def explain(name):
    """解释一个名字。"""
    parts = split_name(name)
    if not parts:
        print(f"  （看不懂这个名字：{name}）")
        return

    # 念法
    spoken = " ".join(parts)
    print(f"  {name}")
    print(f"    读法：{' · '.join(parts)}")
    speak(spoken)

    # 逐词解释
    hit_any = False
    for w in parts:
        low = w.lower()
        if low in WORDS:
            print(f"      {w:16} {WORDS[low]}")
            hit_any = True
        else:
            print(f"      {w:16} （词库里没有，可能是缩写或变量名）")
    if not hit_any:
        print("      → 词库里没找到，可能是你自己起的名字")


def main():
    print("=" * 66)
    print("代码英文读法小工具")
    print("=" * 66)
    print("输入英文名（可空格分隔多个），回车查看。直接回车退出。")
    print("例：chunk_text    cosine_similarity    retrieve")
    print()

    # 命令行直接传参
    args = [a for a in sys.argv[1:] if a.strip()]
    if args:
        for a in args:
            explain(a)
            print()
        return

    # 交互模式
    while True:
        try:
            line = input("查什么 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            break
        for name in line.split():
            explain(name)
            print()


if __name__ == "__main__":
    main()
