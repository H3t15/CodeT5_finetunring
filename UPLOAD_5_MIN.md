# ⚡ 5-Minute GitHub Upload (Quickstart)

## The Fastest Way to Upload Your Project

### Step 1️⃣: Create GitHub Repo (2 minutes)

1. Go to: https://github.com/new
2. Enter repo name: `codet5-vulnerability-detection`
3. Description: `CodeT5 fine-tuning for vulnerability detection on MegaVul dataset`
4. Choose: **Public** (if you want others to see it)
5. Click **Create repository**
6. **COPY** the HTTPS URL (looks like: `https://github.com/YOUR_USERNAME/codet5-vulnerability-detection.git`)

### Step 2️⃣: Upload Project (3 minutes)

Double-click this file (in your project folder):
```
upload_to_github.bat
```

The script will:
- ✅ Check Git installation
- ✅ Configure your user info
- ✅ Initialize repository  
- ✅ Stage all files (excluding models/data)
- ✅ Create commit
- ✅ Ask for your GitHub URL
- ✅ Push to GitHub

**That's it!** Your project is now on GitHub 🎉

---

## Manual Method (If Script Doesn't Work)

Open PowerShell and run:

```powershell
# Navigate to project
cd "c:\Users\het20\OneDrive\Desktop\CodeT%"

# Initialize git
git init

# Configure user (one time)
git config user.name "Your Name"
git config user.email "your@email.com"

# Add files (excludes models, data, outputs via .gitignore)
git add .

# Create commit
git commit -m "Initial commit: CodeT5 vulnerability detection

- Complete preprocessing pipeline
- Training script with multi-GPU support
- Evaluation and inference modules
- Production-ready implementation"

# Add GitHub remote (paste YOUR copied URL)
git remote add origin https://github.com/YOUR_USERNAME/codet5-vulnerability-detection.git

# Set main branch
git branch -M main

# Push to GitHub
git push -u origin main
```

When prompted for password, **use your GitHub Personal Access Token**:
1. Go to: https://github.com/settings/tokens
2. Click **Generate new token**
3. Select: `repo`, `workflow`, `gist`
4. Click **Generate**
5. Copy token
6. Paste as password in terminal

---

## ✅ Verify Success

Visit: `https://github.com/YOUR_USERNAME/codet5-vulnerability-detection`

You should see:
- ✅ All Python scripts
- ✅ README.md (formatted nicely)
- ✅ requirements.txt
- ✅ All other files

---

## 📝 What Gets Uploaded

**Included:**
- ✅ All `.py` scripts
- ✅ `.md` documentation
- ✅ `.txt` and `.yaml` configs
- ✅ `.bat` setup scripts
- ✅ `.gitignore` file

**Excluded (Too Large):**
- ❌ `Data/raw/megavul_simple.json` (~1.1 GB)
- ❌ `models/` (large model files)
- ❌ `outputs/` (temporary predictions)
- ❌ `__pycache__/` and virtual envs

---

## 🚀 Next Steps (Optional)

### Add More Info to GitHub

On your GitHub repo page:

1. **Add Topics** (helps others find your project)
   - Settings → Topics
   - Add: `codet5`, `vulnerability-detection`, `machine-learning`, `security`

2. **Add Badges** (shows in README)
   Edit README.md, add at top:
   ```markdown
   [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
   [![PyTorch 2.0+](https://img.shields.io/badge/pytorch-2.0+-red.svg)](https://pytorch.org/)
   ```

3. **Create Release** (for sharing versions)
   ```powershell
   git tag -a v1.0 -m "Initial release"
   git push origin v1.0
   ```
   Then go to GitHub → Releases → Create Release

### Share Your Project

- **Send Link:** `https://github.com/YOUR_USERNAME/codet5-vulnerability-detection`
- **Get Clone Command:** `git clone https://github.com/YOUR_USERNAME/codet5-vulnerability-detection.git`
- **Add to Portfolio:** Add to your LinkedIn/resume

---

## Future Updates (Easy!)

After uploading, to make changes:

```powershell
# Make changes to your files

# Stage changes
git add .

# Commit
git commit -m "Your change description"

# Push
git push
```

---

## Need Help?

| Issue | Solution |
|-------|----------|
| URL already in use? | Choose different repo name |
| Can't authenticate? | Use Personal Access Token (see above) |
| File too large? | Already handled by `.gitignore` |
| Want to delete and start over? | Delete repo on GitHub, create new one |

---

**You're doing great! Your project is about to be live on GitHub! 🚀**
