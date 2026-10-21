import assert from "node:assert/strict";
import test from "node:test";

import { onRequest as middleware } from "../functions/_middleware.js";
import { onRequestPost } from "../functions/api/subscribe.js";

function request(path, body) {
  return new Request(`https://www.urbanforestpark.com${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
