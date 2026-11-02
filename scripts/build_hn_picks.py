#!/usr/bin/env python3
"""Merge comment aggregates + story signals, enrich via gh api (concurrent), write site JSON."""
from __future__ import annotations
import concurrent.futures
import json
import re
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

PRODUCT = Path("/workspace/product/hn-picks/export")
SITE_DATA = Path("/workspace/site/talentos-site-release/src/data")
SITE_PUBLIC = Path("/workspace/site/talentos-site-release/public/hn-picks")

AI_RE = re.compile(
    r"\b(ai|llm|gpt|claude|openai|anthropic|agentic|\bagents?\b|rag|langchain|llamaindex|"
    r"embedding|vllm|ollama|mlx|inference|transformer|diffusion|"
    r"whisper|copilot|autogen|crewai|huggingface|deepseek|qwen|mistral|gemini|"
    r"mcp\b|a2a|skill|chatgpt|llmops|mlops)\b",
    re.I,
)
DEVTOOL_RE = re.compile(
    r"\b(cli|sdk|framework|library|database|editor|ide|devtools?|observability|"
    r"kubernetes|k8s|docker|compiler|typescript|rust|golang|browser|"
    r"scraping|security|auth)\b",
    re.I,
)
AI_NAME_RE = re.compile(
    r"(ai|llm|gpt|agent|rag|lang|llama|openai|claude|copilot|vector|embed|ml|chat|mcp)",
    re.I,
)


