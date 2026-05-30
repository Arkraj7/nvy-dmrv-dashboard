export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const response = await env.ASSETS.fetch(request);

    // For custom domain, remove X-Robots-Tag if present
    if (!url.hostname.endsWith('.pages.dev')) {
      const newHeaders = new Headers(response.headers);
      newHeaders.delete('X-Robots-Tag');
      newHeaders.delete('x-robots-tag');
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders,
      });
    }

    return response;
  },
};
