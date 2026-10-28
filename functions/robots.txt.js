/**
 * Serve the repository's own robots.txt without Cloudflare's managed
 * content injection, so custom rules such as Disallow: /cdn-cgi/ survive.
 */
export async function onRequest(context) {
  const url = new URL(context.request.url);
  const res = await context.env.ASSETS.fetch(new URL("/robots.txt", url));
  const body = await res.text();
  return new Response(body, {
    status: res.status,
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}
