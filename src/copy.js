// Loads page copy from src/content/pages/*.md (Chinese section first, "# English" second; "## " = one block).
import { marked } from 'marked';
import { url } from './i18n.js';
const files = import.meta.glob('./content/pages/*.md', { query: '?raw', import: 'default', eager: true });
const raw = (n) => files[`./content/pages/${n}.md`];
const routes = { '/': 'home', '/services': 'services', '/open-source': 'research', '/about': 'about', '/contact': 'contact', '/checkup': 'checkup' };
function fixLinks(html, lang) {
  return html.replace(/href="(\/[^"#]*)(#[^"]*)?"/g, (m, p, h = '') => {
    const k = routes[p.replace(/\/$/, '') || '/'];
    return k ? `href="${url(lang, k)}${h}"` : m;
  });
}
export function meta(lang, slug) {
  const path = slug === 'home' ? '/' : `/${slug}`;
  const row = raw('meta').split('\n').map(l => l.split('|').map(s => s.trim())).find(c => c[2] === path);
  return lang === 'zh' ? { title: row[3], description: row[4] } : { title: row[5], description: row[6] };
}
export function page(lang, slug) {
  const src = raw(slug).split(/^# English\s*$/m)[lang === 'zh' ? 0 : 1].split(/^# 中文\s*$/m).pop();
  const blocks = src.split(/^## /m).slice(1).map(b => {
    let [head, ...rest] = b.split('\n');
    let body = rest.join('\n').replace(/^---\s*$/m, '').trim();
    let id; head = head.replace(/\s*\{#([\w-]+)\}\s*$/, (_, i) => { id = i; return ''; }).trim();
    return { head, id, body };
  });
  const [hero, ...rest] = blocks;
  const lines = hero.body.split('\n');
  const h1 = lines[0].replace(/^\*\*|\*\*$/g, '');
  const heroHtml = fixLinks(marked.parse(lines.slice(1).join('\n')), lang);
  const sections = rest.map(s => ({
    ...s,
    secondary: /次要入口|Secondary entry/.test(s.head),
    html: fixLinks(marked.parse(s.body), lang),
  }));
  return { h1, heroHtml, sections };
}
