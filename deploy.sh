#!/usr/bin/env bash
# Build and publish dist/ to the gh-pages branch (current deploy method; token lacks `workflow` scope).
set -e
npm run build && touch dist/.nojekyll
cd dist && rm -rf .git && git init -q -b gh-pages && git add -A && git -c user.name=JimmyWangJimmy -c user.email=JimmyWangJimmy@users.noreply.github.com commit -qm "Deploy $(date +%F_%T)"
git push -f https://github.com/JimmyWangJimmy/talentos-site.git gh-pages
