import assert from "node:assert/strict";
import test from "node:test";

import { onRequest as middleware } from "../functions/_middleware.js";
import { onRequestPost } from "../functions/api/subscribe.js";
import { onRequestPost as parseFlyer } from "../functions/api/parse_flyer.js";
import { onRequestPost as commitJob, commitJobRecord } from "../functions/api/commit_job.js";
import {
  onRequestGet as telegramSetup,
  onRequestPost as telegramWebhook,
} from "../functions/api/telegram.js";

const DESK_HASH = "c7fb53fe0e4080c222faa7272b03ed6d53b888fa66c9645307c27267fe6068c5";

function request(path, body) {
  return new Request(`https://www.urbanforestpark.com${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function deskRequest(path, body) {
  return new Request(`https://www.urbanforestpark.com${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Desk-Passphrase-SHA256": DESK_HASH,
    },
    body: JSON.stringify(body),
  });
}

function context(req, env) {
  return {
    request: req,
    env: env || {},
    waitUntil() {},
  };
}

test("apex host redirects permanently to www and preserves path/query", async () => {
  const response = await middleware({
    request: new Request("https://urbanforestpark.com/jobs/example?source=test"),
    next: async () => new Response("next"),
  });

  assert.equal(response.status, 301);
  assert.equal(
    response.headers.get("location"),
    "https://www.urbanforestpark.com/jobs/example?source=test"
  );
});

test("canonical host passes through middleware", async () => {
  const response = await middleware({
    request: new Request("https://www.urbanforestpark.com/"),
    next: async () => new Response("next", { status: 200 }),
  });

  assert.equal(response.status, 200);
  assert.equal(await response.text(), "next");
});

test("invalid frequency is rejected before any persistence", async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls += 1;
    return new Response("{}", { status: 200 });
  };

  const response = await onRequestPost(
    context(request("/api/subscribe", {
      email: "person@b.in",
      frequency: "daily",
      sector: "all",
    }))
  );

  assert.equal(response.status, 422);
  assert.equal((await response.json()).error, "invalid_frequency");
  assert.equal(calls, 0);
});

test("GitHub persistence upserts subscribers.json and dispatches the welcome", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    const target = String(url);
    calls.push({ target, options });

    if (target.includes("/contents/data/subscribers.json") && options.method !== "PUT") {
      return new Response(JSON.stringify({ message: "Not Found" }), { status: 404 });
    }
    if (target.includes("/contents/data/subscribers.json") && options.method === "PUT") {
      return new Response(JSON.stringify({ content: { sha: "new-sha" } }), { status: 200 });
    }
    if (target.endsWith("/dispatches")) {
      return new Response(null, { status: 204 });
    }
    return new Response("{}", { status: 200 });
  };

  const response = await onRequestPost(
    context(
      request("/api/subscribe", {
        email: "Person@B.in",
        frequency: "3-days",
        sector: "academic",
      }),
      {
        GITHUB_PAT: "test-token",
        GITHUB_REPO: "owner/repo",
      }
    )
  );

  const payload = await response.json();
  assert.equal(payload.ok, true);
  assert.equal(payload.persisted, true);
  assert.equal(payload.storage, "github");
  assert.equal(payload.welcome, "queued");
  assert.equal(payload.welcome_via, "repository_dispatch");

  const put = calls.find((call) => call.options.method === "PUT");
  assert.ok(put, "expected a GitHub contents PUT");
  const body = JSON.parse(put.options.body);
  const stored = JSON.parse(Buffer.from(body.content, "base64").toString("utf8"));
  assert.equal(stored[0].email, "person@b.in");
  assert.equal(stored[0].frequency, "3-days");
  assert.equal(stored[0].sector, "academic");
  assert.equal(stored[0].welcome_sent, false);

  const dispatch = calls.find((call) => call.target.endsWith("/dispatches"));
  const dispatchBody = JSON.parse(dispatch.options.body);
  assert.equal(dispatchBody.event_type, "welcome_email");
  assert.equal(dispatchBody.client_payload.subscriber_email, "person@b.in");
  assert.equal(dispatchBody.client_payload.frequency, "3-days");
  assert.equal(dispatchBody.client_payload.sector, "academic");
});

