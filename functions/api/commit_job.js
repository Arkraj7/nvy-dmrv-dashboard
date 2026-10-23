/**
 * POST /api/commit_job
 * ---------------------------------------------------------------------------
 * Cloudflare Pages Function. The second half of the Syndication Desk flyer
 * intake: after a human reviews and edits the Gemini extraction, this endpoint
 * appends the record to public/jobs.json (India) or public/global_jobs.json
 * through the GitHub Contents API.
 *
 * Request (JSON):
 *   { "job": { ...reviewed fields... }, "jurisdiction": "india" | "global" }
 *
 * Required Pages secrets/vars:
 *   GITHUB_PAT (or GITHUB_TOKEN) with contents:write on GITHUB_REPO
 *   GITHUB_REPO (defaults to Arkraj7/nvy-dmrv-dashboard)
 *   SYNDICATION_PASSPHRASE_SHA256 (same client-side hash as the desk gate)
 *
 * The PAT never reaches the browser. The browser sends only the SHA-256 of the
 * desk passphrase, which is compared server-side.
 */

const GITHUB_API = "https://api.github.com";
const DEFAULT_REPO = "Arkraj7/nvy-dmrv-dashboard";
const BRANCH = "main";
const SITE = "https://www.urbanforestpark.com";
const MAX_TITLE = 180;
const MAX_ORG = 160;
const MAX_TEXT = 700;

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
const EXPERIENCE_LEVELS = [
  "Entry Level / Fellowship",
  "1-3 Years",
  "Mid-Senior (3-6 Years)",
  "Senior",
];
const GLOBAL_REGIONS = [
  "Global / Remote",
  "Europe",
  "North America",
  "Asia-Pacific",
  "Africa & Middle East",
  "Latin America",
  "UN / Multilateral",
];

const EUROPE = new Set([
  "Germany", "Switzerland", "Netherlands", "Belgium", "France", "Italy",
  "Spain", "Portugal", "Ireland", "Austria", "Sweden", "Norway", "Denmark",
  "Finland", "Poland", "Czech Republic", "Greece", "United Kingdom",
]);
const NORTH_AMERICA = new Set(["United States", "Canada", "Mexico"]);
const ASIA_PACIFIC = new Set([
  "India", "Bangladesh", "Nepal", "Sri Lanka", "Maldives", "Indonesia",
  "Malaysia", "Philippines", "Thailand", "Vietnam", "Cambodia", "China",
  "Japan", "Republic of Korea", "Singapore", "Australia", "New Zealand",
  "Papua New Guinea", "Fiji", "Vanuatu", "Solomon Islands", "Myanmar",
]);
const AFRICA_MIDDLE_EAST = new Set([
  "Kenya", "Ethiopia", "Nigeria", "Ghana", "Uganda", "Tanzania", "Rwanda",
  "Zambia", "Zimbabwe", "Cameroon", "Senegal", "Egypt", "Jordan", "Lebanon",
  "Iraq", "Türkiye", "South Africa", "Côte d'Ivoire",
  "Democratic Republic of the Congo", "Saudi Arabia", "United Arab Emirates",
  "Syria", "Chad", "Gabon",
]);
const LATIN_AMERICA = new Set([
  "Brazil", "Peru", "Colombia", "Ecuador", "Bolivia", "Chile", "Argentina",
  "Paraguay", "Uruguay", "Costa Rica",
]);

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

function expectedDeskHash(env) {
  return clean(env && env.SYNDICATION_PASSPHRASE_SHA256).toLowerCase();
}

function deskAuthorised(request, env) {
  const expected = expectedDeskHash(env);
  if (!expected) return { ok: false, status: 503, error: "desk_gate_not_configured" };
  const provided = clean(
    request.headers.get("x-desk-passphrase-sha256") ||
    request.headers.get("x-desk-hash")
  ).toLowerCase();
  if (!provided || provided !== expected) {
    return { ok: false, status: 401, error: "desk_locked" };
  }
  return { ok: true };
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
    "User-Agent": "urbanforestpark-flyer-intake",
  };
}

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

