#!/usr/bin/env bash
# Build and publish dist/ to the gh-pages branch (current deploy method; token lacks `workflow` scope).
# Publish ONLY from the release worktree (/workspace/site/talentos-site-release, branch release/site).
set -e
cd "$(dirname "$0")"
branch=$(git rev-parse --abbrev-ref HEAD)
[ "$branch" = "release/site" ] || { echo "deploy.sh: refuse - current branch is '$branch', deploy only from release/site" >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "deploy.sh: refuse - uncommitted changes" >&2; exit 1; }
npm run build && touch dist/.nojekyll
scripts/predeploy-check.sh dist
cd dist && rm -rf .git && git init -q -b gh-pages && git add -A && git -c user.name=JimmyWangJimmy -c user.email=JimmyWangJimmy@users.noreply.github.com commit -qm "Deploy $(date +%F_%T)"
git push -f https://github.com/JimmyWangJimmy/talentos-site.git gh-pages
