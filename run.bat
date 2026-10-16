@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=C:\Users\yyy\Documents\deepseek-harness\default-workspace\.venv\Scripts\python.exe

:menu
cls
echo ============================================================
echo                    学习工具台
echo ============================================================
echo.
echo   [1] 看数据长什么样       可视化 chunk_text 的执行过程
echo   [2] 查代码英文读法       输入函数名，看读法和中文意思
echo   [3] 跑 RAG 第 01 课验收   检查你的 TODO 写得对不对
echo.
echo   [0] 退出
echo.
echo ============================================================
set /p choice=输入数字后回车:

if "%choice%"=="1" goto opt1
if "%choice%"=="2" goto opt2
if "%choice%"=="3" goto opt3
if "%choice%"=="0" exit
goto menu

:opt1
cls
"%PY%" "kan-shuju.py"
echo.
echo ---- 跑完了，按任意键返回菜单 ----
pause >nul
goto menu

:opt2
cls
"%PY%" "du-daima.py"
echo.
echo ---- 结束，按任意键返回菜单 ----
pause >nul
goto menu

:opt3
cls
"%PY%" "验收\check_hw01.py"
echo.
echo ---- 结束，按任意键返回菜单 ----
pause >nul
goto menu
