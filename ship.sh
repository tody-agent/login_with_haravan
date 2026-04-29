#!/usr/bin/env bash
set -e

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    echo "⚠️ Already on main branch. Just pushing."
    git push origin "$CURRENT_BRANCH"
    exit 0
fi

echo "🚀 Shipping branch: $CURRENT_BRANCH"

# 1. Push current branch to remote
echo ">> [1/5] Pushing $CURRENT_BRANCH to remote..."
git push -u origin "$CURRENT_BRANCH"

# 2. Checkout main and pull latest
echo ">> [2/5] Switching to main and pulling latest..."
git fetch origin
git checkout main
git reset --hard origin/main

# 3. Merge feature branch into main
echo ">> [3/5] Merging $CURRENT_BRANCH into main..."
if ! git merge "$CURRENT_BRANCH" --no-edit; then
    echo "❌ Merge conflicts detected!"
    echo "Vui lòng xử lý conflict bằng tay, sau đó chạy các lệnh sau:"
    echo "  git commit -m \"Chữa conflict\""
    echo "  git push origin main"
    echo "  git checkout $CURRENT_BRANCH"
    exit 1
fi

# 4. Push main
echo ">> [4/5] Pushing main to remote..."
git push origin main

# 5. Switch back to original branch
echo ">> [5/5] Switching back to $CURRENT_BRANCH..."
git checkout "$CURRENT_BRANCH"

echo "=== 🎉 SUCCESSFULLY SHIPPED $CURRENT_BRANCH TO MAIN! ==="
