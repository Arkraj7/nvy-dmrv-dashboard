export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    if (url.hostname.includes('pages.dev')) {
      const response = await env.ASSETS.fetch(request);
      const newHeaders = new Headers(response.headers);
      newHeaders.set('X-Robots-Tag', 'noindex');
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders,
      });
    }
    
    return env.ASSETS.fetch(request);
  },
};
