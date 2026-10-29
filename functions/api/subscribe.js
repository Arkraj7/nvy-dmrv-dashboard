/**
 * Urban Forest Park - Mandate Dispatch subscription endpoint
 * ---------------------------------------------------------------------------
 * Cloudflare Pages Function, deployed automatically with the site
 * (`wrangler pages deploy dist` bundles the /functions directory).
 *
 *   POST /api/subscribe
 *   Content-Type: application/json
 *   { "email": "name@example.in", "frequency": "3-days" | "weekly",
 *     "sector": "all" | "academic" | "forestry-gis" | "corporate-esg" }
 *
 * Response:
 *   { "ok": true, "persisted": true|false, "storage": "github|kv|webhook|none",
 *     "welcome": "queued|already_sent|not_configured|failed" }
 *
 * Persistence cascade (first successful store wins, all configured stores are
 * mirrored where possible):
 *
 *   1. GitHub Contents API - `GITHUB_PAT` (or `GITHUB_TOKEN`) plus
 *      `GITHUB_REPO` (defaults to this repository). The subscriber is
 *      upserted into `data/subscribers.json` on `main`, which is the same
 *      file read by scripts/send_newsletter.py in GitHub Actions. The PAT
 *      needs `contents: write` and `actions: write` (repository_dispatch).
 *
 *   2. Cloudflare KV binding `UFP_SUBSCRIBERS` (legacy alias
 *      `NEWSLETTER_KV`). Subscribers are stored under `sub:<email>` as JSON.
 *      This is the durable zero-GitHub-token fallback.
 *
 *   3. `NEWSLETTER_WEBHOOK_URL` - any HTTPS endpoint that accepts a JSON POST
 *      (e.g. a Google Apps Script sheet writer). Optional
 *      `NEWSLETTER_WEBHOOK_TOKEN` is forwarded as `X-UFP-Token`.
 *
 *   4. No server-side store configured - the subscription is acknowledged
 *      with `persisted: false`. The frontend stores the preference on the
 *      subscriber's device, retries it on a later visit, and shows the
 *      contact-mailbox route, so a signup is never silently lost.
 *
 * Instant welcome email:
 *   A successful GitHub store fires a `welcome_email` repository_dispatch
 *   event. .github/workflows/newsletter_dispatch.yml consumes it, upserts the
 *   address (idempotent), sends `scripts/send_newsletter.py --welcome`, and
 *   commits the updated subscriber file. If repository_dispatch is
 *   unavailable, the function falls back to a workflow_dispatch event with
 *   `subscriber_email`, `frequency` and `sector` inputs.
 *
 * Deployment note:
 *   `GITHUB_REPO` is declared in the tracked wrangler.toml `[vars]` block.
 *   `GITHUB_PAT` is stored as an encrypted Pages secret:
 *     wrangler pages secret put GITHUB_PAT --project-name=nvy-dmrv-dashboard
 *   Pages secrets survive direct `wrangler pages deploy` uploads; plain
 *   dashboard-only variables do not. Never commit the PAT.
 */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const FREQUENCY_ALIASES = new Map([
  ["3-day", "3-days"],
  ["3-days", "3-days"],
  ["3days", "3-days"],
  ["3_days", "3-days"],
  ["every-3-days", "3-days"],
  ["weekly", "weekly"],
]);
const SECTORS = new Set(["all", "academic", "forestry-gis", "corporate-esg"]);
const CHANNELS = new Set(["email", "whatsapp", "telegram"]);
const DEFAULT_REPO = "Arkraj7/nvy-dmrv-dashboard";
const SUBSCRIBERS_PATH = "data/subscribers.json";
const BRANCH = "main";
const GITHUB_API = "https://api.github.com";

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

