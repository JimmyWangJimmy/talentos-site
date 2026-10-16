/**
 * Boss/strategy 2026-10-16: option A — long-term workers.dev (no api. TLS).
 * Override with PUBLIC_CALLBACK_API_BASE if needed; brand domain later = option C.
 */
export const CALLBACK_API_BASE =
  (typeof import.meta !== "undefined" &&
    import.meta.env &&
    import.meta.env.PUBLIC_CALLBACK_API_BASE) ||
  "https://talentos-callback-api.jimmywangjimmy.workers.dev";

export const CALLBACK_API_PATH = "/api/callback-request";

export function callbackEndpoint() {
  return `${String(CALLBACK_API_BASE).replace(/\/$/, "")}${CALLBACK_API_PATH}`;
}
