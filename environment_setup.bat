@echo off
:: DeepVerse environment setup + model download (Windows).
::
:: Mirrors the README install steps using uv instead of conda:
::   1. Creates .venv with Python 3.10
::   2. Installs torch 2.4.0 / torchvision 0.19.0 from the PyTorch cu121 index
::   3. pip-installs requirements.txt
::   4. Snapshots SOTAMak1r/DeepVerse1.1 weights into .\checkpoint via download.py
::
:: Override torch CUDA build:
::   set DEEPVERSE_TORCH_INDEX=https://download.pytorch.org/whl/cu128   (uses cu128 wheels)
::
:: Override HF auth (if the repo is gated):
::   set HF_TOKEN=hf_xxx  (read by download.py via env, no source edit needed)
::
:: Usage:
::   environment_setup.bat                     full setup + download
::   environment_setup.bat --skip-download     env only, no checkpoint pull

setlocal enableextensions
cd /d "%~dp0"

set VENV=%~dp0.venv
set PY=%VENV%\Scripts\python.exe
if not defined DEEPVERSE_TORCH_INDEX set DEEPVERSE_TORCH_INDEX=https://download.pytorch.org/whl/cu121

if not exist "%PY%" (
    echo Creating venv at %VENV% with Python 3.10 ...
    uv venv --python 3.10 "%VENV%"
    if errorlevel 1 ( echo ERROR: uv venv failed & exit /b 1 )
)

echo.
echo Installing torch 2.4.0 / torchvision 0.19.0 from %DEEPVERSE_TORCH_INDEX% ...
uv pip install --python "%PY%" --index-url "%DEEPVERSE_TORCH_INDEX%" "torch==2.4.0" "torchvision==0.19.0"
if errorlevel 1 ( echo ERROR: torch install failed & exit /b 1 )

echo.
echo Installing requirements.txt ...
uv pip install --python "%PY%" -r "%~dp0requirements.txt"
if errorlevel 1 ( echo ERROR: requirements install failed & exit /b 1 )

echo.
echo Verifying core imports ...
"%PY%" -c "import torch, diffusers, transformers, easydict, einops; print('torch', torch.__version__, '| cuda:', torch.cuda.is_available(), '| diffusers', diffusers.__version__)"
if errorlevel 1 ( echo ERROR: import verification failed & exit /b 1 )

if /I "%~1"=="--skip-download" (
    echo.
    echo --skip-download: leaving checkpoints alone.
    goto :done
)

echo.
echo Downloading DeepVerse1.1 weights to .\checkpoint ...
"%PY%" "%~dp0download.py"
if errorlevel 1 ( echo ERROR: download.py failed & exit /b 1 )

:done
echo.
echo Done. venv: %VENV%
echo Next: activate with "%VENV%\Scripts\activate.bat" and run pipeline.py / run.py.
endlocal
