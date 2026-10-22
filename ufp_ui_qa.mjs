/* ==========================================================================
   Urban Forest Park - Phase 6 UI / data QA harness  (ufp_ui_qa.mjs)
   --------------------------------------------------------------------------
   Verifies the expanded opportunity registry, the strictly separated Global
   registry, jurisdiction switcher + region filter, PWA widget/manifest/sw.js,
   the weekly LinkedIn roundup files, the red favicon/emblem assets, the
   header emblem on every page, the institutional refinement (slate /
   ink canvas, editorial serif titles, tabular readouts, micro-badges,
   arrow micro-interactions) and the internal Syndication Desk drawer
   (passphrase gate, digest/roundup assets, backlink kit, secret route).
   Run against  py -m http.server 8801 (public/).
   ========================================================================== */
import pkg from 'file:///C:/Users/arkra/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright-core/index.js';
const { chromium } = pkg;
import fs from 'node:fs';

const EXE = 'C:/Users/arkra/AppData/Local/ms-playwright/chromium-1243/chrome-win64/chrome.exe';
const BASE = 'http://127.0.0.1:8801';
const REPO = 'C:/Users/arkra/NVY DMRV/nvy-dmrv-dashboard/public';
const OUT = 'C:/Users/arkra/AppData/Local/Temp/opencode/ufp_ui_qa';
fs.mkdirSync(OUT, { recursive: true });

const read = (f) => JSON.parse(fs.readFileSync(REPO + '/' + f, 'utf-8'));
const india = read('jobs.json');
const indiaArchive = read('archive.json');
const globalJobs = read('global_jobs.json');
const globalArchive = read('global_archive.json');

const indiaAll = [...india, ...indiaArchive];
const globalAll = [...globalJobs, ...globalArchive];
const indiaIds = new Set(indiaAll.map(j => j.id));
const globalIds = new Set(globalAll.map(j => j.id));
const indiaStates = new Set(india.filter(j => j.state).map(j => j.state));

const GLOBAL_REGIONS = ['Global / Remote', 'Europe', 'North America', 'Asia-Pacific', 'Africa & Middle East', 'Latin America', 'UN / Multilateral'];
const KINDS = ['Job / Career', 'Fellowship', 'Scholarship', 'Grant / Funding', 'Internship', 'Competition / Award'];
const EMOJI_RE = /[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{FE0F}]/u;

const results = [];
function check(label, cond, extra = '') {
  results.push([label, !!cond, extra]);
  console.log((cond ? 'PASS ' : 'FAIL ') + label + (extra ? ' | ' + extra : ''));
}

/* ======================================================================
   A. Data-level checks (no browser)
   ====================================================================== */
check('global registry has 12+ seeded listings', globalJobs.length >= 12, 'count=' + globalJobs.length);
check('India registry has active listings', india.length > 0, 'count=' + india.length);

const bannedRole = /(sales manager|sales analyst|area sales|territory sales|sales executive|sales consultant|business development & marketing associate)/i;
const bannedHits = [...indiaAll, ...globalAll].filter(j => bannedRole.test(String(j.clean_title || '') + ' ' + String(j.title || '')));
check('ZERO Sales Manager / Sales Analyst / Area Sales roles across both registries',
  bannedHits.length === 0, bannedHits.map(j => j.id + ':' + j.clean_title).join(' | '));

const anonymousEmployers = [...indiaAll, ...globalAll].filter(j =>
  /confidential|undisclosed|unknown|leading client|not disclosed/i.test(String(j.organization || ''))
);
check('no anonymous (Confidential/Undisclosed/Unknown/Leading Client) employers in published registries',
  anonymousEmployers.length === 0,
  anonymousEmployers.map(j => j.id + ':' + j.organization).join(', '));

let overlap = [...globalIds].filter(id => indiaIds.has(id));
check('ZERO id overlap between India and Global registries', overlap.length === 0, overlap.slice(0, 3).join(','));

const globalMix = globalJobs.filter(j => j.global !== true);
check('every global record carries global:true', globalMix.length === 0, 'offenders=' + globalMix.length);
const indiaGlobalFlag = indiaAll.filter(j => j.global === true);
check('no India record carries global:true', indiaGlobalFlag.length === 0);
const indiaRegion = indiaAll.filter(j => j.region);
check('no India record carries a global region', indiaRegion.length === 0, indiaRegion.slice(0, 2).map(j => j.id).join(','));
const globalState = globalAll.filter(j => (j.state || '') !== '');
check('all global records have state:"" (never state-filtered)', globalState.length === 0, globalState.slice(0, 2).map(j => j.id).join(','));
const badRegion = globalJobs.filter(j => !GLOBAL_REGIONS.includes(j.region));
check('global regions use the fixed vocabulary', badRegion.length === 0, badRegion.slice(0, 3).map(j => j.region).join(' | '));
const badKind = globalJobs.filter(j => !KINDS.includes(j.opportunity_kind));
check('global opportunity_kind values are exact', badKind.length === 0, badKind.slice(0, 3).map(j => j.opportunity_kind).join(' | '));
const regionsUsed = new Set(globalJobs.map(j => j.region));
check('global registry spans 5+ regions', regionsUsed.size >= 5, [...regionsUsed].join(', '));
const kindsUsed = new Set(globalJobs.map(j => j.opportunity_kind));
check('global registry spans 4+ opportunity kinds', kindsUsed.size >= 4, [...kindsUsed].join(', '));
const GLOBAL_SEED_URL_RE = /^https:\/\/([a-z0-9-]+\.)*(unfccc\.int|greenclimate\.fund|undp\.org|thegef\.org|worldbank\.org|iucn\.org|wri\.org|wri-india\.org|esa\.int|climate\.esa\.int|eacea\.ec\.europa\.eu|erasmus-plus\.ec\.europa\.eu|futureearth\.org|chevening\.org|unu\.edu|zayedsustainabilityprize\.(org|com)|earthshotprize\.org|simonsfoundation\.org)/;
function hasOfficialGlobalUrl(j) {
  const org = String(j.org_website || '');
  if (GLOBAL_SEED_URL_RE.test(org)) return true;
  // Harvested opportunities must apply on the organisation's own host.
  try {
    const orgHost = new URL(org).hostname.replace(/^www\./, '');
    const applyHost = new URL(String(j.apply_url || '')).hostname.replace(/^www\./, '');
    return Boolean(orgHost) && (applyHost === orgHost || applyHost.endsWith('.' + orgHost));
  } catch {
    return false;
  }
}
const badGlobalUrls = globalJobs.filter(j => !hasOfficialGlobalUrl(j));
check('global records use official organisation URLs', badGlobalUrls.length === 0,
  'bad=' + badGlobalUrls.map(j => j.id + ':' + (j.org_website || '')).join(','));

