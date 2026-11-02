# 开源与研究 / Open Source & Research

# 中文

## 页首
**我们把在用的东西公开。**

## ai-agent-skills
我们日常使用的 Agent skill 合集，MIT 协议，可直接复用。
- 仓库：[https://github.com/TalentOS-AI/ai-agent-skills](https://github.com/TalentOS-AI/ai-agent-skills)
- 未经实测的示例会明确标注。
- 每次提交都会经过密钥与隐私扫描。

### 工程 skill（3）
- **sara-tool-authorization**：防止邮件、网页、MCP 返回等不可信工具输出悄悄变成执行授权。
- **openai-agents-sdk-sandbox**：用 OpenAI Agents SDK 搭多 Agent 工作流（SandboxAgent、MCP、guardrail、handoff、Realtime）。
- **state-path-tool-menus**：工具/MCP 很多时，按可执行路径排工具菜单（生产者在前），而不是只按相关度检索。

### 科研 / 学术 skill（14）
Iris 科研助手日常在用的学术流程 skill，已一并开源：
- **acl-latex-paper**：撰写与编译 ACL 系 LaTeX 论文（模板、匿名、页限、编译检查）。
- **acl-paper-figures**：按 ACL/双栏印刷尺寸做 matplotlib 图（Okabe-Ito、灰度安全）并自检。
- **annotation-project**：标注数据集：方案、指南、一致性、LLM 预标、数据说明与许可。
- **citation-audit**：逐条核验参考文献是否真实、归因正确、支撑主张（兼顾 MBA/CSSCI）。
- **citation-verification**：分享参考文献前用 DOI/Crossref/Anthology/arXiv 解析每条引用。
- **deslop**：去掉学术文风里的 AI 套话与防御性表述（含中文期刊补充）。
- **literature-review**：系统文献检索：多源查询、滚雪球、综述矩阵。
- **openalex**：用 OpenAlex 公开 API 查论文、引用、机构、资助与 DOI 元数据。
- **rebuttal-letter**：组织会议 rebuttal / 期刊回复审稿意见信。
- **research-skill-router**：把科研任务路由到合适本地 skill；按需安装外部 MIT/Apache skill。
- **scientific-visualization**：成图后质检：配色对比、PDF 元数据、导出规划。
- **scipilot-figure-skill**：图表类型建议与可视化反模式清单。
- **semantic-scholar**：用 Semantic Scholar 公开 API 查已发表会议/期刊论文与引用/TLDR。
- **venue-deadlines**：跟踪官方 CFP 截稿（AoE 换算）与有出处的录用率。

欢迎提 Issue 和 Pull Request。


## 关注
在 X 上关注 [@KingOfRW](https://x.com/KingOfRW)，看我们正在做什么。

---

# English

## Header
**We publish what we use.**

## ai-agent-skills
The agent skills we use every day. MIT licensed, ready to reuse.
- Repository: [https://github.com/TalentOS-AI/ai-agent-skills](https://github.com/TalentOS-AI/ai-agent-skills)
- Untested examples are clearly marked.
- Every commit is scanned for secrets and private data.

### Engineering skills (3)
- **sara-tool-authorization**: Stop untrusted tool outputs (email, web, MCP results) from silently becoming permission to act.
- **openai-agents-sdk-sandbox**: Build multi-agent workflows with the OpenAI Agents SDK (SandboxAgent, MCP, guardrails, handoffs, Realtime).
- **state-path-tool-menus**: For large tool/MCP libraries, build an ordered, executable tool menu (producers before consumers) instead of relevance-only retrieval.

### Research / academic skills (14)
Academic workflow skills Iris uses day to day, now open-sourced:
- **acl-latex-paper**: Write/compile ACL-family LaTeX papers (template, anonymity, page limits, compile checks).
- **acl-paper-figures**: Build print-size ACL/two-column matplotlib figures (Okabe-Ito, greyscale-safe) with audit helpers.
- **annotation-project**: Design labeled datasets: scheme, guidelines, IAA, LLM pre-annotation, data statement/licensing.
- **citation-audit**: Audit every bibliography entry for reality, attribution, and claim support (MBA/CSSCI-aware).
- **citation-verification**: Resolve every citation against DOI/Crossref/Anthology/arXiv before sharing refs.
- **deslop**: Strip AI writing tells and defensive hedging from academic prose (EN + Chinese journal extras).
- **literature-review**: Systematic literature search protocol, multi-source querying, snowballing, review matrix.
- **openalex**: Search OpenAlex for works, citation counts, affiliations, funding, DOI metadata via public API.
- **rebuttal-letter**: Structure conference rebuttals / journal response-to-reviewers letters.
- **research-skill-router**: Route research tasks to the right local skill; install external MIT/Apache skills on demand.
- **scientific-visualization**: Post-figure QA: palette/contrast audit, PDF metadata, export planning.
- **scipilot-figure-skill**: Chart-type advice and viz anti-pattern checklist.
- **semantic-scholar**: Search Semantic Scholar for published venue papers with citations/TLDR via public API.
- **venue-deadlines**: Track official CFP deadlines (AoE conversion) and sourced acceptance rates.

Issues and pull requests are welcome.


## Follow
Follow [@KingOfRW](https://x.com/KingOfRW) on X to see what we are working on.