function clean(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeFrequency(value) {
  return FREQUENCY_ALIASES.get(clean(value).toLowerCase()) || null;
}

function normalizeSector(value) {
  const sector = clean(value).toLowerCase();
  return SECTORS.has(sector) ? sector : null;
}

function normalizeChannels(value) {
  const raw = Array.isArray(value)
    ? value
    : String(value || "").split(/[,;]/);
  const out = [];
  for (const item of raw) {
    const channel = clean(item).toLowerCase();
    if (CHANNELS.has(channel) && out.indexOf(channel) === -1) out.push(channel);
  }
  return out.length ? out : ["email"];
}

function normalizeSavedSearch(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const out = {};
  const fields = ["query", "category", "state", "city", "position_type", "experience_level", "role"];
  for (const field of fields) {
    const text = clean(value[field], 120);
    if (text) out[field] = text;
  }
  return Object.keys(out).length ? out : null;
}

function githubToken(env) {
  return clean(env && (env.GITHUB_PAT || env.GITHUB_TOKEN));
}

function repoName(env) {
  return clean(env && env.GITHUB_REPO) || DEFAULT_REPO;
}

function githubHeaders(token) {
  return {
    Authorization: "Bearer " + token,
    Accept: "application/vnd.github+json",
    "Content-Type": "application/json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "urbanforestpark-subscribe",
  };
}

/* Workers expose btoa/atob; TextEncoder/TextDecoder keep non-ASCII emails and
   names intact across the GitHub Contents API. */
function encodeBase64(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (let index = 0; index < bytes.length; index += 1) {
    binary += String.fromCharCode(bytes[index]);
  }
  return btoa(binary);
}

function decodeBase64(value) {
  const binary = atob(String(value || "").replace(/\s+/g, ""));
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new TextDecoder().decode(bytes);
}

function parseSubscribers(text) {
  const parsed = JSON.parse(String(text || "[]"));
  const list = Array.isArray(parsed)
    ? parsed
    : Array.isArray(parsed && parsed.subscribers)
      ? parsed.subscribers
      : [];
  return list.filter((item) => item && typeof item === "object" && !Array.isArray(item));
}

function serialiseSubscribers(records) {
  return JSON.stringify(records, null, 2) + "\n";
}

function findRecord(records, email) {
  const needle = clean(email).toLowerCase();
  for (const record of records) {
    if (clean(record && record.email).toLowerCase() === needle) return record;
  }
  return null;
}

function mergeRecord(existing, incoming) {
  if (!existing) {
    return {
      ...incoming,
      active: true,
      welcome_sent: false,
      welcome_queued: false,
    };
  }

  return {
    ...existing,
    ...incoming,
    active: true,
    subscribed_at: existing.subscribed_at || incoming.subscribed_at,
    welcome_sent: existing.welcome_sent === true,
    welcome_sent_at: existing.welcome_sent_at,
    welcome_queued: existing.welcome_sent === true ? false : existing.welcome_queued === true,
    welcome_queued_at: existing.welcome_queued_at,
    updated_at: incoming.updated_at,
  };
}

function welcomeAlreadyHandled(record) {
  if (!record) return false;
  if (record.welcome_sent === true) return true;
  if (record.welcome_queued === true) {
    const queuedAt = Date.parse(clean(record.welcome_queued_at));
    if (!Number.isFinite(queuedAt) || Date.now() - queuedAt < 24 * 60 * 60 * 1000) {
      return true;
    }
  }
  return false;
}

async function readGitHubSubscribers(env) {
  const token = githubToken(env);
  if (!token) return null;

  const repo = repoName(env);
  const url = `${GITHUB_API}/repos/${repo}/contents/${SUBSCRIBERS_PATH}?ref=${encodeURIComponent(BRANCH)}`;
  const response = await fetch(url, { headers: githubHeaders(token) });

  if (response.status === 404) {
    return { records: [], sha: null };
  }
  if (!response.ok) {
    throw new Error(`GitHub contents read failed (HTTP ${response.status})`);
  }

  const payload = await response.json();
  return {
    records: parseSubscribers(decodeBase64(payload.content || "")),
    sha: payload.sha || null,
  };
}

async function writeGitHubSubscribers(env, records, sha, message) {
  const token = githubToken(env);
  if (!token) return false;

  const repo = repoName(env);
  const body = {
    message,
    content: encodeBase64(serialiseSubscribers(records)),
    branch: BRANCH,
  };
  if (sha) body.sha = sha;

  const response = await fetch(
    `${GITHUB_API}/repos/${repo}/contents/${SUBSCRIBERS_PATH}`,
    {
      method: "PUT",
      headers: githubHeaders(token),
      body: JSON.stringify(body),
    }
  );
  return response.ok;
}

async function upsertGitHubSubscriber(env, incoming) {
  if (!githubToken(env)) return { ok: false, reason: "not_configured" };

  let lastError = "unknown";
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const current = await readGitHubSubscribers(env);
      const records = current.records;
      const existing = findRecord(records, incoming.email);
      const merged = mergeRecord(existing, incoming);

      if (existing) {
        records[records.indexOf(existing)] = merged;
      } else {
        records.push(merged);
      }

      const message = existing
        ? `chore(subscribers): update ${incoming.email}`
        : `chore(subscribers): add ${incoming.email}`;
      const written = await writeGitHubSubscribers(env, records, current.sha, message);
      if (written) {
        return {
          ok: true,
          storage: "github",
          existing,
          record: merged,
        };
      }
      lastError = "GitHub contents write failed";
    } catch (error) {
      lastError = String((error && error.message) || error);
    }
  }

  return { ok: false, reason: lastError };
}

