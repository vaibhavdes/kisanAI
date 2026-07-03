from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


ADMIN_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kisan Alert Admin</title>
  <style>
    :root {
      color-scheme: light;
      --green: #116a39;
      --ink: #172017;
      --muted: #687568;
      --line: #dfe7de;
      --soft: #f5f8f3;
      --warn: #9f4a00;
      --bad: #a51d2d;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #fbfcf8;
    }
    header {
      padding: 24px clamp(16px, 4vw, 44px);
      border-bottom: 1px solid var(--line);
      background: #ffffff;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
    }
    h1 { margin: 0; font-size: clamp(22px, 3vw, 34px); }
    main { padding: 24px clamp(16px, 4vw, 44px); display: grid; gap: 24px; }
    .grid { display: grid; grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.6fr); gap: 24px; }
    section {
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 12px 30px rgba(33, 50, 30, 0.06);
    }
    .section-head {
      padding: 16px 18px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }
    h2 { margin: 0; font-size: 18px; }
    .content { padding: 16px 18px; }
    .services { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
    .service {
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--soft);
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      min-height: 50px;
    }
    .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--bad); flex: 0 0 auto; }
    .dot.ok { background: var(--green); }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: middle; }
    th { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
    select, input[type="text"] {
      width: 100%;
      min-width: 110px;
      border: 1px solid #cad7c7;
      border-radius: 8px;
      padding: 9px 10px;
      background: #fff;
      color: var(--ink);
    }
    label { display: inline-flex; align-items: center; gap: 8px; color: var(--muted); }
    button {
      border: 0;
      border-radius: 8px;
      background: var(--green);
      color: #fff;
      padding: 10px 14px;
      font-weight: 700;
      cursor: pointer;
    }
    button.secondary { background: #edf4ec; color: var(--green); border: 1px solid #cfe0ce; }
    button:disabled { opacity: 0.55; cursor: wait; }
    .status { color: var(--muted); font-size: 14px; }
    .banner {
      padding: 12px 14px;
      border-radius: 8px;
      background: #ecf7ef;
      color: var(--green);
      display: none;
    }
    .banner.error { background: #fff0f0; color: var(--bad); }
    @media (max-width: 860px) {
      header { align-items: flex-start; flex-direction: column; }
      .grid { grid-template-columns: 1fr; }
      table, thead, tbody, th, td, tr { display: block; }
      thead { display: none; }
      tr { border-bottom: 1px solid var(--line); padding: 12px 0; }
      td { border: 0; padding: 8px 0; }
      td::before { content: attr(data-label); display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Kisan Alert Admin</h1>
      <div class="status" id="updatedAt">Loading provider configuration...</div>
    </div>
    <button class="secondary" id="refreshBtn">Refresh</button>
  </header>
  <main>
    <div class="banner" id="banner"></div>
    <div class="grid">
      <section>
        <div class="section-head">
          <h2>Service Health</h2>
          <span class="status" id="checkedAt"></span>
        </div>
        <div class="content">
          <div class="services" id="services"></div>
        </div>
      </section>
      <section>
        <div class="section-head">
          <h2>Provider Routes</h2>
          <button id="saveBtn">Save Changes</button>
        </div>
        <div class="content">
          <table>
            <thead>
              <tr>
                <th>Feature</th>
                <th>Enabled</th>
                <th>Primary</th>
                <th>Fallback</th>
                <th>Use Fallback</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody id="routes"></tbody>
          </table>
        </div>
      </section>
    </div>
  </main>
  <script>
    const allowedProviders = {
      weather: ["imd", "open_meteo"],
      stt: ["google_stt", "sarvam_stt"],
      tts: ["google_tts", "sarvam_tts"],
      translation: ["google_translate", "sarvam_translate"],
      llm_advisory: ["vertex_ai", "gemini"],
      vision_ocr: ["vertex_ai_vision", "gemini_vision"],
      satellite: ["earth_engine"],
      geocoding_maps: ["google_maps", "osm_nominatim"],
      whatsapp: ["authkey", "twilio"],
      sms_voice: ["authkey", "twilio"]
    };
    const routeState = new Map();

    function optionList(feature, selected, allowEmpty) {
      const options = allowEmpty ? [''] : [];
      options.push(...(allowedProviders[feature] || []));
      return options.map(value => {
        const label = value || 'none';
        return `<option value="${value}" ${value === (selected || '') ? 'selected' : ''}>${label}</option>`;
      }).join('');
    }

    function showBanner(message, error = false) {
      const banner = document.getElementById('banner');
      banner.textContent = message;
      banner.className = `banner${error ? ' error' : ''}`;
      banner.style.display = 'block';
      setTimeout(() => { banner.style.display = 'none'; }, 3200);
    }

    async function loadHealth() {
      const response = await fetch('/health');
      const data = await response.json();
      document.getElementById('checkedAt').textContent = data.checkedAt || '';
      const services = document.getElementById('services');
      services.innerHTML = Object.entries(data.services || {}).map(([name, ok]) => `
        <div class="service">
          <span>${name}</span>
          <span class="dot ${ok ? 'ok' : ''}" aria-label="${ok ? 'ok' : 'not ready'}"></span>
        </div>
      `).join('');
    }

    async function loadRoutes() {
      const response = await fetch('/api/v1/providers/config');
      const data = await response.json();
      routeState.clear();
      const tbody = document.getElementById('routes');
      tbody.innerHTML = data.routes.map(route => {
        routeState.set(route.feature, route);
        const fallbackDisabled = route.feature === 'satellite' ? 'disabled' : '';
        return `
          <tr data-feature="${route.feature}">
            <td data-label="Feature"><strong>${route.feature}</strong></td>
            <td data-label="Enabled"><label><input type="checkbox" data-field="enabled" ${route.enabled ? 'checked' : ''}> enabled</label></td>
            <td data-label="Primary"><select data-field="primary">${optionList(route.feature, route.primary, false)}</select></td>
            <td data-label="Fallback"><select data-field="secondary" ${fallbackDisabled}>${optionList(route.feature, route.secondary, true)}</select></td>
            <td data-label="Use Fallback"><label><input type="checkbox" data-field="allow_fallback" ${route.allow_fallback ? 'checked' : ''} ${fallbackDisabled}> fallback</label></td>
            <td data-label="Note"><input type="text" data-field="note" value="${route.note || ''}"></td>
          </tr>
        `;
      }).join('');
      document.getElementById('updatedAt').textContent = `Updated at ${data.updated_at}`;
    }

    function collectRoutes() {
      const routes = {};
      document.querySelectorAll('#routes tr').forEach(row => {
        const feature = row.dataset.feature;
        routes[feature] = {
          primary: row.querySelector('[data-field="primary"]').value,
          secondary: row.querySelector('[data-field="secondary"]').value || null,
          enabled: row.querySelector('[data-field="enabled"]').checked,
          allow_fallback: row.querySelector('[data-field="allow_fallback"]').checked,
          note: row.querySelector('[data-field="note"]').value || null
        };
      });
      return { routes };
    }

    async function saveRoutes() {
      const button = document.getElementById('saveBtn');
      button.disabled = true;
      try {
        const response = await fetch('/api/v1/providers/config', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(collectRoutes())
        });
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to save provider routes');
        }
        await loadRoutes();
        showBanner('Provider routes saved');
      } catch (error) {
        showBanner(error.message, true);
      } finally {
        button.disabled = false;
      }
    }

    async function refreshAll() {
      await Promise.all([loadHealth(), loadRoutes()]);
    }

    document.getElementById('saveBtn').addEventListener('click', saveRoutes);
    document.getElementById('refreshBtn').addEventListener('click', refreshAll);
    refreshAll().catch(error => showBanner(error.message, true));
  </script>
</body>
</html>
"""


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard() -> HTMLResponse:
    return HTMLResponse(ADMIN_HTML)
