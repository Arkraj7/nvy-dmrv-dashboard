// ============================================
// NAGAR VAN DMRV - GOOGLE APPS SCRIPT
// Deploy as Web App: Execute as Me, Anyone can access
// ============================================

const SHEET_ID = '1mjsb8S14mn5c75ahdwKblT2nVFIEnyK8QQynYk1v-38';

// OpenCode Zen — set OPENCODE_API_KEY in Script Properties (recommended).
// Model: https://opencode.ai/docs/zen/
const OPENCODE_CONFIG = {
  MODEL: 'minimax-m2.5-free'
};

function getOpenCodeCredentials() {
  const props = PropertiesService.getScriptProperties();
  return {
    apiKey: props.getProperty('OPENCODE_API_KEY') || '',
    model: props.getProperty('OPENCODE_MODEL') || OPENCODE_CONFIG.MODEL
  };
}

function doGet(e) {
  const action = (e && e.parameter && e.parameter.action) || '';
  if (action === 'getCounts') {
    return getSurveyCounts();
  }
  return ContentService.createTextOutput('Nagar Van DMRV API is running')
    .setMimeType(ContentService.MimeType.TEXT);
}

/**
 * Returns live survey sample counts from PublicContribution sheet,
 * organized by state/site key for the dashboard.
 */
function getSurveyCounts() {
  try {
    // Map state names from the sheet to dashboard site keys
    const stateKeyMap = {
      'Andhra Pradesh': 'andhra',
      'Delhi': 'delhi',
      'Gujarat': 'gujarat',
      'Jharkhand': 'jharkhand',
      'Karnataka': 'karnataka',
      'Madhya Pradesh': 'mp',
      'Maharashtra': 'maharashtra',
      'Rajasthan': 'rajasthan',
      'West Bengal': 'westbengal',
      'Uttar Pradesh': 'up'
    };

    var sites = {
      overview: 0, gujarat: 0, jharkhand: 0, andhra: 0, mp: 0,
      maharashtra: 0, karnataka: 0, rajasthan: 0, delhi: 0, westbengal: 0
    };
    var locations = [];
    var total = 0;

    // Read PublicContribution sheet: [Date, Name, RespondentType, State, VanName, ...]
    var sheet = getSheet('PublicContribution');
    var data = sheet.getDataRange().getValues();

    // Skip header row (index 0), count data rows
    for (var i = 1; i < data.length; i++) {
      var row = data[i];
      if (!row[0]) continue; // skip empty rows
      var stateName = String(row[3] || '').trim();
      var vanName = String(row[4] || '').trim();
      var respondentType = String(row[2] || '').trim();

      total++;

      var siteKey = stateKeyMap[stateName] || 'other';
      if (sites[siteKey] !== undefined) {
        sites[siteKey]++;
      }
      sites.overview = total;
    }

    // Also count PublicSurvey sheet if it exists
    try {
      var surveySheet = getSheet('PublicSurvey');
      var surveyData = surveySheet.getDataRange().getValues();
      // Header is row 0, count from row 1
      for (var j = 1; j < surveyData.length; j++) {
        if (surveyData[j][0]) {
          total++;
          sites.overview = total;
        }
      }
    } catch (e) {
      // PublicSurvey sheet may not exist yet
    }

    return jsonResponse({
      success: true,
      total: total,
      sites: sites,
      locations: locations
    });

  } catch (error) {
    // Return zeros on error so the dashboard doesn't break
    return jsonResponse({
      success: false,
      total: 0,
      sites: {
        overview: 0, gujarat: 0, jharkhand: 0, andhra: 0, mp: 0,
        maharashtra: 0, karnataka: 0, rajasthan: 0, delhi: 0, westbengal: 0
      },
      locations: []
    });
  }
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
      return jsonResponse(handleChatWithOpenCode(data.message || ''));
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
 * OpenCode Zen — https://opencode.ai/docs/zen/
 * Script properties (Project Settings → Script properties):
 *   OPENCODE_API_KEY  — from https://opencode.ai/auth
 *   OPENCODE_MODEL    — optional, default minimax-m2.5-free (free tier)
 * Uses OpenAI-compatible POST https://opencode.ai/zen/v1/chat/completions
 */
function handleChatWithOpenCode(message) {
  const trimmed = (message || '').trim();
  if (!trimmed) {
    return { success: false, useLocal: true, message: 'Empty message' };
  }

  const creds = getOpenCodeCredentials();
  if (!creds.apiKey) {
    return { success: false, useLocal: true, message: 'OPENCODE_API_KEY not configured' };
  }
  const apiKey = creds.apiKey;
  const model = creds.model;

  const systemPrompt =
    'You are the Nagar Van Assistant for the Nagar Van DMRV Dashboard (India urban forests). ' +
    'You are a helpful, knowledgeable assistant. Answer questions clearly and concisely in 1-3 paragraphs using simple language. ' +
    'You can help with many topics: Nagar Van Yojana, MoEF&CC, CAMPA, DMRV, afforestation, Miyawaki method, ' +
    'carbon sequestration, biodiversity, air quality, urban heat island, water management, public survey, ' +
    'issue reporting, site locations, tree species, environmental impact, community engagement. ' +
    'If a question is not about these topics, politely redirect to relevant topics or suggest contacting arkraj.biswas6@gmail.com. ' +
    'Do not invent statistics. Be friendly and helpful. Use plain text format without markdown symbols.';

  const payload = {
    model: model,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: trimmed }
    ],
    max_tokens: 1024,
    temperature: 0.7
  };

  try {
    const response = UrlFetchApp.fetch('https://opencode.ai/zen/v1/chat/completions', {
      method: 'post',
      contentType: 'application/json',
      headers: { Authorization: 'Bearer ' + apiKey },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });

    const code = response.getResponseCode();
    const raw = response.getContentText();
    let body;
    try {
      body = JSON.parse(raw);
    } catch (parseErr) {
      return { success: false, useLocal: true, message: 'Invalid OpenCode response' };
    }

    if (code !== 200) {
      const errMsg = (body.error && body.error.message) ? body.error.message : raw;
      return { success: false, useLocal: true, message: 'OpenCode API error (' + code + '): ' + errMsg };
    }

    const reply = body.choices &&
      body.choices[0] &&
      body.choices[0].message &&
      body.choices[0].message.content;

    if (!reply) {
      return { success: false, useLocal: true, message: 'No reply from OpenCode' };
    }

    return { success: true, reply: String(reply).trim(), source: 'opencode', model: model };
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