function kvBinding(env) {
  const binding = env && (env.UFP_SUBSCRIBERS || env.NEWSLETTER_KV);
  if (!binding || typeof binding.get !== "function" || typeof binding.put !== "function") {
    return null;
  }
  return binding;
}

async function upsertKVSubscriber(env, incoming) {
  const kv = kvBinding(env);
  if (!kv) return { ok: false, reason: "not_configured" };

  try {
    const raw = await kv.get("sub:" + incoming.email);
    let existing = null;
    if (raw) {
      try {
        existing = JSON.parse(raw);
      } catch (error) {
        existing = null;
      }
    }
    const merged = mergeRecord(existing, incoming);
    await kv.put("sub:" + incoming.email, JSON.stringify(merged));
    return {
      ok: true,
      storage: "kv",
      existing,
      record: merged,
    };
  } catch (error) {
    return { ok: false, reason: String((error && error.message) || error) };
  }
}

async function forwardWebhook(env, record) {
  if (!env || !env.NEWSLETTER_WEBHOOK_URL) return { ok: false, reason: "not_configured" };

  try {
    const headers = { "Content-Type": "application/json" };
    if (env.NEWSLETTER_WEBHOOK_TOKEN) {
      headers["X-UFP-Token"] = env.NEWSLETTER_WEBHOOK_TOKEN;
    }
    const response = await fetch(env.NEWSLETTER_WEBHOOK_URL, {
      method: "POST",
      headers,
      body: JSON.stringify(record),
    });
    return response.ok
      ? { ok: true, storage: "webhook" }
      : { ok: false, reason: `webhook HTTP ${response.status}` };
  } catch (error) {
    return { ok: false, reason: String((error && error.message) || error) };
  }
}

