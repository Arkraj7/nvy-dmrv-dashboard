export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const response = await fetch(request);
    
    if (url.hostname.includes('pages.dev')) {
      const newHeaders = new Headers(response.headers);
      newHeaders.set('X-Robots-Tag', 'noindex');
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders,
      });
    }
    
    return response;
  },
};