function todayIst() {
  try {
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Kolkata",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date());
  } catch (error) {
    const shifted = new Date(Date.now() + 5.5 * 60 * 60 * 1000);
    return shifted.toISOString().slice(0, 10);
  }
}

function addDays(isoDate, days) {
  const d = new Date(isoDate + "T00:00:00Z");
  if (isNaN(d.getTime())) return isoDate;
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

const MONTHS = {
  jan: 1, january: 1, feb: 2, february: 2, mar: 3, march: 3,
  apr: 4, april: 4, may: 5, jun: 6, june: 6, jul: 7, july: 7,
  aug: 8, august: 8, sep: 9, sept: 9, september: 9, oct: 10,
  october: 10, nov: 11, november: 11, dec: 12, december: 12,
};

function deadlineIso(value) {
  const text = clean(value, 90);
  if (!text) return "";
  const iso = text.match(/\b(20\d{2})-(\d{2})-(\d{2})\b/);
  if (iso) return `${iso[1]}-${iso[2]}-${iso[3]}`;
  let match = text.match(
    /\b(\d{1,2})\s+(Jan(?:uary)?\.?|Feb(?:ruary)?\.?|Mar(?:ch)?\.?|Apr(?:il)?\.?|May\.?|Jun(?:e)?\.?|Jul(?:y)?\.?|Aug(?:ust)?\.?|Sep(?:t(?:ember)?)?\.?|Oct(?:ober)?\.?|Nov(?:ember)?\.?|Dec(?:ember)?\.?)\s+(20\d{2})\b/i
  );
  if (match) {
    const month = MONTHS[match[2].replace(/\./g, "").toLowerCase().slice(0, 3)];
    if (month) {
      return `${match[3]}-${String(month).padStart(2, "0")}-${String(match[1]).padStart(2, "0")}`;
    }
  }
  match = text.match(
    /\b(Jan(?:uary)?\.?|Feb(?:ruary)?\.?|Mar(?:ch)?\.?|Apr(?:il)?\.?|May\.?|Jun(?:e)?\.?|Jul(?:y)?\.?|Aug(?:ust)?\.?|Sep(?:t(?:ember)?)?\.?|Oct(?:ober)?\.?|Nov(?:ember)?\.?|Dec(?:ember)?\.?)\s+(\d{1,2}),?\s+(20\d{2})\b/i
  );
  if (match) {
    const month = MONTHS[match[1].replace(/\./g, "").toLowerCase().slice(0, 3)];
    if (month) {
      return `${match[3]}-${String(month).padStart(2, "0")}-${String(match[2]).padStart(2, "0")}`;
    }
  }
  return "";
}

function slugify(value) {
  return clean(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60)
    .replace(/-+$/g, "");
}

function uniqueId(base, taken) {
  const root = slugify(base) || "green-job";
  let candidate = root;
  let counter = 2;
  while (taken.has(candidate)) {
    const suffix = "-" + counter;
    candidate = root.slice(0, 60 - suffix.length).replace(/-+$/g, "") + suffix;
    counter += 1;
  }
  taken.add(candidate);
  return candidate;
}

function roleIdentity(job) {
  const title = clean(job && (job.clean_title || job.title))
    .toLowerCase()
    .replace(/\b(?:19|20)\d{2}\b/g, " ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
  const org = clean(job && job.organization)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
  return title && org ? `${title}|${org}` : "";
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

function inferRegion(country, organization) {
  if (EUROPE.has(country)) return "Europe";
  if (NORTH_AMERICA.has(country)) return "North America";
  if (ASIA_PACIFIC.has(country)) return "Asia-Pacific";
  if (AFRICA_MIDDLE_EAST.has(country)) return "Africa & Middle East";
  if (LATIN_AMERICA.has(country)) return "Latin America";
  if (/\b(united nations|un |undp|unep|unfccc|iucn|wri|world bank|global fund|green climate fund|multilateral)\b/i.test(organization)) {
    return "UN / Multilateral";
  }
  return "Global / Remote";
}

function experienceFor(positionType, title) {
  const text = `${positionType} ${title}`.toLowerCase();
  if (/intern|fellowship|trainee|assistant/.test(text)) return "Entry Level / Fellowship";
  if (/director|head|senior|lead|chief/.test(text)) return "Senior";
  if (/manager|advisor|adviser|specialist|officer/.test(text)) return "Mid-Senior (3-6 Years)";
  return "1-3 Years";
}

function employmentFor(positionType, kind) {
  if (kind === "Internship" || /intern/i.test(positionType)) return "INTERN";
  if (kind === "Fellowship" || kind === "Scholarship") return "OTHER";
  if (kind === "Grant / Funding" || kind === "Competition / Award") return "CONTRACTOR";
  if (/consultant|contract/i.test(positionType)) return "CONTRACTOR";
  return "FULL_TIME";
}

function buildRecord(input, jurisdiction) {
  const today = todayIst();
  const title = clean(input.clean_title, MAX_TITLE);
  const organization = clean(input.organization, MAX_ORG);
  const applyUrl = safeHttpUrl(input.application_url);
  if (!title || !organization) {
    return { error: "missing_title_or_organization" };
  }
  if (!applyUrl) return { error: "invalid_application_url" };
  const kind = normalizeKind(input.opportunity_kind, title);
  const positionType = normalizePositionType(input.position_type, title);
  const country = jurisdiction === "india"
    ? "India"
    : clean(input.country, 90) || "Global";
  const deadline = clean(input.application_deadline, 90) || "Rolling / Open";
  const parsedDeadline = deadlineIso(deadline);
  const validThrough = parsedDeadline || addDays(today, 30);
  const orgWebsite = safeHttpUrl(input.org_website);
  let orgDomain = "";
  if (orgWebsite) {
    try {
      orgDomain = new URL(orgWebsite).hostname.replace(/^www\./, "");
    } catch (error) {
      orgDomain = "";
    }
  }
  const region = jurisdiction === "global"
    ? (
        GLOBAL_REGIONS.includes(clean(input.region))
          ? clean(input.region)
          : inferRegion(country, organization)
      )
    : "";
  return {
    record: {
      clean_title: title,
      organization,
      city: clean(input.city, 120),
      state: jurisdiction === "india"
        ? (clean(input.state, 120) || "Multiple States / Remote")
        : "",
      country,
      region,
      category: normalizeCategory(input.category, title, kind),
      position_type: positionType,
      opportunity_kind: kind,
      experience_level: EXPERIENCE_LEVELS.includes(clean(input.experience_level))
        ? clean(input.experience_level)
        : experienceFor(positionType, title),
      employment_type: employmentFor(positionType, kind),
      deadline_or_window: deadline,
      valid_through: validThrough,
      qualification_summary: clean(input.qualification_summary, 500),
      compensation_or_fellowship: clean(input.stipend_or_salary, 220) ||
        "Not disclosed - see official portal",
      role_summary: clean(input.role_summary, MAX_TEXT),
      key_responsibilities: listOfStrings(input.key_responsibilities, 6, 220),
      must_have_skills: listOfStrings(input.must_have_skills, 8, 70),
      application_tip: "Confirm the eligibility and closing date on the official application page before applying.",
      apply_url: applyUrl,
      org_website: orgWebsite,
      org_domain: orgDomain,
      source_portal: "Flyer intake (Gemini Vision)",
      entry_type: "posting",
      status: "active",
      global: jurisdiction === "global",
      evergreen: false,
      date_added: today,
      date_posted: today,
      title_hi: "",
      summary_hi: "",
      verification: {
        verified_at: today,
        method: "flyer-intake-gemini-vision",
        source: applyUrl,
      },
    },
  };
}

async function readRegistry(repo, path, token) {
  const response = await fetch(
    `${GITHUB_API}/repos/${repo}/contents/${path}?ref=${encodeURIComponent(BRANCH)}`,
    { headers: githubHeaders(token) }
  );
  if (response.status === 404) return { list: [], sha: null };
  if (!response.ok) {
    return { error: "github_read_failed", status: response.status };
  }
  const payload = await response.json();
  let list = [];
  try {
    const parsed = JSON.parse(decodeBase64(payload.content));
    list = Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    return { error: "registry_json_invalid", status: 500 };
  }
  return { list, sha: payload.sha || null };
}

async function writeRegistry(repo, path, list, sha, token, message) {
  const body = {
    message,
    content: encodeBase64(JSON.stringify(list, null, 2) + "\n"),
    branch: BRANCH,
  };
  if (sha) body.sha = sha;
  const response = await fetch(
    `${GITHUB_API}/repos/${repo}/contents/${path}`,
    {
      method: "PUT",
      headers: githubHeaders(token),
      body: JSON.stringify(body),
    }
  );
  if (!response.ok) {
    const detail = await response.text();
    return {
      error: response.status === 409 ? "write_conflict" : "github_write_failed",
      status: response.status,
      detail: clean(detail, 300),
    };
  }
  return { payload: await response.json() };
}

export async function commitJobRecord(job, jurisdiction, env, options) {
  const force = !!(options && options.force);
  const runtimeEnv = env || {};
  const token = githubToken(runtimeEnv);
  if (!token) return { ok: false, status: 503, error: "github_not_configured" };

  const registryName = clean(jurisdiction).toLowerCase();
  if (!["india", "global"].includes(registryName)) {
    return {
      ok: false,
      status: 422,
      error: "invalid_jurisdiction",
      allowed: ["india", "global"],
    };
  }
  if (!job || typeof job !== "object" || Array.isArray(job)) {
    return { ok: false, status: 422, error: "missing_job" };
  }

  const built = buildRecord(job, registryName);
  if (built.error) return { ok: false, status: 422, error: built.error };
  const record = built.record;

  const repo = repoName(runtimeEnv);
  const path = registryName === "global"
    ? "public/global_jobs.json"
    : "public/jobs.json";
  const registry = await readRegistry(repo, path, token);
  if (registry.error) {
    return {
      ok: false,
      status: 502,
      error: registry.error,
      upstream_status: registry.status,
    };
  }

  const existing = registry.list;
  const otherPath = registryName === "global"
    ? "public/jobs.json"
    : "public/global_jobs.json";
  const otherRegistry = await readRegistry(repo, otherPath, token);
  const allExisting = [...existing, ...(otherRegistry.list || [])];
  const applyUrl = record.apply_url.toLowerCase();
  const identity = roleIdentity(record);
  if (!force) {
    for (const item of allExisting) {
      if (clean(item && item.apply_url).toLowerCase() === applyUrl) {
        return {
          ok: false,
          status: 409,
          error: "duplicate_application_url",
          existing: clean(item.id),
        };
      }
      if (identity && roleIdentity(item) === identity) {
        return {
          ok: false,
          status: 409,
          error: "duplicate_role",
          existing: clean(item.id),
        };
      }
    }
  }

  const taken = new Set(existing.map((item) => clean(item && item.id)).filter(Boolean));
  record.id = uniqueId(`${record.clean_title}-${record.organization}`, taken);
  existing.unshift(record);

  const written = await writeRegistry(
    repo,
    path,
    existing,
    registry.sha,
    token,
    `feat(registry): add ${record.clean_title} via flyer intake`
  );
  if (written.error) {
    return {
      ok: false,
      status: written.status === 409 ? 409 : 502,
      error: written.error,
      upstream_status: written.status,
      detail: written.detail,
    };
  }

  return {
    ok: true,
    status: 200,
    id: record.id,
    path,
    registry: registryName,
    commit: written.payload && written.payload.commit && written.payload.commit.sha,
    job_url: `${SITE}/jobs/${encodeURIComponent(record.id)}`,
    registry_url: registryName === "global"
      ? `${SITE}/global-climate-sustainability-opportunities.html`
      : `${SITE}/`,
    rebuild_required: true,
  };
}

export async function updateJobRecord(job, jurisdiction, env) {
  const runtimeEnv = env || {};
  const token = githubToken(runtimeEnv);
  if (!token) return { ok: false, status: 503, error: "github_not_configured" };

  const registryName = clean(jurisdiction).toLowerCase();
  if (!["india", "global"].includes(registryName)) {
    return { ok: false, status: 422, error: "invalid_jurisdiction", allowed: ["india", "global"] };
  }
  if (!job || typeof job !== "object" || Array.isArray(job)) {
    return { ok: false, status: 422, error: "missing_job" };
  }

  const built = buildRecord(job, registryName);
  if (built.error) return { ok: false, status: 422, error: built.error };
  const newRecord = built.record;

  const repo = repoName(runtimeEnv);
  const path = registryName === "global" ? "public/global_jobs.json" : "public/jobs.json";
  const registry = await readRegistry(repo, path, token);
  if (registry.error) {
    return { ok: false, status: 502, error: registry.error, upstream_status: registry.status };
  }

  const existing = registry.list;
  const applyUrl = newRecord.apply_url.toLowerCase();
  const index = existing.findIndex((item) => clean(item && item.apply_url).toLowerCase() === applyUrl);
  if (index === -1) {
    return { ok: false, status: 404, error: "not_found", detail: "No existing record with this application URL." };
  }

  const oldRecord = existing[index];
  const updated = { ...oldRecord, ...newRecord, id: oldRecord.id, date_added: oldRecord.date_added };
  existing[index] = updated;

  const written = await writeRegistry(
    repo, path, existing, registry.sha, token,
    `fix(registry): update ${updated.clean_title} via Telegram intake`
  );
  if (written.error) {
    return { ok: false, status: written.status === 409 ? 409 : 502, error: written.error, upstream_status: written.status, detail: written.detail };
  }

  return {
    ok: true, status: 200, id: updated.id, path, registry: registryName,
    commit: written.payload && written.payload.commit && written.payload.commit.sha,
    job_url: `${SITE}/jobs/${encodeURIComponent(updated.id)}`,
    registry_url: registryName === "global" ? `${SITE}/global-climate-sustainability-opportunities.html` : `${SITE}/`,
    rebuild_required: true, updated: true,
  };
}

export async function deleteJobRecord(applyUrl, env) {
  const runtimeEnv = env || {};
  const token = githubToken(runtimeEnv);
  if (!token) return { ok: false, status: 503, error: "github_not_configured" };

  const url = safeHttpUrl(applyUrl);
  if (!url) return { ok: false, status: 422, error: "invalid_application_url" };
  const target = url.toLowerCase();

  const repo = repoName(runtimeEnv);
  const paths = ["public/jobs.json", "public/global_jobs.json"];
  for (const path of paths) {
    const registry = await readRegistry(repo, path, token);
    if (registry.error) continue;
    const existing = registry.list;
    const index = existing.findIndex((item) => clean(item && item.apply_url).toLowerCase() === target);
    if (index === -1) continue;

    const removed = existing[index];
    existing.splice(index, 1);

    const written = await writeRegistry(
      repo, path, existing, registry.sha, token,
      `chore(registry): delete ${removed.clean_title} via Telegram intake`
    );
    if (written.error) {
      return { ok: false, status: written.status === 409 ? 409 : 502, error: written.error, upstream_status: written.status, detail: written.detail };
    }

    return {
      ok: true, status: 200, id: removed.id, path,
      registry: path === "public/global_jobs.json" ? "global" : "india",
      commit: written.payload && written.payload.commit && written.payload.commit.sha,
      job_url: `${SITE}/jobs/${encodeURIComponent(removed.id)}`,
      rebuild_required: true, deleted: true,
    };
  }

  return { ok: false, status: 404, error: "not_found", detail: "No record with this application URL." };
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const runtimeEnv = env || {};
  const gate = deskAuthorised(request, runtimeEnv);
  if (!gate.ok) return json({ ok: false, error: gate.error }, gate.status);

  let body;
  try {
    body = await request.json();
  } catch (error) {
    return json({ ok: false, error: "invalid_json" }, 400);
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return json({ ok: false, error: "invalid_payload" }, 400);
  }

  const result = await commitJobRecord(body.job, body.jurisdiction, runtimeEnv);
  const status = result.status || (result.ok ? 200 : 500);
  const payload = { ...result };
  delete payload.status;
  return json(payload, status);
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
