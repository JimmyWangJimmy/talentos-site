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
# /jobs/: refuse dry-run/sample/empty job data (build it with scripts/build_jobs.py in strict mode first).
if [ -f "$DIST/jobs/index.html" ] && [ "${ALLOW_EMPTY_JOBS:-0}" != "1" ]; then
  state=$(grep -o 'data-jobs-state="[a-z-]*"' "$DIST/jobs/index.html" | head -1)
  [ "$state" = 'data-jobs-state="ok"' ] || fail "/jobs/ is not publishable ($state): run scripts/build_jobs.py without --allow-small"
  if grep -qE '(^|[^0-9])1[3-9][0-9]{9}([^0-9]|$)|[0-9]{17}[0-9Xx]([^0-9]|$)|党员|硬伤|适合你|优先投' "$DIST/jobs/index.html"; then
    fail "/jobs/ contains phone/ID-number pattern or profile words"
  fi
fi
echo "predeploy-check: OK ($DIST)"
