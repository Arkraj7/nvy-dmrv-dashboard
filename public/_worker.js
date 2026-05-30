export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const response = await env.ASSETS.fetch(request);

    if (url.hostname.endsWith('.pages.dev')) {
      const headers = new Headers(response.headers);
      headers.set('X-Robots-Tag', 'noindex');
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    }

    return response;
  },
};