test("KV is the zero-GitHub-token persistence fallback", async () => {
  const puts = [];
  const kv = {
    async get() {
      return null;
    },
    async put(key, value) {
      puts.push({ key, value });
    },
  };

  const response = await onRequestPost(
    context(
      request("/api/subscribe", {
        email: "kv@b.in",
        frequency: "weekly",
        sector: "corporate-esg",
      }),
      { UFP_SUBSCRIBERS: kv }
    )
  );

  const payload = await response.json();
  assert.equal(payload.ok, true);
  assert.equal(payload.persisted, true);
  assert.equal(payload.storage, "kv");
  assert.equal(puts.length, 1);
  assert.equal(puts[0].key, "sub:kv@b.in");
  assert.equal(JSON.parse(puts[0].value).frequency, "weekly");
});

test("no server store still acknowledges and logs the signup", async () => {
  const logs = [];
  const original = console.log;
  console.log = (line) => logs.push(line);
  try {
    const response = await onRequestPost(
      context(
        request("/api/subscribe", {
          email: "local@b.in",
          frequency: "3-days",
          sector: "all",
        })
      )
    );

    const payload = await response.json();
    assert.equal(payload.ok, true);
    assert.equal(payload.persisted, false);
    assert.equal(payload.storage, "none");
    assert.equal(payload.welcome, "not_configured");
    assert.equal(logs.length, 1);
    assert.equal(JSON.parse(logs[0]).event, "subscriber_unpersisted");
  } finally {
    console.log = original;
  }
});

const EXTRACTED_JOB = {
  clean_title: "Junior Forest Carbon Analyst",
  organization: "Example Climate Institute",
  city: "Nairobi",
  state: "",
  country: "Kenya",
  category: "ESG, Carbon Markets & Corporate Sustainability",
  position_type: "Full-Time Corporate / NGO",
  opportunity_kind: "Job / Career",
  stipend_or_salary: "USD 2,400 per month",
  qualification_summary: "MSc in environmental science or a related field.",
  must_have_skills: ["carbon accounting", "GIS", "data analysis"],
  application_deadline: "27 October 2026",
  application_url: "https://example.org/careers/forest-carbon-analyst",
  org_website: "https://example.org/",
  role_summary: "Analyse forest carbon projects and support verification.",
  key_responsibilities: ["Review project data", "Prepare verification notes"],
};

function telegramRequest(update, extraHeaders) {
  return new Request("https://www.urbanforestpark.com/api/telegram", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Bot-Api-Secret-Token": "hook-secret",
      ...(extraHeaders || {}),
    },
    body: JSON.stringify(update),
  });
}

test("Telegram webhook rejects updates without the configured secret header", async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls += 1;
    return new Response("{}", { status: 200 });
  };
  const response = await telegramWebhook(
    context(
      new Request("https://www.urbanforestpark.com/api/telegram", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ update_id: 1 }),
      }),
      {
        TELEGRAM_INBOX_BOT_TOKEN: "test-token",
        TELEGRAM_WEBHOOK_SECRET: "hook-secret",
      }
    )
  );
  assert.equal(response.status, 401);
  assert.equal((await response.json()).error, "unauthorized");
  assert.equal(calls, 0);
});

