#!/usr/bin/env python3
"""Generate salary intelligence pages from the verified job registry."""
from __future__ import annotations
import json, re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC = REPO_ROOT / "public"
SITE = "https://www.urbanforestpark.com"

def _fit(text, limit):
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[:limit - 1].rstrip() + "\u2026"

GTM_SCRIPT = """<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-TWFHGXN7');</script>
<!-- End Google Tag Manager -->"""

GTM_NOSCRIPT = """<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-TWFHGXN7"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""

SWG_SCRIPT = """    <script async type="application/javascript"
        src="https://news.google.com/swg/js/v1/swg-basic.js"></script>
    <script>
      (self.SWG_BASIC = self.SWG_BASIC || []).push( basicSubscriptions => {
        basicSubscriptions.init({
          type: "NewsArticle",
          isPartOfType: ["Product"],
          isPartOfProductId: "CAowvJXIDA:openaccess",
          clientOptions: { theme: "light", lang: "en-GB" },
        });
      });
    </script>"""

def plain(v): return str(v or "").strip()
def slugify(v): return re.sub(r"[^a-z0-9-]+", "-", str(v or "").lower()).strip("-") or "role"

def load_jobs():
    out = []
    for name in ("jobs.json", "global_jobs.json"):
        path = PUBLIC / name
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for j in data:
                        j = dict(j); j["_registry"] = "india" if name == "jobs.json" else "global"; out.append(j)
            except Exception: pass
    return out

def page_shell(title, desc, canonical, body):
    return f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
{GTM_SCRIPT}
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{canonical}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta name="theme-color" content="#F8FAFC">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <link rel="shortcut icon" href="/favicon.ico">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{canonical}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"CollectionPage","name":"{title}","description":"{desc}","url":"{canonical}"}}
  </script>
  <link rel="stylesheet" href="/styles/jobs.css">
  <link rel="stylesheet" href="/styles/hub.css">
  <script src="/js/consent-tags.js?v=20261028"></script>
</head>
<body>
{GTM_NOSCRIPT}
  <a class="skip-link" href="#main-content">Skip to salary details</a>
  <main class="detail-wrap" id="main-content" style="max-width:960px;margin:0 auto;padding:24px 16px;">
    <nav class="job-crumbs" aria-label="Breadcrumb">
      <a href="/">Career Registry</a> <span aria-hidden="true">/</span>
      <span>Salary Guide</span>
    </nav>
    {body}
  </main>
  <script defer src="/js/consent.js?v=20261028b"></script>
{SWG_SCRIPT}
</body>
</html>
"""

def aggregate(jobs):
    by_role=defaultdict(list); by_city=defaultdict(list); by_exp=defaultdict(list)
    for j in jobs:
        by_role[plain(j.get("position_type")) or "Other"].append(j)
        by_city[plain(j.get("city")) or plain(j.get("state")) or "India"].append(j)
        by_exp[plain(j.get("experience_level")) or "Not disclosed"].append(j)
    return by_role, by_city, by_exp

def comp_samples(jobs, n=5):
    out=[]; seen=set()
    for j in jobs:
        c=plain(j.get("compensation_or_fellowship"))
        if c and c not in seen:
            seen.add(c); out.append(c)
            if len(out)>=n: break
    return out

def extract_numbers(text):
    # Pull the first currency/amount-like numbers from a free-text compensation string.
    nums=[]
    for m in re.finditer(r"(?<!\d)(\d[\d,]*(?:\.\d+)?)", str(text or "")):
        try:
            nums.append(float(m.group(1).replace(",", "")))
        except ValueError:
            pass
    return nums

