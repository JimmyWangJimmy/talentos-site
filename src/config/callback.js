/**
 * Preview: set PUBLIC_CALLBACK_API_BASE to workers.dev URL after deploy.
 * Production: https://api.agentbay.asia
 */
export const CALLBACK_API_BASE =
  (typeof import.meta !== "undefined" &&
    import.meta.env &&
    import.meta.env.PUBLIC_CALLBACK_API_BASE) ||
  "https://api.agentbay.asia";

export const CALLBACK_API_PATH = "/api/callback-request";

export function callbackEndpoint() {
  return `${String(CALLBACK_API_BASE).replace(/\/$/, "")}${CALLBACK_API_PATH}`;
}
