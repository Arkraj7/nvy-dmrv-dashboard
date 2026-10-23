/**
 * POST /api/parse_flyer
 * ---------------------------------------------------------------------------
 * Cloudflare Pages Function. Accepts a flyer image or PDF from the unlocked
 * Syndication Desk, sends it to Gemini 2.5 Flash, and returns a validated
 * draft job record for human review. Nothing is written to the registry here.
 *
 * Request (JSON):
 *   {
 *     "image": "<base64, no data: prefix>",
 *     "mimeType": "image/jpeg" | "image/png" | "image/webp" |
 *                 "image/gif" | "application/pdf",
 *     "jurisdiction": "india" | "global"
 *   }
 *
 * Response:
 *   { "ok": true, "model": "gemini-2.5-flash", "job": { ... } }
 *
 * The GEMINI_API_KEY secret is read only from the Pages environment. It is
 * never returned, logged, or embedded in the browser.
 */

const GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models";
const DEFAULT_MODEL = "gemini-2.5-flash";
// 2.5 Flash is the requested production model, but Google retires models for
// new API keys. Try the current Flash models before failing the desk.
const FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-flash-latest"];
const MAX_FILE_BYTES = 8 * 1024 * 1024;
const ALLOWED_MIME = new Set([
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
  "image/gif",
  "application/pdf",
]);

const CATEGORIES = [
  "Academic, JRF, SRF & PhD Positions",
  "Research Associate & Project Staff (Contractual)",
  "Forestry, Wildlife & Afforestation",
  "GIS, Remote Sensing & Earth Observation",
  "ESG, Carbon Markets & Corporate Sustainability",
  "Climate Policy, Think-Tanks & Fellowships",
  "Grants & Research Funding",
  "Scholarships & Doctoral Support",
  "Fellowships & Leadership Programs",
  "Internships & Student Traineeships",
  "Competitions, Hackathons & Awards",
];
const POSITION_TYPES = [
  "JRF / SRF",
  "PhD / Doctoral Fellowship",
  "Project Associate / Research Associate",
  "Young Professional / Consultant (Contractual)",
  "Faculty / Academic",
  "Full-Time Corporate / NGO",
  "Fellowship / Internship",
];
const OPPORTUNITY_KINDS = [
  "Job / Career",
  "Fellowship",
  "Scholarship",
  "Grant / Funding",
  "Internship",
  "Competition / Award",
];

const RESPONSE_SCHEMA = {
  type: "OBJECT",
  properties: {
    clean_title: { type: "STRING" },
    organization: { type: "STRING" },
    city: { type: "STRING" },
    state: { type: "STRING" },
    country: { type: "STRING" },
    category: { type: "STRING" },
    position_type: { type: "STRING" },
    opportunity_kind: { type: "STRING" },
    stipend_or_salary: { type: "STRING" },
    qualification_summary: { type: "STRING" },
    must_have_skills: { type: "ARRAY", items: { type: "STRING" } },
    application_deadline: { type: "STRING" },
    application_url: { type: "STRING" },
    org_website: { type: "STRING" },
    role_summary: { type: "STRING" },
    key_responsibilities: { type: "ARRAY", items: { type: "STRING" } },
  },
  required: [
    "clean_title",
    "organization",
    "city",
    "state",
    "country",
    "category",
    "position_type",
    "stipend_or_salary",
    "qualification_summary",
    "must_have_skills",
    "application_deadline",
    "application_url",
    "org_website",
  ],
};

const PROMPT = `You are the intake editor for Urban Forest Park, a verified green-jobs
registry for India and international climate, environment, forestry, ESG and
sustainability opportunities.

Read the attached flyer image or PDF and extract ONE job, fellowship,
internship, scholarship, grant or competition notice. Return only the JSON
object requested by the schema.

Rules:
- Copy facts exactly as printed. Never invent a salary, deadline, eligibility
  requirement, website, or application URL.
- clean_title: the role title, without emojis, "Apply now", or flyer slogans.
- organization: the employer or host institution's proper name.
- city/state: use the duty station. Leave state empty outside India. If the
  flyer says remote, home-based or multiple locations, put "Remote" or the
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
- must_have_skills: 4-7 short tags grounded in the flyer.
- application_deadline: printed closing date, or "Rolling / Open" if none.
- application_url: the printed official application URL. If the flyer prints a
  QR code only and no text URL, return an empty string. Never guess.
- org_website: the organisation's official homepage if printed; otherwise
  empty. Do not put the application URL here.
- role_summary: 2-3 factual sentences, 40-70 words, using only flyer content.
- key_responsibilities: up to 5 short bullets supported by the flyer.`;

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

function clean(value, max) {
  const text = String(value == null ? "" : value).replace(/\s+/g, " ").trim();
  return max ? text.slice(0, max) : text;
}

function listOfStrings(value, maxItems, maxLength) {
  const raw = Array.isArray(value)
    ? value
    : String(value || "").split(/[,;\n]/);
  const out = [];
  for (const item of raw) {
    const text = clean(item, maxLength);
    if (text && !out.includes(text)) out.push(text);
    if (out.length >= maxItems) break;
  }
  return out;
}