def build_salary_guide():
    jobs=load_jobs()
    by_role, by_city, by_exp = aggregate(jobs)
    role_rows=[]
    for role, js in sorted(by_role.items(), key=lambda x:-len(x[1])):
        samples=comp_samples(js)
        sample_html="<br>".join(f"<small>{s}</small>" for s in samples) if samples else "<small>Not disclosed</small>"
        nums=[]
        for j in js:
            nums.extend(extract_numbers(j.get("compensation_or_fellowship")))
        if nums:
            numeric = f"Observed amounts: {min(nums):,.0f} – {max(nums):,.0f}"
        else:
            numeric = "No numeric band stated"
        role_rows.append(f"<tr><td><a href='/salaries/{slugify(role)}'>{role}</a></td><td>{len(js)}</td><td>{sample_html}<br><small style='color:#16a34a;'>{numeric}</small></td></tr>")
    city_rows=[]
    for city, js in sorted(by_city.items(), key=lambda x:-len(x[1]))[:25]:
        samples=comp_samples(js,3)
        sample_html=", ".join(samples) if samples else "Not disclosed"
        city_rows.append(f"<tr><td>{city}</td><td>{len(js)}</td><td><small>{sample_html}</small></td></tr>")
    exp_rows=[]
    for exp, js in sorted(by_exp.items(), key=lambda x:-len(x[1])):
        samples=comp_samples(js,3)
        sample_html=", ".join(samples) if samples else "Not disclosed"
        exp_rows.append(f"<tr><td>{exp}</td><td>{len(js)}</td><td><small>{sample_html}</small></td></tr>")
    body=f"""
    <h1>Salary Guide — Climate, Forestry, ESG & Research Jobs in India</h1>
    <p>Aggregated compensation bands from {len(jobs)} verified listings.</p>
    <h2>By role</h2>
    <div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:14px;">
      <thead><tr><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">Role</th><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">Listings</th><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">Sample compensation</th></tr></thead>
      <tbody>{''.join(role_rows)}</tbody></table></div>
    <h2>By city</h2>
    <div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:14px;">
      <thead><tr><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">City</th><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">Listings</th><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">Sample compensation</th></tr></thead>
      <tbody>{''.join(city_rows)}</tbody></table></div>
    <h2>By experience level</h2>
    <div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:14px;">
      <thead><tr><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">Experience</th><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">Listings</th><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">Sample compensation</th></tr></thead>
      <tbody>{''.join(exp_rows)}</tbody></table></div>
    """
    html=page_shell(_fit("Salary Guide — Green Jobs in India | Urban Forest Park", 65), f"Aggregated salary bands by role, city and experience from {len(jobs)} verified green jobs.", SITE+"/salary-guide", body)
    (PUBLIC/"salary-guide.html").write_text(html, encoding="utf-8")
    (PUBLIC/"salaries").mkdir(exist_ok=True)
    # The old /salaries/ duplicate is retired: it canonicalised to the guide and
    # had no inbound links. Keep a permanent redirect instead of a second page.
    legacy_index = PUBLIC/"salaries"/"index.html"
    if legacy_index.exists():
        legacy_index.unlink()
    kept = set()
    for role, js in by_role.items():
        rows=[]
        for j in sorted(js, key=lambda x:str(x.get("date_added","")), reverse=True)[:40]:
            title=plain(j.get("clean_title") or j.get("title"))
            org=plain(j.get("organization"))
            city=plain(j.get("city")) or plain(j.get("state")) or "India"
            comp=plain(j.get("compensation_or_fellowship")) or "Not disclosed"
            rows.append(f"<tr><td>{title}</td><td>{org}</td><td>{city}</td><td><small>{comp}</small></td></tr>")
        body=f"""
        <h1>{role} — Salary & Compensation (India)</h1>
        <p>{len(js)} verified listings. Compensation as printed on official notices.</p>
        <p style="line-height:1.7;margin-bottom:16px;">This page aggregates observed compensation for <strong>{role}</strong> roles across {len(js)} verified green-jobs listings in India. Figures are taken verbatim from official notifications and may include stipends, fellowships, CTC or consolidated pay. Use them to benchmark your expectations before applying; always confirm the latest amount on the employer's official page.</p>
        <h2>How to read these numbers</h2>
        <ul style="line-height:1.8;margin-bottom:16px;">
          <li><strong>Not disclosed:</strong> the employer did not publish a figure; ask during the interview or check the official notification.</li>
          <li><strong>Stipend / fellowship:</strong> usually monthly, for project staff and research fellows.</li>
          <li><strong>CTC / annual:</strong> full-time corporate or NGO roles, often with variable pay and benefits.</li>
          <li><strong>LPA:</strong> lakhs per annum (1 LPA = Rs 1,00,000 per year).</li>
        </ul>
        <div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:14px;">
          <thead><tr><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">Role</th><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">Employer</th><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">City</th><th style="text-align:left;padding:8px;border-bottom:1px solid #e2e8f0;">Compensation</th></tr></thead>
          <tbody>{''.join(rows)}</tbody></table></div>
        <h2>Frequently asked questions</h2>
        <details style="margin-bottom:8px;"><summary style="cursor:pointer;font-weight:600;">Are these salaries guaranteed?</summary><p style="margin-top:6px;line-height:1.6;">No. Figures are observed compensation from verified listings and official notifications; actual pay depends on experience, location and the employer's final offer.</p></details>
        <details style="margin-bottom:8px;"><summary style="cursor:pointer;font-weight:600;">How often is this page updated?</summary><p style="margin-top:6px;line-height:1.6;">The registry refreshes daily; this page is rebuilt on every build from the latest verified listings.</p></details>
        <details style="margin-bottom:16px;"><summary style="cursor:pointer;font-weight:600;">Where can I find open {role} roles?</summary><p style="margin-top:6px;line-height:1.6;">See the <a href="/sustainability-jobs-india">sustainability jobs hub</a> and the <a href="/employers">employer profiles</a> for current vacancies.</p></details>
        <p style="margin-top:16px;"><a href="/salary-guide">Back to salary guide</a></p>
        """
        html=page_shell(_fit(f"{role} Salary | Urban Forest Park", 65), _fit(f"Compensation ranges for {role} roles across {len(js)} verified listings.", 160), SITE+"/salaries/"+slugify(role), body)
        (PUBLIC/"salaries"/f"{slugify(role)}.html").write_text(html, encoding="utf-8")
        kept.add(f"{slugify(role)}.html")
    for path in (PUBLIC/"salaries").glob("*.html"):
        if path.name not in kept:
            path.unlink()
    sync_sitemap()


