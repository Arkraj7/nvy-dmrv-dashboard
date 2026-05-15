// ============================================
// NAGAR VAN DMRV - GOOGLE APPS SCRIPT
// Deploy as Web App: Execute as Me, Anyone can access
// ============================================

const SHEET_ID = '1mjsb8S14mn5c75ahdwKblT2nVFIEnyK8QQynYk1v-38';

function doGet() {
  return ContentService.createTextOutput('Nagar Van DMRV API is running')
    .setMimeType(ContentService.MimeType.TEXT);
}

function getSheet(sheetName) {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    throw new Error('Sheet tab not found: "' + sheetName + '". Create it in the spreadsheet.');
  }
  return sheet;
}

/**
 * Merges POST body (e.parameter) and URL query string (e.queryString).
 */
function getRequestParams(e) {
  const params = {};

  if (e && e.parameter) {
    Object.keys(e.parameter).forEach(function (key) {
      params[key] = e.parameter[key];
    });
  }

  if (e && e.queryString) {
    e.queryString.split('&').forEach(function (pair) {
      if (!pair) return;
      const eq = pair.indexOf('=');
      const key = decodeURIComponent((eq > -1 ? pair.slice(0, eq) : pair).replace(/\+/g, ' '));
      const val = eq > -1
        ? decodeURIComponent(pair.slice(eq + 1).replace(/\+/g, ' '))
        : '';
      if (params[key] === undefined) {
        params[key] = val;
      }
    });
  }

  if (e && e.postData && e.postData.contents) {
    const type = (e.postData.type || '').toLowerCase();
    if (type.indexOf('application/json') !== -1) {
      try {
        const json = JSON.parse(e.postData.contents);
        Object.keys(json).forEach(function (key) {
          if (params[key] === undefined) params[key] = json[key];
        });
      } catch (err) { /* ignore invalid JSON */ }
    }
  }

  return params;
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    const data = getRequestParams(e);
    const action = (data.action || '').trim();

    let sheet = null;
    let row = [];

    if (action === 'submitFeedback') {
      sheet = getSheet('PublicFeedback');
      row = [
        new Date(),
        data.name || '',
        data.type || '',
        data.rating || '',
        data.message || '',
        data.timestamp || new Date().toISOString()
      ];
    } else if (action === 'submitSurvey') {
      sheet = getSheet('PublicSurvey');
      row = [
        new Date(),
        data.name || '',
        data.age || '',
        data.gender || '',
        data.state || '',
        data.parkType || '',
        data.parkTypeOther || '',
        data.parkName || '',
        data.latitude || '',
        data.longitude || '',
        data.visitReason || '',
        data.wellbeing || '',
        data.envChange || '',
        data.facilities || '',
        data.wtp || '',
        data.feedback || '',
        data.timestamp || new Date().toISOString()
      ];
    } else if (action === 'submitGrievance') {
      sheet = getSheet('Grievances');
      row = [
        new Date(),
        data.name || '',
        data.email || '',
        data.phone || '',
        data.state || '',
        data.parkName || '',
        data.category || data.issueType || '',
        data.description || '',
        data.severity || '',
        data.lat || data.latitude || '',
        data.lon || data.longitude || '',
        data.reportID || ''
      ];
    } else if (action === 'submitPublicContribution') {
      sheet = getSheet('PublicContribution');
      row = [
        new Date(),
        data.name || '',
        data.respondentType || '',
        data.state || '',
        data.vanName || '',
        data.visitFrequency || '',
        data.purpose || '',
        data.duration || '',
        data.eco || '',
        data.clean || '',
        data.safety || '',
        data.review || '',
        data.timestamp || new Date().toISOString()
      ];
    } else if (action === 'chat') {
      return jsonResponse(handleChatWithGemini(data.message || ''));
    } else {
      return jsonResponse({
        success: false,
        message: 'Unknown action: "' + action + '". Use submitSurvey, submitFeedback, submitGrievance, or chat.'
      });
    }

    sheet.appendRow(row);
    return jsonResponse({ success: true, message: 'Submitted successfully!' });

  } catch (error) {
    return jsonResponse({ success: false, message: 'Error: ' + error.toString() });
  }
}

function submitGrievance(data) {
  return handleDirectSubmit('submitGrievance', data);
}

function submitSurvey(data) {
  return handleDirectSubmit('submitSurvey', data);
}

function submitFeedback(data) {
  return handleDirectSubmit('submitFeedback', data);
}

/**
 * Optional: set Script Property GEMINI_API_KEY (Project Settings → Script properties).
 * Get a free key at https://aistudio.google.com/apikey
 */
function handleChatWithGemini(message) {
  const trimmed = (message || '').trim();
  if (!trimmed) {
    return { success: false, useLocal: true, message: 'Empty message' };
  }

  const apiKey = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
  if (!apiKey) {
    return { success: false, useLocal: true, message: 'GEMINI_API_KEY not configured' };
  }

  const systemPrompt =
    'You are the Nagar Van Assistant for the Nagar Van DMRV Dashboard (India urban forests). ' +
    'Answer clearly in 2–5 short paragraphs. Topics: Nagar Van Yojana, MoEF&CC, CAMPA, DMRV, ' +
    'afforestation, Miyawaki, public survey (public-survey.html), issue reporting (report.html), ' +
    'carbon sequestration, biodiversity, air quality. If unsure, suggest arkraj.biswas6@gmail.com. ' +
    'Do not invent statistics. User question: ';

  const payload = {
    contents: [{ parts: [{ text: systemPrompt + trimmed }] }],
    generationConfig: { temperature: 0.6, maxOutputTokens: 512 }
  };

  try {
    const response = UrlFetchApp.fetch(
      'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=' + apiKey,
      {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify(payload),
        muteHttpExceptions: true
      }
    );

    const code = response.getResponseCode();
    const body = JSON.parse(response.getContentText());

    if (code !== 200) {
      return { success: false, useLocal: true, message: 'Gemini API error: ' + code };
    }

    const reply = body.candidates &&
      body.candidates[0] &&
      body.candidates[0].content &&
      body.candidates[0].content.parts &&
      body.candidates[0].content.parts[0] &&
      body.candidates[0].content.parts[0].text;

    if (!reply) {
      return { success: false, useLocal: true, message: 'No reply from Gemini' };
    }

    return { success: true, reply: String(reply).trim(), source: 'gemini' };
  } catch (error) {
    return { success: false, useLocal: true, message: error.toString() };
  }
}

function handleDirectSubmit(action, data) {
  try {
    data = data || {};
    data.action = action;
    const result = doPost({ parameter: data, queryString: '' });
    return JSON.parse(result.getContent());
  } catch (error) {
    return { success: false, message: error.toString() };
  }
}
