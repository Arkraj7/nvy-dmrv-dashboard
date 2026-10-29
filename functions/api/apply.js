/**
 * POST /api/apply
 * Lightweight application-funnel ping. Records "I applied" events as a
 * Telegram notification to the editor/admin when a bot token is configured,
 * and always returns 200 so the client can keep its localStorage counter in
 * sync. No candidate PII is required or stored.
 */
const TELEGRAM_API = "https://api.telegram.org/bot";

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

function clean(value, max) {
  const text = String(value == null ? "" : value).replace(/\s+/g, " ").trim();
  return max ? text.slice(0, max) : text;
}

export async function onRequestPost(context) {
  const { request, env } = context;
  let payload = {};
  try { payload = await request.json(); } catch (e) { payload = {}; }
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) payload = {};

  const jobId = clean(payload.job_id || payload.jobId, 120);
  const title = clean(payload.title || payload.job_title, 180);
  const org = clean(payload.organization || payload.org, 160);
  const location = clean(payload.location || payload.city, 120);
  const url = clean(payload.url || payload.apply_url, 400);

  const record = {
    event: "job_applied",
    job_id: jobId || null,
    title: title || null,
    organization: org || null,
    location: location || null,
    url: url || null,
    at: new Date().toISOString(),
    user_agent: request.headers.get("User-Agent") || "",
  };

  const token = clean(env && (env.TELEGRAM_BOT_TOKEN || env.TELEGRAM_INBOX_BOT_TOKEN), 200);
  const chatId = clean(env && (env.TELEGRAM_ADMIN_USER_ID || env.TELEGRAM_ADMIN_CHAT_ID), 60);
  let telegram = { status: "not_configured" };
  if (token && chatId) {
    try {
      const text =
        "Applied: " + (title || jobId || "unknown role") +
        (org ? " at " + org : "") +
        (location ? " (" + location + ")" : "") +
        (url ? "\n" + url : "");
      const response = await fetch(`${TELEGRAM_API}${token}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId, text: text }),
      });
      telegram = response.ok
        ? { status: "sent" }
        : { status: "failed", http: response.status };
    } catch (error) {
      telegram = { status: "failed", error: String((error && error.message) || error) };
    }
  }

  console.log(JSON.stringify(record));
  return json({ ok: true, recorded: true, telegram: telegram.status });
}

export async function onRequestGet() {
  return json({ ok: false, error: "method_not_allowed" }, 405);
}

export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      Allow: "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Cache-Control": "no-store",
    },
  });
}