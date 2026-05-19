@echo off
:: Run the DeepVerse bundled examples (assets\demo1.png + demo3.png).
::
:: Mirrors the two README sample commands:
::   1. demo1.png + "The character rides a horse and walks on the street"  (rgb only)
::   2. demo3.png + "The car is driving slowly in the direction of the road"  (--add_depth --add_ply)
::
:: Prereqs:
::   1. environment_setup.bat has been run (creates .venv + downloads checkpoint/)
::   2. assets\demo1.png and assets\demo3.png present (shipped with the repo)
::
:: Usage:
::   run_examples.bat              run all bundled demos
::   run_examples.bat --demo demo1 single demo only (demo1 | demo3)
::   run_examples.bat --add_ply    pass through to run.py
::
:: Output: ./output/generated_video.mp4 (+ .ply files per demo3)

setlocal enableextensions enabledelayedexpansion
cd /d "%~dp0"

set CKPT=%~dp0checkpoint

:: Python selection (no hard venv assumption):
::   1. DEEPVERSE_PY env var overrides everything (absolute path or command name)
::   2. .venv\Scripts\python.exe if present
::   3. plain `python` on PATH (whatever's active)
if defined DEEPVERSE_PY (
    set PY=%DEEPVERSE_PY%
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set PY=%~dp0.venv\Scripts\python.exe
) else (
    set PY=python
)

if not exist "%CKPT%\transformer" (
    echo ERROR: checkpoint\transformer\ missing.
    echo Run environment_setup.bat ^(or python download.py^) first.
    exit /b 2
)

set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

:: Pick which demos to run (--demo <name> overrides default).
set DEMOS=demo1 demo3
set PASSTHROUGH=
:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--demo" ( set DEMOS=%~2 & shift & shift & goto parse_args )
set PASSTHROUGH=%PASSTHROUGH% %1
shift
goto parse_args
:args_done

echo ============================================================
echo DeepVerse example runner  ^| demos: %DEMOS%
echo ============================================================
echo   python     : %PY%
echo   model_path : %CKPT%
echo   passthrough:%PASSTHROUGH%
echo ============================================================

for %%D in (%DEMOS%) do (
    set "IMG=%~dp0assets\%%D.png"
    if not exist "!IMG!" ( echo ERROR: missing !IMG!  & exit /b 2 )

    if /I "%%D"=="demo1" (
        set "PROMPT=The character rides a horse and walks on the street"
        set "EXTRA="
    ) else if /I "%%D"=="demo3" (
        set "PROMPT=The car is driving slowly in the direction of the road"
        set "EXTRA=--add_depth --add_ply"
    ) else (
        set "PROMPT=Generated DeepVerse sample"
        set "EXTRA="
    )

    echo.
    echo --- %%D ---
    echo prompt: !PROMPT!
    "%PY%" "%~dp0run.py" --input_image "!IMG!" --model_path "%CKPT%" --prompt_type text --prompt "!PROMPT!" !EXTRA!%PASSTHROUGH%
    if errorlevel 1 ( echo FAIL on %%D ^(rc=!ERRORLEVEL!^) & exit /b !ERRORLEVEL! )
)

echo.
echo Done. See output\generated_video.mp4 ^(and .ply files for demo3^).
endlocal