def load_json(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def classify(name: str, desc: str, topics: list[str]) -> str:
    blob = " ".join([name, desc or "", " ".join(topics or [])])
    if AI_RE.search(blob) or AI_NAME_RE.search(name):
        return "AI / Agent"
    if DEVTOOL_RE.search(blob):
        return "开发工具"
    return "其他开源"




def comment_coverage_from_checkpoint() -> dict:
    """Honest crawl window(s) from raw/checkpoint.json done_weeks (may be non-contiguous)."""
    from datetime import datetime, timedelta
    ck_path = Path("/workspace/product/hn-picks/raw/checkpoint.json")
    target_end = datetime.now(timezone.utc).strftime("%Y-%m")
    empty = {
        "comment_start": "2020-01",
        "comment_end": "unknown",
        "ranges": [],
        "complete": False,
        "in_progress": True,
        "target_end": target_end,
        "weeks_done": 0,
    }
    if not ck_path.exists():
        return empty
    ck = json.loads(ck_path.read_text())
    weeks = sorted(ck.get("done_weeks") or [])
    if not weeks:
        return empty
    # collapse contiguous weekly shards into ranges
    ranges = []
    rs = weeks[0]
    prev = datetime.strptime(weeks[0], "%Y-%m-%d")
    for w in weeks[1:]:
        cur = datetime.strptime(w, "%Y-%m-%d")
        if (cur - prev).days > 7:
            re = (prev + timedelta(days=6)).strftime("%Y-%m")
            ranges.append({"start": rs[:7], "end": re, "start_week": rs, "end_week": prev.strftime("%Y-%m-%d")})
            rs = w
        prev = cur
    re = (prev + timedelta(days=6)).strftime("%Y-%m")
    ranges.append({"start": rs[:7], "end": re, "start_week": rs, "end_week": prev.strftime("%Y-%m-%d")})
    # Prefer displaying the newest range for the banner primary end, and all ranges for honesty
    newest = ranges[-1]
    oldest = ranges[0]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    last = datetime.strptime(weeks[-1], "%Y-%m-%d")
    # complete only if continuous from 2020-01-01 to ~now
    expected_start = datetime(2020, 1, 1)
    complete = (
        len(ranges) == 1
        and datetime.strptime(weeks[0], "%Y-%m-%d") <= expected_start + timedelta(days=7)
        and (now - last).days <= 14
    )
    return {
        "comment_start": oldest["start"],
        "comment_end": newest["end"],
        "ranges": ranges,
        "comment_start_week": weeks[0],
        "comment_end_week": weeks[-1],
        "weeks_done": len(weeks),
        "complete": complete,
        "in_progress": not complete,
        "target_end": target_end,
    }

def gh_repo(full: str) -> dict | None:
    try:
        out = subprocess.check_output(
            [
                "gh", "api", f"repos/{full}",
                "-H", "Accept: application/vnd.github+json",
                "--jq", "{full_name,description,stargazers_count,language,topics,archived,html_url,homepage}",
            ],
            stderr=subprocess.DEVNULL,
            timeout=25,
            text=True,
        )
        return json.loads(out)
    except Exception:
        return None


def main():
    raw = load_json(PRODUCT / "repos_raw.json")
    if not raw:
        ck = load_json(Path("/workspace/product/hn-picks/raw/checkpoint.json"))
        if not ck:
            raise SystemExit("no data")
        items = []
        for full, rec in ck["repos"].items():
            items.append({
                "repo": full,
                "url": f"https://github.com/{full}",
                "recommenders": len(rec["authors"]),
                "mentions": sum(rec["authors"].values()),
                "first_ts": rec["first_ts"],
                "last_ts": rec["last_ts"],
                "samples": rec.get("samples") or [],
            })
        raw = {"items": items}

    stories = load_json(PRODUCT / "stories_github.json") or {"items": {}}
    story_map = stories.get("items") or {}
    by_repo = {it["repo"]: it for it in raw["items"]}
    all_repos = set(by_repo) | set(story_map)

    merged = []
    for full in all_repos:
        c = by_repo.get(full) or {
            "repo": full, "url": f"https://github.com/{full}",
            "recommenders": 0, "mentions": 0, "first_ts": 0, "last_ts": 0, "samples": [],
        }
        s = story_map.get(full) or {}
        recommenders = c["recommenders"]
        points_max = int(s.get("points_max") or 0)
        if recommenders < 2 and points_max < 40:
            continue
        score = recommenders * 10 + min(points_max, 500) // 5 + min(c["mentions"], 50)
        # boost likely-AI names so they enter enrich pool
        if AI_NAME_RE.search(full):
            score += 25
        merged.append({
            "repo": full,
            "url": c["url"],
            "recommenders": recommenders,
            "mentions": c["mentions"],
            "story_points_max": points_max,
            "story_title": s.get("best_title") or "",
            "story_id": s.get("best_id") or "",
            "first_ts": c["first_ts"] or s.get("created_at_i") or 0,
            "last_ts": c["last_ts"] or s.get("created_at_i") or 0,
            "samples": c.get("samples") or [],
            "score": score,
        })

    merged.sort(key=lambda x: (-x["score"], -x["recommenders"], -x["story_points_max"], x["repo"]))
    TOP = min(450, len(merged))
    # Ensure AI-named repos get slots even if mid-score
    selected = merged[:TOP]
    have = {x["repo"] for x in selected}
    for it in merged[TOP:]:
        if len(selected) >= 500:
            break
        if AI_NAME_RE.search(it["repo"]) and it["repo"] not in have:
            selected.append(it)
            have.add(it["repo"])
    print(f"candidates={len(merged)} enriching={len(selected)}", flush=True)

    def enrich_one(it):
        meta = gh_repo(it["repo"])
        out = dict(it)
        if meta is None:
            out["alive"] = False
            out["stars"] = None
            out["description"] = out.get("story_title") or ""
            out["language"] = None
            out["topics"] = []
            out["category"] = classify(out["repo"], out["description"], [])
        else:
            out["alive"] = True
            out["stars"] = meta.get("stargazers_count")
            out["description"] = (meta.get("description") or out.get("story_title") or "")[:280]
            out["language"] = meta.get("language")
            out["topics"] = meta.get("topics") or []
            out["homepage"] = meta.get("homepage") or ""
            out["category"] = classify(out["repo"], out["description"], out["topics"])
            out["url"] = meta.get("html_url") or out["url"]
        hn_links = []
        for s in out.get("samples") or []:
            oid = s.get("objectID")
            if oid:
                hn_links.append(f"https://news.ycombinator.com/item?id={oid}")
        if out.get("story_id") and len(hn_links) < 3:
            u = f"https://news.ycombinator.com/item?id={out['story_id']}"
            if u not in hn_links:
                hn_links.append(u)
        out["hn_links"] = hn_links[:3]
        out.pop("samples", None)
        return out

    enriched = []
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(enrich_one, it) for it in selected]
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            enriched.append(fut.result())
            if i % 50 == 0 or i == len(futs):
                print(f"enriched {i}/{len(futs)} in {time.time()-t0:.1f}s", flush=True)

    # Prefer: alive, AI category, then score
    cat_rank = {"AI / Agent": 0, "开发工具": 1, "其他开源": 2}
    enriched.sort(key=lambda x: (
        0 if x.get("alive") else 1,
        cat_rank.get(x.get("category"), 9),
        -x.get("score", 0),
        -(x.get("stars") or 0),
    ))

    tz8 = timezone(timedelta(hours=8))
    coverage = comment_coverage_from_checkpoint()
    ranges = coverage.get("ranges") or []
    if len(ranges) > 1:
        cov_label = " + ".join(f"{r['start']}–{r['end']}" for r in ranges)
    else:
        cov_label = f"{coverage['comment_start']}–{coverage['comment_end']}"
    method = (
        f"Rank primarily by distinct HN commenters who linked the repo "
        f"(weekly shards {cov_label}"
        + (", crawl in progress" if coverage.get("in_progress") else "")
        + "); story points as secondary. Stars are reference only."
    )
    disclaimer = (
        f"提及≠推荐背书。夸和踩都会计入提及。当前评论数据覆盖：{cov_label}"
        + ("（抓取仍在进行，区间可能不连续）。" if coverage.get("in_progress") else "。")
        + "Algolia 单查询约 1000 条上限，按周分片仍可能漏数据。"
    )
    payload = {
        "generated_at": datetime.now(tz8).isoformat(timespec="seconds"),
        "title": "HN 开源精选",
        "title_en": "HN Open-Source Picks",
        "source": "Hacker News comments & stories via Algolia; metadata via GitHub API",
        "method": method,
        "disclaimer": disclaimer,
        "coverage": coverage,
        "count": len(enriched),
        "stats": {
            "ai_agent": sum(1 for x in enriched if x.get("category") == "AI / Agent"),
            "devtools": sum(1 for x in enriched if x.get("category") == "开发工具"),
            "other": sum(1 for x in enriched if x.get("category") == "其他开源"),
            "recommenders_ge5": sum(1 for x in enriched if x.get("recommenders", 0) >= 5),
        },
        "items": enriched,
    }
    PRODUCT.mkdir(parents=True, exist_ok=True)
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    SITE_PUBLIC.mkdir(parents=True, exist_ok=True)
    text_pretty = json.dumps(payload, ensure_ascii=False, indent=2)
    text_compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    (PRODUCT / "hn-picks.json").write_text(text_pretty)
    (SITE_DATA / "hn-picks.json").write_text(text_compact)
    (SITE_PUBLIC / "data.json").write_text(text_pretty)
    main_data = Path("/workspace/site/talentos-site/src/data")
    main_data.mkdir(parents=True, exist_ok=True)
    (main_data / "hn-picks.json").write_text(text_compact)
    print(f"wrote {len(enriched)} items ai={payload['stats']['ai_agent']} dev={payload['stats']['devtools']}", flush=True)


if __name__ == "__main__":
    main()
