@echo off
REM GitHub Upload Script for CodeT5 Project
REM This script automates the process of uploading your project to GitHub

echo.
echo =====================================================
echo     CodeT5 Project - GitHub Upload Script
echo =====================================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [✓] Git is installed
echo.

REM Check if already a git repo
if exist .git (
    echo [!] Git repository already initialized
    echo.
    
    echo Do you want to:
    echo   1. Push existing repository to GitHub
    echo   2. Start fresh (remove current .git)
    echo   3. Cancel
    echo.
    
    set /p choice="Enter choice (1-3): "
    
    if "%choice%"=="2" (
        echo Removing current git repository...
        rmdir /s /q .git
        echo [✓] Removed
    ) else if "%choice%"=="3" (
        echo Cancelled.
        exit /b 0
    )
)

echo.
echo =====================================================
echo Step 1: Configure Git User
echo =====================================================
echo.

REM Check if user already configured
git config --global user.name >nul 2>&1
if errorlevel 1 (
    set /p username="Enter your name (for git commits): "
    set /p email="Enter your email (for git commits): "
    
    git config --global user.name "%username%"
    git config --global user.email "%email%"
    
    echo [✓] Git user configured
) else (
    echo [✓] Git user already configured
    git config --global user.name
)

echo.
echo =====================================================
echo Step 2: Initialize Repository
echo =====================================================
echo.

if not exist .git (
    echo Initializing git repository...
    git init
    echo [✓] Repository initialized
) else (
    echo [✓] Repository already exists
)

echo.
echo =====================================================
echo Step 3: Add Files to Git
echo =====================================================
echo.

echo Adding files (excluding models, data, outputs)...
git add .

echo.
echo [?] Files to be committed:
echo.
git status --short | findstr /V "\.bin" | findstr /V "megavul_simple"

echo.
echo [?] Continue? (Y/N)
set /p continue="Enter: "

if /i not "%continue%"=="Y" (
    echo Cancelled. Run: git status to see changes.
    pause
    exit /b 0
)

echo.
echo =====================================================
echo Step 4: Create Initial Commit
echo =====================================================
echo.

echo Committing files...
git commit -m "Initial commit: CodeT5 Vulnerability Detection implementation

- Complete preprocessing script for MegaVul dataset
- Training script with single and multi-GPU support
- Evaluation pipeline with metrics and visualizations
- Inference engine for vulnerability detection
- Comprehensive documentation and guides
- Production-ready implementation"

echo [✓] Files committed

echo.
echo =====================================================
echo Step 5: Add GitHub Remote
echo =====================================================
echo.

echo You need to create a repository on GitHub first:
echo.
echo 1. Go to: https://github.com/new
echo 2. Create repository: codet5-vulnerability-detection
echo 3. Copy the repository URL
echo.

set /p github_url="Paste your GitHub repository URL: "

if "%github_url%"=="" (
    echo ERROR: Repository URL is required
    pause
    exit /b 1
)

echo Adding remote origin...
git remote remove origin >nul 2>&1
git remote add origin %github_url%

echo [✓] Remote added

echo.
echo =====================================================
echo Step 6: Set Main Branch
echo =====================================================
echo.

git branch -M main
echo [✓] Branch set to main

echo.
echo =====================================================
echo Step 7: Push to GitHub
echo =====================================================
echo.

echo Pushing to GitHub...
echo NOTE: You may be prompted for credentials
echo   - If asked for password, use your GitHub Personal Access Token
echo   - Get token from: https://github.com/settings/tokens
echo.

git push -u origin main

if errorlevel 1 (
    echo.
    echo [ERROR] Push failed. Check:
    echo   - Repository URL is correct
    echo   - You have internet connection
    echo   - Your credentials are valid
    echo.
    echo Try again with: git push -u origin main
    pause
    exit /b 1
)

echo.
echo =====================================================
echo SUCCESS! Project uploaded to GitHub
echo =====================================================
echo.
echo Repository URL: %github_url%
echo.
echo Next steps:
echo   1. Visit your repository on GitHub
echo   2. Add topics for discoverability
echo   3. Enable GitHub Pages (optional)
echo   4. Share the link with collaborators
echo.

echo.
echo [TIP] To make future changes:
echo   1. Make changes to your files
echo   2. Run: git add .
echo   3. Run: git commit -m "Description"
echo   4. Run: git push
echo.

pause
