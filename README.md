# talentos-site

TalentOS brand website (Astro, static, zero client JS). ## Deploy (current)
Pages serves the `gh-pages` branch (build_type=legacy). Run `./deploy.sh` (build + force-push dist/ to gh-pages).
The gh token on the box lacks the `workflow` scope, so the Actions workflow (withastro/action) is parked at `deploy/deploy.yml`.
To switch to Actions: `gh auth refresh -s workflow` (Jimmy signs in), `mkdir -p .github/workflows && git mv deploy/deploy.yml .github/workflows/`, push, then
`gh api -X PUT repos/JimmyWangJimmy/talentos-site/pages -f build_type=workflow`.

## Edit content
Page copy: `src/content/pages/*.md` (same format as the copy deck: `# 中文` then `# English`, one `## ` per block; first block = hero, bold first line = h1; 次要入口/Secondary entry blocks render as a slim bar; `meta.md` table = titles/descriptions). Nav/footer strings:
- `zh.json` — Chinese (served at `/`)
- `en.json` — English (served at `/en/`)
- `theme.json` — colors
Logo: replace `public/logo.svg` and `public/favicon.svg`.
Keep the JSON keys; only change values. Run `npm run build` to check, then push to `main`.

## Switch to www.agentbay.asia (after the DNS CNAME www -> jimmywangjimmy.github.io exists)
1. In `astro.config.mjs` change the defaults to `site: 'https://www.agentbay.asia'`, `base: '/'` (or set SITE_URL/SITE_BASE env in deploy.sh / the workflow).
2. `cp CNAME.custom-domain public/CNAME`
3. Commit + push to main, then `./deploy.sh`.
4. IT运维 sets the Pages custom domain: `gh api -X PUT repos/JimmyWangJimmy/talentos-site/pages -f cname=www.agentbay.asia`
5. When the certificate is issued (check `gh api repos/JimmyWangJimmy/talentos-site/pages --jq .https_certificate.state` = `approved`):
   `gh api -X PUT repos/JimmyWangJimmy/talentos-site/pages -F https_enforced=true`
Do not touch the root domain or MX/SPF/DKIM records.

## AI 岗位库 /jobs/（feat/jobs）
- 数据：`python3 scripts/build_jobs.py` 读 `/workspace/product/ai-job-board/export/ai-jobs-seed.json`（没有就依次用 `/workspace/job-monitor/export/ai-jobs-latest.json`、示例），按 `talentos.aijobs.v1` 校验、去重、下架过期、扫 PII，写 `src/data/jobs.json`（不进仓库），然后 `npm run build`。
- 闸门：有效条数 `--min-count`（默认 80，或环境变量 `JOBS_MIN_COUNT`）、示例数据、`generated_at` 不是今天、条数比上次少 30% 以上，任一命中就 exit 1，旧 `jobs.json` 不动。
- 预演：`--allow-small` 把闸门降成警告，输出标记为 dry-run；`scripts/predeploy-check.sh` 会拒绝发布 dry-run、示例或空的 /jobs/。
- 页面只有中文版；导航入口只加在中文导航里。CTA 统一跳 `/checkup/?src=jobs&cta=top|inline|footer`，企业入口 `/checkup/?src=jobs-biz&cta=biz` + mailto `[岗位库-企业]`；/checkup/ 把来源写进现有 `page` 字段（`src:cta|utm_source|utm_campaign`）。
