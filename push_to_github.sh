#!/bin/bash
# Push ONLY this project (Personalized-X-Recommendation-Algorithm) to GitHub.
# Do NOT run from your home dir or from a folder that has Taxora or other repos.
# Run from inside this project folder only.

set -e
REPO_URL="https://github.com/Hamzakhan7473/Personalized-X-Recommendation-Algorithm.git"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"
echo "This will push ONLY the X Recommendation project (no Taxora, no other projects)."
echo ""

# Remove any existing .git here so we start clean and never use a parent repo
rm -rf .git
git init
git branch -M main

# Add only files in THIS folder (backend, README, .gitignore, this script)
git add .
git status
echo ""
echo "--- Files that will be pushed (only what you see above) ---"
read -p "Commit and force-push to $REPO_URL? This will REPLACE whatever is there. [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  git commit -m "Personalized X Recommendation Algorithm: ranking pipeline, backend, no Taxora"
  git remote add origin "$REPO_URL"
  git push -u origin main --force
  echo "Done. Repo now contains only this project: https://github.com/Hamzakhan7473/Personalized-X-Recommendation-Algorithm"
fi
