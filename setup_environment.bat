@echo off
REM CodeT5 Fine-tuning Environment Setup for Windows
REM This script creates and configures the Conda environment

echo ============================================
echo CodeT5 Fine-tuning Environment Setup
echo ============================================
echo.

REM Check if conda is installed
conda --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Conda is not installed or not in PATH
    echo Please install Miniconda or Anaconda first
    exit /b 1
)

REM Create conda environment
echo Creating conda environment: codet5_vul...
call conda create -n codet5_vul python=3.11 -y

if errorlevel 1 (
    echo ERROR: Failed to create conda environment
    exit /b 1
)

REM Activate environment
call conda activate codet5_vul

if errorlevel 1 (
    echo ERROR: Failed to activate conda environment
    exit /b 1
)

echo.
echo ============================================
echo Installing PyTorch (CUDA 12.1)
echo ============================================
call conda install pytorch pytorch-cuda=12.1 -c pytorch -c nvidia -y

echo.
echo ============================================
echo Installing HuggingFace & ML Libraries
echo ============================================
pip install --upgrade pip setuptools wheel

REM Core dependencies
pip install transformers==4.40.0 ^
            datasets==2.18.0 ^
            torch-cuda-compat ^
            scipy==1.13.0 ^
            numpy==1.24.3 ^
            pandas==2.2.0 ^
            scikit-learn==1.4.0 ^
            tqdm==4.66.2

REM Training & evaluation
pip install accelerate==0.28.0 ^
            evaluate==0.4.1 ^
            peft==0.11.0 ^
            bitsandbytes==0.42.0

REM Additional utilities
pip install wandb==0.16.0 ^
            tensorboard==2.16.0 ^
            pyyaml==6.0.1 ^
            python-dotenv==1.0.0

echo.
echo ============================================
echo Verifying Installation
echo ============================================
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
python -c "import transformers; print(f'Transformers version: {transformers.__version__}')"
python -c "import datasets; print(f'Datasets version: {datasets.__version__}')"

echo.
echo ============================================
echo Environment Setup Complete!
echo ============================================
echo.
echo To activate this environment in future, run:
echo   conda activate codet5_vul
echo.
echo To deactivate, run:
echo   conda deactivate
echo.
pause
