import { defineConfig } from 'astro/config';
// Preview (github.io project page): defaults below.
// Custom domain: set SITE_URL=https://www.agentbay.asia and SITE_BASE=/ (see README).
export default defineConfig({
  site: process.env.SITE_URL || 'https://jimmywangjimmy.github.io',
  base: process.env.SITE_BASE || '/talentos-site',
  trailingSlash: 'always',
  build: { inlineStylesheets: 'always' },
});