test("Telegram webhook handles /start and returns the chat id", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url: String(url), options });
    return new Response(JSON.stringify({ ok: true, result: { message_id: 9 } }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };
  const update = {
    update_id: 2,
    message: {
      message_id: 2,
      date: 1760000000,
      chat: { id: 999, type: "private" },
      from: { id: 999, is_bot: false, first_name: "Tester" },
      text: "/start",
    },
  };
  const response = await telegramWebhook(
    context(
      telegramRequest(update, { "X-UFP-Test-Secret": "setup-secret" }),
      {
        TELEGRAM_INBOX_BOT_TOKEN: "test-token",
        TELEGRAM_WEBHOOK_SECRET: "hook-secret",
        TELEGRAM_SETUP_SECRET: "setup-secret",
        TELEGRAM_ADMIN_USER_ID: "123",
      }
    )
  );
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.ok, true);
  assert.equal(payload.command, "start");
  const sendCall = calls.find((call) => call.url.includes("/sendMessage"));
  assert.ok(sendCall, "expected a sendMessage call");
  assert.match(sendCall.url, /sendMessage/);
  assert.equal(JSON.parse(sendCall.options.body).chat_id, 123);
});

test("Telegram webhook converts a pasted job email into structured job info", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    const target = String(url);
    calls.push({ target, options });
    if (target.includes("generativelanguage.googleapis.com")) {
      return new Response(
        JSON.stringify({
          candidates: [{ content: { parts: [{ text: JSON.stringify(EXTRACTED_JOB) }] } }],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }
    return new Response(JSON.stringify({ ok: true, result: { message_id: 10 } }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };
  const update = {
    update_id: 3,
    message: {
      message_id: 3,
      date: 1760000000,
      chat: { id: 999, type: "private" },
      from: { id: 999, is_bot: false, first_name: "Tester" },
      text: "Subject: Junior Forest Carbon Analyst at Example Climate Institute. Location: Nairobi, Kenya. Deadline: 27 October 2026. Apply: https://example.org/careers/forest-carbon-analyst",
    },
  };
  const response = await telegramWebhook(
    context(
      telegramRequest(update, { "X-UFP-Test-Secret": "setup-secret" }),
      {
        TELEGRAM_INBOX_BOT_TOKEN: "test-token",
        TELEGRAM_WEBHOOK_SECRET: "hook-secret",
        TELEGRAM_SETUP_SECRET: "setup-secret",
        TELEGRAM_ADMIN_USER_ID: "123",
        GEMINI_API_KEY: "test-key",
      }
    )
  );
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.ok, true);
  assert.equal(payload.job.clean_title, EXTRACTED_JOB.clean_title);
  assert.equal(payload.job.organization, EXTRACTED_JOB.organization);
  assert.equal(payload.delivered, true);
  const gemini = calls.find((call) => call.target.includes("generativelanguage.googleapis.com"));
  assert.ok(gemini);
  assert.match(gemini.options.body, /Junior Forest Carbon Analyst/);
  const send = calls.find((call) => call.target.includes("/sendMessage"));
  assert.ok(send);
  assert.match(JSON.parse(send.options.body).text, /Junior Forest Carbon Analyst/);
});

test("Telegram webhook reads a job link before extracting it", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    const target = String(url);
    calls.push({ target, options });
    if (target.startsWith("https://example.org/job/123")) {
      return new Response(
        "<html><body><h1>Wetland Restoration Officer</h1><p>Example Conservation Trust, Pune. Apply by 30 November 2026 at https://example.org/apply/wetland.</p></body></html>",
        { status: 200, headers: { "Content-Type": "text/html; charset=utf-8" } }
      );
    }
    if (target.includes("generativelanguage.googleapis.com")) {
      return new Response(
        JSON.stringify({
          candidates: [{
            content: {
              parts: [{
                text: JSON.stringify({
                  ...EXTRACTED_JOB,
                  clean_title: "Wetland Restoration Officer",
                  organization: "Example Conservation Trust",
                  city: "Pune",
                  country: "India",
                  application_url: "https://example.org/apply/wetland",
                }),
              }],
            },
          }],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }
    return new Response(JSON.stringify({ ok: true, result: { message_id: 11 } }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };
  const update = {
    update_id: 4,
    message: {
      message_id: 4,
      date: 1760000000,
      chat: { id: 999, type: "private" },
      from: { id: 999, is_bot: false, first_name: "Tester" },
      text: "https://example.org/job/123",
    },
  };
  const response = await telegramWebhook(
    context(
      telegramRequest(update, { "X-UFP-Test-Secret": "setup-secret" }),
      {
        TELEGRAM_INBOX_BOT_TOKEN: "test-token",
        TELEGRAM_WEBHOOK_SECRET: "hook-secret",
        TELEGRAM_SETUP_SECRET: "setup-secret",
        TELEGRAM_ADMIN_USER_ID: "123",
        GEMINI_API_KEY: "test-key",
      }
    )
  );
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.ok, true);
  assert.equal(payload.job.clean_title, "Wetland Restoration Officer");
  assert.ok(calls.some((call) => call.target === "https://example.org/job/123"));
});

test("Telegram setup registers the webhook through the Pages secret", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    const target = String(url);
    calls.push({ target, options });
    if (target.endsWith("/getMe")) {
      return new Response(JSON.stringify({ ok: true, result: { id: 42, username: "ufp_test_bot" } }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (target.endsWith("/setWebhook")) {
      return new Response(JSON.stringify({ ok: true, result: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (target.endsWith("/getWebhookInfo")) {
      return new Response(JSON.stringify({
        ok: true,
        result: { url: "https://www.urbanforestpark.com/api/telegram", pending_update_count: 0 },
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    return new Response("{}", { status: 200 });
  };
  const response = await telegramSetup(
    context(
      new Request("https://www.urbanforestpark.com/api/telegram?setup=setup-secret"),
      {
        TELEGRAM_INBOX_BOT_TOKEN: "test-token",
        TELEGRAM_WEBHOOK_SECRET: "hook-secret",
        TELEGRAM_SETUP_SECRET: "setup-secret",
      }
    )
  );
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.ok, true);
  assert.equal(payload.bot.username, "ufp_test_bot");
  assert.equal(payload.webhook.url, "https://www.urbanforestpark.com/api/telegram");
  const setWebhook = calls.find((call) => call.target.endsWith("/setWebhook"));
  const body = JSON.parse(setWebhook.options.body);
  assert.equal(body.secret_token, "hook-secret");
});

test("flyer parse endpoint rejects an unlocked browser without the desk hash", async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls += 1;
    return new Response("{}", { status: 200 });
  };
  const response = await parseFlyer(
    context(
      request("/api/parse_flyer", { image: "aGVsbG8=", mimeType: "image/png", jurisdiction: "global" }),
      { GEMINI_API_KEY: "test-key", SYNDICATION_PASSPHRASE_SHA256: DESK_HASH }
    )
  );
  assert.equal(response.status, 401);
  assert.equal((await response.json()).error, "desk_locked");
  assert.equal(calls, 0);
});

test("flyer parse endpoint returns validated editable fields from Gemini Vision", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url: String(url), options });
    return new Response(
      JSON.stringify({
        candidates: [{ content: { parts: [{ text: JSON.stringify(EXTRACTED_JOB) }] } }],
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  };

  const response = await parseFlyer(
    context(
      deskRequest("/api/parse_flyer", {
        image: "iVBORw0KGgo=",
        mimeType: "image/png",
        jurisdiction: "global",
      }),
      { GEMINI_API_KEY: "test-key", SYNDICATION_PASSPHRASE_SHA256: DESK_HASH }
    )
  );
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.ok, true);
  assert.equal(payload.model, "gemini-2.5-flash");
  assert.equal(payload.job.clean_title, "Junior Forest Carbon Analyst");
  assert.equal(payload.job.application_url, "https://example.org/careers/forest-carbon-analyst");
  assert.equal(payload.job.jurisdiction, "global");
  assert.equal(calls.length, 1);
  assert.match(calls[0].url, /gemini-2\.5-flash:generateContent/);
  const geminiBody = JSON.parse(calls[0].options.body);
  assert.equal(geminiBody.contents[0].parts[1].inline_data.mime_type, "image/png");
  assert.equal(geminiBody.contents[0].parts[1].inline_data.data, "iVBORw0KGgo=");
});

test("flyer parse endpoint falls back when the primary Gemini model is retired", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url: String(url), options });
    if (calls.length === 1) {
      return new Response(
        JSON.stringify({ error: { code: 404, message: "model no longer available" } }),
        { status: 404, headers: { "Content-Type": "application/json" } }
      );
    }
    return new Response(
      JSON.stringify({
        candidates: [{ content: { parts: [{ text: JSON.stringify(EXTRACTED_JOB) }] } }],
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  };

  const response = await parseFlyer(
    context(
      deskRequest("/api/parse_flyer", {
        image: "iVBORw0KGgo=",
        mimeType: "image/png",
        jurisdiction: "global",
      }),
      { GEMINI_API_KEY: "test-key", SYNDICATION_PASSPHRASE_SHA256: DESK_HASH }
    )
  );
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.ok, true);
  assert.equal(payload.model, "gemini-3.8-flash");
  assert.equal(calls.length, 2);
  assert.match(calls[0].url, /gemini-2\.5-flash:generateContent/);
  assert.match(calls[1].url, /gemini-3\.8-flash:generateContent/);
});

test("flyer parse endpoint skips a rate-limited fallback model", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url: String(url), options });
    if (calls.length === 1) {
      return new Response(
        JSON.stringify({ error: { code: 404, message: "model no longer available" } }),
        { status: 404, headers: { "Content-Type": "application/json" } }
      );
    }
    if (calls.length === 2) {
      return new Response(
        JSON.stringify({ error: { code: 429, message: "quota exceeded" } }),
        { status: 429, headers: { "Content-Type": "application/json" } }
      );
    }
    return new Response(
      JSON.stringify({
        candidates: [{ content: { parts: [{ text: JSON.stringify(EXTRACTED_JOB) }] } }],
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  };

  const response = await parseFlyer(
    context(
      deskRequest("/api/parse_flyer", {
        image: "iVBORw0KGgo=",
        mimeType: "image/png",
        jurisdiction: "global",
      }),
      { GEMINI_API_KEY: "test-key", SYNDICATION_PASSPHRASE_SHA256: DESK_HASH }
    )
  );
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.ok, true);
  assert.equal(payload.model, "gemini-3.6-flash");
  assert.equal(calls.length, 3);
  assert.match(calls[0].url, /gemini-2\.5-flash:generateContent/);
  assert.match(calls[1].url, /gemini-3\.8-flash:generateContent/);
  assert.match(calls[2].url, /gemini-3\.6-flash:generateContent/);
});

test("flyer parse endpoint fails closed when GEMINI_API_KEY is absent", async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls += 1;
    return new Response("{}", { status: 200 });
  };
  const response = await parseFlyer(
    context(
      deskRequest("/api/parse_flyer", {
        image: "iVBORw0KGgo=",
        mimeType: "image/png",
        jurisdiction: "india",
      }),
      { SYNDICATION_PASSPHRASE_SHA256: DESK_HASH }
    )
  );
  assert.equal(response.status, 503);
  assert.equal((await response.json()).error, "gemini_not_configured");
  assert.equal(calls, 0);
});

test("commit_job appends a reviewed role to global_jobs.json through GitHub", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    const target = String(url);
    calls.push({ target, options });
    if (target.includes("/contents/public/global_jobs.json") && options.method !== "PUT") {
      return new Response(
        JSON.stringify({
          sha: "old-sha",
          content: Buffer.from(JSON.stringify([{ id: "existing-job" }])).toString("base64"),
        }),
        { status: 200 }
      );
    }
    if (target.includes("/contents/public/global_jobs.json") && options.method === "PUT") {
      return new Response(JSON.stringify({ commit: { sha: "new-commit" } }), { status: 200 });
    }
    return new Response("{}", { status: 404 });
  };

  const response = await commitJob(
    context(
      deskRequest("/api/commit_job", { job: EXTRACTED_JOB, jurisdiction: "global" }),
      {
        GITHUB_PAT: "test-token",
        GITHUB_REPO: "owner/repo",
        SYNDICATION_PASSPHRASE_SHA256: DESK_HASH,
      }
    )
  );
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.ok, true);
  assert.equal(payload.registry, "global");
  assert.equal(payload.path, "public/global_jobs.json");
  assert.equal(payload.commit, "new-commit");
  assert.ok(payload.id);

  const put = calls.find((call) => call.options.method === "PUT");
  assert.ok(put, "expected a GitHub contents PUT");
  assert.match(put.target, /\/contents\/public\/global_jobs\.json$/);
  const body = JSON.parse(put.options.body);
  assert.equal(body.sha, "old-sha");
  const stored = JSON.parse(Buffer.from(body.content, "base64").toString("utf8"));
  assert.equal(stored.length, 2);
  assert.equal(stored[0].id, payload.id);
  assert.equal(stored[0].clean_title, "Junior Forest Carbon Analyst");
  assert.equal(stored[0].global, true);
  assert.equal(stored[0].region, "Africa & Middle East");
  assert.equal(stored[0].status, "active");
  assert.equal(stored[0].verification.method, "flyer-intake-gemini-vision");
});

