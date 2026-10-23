/**
 * Telegram intake webhook
 * ---------------------------------------------------------------------------
 * POST /api/telegram
 *
 * Receives Telegram updates from the @ufp_flyer_intake_bot and turns a pasted
 * job email, a job URL, an image, or a PDF into a structured job draft. The
 * draft is returned to the editor in Telegram; nothing is published
 * automatically. Human approval still happens in the Syndication Desk.
 *
 * GET /api/telegram?setup=<TELEGRAM_SETUP_SECRET>
 * Registers the production webhook with Telegram. The bot token stays in the
 * Pages secret TELEGRAM_INBOX_BOT_TOKEN and is never returned or logged.
 *
 * Optional secrets/vars:
 *   TELEGRAM_INBOX_BOT_TOKEN  bot token (required)
 *   TELEGRAM_WEBHOOK_SECRET   Telegram X-Telegram-Bot-Api-Secret-Token value
 *   TELEGRAM_SETUP_SECRET     one-off setup/test gate
 *   TELEGRAM_ADMIN_USER_ID    restrict intake to this Telegram user/chat
 *   TELEGRAM_WEBHOOK_URL      override the registered HTTPS endpoint
 */

import {
  CATEGORIES,
  POSITION_TYPES,
  OPPORTUNITY_KINDS,
  RESPONSE_SCHEMA,
  FALLBACK_MODELS,
  normalizeJob,
  parseModelJson,
} from "./parse_flyer.js";
import { commitJobRecord } from "./commit_job.js";

const GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models";
const DEFAULT_MODEL = "gemini-2.5-flash";
const TELEGRAM_API = "https://api.telegram.org/bot";
const SITE = "https://www.urbanforestpark.com";
const DEFAULT_WEBHOOK_URL = SITE + "/api/telegram";
const MAX_FILE_BYTES = 8 * 1024 * 1024;
const MAX_TEXT_CHARS = 24000;
const MAX_PAGE_BYTES = 2 * 1024 * 1024;
const BLOCKED_HOSTS = [
  /(^|\.)linkedin\.com$/i,
  /(^|\.)indeed\.com$/i,
  /(^|\.)naukri\.com$/i,
];

const TEXT_PROMPT = `You are the intake editor for Urban Forest Park, a verified green-jobs
registry for India and international climate, environment, forestry, ESG and
sustainability opportunities.

Read the supplied job notice, email, or job-page text and extract ONE job,
fellowship, internship, scholarship, grant or competition. Return only the JSON
object requested by the schema.

Rules:
- Copy facts exactly as printed. Never invent a salary, deadline, eligibility
  requirement, website, or application URL.
- clean_title: the role title, without emojis, "Apply now", or email subject
  prefixes such as "Job Alert:".
- organization: the employer or host institution's proper name.
- city/state: use the duty station. Leave state empty outside India. If the
  notice says remote, home-based or multiple locations, put "Remote" or the
  printed location in city.
- country: the host country in plain English. Use "Global" only for a genuinely
  worldwide/remote opportunity.
- category and position_type: choose exactly one allowed value supplied by the
  caller. If none fits, use the closest career-track value.
- opportunity_kind: Job / Career, Fellowship, Scholarship, Grant / Funding,
  Internship, or Competition / Award.
- stipend_or_salary: only the printed amount/currency/period; otherwise
  "Not disclosed - see official portal".
- qualification_summary: one short sentence with the printed degree/experience.
  Do not add requirements that are not visible.
- must_have_skills: 4-7 short tags grounded in the notice.
- application_deadline: printed closing date, or "Rolling / Open" if none.
- application_url: the printed official application URL. If the notice only
  gives a source/job-page URL supplied by the caller, use that URL only when it
  is a specific job/notice page, never a careers home or search page. Never
  guess.
- org_website: the organisation's official homepage if printed; otherwise
  empty. Do not put the application URL here.
- role_summary: 2-3 factual sentences, 40-70 words, using only the supplied
  content.
- key_responsibilities: up to 5 short bullets supported by the notice.`;

