"""
学习工具台
==========

为什么用 Python 写菜单而不是 bat：
  bat 文件在中文 Windows 上有编码地狱（GBK / UTF-8 / chcp 混在一起就乱码），
  而 Python 处理中文没问题。所以 bat 只负责"启动"，菜单逻辑全在这里。

用法：
  双击 rag-qa 目录下的 run.bat（推荐）
  或在终端跑：python 工具台.py
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PY = r"C:\Users\yyy\Documents\deepseek-harness\default-workspace\.venv\Scripts\python.exe"

MENU = """
============================================================
                   学习工具台
============================================================

  【看代码】
  [1] 看数据长什么样      可视化 chunk_text 的执行过程
  [2] 逐个符号验算        用真实数字演示 != len raise f"" zip sum 等
  [3] 五个函数的数据流    看清「卡片是文字、向量是数字」
  [4] 角度 vs 距离        为什么 RAG 用余弦相似度而不是欧氏距离

  【查与测】
  [5] 查代码英文读法      输入函数名，看读法和中文意思
  [6] 跑 RAG 第 01 课验收  检查你的 TODO 写得对不对

  【文档】
  [7] 打开逐行讲解        用记事本打开 chunk_text 的逐符号讲解

  [0] 退出

============================================================
"""


def run_script(relpath, argv=None):
    """在项目目录下跑一个脚本。"""
    path = os.path.join(HERE, relpath)
    if not os.path.exists(path):
        print(f"\n！找不到文件：{relpath}")
        print(f"  期望位置：{path}")
        return
    cmd = [PY, path] + (argv or [])
    try:
        subprocess.run(cmd, cwd=HERE)
    except Exception as e:
        print(f"\n！运行出错：{e}")


def main():
    while True:
        print(MENU)
        try:
            choice = input("输入数字后回车（直接回车=退出）> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("", "0", "q", "Q"):
            break

        if choice == "1":
            print("\n" + "=" * 60)
            print("看数据长什么样 —— 可视化 chunk_text 的执行过程")
            print("=" * 60 + "\n")
            run_script("kan-shuju.py")

        elif choice == "2":
            print("\n" + "=" * 60)
            print("逐个符号验算 —— 用真实数字演示每个符号")
            print("=" * 60 + "\n")
            run_script("yan-suan.py")

        elif choice == "3":
            print("\n" + "=" * 60)
            print("五个函数的数据流 —— 卡片是文字，向量是数字")
            print("=" * 60 + "\n")
            run_script("wu-bu.py")

        elif choice == "4":
            print("\n" + "=" * 60)
            print("角度 vs 距离 —— 为什么用余弦相似度")
            print("=" * 60 + "\n")
            run_script("jiao-du-vs-ju-li.py")

        elif choice == "5":
            print("\n" + "=" * 60)
            print("查代码英文读法")
            print("=" * 60)
            print("\n可以直接打函数名（空格分隔多个），例如：")
            print("  chunk_text  cosine_similarity  retrieve")
            print("（直接回车返回菜单）\n")
            try:
                line = input("查什么 > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                continue
            if line:
                run_script("du-daima.py", line.split())

        elif choice == "6":
            print("\n" + "=" * 60)
            print("RAG 第 01 课验收（8 项检查）")
            print("=" * 60 + "\n")
            run_script(os.path.join("验收", "check_hw01.py"))

        elif choice == "7":
            doc = os.path.join(HERE, "逐行读懂-chunk_text.md")
            if os.path.exists(doc):
                print(f"\n正在打开：{doc}")
                os.startfile(doc)
            else:
                print(f"\n！找不到 {doc}")

        else:
            print(f"\n！没有 [{choice}] 这个选项")

        print("\n" + "-" * 60)
        input("按回车返回菜单...")


if __name__ == "__main__":
    main()
