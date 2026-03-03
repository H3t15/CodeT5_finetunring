# Git Quick Reference for CodeT5 Project

## Initial Setup (One Time Only)

```bash
# Create GitHub repo at: https://github.com/new

# Initialize local repository
git init

# Configure user info
git config user.name "Your Name"
git config user.email "your@email.com"

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: CodeT5 vulnerability detection"

# Add GitHub remote
git remote add origin https://github.com/USERNAME/REPO.git

# Set main branch
git branch -M main

# Push to GitHub
git push -u origin main
```

---

## Regular Workflow (After Initial Setup)

### View Status
```bash
# See what files changed
git status

# See changes in detail
git diff

# See recent commits
git log --oneline -10
```

### Make Changes & Commit
```bash
# Stage specific file
git add path/to/file.py

# Stage all changes
git add .

# Create commit
git commit -m "Brief description of changes"

# Push to GitHub
git push
```

### Pull Latest Changes
```bash
# Get updates from GitHub
git pull origin main
```

---

## Common Tasks

### Create a New Branch (for features)
```bash
# Create and switch to new branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "Add my feature"

# Push branch to GitHub
git push -u origin feature/my-feature

# On GitHub: Create Pull Request
```

### Update Main Branch
```bash
# Switch to main
git checkout main

# Get latest
git pull origin main
```

### Undo Changes
```bash
# Undo changes in file (before commit)
git checkout path/to/file.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

### Update Remote URL
```bash
# View current remote
git remote -v

# Remove old remote
git remote remove origin

# Add new remote
git remote add origin https://github.com/USERNAME/REPO.git

# Verify
git remote -v
```

### Create Release Tag
```bash
# Create tag
git tag -a v1.0 -m "Version 1.0 release"

# Push tag to GitHub
git push origin v1.0
```

---

## Useful Commands

| Command | Purpose |
|---------|---------|
| `git status` | Check current status |
| `git log -n 5` | Show last 5 commits |
| `git diff` | View all changes |
| `git add .` | Stage all files |
| `git commit -m "msg"` | Create commit |
| `git push` | Push to GitHub |
| `git pull` | Get from GitHub |
| `git checkout -b branch` | Create branch |
| `git switch main` | Switch branch |
| `git branch -d branch` | Delete branch |
| `git remote -v` | Show remotes |
| `git reset --hard HEAD~1` | Undo last commit |

---

## GitHub-Specific Tasks

### Update Repository Description
1. Go to Settings on GitHub
2. Update "About" section
3. Add Topics for discoverability

### Enable GitHub Pages
1. Settings → Pages
2. Select source branch (main)
3. Choose folder (/docs or root)
4. Save

### Add Collaborators
1. Settings → Collaborators
2. Click "Add people"
3. Enter GitHub username

### Manage Issues
1. Issues tab on GitHub
2. Click "New Issue"
3. Fill in template
4. Click "Submit new issue"

---

## File Size Limits

⚠️ GitHub has limits:
- Max file size: 100 MB
- Max repo size: 100 GB (soft limit)
- Files > 50 MB: Warning
- Files > 100 MB: Blocked

**If your files are too large:**

Option 1: Use `.gitignore` (exclude files)
```bash
# Already configured in .gitignore
# Models, data, and outputs excluded
```

Option 2: Use Git LFS (Large File Storage)
```bash
# Install LFS
git lfs install

# Track large files
git lfs track "*.bin"
git add .gitattributes

# Push
git add .
git commit -m "Add large files with LFS"
git push
```

Option 3: Host elsewhere
- Hugging Face Model Hub
- Google Drive
- AWS S3
- Zenodo

---

## Troubleshooting

### "error: The remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/USERNAME/REPO.git
```

### "error: src refspec main does not match any"
```bash
# Create initial commit first
git add .
git commit -m "Initial commit"

# Then push
git push -u origin main
```

### "fatal: Not a git repository"
```bash
git init
git remote add origin https://github.com/USERNAME/REPO.git
```

### "error: updates were rejected"
```bash
# Pull first
git pull origin main

# Then push again
git push origin main
```

### Authentication failed
```bash
# Use personal access token instead of password
# Get token: https://github.com/settings/tokens

# For HTTPS (Windows)
git credential reject
git push  # Will prompt for token again

# Or use SSH
ssh-keygen -t ed25519 -C "your@email"
# Add public key to GitHub → Settings → SSH Keys
```

---

## Pro Tips

1. **Commit Often** - Small, logical commits are easier to track
2. **Meaningful Messages** - Describe WHAT and WHY, not just WHAT
3. **Pull Before Push** - Always pull latest before pushing
4. **Use Branches** - Create branches for features, keep main clean
5. **Review Before Commit** - Check `git diff` before committing
6. **Document Changes** - Keep README updated with latest features
7. **Add .gitignore** - Already done! (excludes large files)
8. **Use GitHub Issues** - Track bugs and features

---

## Example Commit Messages

```
# Good
git commit -m "Add vulnerability localization to inference script

- Implemented line-level vulnerability detection
- Added attention visualization
- Includes test cases"

# Better structure
git commit -m "feat: Add vulnerability localization

- Analyze code line by line
- Visualize attention weights
- Map tokens to source lines
- Include unit tests

Closes #42"

# Not great
git commit -m "fixed stuff"
git commit -m "update"
```

---

## Quick Start After Clone

If someone clones your repo:

```bash
# Clone repository
git clone https://github.com/USERNAME/REPO.git
cd REPO

# Create environment
conda create -n codet5_vul python=3.11 -y
conda activate codet5_vul

# Install dependencies
pip install -r requirements.txt

# Download data if needed
# (Note: The preprocessing script expects Data/raw/megavul_simple.json)

# Run pipeline
python run_pipeline.py
```

---

## Resources

- **Git Documentation:** https://git-scm.com/doc
- **GitHub Help:** https://docs.github.com
- **GitHub Desktop App:** https://desktop.github.com (GUI alternative)
- **GitKraken:** https://www.gitkraken.com (Advanced GUI)
- **Gitflow Cheat Sheet:** https://danielkummer.github.io/git-flow-cheatsheet/

---

**Happy coding! 🚀**
