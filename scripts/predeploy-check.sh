#!/usr/bin/env bash
# Pre-deploy gate for dist/. Usage: scripts/predeploy-check.sh [dist_dir]
# Fails if the build contains the unreleased /demo/ pages (allowed only with ALLOW_DEMO=1,
# after real Turnstile is in and the boss approves), or anything that looks like a secret.
set -euo pipefail
DIST="${1:-dist}"
fail() { echo "predeploy-check: FAIL - $*" >&2; exit 1; }
[ -d "$DIST" ] || fail "no $DIST directory"
[ -f "$DIST/index.html" ] || fail "$DIST/index.html missing"
if [ "${ALLOW_DEMO:-0}" != "1" ]; then
  hits=$(find "$DIST" -ipath '*demo*' -print | head -5)
  [ -z "$hits" ] || fail "demo pages in build (set ALLOW_DEMO=1 only after Turnstile + boss OK): $hits"
  if grep -rIl --include='*.html' -E 'href="(/en)?/demo/?"' "$DIST" >/dev/null 2>&1; then
    fail "a page links to /demo/: $(grep -rIl --include='*.html' -E 'href="(/en)?/demo/?"' "$DIST" | head -3 | tr '\n' ' ')"
  fi
fi
if grep -rIlE '(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' "$DIST" >/dev/null 2>&1; then
  fail "secret-like string in build"
fi
echo "predeploy-check: OK ($DIST)"