/* Weekly LinkedIn roundup files */
const txt = fs.readFileSync(REPO + '/linkedin_weekly_post.txt', 'utf-8');
const weekly = read('linkedin_weekly.json');
const numbered = txt.split('\n').filter(l => /^\d{1,2}\.\s/.test(l));
check('roundup txt has 8-10 numbered items', numbered.length >= 8 && numbered.length <= 10, 'items=' + numbered.length);
const urls = [...txt.matchAll(/https:\/\/www\.urbanforestpark\.com\/jobs\/([A-Za-z0-9_.\-%]+)/g)].map(m => decodeURIComponent(m[1]));
check('roundup txt has as many links as items', urls.length === numbered.length, `urls=${urls.length} items=${numbered.length}`);
const badUrls = urls.filter(id => !indiaIds.has(id) && !globalIds.has(id));
check('every roundup link resolves to a registry id', badUrls.length === 0, badUrls.join(','));
check('roundup txt labels [INDIA] and [GLOBAL]', txt.includes('[INDIA]') && txt.includes('[GLOBAL]'));
check('roundup txt carries the required hashtags', txt.includes('#ClimateJobs') && txt.includes('#Forestry') && txt.includes('#ESG') && txt.includes('#Sustainability') && txt.includes('#JRF') && txt.includes('#Fellowships') && txt.includes('#GreenJobsIndia') && txt.includes('#GIS') && txt.includes('#UrbanForestPark'));
check('roundup has 2-3 global highlights', weekly.counts.global >= 2 && weekly.counts.global <= 3, 'global=' + weekly.counts.global);
check('roundup json matches txt item count', weekly.counts.total === numbered.length, `${weekly.counts.total} vs ${numbered.length}`);
check('roundup json has hook + cta', !!weekly.hook && !!weekly.cta);
check('roundup json items carry registry + static job url', weekly.items.every(i => (i.registry === 'india' || i.registry === 'global') && /^https:\/\/www\.urbanforestpark\.com\/jobs\//.test(i.url)));
const wrongSubject = weekly.subject !== 'Ready to Post: Your Weekly LinkedIn Top 10 Opportunities Roundup';
check('exact weekly LinkedIn email subject', !wrongSubject, weekly.subject);

/* Static /jobs/<slug> detail pages: one per active and archived record. */
const allStaticJobs = [...indiaAll, ...globalAll];
const activeStaticJobs = [...india, ...globalJobs];
const pageText = (id) => {
  const file = REPO + '/jobs/' + id + '.html';
  return fs.existsSync(file) ? fs.readFileSync(file, 'utf-8') : '';
};
const missingStatic = allStaticJobs.filter(j => !fs.existsSync(REPO + '/jobs/' + j.id + '.html'));
check('static /jobs/<id>.html page exists for every registry record',
  missingStatic.length === 0, 'missing=' + missingStatic.map(j => j.id).slice(0, 4).join(','));

const badCanonical = allStaticJobs.filter(j => {
  const html = pageText(j.id);
  return !html.includes('<link rel="canonical" href="https://www.urbanforestpark.com/jobs/' + j.id + '">');
});
check('every static job page has a self-referencing www canonical',
  badCanonical.length === 0, badCanonical.map(j => j.id).slice(0, 4).join(','));

const staticTitles = allStaticJobs.map(j => {
  const m = pageText(j.id).match(/<title>([^<]+)<\/title>/i);
  return m ? m[1] : '';
});
check('static job pages carry unique, non-empty titles',
  staticTitles.every(Boolean) && new Set(staticTitles).size === staticTitles.length,
  'n=' + staticTitles.length + ' unique=' + new Set(staticTitles).size);

const badActiveSchema = activeStaticJobs.filter(j => {
  const html = pageText(j.id);
  return !html.includes('"@type": "JobPosting"') || !html.includes('"url": "https://www.urbanforestpark.com/jobs/' + j.id + '"');
});
check('every active static page carries JobPosting JSON-LD with its static URL',
  badActiveSchema.length === 0, badActiveSchema.map(j => j.id).slice(0, 4).join(','));

const badArchiveSchema = indiaArchive.filter(j => pageText(j.id).includes('"@type": "JobPosting"'));
check('archived static pages carry WebPage, never stale JobPosting schema',
  badArchiveSchema.length === 0, badArchiveSchema.map(j => j.id).slice(0, 4).join(','));

const badRelated = activeStaticJobs.filter(j => (pageText(j.id).match(/class="related-card"/g) || []).length !== 5);
check('every active static job page links exactly five related jobs',
  badRelated.length === 0, badRelated.map(j => j.id).slice(0, 4).join(','));

const badApply = activeStaticJobs.filter(j => {
  const html = pageText(j.id);
  const apply = String(j.apply_url || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;');
  return !html.includes('href="' + apply + '" target="_blank"');
});
check('every active static page exposes the official apply link in a new tab',
  badApply.length === 0, badApply.map(j => j.id).slice(0, 4).join(','));

const indexRaw = fs.readFileSync(REPO + '/index.html', 'utf-8');
const feedStart = indexRaw.indexOf('<!-- JOB_FEED_START -->');
const feedEnd = indexRaw.indexOf('<!-- JOB_FEED_END -->');
const rawFeed = feedStart >= 0 && feedEnd > feedStart ? indexRaw.slice(feedStart, feedEnd) : '';
check('index.html pre-renders 12 job cards inside #jobs-feed markers',
  (rawFeed.match(/<article class="job-card/g) || []).length === 12,
  'n=' + (rawFeed.match(/<article class="job-card/g) || []).length);
check('raw index.html contains no Loading... feed placeholder',
  !/Loading(?:\.\.\.|&hellip;|…)/i.test(indexRaw));

const sitemapRaw = fs.readFileSync(REPO + '/sitemap.xml', 'utf-8');
const missingSitemapJobs = allStaticJobs.filter(j => !sitemapRaw.includes('<loc>https://www.urbanforestpark.com/jobs/' + j.id + '</loc>'));
check('sitemap.xml lists every static job URL',
  missingSitemapJobs.length === 0 && !sitemapRaw.includes('?job='),
  'missing=' + missingSitemapJobs.length + ' legacy=' + sitemapRaw.includes('?job='));

/* ======================================================================
   B. Browser setup
   ====================================================================== */
const browser = await chromium.launch({ executablePath: EXE, headless: true });
const context = await browser.newContext({ viewport: { width: 1366, height: 900 } });
await context.grantPermissions(['notifications', 'clipboard-read', 'clipboard-write'], { origin: BASE });
await context.addInitScript(() => {
  window.__ufpNotifs = [];
  try {
    const orig = ServiceWorkerRegistration.prototype.showNotification;
    if (orig && !ServiceWorkerRegistration.prototype.__ufpPatched) {
      ServiceWorkerRegistration.prototype.__ufpPatched = true;
      ServiceWorkerRegistration.prototype.showNotification = function (title, options) {
        try { window.__ufpNotifs.push({ via: 'sw', title: String(title), body: (options && options.body) || '' }); } catch (e) {}
        return orig.apply(this, arguments);
      };
    }
  } catch (e) {}
  try {
    const NativeNotification = window.Notification;
    window.Notification = new Proxy(NativeNotification, {
      construct(target, args) {
        try { window.__ufpNotifs.push({ via: 'window', title: String(args[0]), body: (args[1] && args[1].body) || '' }); } catch (e) {}
        return Reflect.construct(target, args);
      }
    });
  } catch (e) {}
});

const consoleErrors = [];
const sameOriginHttpErrors = [];
function attach(page, tag) {
  page.on('pageerror', err => {
    const stack = String(err.stack || '');
    if (/googlesyndication|doubleclick|google-analytics/.test(stack)) return;
    consoleErrors.push(tag + ' pageerror: ' + err.message + ' :: ' + stack.slice(0, 600));
  });
  page.on('response', response => {
    if (response.status() >= 400 && response.url().startsWith(BASE)) {
      sameOriginHttpErrors.push(response.status() + ' ' + response.url());
    }
  });
  page.on('console', msg => {
    if (msg.type() !== 'error') return;
    const text = msg.text();
    const loc = (msg.location() || {}).url || '';
    /* Ignore third-party analytics/ad noise: only same-origin console
       errors (or errors without a location) are treated as regressions. */
    if (loc && !loc.startsWith(BASE) && !/(^|\/)(js|styles)\//.test(loc)) return;
    if (/Unsupported method|api\/subscribe|ERR_ABORTED|google-analytics|googlesyndication|doubleclick/.test(text)) return;
    consoleErrors.push(tag + ' console: ' + text.slice(0, 140) + (loc ? ' @ ' + loc : ''));
  });
}

const page = await context.newPage();
attach(page, 'home');
const cardIds = async (pg) => pg.$$eval('.job-card', els => els.map(el => el.getAttribute('data-id')));

/* ======================================================================
   C. HTTP sweep - every new/affected asset
   ====================================================================== */
const sweep = [
  '/', '/global-climate-sustainability-opportunities.html',
  '/manifest.json', '/site.webmanifest', '/sw.js', '/js/pwa.js',
  '/favicon.svg', '/favicon.ico', '/favicon-96x96.png', '/apple-touch-icon.png',
  '/web-app-manifest-192x192.png', '/web-app-manifest-512x512.png',
  '/assets/images/Logo_UFF.png',
  '/linkedin_weekly_post.txt', '/linkedin_weekly.json',
  '/js/back-to-top.js',
  '/global_jobs.json', '/global_archive.json',
  '/dashboard.html', '/privacy.html', '/terms.html', '/cookies.html',
  '/accessibility.html', '/unsubscribe.html',
  '/jrf-srf-project-associate-jobs.html', '/phd-fellowships-climate-sustainability.html',
  '/forestry-wildlife-government-jobs.html', '/gis-remote-sensing-climate-jobs.html',
  '/esg-carbon-sustainability-jobs.html', '/hindi-environment-forestry-jobs.html',
  '/bharat-regional-green-jobs.html'
];
for (const path of sweep) {
  const resp = await context.request.get(BASE + path);
  check('HTTP 200 ' + path, resp.status() === 200, String(resp.status()));
}
const missing = await context.request.get(BASE + '/js/does-not-exist-control.js');
check('control: a missing asset returns 404', missing.status() === 404, String(missing.status()));

/* manifest exact values */
const manifest = await (await context.request.get(BASE + '/manifest.json')).json();
check('manifest name exact', manifest.name === 'Urban Forest Park — Green Jobs, Grants & Fellowships', manifest.name);
check('manifest short_name exact', manifest.short_name === 'UFP Jobs', manifest.short_name);
check('manifest display standalone', manifest.display === 'standalone');
check('manifest start_url /?source=pwa', manifest.start_url === '/?source=pwa');
check('manifest theme_color #C9544D', manifest.theme_color === '#C9544D');
check('manifest background_color #0B0F17', manifest.background_color === '#0B0F17');
const iconSizes = (manifest.icons || []).map(i => i.sizes);
check('manifest has 192x192 + 512x512 icons', iconSizes.includes('192x192') && iconSizes.includes('512x512'), iconSizes.join(','));

/* sw.js content */
const sw = await (await context.request.get(BASE + '/sw.js')).text();
check('sw.js caches the offline shell', /caches\.open/.test(sw) && /addEventListener\('install'/.test(sw));
check('sw.js checks jobs.json + global_jobs.json', sw.includes('/jobs.json') && sw.includes('/global_jobs.json'));
check('sw.js can raise notifications', sw.includes('showNotification') && sw.includes('notificationclick'));
check('sw.js handles stats + freshness message', sw.includes('/stats.json') && sw.includes('UFP_CHECK_JOBS'));

/* ======================================================================
   D. Homepage - jurisdiction switcher, filters, feed separation
   ====================================================================== */
await page.goto(BASE + '/', { waitUntil: 'networkidle' });
await page.waitForSelector('.job-card', { timeout: 20000 });

check('manifest link is /manifest.json', (await page.getAttribute('link[rel="manifest"]', 'href')) === '/manifest.json');
check('pwa.js is loaded on the registry', (await page.locator('script[src="js/pwa.js"]').count()) === 1);
check('header emblem rendered (naturalWidth>0)', await page.evaluate(() => {
  const img = document.querySelector('.brand .ufp-header-logo');
  return !!img && img.complete && img.naturalWidth > 0;
}));
check('header emblem is a 48px circle', await page.evaluate(() => {
  const img = document.querySelector('.brand .ufp-header-logo');
  if (!img) return false;
  const cs = getComputedStyle(img);
  return cs.borderRadius === '50%' && Math.abs(parseFloat(cs.width) - 48) <= 1 && cs.objectFit === 'cover'
    && /rgba\(16,\s*185,\s*129/.test(cs.borderColor);
}));

const heroPills = page.locator('.hero-js [data-jurisdiction]');
check('hero jurisdiction switcher has 2 pills', await heroPills.count() === 2);
const heroIndiaText = (await heroPills.nth(0).innerText()).replace(/\s+/g, ' ');
const heroGlobalText = (await heroPills.nth(1).innerText()).replace(/\s+/g, ' ');
check('hero India pill labelled "India Jobs" + "Jobs, JRF, Fellowships & Grants"',
  /India Jobs/.test(heroIndiaText) && /Jobs, JRF, Fellowships & Grants/.test(heroIndiaText), heroIndiaText);
check('hero Global pill labelled "Global Opportunities" + "International Jobs, Grants & Scholarships"',
  /Global Opportunities/.test(heroGlobalText) && /International Jobs, Grants & Scholarships/.test(heroGlobalText), heroGlobalText);
check('header jurisdiction switcher removed from the header', await page.locator('.header-js [data-jurisdiction]').count() === 0);
check('header actions carry no flag emoji', await page.evaluate(() => {
  const actions = document.querySelector('.header-actions');
  return !!actions && !/\u{1F1EE}\u{1F1F3}|\u{1F30D}/u.test(actions.textContent);
}));
check('professional language control: 2 segments, no separator, EN active, distinct active fill', await page.evaluate(() => {
  const group = document.getElementById('lang-toggle');
  if (!group || !group.closest('.header-actions')) return false;
  const btns = group.querySelectorAll('.lang-btn');
  if (btns.length !== 2) return false;
  if (group.querySelector('.lang-sep')) return false;
  const en = btns[0], hi = btns[1];
  if (en.getAttribute('data-ufp-lang-option') !== 'en' || hi.getAttribute('data-ufp-lang-option') !== 'hi') return false;
  if (en.getAttribute('aria-pressed') !== 'true' || hi.getAttribute('aria-pressed') !== 'false') return false;
  if (getComputedStyle(group).borderRadius !== '999px') return false;
  return getComputedStyle(en).backgroundColor !== getComputedStyle(hi).backgroundColor;
}));

check('12 sector pills (11 categories + All Sectors)', await page.locator('.cat-pill').count() === 12, 'n=' + await page.locator('.cat-pill').count());
const pillCats = await page.$$eval('.cat-pill', els => els.map(el => el.getAttribute('data-cat')));
check('new grant/scholarship/fellowship/internship/competition pills exist',
  ['Grants & Research Funding', 'Scholarships & Doctoral Support', 'Fellowships & Leadership Programs', 'Internships & Student Traineeships', 'Competitions, Hackathons & Awards'].every(c => pillCats.includes(c)),
  pillCats.join(' | ').slice(0, 200));

const kindValues = await page.$$eval('#kind-filter option', els => els.map(o => o.value));
check('opportunity-type filter has 7 exact values',
  kindValues.length === 7 && kindValues[0] === 'all' && KINDS.every(k => kindValues.includes(k)),
  kindValues.join(' | '));

/* India default state */
const indiaCardIds = await cardIds(page);
check('India feed shows only India records', indiaCardIds.length > 0 && indiaCardIds.every(id => indiaIds.has(id)), 'cards=' + indiaCardIds.length);
check('India feed shows no global records', indiaCardIds.every(id => !globalIds.has(id)));
const stateOptsIndia = await page.$$eval('#state-filter option', els => els.map(o => ({ v: o.value, t: o.textContent })));
check('India state filter starts with All India', /All India/.test(stateOptsIndia[0].t), stateOptsIndia[0].t);
check('India state filter is clean (only real states)',
  stateOptsIndia.slice(1).every(o => indiaStates.has(o.v)), stateOptsIndia.slice(1, 5).map(o => o.v).join(' | '));
check('India state filter has no duplicates', new Set(stateOptsIndia.map(o => o.v)).size === stateOptsIndia.length);
check('India state filter carries no global regions', !stateOptsIndia.some(o => GLOBAL_REGIONS.includes(o.v)), stateOptsIndia.map(o => o.v).join(' | ').slice(0, 120));
check('deadline / application-window chips render on India cards', await page.locator('.job-card .jc-deadline').count() >= 1, 'n=' + await page.locator('.job-card .jc-deadline').count());
check('public broadcast/roundup copy buttons removed from the homepage UI',
  await page.locator('#copy-linkedin-roundup, #copy-daily-digest, #copy-daily-digest-strip, .footer-broadcast').count() === 0);
check('no community.copy i18n hook left in the DOM', await page.locator('[data-i18n="community.copy"]').count() === 0);
check('no "Copy Weekly LinkedIn Roundup" text remains on the page', !(await page.locator('body').innerText()).includes('Copy Weekly LinkedIn Roundup'));
check('subtle Syndication Desk link present in the footer', await page.locator('footer [data-syndication-open]').count() >= 1);
check('institutional mailto on the homepage footer', await page.locator('footer a[href="mailto:urbanforestpark@gmail.com"]').count() >= 1);

/* India state filter actually filters */
const firstState = stateOptsIndia.find(o => indiaStates.has(o.v));
if (firstState) {
  await page.selectOption('#state-filter', firstState.v);
  await page.waitForTimeout(500);
  const ids = await cardIds(page);
  const wrong = ids.filter(id => (indiaAll.find(j => j.id === id) || {}).state !== firstState.v);
  check('state filter returns only that state', wrong.length === 0 && ids.length > 0, `${ids.length} cards, wrong=${wrong.length}`);
  await page.selectOption('#state-filter', 'all');
  await page.waitForTimeout(400);
}
check('India mode URL has no region=global', !page.url().includes('region=global'), page.url());

/* Switch to Global via hero pill */
await page.locator('.hero-js [data-jurisdiction="global"]').click();
await page.waitForTimeout(700);
check('global pill activates (aria-pressed)', (await page.getAttribute('.hero-js [data-jurisdiction="global"]', 'aria-pressed')) === 'true');
check('body enters registry-global mode', await page.evaluate(() => document.body.classList.contains('registry-global')));
check('URL routes to ?region=global', page.url().includes('region=global'), page.url());
check('hero heading swaps to the Global title', /Worldwide/.test(await page.$eval('#hero-heading', el => el.textContent)), (await page.$eval('#hero-heading', el => el.textContent)).slice(0, 60));
check('hero sub swaps to the Global copy', /International jobs, grants/.test(await page.$eval('#hero-sub', el => el.textContent)), (await page.$eval('#hero-sub', el => el.textContent)).slice(0, 60));
check('feed header switches to International Opportunities', /International Opportunities/.test(await page.$eval('#feed-title', el => el.textContent)));
const globalCardIds = await cardIds(page);
check('Global feed shows 12+ global records', globalCardIds.length >= 12, 'cards=' + globalCardIds.length);
check('Global feed shows ZERO India records', globalCardIds.every(id => !indiaIds.has(id)));
check('Global feed records all resolve to global_jobs.json', globalCardIds.every(id => globalIds.has(id)));

const stateOptsGlobal = await page.$$eval('#state-filter option', els => els.map(o => ({ v: o.value, t: o.textContent })));
check('region filter replaces the state dropdown (All Global)', /All Global/.test(stateOptsGlobal[0].t), stateOptsGlobal[0].t);
check('region filter offers the 7 global regions', GLOBAL_REGIONS.every(r => stateOptsGlobal.some(o => o.v === r)), stateOptsGlobal.map(o => o.v).join(' | '));
check('region filter is clean (no Indian states)', !stateOptsGlobal.some(o => o.v !== 'all' && indiaStates.has(o.v)));
check('region filter has no duplicates', new Set(stateOptsGlobal.map(o => o.v)).size === stateOptsGlobal.length);
check('state-filter label switched to Global Region', /Global Region/i.test(await page.$eval('#state-filter-label', el => el.textContent)));

/* Region sub-filter */
await page.selectOption('#state-filter', 'UN / Multilateral');
await page.waitForTimeout(600);
const unionCards = await cardIds(page);
const unionWrong = unionCards.filter(id => (globalJobs.find(j => j.id === id) || {}).region !== 'UN / Multilateral');
check('region filter (UN / Multilateral) is exact', unionCards.length > 0 && unionWrong.length === 0, `${unionCards.length} cards, wrong=${unionWrong.length}`);
check('region sub-filter routed in URL (gregion)', page.url().includes('gregion=UN'), decodeURIComponent(page.url()));

/* Kind filter in global mode */
await page.selectOption('#state-filter', 'all');
await page.selectOption('#kind-filter', 'Scholarship');
await page.waitForTimeout(600);
const schIds = await cardIds(page);
const schWrong = schIds.filter(id => (globalJobs.find(j => j.id === id) || {}).opportunity_kind !== 'Scholarship');
check('opportunity-type filter returns only scholarships', schIds.length > 0 && schWrong.length === 0, `${schIds.length} cards, wrong=${schWrong.length}`);
const schBadges = await page.$$eval('.job-card .badge-kind', els => els.map(e => e.textContent.trim()));
check('scholarship cards render the kind badge', schBadges.length === schIds.length && schBadges.every(t => t === 'Scholarship'), schBadges.join(','));
await page.selectOption('#kind-filter', 'all');
await page.waitForTimeout(500);
check('global feed restored to all regions/kinds', (await cardIds(page)).length === globalCardIds.length);

/* Back to India */
await page.locator('.hero-js [data-jurisdiction="india"]').click();
await page.waitForTimeout(700);
check('India mode restored (no registry-global)', !(await page.evaluate(() => document.body.classList.contains('registry-global'))));
check('India mode URL cleaned of region=global', !page.url().includes('region=global'), page.url());
const backIds = await cardIds(page);
check('India feed restored with India-only records', backIds.length > 0 && backIds.every(id => indiaIds.has(id)));
check('state-filter label restored to State / Region', /State \/ Region/i.test(await page.$eval('#state-filter-label', el => el.textContent)));

/* Deep link: region + kind */
await page.goto(BASE + '/?region=global&kind=' + encodeURIComponent('Grant / Funding'), { waitUntil: 'networkidle' });
await page.waitForSelector('.job-card', { timeout: 20000 });
const grantIds = await cardIds(page);
const grantWrong = grantIds.filter(id => (globalJobs.find(j => j.id === id) || {}).opportunity_kind !== 'Grant / Funding');
check('?region=global&kind=Grant / Funding deep link filters correctly', grantIds.length > 0 && grantWrong.length === 0, `${grantIds.length} cards`);
check('deep-link hero heading shows the global kind scope', /Grant \/ Funding/.test(await page.$eval('#hero-heading', el => el.textContent)), (await page.$eval('#hero-heading', el => el.textContent)).slice(0, 60));

/* Global dossier: kind + deadline + region rows */
const dossierJob = globalJobs.find(j => j.opportunity_kind === 'Scholarship') || globalJobs[0];
await page.goto(BASE + '/?job=' + encodeURIComponent(dossierJob.id), { waitUntil: 'networkidle' });
await page.waitForSelector('.detail-card', { timeout: 20000 });
check('global dossier opens from ?job=id', await page.locator('.detail-card').count() === 1);
check('global dossier shows the kind badge', (await page.locator('.detail-kicker .badge-kind').count()) >= (dossierJob.opportunity_kind !== 'Job / Career' ? 1 : 0));
const eligRows = await page.$$eval('.elig-grid dt', els => els.map(e => e.textContent.trim()));
check('global dossier shows Opportunity Type + Deadline / Window rows', eligRows.includes('Opportunity Type') && eligRows.includes('Deadline / Window'), eligRows.join(' | '));
check('global dossier shows the Region row with its region', await page.evaluate((region) => {
  const rows = [...document.querySelectorAll('.elig-grid > div')];
  const row = rows.find(r => r.querySelector('dt') && r.querySelector('dt').textContent.trim() === 'Region');
  return !!row && row.querySelector('dd').textContent.includes(region);
}, dossierJob.region), dossierJob.region);
check('global dossier eligibility shows its exact kind', await page.evaluate((kind) => {
  const rows = [...document.querySelectorAll('.elig-grid > div')];
  const row = rows.find(r => r.querySelector('dt') && r.querySelector('dt').textContent.trim() === 'Opportunity Type');
  return !!row && row.querySelector('dd').textContent.trim() === kind;
}, dossierJob.opportunity_kind), dossierJob.opportunity_kind);

/* ======================================================================
   E. PWA widget + service worker + notifications
   ====================================================================== */
await page.goto(BASE + '/', { waitUntil: 'networkidle' });
check('hero heading restored to the India title', /India/.test(await page.$eval('#hero-heading', el => el.textContent)), (await page.$eval('#hero-heading', el => el.textContent)).slice(0, 60));
await page.waitForSelector('#ufp-app-widget:not([hidden])', { timeout: 10000 });
check('app widget pops up on the registry', await page.locator('#ufp-app-widget').isVisible());
const widgetText = (await page.locator('#ufp-app-widget').innerText()).replace(/\s+/g, ' ');
check('widget headline exact', widgetText.includes('Get the UrbanForestPark App & Instant Job Alerts'), widgetText.slice(0, 80));
check('widget subtitle mentions JRF / Forestry / ESG / Grant alerts', /JRF, Forestry, ESG and Grant alerts/.test(widgetText));
check('widget install button labelled', (await page.locator('#ufp-install-btn').innerText()).includes('Download / Install App'));
check('widget notify button labelled', (await page.locator('#ufp-notify-btn').innerText()).includes('Enable Instant Job Notifications'));

const swWorkerUrls = context.serviceWorkers().map(w => w.url());
check('sw.js registered with root scope', swWorkerUrls.some(u => /\/sw\.js$/.test(u)), swWorkerUrls.join(','));

await page.locator('#ufp-app-close').click();
await page.waitForTimeout(400);
check('x collapses widget to the floating pill', await page.locator('#ufp-app-widget').isHidden() && await page.locator('#ufp-app-pill').isVisible());
check('collapse state persisted', await page.evaluate(() => localStorage.getItem('ufp_app_widget_collapsed')) === '1');
check('pill labelled "App & Alerts"', (await page.locator('#ufp-app-pill').innerText()).includes('App & Alerts'));
await page.locator('#ufp-app-pill').click();
await page.waitForTimeout(400);
check('pill re-opens the widget', await page.locator('#ufp-app-widget').isVisible());

await page.locator('#ufp-notify-btn').click();
await page.waitForTimeout(4000);
check('notifications flag stored (ufp_notifications_enabled=true)', await page.evaluate(() => localStorage.getItem('ufp_notifications_enabled')) === 'true');
const lastSeen = await page.evaluate(() => localStorage.getItem('ufp_last_seen_job_id'));
check('last seen job id stored', !!lastSeen, String(lastSeen));
const notifs1 = await page.evaluate(() => window.__ufpNotifs || []);
check('welcome notification raised', notifs1.length >= 1 && /alerts are ON/.test(notifs1.map(n => n.title).join(' | ')), JSON.stringify(notifs1).slice(0, 140));

await page.evaluate(() => localStorage.setItem('ufp_last_seen_job_id', 'stale-nonexistent-id'));
await page.evaluate(() => window.dispatchEvent(new Event('focus')));
await page.waitForTimeout(3500);
const notifs2 = await page.evaluate(() => window.__ufpNotifs || []);
check('auto-alert fires for a newer job', notifs2.some(n => /New on UrbanForestPark/.test(n.title)), JSON.stringify(notifs2.slice(-2)).slice(0, 200));
check('alert deep-links to the job dossier', notifs2.some(n => /tap to view and apply/.test(n.body || '')), (notifs2.slice(-1)[0] || {}).body || '');

await page.screenshot({ path: OUT + '/home-global-widget.png' });
await page.locator('.hero-js [data-jurisdiction="global"]').click();
await page.waitForTimeout(700);
await page.screenshot({ path: OUT + '/home-global.png' });
await page.locator('.hero-js [data-jurisdiction="india"]').click();
await page.waitForTimeout(500);

/* ======================================================================
   F. Syndication Desk drawer (internal; public buttons removed)
   ====================================================================== */
await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(500);

/* Invisible until summoned. */
check('drawer is invisible before it is summoned', await page.locator('.synd-root.is-open').count() === 0);

/* Ctrl+Shift+U summons it. */
await page.keyboard.press('Control+Shift+U');
await page.waitForTimeout(400);
check('Ctrl+Shift+U opens the Syndication Desk', await page.locator('.synd-root.is-open').count() === 1);
check('passphrase gate shown first', await page.locator('#synd-gate').isVisible() && !(await page.locator('#synd-content').isVisible()));

/* Wrong passphrase is rejected. */
await page.fill('#synd-pass', 'not-the-passphrase');
await page.click('#synd-unlock');
await page.waitForTimeout(450);
check('wrong passphrase rejected with an error', /not recognised/i.test(await page.locator('#synd-err').innerText()));
check('gate stays closed after a bad attempt', await page.locator('#synd-gate').isVisible());

/* Correct passphrase unlocks the desk for the session. */
await page.fill('#synd-pass', 'UrbanForest@2026');
await page.click('#synd-unlock');
await page.waitForTimeout(1000);
check('correct passphrase unlocks the desk', await page.locator('#synd-content').isVisible() && !(await page.locator('#synd-gate').isVisible()));
check('lock icon is rendered on the gate markup', await page.locator('.synd-gate .synd-lock svg').count() === 1);

/* Assets load: digest + roundup previews. */
const digestPreview = await page.locator('#synd-digest-pre').innerText();
const roundupPreview = await page.locator('#synd-roundup-pre').innerText();
check('daily broadcast preview populated from daily_digest.json', digestPreview.length > 40 && !/not available|No broadcast/i.test(digestPreview), digestPreview.slice(0, 60));
check('LinkedIn roundup preview populated from linkedin_weekly_post.txt', roundupPreview.length > 40 && !/not available|No roundup/i.test(roundupPreview), roundupPreview.slice(0, 60));

/* Copy the broadcast to the clipboard. */
await page.click('#synd-copy-digest');
await page.waitForTimeout(600);
const clipText = await page.evaluate(() => navigator.clipboard.readText().catch(() => ''));
check('broadcast copy button writes the digest to the clipboard', clipText.length > 40 && clipText.includes(digestPreview.slice(10, 40)), clipText.slice(0, 50));
check('copy confirmation shown in the drawer status line', /copied/i.test(await page.locator('#synd-status').innerText()));

/* Backlink kit rows + tracked copy. */
const kitRows = await page.locator('.synd-row').count();
check('backlink kit lists 10+ canonical links', kitRows >= 10, 'rows=' + kitRows);
await page.locator('.synd-row [data-copy-text*="utm_source=syndication"]').first().click();
await page.waitForTimeout(450);
const clipTracked = await page.evaluate(() => navigator.clipboard.readText().catch(() => ''));
check('tracked backlink carries the syndication UTM tag', /utm_source=syndication/.test(clipTracked), clipTracked.slice(0, 70));

/* Locking the desk brings the gate back. */
await page.click('#synd-lock-btn');
await page.waitForTimeout(300);
check('Lock desk returns to the passphrase gate', await page.locator('#synd-gate').isVisible());

/* Escape closes the drawer. */
await page.keyboard.press('Escape');
await page.waitForTimeout(350);
check('Escape closes the drawer', await page.locator('.synd-root.is-open').count() === 0);

/* Locking persists: reopening restores the gate. */
await page.keyboard.press('Control+Shift+U');
await page.waitForTimeout(350);
check('locking the desk persists across reopen (gate shown)', await page.locator('#synd-gate').isVisible());

/* Unlock again; closing and reopening skips the gate for this tab session. */
await page.fill('#synd-pass', 'UrbanForest@2026');
await page.click('#synd-unlock');
await page.waitForTimeout(900);
check('re-unlock via passphrase succeeds', await page.locator('#synd-content').isVisible());
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
await page.keyboard.press('Control+Shift+U');
await page.waitForTimeout(400);
check('unlock persists for the tab session (gate skipped)', await page.locator('#synd-content').isVisible());
await page.keyboard.press('Escape');
await page.waitForTimeout(250);

/* ?syndication=1 deep link opens the desk. */
await page.goto(BASE + '/?syndication=1', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(450);
check('?syndication=1 deep link opens the desk', await page.locator('.synd-root.is-open').count() === 1);
await page.keyboard.press('Escape');
await page.waitForTimeout(250);

/* Secret route /admin-syndication/ auto-opens the desk; noindex enforced. */
await page.goto(BASE + '/admin-syndication/', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(600);
check('secret route /admin-syndication/ serves the desk page', /Syndication Desk/.test(await page.title()), await page.title());
check('secret route carries robots noindex', (await page.getAttribute('meta[name="robots"]', 'content') || '').includes('noindex'));
check('secret route auto-opens the drawer', await page.locator('.synd-root.is-open').count() === 1);
await page.keyboard.press('Escape');
await page.waitForTimeout(250);

/* ======================================================================
   G. Emblem on every page + global hub structure + legal emoji ban
   ====================================================================== */
const logoPages = [
  '/jrf-srf-project-associate-jobs.html', '/phd-fellowships-climate-sustainability.html',
  '/forestry-wildlife-government-jobs.html', '/gis-remote-sensing-climate-jobs.html',
  '/esg-carbon-sustainability-jobs.html', '/hindi-environment-forestry-jobs.html',
  '/bharat-regional-green-jobs.html', '/global-climate-sustainability-opportunities.html',
  '/privacy.html', '/terms.html', '/cookies.html', '/accessibility.html', '/unsubscribe.html',
  '/dashboard.html'
];
for (const path of logoPages) {
  await page.goto(BASE + path, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.ufp-header-logo', { timeout: 10000 });
  const ok = await page.evaluate(() => {
    const img = document.querySelector('.ufp-header-logo');
    if (!img) return 'missing';
    const cs = getComputedStyle(img);
    if (!img.complete || img.naturalWidth === 0) return 'broken';
    if (cs.borderRadius !== '50%') return 'not-circle:' + cs.borderRadius;
    if (parseFloat(cs.width) < 40) return 'too-small:' + cs.width;
    return 'ok';
  });
  check('emblem renders on ' + path, ok === 'ok', ok);
}

/* Global hub page */
await page.goto(BASE + '/global-climate-sustainability-opportunities.html', { waitUntil: 'networkidle' });
const hubTitle = await page.title();
check('global hub title targets global queries', /Global Climate & Sustainability Opportunities/.test(hubTitle), hubTitle.slice(0, 90));
check('global hub canonical exact', (await page.getAttribute('link[rel="canonical"]', 'href')) === 'https://www.urbanforestpark.com/global-climate-sustainability-opportunities');
const hubRegionCards = await page.locator('.region-card').count();
check('global hub groups by region', hubRegionCards >= 6, 'cards=' + hubRegionCards);
check('global hub shows 15 seeded static job links', (await page.locator('.region-states li a[href^="/jobs/"]').count()) >= 12, 'n=' + await page.locator('.region-states li a[href^="/jobs/"]').count());
check('global hub kind links route to the registry', (await page.locator('a[href*="kind="]').count()) >= 6);
check('global hub has NO india state links', (await page.locator('a[href*="?state="]').count()) === 0);
check('global hub CTA jumps to the static global grid', (await page.locator('a[href="#global-grid"]').count()) >= 1);
const hubLd = await page.$$eval('script[type="application/ld+json"]', els => els.map(e => e.textContent).join(' '));
check('global hub JSON-LD: CollectionPage + ItemList + FAQPage + BreadcrumbList',
  hubLd.includes('"CollectionPage"') && hubLd.includes('"ItemList"') && hubLd.includes('"FAQPage"') && hubLd.includes('"BreadcrumbList"'));
check('global hub has no India registry ids in its links', await page.evaluate(() => {
  const hrefs = [...document.querySelectorAll('a[href^="/jobs/"]')].map(a => a.getAttribute('href'));
  return hrefs.every(h => !/wii-dehradun|iit-|iisc|jrf-tiger/.test(h));
}));
check('global hub lists India pathways separately', (await page.locator('a[href="/jrf-srf-project-associate-jobs"]').count()) >= 1);

/* hub pages carry the global nav link */
for (const path of ['/jrf-srf-project-associate-jobs.html', '/hindi-environment-forestry-jobs.html']) {
  await page.goto(BASE + path, { waitUntil: 'domcontentloaded' });
  check('hub links to the Global hub ' + path, (await page.locator('a[href="/global-climate-sustainability-opportunities"]').count()) >= 1);
}

/* Legal pages: English-only + emoji ban intact */
for (const path of ['/privacy.html', '/terms.html', '/cookies.html', '/accessibility.html', '/unsubscribe.html']) {
  await page.goto(BASE + path, { waitUntil: 'domcontentloaded' });
  const body = await page.evaluate(() => document.body.innerText);
  check('legal page emoji-free ' + path, !EMOJI_RE.test(body));
  check('legal topbar nav has no legacy dMRV link ' + path, await page.evaluate(() => {
    const nav = document.querySelector('.legal-nav');
    const header = document.querySelector('.legal-topbar');
    return !!nav && !!header && !/dMRV/i.test(nav.textContent) && !/NVY/i.test(header.textContent);
  }));
}
check('dashboard registers the unified sw.js', (await (await context.request.get(BASE + '/dashboard.html')).text()).includes("navigator.serviceWorker.register('/sw.js'"));

/* ======================================================================
   H. Header cleanup (no legacy dMRV nav) + floating Back-to-top control
   ====================================================================== */
await page.goto(BASE + '/', { waitUntil: 'networkidle' });
await page.waitForSelector('.job-card', { timeout: 20000 });

check('header nav carries no legacy dMRV reference', await page.evaluate(() =>
  !!document.querySelector('.site-nav') && [...document.querySelectorAll('.site-nav .nav-link')]
    .every(a => !/dMRV/i.test(a.textContent) && !/dashboard\.html/.test(a.getAttribute('href') || ''))));
check('header nav keeps the portal links (registry, archive, states)', await page.evaluate(() => {
  const links = [...document.querySelectorAll('.site-nav .nav-link')].map(a => a.getAttribute('href'));
  return links.length === 3 && links[0] === '/' && links.includes('/?view=archive') && links.includes('#filter-bar');
}));
check('header itself carries no NVY/dMRV text', await page.evaluate(() => {
  const header = document.querySelector('.site-header');
  return !!header && !/NVY|dMRV/i.test(header.textContent);
}));
check('header action order: language > night mode > saved > publish CTA', await page.evaluate(() => {
  const actions = document.querySelector('.header-actions');
  if (!actions) return false;
  const order = [...actions.children].map(el => {
    if (el.classList.contains('lang-toggle')) return 'lang';
    if (el.classList.contains('theme-toggle')) return 'theme';
    if (el.classList.contains('saved-header-btn')) return 'saved';
    if (el.classList.contains('nav-cta')) return 'cta';
    if (el.classList.contains('nav-toggle')) return 'menu';
    return 'other';
  });
  return JSON.stringify(order) === JSON.stringify(['lang', 'theme', 'saved', 'cta', 'menu']);
}));

check('back-to-top control exists on the registry', (await page.locator('.ufp-btt').count()) === 1);
check('back-to-top stays hidden at the top', await page.evaluate(() => {
  const b = document.querySelector('.ufp-btt');
  return !!b && !b.classList.contains('is-visible') && getComputedStyle(b).visibility === 'hidden';
}));
await page.evaluate(() => window.scrollTo({ top: 1500, behavior: 'instant' }));
await page.waitForTimeout(500);
check('back-to-top appears after scrolling down', await page.evaluate(() => {
  const b = document.querySelector('.ufp-btt');
  if (!b || !b.classList.contains('is-visible')) return false;
  const cs = getComputedStyle(b);
  return cs.opacity === '1' && cs.visibility === 'visible';
}));
check('back-to-top sits in the lower-right action zone with elevation', await page.evaluate(() => {
  const b = document.querySelector('.ufp-btt');
  if (!b) return false;
  const r = b.getBoundingClientRect();
  const cs = getComputedStyle(b);
  return r.width >= 42 && r.height >= 42
    && r.right > window.innerWidth * 0.55 && r.bottom > window.innerHeight * 0.5
    && cs.boxShadow !== 'none' && parseFloat(cs.borderTopWidth) >= 1;
}));
check('back-to-top clears the widget column and cookie bar', await page.evaluate(() => {
  const b = document.querySelector('.ufp-btt');
  if (!b) return false;
  const rb = b.getBoundingClientRect();
  const hits = [document.getElementById('ufp-app-widget'), document.getElementById('ufp-app-pill'), document.getElementById('ufp-cookie-consent')];
  return hits.every(el => {
    if (!el || el.hasAttribute('hidden')) return true;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return true;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return true;
    return rb.right <= r.left || rb.left >= r.right || rb.bottom <= r.top || rb.top >= r.bottom;
  });
}));
await page.evaluate(() => document.getElementById('theme-toggle').click());
await page.waitForTimeout(350);
check('back-to-top follows night mode', await page.evaluate(() => {
  const b = document.querySelector('.ufp-btt');
  return !!b && getComputedStyle(b).backgroundColor === 'rgb(16, 26, 22)';
}));
await page.evaluate(() => document.getElementById('theme-toggle').click());
await page.waitForTimeout(350);
check('back-to-top returns to light styling', await page.evaluate(() => {
  const b = document.querySelector('.ufp-btt');
  return !!b && getComputedStyle(b).backgroundColor !== 'rgb(16, 26, 22)';
}));
await page.locator('.ufp-btt').click();
let bttTop = false;
for (let i = 0; i < 20; i++) {
  await page.waitForTimeout(150);
  if (await page.evaluate(() => (window.pageYOffset || 0) < 6)) { bttTop = true; break; }
}
check('clicking back-to-top smooth-scrolls to the top', bttTop);
await page.waitForTimeout(350);
check('back-to-top hides again at the top', await page.evaluate(() => {
  const b = document.querySelector('.ufp-btt');
  return !!b && !b.classList.contains('is-visible');
}));

/* present on every surface */
for (const path of ['/jrf-srf-project-associate-jobs.html', '/global-climate-sustainability-opportunities.html', '/privacy.html', '/dashboard.html', '/explore-dashboard.html']) {
  await page.goto(BASE + path, { waitUntil: 'domcontentloaded' });
  const n = await page.locator('.ufp-btt').count();
  check('back-to-top present on ' + path, n === 1, 'n=' + n);
}
await page.goto(BASE + '/global-climate-sustainability-opportunities.html', { waitUntil: 'domcontentloaded' });
await page.evaluate(() => window.scrollTo({ top: 1500, behavior: 'instant' }));
await page.waitForTimeout(450);
check('back-to-top appears on a hub page after scrolling', await page.evaluate(() => {
  const b = document.querySelector('.ufp-btt');
  return !!b && b.classList.contains('is-visible');
}));

/* ======================================================================
   H. Institutional refinement: soft shading, editorial serif, tabular
      readouts, micro-badges, arrow micro-interactions, email sweep
   ====================================================================== */
await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(500);
const tokens = await page.evaluate(() => {
  const cs = getComputedStyle(document.documentElement);
  return {
    bg: cs.getPropertyValue('--bg').trim(),
    bg2: cs.getPropertyValue('--bg-2').trim(),
    serif: cs.getPropertyValue('--font-serif').trim()
  };
});
check('light canvas token is the cool slate #F8FAFC', tokens.bg.toUpperCase() === '#F8FAFC', tokens.bg);
check('secondary canvas token is #F1F5F9', tokens.bg2.toUpperCase() === '#F1F5F9', tokens.bg2);
check('institutional serif stack registered', /Spectral/.test(tokens.serif), tokens.serif.slice(0, 70));
check('hero heading uses the editorial serif stack', await page.evaluate(() => /Spectral/.test(getComputedStyle(document.querySelector('#hero-heading')).fontFamily)));
check('section titles render in the serif stack', await page.evaluate(() => /Spectral/.test(getComputedStyle(document.querySelector('#feed-title')).fontFamily)));
check('telemetry readouts are tabular mono figures', await page.evaluate(() => {
  const el = document.querySelector('.tel-value');
  if (!el) return false;
  const cs = getComputedStyle(el);
  return /IBM Plex Mono/.test(cs.fontFamily) && cs.fontVariantNumeric.includes('tabular-nums');
}));
check('four telemetry micro-icons render', await page.locator('.tel-card .tel-icon').count() === 4);
check('sector pills carry the diamond micro-dot', await page.evaluate(() => {
  const pill = document.querySelector('.cat-pill');
  if (!pill) return false;
  const cs = getComputedStyle(pill, '::before');
  return cs.content !== 'none' && parseFloat(cs.width) >= 4;
}));
check('card CTA arrow is animated on hover', await page.evaluate(() => {
  const svg = document.querySelector('.jc-view svg');
  if (!svg) return false;
  return parseFloat(getComputedStyle(svg).transitionDuration) > 0;
}));
check('footer links carry the floating arrow micro-interaction', await page.evaluate(() => {
  const a = document.querySelector('.footer-col a');
  if (!a) return false;
  const cs = getComputedStyle(a, '::after');
  return cs.content !== 'none' && cs.content !== '' && cs.content !== 'normal';
}));
check('experience badges carry an SVG shield micro-icon mask', await page.evaluate(() => {
  const b = document.querySelector('.badge-exp');
  if (!b) return false;
  const cs = getComputedStyle(b, '::before');
  return (cs.maskImage || cs.webkitMaskImage || 'none') !== 'none';
}));
check('no legacy personal email anywhere in the homepage DOM', await page.evaluate(() => !document.documentElement.innerHTML.includes('arkraj.biswas6')));
check('institutional address present in the publish-modal note', await page.evaluate(() => {
  const el = document.querySelector('.modal-mailto-note');
  return !!el && el.innerHTML.includes('urbanforestpark@gmail.com');
}));

/* Night-mode canvas token + meta theme-color. */
await page.click('#theme-toggle');
await page.waitForTimeout(400);
check('night canvas token is the deep ink #0B0F17', await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--bg').trim().toUpperCase() === '#0B0F17'));
check('theme-color meta follows night mode', (await page.getAttribute('#meta-theme-color', 'content')) === '#0B0F17');
await page.click('#theme-toggle');
await page.waitForTimeout(350);

/* robots.txt hides the secret route. */
const robotsTxt = fs.readFileSync(REPO + '/robots.txt', 'utf-8');
check('robots.txt disallows the secret syndication route', /Disallow: \/admin-syndication/.test(robotsTxt));

/* Kind badges on the registry feed (global mode) carry the medal mask. */
await page.goto(BASE + '/?region=global', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(900);
check('global feed renders kind badges', await page.locator('.badge-kind').count() >= 1, 'n=' + await page.locator('.badge-kind').count());
check('kind badges carry an SVG medal micro-icon mask', await page.evaluate(() => {
  const b = document.querySelector('.badge-kind');
  if (!b) return false;
  const cs = getComputedStyle(b, '::before');
  return (cs.maskImage || cs.webkitMaskImage || 'none') !== 'none';
}));
await page.goto(BASE + '/global-climate-sustainability-opportunities.html', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(300);
check('hub footer carries the Syndication Desk link', await page.locator('footer [data-syndication-open]').count() >= 1);
check('global hub headings render in the serif stack', await page.evaluate(() => /Spectral/.test(getComputedStyle(document.querySelector('.hub-hero h1')).fontFamily)));

/* Drawer script + institutional email on hub, legal and dashboard surfaces. */
for (const path of ['/esg-carbon-sustainability-jobs.html', '/privacy.html', '/dashboard.html']) {
  await page.goto(BASE + path, { waitUntil: 'domcontentloaded' });
  check('syndication drawer loaded on ' + path, await page.locator('script[src="/js/syndication-drawer.js"]').count() === 1);
}
await page.goto(BASE + '/privacy.html', { waitUntil: 'domcontentloaded' });
check('legal pages carry the institutional email', (await page.locator('body').innerText()).includes('urbanforestpark@gmail.com'));
check('legal pages carry no legacy personal email', !(await page.locator('body').innerText()).includes('arkraj.biswas6'));
check('legal footer carries the discreet Syndication Desk control', await page.locator('.legal-footer [data-syndication-open]').count() >= 1);

/* ======================================================================
   J. Phase upgrades: right-side hero instant search (active + archived),
      sponsor-placeholder purge, newsletter welcome flow
   ====================================================================== */
await page.goto(BASE + '/', { waitUntil: 'networkidle' });
await page.waitForSelector('.job-card', { timeout: 20000 });

/* --- J1. Hero search mounts on the right of the masthead row --- */
const heroSearchLayout = await page.evaluate(() => {
  const row = document.querySelector('.hero-head-row');
  const heading = document.getElementById('hero-heading');
  const search = document.getElementById('hero-search');
  const input = document.getElementById('hero-search-input');
  const btn = document.getElementById('hero-search-btn');
  if (!row || !heading || !search || !input || !btn) return null;
  const rr = row.getBoundingClientRect();
  const hr = heading.getBoundingClientRect();
  const sr = search.getBoundingClientRect();
  const br = btn.getBoundingClientRect();
  return {
    rowDisplay: getComputedStyle(row).display,
    sameRow: sr.left >= hr.right - 2 && Math.abs(sr.top - hr.top) < 140,
    rightAligned: sr.right <= rr.right + 1,
    btnVisible: br.width >= 40 && br.height >= 32,
    placeholder: input.getAttribute('placeholder') || ''
  };
});
check('J: hero head row places the instant search to the right of the H1',
  !!heroSearchLayout && heroSearchLayout.rowDisplay === 'flex' && heroSearchLayout.sameRow && heroSearchLayout.rightAligned,
  JSON.stringify(heroSearchLayout || {}).slice(0, 220));
check('J: hero search button renders at interactive size', !!heroSearchLayout && heroSearchLayout.btnVisible);
check('J: hero search input advertises title / skill / organisation search',
  !!heroSearchLayout && /title/i.test(heroSearchLayout.placeholder) && /skill/i.test(heroSearchLayout.placeholder) && /organisation/i.test(heroSearchLayout.placeholder),
  heroSearchLayout ? heroSearchLayout.placeholder : '');

/* --- J2. Typing pops the dropdown with Direct + Related groups --- */
await page.fill('#hero-search-input', 'gis');
await page.waitForTimeout(320);
const heroPanel = await page.evaluate(() => {
  const panel = document.getElementById('hero-search-panel');
  const root = document.getElementById('hero-search');
  const rows = panel ? [...panel.querySelectorAll('.hs-row')] : [];
  return {
    hidden: panel ? panel.hidden : true,
    rootOpen: !!root && root.classList.contains('hs-open'),
    ariaExpanded: (document.getElementById('hero-search-input') || {}).getAttribute
      ? document.getElementById('hero-search-input').getAttribute('aria-expanded') : null,
    rows: rows.length,
    text: panel ? panel.innerText : '',
    activeBadges: rows.filter(r => r.querySelector('.hs-badge.is-active')).length,
    archivedBadges: rows.filter(r => r.querySelector('.hs-badge.is-archived')).length
  };
});
check('J: typing 2+ characters opens the anchored dropdown panel',
  !heroPanel.hidden && heroPanel.rootOpen && heroPanel.rows >= 1, JSON.stringify({ hidden: heroPanel.hidden, rows: heroPanel.rows }));
check('J: dropdown announces the expanded combobox state', heroPanel.ariaExpanded === 'true');
check('J: dropdown renders the Direct Matches group', /direct matches/i.test(heroPanel.text));
check('J: dropdown renders the Related & Similar Positions group', /related & similar positions in this field/i.test(heroPanel.text));
check('J: every dropdown row carries an ACTIVE or ARCHIVED status badge',
  heroPanel.activeBadges + heroPanel.archivedBadges >= heroPanel.rows && heroPanel.rows >= 1,
  `active=${heroPanel.activeBadges} archived=${heroPanel.archivedBadges} rows=${heroPanel.rows}`);

/* --- J3. Live sweep: archive.json + jobs.json + global_jobs.json --- */
const blobOf = j => [j.clean_title, j.title_hi, j.organization, j.state, j.city, j.region, j.country,
  j.category, j.position_type, j.opportunity_kind, j.qualification_summary, j.experience_level,
  (j.must_have_skills || []).join(' ')].join(' ').toLowerCase();
const allTagged = [
  ...india.map(j => ({ j, archived: false })),
  ...globalJobs.map(j => ({ j, archived: false })),
  ...indiaArchive.map(j => ({ j, archived: true })),
  ...globalArchive.map(j => ({ j, archived: true }))
];
function tokenPlan(records) {
  for (let minHits = 1; minHits <= 3; minHits += 1) {
    for (const rec of records) {
      const words = String(rec.j.clean_title || '').toLowerCase().split(/[^a-z0-9+#.]+/).filter(w => w.length >= 6);
      for (const w of words) {
        const hits = allTagged.filter(r => blobOf(r.j).includes(w));
        if (hits.length === minHits && hits.some(h => h.j.id === rec.j.id)) {
          return { token: w, exact: hits.length === 1, ids: hits.map(h => h.j.id) };
        }
      }
    }
  }
  return null;
}
async function heroRowsFor(token) {
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.job-card', { timeout: 20000 });
  await page.fill('#hero-search-input', token);
  await page.waitForTimeout(350);
  return page.evaluate(() => {
    const panel = document.getElementById('hero-search-panel');
    const rows = panel ? [...panel.querySelectorAll('.hs-row')] : [];
    return {
      open: !!panel && !panel.hidden,
      rows: rows.map(r => ({
        id: r.getAttribute('data-job-id'),
        active: !!r.querySelector('.hs-badge.is-active'),
        archived: !!r.querySelector('.hs-badge.is-archived')
      }))
    };
  });
}
const archivePlan = tokenPlan(indiaArchive.map(j => ({ j, archived: true })));
const activePlan = tokenPlan(india.map(j => ({ j, archived: false })));
const globalPlan = tokenPlan(globalJobs.map(j => ({ j, archived: false })));
check('J: a unique archived title token exists for the live search sweep', !!archivePlan, archivePlan ? archivePlan.token : 'none');
check('J: a unique active title token exists for the live search sweep', !!activePlan, activePlan ? activePlan.token : 'none');
check('J: a unique global title token exists for the live search sweep', !!globalPlan, globalPlan ? globalPlan.token : 'none');
if (archivePlan) {
  const stateA = await heroRowsFor(archivePlan.token);
  const hitA = stateA.rows.filter(r => r.id && archivePlan.ids.includes(r.id));
  check('J: hero search reaches archive.json ("' + archivePlan.token + '")', stateA.open && hitA.length >= 1, JSON.stringify(stateA).slice(0, 200));
  check('J: archived search hit is badged ARCHIVED', hitA.some(r => r.archived), JSON.stringify(hitA).slice(0, 160));
}
if (activePlan) {
  const stateB = await heroRowsFor(activePlan.token);
  const hitB = stateB.rows.filter(r => r.id && activePlan.ids.includes(r.id));
  check('J: hero search reaches jobs.json ("' + activePlan.token + '")', stateB.open && hitB.length >= 1, JSON.stringify(stateB).slice(0, 200));
  check('J: active search hit is badged ACTIVE', hitB.some(r => r.active), JSON.stringify(hitB).slice(0, 160));
}
if (globalPlan) {
  const stateC = await heroRowsFor(globalPlan.token);
  const hitC = stateC.rows.filter(r => r.id && globalPlan.ids.includes(r.id));
  check('J: hero search reaches global_jobs.json ("' + globalPlan.token + '")', stateC.open && hitC.length >= 1, JSON.stringify(stateC).slice(0, 200));
}

/* --- J4. Enter mirrors the query into the main feed filter --- */
if (activePlan) {
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.job-card', { timeout: 20000 });
  await page.fill('#hero-search-input', activePlan.token);
  await page.waitForTimeout(280);
  await page.press('#hero-search-input', 'Enter');
  await page.waitForTimeout(700);
  const feedState = await page.evaluate(() => ({
    mainSearch: document.getElementById('jobs-search').value,
    cards: [...document.querySelectorAll('.job-card')].map(c => c.getAttribute('data-id')),
    panelHidden: document.getElementById('hero-search-panel').hidden
  }));
  check('J: Enter mirrors the query into the main search box',
    feedState.mainSearch === activePlan.token, 'main=' + feedState.mainSearch);
  check('J: Enter filters the feed down to the matching job',
    feedState.cards.length >= 1 && feedState.cards.includes(activePlan.ids[0]),
    'cards=' + feedState.cards.slice(0, 4).join(','));
  check('J: dropdown collapses after submitting', feedState.panelHidden);
}

/* --- J5. Clicking an archived recommendation opens its dossier --- */
if (archivePlan) {
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.job-card', { timeout: 20000 });
  await page.fill('#hero-search-input', archivePlan.token);
  await page.waitForTimeout(320);
  await page.click('#hero-search-panel .hs-row[data-job-id="' + archivePlan.ids[0] + '"]');
  await page.waitForTimeout(600);
  const dossierState = await page.evaluate(() => ({
    jobParam: new URLSearchParams(window.location.search).get('job'),
    pathname: window.location.pathname,
    detailCard: !!document.querySelector('#job-detail .detail-card'),
    canonical: (document.querySelector('link[rel="canonical"]') || {}).href || ''
  }));
  check('J: clicking an archived dropdown row opens its static job dossier',
    dossierState.detailCard && dossierState.pathname === '/jobs/' + archivePlan.ids[0],
    JSON.stringify({ path: dossierState.pathname, expected: archivePlan.ids[0], detail: dossierState.detailCard }));
  check('J: archived dossier keeps the self-referencing static canonical',
    dossierState.canonical === 'https://www.urbanforestpark.com/jobs/' + archivePlan.ids[0],
    dossierState.canonical);
}

/* --- J6. Zero sponsor / leaderboard placeholders anywhere --- */
await page.goto(BASE + '/', { waitUntil: 'networkidle' });
await page.waitForSelector('.job-card', { timeout: 20000 });
const placeholderRe = /sponsor this space|leaderboard space|institutional partner space|in-feed partner slot/i;
const feedPlaceholders = await page.evaluate(() => ({
  text: document.body.innerText,
  containers: document.querySelectorAll('.ad-container, .ad-label, .ad-cta').length
}));
check('J: feed carries no sponsor/leaderboard placeholder copy', !placeholderRe.test(feedPlaceholders.text),
  (feedPlaceholders.text.match(placeholderRe) || [''])[0]);
check('J: feed carries zero ad placeholder containers', feedPlaceholders.containers === 0, 'n=' + feedPlaceholders.containers);
await page.evaluate(() => { document.querySelector('.job-card').click(); });
await page.waitForTimeout(500);
const detailPlaceholders = await page.evaluate(() => ({
  text: /sponsor this space|leaderboard space|institutional partner space|in-feed partner slot/i.test(document.body.innerText),
  containers: document.querySelectorAll('.ad-container, .ad-label, .ad-cta').length
}));
check('J: dossier view carries zero sponsor placeholders', !detailPlaceholders.text && detailPlaceholders.containers === 0, JSON.stringify(detailPlaceholders));
const repoRoot = 'C:/Users/arkra/NVY DMRV/nvy-dmrv-dashboard';
const htmlFiles = fs.readdirSync(REPO).filter(f => f.endsWith('.html'));
const htmlOffenders = htmlFiles.filter(f => /sponsor this space|leaderboard space|institutional partner space|in-feed partner slot/i.test(fs.readFileSync(REPO + '/' + f, 'utf-8')));
check('J: no placeholder ad copy in any of the ' + htmlFiles.length + ' published HTML pages', htmlOffenders.length === 0, htmlOffenders.join(','));
const jobsSource = fs.readFileSync(REPO + '/js/jobs.js', 'utf-8');
check('J: jobs.js renders no ad placeholders (no adInFeed/adDetail builders)',
  !/adInFeedHtml|adDetailHtml|ad-container|Sponsor this space|Leaderboard space/i.test(jobsSource));

/* --- J7. Newsletter submit triggers the welcome flow --- */
const mailerSource = fs.readFileSync(repoRoot + '/scripts/send_newsletter.py', 'utf-8');
check('J: mailer defines the welcome template builder (subscriber, frequency, sector)',
  /def build_welcome_email_html\(/.test(mailerSource) && /subscriber_email/.test(mailerSource));
check('J: mailer exposes --welcome and --test-welcome modes',
  mailerSource.includes('"--welcome"') && mailerSource.includes('"--test-welcome"'));
check('J: mailer auto-welcomes pending subscribers on every run',
  /def process_welcome_backlog\(/.test(mailerSource) && /process_welcome_backlog\(channel, config, jobs/.test(mailerSource));
check('J: welcome subject line matches the institutional template',
  mailerSource.includes('Welcome to Urban Forest Park \\u2014 India & Global Environmental,'));
check('J: welcome email carries the top-3 featured active opportunities',
  /def featured_jobs\(/.test(mailerSource) && /TOP 3 FEATURED ACTIVE OPPORTUNITIES/.test(mailerSource));
check('J: welcome email links the app install with the source campaign tag',
  mailerSource.includes('?source=welcome_email'));
const subscribeSource = fs.readFileSync(repoRoot + '/functions/api/subscribe.js', 'utf-8');
check('J: /api/subscribe triggers the instant welcome email',
  subscribeSource.includes('welcome_email') && subscribeSource.includes('GITHUB_PAT') && subscribeSource.includes('waitUntil'));
check('J: /api/subscribe records welcome_sent:false for new subscribers',
  /welcome_sent: false/.test(subscribeSource));
const workflowSource = fs.readFileSync(repoRoot + '/.github/workflows/newsletter_dispatch.yml', 'utf-8');
check('J: dispatch workflow listens for the welcome_email repository event',
  /repository_dispatch/.test(workflowSource) && /types: \[welcome_email\]/.test(workflowSource.split('\n').join('\n')));
check('J: dispatch workflow supports on-demand welcome + test inputs',
  /subscriber_email/.test(workflowSource) && /test_welcome/.test(workflowSource) && /--welcome/.test(workflowSource) && /--test-welcome/.test(workflowSource));

let dispatchPayload = null;
await page.route('**/api/subscribe', async (route) => {
  try { dispatchPayload = route.request().postData(); } catch (e) { /* ignore */ }
  await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, persisted: true, storage: 'kv' }) });
});
await page.fill('#dispatch-email', 'qa-subscriber@example.com');
await page.selectOption('#dispatch-sector', 'academic');
await page.check('input[name="frequency"][value="weekly"]');
await page.click('.dispatch-form button[type="submit"]');
await page.waitForTimeout(1000);
const dispatchState = await page.evaluate(() => {
  const done = document.querySelector('.dispatch-done');
  return {
    doneTitle: done ? done.innerText.replace(/\s+/g, ' ').slice(0, 120) : '',
    hasForm: !!document.querySelector('.dispatch-form')
  };
});
let payloadParsed = null;
try { payloadParsed = dispatchPayload ? JSON.parse(dispatchPayload) : null; } catch (e) { payloadParsed = null; }
check('J: newsletter form POSTs the exact subscription payload',
  !!payloadParsed && payloadParsed.email === 'qa-subscriber@example.com' && payloadParsed.frequency === 'weekly' && payloadParsed.sector === 'academic',
  String(dispatchPayload).slice(0, 160));
check('J: newsletter form confirms the subscription cleanly (welcome flow acknowledged)',
  /Subscription recorded/.test(dispatchState.doneTitle), dispatchState.doneTitle);
await page.unroute('**/api/subscribe');

/* ======================================================================
   I. LAYOUT / NAVIGATION / MOBILE REGRESSION SUITE
   ====================================================================== */

/* --- Check A: the FAQ is strictly below the dossier in detail mode --- */
await page.goto(BASE + '/?job=' + encodeURIComponent(india[0].id), { waitUntil: 'domcontentloaded' });
await page.waitForSelector('#job-detail .detail-card', { timeout: 20000 });
const detailOrder = await page.evaluate(() => {
  const detail = document.getElementById('job-detail').getBoundingClientRect();
  const dispatch = document.getElementById('dispatch').getBoundingClientRect();
  const faq = document.querySelector('.exec-faq').getBoundingClientRect();
  return {
    scrollY: window.scrollY,
    detailTop: detail.top, detailBottom: detail.bottom,
    dispatchTop: dispatch.top, faqTop: faq.top
  };
});
check('A: dossier opens at the top of the screen', detailOrder.scrollY < 100, 'scrollY=' + detailOrder.scrollY);
check('A: newsletter dispatch follows the dossier', detailOrder.dispatchTop >= detailOrder.detailBottom - 0.5,
  `dispatch=${Math.round(detailOrder.dispatchTop)} detailBottom=${Math.round(detailOrder.detailBottom)}`);
check('A: FAQ top is strictly below the dossier bottom', detailOrder.faqTop > detailOrder.detailBottom,
  `faq=${Math.round(detailOrder.faqTop)} detailBottom=${Math.round(detailOrder.detailBottom)}`);

/* --- Check B: exact feed scroll memory on open + back --- */
await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
await page.waitForSelector('.job-card', { timeout: 20000 });
await page.evaluate(() => {
  try {
    sessionStorage.removeItem('ufp_saved_scroll_y');
    sessionStorage.removeItem('ufp_last_clicked_job_id');
    sessionStorage.removeItem('ufp_returning_from_job');
  } catch (e) {}
  window.scrollTo({ top: 850, left: 0, behavior: 'instant' });
});
await page.waitForTimeout(180);
check('B: feed is positioned at 850px before opening a job', await page.evaluate(() => Math.abs(window.scrollY - 850) <= 2),
  'scrollY=' + await page.evaluate(() => window.scrollY));
await page.evaluate(() => { document.querySelector('.job-card').click(); });
await page.waitForTimeout(450);
const detailScrollY = await page.evaluate(() => window.scrollY);
check('B: opening a dossier resets the viewport to the top', detailScrollY < 100, 'scrollY=' + detailScrollY);
await page.evaluate(() => { const b = document.querySelector('.back-link[data-action="back"]'); if (b) b.click(); });
await page.waitForTimeout(500);
const restoredY = await page.evaluate(() => window.scrollY);
check('B: Back/History return restores the exact feed position', Math.abs(restoredY - 850) <= 15, 'scrollY=' + restoredY);

/* --- Check C: 390x844 mobile audit --- */
const mobileContext = await browser.newContext({
  viewport: { width: 390, height: 844 },
  isMobile: true,
  hasTouch: true,
  deviceScaleFactor: 2
});
const mobilePage = await mobileContext.newPage();
attach(mobilePage, 'mobile');
await mobilePage.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
await mobilePage.waitForSelector('.job-card', { timeout: 20000 });
await mobilePage.waitForSelector('#ufp-app-pill:not([hidden])', { timeout: 12000 });
await mobilePage.waitForTimeout(250);

const mobileLayout = await mobilePage.evaluate(() => {
  const grid = document.querySelector('.telemetry-grid');
  const cols = getComputedStyle(grid).gridTemplateColumns.split(/\s+/).filter(Boolean).length;
  const gr = grid.getBoundingClientRect();
  const pill = document.getElementById('ufp-app-pill');
  const pr = pill.getBoundingClientRect();
  const heroActions = document.querySelector('.header-actions');
  const logo = document.querySelector('.ufp-header-logo');
  const lr = logo.getBoundingClientRect();
  return {
    docWidth: document.documentElement.scrollWidth,
    bodyWidth: document.body.scrollWidth,
    cols,
    gridHeight: gr.height,
    pillHeight: pr.height,
    widgetHidden: document.getElementById('ufp-app-widget').hidden,
    actionsTop: heroActions.getBoundingClientRect().top,
    brandBottom: document.querySelector('.brand').getBoundingClientRect().bottom,
    logoWidth: lr.width,
    filterWrap: getComputedStyle(document.querySelector('.pill-row')).flexWrap,
    filterOverflow: getComputedStyle(document.querySelector('.pill-row')).overflowX,
    cardFigure: document.querySelector('.job-figure--card').getBoundingClientRect().width
  };
});
check('C: zero horizontal overflow at 390px', mobileLayout.docWidth <= 390 && mobileLayout.bodyWidth <= 390,
  `doc=${mobileLayout.docWidth} body=${mobileLayout.bodyWidth}`);
check('C: telemetry is a tight 2x2 grid under 130px', mobileLayout.cols === 2 && mobileLayout.gridHeight < 130,
  `cols=${mobileLayout.cols} h=${Math.round(mobileLayout.gridHeight)}`);
check('C: PWA widget starts collapsed as a 34px mini-pill', mobileLayout.widgetHidden && mobileLayout.pillHeight <= 36,
  `hidden=${mobileLayout.widgetHidden} h=${mobileLayout.pillHeight}`);
check('C: header controls form a compact second row', mobileLayout.actionsTop >= mobileLayout.brandBottom - 2,
  `actions=${Math.round(mobileLayout.actionsTop)} brandBottom=${Math.round(mobileLayout.brandBottom)}`);
check('C: mobile brand emblem is 36px', Math.abs(mobileLayout.logoWidth - 36) <= 1, 'w=' + mobileLayout.logoWidth);
check('C: filter pills are a single swipeable row', mobileLayout.filterWrap === 'nowrap' && mobileLayout.filterOverflow === 'auto',
  `${mobileLayout.filterWrap}/${mobileLayout.filterOverflow}`);
check('C: mobile card figure is 46px', Math.abs(mobileLayout.cardFigure - 46) <= 1, 'w=' + mobileLayout.cardFigure);

/* Dismiss consent, then expand the widget and measure its real card size. */
await mobilePage.locator('[data-ufp-cc-choice="essential"]').click();
await mobilePage.waitForTimeout(450);
await mobilePage.locator('#ufp-app-pill').click();
await mobilePage.waitForTimeout(350);
const widgetBox = await mobilePage.evaluate(() => {
  const w = document.getElementById('ufp-app-widget');
  const r = w.getBoundingClientRect();
  return { hidden: w.hidden, width: r.width, height: r.height, bottom: window.innerHeight - r.bottom };
});
check('C: expanded app card stays under 22% of the mobile screen',
  !widgetBox.hidden && widgetBox.height <= 844 * 0.22 && widgetBox.width <= 390 - 24,
  `h=${Math.round(widgetBox.height)} w=${Math.round(widgetBox.width)}`);

/* Phone dossier: stacked full-width portal buttons and 64px figure. */
await mobilePage.evaluate(() => { document.querySelector('.job-card').click(); });
await mobilePage.waitForTimeout(450);
const mobileDetail = await mobilePage.evaluate(() => {
  const head = document.querySelector('.detail-head').getBoundingClientRect();
  const fig = document.querySelector('.job-figure--detail').getBoundingClientRect();
  const btns = [...document.querySelectorAll('.verify-actions .verify-btn')].map(b => b.getBoundingClientRect());
  return {
    scrollY: window.scrollY,
    headHeight: head.height,
    figWidth: fig.width,
    btnWidths: btns.map(r => Math.round(r.width)),
    btnHeights: btns.map(r => Math.round(r.height)),
    actionsWidth: Math.round(document.querySelector('.verify-actions').getBoundingClientRect().width),
    containerWidth: document.querySelector('.detail-card').getBoundingClientRect().width
  };
});
check('C: mobile dossier opens at the top', mobileDetail.scrollY < 100, 'scrollY=' + mobileDetail.scrollY);
check('C: mobile dossier figure is 64px', Math.abs(mobileDetail.figWidth - 64) <= 1, 'w=' + mobileDetail.figWidth);
check('C: portal buttons are full-width and 42px+ tall',
  mobileDetail.btnWidths.length >= 2 &&
  mobileDetail.btnWidths.every(w => Math.abs(w - mobileDetail.actionsWidth) <= 2) &&
  mobileDetail.btnHeights.every(h => h >= 42),
  `w=${mobileDetail.btnWidths.join(',')} h=${mobileDetail.btnHeights.join(',')} actions=${mobileDetail.actionsWidth}`);

check('C: mobile sticky dossier action bar is visible', await mobilePage.locator('#mobile-action-bar').isVisible());
check('C: mobile action bar has back, save and apply controls',
  await mobilePage.locator('#mobile-action-bar [data-action="back"]').count() === 1 &&
  await mobilePage.locator('#mobile-action-bar [data-action="save-current"]').count() === 1 &&
  await mobilePage.locator('#mobile-action-bar [data-mobile-apply]').count() === 1);

await mobilePage.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
await mobilePage.waitForSelector('.job-card', { timeout: 20000 });
await mobilePage.waitForTimeout(250);
check('C: quick-filter strip renders 7 researcher filters + Saved',
  await mobilePage.locator('#quick-filters [data-quick]').count() === 7 &&
  await mobilePage.locator('#saved-filter-btn').count() === 1,
  'n=' + await mobilePage.locator('#quick-filters [data-quick]').count());
check('C: every job card has save + share + WhatsApp actions',
  await mobilePage.locator('.job-card [data-save-id]').count() >= 1 &&
  await mobilePage.locator('.job-card [data-share-id]').count() >= 1 &&
  await mobilePage.locator('.job-card .jc-wa').count() >= 1);
check('C: skeleton shimmer markup is replaced after load',
  await mobilePage.locator('.skeleton-card').count() === 0);

const firstMobileId = await mobilePage.locator('.job-card').first().getAttribute('data-id');
await mobilePage.locator('.job-card').first().locator('[data-save-id]').click();
await mobilePage.waitForTimeout(120);
const savedAfterTap = await mobilePage.evaluate(() => JSON.parse(localStorage.getItem('ufp_saved_jobs') || '[]'));
check('C: ★ Save persists the job id in ufp_saved_jobs',
  savedAfterTap.includes(firstMobileId), savedAfterTap.join(','));
await mobilePage.locator('#saved-header-btn').click();
await mobilePage.waitForTimeout(180);
check('C: Saved drawer opens with the shortlisted job',
  await mobilePage.locator('#saved-drawer.open').count() === 1 &&
  await mobilePage.locator('#saved-drawer [data-saved-open]').count() >= 1);
await mobilePage.locator('#saved-close').click();

await mobilePage.locator('#quick-filters [data-quick="academic"]').click();
await mobilePage.waitForTimeout(220);
const academicOnly = await mobilePage.locator('.job-card').count();
check('C: JRF/SRF quick filter activates', await mobilePage.locator('#quick-filters [data-quick="academic"]').getAttribute('aria-pressed') === 'true',
  'cards=' + academicOnly);
await mobilePage.locator('#quick-filters [data-quick="academic"]').click();

const feedOk = await fetch(BASE + '/feed.xml').then(async r => ({ status: r.status, text: await r.text() }));
const jrfFeedOk = await fetch(BASE + '/jrf-feed.xml').then(async r => ({ status: r.status, text: await r.text() }));
check('D: /feed.xml returns HTTP 200 valid RSS', feedOk.status === 200 && /^<\?xml/.test(feedOk.text.trim()) && /<rss[\s>]/.test(feedOk.text) && /<item>/.test(feedOk.text), 'status=' + feedOk.status);
check('D: /jrf-feed.xml returns HTTP 200 valid RSS', jrfFeedOk.status === 200 && /^<\?xml/.test(jrfFeedOk.text.trim()) && /<rss[\s>]/.test(jrfFeedOk.text) && /<item>/.test(jrfFeedOk.text), 'status=' + jrfFeedOk.status);

await mobileContext.close();

/* Tablet (iPad / Android) */
const tabletContext = await browser.newContext({ viewport: { width: 820, height: 1180 } });
const tabletPage = await tabletContext.newPage();
attach(tabletPage, 'tablet');
await tabletPage.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
await tabletPage.waitForSelector('.job-card', { timeout: 20000 });
await tabletPage.waitForTimeout(250);
const tabletLayout = await tabletPage.evaluate(() => {
  const card = document.querySelector('.job-card');
  const quick = document.querySelector('#quick-filters [data-quick]');
  const grid = document.querySelector('.telemetry-grid');
  return {
    docWidth: document.documentElement.scrollWidth,
    telemetryCols: getComputedStyle(grid).gridTemplateColumns.split(/\s+/).filter(Boolean).length,
    cardPadding: parseFloat(getComputedStyle(card).paddingTop),
    quickHeight: quick.getBoundingClientRect().height,
    headerOverflow: document.querySelector('.header-inner').scrollWidth > document.querySelector('.header-inner').clientWidth + 2,
    savedVisible: !!document.getElementById('saved-header-btn')
  };
});
check('E: zero horizontal overflow at 820px', tabletLayout.docWidth <= 820, 'doc=' + tabletLayout.docWidth);
check('E: tablet telemetry is a balanced 2x2 grid', tabletLayout.telemetryCols === 2, 'cols=' + tabletLayout.telemetryCols);
check('E: tablet cards use 18px padding', Math.abs(tabletLayout.cardPadding - 18) <= 1, 'padding=' + tabletLayout.cardPadding);
check('E: tablet quick filters meet 44px touch target', tabletLayout.quickHeight >= 44, 'h=' + tabletLayout.quickHeight);
check('E: tablet header does not wrap/overflow', !tabletLayout.headerOverflow);
check('E: tablet header exposes the Saved shortlist', tabletLayout.savedVisible);
await tabletContext.close();

/* Laptop / desktop */
const laptopContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const laptopPage = await laptopContext.newPage();
attach(laptopPage, 'laptop');
await laptopPage.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
await laptopPage.waitForSelector('.job-card', { timeout: 20000 });
await laptopPage.waitForTimeout(250);
check('F: zero horizontal overflow at 1440px',
  await laptopPage.evaluate(() => document.documentElement.scrollWidth <= 1440));
check('F: search input shows the Press / hint',
  (await laptopPage.locator('.search-kbd').innerText()).toLowerCase().includes('press /'));
await laptopPage.evaluate(() => document.body.focus());
await laptopPage.keyboard.press('/');
await laptopPage.waitForTimeout(120);
check('F: / keyboard shortcut focuses the registry search',
  await laptopPage.evaluate(() => document.activeElement && document.activeElement.id === 'jobs-search'));
check('F: every card exposes Share and Saved actions',
  await laptopPage.locator('.job-card [data-share-id]').count() >= 1 &&
  await laptopPage.locator('.job-card [data-save-id]').count() >= 1);
await laptopPage.evaluate(() => window.scrollTo(0, 520));
await laptopPage.waitForTimeout(120);
await laptopPage.evaluate(() => document.querySelector('.job-card').click());
await laptopPage.waitForTimeout(300);
check('F: dossier opens with a sticky-free desktop view', await laptopPage.locator('body.view-detail').count() === 1);
await laptopPage.keyboard.press('Escape');
await laptopPage.waitForTimeout(450);
const laptopAfterEscape = await laptopPage.evaluate(() => ({ y: window.scrollY, detail: document.body.classList.contains('view-detail') }));
check('F: Escape returns to the feed at the saved scroll offset',
  !laptopAfterEscape.detail && laptopAfterEscape.y >= 300,
  `y=${Math.round(laptopAfterEscape.y)}`);
await laptopContext.close();

check('no unexpected console/page errors', consoleErrors.length === 0, consoleErrors.slice(0, 4).join(' || ').slice(0, 240));
check('zero same-origin HTTP errors across the whole run', sameOriginHttpErrors.length === 0, sameOriginHttpErrors.slice(0, 4).join(' || ').slice(0, 240));

await browser.close();

const failures = results.filter(r => !r[1]);
console.log('\n' + (results.length - failures.length) + '/' + results.length + ' checks passed');
if (failures.length) {
  console.log('FAILURES:');
  failures.forEach(f => console.log(' -', f[0], f[2]));
  process.exit(1);
}
