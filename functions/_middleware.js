/**
 * Urban Forest Park - canonical-host middleware
 * ---------------------------------------------------------------------------
 * Cloudflare Pages serves both `urbanforestpark.com` and
 * `www.urbanforestpark.com`. Canonical tags, sitemap entries, feeds and
 * JSON-LD all use the `www` host, so the apex host must redirect permanently
 * instead of serving a duplicate origin.
 *
 * Pages `_redirects` cannot match a hostname, but Pages Functions middleware
 * can. This runs for every request on the Pages project. Requests on the
 * canonical `www` host (and on `*.pages.dev` previews) pass straight through.
 */

const APEX_HOST = "urbanforestpark.com";
const CANONICAL_HOST = "www.urbanforestpark.com";

export async function onRequest(context) {
  const url = new URL(context.request.url);

  if (url.hostname === APEX_HOST) {
    const target = `https://${CANONICAL_HOST}${url.pathname}${url.search}`;
    return Response.redirect(target, 301);
  }

  return context.next();
}
