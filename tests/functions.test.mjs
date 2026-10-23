import assert from "node:assert/strict";
import test from "node:test";

import { onRequest as middleware } from "../functions/_middleware.js";
import { onRequestPost } from "../functions/api/subscribe.js";
import { onRequestPost as parseFlyer } from "../functions/api/parse_flyer.js";
import { onRequestPost as commitJob } from "../functions/api/commit_job.js";

const DESK_HASH = "358dc445f18f1c5a6f13af6aba6e7fdad57d541b14264c572978b27f862462e2";

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
