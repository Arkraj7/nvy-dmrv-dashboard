/**
 * Climate AI — Intelligent climate Q&A with chart generation
 * Inspired by CRAVIS (CEEW). Uses Nagar Van site data.
 */
const ClimateAI = (function () {
  const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const YEARS = ['Yr 0','Yr 1','Yr 2','Yr 3','Yr 4','Yr 5','Yr 6','Yr 7','Yr 8','Yr 9','Yr 10','Yr 11','Yr 12'];

  /* ── Knowledge Base ─────────────────────────────── */
  const FACTS = [
    { kw:['nagar van','yojana','scheme'], ans:'Nagar Van Yojana (NVY) is a MoEF&CC flagship scheme to develop 400+ urban forests across India. Each site is 2–100 ha, funded under National CAMPA with ₹2–4 Cr per site. The DMRV Dashboard tracks their ecological & socio-economic impacts.' },
    { kw:['miyawaki'], ans:'The Miyawaki method (Dr Akira Miyawaki) plants 30–50 native species densely (3–5 saplings/m²) to create a multi-layered forest. Growth is 10× faster than conventional — reaching maturity in 20 years vs 200.' },
    { kw:['camp'], ans:'CAMPA (Compensatory Afforestation Fund Management and Planning Authority) manages ₹60,000+ Cr collected from forest land diversion. Funds are used for afforestation, NVY, and wildlife conservation under Supreme Court oversight.' },
    { kw:['dmrv','digital monitoring'], ans:'DMRV = Digital Monitoring, Reporting & Verification. An AI-powered system using satellite NDVI (NASA AppEEARS), IoT sensors, CVM surveys, and CPCB air quality data to quantify urban forest impacts in real time.' },
    { kw:['urban heat','uhi','heat island'], ans:'Urban Heat Island (UHI) effect makes cities 3–8°C hotter than surrounding areas. Nagar Van sites reduce UHI by 1–4°C locally through shade & evapotranspiration. Rajasthan sites (Kaylana, Depalsar) show 2.8–3.8°C reduction.' },
    { kw:['air quality','pm2.5','pollution'], ans:'Nagar Van trees reduce PM2.5 by 15–28% by intercepting particulate matter on leaf surfaces. NCAP sites (Indore, Bhopal, Surat, Firozabad) show the highest reductions due to higher baseline pollution levels.' },
    { kw:['carbon','sequestration','co2'], ans:'Urban forests sequester 2.5–5.5 t CO₂/ha/yr depending on species, age & climate. MP sites (Devguradiya, Shahpura) show highest rates (4.6–4.8 t/ha/yr) due to older age & higher NDVI baselines.' },
    { kw:['biodiversity','bird','species'], ans:'NVY sites increase bird species by 20–50% compared to bare land. Vaishnodevi Temple Seeladehi (Seoni, MP) shows highest (+50%) due to Pench Tiger Reserve proximity. Indroda Nature Park (Gandhinagar) +44% due to existing dinosaur park ecosystem.' },
    { kw:['who-5','wellbeing','well being'], ans:'WHO-5 Well-Being Index scores for NVY visitors are 15–28 pts higher than non-visitors. Sarnath Varanasi (+28 pts) and Devli Areb Kota (+24 pts) score highest — both are pilgrimage/student cities where green access has strong mental health impact.' },
    { kw:['wtp','willingness','pay','cvm'], ans:'Willingness to Pay (WTP) via Contingent Valuation Method (CVM) surveys averages ₹19–40/month across sites. Tirupati (₹35), Sarnath (₹40), and Gandhinagar (₹32) show highest — driven by religious tourism and higher-income demographics.' },
    { kw:['water','recharge','stormwater','runoff'], ans:'Nagar Van sites recharge 5,000–22,000 L/yr/ha through root-channel infiltration. Nellore (coastal AP) shows highest (22k L) due to tropical rainfall. Churu sites (6k L) lowest due to arid Thar climate.' },
    { kw:['ncap'], ans:'NCAP (National Clean Air Programme) funds Nagar Van in 131 non-attainment cities. NCAP sites in this dataset: Devguradiya (Indore), Shahpura (Bhopal), Nellore, Dumas (Surat), Navalakhi (Ujjain), Purva (Jabalpur), Palnagar (Dewas), Sirol Pahadi (Gwalior), Datauji (Firozabad), Merui (Raebareli), Rajapur (Raebareli).' },
    { kw:['ncap city','non-attainment'], ans:'Non-attainment cities are those consistently failing NAAQS air quality standards. NCAP aims 20–30% PM2.5/PM10 reduction by 2026. NVY is a key green infrastructure intervention under NCAP.' },
    { kw:['ndvi'], ans:'NDVI (Normalized Difference Vegetation Index) measures vegetation health (-1 to +1). NVY sites start at 0.08–0.28 (bare/degraded) and reach 0.32–0.62 after 3 years. Depalsar (Churu, Rajasthan) has lowest baseline (0.08) — highest potential for satellite-verified NDVI growth.' },
    { kw:['mmr','matheran'], ans:'The Matheran Marginal Railway (MMR) eco-sensitive zone is a UNESCO Heritage site. NVY has proposed 2 ha forest along the railway buffer — pending sanction.' },
    { kw:['area','hectare','size'], ans:'NVY sites range from 2 ha (Sarnath, Varanasi) to 100 ha (Devguradiya, Indore). Average size ~44 ha. Total area across 30 sites: ~1,555 ha. 20 of 30 sites are 50 ha — the standard NVY plot size.' },
    { kw:['cost','budget','funding','instalment'], ans:'Standard NVY cost is ₹200L per 50 ha site (₹4L/ha). Total investment across 30 sites: ₹5,410L (~₹54 Cr). Punjab site (Rakh Nehar Ki Bir) highest at ₹205.3L. Sarnath lowest at ₹8L (2 ha).' },
    { kw:['report','issue','bug'], ans:'To report an issue or bug, use the "Report Issue" page (report.html) or email arkraj.biswas6@gmail.com. You can also click "Submit Feedback" in the footer.' },
    { kw:['survey','public survey'], ans:'The Public Survey helps collect community data on urban forest perceptions, WTP, and wellbeing. Visit public-survey.html to participate.' },
    { kw:['volunteer','involve','participate'], ans:'To get involved: email arkraj.biswas6@gmail.com. Opportunities include field surveys, data collection, GIS analysis, and community outreach for Nagar Van sites.' },
    { kw:['state','location','where'], ans:'The 30 Nagar Van sites span 6 states: Uttar Pradesh (10 sites), Rajasthan (7), Madhya Pradesh (7), Andhra Pradesh (2), Gujarat (2), Punjab (2).' },
    { kw:['total','count','number of'], ans:'The Dashboard tracks 30 Nagar Van sites across 6 states. Batch 1: 10 sites (2025). Batch 2: 20 sites (May 2026 update).' },
    { kw:['green calculator','calculator','carbon calculator'], ans:'The Green Calculator tool (green-calculator.html) quantifies CO₂ sequestration, biodiversity potential, cooling effect, air quality improvement, stormwater reduction & Green Branding Score for any urban green space.' }
  ];

  /* ── Site Data (lightweight summary) ────────────── */
  let SITES = [];

  function loadSiteData() {
    if (SITES.length) return;
    try {
      const el = document.getElementById('nv-spatial-data');
      if (el) SITES = JSON.parse(el.textContent);
    } catch(e) {}
  }

  function getAllSites() { loadSiteData(); return SITES; }

  function findSites(query) {
    loadSiteData();
    const q = query.toLowerCase();
    let results = [];
    let seen = new Set();
    SITES.forEach(s => {
      let score = 0;
      if (s.name.toLowerCase().includes(q)) score += 20;
      if (s.state.toLowerCase().includes(q)) score += 15;
      if (s.district.toLowerCase().includes(q)) score += 12;
      if (s.climate.toLowerCase().includes(q)) score += 8;
      if (s.zone && s.zone.toLowerCase().includes(q)) score += 6;
      if (q.split(' ').some(w => w.length > 2 && s.name.toLowerCase().includes(w))) score += 4;
      if (score > 0 && !seen.has(s.id)) {
        seen.add(s.id);
        results.push({ site: s, score });
      }
    });
    results.sort((a,b) => b.score - a.score);
    return results.slice(0, 5).map(r => r.site);
  }

  function getSitesByState(state) {
    loadSiteData();
    return SITES.filter(s => s.state.toLowerCase().includes(state.toLowerCase()));
  }

  function getStateSummary() {
    loadSiteData();
    let summary = {};
    SITES.forEach(s => {
      if (!summary[s.state]) summary[s.state] = { count:0, area:0, cost:0, sites:[] };
      summary[s.state].count++;
      summary[s.state].area += s.area;
      summary[s.state].cost += s.cost;
      summary[s.state].sites.push(s.name);
    });
    return summary;
  }

  /* ── Intent Classification ──────────────────────── */
  function classifyIntent(query) {
    const q = query.toLowerCase();

    if (/chart|graph|plot|show.*(temp|rainfall|carbon|ndvi|pm|bio|who)|visualize|compare/i.test(q)) {
      return 'chart';
    }
    if (/compare|versus|vs\.?|difference|which.*(better|higher|lower|more)|ranking/i.test(q)) {
      return 'compare';
    }
    if (/hello|hi |hey|greet|namaste/i.test(q)) {
      return 'greeting';
    }
    if (/help|what can you|capabilities|guide|manual/i.test(q)) {
      return 'help';
    }
    return 'info';
  }

  function extractMetric(query) {
    const q = query.toLowerCase();
    if (/temperature|temp|uhi|heat|cooling|hot/i.test(q)) return 'temperature';
    if (/rainfall|rain|precipitation|rainy/i.test(q)) return 'rainfall';
    if (/carbon|co2|sequestration/i.test(q)) return 'carbon';
    if (/ndvi|vegetation|greenness/i.test(q)) return 'ndvi';
    if (/pm2\.5|pm25|air quality|pollution|particulate/i.test(q)) return 'pm25';
    if (/biodiversity|bird|species|wildlife/i.test(q)) return 'biodiversity';
    if (/who-5|who5|wellbeing|well-being|mental/i.test(q)) return 'who5';
    if (/wtp|willingness|pay|economic|valuation/i.test(q)) return 'wtp';
    if (/water|recharge|runoff|stormwater/i.test(q)) return 'water';
    if (/area|hectare|size/i.test(q)) return 'area';
    return null;
  }

  function getChartConfig(metric, sites) {
    if (!sites || !sites.length) return null;

    const col = { "Uttar Pradesh":"#4fc3f7", "Rajasthan":"#ffd54f", "Madhya Pradesh":"#ce93d8", "Andhra Pradesh":"#4db6ac", "Gujarat":"#81c784", "Punjab":"#ffcc02" };

    if (metric === 'temperature') {
      return {
        type: 'line', title: '🌡️ Monthly Temperature Reduction (°C)',
        labels: MONTHS,
        datasets: sites.map(s => ({
          label: s.name.split(' ').slice(0,2).join(' '),
          data: s.tempRed || [],
          borderColor: col[s.state] || '#5dc48a',
          backgroundColor: col[s.state] + '22' || '#5dc48a22',
          fill: true, tension: 0.3, pointRadius: 2
        }))
      };
    }
    if (metric === 'rainfall') {
      return {
        type: 'bar', title: '🌧️ Monthly Rainfall (mm)',
        labels: MONTHS,
        datasets: sites.map(s => ({
          label: s.name.split(' ').slice(0,2).join(' '),
          data: s.rainfall || [],
          backgroundColor: col[s.state] || '#5dc48a',
          borderRadius: 3
        }))
      };
    }
    if (metric === 'carbon') {
      return {
        type: 'line', title: '🌲 Cumulative Carbon Sequestration (t CO₂/ha)',
        labels: YEARS,
        datasets: sites.map(s => ({
          label: s.name.split(' ').slice(0,2).join(' '),
          data: s.carbonYr || [],
          borderColor: col[s.state] || '#5dc48a',
          backgroundColor: col[s.state] + '11' || '#5dc48a11',
          fill: true, tension: 0.3, pointRadius: 1.5
        }))
      };
    }
    if (metric === 'ndvi') {
      return {
        type: 'line', title: '🌿 Monthly NDVI Pattern (Post-Planting)',
        labels: MONTHS,
        datasets: sites.map(s => ({
          label: s.name.split(' ').slice(0,2).join(' '),
          data: s.ndviMon || [],
          borderColor: col[s.state] || '#5dc48a',
          backgroundColor: col[s.state] + '22' || '#5dc48a22',
          fill: true, tension: 0.3, pointRadius: 2
        }))
      };
    }
    if (metric === 'pm25') {
      return {
        type: 'bar', title: '💨 PM2.5 — Site vs City (µg/m³)',
        labels: MONTHS,
        datasets: [
          { label: sites[0]?.name?.split(' ').slice(0,2).join(' ') + ' (Site)', data: sites[0]?.pm25Site || [], backgroundColor: '#5dc48a', borderRadius: 3 },
          { label: sites[0]?.name?.split(' ').slice(0,2).join(' ') + ' (City)', data: sites[0]?.pm25City || [], backgroundColor: '#ef4444', borderRadius: 3 }
        ]
      };
    }
    if (metric === 'biodiversity') {
      return {
        type: 'radar', title: '🐦 Bird Species — Quarterly Comparison',
        labels: ['Q1','Q2','Q3','Q4'],
        datasets: sites.map(s => ({
          label: s.name.split(' ').slice(0,2).join(' '),
          data: s.bioQ || [],
          borderColor: col[s.state] || '#5dc48a',
          backgroundColor: col[s.state] + '33' || '#5dc48a33',
          pointRadius: 3
        }))
      };
    }
    if (metric === 'who5') {
      return {
        type: 'bar', title: '😊 WHO-5 Well-Being Score',
        labels: ['Visitors', 'Non-Visitors'],
        datasets: sites.slice(0,5).map(s => ({
          label: s.name.split(' ').slice(0,2).join(' '),
          data: [s.who5V || 0, s.who5NV || 0],
          backgroundColor: col[s.state] || '#5dc48a',
          borderRadius: 3
        }))
      };
    }
    if (metric === 'area') {
      let areas = {};
      sites.forEach(s => {
        if (!areas[s.state]) areas[s.state] = 0;
        areas[s.state] += s.area;
      });
      return {
        type: 'bar', title: '📐 Total Area by State (ha)',
        labels: Object.keys(areas),
        datasets: [{
          label: 'Hectares', data: Object.values(areas),
          backgroundColor: Object.keys(areas).map(st => col[st] || '#5dc48a'),
          borderRadius: 4
        }]
      };
    }
    return null;
  }

  /* ── Response Generation ────────────────────────── */
  function generateResponse(query) {
    const intent = classifyIntent(query);
    const q = query.toLowerCase();

    if (intent === 'greeting') {
      const greetings = [
        'Namaste! I\'m your Climate AI assistant. Ask me anything about Nagar Van sites, climate data, or try "show chart" to visualise metrics.',
        'Hello! I can help you explore climate data across 30 Nagar Van sites. Ask about temperature trends, carbon sequestration, or type "help" to see what I can do.',
        'Hi there! Ask me about urban forests, climate metrics, or say "show me temperature for Rajasthan" to generate a chart!'
      ];
      return { text: greetings[Math.floor(Math.random() * greetings.length)] };
    }

    if (intent === 'help') {
      return { text: `I can help with:<br><br>📍 <b>Site Info</b> — "Tell me about Kaylana Nagar Van"<br>📊 <b>Charts</b> — "Show temperature for Rajasthan sites"<br>🔬 <b>Compare</b> — "Compare carbon in MP vs UP"<br>🧠 <b>General Knowledge</b> — "What is UHI effect?"<br>🌐 <b>State Summary</b> — "Show Uttar Pradesh sites"<br>📐 <b>Metrics</b> — temperature, rainfall, carbon, NDVI, PM2.5, biodiversity, WHO-5, WTP<br><br>Try: <i>"show rainfall for Rajasthan"</i> or <i>"carbon chart all sites"</i>` };
    }

    if (intent === 'chart') {
      const metric = extractMetric(q);
      const sites = findSites(q);
      const stateSites = Object.keys(getStateSummary()).filter(st => q.includes(st.toLowerCase()));
      let targetSites = [];

      if (stateSites.length) {
        targetSites = getSitesByState(stateSites[0]);
      } else if (sites.length) {
        targetSites = sites.slice(0, 3);
      } else if (/all|every|total|overview/i.test(q)) {
        loadSiteData();
        targetSites = SITES.slice(0, 5);
      } else {
        loadSiteData();
        targetSites = SITES.slice(0, 3);
      }

      if (!metric) {
        return { text: 'Which metric would you like to chart? Try: <b>temperature</b>, <b>rainfall</b>, <b>carbon</b>, <b>NDVI</b>, <b>PM2.5</b>, <b>biodiversity</b>, or <b>WHO-5</b>.' };
      }

      const chartConfig = getChartConfig(metric, targetSites);
      if (!chartConfig) return { text: 'Could not generate chart for that combination. Try a different metric or location.' };

      const siteNames = targetSites.map(s => s.name).join(', ');
      return {
        text: `📊 Showing <b>${chartConfig.title}</b> for: ${siteNames}`,
        chart: chartConfig
      };
    }

    if (intent === 'compare') {
      const metric = extractMetric(q);
      const states = Object.keys(getStateSummary()).filter(st => q.includes(st.toLowerCase()));
      loadSiteData();
      let cmpSites = [];

      if (states.length >= 2) {
        states.forEach(st => { cmpSites = cmpSites.concat(getSitesByState(st)); });
      } else if (states.length === 1) {
        cmpSites = getSitesByState(states[0]);
      } else if (/site|all|every/i.test(q)) {
        cmpSites = SITES.slice(0, 5);
      } else {
        cmpSites = SITES.slice(0, 3);
      }

      if (!metric) return { text: 'What would you like to compare? Try: "compare carbon in MP and UP" or "compare temperature across states".' };
      const chartConfig = getChartConfig(metric, cmpSites);
      if (!chartConfig) return { text: 'Comparison data not available for that combination.' };

      return {
        text: `📊 Comparing <b>${chartConfig.title}</b>`,
        chart: chartConfig
      };
    }

    /* ── Info intent ──────────────────────────────── */
    /* Check facts */
    for (let f of FACTS) {
      if (f.kw.some(k => q.includes(k))) {
        return { text: f.ans };
      }
    }

    /* Site info */
    const matchedSites = findSites(q);
    if (matchedSites.length) {
      const s = matchedSites[0];
      const stateSummary = getStateSummary();
      if (matchedSites.length >= 3 && !q.includes(s.name.toLowerCase().split(' ')[0])) {
        let html = `<b>${matchedSites.length} sites found:</b><br><ul style="margin:4px 0;padding-left:16px">`;
        matchedSites.forEach(site => {
          html += `<li style="margin:2px 0"><b>${site.name}</b> — ${site.district}, ${site.state} (${site.area} ha, ${site.climate})</li>`;
        });
        if (matchedSites.length > 5) html += `<li>...and ${matchedSites.length - 5} more</li>`;
        html += '</ul>';
        return { text: html };
      }

      let html = `<div style="border-left:3px solid #5dc48a;padding-left:12px;margin:4px 0">`;
      html += `<b>${s.name}</b><br>`;
      html += `📍 ${s.district}, ${s.state} · ${s.climate}<br>`;
      html += `🌳 ${s.area} ha · 📅 FY ${s.fy} · ₹${s.cost}L`;
      if (s.cat) html += ` · ⭐ ${s.cat}`;
      html += `<br><br>${s.desc.substring(0, 200)}${s.desc.length > 200 ? '...' : ''}`;
      html += `<br><br><b>Key Metrics:</b><br>`;
      html += `🌡️ UHI Reduction: ${s.env.uhi} · 💨 PM2.5: ${s.env.pm25} · 🌿 NDVI: ${s.env.ndvi}<br>`;
      html += `🌲 Carbon: ${s.env.carbon} · 🐦 Birds: ${s.env.birds} · 💧 Water: ${s.env.water}<br>`;
      html += `😊 WHO-5: ${s.env.who5} · 💰 WTP: ${s.env.wtp}`;
      html += `</div>`;

      const totalSites = getAllSites().length;
      return { text: html, totalSites };
    }

    /* State summary */
    const stateSum = getStateSummary();
    const stateMatch = Object.keys(stateSum).filter(st => q.includes(st.toLowerCase()));
    if (stateMatch.length) {
      const st = stateSum[stateMatch[0]];
      return { text: `<b>${stateMatch[0]}</b> — ${st.count} sites, ${st.area} ha total, ₹${st.cost}L investment.<br><br>Sites: ${st.sites.join(', ')}` };
    }

    return { text: 'I couldn\'t find specific information about that. Try asking about a specific site, state, or metric. Type <b>"help"</b> to see what I can do.' };
  }

  /* ── UI ─────────────────────────────────────────── */
  function toggle() {
    const win = document.getElementById('ca-chat-window');
    const btn = document.getElementById('ca-chat-toggle');
    if (!win) return;
    const open = win.classList.toggle('open');
    btn.classList.toggle('hidden', open);
    if (open) {
      document.getElementById('ca-chat-input')?.focus();
    }
  }

  function send() {
    const input = document.getElementById('ca-chat-input');
    const msg = (input?.value || '').trim();
    if (!msg) return;
    input.value = '';
    addMessage(msg, true);
    processMessage(msg);
  }

  function addMessage(text, isUser) {
    const msgs = document.getElementById('ca-chat-msgs');
    if (!msgs) return;
    const div = document.createElement('div');
    div.className = 'ca-msg' + (isUser ? ' ca-user' : ' ca-ai');
    div.innerHTML = isUser
      ? `<div class="ca-bubble ca-user-bubble">${escHtml(text)}</div>`
      : `<div class="ca-avatar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg></div><div class="ca-bubble ca-ai-bubble">${text}</div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function escHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function showTyping() {
    const msgs = document.getElementById('ca-chat-msgs');
    if (!msgs) return;
    const div = document.createElement('div');
    div.className = 'ca-msg ca-ai ca-typing-indicator';
    div.id = 'ca-typing';
    div.innerHTML = `<div class="ca-avatar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg></div><div class="ca-bubble ca-ai-bubble"><span class="ca-typing-dot"></span><span class="ca-typing-dot"></span><span class="ca-typing-dot"></span></div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function hideTyping() {
    const el = document.getElementById('ca-typing');
    if (el) el.remove();
  }

  function processMessage(msg) {
    showTyping();
    setTimeout(() => {
      hideTyping();
      const result = generateResponse(msg);
      let text = result.text;

      if (result.chart) {
        const chartId = 'ca-chart-' + Date.now();
        text += `<br><br><button class="ca-chart-btn" onclick="ClimateAI.showChart('${chartId}', '${result.chart.type}', '${result.chart.title.replace(/'/g, "\\'")}')" data-chart='${JSON.stringify(result.chart).replace(/'/g, "&#39;")}'>📊 View Chart</button>`;
        text += `<div id="${chartId}" style="display:none;margin-top:8px"><canvas style="max-height:260px"></canvas></div>`;
      }

      addMessage(text, false);
    }, 600 + Math.random() * 400);
  }

  function showChart(id, type, title) {
    const container = document.getElementById(id);
    if (!container) return;
    const canvas = container.querySelector('canvas');
    if (!canvas) return;

    const btn = container.previousElementSibling;
    if (btn && btn.classList.contains('ca-chart-btn')) {
      btn.style.display = 'none';
    }
    container.style.display = 'block';

    const parent = container.closest('.ca-ai-bubble') || container;
    const maxWidth = parent.offsetWidth || 280;

    canvas.style.maxWidth = maxWidth + 'px';
    canvas.style.maxHeight = '220px';

    const dataStr = btn?.getAttribute('data-chart');
    if (!dataStr) return;
    try {
      const data = JSON.parse(dataStr.replace(/&#39;/g, "'"));
      if (window.caChart) try { window.caChart.destroy(); } catch(e) {}
      const ctx = canvas.getContext('2d');
      window.caChart = new Chart(ctx, {
        type: data.type || 'bar',
        data: {
          labels: data.labels,
          datasets: data.datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: { labels: { color: '#6b7280', font: { size: 9 }, boxWidth: 10 } }
          },
          scales: {
            x: { ticks: { color: '#9ca3af', font: { size: 8 }, maxTicksLimit: 8 }, grid: { color: 'rgba(27,58,45,0.06)' } },
            y: { ticks: { color: '#9ca3af', font: { size: 8 } }, grid: { color: 'rgba(27,58,45,0.06)' } }
          }
        }
      });
    } catch(e) {
      container.innerHTML = '<span style="font-size:11px;color:#ef4444">Chart render error. Try again.</span>';
    }
  }

  function quick(q) {
    const input = document.getElementById('ca-chat-input');
    if (input) input.value = q;
    send();
  }

  function handleKey(e) {
    if (e.key === 'Enter') send();
  }

  /* ── Init ───────────────────────────────────────── */
  function init(siteData) {
    if (siteData) SITES = siteData;
    loadSiteData();

    /* Add typing dots CSS if not present */
    if (!document.getElementById('ca-typing-style')) {
      const style = document.createElement('style');
      style.id = 'ca-typing-style';
      style.textContent = `
        .ca-typing-dot { display:inline-block; width:6px; height:6px; border-radius:50%; background:#5dc48a; margin:0 2px; animation:caBounce 1.4s infinite both; }
        .ca-typing-dot:nth-child(2) { animation-delay:0.16s; }
        .ca-typing-dot:nth-child(3) { animation-delay:0.32s; }
        @keyframes caBounce { 0%,80%,100% { transform:scale(0.6) } 40% { transform:scale(1) } }
      `;
      document.head.appendChild(style);
    }
  }

  return {
    init, toggle, send, quick, handleKey,
    addMessage, processMessage, showChart,
    findSites, getSitesByState, getStateSummary,
    getAllSites, generateResponse
  };
})();
