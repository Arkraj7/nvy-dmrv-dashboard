/**
 * Urban Forest Park - canonical-host and legacy query redirect middleware
 * ---------------------------------------------------------------------------
 * Cloudflare Pages serves both `urbanforestpark.com` and
 * `www.urbanforestpark.com`. Canonical tags, sitemap entries, feeds and
 * JSON-LD all use the `www` host, so the apex host must redirect permanently
 * instead of serving a duplicate origin.
 *
 * Pages `_redirects` cannot match a hostname or a query string, so this
 * middleware also handles:
 *   - apex host -> www host
 *   - legacy `?job=<id>` links -> the canonical `/jobs/<slug>` dossier URL
 *     (or a matching hub when the record was removed/quarantined)
 *
 * Pages Functions middleware runs for every request on the Pages project.
 * Requests on the canonical `www` host (and on `*.pages.dev` previews) pass
 * straight through unless they carry a `?job=` parameter.
 */

const APEX_HOST = "urbanforestpark.com";
const CANONICAL_HOST = "www.urbanforestpark.com";

export async function onRequest(context) {
  const url = new URL(context.request.url);

  if (url.hostname === APEX_HOST) {
    const target = `https://${CANONICAL_HOST}${url.pathname}${url.search}`;
    return Response.redirect(target, 301);
  }

  const jobId = url.searchParams.get("job");
  if (jobId) {
    const key = jobId.trim();
    let target = null;
    try {
      const assetUrl = new URL("/job_redirects.json", url);
      const res = await context.env.ASSETS.fetch(assetUrl);
      if (res.ok) {
        const map = await res.json();
        target = map[key];
      }
    } catch (e) {
      // Fall through to the generic cleanup below.
    }

    if (target) {
      const redirectUrl = new URL(target, url);
      redirectUrl.search = "";
      return Response.redirect(redirectUrl.toString(), 301);
    }

    // Unknown legacy job id: drop the query parameter and keep the path.
    url.searchParams.delete("job");
    return Response.redirect(url.toString(), 302);
  }

  return context.next();
}
