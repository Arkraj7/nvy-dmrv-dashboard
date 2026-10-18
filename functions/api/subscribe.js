/**
 * Urban Forest Park — Mandate Dispatch subscription endpoint
 * ---------------------------------------------------------------------------
 * Cloudflare Pages Function, deployed automatically with the site
 * (`wrangler pages deploy dist` bundles the /functions directory).
 *
 *   POST /api/subscribe
 *   Content-Type: application/json
 *   { "email": "…", "frequency": "3-day" | "weekly", "sector": "all" | "academic" | "forestry-gis" | "corporate-esg" }
 *
 * Response:  { "ok": true, "persisted": true|false }
 *
 * Persistence cascade (configured entirely through the Pages project's
 * environment variables / bindings — no code change required):
 *
 *   1. KV binding `NEWSLETTER_KV`
 *      Pages project → Settings → Functions → KV namespace bindings:
 *          Variable name: NEWSLETTER_KV
 *      Subscribers are stored under `sub:<email>` as JSON. Recommended.
 *
 *   2. Environment variable `NEWSLETTER_WEBHOOK_URL`
 *      Any HTTPS endpoint that accepts a JSON POST — e.g. the companion
 *      Google Apps Script in google-apps-script/newsletter-subscribe.gs
 *      (writes straight into a Google Sheet; free to host). Optionally set
 *      `NEWSLETTER_WEBHOOK_TOKEN` and it is forwarded as the
 *      `X-UFP-Token` header for shared-secret verification.
 *
 *   3. Neither configured → the subscription is acknowledged
 *      (`persisted: false`) and the frontend transparently records the
 *      preference on the subscriber's device, showing the contact-mailbox
 *      route so no request is ever lost or errors out.
 *
 * The main-site copy of the subscriber list used by the 3-day mailer
 * (scripts/send_newsletter.py) can come from repository data
 * (data/subscribers.json), a 📄 published Google Sheet CSV
 * (NEWSLETTER_SUBSCRIBERS_CSV), or a workflow secret
 * (NEWSLETTER_SUBSCRIBERS). See the mailer script header for details.
 */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const FREQUENCIES = new Set(["3-day", "weekly"]);
const SECTORS = new Set(["all", "academic", "forestry-gis", "corporate-esg"]);

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;

  let payload;
  try {
    payload = await request.json();
  } catch (err) {
    return json({ ok: false, error: "invalid_json" }, 400);
  }
  if (!payload || typeof payload !== "object") {
    return json({ ok: false, error: "invalid_payload" }, 400);
  }

  const email = String(payload.email || "").trim().toLowerCase();
  const frequency = FREQUENCIES.has(String(payload.frequency)) ? String(payload.frequency) : "3-day";
  const sector = SECTORS.has(String(payload.sector)) ? String(payload.sector) : "all";

  if (email.length === 0 || email.length > 254 || !EMAIL_RE.test(email)) {
    return json({ ok: false, error: "invalid_email" }, 422);
  }

  const record = {
    email,
    frequency,
    sector,
    source: "urbanforestpark.com",
    subscribed_at: new Date().toISOString(),
    user_agent: request.headers.get("User-Agent") || "",
  };

  // 1. KV binding ---------------------------------------------------------
  if (env && env.NEWSLETTER_KV && typeof env.NEWSLETTER_KV.put === "function") {
    try {
      await env.NEWSLETTER_KV.put("sub:" + email, JSON.stringify(record));
      return json({ ok: true, persisted: true, storage: "kv" });
    } catch (err) {
      // Fall through to the webhook / acknowledgement paths below.
    }
  }

  // 2. Webhook forwarding -------------------------------------------------
  if (env && env.NEWSLETTER_WEBHOOK_URL) {
    try {
      const headers = { "Content-Type": "application/json" };
      if (env.NEWSLETTER_WEBHOOK_TOKEN) {
        headers["X-UFP-Token"] = env.NEWSLETTER_WEBHOOK_TOKEN;
      }
      const upstream = await fetch(env.NEWSLETTER_WEBHOOK_URL, {
        method: "POST",
        headers,
        body: JSON.stringify(record),
      });
      if (upstream.ok) {
        return json({ ok: true, persisted: true, storage: "webhook" });
      }
    } catch (err) {
      // Fall through to the acknowledgement path below.
    }
  }

  // 3. Acknowledgement without server-side persistence --------------------
  // The frontend records the preference on the subscriber's device and
  // surfaces the contact route; this must never surface as a hard error.
  return json({ ok: true, persisted: false, storage: "client" });
}

export async function onRequestGet() {
  return json({ ok: false, error: "method_not_allowed" }, 405);
}

export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      "Allow": "POST, OPTIONS",
      "Cache-Control": "no-store",
    },
  });
}
