#!/usr/bin/env python3
"""build_jobs.py - validate a talentos.aijobs.v1 export and write the public src/data/jobs.json
that src/pages/jobs.astro renders. Python stdlib only; no network.

Contract: /workspace/product/ai-job-board/data-contract-v1.md (schema talentos.aijobs.v1).
Gates (exit 1, existing src/data/jobs.json left untouched):
  schema / whitelist violation, sample data, stale generated_at, PII or profile words,
  forbidden source, open count < --min-count, >30% drop vs previous build.
--allow-small = DRY RUN: gates become warnings, output is marked dry_run and
scripts/predeploy-check.sh refuses to publish it.

Usage:
  python3 scripts/build_jobs.py                       # strict (production)
  python3 scripts/build_jobs.py --allow-small         # dry run, e.g. with the sample
  python3 scripts/build_jobs.py --input FILE --min-count 80 --today 2026-10-30
then: npm run build
"""
import argparse, csv, datetime as dt, hashlib, json, os, re, sys, tempfile
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCT = "/workspace/product/ai-job-board"
DEFAULT_INPUTS = [f"{PRODUCT}/export/ai-jobs-seed.json",
                  "/workspace/job-monitor/export/ai-jobs-latest.json",
                  f"{PRODUCT}/export/ai-jobs-latest.sample.json"]
OUT = os.path.join(ROOT, "src", "data", "jobs.json")
BLOCKLIST = f"{PRODUCT}/data/blocklist.txt"
SEED_COMPANIES = [f"{PRODUCT}/export/seed-companies.csv", f"{PRODUCT}/seeds.csv"]
# Source-domain allowlist (contract §6). Hosts from the seed CSV's URL column are added at runtime.
ALLOWED_SOURCES = {"join.qq.com", "jobs.bytedance.com", "zhaopin.meituan.com", "vrfi1sk8a0.jobs.feishu.cn",
                   # university career sites named in data-contract-v1 §6
                   "career.sysu.edu.cn", "scdc.jnu.edu.cn", "career.scnu.edu.cn", "career.gdufs.edu.cn",
                   "scc.pku.edu.cn", "career.cic.tsinghua.edu.cn"}
TZ = dt.timezone(dt.timedelta(hours=8))

TOP_FIELDS = {"schema", "generated_at", "producer", "is_sample", "run_ref", "items"}
TOP_REQ = {"schema", "generated_at", "producer", "items"}
JOB_REQ = ["id", "title", "company", "company_type", "city", "recruit_type", "job_family", "deadline",
           "deadline_verified", "first_seen", "last_verified", "status", "source_url", "source_name"]