test("commit_job rejects a duplicate application URL before writing", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ target: String(url), options });
    return new Response(
      JSON.stringify({
        sha: "old-sha",
        content: Buffer.from(
          JSON.stringify([{ id: "existing", apply_url: EXTRACTED_JOB.application_url }])
        ).toString("base64"),
      }),
      { status: 200 }
    );
  };

  const response = await commitJob(
    context(
      deskRequest("/api/commit_job", { job: EXTRACTED_JOB, jurisdiction: "global" }),
      {
        GITHUB_PAT: "test-token",
        GITHUB_REPO: "owner/repo",
        SYNDICATION_PASSPHRASE_SHA256: DESK_HASH,
      }
    )
  );
  const payload = await response.json();
  assert.equal(response.status, 409);
  assert.equal(payload.error, "duplicate_application_url");
  assert.equal(calls.some((call) => call.options.method === "PUT"), false);
});

test("commit_job fails closed when the server-side GitHub token is absent", async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls += 1;
    return new Response("{}", { status: 200 });
  };
  const response = await commitJob(
    context(
      deskRequest("/api/commit_job", { job: EXTRACTED_JOB, jurisdiction: "india" }),
      { SYNDICATION_PASSPHRASE_SHA256: DESK_HASH }
    )
  );
  assert.equal(response.status, 503);
  assert.equal((await response.json()).error, "github_not_configured");
  assert.equal(calls, 0);
});

