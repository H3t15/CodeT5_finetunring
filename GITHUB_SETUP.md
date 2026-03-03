# GitHub Upload Guide

This guide will help you upload the CodeT5 Vulnerability Detection project to GitHub.

## Prerequisites

1. **GitHub Account** - Create one at https://github.com/signup (if you don't have one)
2. **Git Installed** - Download from https://git-scm.com/download/win (Windows)
3. **GitHub CLI (Optional)** - https://cli.github.com/

## Step 1: Create Repository on GitHub

### Option A: Using Web Browser (Easiest)

1. Go to https://github.com/new
2. Fill in repository details:
   - **Repository name:** `codet5-vulnerability-detection`
   - **Description:** `Complete implementation for fine-tuning CodeT5 on MegaVul dataset for vulnerability detection`
   - **Public/Private:** Choose based on preference
   - **Initialize repository:** Leave all unchecked (we'll push existing code)
3. Click **Create repository**
4. Copy the repository URL (will look like: `https://github.com/YOUR_USERNAME/codet5-vulnerability-detection.git`)

### Option B: Using GitHub CLI

```bash
gh repo create codet5-vulnerability-detection --public --source=. --remote=origin --push
```

## Step 2: Initialize Git in Your Project

Navigate to your project directory and run:

```bash
cd "c:\Users\het20\OneDrive\Desktop\CodeT%"
```

Initialize git repository:

```bash
git init
```

Add all files (excluding what's in .gitignore):

```bash
git add .
```

Check what will be committed:

```bash
git status
```

You should see files like:
- ✅ Scripts (01_preprocess.py, 02_train.py, etc.)
- ✅ Requirements.txt, README.md
- ✅ Configuration files
- ❌ models/ (excluded - too large)
- ❌ Data/raw/ (excluded - too large)
- ❌ outputs/ (excluded - temporary)

## Step 3: Create Initial Commit

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"

git commit -m "Initial commit: Complete CodeT5 fine-tuning implementation

- Preprocessing script for MegaVul dataset
- Training script with multi-GPU support
- Evaluation and inference pipelines
- Comprehensive documentation
- Ready for production deployment"
```

## Step 4: Add Remote and Push

Replace `YOUR_USERNAME` and `REPOSITORY_NAME` with your actual GitHub username and repo name:

```bash
git remote add origin https://github.com/YOUR_USERNAME/codet5-vulnerability-detection.git

git branch -M main

git push -u origin main
```

If you get authentication error, you have 2 options:

### Option A: GitHub Personal Access Token (Recommended)

1. Go to https://github.com/settings/tokens
2. Click "Generate new token"
3. Select scopes: `repo`, `workflow`, `gist`
4. Copy the token
5. When prompted for password, paste the token instead of your password

### Option B: SSH Key

Follow: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

## Step 5: Verify Upload

Visit your repository on GitHub:
```
https://github.com/YOUR_USERNAME/codet5-vulnerability-detection
```

You should see:
- ✅ All your scripts
- ✅ README.md rendered
- ✅ requirements.txt visible
- ✅ EXECUTION_GUIDE.txt

## Step 6: Add Model Weights (Optional)

If you want to share trained model weights, you can use **Git LFS** (Large File Storage):

```bash
# Install Git LFS
git lfs install

# Track model files
git lfs track "models/**/*.bin"
git add .gitattributes

# Add models
git add models/
git commit -m "Add trained model weights"
git push
```

**Note:** GitHub LFS has bandwidth limits on free accounts. Alternatively, use these for model distribution:
- **Hugging Face Model Hub:** https://huggingface.co/models
- **Google Drive / OneDrive:** Share model in cloud
- **Zenodo:** Academic archive for reproducibility

## Step 7: Add Badges to README (Optional)

Edit your README.md to add badges at the top:

```markdown
# CodeT5 Vulnerability Detection Fine-tuning

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch 2.0+](https://img.shields.io/badge/pytorch-2.0+-red.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/github-repo-green.svg)](https://github.com/YOUR_USERNAME/codet5-vulnerability-detection)

Complete, production-ready implementation for fine-tuning CodeT5 on the MegaVul dataset...
```

## Step 8: Create Additional GitHub Files (Optional But Recommended)

### 1. Create `LICENSE` file

We recommend MIT License:

```bash
# Download MIT license
curl https://opensource.org/licenses/MIT -o LICENSE
```

Or manually create `LICENSE` file with MIT template from https://opensource.org/licenses/MIT

Then commit:

```bash
git add LICENSE
git commit -m "Add MIT license"
git push
```

### 2. Create `CONTRIBUTING.md`

Create `CONTRIBUTING.md`:

```markdown
# Contributing

Contributions are welcome! Here's how to get started:

## Development Setup

```bash
conda create -n codet5_dev python=3.11 -y
conda activate codet5_dev
pip install -r requirements.txt
```

## Making Changes

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes
4. Test your changes
5. Commit: `git commit -m "Add feature: description"`
6. Push: `git push origin feature/your-feature`
7. Submit Pull Request

## Code Style

- Use Python 3.11+
- Follow PEP 8
- Add docstrings to functions
- Include type hints where applicable

## Testing

Run evaluation on test set before submitting:

```bash
python scripts/03_evaluate.py
```

## Report Issues

Use GitHub Issues to report bugs or suggest features.
```

Then commit:

```bash
git add CONTRIBUTING.md
git commit -m "Add contribution guidelines"
git push
```

### 3. Create Issue Templates

Create `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug Report
about: Report a bug or issue
---

## Description
Brief description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Python version:
- PyTorch version:
- GPU model:
- OS:

## Additional Context
Any other information
```

## Step 9: Complete! Push Latest Changes

```bash
git add .
git commit -m "Add GitHub configuration files"
git push
```

## Verify Everything

Check your repository page:
- ✅ All scripts visible
- ✅ README.md rendered with badges
- ✅ LICENSE file visible
- ✅ File count matches local
- ✅ Latest commit timestamp recent

## Troubleshooting

### Error: "Updates were rejected because the remote contains work that you do not have locally"

```bash
git pull origin main --rebase
git push origin main
```

### Error: "SSH key permission denied"

Use HTTPS instead:

```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/codet5-vulnerability-detection.git
git push -u origin main
```

### Error: ".gitignore not working"

Clear git cache:

```bash
git rm -r --cached .
git add .
git commit -m "Update .gitignore"
git push
```

## Next Steps After Upload

### 1. Add Topics (on GitHub)

On your repository page, click "⚙️ Settings" → "Topics" and add:
- `codet5`
- `vulnerability-detection`
- `machine-learning`
- `security`
- `megavul`
- `code-analysis`
- `python`

### 2. Enable GitHub Pages Docs (Optional)

If you want to host documentation:

1. Go to Settings → Pages
2. Set source to "Deploy from a branch"
3. Select `main` branch and `/docs` folder

### 3. Set Up GitHub Actions (Optional)

Create `.github/workflows/tests.yml` for automated testing:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/ (if you add tests)
```

### 4. Create Releases

After important milestones:

```bash
git tag -a v1.0 -m "Initial release"
git push origin v1.0
```

Then go to GitHub → Releases → Create Release

## Documentation URLs

After upload, share these:

- **Repository:** `https://github.com/YOUR_USERNAME/codet5-vulnerability-detection`
- **Issues:** `https://github.com/YOUR_USERNAME/codet5-vulnerability-detection/issues`
- **Discussions:** `https://github.com/YOUR_USERNAME/codet5-vulnerability-detection/discussions`
- **Clone URL:** `https://github.com/YOUR_USERNAME/codet5-vulnerability-detection.git`

## Quick Reference

```bash
# Initial setup (one time)
git init
git config user.name "Your Name"
git config user.email "your@email.com"
git remote add origin https://github.com/USERNAME/REPO.git

# Regular workflow
git add .
git commit -m "Description"
git push

# Check status
git status
git log --oneline

# Update from origin
git pull
```

---

**Need Help?**

- GitHub Docs: https://docs.github.com
- Git Tutorial: https://git-scm.com/book/en/v2
- About Licenses: https://choosealicense.com

**You're ready to share your project with the world! 🚀**
