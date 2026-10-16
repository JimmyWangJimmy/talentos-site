// Public endpoint (no secrets). Worker: /workspace/site/callback-api, route POST /checkup-request → KV.
export const CHECKUP_ENDPOINT =
  (import.meta.env && import.meta.env.PUBLIC_CHECKUP_ENDPOINT) ||
  "https://talentos-callback-api.jimmywangjimmy.workers.dev/checkup-request";
export const CHECKUP_EMAIL = "talentos@agentbay.asia";