test("commitJobRecord appends a role directly without the desk gate", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    const target = String(url);
    calls.push({ target, options });
    if (target.includes("/contents/public/global_jobs.json") && options.method !== "PUT") {
      return new Response(
        JSON.stringify({
          sha: "old-sha",
          content: Buffer.from(JSON.stringify([])).toString("base64"),
        }),
        { status: 200 }
      );
    }
    if (target.includes("/contents/public/global_jobs.json") && options.method === "PUT") {
      return new Response(JSON.stringify({ commit: { sha: "direct-commit" } }), { status: 200 });
    }
    return new Response("{}", { status: 404 });
  };

  const result = await commitJobRecord(EXTRACTED_JOB, "global", {
    GITHUB_PAT: "test-token",
    GITHUB_REPO: "owner/repo",
  });

  assert.equal(result.ok, true);
  assert.equal(result.status, 200);
  assert.equal(result.registry, "global");
  assert.equal(result.path, "public/global_jobs.json");
  assert.equal(result.commit, "direct-commit");
  assert.ok(result.id);
  assert.ok(result.job_url);

  const put = calls.find((call) => call.options.method === "PUT");
  assert.ok(put, "expected a GitHub contents PUT");
  const stored = JSON.parse(
    Buffer.from(JSON.parse(put.options.body).content, "base64").toString("utf8")
  );
  assert.equal(stored.length, 1);
  assert.equal(stored[0].clean_title, "Junior Forest Carbon Analyst");
  assert.equal(stored[0].global, true);
  assert.equal(stored[0].status, "active");
});