JOB_FIELDS = set(JOB_REQ) | {"summary"}
ENUMS = {
    "company_type": {"大厂", "AI创业", "量化", "外企", "国企研究所", "其他"},
    "recruit_type": {"校招", "实习", "社招"},
    "job_family": {"算法研究", "工程研发", "硬件与机器人", "产品与设计", "商业与运营", "其他"},
    "status": {"open", "expired", "unknown"},
}
CITIES = {"深圳", "广州", "香港", "上海", "北京", "杭州", "珠海", "东莞", "佛山", "澳门", "远程", "其他"}
GBA_CITIES = {"深圳", "广州", "珠海", "东莞", "佛山", "香港", "澳门"}
FAMILY_ORDER = ["算法研究", "工程研发", "产品与设计", "硬件与机器人", "商业与运营", "其他"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GEN_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$")
TRACKING = re.compile(r"^(utm_.*|spm|from|source|share.*|ref)$", re.I)
FORBIDDEN_HOSTS = ("haitou", "campus.51job.com", "hk.jobsdb.com", "linkedin.com", "zhipin.com",
                   "liepin.com", "maimai.cn", "t.cn", "url.cn", "bit.ly", "dwz.cn")
PII = {
    "phone": re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "wechat": re.compile(r"(微信|wechat|vx|v信)\s*[:：号]?\s*[A-Za-z][-_A-Za-z0-9]{5,19}", re.I),
}
PROFILE_WORDS = ("优先投", "有硬伤", "硬伤", "适合你", "非党员", "党员", "Eileen")


def canon_url(u):
    s = urlsplit(u.strip())
    scheme = "https" if s.scheme in ("http", "https") else s.scheme
    host = (s.hostname or "").lower()
    if s.port and not ((s.scheme == "http" and s.port == 80) or (s.scheme == "https" and s.port == 443)):
        host = f"{host}:{s.port}"
    q = sorted((k, v) for k, v in parse_qsl(s.query, keep_blank_values=True) if not TRACKING.match(k))
    return urlunsplit((scheme, host, s.path, urlencode(q), ""))


def job_id(u):
    return hashlib.sha1(canon_url(u).encode("utf-8")).hexdigest()[:12]


def norm_title(t):
    t = "".join(chr(ord(c) - 0xFEE0) if 0xFF01 <= ord(c) <= 0xFF5E else c for c in t)
    t = t.replace("\u3000", "").replace("【", "[").replace("】", "]")
    return re.sub(r"\s+", "", t).lower()


def is_date(v):
    if not isinstance(v, str) or not DATE_RE.match(v):
        return False
    try:
        dt.date.fromisoformat(v)
        return True
    except ValueError:
        return False


def validate_job(j, i):
    errs = []
    if not isinstance(j, dict):
        return [f"items[{i}] is not an object"]
    extra = set(j) - JOB_FIELDS
    if extra:
        errs.append(f"items[{i}] non-whitelisted fields {sorted(extra)}")
    for k in JOB_REQ:
        if k not in j:
            errs.append(f"items[{i}] missing {k}")
    if errs:
        return errs
    p = f"items[{i}] ({j.get('id')})"
    if not (isinstance(j["id"], str) and re.fullmatch(r"[0-9a-f]{12}", j["id"])):
        errs.append(f"{p} bad id")
    for k, lo, hi in (("title", 2, 120), ("company", 1, 80)):
        if not (isinstance(j[k], str) and lo <= len(j[k]) <= hi):
            errs.append(f"{p} {k} length must be {lo}-{hi}")
    for k, allowed in ENUMS.items():
        if j[k] not in allowed:
            errs.append(f"{p} {k}={j[k]!r} not in enum")
    c = j["city"]
    if not (isinstance(c, list) and 1 <= len(c) <= 8 and len(set(c)) == len(c) and all(x in CITIES for x in c)):
        errs.append(f"{p} bad city {c!r}")
    if not (j["deadline"] is None or is_date(j["deadline"])):
        errs.append(f"{p} bad deadline")
    if not isinstance(j["deadline_verified"], bool):
        errs.append(f"{p} deadline_verified not bool")
    for k in ("first_seen", "last_verified"):
        if not is_date(j[k]):
            errs.append(f"{p} bad {k}")
    u = j["source_url"]
    if not (isinstance(u, str) and re.match(r"^https?://", u) and len(u) <= 500):
        errs.append(f"{p} bad source_url")
    elif isinstance(j["id"], str) and j["id"] != job_id(u):
        errs.append(f"{p} id != sha1(canonical source_url)[:12] (expected {job_id(u)})")
    if not (isinstance(j["source_name"], str) and len(j["source_name"]) <= 80):
        errs.append(f"{p} bad source_name")
    if "summary" in j and not (isinstance(j["summary"], str) and len(j["summary"]) <= 60):
        errs.append(f"{p} summary must be a string of <=60 chars")
    if j.get("summary") and j["summary"] == j["title"]:
        errs.append(f"{p} summary identical to title")
    return errs


def scan_pii(j):
    hits = []
    for k in ("title", "company", "summary", "source_url"):
        v = j.get(k) or ""
        for name, rx in PII.items():
            if k == "source_url" and name in ("email", "wechat"):
                continue
            if rx.search(v):
                hits.append(f"{j['id']}: {name} in {k}")
        if k != "source_url":
            for w in PROFILE_WORDS:
                if w in v:
                    hits.append(f"{j['id']}: profile word {w!r} in {k}")
    host = (urlsplit(j["source_url"]).hostname or "").lower()
    if any(h in host for h in FORBIDDEN_HOSTS):
        hits.append(f"{j['id']}: forbidden source host {host}")
    if re.search(r"[?&](token|sid|session|access_token|ticket)=", j["source_url"], re.I):
        hits.append(f"{j['id']}: personal token in source_url")
    return hits


def load_allowed_sources():
    allowed = set(ALLOWED_SOURCES)
    for path in SEED_COMPANIES:
        if os.path.exists(path):
            with open(path, encoding="utf-8-sig", newline="") as fh:
                for row in csv.reader(fh):
                    for cell in row:
                        if re.match(r"^https?://", cell.strip()):
                            h = (urlsplit(cell.strip()).hostname or "").lower()
                            if h:
                                allowed.add(h)
    return allowed


def load_blocklist():
    ids, domains = set(), set()
    if os.path.exists(BLOCKLIST):
        for line in open(BLOCKLIST, encoding="utf-8"):
            s = line.split("#", 1)[0].strip().lower()
            if not s:
                continue
            (ids if re.fullmatch(r"[0-9a-f]{12}", s) else domains).add(s)
    return ids, domains


def compute_stats(items):
    """Aggregate observation-block stats/insights from published items (no hand-written numbers)."""
    from collections import Counter
    n = len(items)
    if n == 0:
        return {
            "count": 0,
            "recruit_type": {},
            "job_family": {},
            "city_freq": {},
            "gba_count": 0,
            "gba_pct": 0,
            "campus": 0,
            "intern": 0,
            "fulltime": 0,
        }, []
    recruit = Counter(j["recruit_type"] for j in items)
    family = Counter(j["job_family"] for j in items)
    cities = Counter(c for j in items for c in j["city"])
    gba = sum(1 for j in items if any(c in GBA_CITIES for c in j["city"]))
    stats = {
        "count": n,
        "recruit_type": {k: recruit[k] for k in ("校招", "实习", "社招") if recruit.get(k)},
        "job_family": {k: family[k] for k in FAMILY_ORDER if family.get(k)},
        "city_freq": dict(cities.most_common()),
        "gba_count": gba,
        "gba_pct": round(100 * gba / n),
        "campus": recruit.get("校招", 0),
        "intern": recruit.get("实习", 0),
        "fulltime": recruit.get("社招", 0),
    }
    insights = []
    if family:
        top_f, top_fn = family.most_common(1)[0]
        insights.append(f"方向：{top_f}占 {round(100 * top_fn / n)}%")
    if cities:
        top_c, top_cn = cities.most_common(1)[0]
        insights.append(f"城市：{top_c}出镜 {top_cn} 次")
    campus, intern, full = stats["campus"], stats["intern"], stats["fulltime"]
    if campus and intern and abs(campus - intern) <= max(2, int(n * 0.1)):
        insights.append("结构：校招与实习约各半")
    elif campus and intern:
        if campus >= intern * 1.5:
            insights.append(f"结构：校招为主（{campus}/{n}）")
        elif intern >= campus * 1.5:
            insights.append(f"结构：实习为主（{intern}/{n}）")
        else:
            insights.append(f"结构：校招 {campus} / 实习 {intern}")
    elif campus:
        insights.append(f"结构：以校招为主（{campus} 条）")
    elif intern:
        insights.append(f"结构：以实习为主（{intern} 条）")
    elif full:
        insights.append(f"结构：以社招为主（{full} 条）")
    return stats, insights[:3]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", help="export JSON (default: first existing of %s)" % ", ".join(DEFAULT_INPUTS))
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--min-count", type=int, default=int(os.environ.get("JOBS_MIN_COUNT", 80)),
                    help="minimum open jobs to publish (default 80, env JOBS_MIN_COUNT)")
    ap.add_argument("--allow-small", action="store_true",
                    help="DRY RUN: downgrade gates to warnings; output marked dry_run (not deployable)")
    ap.add_argument("--today", help="override today (YYYY-MM-DD, Asia/Shanghai)")
    a = ap.parse_args()

    today = dt.date.fromisoformat(a.today) if a.today else dt.datetime.now(TZ).date()
    src = a.input or next((p for p in DEFAULT_INPUTS if os.path.exists(p)), None)
    if not src or not os.path.exists(src):
        print(f"build_jobs: FAIL - input not found ({src or DEFAULT_INPUTS})", file=sys.stderr)
        return 1
    fatal, warn = [], []
    gate = (lambda m: warn.append(m)) if a.allow_small else (lambda m: fatal.append(m))

    try:
        with open(src, encoding="utf-8") as fh:
            raw = fh.read()
        if raw.startswith("\ufeff"):
            fatal.append("input has a UTF-8 BOM")
            raw = raw[1:]
        d = json.loads(raw)
    except (OSError, ValueError) as e:
        print(f"build_jobs: FAIL - cannot read {src}: {e}", file=sys.stderr)
        return 1
    if not isinstance(d, dict):
        print("build_jobs: FAIL - top level must be an object", file=sys.stderr)
        return 1

    # --- schema (hard errors even in dry run) ---
    if set(d) - TOP_FIELDS:
        fatal.append(f"non-whitelisted top-level fields {sorted(set(d) - TOP_FIELDS)}")
    if TOP_REQ - set(d):
        fatal.append(f"missing top-level fields {sorted(TOP_REQ - set(d))}")
    if d.get("schema") != "talentos.aijobs.v1":
        fatal.append(f"schema must be talentos.aijobs.v1, got {d.get('schema')!r}")
    if d.get("producer") not in ("scout", "manual", "sample"):
        fatal.append(f"bad producer {d.get('producer')!r}")
    gen = d.get("generated_at", "")
    if not (isinstance(gen, str) and GEN_RE.match(gen)):
        fatal.append(f"generated_at must be YYYY-MM-DDTHH:MM:SS+08:00, got {gen!r}")
    items = d.get("items")
    if not isinstance(items, list) or len(items) > 5000:
        fatal.append("items must be an array of <=5000")
        items = []
    for i, j in enumerate(items):
        fatal.extend(validate_job(j, i))
    if fatal:
        return report(fatal, warn, src)

    # --- publish gates ---
    if d["producer"] == "sample" or d.get("is_sample") is True:
        gate("sample data (producer=sample / is_sample) is never published")
    if gen[:10] != today.isoformat():
        gate(f"generated_at {gen[:10]} is not today {today} (upstream did not run?)")

    pii = [h for j in items for h in scan_pii(j)]
    if pii:
        fatal.extend(pii)  # PII is never downgraded
        return report(fatal, warn, src)

    allowed = load_allowed_sources()
    off = sorted({(urlsplit(j["source_url"]).hostname or "").lower() for j in items} - allowed)
    if off:
        gate(f"source domains not in allowlist: {off[:10]}")
    bad_name = [j["id"] for j in items if j["source_name"].lower() != (urlsplit(j["source_url"]).hostname or "").lower()]
    if bad_name:
        gate(f"source_name != source_url host for {len(bad_name)} item(s), e.g. {bad_name[:3]}")

    # --- blocklist, dedupe, expiry ---
    bl_ids, bl_domains = load_blocklist()
    seen, by_key, out, dropped = {}, {}, [], {"blocklist": 0, "dup": 0, "expired": 0, "stale": 0}
    for j in items:
        host = (urlsplit(j["source_url"]).hostname or "").lower()
        if j["id"] in bl_ids or any(host == b or host.endswith("." + b) for b in bl_domains):
            dropped["blocklist"] += 1
            continue
        key = (j["company"].strip(), norm_title(j["title"]), tuple(sorted(j["city"])), j["recruit_type"])
        prev = seen.get(j["id"]) or by_key.get(key)
        if prev:
            dropped["dup"] += 1
            prev["first_seen"] = min(prev["first_seen"], j["first_seen"])
            prev["last_verified"] = max(prev["last_verified"], j["last_verified"])
            continue
        j = {k: j[k] for k in JOB_REQ + ["summary"] if k in j}
        if isinstance(j.get("summary"), str) and not j["summary"].strip():
            j.pop("summary")  # empty summary -> no summary block on the page
        if j["deadline"] and j["deadline"] < today.isoformat():
            j["status"] = "expired"
        if j["status"] == "expired":
            dropped["expired"] += 1
            continue
        if j["deadline"] is None and (today - dt.date.fromisoformat(j["last_verified"])).days > 30:
            dropped["stale"] += 1
            continue
        seen[j["id"]] = by_key[key] = j
        out.append(j)

    n_open = sum(1 for j in out if j["status"] == "open")
    if n_open < a.min_count:
        gate(f"only {n_open} open jobs (< min-count {a.min_count})")
    if os.path.exists(a.out):
        try:
            with open(a.out, encoding="utf-8") as fh:
                prev = json.load(fh)
            pn = len(prev.get("items", [])) if not prev.get("dry_run") else 0
            if pn and len(out) < pn * 0.7:
                gate(f"count dropped >30% vs previous build ({pn} -> {len(out)})")
        except (OSError, ValueError):
            warn.append("previous jobs.json unreadable; drop check skipped")
    if fatal:
        return report(fatal, warn, src)

    week_end = (today + dt.timedelta(days=7)).isoformat()
    out.sort(key=lambda j: (j["status"] != "open", j["deadline"] or "9999", j["company"], j["title"]))
    stats, insights = compute_stats(out)
    result = {
        "schema": "talentos.aijobs.public.v1",
        "dry_run": bool(warn) and a.allow_small,
        "is_sample": d["producer"] == "sample" or d.get("is_sample") is True,
        "generated_at": gen,
        "built_at": dt.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "today": today.isoformat(),
        "count": len(out),
        "count_open": n_open,
        # no "new_today": first_seen has no reliable history yet, so we don't publish a new-count
        "closing_this_week": [j["id"] for j in out if j["deadline"] and j["deadline"] <= week_end and j["status"] == "open"],
        "stats": stats,
        "insights": insights,
        "items": out,
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(a.out), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.chmod(tmp, 0o644)
    os.replace(tmp, a.out)
    for w in warn:
        print(f"build_jobs: WARN - {w}", file=sys.stderr)
    print(f"build_jobs: {'DRY RUN' if result['dry_run'] else 'OK'} - {src} -> {a.out}: "
          f"{len(out)} jobs ({n_open} open), dropped {dropped}")
    return 0


def report(fatal, warn, src):
    for w in warn:
        print(f"build_jobs: WARN - {w}", file=sys.stderr)
    for f in fatal[:50]:
        print(f"build_jobs: FAIL - {f}", file=sys.stderr)
    print(f"build_jobs: FAIL - {len(fatal)} error(s) in {src}; previous jobs.json left unchanged", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
