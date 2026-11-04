"""Generate a Contact Us page matching the site shell."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_seo_pages as bsp

body = """
  <main style="max-width:900px;margin:0 auto;padding:40px 20px;">
    <h1>Contact Urban Forest Park</h1>
    <p style="font-size:17px;color:var(--ink-2);max-width:720px;">
      Questions about a listing, a broken link, a partnership, or the Nagar Van dMRV dashboard?
      Reach the editorial team below. We read every message and reply within 3-5 working days.
    </p>

    <section style="margin-top:28px;">
      <h2>Email</h2>
      <p><a href="mailto:urbanforestpark@gmail.com">urbanforestpark@gmail.com</a></p>
      <p style="color:var(--ink-3);font-size:14px;">For listing corrections, broken-link reports and editorial queries.</p>
    </section>

    <section style="margin-top:28px;">
      <h2>Official communities</h2>
      <ul>
        <li><a href="https://t.me/urbanforestpark" target="_blank" rel="noopener noreferrer">Telegram channel</a> &mdash; daily job alerts</li>
        <li><a href="https://www.linkedin.com/groups/40965341/" target="_blank" rel="noopener noreferrer">LinkedIn Group</a></li>
        <li><a href="https://www.facebook.com/share/1EwgtMnfcx/" target="_blank" rel="noopener noreferrer">Facebook page</a></li>
        <li><a href="https://chat.whatsapp.com/JJ0ItiNOfvEDCDIENscenw" target="_blank" rel="noopener noreferrer">WhatsApp community</a></li>
      </ul>
    </section>

    <section style="margin-top:28px;">
      <h2>Report a broken link</h2>
      <p>Every job page carries a &ldquo;Report a broken link&rdquo; button. Use it on the listing page and we re-verify the source within 24 hours.</p>
    </section>

    <section style="margin-top:28px;">
      <h2>Editorial &amp; governance</h2>
      <p>Urban Forest Park is published by Arkraj Biswas. See the <a href="/about">About page</a> for editorial standards, verification method and governance. Privacy and terms: <a href="/privacy">Privacy Policy</a> and <a href="/terms">Terms of Use</a>.</p>
    </section>
  </main>
"""

title = "Contact Urban Forest Park | Green Jobs & Career Registry"
desc = "Contact Urban Forest Park: email, official communities, broken-link reports and editorial queries for the India green jobs and career registry."
html_doc = f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="https://www.urbanforestpark.com/contact">
  <link rel="stylesheet" href="/styles/jobs.css?v=20261104c">
</head>
<body>
{bsp.header_html()}
{body}
{bsp.footer_html()}
  <script defer src="/js/i18n.js"></script>
  <script defer src="/js/hub.js"></script>
</body>
</html>
"""

out = ROOT / "public" / "contact.html"
out.write_text(html_doc, encoding="utf-8")
print("wrote", out)