test("commitJobRecord rejects a duplicate application URL directly", async () => {
  const calls = [];
  globalThis.fetch = async (url) => {
    const target = String(url);
    calls.push({ target });
    return new Response(
      JSON.stringify({
        sha: "old-sha",
        content: Buffer.from(
          JSON.stringify([{ id: "existing", apply_url: EXTRACTED_JOB.application_url }])
        ).toString("base64"),
      }),
      { status: 200 }
    );
  };

  const result = await commitJobRecord(EXTRACTED_JOB, "global", {
    GITHUB_PAT: "test-token",
    GITHUB_REPO: "owner/repo",
  });

  assert.equal(result.ok, false);
  assert.equal(result.status, 409);
  assert.equal(result.error, "duplicate_application_url");
  assert.ok(calls.some((call) => call.target.includes("/contents/public/global_jobs.json")));
});

test("Telegram webhook auto-publishes an extracted email to the registry", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    const target = String(url);
    calls.push({ target, options });
    if (target.includes("generativelanguage.googleapis.com")) {
      return new Response(
        JSON.stringify({
          candidates: [{ content: { parts: [{ text: JSON.stringify(EXTRACTED_JOB) }] } }],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }
    if (target.includes("api.github.com")) {
      if (options.method === "PUT") {
        return new Response(JSON.stringify({ commit: { sha: "gh-commit" } }), { status: 200 });
      }
      return new Response(
        JSON.stringify({
          sha: "old",
          content: Buffer.from(JSON.stringify([])).toString("base64"),
        }),
        { status: 200 }
      );
    }
    return new Response(
      JSON.stringify({ ok: true, result: { message_id: 1 } }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  };

  const response = await telegramWebhook(
    context(
      telegramRequest(
        {
          update_id: 6,
          message: {
            message_id: 6,
            date: 1760000000,
            chat: { id: 9, type: "private" },
            from: { id: 9, is_bot: false, first_name: "Intake test" },
            text: "Subject: Junior Forest Carbon Analyst at Example Climate Institute. Location: Nairobi, Kenya. Deadline: 27 October 2026. Apply: https://example.org/careers/forest-carbon-analyst",
          },
        },
        { "X-UFP-Test-Secret": "setup-secret" }
      ),
      {
        TELEGRAM_INBOX_BOT_TOKEN: "test-token",
        TELEGRAM_WEBHOOK_SECRET: "hook-secret",
        TELEGRAM_SETUP_SECRET: "setup-secret",
        TELEGRAM_ADMIN_USER_ID: "123",
        GEMINI_API_KEY: "test-key",
        GITHUB_PAT: "test-token",
        GITHUB_REPO: "owner/repo",
      }
    )
  );

  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.ok, true);
  assert.equal(payload.published, true);
  assert.equal(payload.commit, "gh-commit");
  assert.ok(payload.path);
  assert.ok(payload.job_url);
  assert.ok(payload.job_url.startsWith("https://www.urbanforestpark.com/jobs/"));
  assert.equal(payload.delivered, true);

  const put = calls.find((call) => call.options.method === "PUT");
  assert.ok(put, "expected a GitHub contents PUT for auto-publish");
  const body = JSON.parse(put.options.body);
  assert.ok(put.target.includes("/contents/public/jobs.json"));
});