function clean(value, max) {
  const text = String(value == null ? "" : value).replace(/\s+/g, " ").trim();
  return max ? text.slice(0, max) : text;
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

function telegramToken(env) {
  return clean(env && (env.TELEGRAM_INBOX_BOT_TOKEN || env.TELEGRAM_BOT_TOKEN));
}

async function telegramApi(env, method, payload) {
  const token = telegramToken(env);
  if (!token) return { ok: false, error: "telegram_not_configured" };
  let response;
  try {
    response = await fetch(`${TELEGRAM_API}${token}/${method}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
  } catch (error) {
    return { ok: false, error: "telegram_unreachable" };
  }
  let body = {};
  try {
    body = await response.json();
  } catch (error) {
    body = {};
  }
  return {
    ok: response.ok && body.ok === true,
    status: response.status,
    result: body.result || null,
    error: clean(body.description || "telegram_error", 300),
  };
}

async function sendMessage(env, chatId, html, extra) {
  return telegramApi(env, "sendMessage", {
    chat_id: chatId,
    text: html,
    parse_mode: "HTML",
    disable_web_page_preview: true,
    ...(extra || {}),
  });
}

function safeHttpUrl(value) {
  const text = clean(value, 700);
  if (!/^https?:\/\//i.test(text)) return "";
  try {
    const url = new URL(text);
    if (!url.hostname || !url.hostname.includes(".")) return "";
    return url.toString();
  } catch (error) {
    return "";
  }
}

function isBlockedHost(hostname) {
  return BLOCKED_HOSTS.some((pattern) => pattern.test(String(hostname || "")));
}

function isPrivateHost(hostname) {
  const host = String(hostname || "").toLowerCase().replace(/^\[|\]$/g, "");
  if (!host) return true;
  if (host === "localhost" || host.endsWith(".localhost") || host.endsWith(".local") || host.endsWith(".internal")) {
    return true;
  }
  if (host === "::1" || host === "0:0:0:0:0:0:0:1" || host.startsWith("fc") || host.startsWith("fd") || host.startsWith("fe80")) {
    return true;
  }
  const parts = host.split(".");
  if (parts.length === 4 && parts.every((part) => /^\d{1,3}$/.test(part))) {
    const nums = parts.map(Number);
    if (nums.some((n) => n > 255)) return true;
    if (nums[0] === 10 || nums[0] === 127 || nums[0] === 0) return true;
    if (nums[0] === 169 && nums[1] === 254) return true;
    if (nums[0] === 172 && nums[1] >= 16 && nums[1] <= 31) return true;
    if (nums[0] === 192 && nums[1] === 168) return true;
    if (nums[0] === 100 && nums[1] >= 64 && nums[1] <= 127) return true;
    if (nums[0] >= 224) return true;
  }
  return false;
}

function extractUrl(text) {
  const match = String(text || "").match(/https?:\/\/[^\s<>"']+/i);
  if (!match) return "";
  const raw = match[0].replace(/[),.;:!?]+$/g, "");
  return safeHttpUrl(raw);
}

function jurisdictionFrom(text) {
  const haystack = String(text || "").toLowerCase();
  if (/#global\b|\/global\b|\bglobal\b|\binternational\b|\bworldwide\b/.test(haystack)) {
    return "global";
  }
  return "india";
}

function decodeEntities(text) {
  return String(text || "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)))
    .replace(/&#x([0-9a-f]+);/gi, (_, code) => String.fromCharCode(parseInt(code, 16)));
}

function htmlToText(html) {
  return decodeEntities(
    String(html || "")
      .replace(/<script[\s\S]*?<\/script>/gi, " ")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<noscript[\s\S]*?<\/noscript>/gi, " ")
      .replace(/<!--[\s\S]*?-->/g, " ")
      .replace(/<(?:br|p|div|li|h[1-6]|tr|section|article)\b[^>]*>/gi, "\n")
      .replace(/<[^>]+>/g, " ")
  )
    .replace(/[ \t]+/g, " ")
    .replace(/\n\s*\n+/g, "\n\n")
    .trim()
    .slice(0, MAX_TEXT_CHARS);
}

function bytesToBase64(bytes) {
  let binary = "";
  const chunk = 0x8000;
  for (let index = 0; index < bytes.length; index += chunk) {
    binary += String.fromCharCode.apply(null, bytes.subarray(index, index + chunk));
  }
  return btoa(binary);
}

async function fetchReadable(url) {
  const safe = safeHttpUrl(url);
  if (!safe) return { error: "invalid_url" };
  const parsed = new URL(safe);
  if (isBlockedHost(parsed.hostname)) return { error: "blocked_source" };
  if (isPrivateHost(parsed.hostname)) return { error: "blocked_private_host" };

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  let response;
  try {
    response = await fetch(safe, {
      redirect: "follow",
      headers: {
        "User-Agent": "UrbanForestPark-JobIntake/1.0 (+https://www.urbanforestpark.com)",
        Accept: "text/html,application/xhtml+xml,text/plain,application/pdf;q=0.9,*/*;q=0.5",
      },
      signal: controller.signal,
    });
  } catch (error) {
    return { error: "fetch_failed" };
  } finally {
    clearTimeout(timer);
  }
  if (!response.ok) return { error: "fetch_http_" + response.status };
  const type = String(response.headers.get("content-type") || "").toLowerCase();
  const length = Number(response.headers.get("content-length") || 0);
  if (length > MAX_PAGE_BYTES) return { error: "page_too_large" };
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength > MAX_PAGE_BYTES) return { error: "page_too_large" };

  if (type.includes("application/pdf")) {
    return {
      kind: "media",
      mimeType: "application/pdf",
      data: bytesToBase64(new Uint8Array(buffer)),
      sourceUrl: safe,
    };
  }
  if (type && !/text\/|application\/(?:xhtml\+xml|xml|ld\+json)|message\/rfc822/.test(type)) {
    return { error: "unsupported_page_type" };
  }
  const text = new TextDecoder().decode(buffer);
  return {
    kind: "text",
    text: type.includes("html") || type.includes("xml") ? htmlToText(text) : text.slice(0, MAX_TEXT_CHARS),
    sourceUrl: safe,
  };
}

async function downloadTelegramFile(env, fileId) {
  const info = await telegramApi(env, "getFile", { file_id: fileId });
  if (!info.ok || !info.result || !info.result.file_path) {
    return { error: info.error || "telegram_file_lookup_failed" };
  }
  const token = telegramToken(env);
  const url = `https://api.telegram.org/file/bot${token}/${info.result.file_path}`;
  let response;
  try {
    response = await fetch(url);
  } catch (error) {
    return { error: "telegram_file_download_failed" };
  }
  if (!response.ok) return { error: "telegram_file_http_" + response.status };
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength > MAX_FILE_BYTES) return { error: "file_too_large" };
  return { bytes: new Uint8Array(buffer), filePath: info.result.file_path };
}

async function readTelegramMedia(env, message) {
  const photo = Array.isArray(message.photo) ? message.photo[message.photo.length - 1] : null;
  const document = message.document || null;
  const fileId = photo ? photo.file_id : document ? document.file_id : "";
  if (!fileId) return { error: "missing_media" };
  const fileName = clean(document && document.file_name, 160);
  let mimeType = clean(
    (photo && "image/jpeg") || (document && document.mime_type) || "",
    100
  ).toLowerCase();
  if (mimeType === "image/jpg") mimeType = "image/jpeg";
  if (!mimeType && /\.pdf$/i.test(fileName)) mimeType = "application/pdf";
  if (!mimeType && /\.(?:jpe?g)$/i.test(fileName)) mimeType = "image/jpeg";
  if (!mimeType && /\.png$/i.test(fileName)) mimeType = "image/png";
  const isText = /^text\/plain$/.test(mimeType) || /\.(?:txt|eml)$/i.test(fileName) ||
    mimeType === "message/rfc822";
  const allowed = new Set([
    "image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf",
    "text/plain", "message/rfc822",
  ]);
  if (!allowed.has(mimeType) && !isText) return { error: "unsupported_file_type" };

  const downloaded = await downloadTelegramFile(env, fileId);
  if (downloaded.error) return downloaded;
  if (isText) {
    return {
      kind: "text",
      text: new TextDecoder().decode(downloaded.bytes).slice(0, MAX_TEXT_CHARS),
      fileName,
    };
  }
  return {
    kind: "media",
    mimeType,
    data: bytesToBase64(downloaded.bytes),
    fileName,
  };
}

async function extractJob({ env, text, media, sourceUrl, jurisdiction }) {
  const apiKey = clean(env && env.GEMINI_API_KEY);
  if (!apiKey) return { error: "gemini_not_configured" };
  const configuredModel = clean(env && env.GEMINI_MODEL) || DEFAULT_MODEL;
  const models = [configuredModel, ...FALLBACK_MODELS].filter(
    (name, index, list) => name && list.indexOf(name) === index
  );
  const prompt = [
    TEXT_PROMPT,
    "",
    "Allowed category values: " + CATEGORIES.join(" | "),
    "Allowed position_type values: " + POSITION_TYPES.join(" | "),
    "Allowed opportunity_kind values: " + OPPORTUNITY_KINDS.join(" | "),
    "Jurisdiction selected by the editor: " + jurisdiction + ".",
    "Source URL supplied by the editor: " + (sourceUrl || "(none)"),
    "",
    "Job notice text:",
    text || "(no text supplied; read the attachment)",
  ].join("\n");

  const parts = [{ text: prompt }];
  if (media && media.data) {
    parts.push({ inline_data: { mime_type: media.mimeType, data: media.data } });
  }
  const payload = {
    contents: [{ role: "user", parts }],
    generationConfig: {
      temperature: 0.1,
      maxOutputTokens: 2400,
      responseMimeType: "application/json",
      responseSchema: RESPONSE_SCHEMA,
    },
  };

  let response;
  let model = "";
  let lastStatus = 0;
  let lastError = "gemini_unreachable";
  for (const candidate of models) {
    try {
      response = await fetch(
        `${GEMINI_ENDPOINT}/${encodeURIComponent(candidate)}:generateContent?key=${encodeURIComponent(apiKey)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );
    } catch (error) {
      lastError = "gemini_unreachable";
      continue;
    }
    if (response.ok) {
      model = candidate;
      break;
    }
    lastStatus = response.status;
    if (response.status === 400 || response.status === 403) {
      return { error: "gemini_rejected_request" };
    }
    if (response.status === 429) {
      lastError = "gemini_rate_limited";
      continue;
    }
    lastError = "gemini_error";
  }
  if (!response || !response.ok) {
    return {
      error: lastError === "gemini_rate_limited" ? "gemini_rate_limited" : "gemini_error",
      status: lastStatus || undefined,
    };
  }

  let result;
  try {
    result = await response.json();
  } catch (error) {
    return { error: "gemini_invalid_response" };
  }
  const responseParts =
    result && result.candidates && result.candidates[0] &&
    result.candidates[0].content && result.candidates[0].content.parts;
  const output = Array.isArray(responseParts)
    ? responseParts.map((part) => clean(part && part.text)).filter(Boolean).join("\n")
    : "";
  if (!output) return { error: "empty_model_response" };
  let parsed;
  try {
    parsed = parseModelJson(output);
  } catch (error) {
    return { error: "invalid_model_json" };
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    return { error: "invalid_model_json" };
  }
  const job = normalizeJob(parsed, jurisdiction);
  if (!job.clean_title || !job.organization) {
    return { error: "incomplete_extraction" };
  }
  if (!job.application_url && sourceUrl && safeHttpUrl(sourceUrl) && !isBlockedHost(new URL(sourceUrl).hostname)) {
    job.application_url = sourceUrl;
  }
  return { job, model };
}

function formatJob(job) {
  const rows = [];
  rows.push(`<b>${escapeHtml(job.clean_title)}</b>`);
  rows.push(escapeHtml(job.organization));
  const location = [job.city, job.state, job.country].filter(Boolean).join(", ");
  if (location) rows.push(`📍 ${escapeHtml(location)}`);
  rows.push(`🏷 ${escapeHtml(job.category)}`);
  rows.push(`🧾 ${escapeHtml(job.opportunity_kind)} · ${escapeHtml(job.position_type)}`);
  if (job.application_deadline) rows.push(`🗓 ${escapeHtml(job.application_deadline)}`);
  if (job.stipend_or_salary) rows.push(`💰 ${escapeHtml(job.stipend_or_salary)}`);
  if (job.qualification_summary) rows.push(`🎓 ${escapeHtml(job.qualification_summary)}`);
  if (job.must_have_skills && job.must_have_skills.length) {
    rows.push(`🔧 ${escapeHtml(job.must_have_skills.join(" · "))}`);
  }
  if (job.role_summary) rows.push(`\n${escapeHtml(job.role_summary)}`);
  if (job.application_url) {
    rows.push(`\n🔗 <a href="${escapeHtml(job.application_url)}">Official application / source</a>`);
  } else {
    rows.push("\n🔗 No application URL was printed. Add it in the desk.");
  }
  rows.push(`\n<a href="${SITE}/#syndication">Registry entry</a>`);
  rows.push("<i>Published directly to the registry. No Syndication Desk review.</i>");
  return rows.join("\n").slice(0, 3900);
}

async function handleUpdate(update, env) {
  const message = update && (update.message || update.edited_message);
  if (!message || !message.chat || message.chat.id == null) {
    return { ok: false, error: "unsupported_update" };
  }
  const chatId = message.chat.id;
  const fromId = message.from && message.from.id != null ? message.from.id : chatId;
  const text = clean(message.text || message.caption || "");

  // /start and /chatid are deliberately public so a new editor can discover
  // the numeric chat id even before TELEGRAM_ADMIN_USER_ID is corrected.
  if (/^\/start(?:@\w+)?\b/i.test(text) || /^\/help(?:@\w+)?\b/i.test(text)) {
    const intro = [
      "<b>UFP Flyer Intake is online.</b>",
      "Send one of these:",
      "• a job URL",
      "• a pasted job email or description",
      "• a flyer image or PDF",
      "",
      "Add <code>#global</code> for an international role; otherwise I use India.",
      `Your chat ID: <code>${escapeHtml(chatId)}</code>`,
      "I extract the job facts and send them back for review. Nothing is published automatically.",
    ].join("\n");
    await sendMessage(env, chatId, intro);
    return { ok: true, command: "start" };
  }
  if (/^\/chatid(?:@\w+)?\b/i.test(text)) {
    await sendMessage(env, chatId, `Chat ID: <code>${escapeHtml(chatId)}</code>`);
    return { ok: true, command: "chatid" };
  }

  const admin = clean(env && env.TELEGRAM_ADMIN_USER_ID);
  if (admin && String(fromId) !== admin && String(chatId) !== admin) {
    await sendMessage(env, chatId, "This intake bot is restricted to the registry editor.");
    return { ok: false, error: "not_authorised" };
  }

  const jurisdiction = jurisdictionFrom(text);
  let media = null;
  let sourceUrl = extractUrl(text);
  let combinedText = text;

  if (message.photo || message.document) {
    media = await readTelegramMedia(env, message);
    if (media.error) {
      const reply = media.error === "unsupported_file_type"
        ? "Send an image, PDF, or plain-text email attachment."
        : "I could not download that attachment. Try again or paste the text.";
      await sendMessage(env, chatId, reply);
      return { ok: false, error: media.error };
    }
    if (media.kind === "text") {
      combinedText = [text, media.text].filter(Boolean).join("\n\n").slice(0, MAX_TEXT_CHARS);
      media = null;
    }
  }

  if (!media) {
    if (!combinedText || combinedText.length < 10) {
      await sendMessage(env, chatId, "Send a job URL, a pasted job email, or a flyer image/PDF.");
      return { ok: false, error: "empty_input" };
    }
    if (sourceUrl) {
      if (isBlockedHost(new URL(sourceUrl).hostname)) {
        await sendMessage(
          env,
          chatId,
          "I do not fetch LinkedIn, Indeed, or Naukri. Paste the job description text instead and I will structure it."
        );
        return { ok: false, error: "blocked_source" };
      }
      const page = await fetchReadable(sourceUrl);
      if (page.error) {
        const notes = combinedText.replace(sourceUrl, "").trim();
        if (notes.length < 40) {
          await sendMessage(
            env,
            chatId,
            "I could not read that link. Paste the job description or attach the flyer, and I will extract it."
          );
          return { ok: false, error: page.error };
        }
      } else if (page.kind === "media") {
        media = page;
      } else if (page.text) {
        combinedText = [combinedText, page.text].filter(Boolean).join("\n\n").slice(0, MAX_TEXT_CHARS);
      }
    }
  }

  await telegramApi(env, "sendChatAction", { chat_id: chatId, action: "typing" });
  const extracted = await extractJob({
    env,
    text: combinedText,
    media,
    sourceUrl,
    jurisdiction,
  });
  if (extracted.error) {
    const messages = {
      gemini_rate_limited: "Gemini is rate-limited right now. Try again in a few minutes.",
      gemini_not_configured: "The intake model is not configured.",
      incomplete_extraction: "I could not find a role title and organisation. Try a clearer notice.",
      blocked_source: "That source cannot be fetched.",
    };
    const reply = messages[extracted.error] || "I could not convert that notice into a job. Try a clearer email or flyer.";
    await sendMessage(env, chatId, reply);
    return { ok: false, error: extracted.error };
  }

  const committed = await commitJobRecord(extracted.job, jurisdiction, env);
  const jurisdictionHint = extracted.job.country && extracted.job.country !== "India" && jurisdiction === "india"
    ? `\n\n⚠️ Extracted country is ${escapeHtml(extracted.job.country)} but no #global tag was used — added to the India registry. Resend with #global for international roles.`
    : "";
  const published = committed.ok
    ? `\n\n✅ Added to ${committed.registry} registry (${committed.id}).` +
      (committed.job_url ? `\n🔗 Registry: ${committed.registry_url}` : "") +
      jurisdictionHint +
      "\n<i>The job page and badge counts update after the next pipeline run.</i>"
    : `\n\n⚠️ Could not auto-publish: ${committed.error || "unknown error"}. Copy the details above into the Syndication Desk.` + jurisdictionHint;

  const sent = await sendMessage(env, chatId, formatJob(extracted.job) + published);
  return {
    ok: true,
    job: extracted.job,
    model: extracted.model,
    published: committed.ok,
    commit: committed.commit,
    path: committed.path,
    job_url: committed.job_url,
    registry_url: committed.registry_url,
    publish_error: committed.ok ? null : committed.error,
    delivered: sent.ok,
    delivery_error: sent.ok ? null : sent.error,
  };
}

function setupAuthorised(request, env) {
  const expected = clean(env && env.TELEGRAM_SETUP_SECRET);
  if (!expected) return { ok: false, status: 503, error: "setup_not_configured" };
  const url = new URL(request.url);
  const provided = clean(
    url.searchParams.get("setup") ||
    request.headers.get("x-ufp-setup-secret")
  );
  if (!provided || provided !== expected) {
    return { ok: false, status: 401, error: "setup_locked" };
  }
  return { ok: true };
}

export async function onRequestGet(context) {
  const { request, env } = context;
  const gate = setupAuthorised(request, env);
  if (!gate.ok) return json({ ok: false, error: gate.error }, gate.status);
  if (!telegramToken(env)) {
    return json({ ok: false, error: "telegram_not_configured" }, 503);
  }

  const me = await telegramApi(env, "getMe", {});
  if (!me.ok) {
    return json(
      { ok: false, error: "telegram_auth_failed", detail: me.error },
      502
    );
  }

  const requestUrl = new URL(request.url);
  if (requestUrl.searchParams.get("admin") === "1") {
    const admin = clean(env && env.TELEGRAM_ADMIN_USER_ID);
    if (!admin) return json({ ok: false, error: "admin_not_configured" }, 503);
    const adminId = /^-?\d+$/.test(admin) ? Number(admin) : admin;
    const chat = await telegramApi(env, "getChat", { chat_id: adminId });
    return json({
      ok: true,
      bot: {
        id: me.result && me.result.id,
        username: me.result && me.result.username,
      },
      admin_check: {
        ok: chat.ok,
        error: chat.ok ? null : chat.error,
        type: chat.ok && chat.result ? chat.result.type : null,
        title: chat.ok && chat.result ? (chat.result.title || chat.result.first_name || null) : null,
        username: chat.ok && chat.result ? (chat.result.username || null) : null,
      },
    });
  }

  const webhookUrl = clean(env && env.TELEGRAM_WEBHOOK_URL) || DEFAULT_WEBHOOK_URL;
  const secret = clean(env && env.TELEGRAM_WEBHOOK_SECRET);
  const payload = {
    url: webhookUrl,
    allowed_updates: ["message", "edited_message"],
    drop_pending_updates: false,
  };
  if (secret) payload.secret_token = secret;
  const set = await telegramApi(env, "setWebhook", payload);
  if (!set.ok) {
    return json({ ok: false, error: "set_webhook_failed", detail: set.error }, 502);
  }
  const info = await telegramApi(env, "getWebhookInfo", {});
  return json({
    ok: true,
    bot: {
      id: me.result && me.result.id,
      username: me.result && me.result.username,
    },
    webhook: info.ok && info.result ? {
      url: info.result.url,
      pending_update_count: info.result.pending_update_count,
      last_error_message: info.result.last_error_message || null,
      allowed_updates: info.result.allowed_updates || null,
    } : null,
    webhook_error: info.ok ? null : info.error,
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!telegramToken(env)) {
    return json({ ok: false, error: "telegram_not_configured" }, 503);
  }

  const webhookSecret = clean(env && env.TELEGRAM_WEBHOOK_SECRET);
  if (webhookSecret) {
    const provided = clean(request.headers.get("x-telegram-bot-api-secret-token"));
    if (provided !== webhookSecret) {
      return json({ ok: false, error: "unauthorized" }, 401);
    }
  }

  let update;
  try {
    update = await request.json();
  } catch (error) {
    return json({ ok: false, error: "invalid_json" }, 400);
  }
  if (!update || typeof update !== "object" || Array.isArray(update)) {
    return json({ ok: false, error: "invalid_update" }, 400);
  }

  const setupSecret = clean(env && env.TELEGRAM_SETUP_SECRET);
  const testSecret = clean(request.headers.get("x-ufp-test-secret"));
  const testMode = Boolean(setupSecret && testSecret && testSecret === setupSecret);
  if (testMode) {
    const admin = clean(env && env.TELEGRAM_ADMIN_USER_ID);
    if (!admin) return json({ ok: false, error: "admin_not_configured" }, 503);
    const adminId = /^-?\d+$/.test(admin) ? Number(admin) : admin;
    const clone = JSON.parse(JSON.stringify(update));
    if (clone.message) {
      clone.message.chat = { ...(clone.message.chat || {}), id: adminId };
      clone.message.from = { ...(clone.message.from || {}), id: adminId };
    }
    const result = await handleUpdate(clone, env);
    return json({ ok: true, test: true, ...result }, result.ok ? 200 : 422);
  }

  const task = handleUpdate(update, env).catch(() => {});
  if (typeof context.waitUntil === "function") {
    context.waitUntil(task);
    return json({ ok: true });
  }
  await task;
  return json({ ok: true });
}

export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, X-Telegram-Bot-Api-Secret-Token, X-UFP-Test-Secret",
    },
  });
}
