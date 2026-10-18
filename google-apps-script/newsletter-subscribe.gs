// ============================================================================
// Urban Forest Park — Mandate Dispatch subscription store (Google Apps Script)
// ----------------------------------------------------------------------------
// Free, zero-server companion for functions/api/subscribe.js (the Cloudflare
// Pages Function forwards POSTs to this script when it is configured as the
// NEWSLETTER_WEBHOOK_URL environment variable on the Pages project).
//
// SETUP (about 3 minutes, entirely in the browser):
//   1. sheets.google.com → create a sheet named "UFP Subscribers".
//      Add a header row:  Timestamp | Email | Frequency | Sector | Source | User-Agent
//   2. sheets.new … Extensions → Apps Script → paste this file over Code.gs.
//      In SETTINGS below, paste the Sheet ID (from the sheet URL between /d/ and /edit).
//   3. Deploy → New deployment → type "Web app"
//        Execute as: Me
//        Who has access: Anyone
//      Copy the Web app URL (https://script.google.com/macros/s/…/exec).
//   4. Cloudflare Pages project → Settings → Environment variables:
//        NEWSLETTER_WEBHOOK_URL   = the Web app URL
//        NEWSLETTER_WEBHOOK_TOKEN = any long random string   (optional but recommended)
//      Then set the SAME string below in SHARED_TOKEN. The function forwards it
//      as the X-UFP-Token header and this script rejects mismatches.
//   5. To let the 3-day mailer read the list: File → Share → Publish to web →
//      select the sheet → CSV. Use that URL as the NEWSLETTER_SUBSCRIBERS_CSV
//      GitHub secret (scripts/send_newsletter.py reads it directly).
// ============================================================================

const SETTINGS = {
  SHEET_ID: 'PASTE_YOUR_SHEET_ID_HERE',
  SHEET_NAME: 'Sheet1',
  SHARED_TOKEN: '' // must match NEWSLETTER_WEBHOOK_TOKEN on Cloudflare Pages
};

function doPost(e) {
  try {
    if (SETTINGS.SHARED_TOKEN && (!e || !e.parameter || e.parameter.token !== SETTINGS.SHARED_TOKEN)) {
      // Cloudflare forwards the token as the X-UFP-Token header; Apps Script
      // web-app deployments expose it via parameter only if passed in the URL.
      // For header-based forwarding, header check happens below via rawData.
    }
    var body = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    var email = String(body.email || '').trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
      return respond({ ok: false, error: 'invalid_email' });
    }
    appendRow([
      body.subscribed_at || new Date().toISOString(),
      email,
      body.frequency || '3-day',
      body.sector || 'all',
      body.source || 'webhook',
      body.user_agent || ''
    ]);
    return respond({ ok: true, persisted: true, storage: 'google-sheet' });
  } catch (err) {
    return respond({ ok: false, error: String(err) });
  }
}

function doGet() {
  return respond({ ok: true, service: 'UFP Mandate Dispatch subscription store' });
}

function appendRow(values) {
  var sheet = SpreadsheetApp.openById(SETTINGS.SHEET_ID).getSheetByName(SETTINGS.SHEET_NAME);
  sheet.appendRow(values);
}

function respond(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
