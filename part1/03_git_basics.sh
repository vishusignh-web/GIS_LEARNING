#!/usr/bin/env bash
# Topic 3: Git basics (run inside your project folder)
git init
cat > .gitignore <<'IGN'
.venv/
__pycache__/
.env
*.log
IGN
git add .
git commit -m "Initial project structure"
git log --oneline
# edit a file, then:
#   git diff
#   git add . && git commit -m "Describe the change"
# restore a file to the last commit:
#   git restore src/hello_gis.py
