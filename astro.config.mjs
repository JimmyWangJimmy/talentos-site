import { defineConfig } from 'astro/config';
// Preview (github.io project page): defaults below.
// Custom domain: set SITE_URL=https://www.agentbay.asia and SITE_BASE=/ (see README).
export default defineConfig({
  site: process.env.SITE_URL || 'https://www.agentbay.asia',
  base: process.env.SITE_BASE || '/',
  trailingSlash: 'always',
  build: { inlineStylesheets: 'always' },
});
