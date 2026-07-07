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
    button.danger { background: #fff3f4; color: var(--bad); border: 1px solid #f1c5ca; }
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
    <section>
      <div class="section-head">
        <h2>Scheduled Alerts</h2>
        <span class="status">Enabled/disabled and frequency are used by the daily scheduler.</span>
      </div>
      <div class="content stack">
        <div class="row">
          <div>
            <label><input id="weatherEnabled" type="checkbox"> weather enabled</label>
          </div>
          <div>
            <label for="weatherFrequency">Weather frequency days</label>
            <input id="weatherFrequency" type="text" value="1">
          </div>
          <div>
            <label><input id="satelliteEnabled" type="checkbox"> satellite enabled</label>
          </div>
          <div>
            <label for="satelliteFrequency">Satellite frequency days</label>
            <input id="satelliteFrequency" type="text" value="7">
          </div>
          <div>
            <label for="morningHour">Morning hour</label>
            <input id="morningHour" type="text" value="7">
          </div>
          <div>
            <button class="secondary" id="saveScheduleBtn">Save Schedule</button>
          </div>
        </div>
        <div class="row">
          <div>
            <label for="farmerSelect">Farmer</label>
            <select id="farmerSelect"></select>
          </div>
          <div>
            <label for="alertKind">Alert Type</label>
            <select id="alertKind">
              <option value="weather">Daily weather + crop advisory</option>
              <option value="satellite">Satellite farm health update</option>
            </select>
          </div>
          <div>
            <button id="sendTestAlertBtn">Send Test Alert</button>
          </div>
        </div>
        <div class="status">Test alert uses only the selected farmer's saved location, active crop and provider data. Weather sends WhatsApp, one Authkey voice call and SMS if configured. Satellite sends WhatsApp only.</div>
        <pre id="alertOutput">No alert sent yet.</pre>
      </div>
    </section>
    <section>
      <div class="section-head">
        <h2>Registered Farmers</h2>
        <button class="secondary" id="refreshFarmersBtn">Refresh Farmers</button>
      </div>
      <div class="content">
        <div class="cards" id="farmers"></div>
        <pre id="farmerDetail">Select a farmer to view stored context.</pre>
      </div>
    </section>
    <section>
      <div class="section-head">
        <h2>Sensor Reading Injector</h2>
        <span class="status">Generic IoT/manual demo input for soil moisture and weather station data.</span>
      </div>
      <div class="content stack">
        <div class="row">
          <div>
            <label for="sensorFarmerSelect">Farmer</label>
            <select id="sensorFarmerSelect"></select>
          </div>
          <div>
            <label for="sensorId">Sensor ID</label>
            <input id="sensorId" type="text" value="manual_sensor_01">
          </div>
          <div>
            <label for="deviceType">Device type</label>
            <input id="deviceType" type="text" value="soil_moisture_sensor">
          </div>
          <div>
            <label for="sensorSource">Source</label>
            <input id="sensorSource" type="text" value="manual_entry">
          </div>
        </div>
        <div class="row">
          <div>
            <label for="sensorMoisture">Soil moisture 0-1</label>
            <input id="sensorMoisture" type="text" value="0.16">
          </div>
          <div>
            <label for="soilTemp">Soil temp C</label>
            <input id="soilTemp" type="text" value="29.4">
          </div>
          <div>
            <label for="airTemp">Air temp C</label>
            <input id="airTemp" type="text" value="34.1">
          </div>
          <div>
            <label for="humidity">Humidity %</label>
            <input id="humidity" type="text" value="62">
          </div>
          <div>
            <label for="rainfall">Rainfall mm</label>
            <input id="rainfall" type="text" value="0">
          </div>
          <div>
            <label for="battery">Battery %</label>
            <input id="battery" type="text" value="78">
          </div>
          <div>
            <button id="saveSensorBtn">Save Sensor Reading</button>
          </div>
        </div>
        <div class="status">The advisory engine will reuse the latest reading when a farmer asks irrigation/water advice.</div>
        <pre id="sensorOutput">No sensor reading saved yet.</pre>
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
    <section>
      <div class="section-head">
        <h2>Service Audit</h2>
        <button class="secondary" id="refreshAuditBtn">Refresh Audit</button>
      </div>
      <div class="content">
        <div class="cards" id="auditLogs"></div>
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

    async function loadSchedule() {
      const response = await fetch('/api/v1/alerts/schedule');
      const data = await response.json();
      document.getElementById('weatherEnabled').checked = Boolean(data.weather_enabled);
      document.getElementById('satelliteEnabled').checked = Boolean(data.satellite_enabled);
      document.getElementById('weatherFrequency').value = data.weather_frequency_days || 1;
      document.getElementById('satelliteFrequency').value = data.satellite_frequency_days || 7;
      document.getElementById('morningHour').value = data.morning_hour_local ?? 7;
    }

    async function saveSchedule() {
      const payload = {
        weather_enabled: document.getElementById('weatherEnabled').checked,
        satellite_enabled: document.getElementById('satelliteEnabled').checked,
        weather_frequency_days: Number(document.getElementById('weatherFrequency').value || 1),
        satellite_frequency_days: Number(document.getElementById('satelliteFrequency').value || 7),
        morning_hour_local: Number(document.getElementById('morningHour').value || 7)
      };
      const response = await fetch('/api/v1/alerts/schedule', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Could not save schedule');
      }
      await loadSchedule();
      showBanner('Alert schedule saved');
    }

    async function loadFarmers() {
      const response = await fetch('/api/v1/farmers?limit=100');
      const farmers = await response.json();
      const select = document.getElementById('farmerSelect');
      select.innerHTML = farmers.map(farmer => {
        const label = `${farmer.name} · ${farmer.village}, ${farmer.district} · ${farmer.phone}`;
        return `<option value="${farmer.id}">${label}</option>`;
      }).join('');
      const sensorSelect = document.getElementById('sensorFarmerSelect');
      sensorSelect.innerHTML = select.innerHTML;
      if (!farmers.length) {
        select.innerHTML = '<option value="">No farmers yet</option>';
        sensorSelect.innerHTML = '<option value="">No farmers yet</option>';
      }
      const container = document.getElementById('farmers');
      if (!farmers.length) {
        container.innerHTML = '<div class="status">No registered farmers yet.</div>';
        return;
      }
      container.innerHTML = farmers.map(farmer => `
        <div class="card">
          <div><strong>${farmer.name}</strong> · ${farmer.phone}</div>
          <div>${farmer.village || '-'}, ${farmer.taluka || '-'}, ${farmer.district || '-'}, ${farmer.state || '-'} ${farmer.pincode || ''}</div>
          <div class="mono">Language: ${farmer.language} · Crop: ${farmer.active_crop || '-'} · Water: ${farmer.water_availability || '-'}</div>
          <div class="mono">Lat/Lng: ${farmer.farm?.latitude ?? '-'}, ${farmer.farm?.longitude ?? '-'} · Soil: ${farmer.farm?.soil_type || '-'}</div>
          <div class="row">
            <button class="secondary" data-action="viewFarmer" data-farmer="${farmer.id}">View Context</button>
            <button class="danger" data-action="deleteFarmer" data-farmer="${farmer.id}">Remove User</button>
          </div>
        </div>
      `).join('');
    }

    async function viewFarmer(farmerId) {
      const [farmersResponse, messagesResponse, ticketsResponse] = await Promise.all([
        fetch('/api/v1/farmers?limit=100'),
        fetch(`/api/v1/conversations/${farmerId}?limit=12`),
        fetch(`/api/v1/expert/tickets/${farmerId}`)
      ]);
      const farmers = await farmersResponse.json();
      const farmer = farmers.find(item => item.id === farmerId);
      const messages = await messagesResponse.json();
      const tickets = await ticketsResponse.json();
      document.getElementById('farmerDetail').textContent = JSON.stringify({
        farmer,
        openTickets: tickets,
        recentMessages: messages
      }, null, 2);
    }

    async function deleteFarmer(farmerId) {
      const ok = window.confirm('Remove this farmer and their stored context?');
      if (!ok) {
        return;
      }
      const response = await fetch(`/api/v1/farmers/${farmerId}`, { method: 'DELETE' });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Could not remove farmer');
      }
      document.getElementById('farmerDetail').textContent = 'Select a farmer to view stored context.';
      await Promise.all([loadFarmers(), loadTickets(), loadAuditLogs()]);
      showBanner('Farmer removed');
    }

    async function sendSelectedFarmerAlert() {
      const farmerId = document.getElementById('farmerSelect').value;
      if (!farmerId) {
        throw new Error('Select a registered farmer first');
      }
      const payload = {
        kind: document.getElementById('alertKind').value,
        farmer_ids: [farmerId],
        crop: 'crop',
        min_priority: 'low',
        respect_frequency: false,
        dedupe: false,
        idempotency_key: `admin-test-${Date.now()}`
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
      document.getElementById('alertOutput').textContent = JSON.stringify({
        summary: summarizeAlertRun(data),
        raw: data
      }, null, 2);
      showBanner('Test alert submitted for selected farmer');
    }

    function numericValue(id) {
      const value = document.getElementById(id).value;
      if (value === '') return null;
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : null;
    }

    async function saveSensorReading() {
      const farmerId = document.getElementById('sensorFarmerSelect').value;
      if (!farmerId) {
        throw new Error('Select a registered farmer first');
      }
      const payload = {
        farmer_id: farmerId,
        sensor_id: document.getElementById('sensorId').value || 'manual_sensor_01',
        source: document.getElementById('sensorSource').value || 'manual_entry',
        device_type: document.getElementById('deviceType').value || 'soil_moisture_sensor',
        timestamp: new Date().toISOString(),
        readings: {
          soil_moisture: numericValue('sensorMoisture'),
          soil_temperature_c: numericValue('soilTemp'),
          air_temperature_c: numericValue('airTemp'),
          humidity_percent: numericValue('humidity'),
          rainfall_mm: numericValue('rainfall'),
          battery_percent: numericValue('battery')
        }
      };
      const response = await fetch('/api/v1/sensors/readings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Sensor reading failed');
      }
      document.getElementById('sensorOutput').textContent = JSON.stringify(data, null, 2);
      showBanner('Sensor reading saved');
    }

    function summarizeAlertRun(data) {
      const first = (data.results || [])[0] || {};
      const delivery = first.delivery || {};
      return {
        runDate: data.run_date,
        generated: data.generated,
        delivered: data.delivered,
        farmerId: first.farmer_id,
        risk: first.risk_level,
        priority: first.priority,
        overallStatus: delivery.overall_status,
        channels: (delivery.results || []).map(item => ({
          channel: item.channel,
          provider: item.provider,
          operation: item.operation,
          status: item.status,
          sent: item.sent,
          dryRun: item.dry_run,
          error: item.error,
          rawStatus: item.raw_status
        }))
      };
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

    async function loadAuditLogs() {
      const response = await fetch('/api/v1/providers/audit?limit=15');
      const data = await response.json();
      const logs = data.logs || [];
      const container = document.getElementById('auditLogs');
      if (!logs.length) {
        container.innerHTML = '<div class="status">No service audit logs yet.</div>';
        return;
      }
      container.innerHTML = logs.slice().reverse().map(log => `
        <div class="card">
          <div><strong>${log.service}</strong> · ${log.operation} · ${log.provider || '-'}</div>
          <div class="mono">${log.success ? 'ok' : 'failed'} · status ${log.status_code || '-'} · ${log.duration_ms || 0} ms · ${log.channel || '-'}</div>
          <div class="mono">Farmer: ${log.farmer_phone || '-'} · ${log.farmer_id || '-'}</div>
          ${log.error ? `<div style="color: var(--bad);">${log.error}</div>` : ''}
          <pre>${JSON.stringify({ request: log.request_body, response: log.response_body }, null, 2)}</pre>
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
      await Promise.all([loadHealth(), loadRoutes(), loadSchedule(), loadFarmers(), loadTickets(), loadAuditLogs()]);
    }

    document.getElementById('saveBtn').addEventListener('click', saveRoutes);
    document.getElementById('saveScheduleBtn').addEventListener('click', () => saveSchedule().catch(error => showBanner(error.message, true)));
    document.getElementById('refreshBtn').addEventListener('click', refreshAll);
    document.getElementById('refreshTicketsBtn').addEventListener('click', () => loadTickets().catch(error => showBanner(error.message, true)));
    document.getElementById('refreshFarmersBtn').addEventListener('click', () => loadFarmers().catch(error => showBanner(error.message, true)));
    document.getElementById('refreshAuditBtn').addEventListener('click', () => loadAuditLogs().catch(error => showBanner(error.message, true)));
    document.getElementById('sendTestAlertBtn').addEventListener('click', () => sendSelectedFarmerAlert().catch(error => showBanner(error.message, true)));
    document.getElementById('saveSensorBtn').addEventListener('click', () => saveSensorReading().catch(error => showBanner(error.message, true)));
    document.getElementById('tickets').addEventListener('click', event => {
      if (event.target && event.target.dataset.action === 'updateTicket') {
        updateTicket(event.target.closest('.card')).catch(error => showBanner(error.message, true));
      }
    });
    document.getElementById('farmers').addEventListener('click', event => {
      if (event.target && event.target.dataset.action === 'viewFarmer') {
        viewFarmer(event.target.dataset.farmer).catch(error => showBanner(error.message, true));
      }
      if (event.target && event.target.dataset.action === 'deleteFarmer') {
        deleteFarmer(event.target.dataset.farmer).catch(error => showBanner(error.message, true));
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
