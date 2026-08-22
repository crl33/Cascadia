/**
 * Hostname gateway: cascadia.papsukkal.com → Cloudflare Pages production.
 * Git pushes auto-deploy the Pages project; this Worker only attaches the custom
 * domain (Wrangler OAuth can create Worker custom domains, not zone DNS records).
 */
const PAGES_HOST = "cascadia-c7y.pages.dev";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    url.hostname = PAGES_HOST;
    return fetch(new Request(url, request));
  },
};