function safeHttpUrl(value) {
  const text = clean(value, 600);
  if (!/^https?:\/\//i.test(text)) return "";
  try {
    const url = new URL(text);
    if (!url.hostname || !url.hostname.includes(".")) return "";
    return url.toString();
  } catch (error) {
    return "";
  }
}

function normalizeCategory(value, title, kind) {
  const text = clean(value);
  if (CATEGORIES.includes(text)) return text;
  const haystack = `${text} ${title} ${kind}`.toLowerCase();
  if (/gis|remote sensing|geospatial|earth observation|satellite/.test(haystack)) {
    return "GIS, Remote Sensing & Earth Observation";
  }
  if (/phd|doctoral|postdoc|fellowship|fellow/.test(haystack)) {
    return "Fellowships & Leadership Programs";
  }
  if (/intern|trainee/.test(haystack)) return "Internships & Student Traineeships";
  if (/scholarship|studentship/.test(haystack)) return "Scholarships & Doctoral Support";
  if (/grant|funding|call for proposal/.test(haystack)) return "Grants & Research Funding";
  if (/forest|wildlife|conservation|biodiversity|ecology|marine/.test(haystack)) {
    return "Forestry, Wildlife & Afforestation";
  }
  if (/esg|carbon|sustainability|climate finance|green finance|net zero/.test(haystack)) {
    return "ESG, Carbon Markets & Corporate Sustainability";
  }
  return "Climate Policy, Think-Tanks & Fellowships";
}

function normalizePositionType(value, title) {
  const text = clean(value);
  if (POSITION_TYPES.includes(text)) return text;
  const haystack = `${text} ${title}`.toLowerCase();
  if (/jrf|srf/.test(haystack)) return "JRF / SRF";
  if (/phd|doctoral|postdoc|post-doc/.test(haystack)) return "PhD / Doctoral Fellowship";
  if (/project associate|research associate|research assistant/.test(haystack)) {
    return "Project Associate / Research Associate";
  }
  if (/consultant|young professional|contract/.test(haystack)) {
    return "Young Professional / Consultant (Contractual)";
  }
  if (/professor|faculty|lecturer/.test(haystack)) return "Faculty / Academic";
  if (/fellow|intern|trainee/.test(haystack)) return "Fellowship / Internship";
  return "Full-Time Corporate / NGO";
}

function normalizeKind(value, title) {
  const text = clean(value);
  if (OPPORTUNITY_KINDS.includes(text)) return text;
  const haystack = `${text} ${title}`.toLowerCase();
  if (/grant|funding|call for proposal/.test(haystack)) return "Grant / Funding";
  if (/scholarship|studentship/.test(haystack)) return "Scholarship";
  if (/fellowship|fellow|postdoc|post-doc/.test(haystack)) return "Fellowship";
  if (/intern|trainee/.test(haystack)) return "Internship";
  if (/competition|award|prize|challenge/.test(haystack)) return "Competition / Award";
  return "Job / Career";
}

function expectedDeskHash(env) {
  return clean(env && env.SYNDICATION_PASSPHRASE_SHA256).toLowerCase();
}

function providedDeskHash(request) {
  return clean(
    request.headers.get("x-desk-passphrase-sha256") ||
    request.headers.get("x-desk-hash")
  ).toLowerCase();
}

function deskAuthorised(request, env) {
  const expected = expectedDeskHash(env);
  if (!expected) return { ok: false, status: 503, error: "desk_gate_not_configured" };
  const provided = providedDeskHash(request);
  if (!provided || provided !== expected) {
    return { ok: false, status: 401, error: "desk_locked" };
  }
  return { ok: true };
}

function decodePayload(body) {
  const raw = String((body && (body.image || body.file || body.data)) || "").trim();
  const match = raw.match(/^data:([^;]+);base64,(.*)$/is);
  let mimeType = clean(
    (match && match[1]) || body.mimeType || body.mime_type || ""
  ).toLowerCase();
  if (mimeType === "image/jpg") mimeType = "image/jpeg";
  const data = (match ? match[2] : raw).replace(/\s+/g, "");
  return { data, mimeType };
}

function approxBytes(base64) {
  return Math.floor((base64.length * 3) / 4);
}

function normalizeJob(parsed, jurisdiction) {
  const title = clean(parsed && parsed.clean_title, 180);
  const organization = clean(parsed && parsed.organization, 160);
  const kind = normalizeKind(parsed && parsed.opportunity_kind, title);
  const category = normalizeCategory(parsed && parsed.category, title, kind);
  const positionType = normalizePositionType(parsed && parsed.position_type, title);
  const country = clean(parsed && parsed.country, 90) ||
    (jurisdiction === "india" ? "India" : "Global");
  return {
    clean_title: title,
    organization,
    city: clean(parsed && parsed.city, 120),
    state: clean(parsed && parsed.state, 120),
    country,
    category,
    position_type: positionType,
    opportunity_kind: kind,
    stipend_or_salary: clean(parsed && parsed.stipend_or_salary, 200) ||
      "Not disclosed - see official portal",
    qualification_summary: clean(parsed && parsed.qualification_summary, 500),
    must_have_skills: listOfStrings(parsed && parsed.must_have_skills, 8, 70),
    application_deadline: clean(parsed && parsed.application_deadline, 80) ||
      "Rolling / Open",
    application_url: safeHttpUrl(parsed && parsed.application_url),
    org_website: safeHttpUrl(parsed && parsed.org_website),
    role_summary: clean(parsed && parsed.role_summary, 700),
    key_responsibilities: listOfStrings(
      parsed && parsed.key_responsibilities, 6, 220
    ),
    jurisdiction,
  };
}

function parseModelJson(text) {
  let raw = String(text || "").trim();
  raw = raw.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "").trim();
  try {
    return JSON.parse(raw);
  } catch (error) {
    const start = raw.indexOf("{");
    const end = raw.lastIndexOf("}");
    if (start >= 0 && end > start) {
      return JSON.parse(raw.slice(start, end + 1));
    }
    throw error;
  }
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const runtimeEnv = env || {};

  const gate = deskAuthorised(request, runtimeEnv);
  if (!gate.ok) return json({ ok: false, error: gate.error }, gate.status);

  const apiKey = clean(runtimeEnv.GEMINI_API_KEY);
  if (!apiKey) return json({ ok: false, error: "gemini_not_configured" }, 503);

  let body;
  try {
    body = await request.json();
  } catch (error) {
    return json({ ok: false, error: "invalid_json" }, 400);
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return json({ ok: false, error: "invalid_payload" }, 400);
  }
  const jurisdiction = clean(body.jurisdiction).toLowerCase();
  if (!["india", "global"].includes(jurisdiction)) {
    return json(
      { ok: false, error: "invalid_jurisdiction", allowed: ["india", "global"] },
      422
    );
  }

  const { data, mimeType } = decodePayload(body);
  if (!data) return json({ ok: false, error: "missing_file" }, 422);
  if (!ALLOWED_MIME.has(mimeType)) {
    return json(
      { ok: false, error: "unsupported_file_type", allowed: Array.from(ALLOWED_MIME) },
      415
    );
  }
  if (approxBytes(data) > MAX_FILE_BYTES) {
    return json(
      { ok: false, error: "file_too_large", max_bytes: MAX_FILE_BYTES },
      413
    );
  }
  if (!/^[a-zA-Z0-9+/=]+$/.test(data)) {
    return json({ ok: false, error: "invalid_base64" }, 422);
  }

  const configuredModel = clean(runtimeEnv.GEMINI_MODEL) || DEFAULT_MODEL;
  const models = [configuredModel, ...FALLBACK_MODELS].filter(
    (name, index, list) => name && list.indexOf(name) === index
  );
  const prompt = [
    PROMPT,
    "",
    "Allowed category values: " + CATEGORIES.join(" | "),
    "Allowed position_type values: " + POSITION_TYPES.join(" | "),
    "Allowed opportunity_kind values: " + OPPORTUNITY_KINDS.join(" | "),
    "Jurisdiction selected by the editor: " + jurisdiction + ".",
  ].join("\n");

  const payload = {
    contents: [
      {
        role: "user",
        parts: [
          { text: prompt },
          { inline_data: { mime_type: mimeType, data } },
        ],
      },
    ],
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
      return json(
        { ok: false, error: "gemini_rejected_request", status: response.status },
        502
      );
    }
    if (response.status === 429) {
      lastError = "gemini_rate_limited";
      continue;
    }
    // 404 means this key cannot use the model; 5xx is usually transient.
    // Both are worth retrying with the next Flash candidate.
    lastError = "gemini_error";
  }

  if (!response || !response.ok) {
    if (lastError === "gemini_rate_limited") {
      return json({ ok: false, error: "gemini_rate_limited" }, 429);
    }
    if (lastStatus === 404) {
      return json({ ok: false, error: "gemini_model_unavailable" }, 502);
    }
    return json(
      { ok: false, error: lastError, status: lastStatus || undefined },
      502
    );
  }

  let result;
  try {
    result = await response.json();
  } catch (error) {
    return json({ ok: false, error: "gemini_invalid_response" }, 502);
  }
  const parts =
    result &&
    result.candidates &&
    result.candidates[0] &&
    result.candidates[0].content &&
    result.candidates[0].content.parts;
  const text = Array.isArray(parts)
    ? parts.map((part) => clean(part && part.text)).filter(Boolean).join("\n")
    : "";
  if (!text) return json({ ok: false, error: "empty_model_response" }, 502);

  let parsed;
  try {
    parsed = parseModelJson(text);
  } catch (error) {
    return json({ ok: false, error: "invalid_model_json" }, 502);
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    return json({ ok: false, error: "invalid_model_json" }, 502);
  }

  const job = normalizeJob(parsed, jurisdiction);
  if (!job.clean_title || !job.organization) {
    return json(
      {
        ok: false,
        error: "incomplete_extraction",
        detail: "The flyer did not yield a title and organisation. Try a clearer image.",
      },
      422
    );
  }

  return json({ ok: true, model, jurisdiction, job });
}

export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, X-Desk-Passphrase-SHA256",
    },
  });
}
