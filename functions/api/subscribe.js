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
 * Instant welcome email (optional, first configured channel wins):
 *
 *   1. `GITHUB_PAT` + `GITHUB_REPO` (e.g. "owner/urbanforestpark")
 *      Fires a repository_dispatch event `welcome_email` whose payload is
 *      consumed by .github/workflows/newsletter_dispatch.yml, which runs
 *      `scripts/send_newsletter.py --welcome <email>` — so the new
 *      subscriber receives the formal onboarding email within minutes.
 *      The PAT needs `contents: write` (fine-grained, this repository only).
 *
 *   2. `WELCOME_WEBHOOK_URL`
 *      Any HTTPS endpoint that accepts a JSON POST with the full subscriber
 *      record plus `{"event": "welcome_email"}`.
 *
 * The trigger is fire-and-forget (`context.waitUntil`) and never blocks or
 * breaks the subscription response. Re-submissions of an address that was
 * already queued/welcomed are skipped, so no duplicate welcomes are sent.
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

/* Fire the instant-welcome trigger. Fire-and-forget: never throws. */
async function triggerWelcomeEmail(env, record) {
  try {
    if (env && env.GITHUB_PAT && env.GITHUB_REPO) {
      const response = await fetch(
        "https://api.github.com/repos/" + env.GITHUB_REPO + "/dispatches",
        {
          method: "POST",
          headers: {
            Authorization: "Bearer " + env.GITHUB_PAT,
            Accept: "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "urbanforestpark-subscribe",
          },
          body: JSON.stringify({
            event_type: "welcome_email",
            client_payload: {
              email: record.email,
              frequency: record.frequency,
              sector: record.sector,
              source: record.source,
            },
          }),
        }
      );
      return response.ok ? "github" : "github_failed";
    }
    if (env && env.WELCOME_WEBHOOK_URL) {
      const response = await fetch(env.WELCOME_WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event: "welcome_email", ...record }),
      });
      return response.ok ? "webhook" : "webhook_failed";
    }
  } catch (err) {
    return "failed";
  }
  return "not_configured";
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

  /* Skip the welcome trigger for an address already queued/welcomed. */
  let alreadyKnown = false;
  if (env && env.NEWSLETTER_KV && typeof env.NEWSLETTER_KV.get === "function") {
    try {
      const existing = await env.NEWSLETTER_KV.get("sub:" + email);
      alreadyKnown = !!(
        existing && /"welcome_sent"\s*:\s*true|"welcome_queued"\s*:\s*true/.test(existing)
      );
    } catch (err) {
      /* A KV read failure must never block the subscription. */
    }
  }

  const canTrigger = !alreadyKnown &&
    !!((env && env.GITHUB_PAT && env.GITHUB_REPO) || (env && env.WELCOME_WEBHOOK_URL));

  const record = {
    email,
    frequency,
    sector,
    source: "urbanforestpark.com",
    subscribed_at: new Date().toISOString(),
    user_agent: request.headers.get("User-Agent") || "",
    welcome_sent: false,
    welcome_queued: alreadyKnown || canTrigger,
  };

  /* 1. KV binding --------------------------------------------------------- */
  let storage = "client";
  let persisted = false;
  if (env && env.NEWSLETTER_KV && typeof env.NEWSLETTER_KV.put === "function") {
    try {
      await env.NEWSLETTER_KV.put("sub:" + email, JSON.stringify(record));
      storage = "kv";
      persisted = true;
    } catch (err) {
      // Fall through to the webhook / acknowledgement paths below.
    }
  }

  /* 2. Webhook forwarding ------------------------------------------------- */
  if (!persisted && env && env.NEWSLETTER_WEBHOOK_URL) {
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
        storage = "webhook";
        persisted = true;
      }
    } catch (err) {
      // Fall through to the acknowledgement path below.
    }
  }

  /* 3. Instant welcome email (fire-and-forget) ----------------------------- */
  if (canTrigger) {
    const trigger = triggerWelcomeEmail(env, record);
    if (typeof context.waitUntil === "function") {
      context.waitUntil(trigger);
    }
  }

  /* 4. Acknowledgement without server-side persistence --------------------- */
  // The frontend records the preference on the subscriber's device and
  // surfaces the contact route; this must never surface as a hard error.
  return json({ ok: true, persisted, storage });
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