async function triggerWelcomeEmail(env, record) {
  const token = githubToken(env);
  if (!token) return { status: "not_configured" };

  const repo = repoName(env);
  const payload = {
    subscriber_email: record.email,
    email: record.email,
    frequency: record.frequency,
    sector: record.sector,
    source: record.source,
  };

  try {
    const dispatch = await fetch(`${GITHUB_API}/repos/${repo}/dispatches`, {
      method: "POST",
      headers: githubHeaders(token),
      body: JSON.stringify({
        event_type: "welcome_email",
        client_payload: payload,
      }),
    });
    if (dispatch.ok) {
      return { status: "queued", via: "repository_dispatch" };
    }

    const workflow = await fetch(
      `${GITHUB_API}/repos/${repo}/actions/workflows/newsletter_dispatch.yml/dispatches`,
      {
        method: "POST",
        headers: githubHeaders(token),
        body: JSON.stringify({
          ref: BRANCH,
          inputs: {
            subscriber_email: record.email,
            frequency: record.frequency,
            sector: record.sector,
          },
        }),
      }
    );
    if (workflow.ok) {
      return { status: "queued", via: "workflow_dispatch" };
    }
    return {
      status: "failed",
      via: "workflow_dispatch",
      http: workflow.status,
    };
  } catch (error) {
    return { status: "failed", error: String((error && error.message) || error) };
  }
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const runtimeEnv = env || {};

  let payload;
  try {
    payload = await request.json();
  } catch (error) {
    return json({ ok: false, error: "invalid_json" }, 400);
  }
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return json({ ok: false, error: "invalid_payload" }, 400);
  }

  const email = clean(payload.email).toLowerCase();
  if (!email || email.length > 254 || !EMAIL_RE.test(email)) {
    return json({ ok: false, error: "invalid_email" }, 422);
  }

  const requestedFrequency = clean(payload.frequency);
  const frequency = normalizeFrequency(requestedFrequency) || (requestedFrequency ? null : "3-days");
  if (!frequency) {
    return json(
      {
        ok: false,
        error: "invalid_frequency",
        allowed: ["3-days", "weekly"],
      },
      422
    );
  }

  const requestedSector = clean(payload.sector);
  const sector = normalizeSector(requestedSector) || (requestedSector ? null : "all");
  if (!sector) {
    return json(
      {
        ok: false,
        error: "invalid_sector",
        allowed: Array.from(SECTORS),
      },
      422
    );
  }

  const channels = normalizeChannels(payload.channels);
  const savedSearch = normalizeSavedSearch(payload.saved_search || payload.savedSearch);
  const whatsappNumber = clean(payload.whatsapp_number || payload.whatsappNumber, 40);

  const now = new Date().toISOString();
  const record = {
    email,
    frequency,
    sector,
    channels,
    saved_search: savedSearch,
    whatsapp_number: whatsappNumber || null,
    active: true,
    source: "urbanforestpark.com",
    subscribed_at: now,
    updated_at: now,
    user_agent: request.headers.get("User-Agent") || "",
    welcome_sent: false,
    welcome_queued: false,
  };

  const github = await upsertGitHubSubscriber(runtimeEnv, record);
  const kv = await upsertKVSubscriber(runtimeEnv, record);

  let persistence = null;
  if (github.ok) {
    persistence = { ...github, storage: kv.ok ? "github+kv" : "github" };
  } else if (kv.ok) {
    persistence = kv;
  } else {
    const webhook = await forwardWebhook(runtimeEnv, record);
    if (webhook.ok) persistence = webhook;
  }

  const persisted = !!(persistence && persistence.ok);
  const existing = (github.ok && github.existing) || (kv.ok && kv.existing) || null;
  const welcomePromise = welcomeAlreadyHandled(existing)
    ? Promise.resolve({ status: "already_sent" })
    : triggerWelcomeEmail(runtimeEnv, record);
  if (typeof context.waitUntil === "function") {
    context.waitUntil(welcomePromise);
  }
  const welcome = await welcomePromise;

  if (!persisted) {
    /* Cloudflare Pages Function logs are the zero-key durable trace. The
       browser also stores the preference locally and retries it later. */
    console.log(
      JSON.stringify({
        event: "subscriber_unpersisted",
        email,
        frequency,
        sector,
        at: now,
      })
    );
  }

  return json({
    ok: true,
    persisted,
    storage: persistence ? persistence.storage : "none",
    welcome: welcome.status,
    welcome_via: welcome.via || null,
    channels,
    saved_search: savedSearch,
  });
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
