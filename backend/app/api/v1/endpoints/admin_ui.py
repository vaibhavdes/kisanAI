from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


ADMIN_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kisan AI Admin</title>
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
    .stack { display: grid; gap: 14px; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
    .card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--soft);
      padding: 14px;
      display: grid;
      gap: 10px;
    }
    .row { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; align-items: end; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; color: var(--muted); }
    textarea {
      width: 100%;
      min-height: 78px;
      border: 1px solid #cad7c7;
      border-radius: 8px;
      padding: 9px 10px;
      resize: vertical;
      background: #fff;
      color: var(--ink);
    }
    pre {
      white-space: pre-wrap;
      margin: 0;
      padding: 12px;
      border-radius: 8px;
      background: #101810;
      color: #d9f6df;
      max-height: 280px;
      overflow: auto;
    }
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
      <h1>Kisan AI Admin</h1>
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
    <section>
      <div class="section-head">
        <h2>Demo Alert Simulation</h2>
        <button class="secondary" id="seedFarmerBtn">Create Demo Farmer</button>
      </div>
      <div class="content stack">
        <div class="row">
          <div>
            <label for="farmerSelect">Farmer</label>
            <select id="farmerSelect"></select>
          </div>
          <div>
            <label for="scenarioSelect">Scenario</label>
            <select id="scenarioSelect">
              <option value="dry_spell_urgent">Dry spell / urgent call + SMS</option>
              <option value="heat_stress">Heat stress / high priority</option>
              <option value="normal_skip">Normal weather / likely skipped</option>
            </select>
          </div>
          <div>
            <label for="alertCrop">Crop</label>
            <input id="alertCrop" type="text" value="jowar">
          </div>
          <div>
            <button id="runAlertBtn">Run Simulation</button>
          </div>
        </div>
        <div class="row">
          <div>
            <label for="rainfallInput">7-day rainfall mm</label>
            <input id="rainfallInput" type="text" value="0,0,0,0,0,0,1">
          </div>
          <div>
            <label for="moistureInput">Soil moisture</label>
            <input id="moistureInput" type="text" value="0.12">
          </div>
          <div>
            <label for="tempInput">Temperature C</label>
            <input id="tempInput" type="text" value="37">
          </div>
        </div>
        <div class="status">Use this for live demo: it calls the same proactive alert endpoint used by Scheduler/PubSub. Delivery can be dry-run or real depending on AUTHKEY_SEND_ENABLED.</div>
        <pre id="alertOutput">No simulation run yet.</pre>
      </div>
    </section>
    <section>
      <div class="section-head">
        <h2>Expert Tickets</h2>
        <button class="secondary" id="refreshTicketsBtn">Refresh Tickets</button>
      </div>
      <div class="content">
        <div class="cards" id="tickets"></div>
      </div>
    </section>
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
      whatsapp: ["twilio"],
      sms_voice: ["authkey"]
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
        const fallbackDisabled = ['satellite', 'whatsapp', 'sms_voice'].includes(route.feature) ? 'disabled' : '';
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

    async function loadFarmers() {
      const response = await fetch('/api/v1/farmers?limit=100');
      const farmers = await response.json();
      const select = document.getElementById('farmerSelect');
      select.innerHTML = farmers.map(farmer => {
        const label = `${farmer.name} · ${farmer.village}, ${farmer.district} · ${farmer.phone}`;
        return `<option value="${farmer.id}">${label}</option>`;
      }).join('');
      if (!farmers.length) {
        select.innerHTML = '<option value="">No farmers yet</option>';
      }
    }

    async function createDemoFarmer() {
      const response = await fetch('/api/v1/farmers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Demo Farmer',
          phone: '+919970983794',
          language: 'hi-IN',
          village: 'Rahuri',
          district: 'Ahilyanagar',
          state: 'Maharashtra',
          farm: {
            area_acres: 2,
            soil_type: 'black',
            soil_ph: 6.8,
            groundwater_depth_m: 18,
            latitude: 19.3906,
            longitude: 74.6496
          }
        })
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Could not create demo farmer');
      }
      await loadFarmers();
      showBanner('Demo farmer ready');
    }

    function applyScenario() {
      const scenario = document.getElementById('scenarioSelect').value;
      const presets = {
        dry_spell_urgent: { rain: '0,0,0,0,0,0,1', moisture: '0.12', temp: '37' },
        heat_stress: { rain: '0,1,0,0,0,1,0', moisture: '0.16', temp: '39' },
        normal_skip: { rain: '4,3,2,0,1,3,5', moisture: '0.28', temp: '30' }
      };
      const preset = presets[scenario];
      document.getElementById('rainfallInput').value = preset.rain;
      document.getElementById('moistureInput').value = preset.moisture;
      document.getElementById('tempInput').value = preset.temp;
    }

    async function runAlertSimulation() {
      const farmerId = document.getElementById('farmerSelect').value;
      if (!farmerId) {
        throw new Error('Create or select a farmer first');
      }
      const rainfall = document.getElementById('rainfallInput').value
        .split(',')
        .map(value => Number(value.trim()))
        .filter(value => Number.isFinite(value));
      const payload = {
        farmer_ids: [farmerId],
        crop: document.getElementById('alertCrop').value || 'crop',
        min_priority: 'medium',
        rainfall_forecast_mm: rainfall,
        soil_moisture: Number(document.getElementById('moistureInput').value),
        temperature_c: Number(document.getElementById('tempInput').value),
        dedupe: false,
        idempotency_key: `admin-demo-${Date.now()}`
      };
      const response = await fetch('/api/v1/alerts/run-daily', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Alert simulation failed');
      }
      document.getElementById('alertOutput').textContent = JSON.stringify(data, null, 2);
      showBanner('Alert simulation completed');
    }

    async function loadTickets() {
      const response = await fetch('/api/v1/expert/tickets?limit=100');
      const tickets = await response.json();
      const container = document.getElementById('tickets');
      if (!tickets.length) {
        container.innerHTML = '<div class="status">No expert tickets yet. Send a crop photo/diagnosis request to create one.</div>';
        return;
      }
      container.innerHTML = tickets.map(ticket => `
        <div class="card" data-ticket="${ticket.id}">
          <div><strong>${ticket.crop}</strong> · ${ticket.severity} · ${ticket.status}</div>
          <div>${ticket.issue}</div>
          <div class="mono">${ticket.id} · ${ticket.farmer_name} · ${ticket.district || 'district unknown'} · ${ticket.assigned_center}</div>
          <div class="row">
            <select data-field="status">
              ${['open', 'assigned', 'in_progress', 'resolved', 'closed'].map(status => `<option value="${status}" ${status === ticket.status ? 'selected' : ''}>${status}</option>`).join('')}
            </select>
            <input data-field="expert" type="text" placeholder="Expert name" value="${ticket.assigned_expert || ''}">
          </div>
          <textarea data-field="note" placeholder="Expert note / farmer response"></textarea>
          <button data-action="updateTicket">Update Ticket</button>
        </div>
      `).join('');
    }

    async function updateTicket(card) {
      const ticketId = card.dataset.ticket;
      const payload = {
        status: card.querySelector('[data-field="status"]').value,
        assigned_expert: card.querySelector('[data-field="expert"]').value || null,
        expert_note: card.querySelector('[data-field="note"]').value || null,
        notify_farmer: true
      };
      const response = await fetch(`/api/v1/expert/ticket/${ticketId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Ticket update failed');
      }
      showBanner('Ticket updated');
      await loadTickets();
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
      await Promise.all([loadHealth(), loadRoutes(), loadFarmers(), loadTickets()]);
    }

    document.getElementById('saveBtn').addEventListener('click', saveRoutes);
    document.getElementById('refreshBtn').addEventListener('click', refreshAll);
    document.getElementById('refreshTicketsBtn').addEventListener('click', () => loadTickets().catch(error => showBanner(error.message, true)));
    document.getElementById('seedFarmerBtn').addEventListener('click', () => createDemoFarmer().catch(error => showBanner(error.message, true)));
    document.getElementById('scenarioSelect').addEventListener('change', applyScenario);
    document.getElementById('runAlertBtn').addEventListener('click', () => runAlertSimulation().catch(error => showBanner(error.message, true)));
    document.getElementById('tickets').addEventListener('click', event => {
      if (event.target && event.target.dataset.action === 'updateTicket') {
        updateTicket(event.target.closest('.card')).catch(error => showBanner(error.message, true));
      }
    });
    refreshAll().catch(error => showBanner(error.message, true));
  </script>
</body>
</html>
"""


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard() -> HTMLResponse:
    return HTMLResponse(ADMIN_HTML)