def sync_sitemap():
    """List the salary guide and role pages, retiring the /salaries/ duplicate."""
    path = PUBLIC/"sitemap.xml"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"\s*<url>\s*<loc>https://www\.urbanforestpark\.com/salaries?/[^<]*</loc>.*?</url>",
        "", text, flags=re.S,
    )
    text = re.sub(
        r"\s*<url>\s*<loc>https://www\.urbanforestpark\.com/salary-guide</loc>.*?</url>",
        "", text, flags=re.S,
    )
    rows = [
        "  <url><loc>https://www.urbanforestpark.com/salary-guide</loc>"
        "<lastmod>" + date.today().isoformat() + "</lastmod>"
        "<changefreq>weekly</changefreq><priority>0.7</priority></url>"
    ]
    for page in sorted((PUBLIC/"salaries").glob("*.html")):
        rows.append(
            "  <url><loc>https://www.urbanforestpark.com/salaries/"
            + page.stem
            + "</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>"
        )
    text = text.replace("</urlset>", "\n".join(rows) + "\n</urlset>")
    path.write_text(text, encoding="utf-8")

    redirects = PUBLIC/"_redirects"
    if redirects.exists():
        body = redirects.read_text(encoding="utf-8")
        body = re.sub(r"^/salaries/.*\n", "", body, flags=re.M)
        body = body.replace(
            "# END generated job redirects",
            "# END generated job redirects\n"
            "/salaries/ /salary-guide 301\n"
            "/salaries/index.html /salary-guide 301",
        )
        redirects.write_text(body, encoding="utf-8")

if __name__ == "__main__":
    build_salary_guide()
    print("salary pages built")