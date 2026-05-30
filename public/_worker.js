export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const response = await env.ASSETS.fetch(request);

    // For custom domain, strip the noindex header that _headers adds
    if (!url.hostname.endsWith('.pages.dev')) {
      const headers = new Headers(response.headers);
      headers.delete('X-Robots-Tag');
      headers.delete('x-robots-tag');
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    }

    return response;
  },
};
