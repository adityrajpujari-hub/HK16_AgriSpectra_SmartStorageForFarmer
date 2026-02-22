document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('eligibilityForm');
  const fetchRiskBtn = document.getElementById('fetchRiskBtn');
  const riskInput = document.getElementById('autoRiskLevel');
  const resultSection = document.getElementById('eligibilityResult');

  if(!form || !fetchRiskBtn || !riskInput || !resultSection) return;

  function getPayload() {
    const fd = new FormData(form);
    return {
      crop_type: fd.get('crop_type'),
      region: fd.get('region'),
      state: fd.get('state'),
      farmer_category: fd.get('farmer_category'),
      landholding_size: fd.get('landholding_size'),
      storage_days: fd.get('storage_days'),
      temperature: fd.get('temperature'),
      humidity: fd.get('humidity'),
      season: fd.get('season'),
      risk_level: fd.get('risk_level')
    };
  }

  function riskLevelFromResponse(data) {
    return data.risk_level || data.riskLevel || data.level || 'UNKNOWN';
  }

  async function fetchRiskLevel() {
    const payload = getPayload();
    const riskPayload = {
      crop_type: payload.crop_type,
      region: payload.region,
      temperature: payload.temperature,
      humidity: payload.humidity,
      season: payload.season,
      storage_days: payload.storage_days
    };

    const resp = await fetch('/api/risk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(riskPayload)
    });
    const data = await resp.json();
    const level = riskLevelFromResponse(data);
    riskInput.value = String(level).toUpperCase();
    return riskInput.value;
  }

  function renderChecks(checks) {
    return `
      <div class="eligibility-checklist">
        ${checks.map(c => `
          <div class="eligibility-check ${c.met ? 'met' : 'not-met'}">
            <i class="fa-solid ${c.met ? 'fa-circle-check' : 'fa-circle-minus'}"></i>
            <span>${c.label}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  function renderSchemeCard(scheme) {
    return `
      <article class="eligibility-card">
        <h4><i class="fa-solid ${scheme.icon}"></i> ${scheme.name}</h4>
        <p><strong>Purpose:</strong> ${scheme.purpose}</p>
        <p><strong>Why you may be eligible:</strong> ${scheme.why_eligible}</p>
        <p><strong>Recommended next action:</strong> ${scheme.recommended_next_action}</p>
        <p><a href="${scheme.official_link}" target="_blank" rel="noopener noreferrer">Official verification link</a></p>
      </article>
    `;
  }

  function renderResult(data) {
    const summary = data.input_summary || {};
    const checks = Array.isArray(data.checks) ? data.checks : [];
    const schemes = Array.isArray(data.possible_schemes) ? data.possible_schemes : [];
    const actions = Array.isArray(data.recommended_actions) ? data.recommended_actions : [];

    resultSection.style.display = 'block';
    resultSection.innerHTML = `
      <h3><i class="fa-solid fa-badge-check"></i> Possible Support Eligibility Results</h3>
      <p><strong>Crop:</strong> ${summary.crop_type || '-'} | <strong>Region:</strong> ${summary.region || '-'} | <strong>Risk Level:</strong> ${summary.risk_level || '-'}</p>
      ${renderChecks(checks)}
      <div class="eligibility-grid">
        ${schemes.map(renderSchemeCard).join('')}
      </div>
      <div class="content-section" style="margin-top:1rem;">
        <h4><i class="fa-solid fa-list"></i> Recommended Next Steps</h4>
        <ul>
          ${actions.map(a => `<li>${a}</li>`).join('')}
        </ul>
      </div>
      <div class="eligibility-disclaimer">
        <i class="fa-solid fa-circle-exclamation"></i>
        <span>${data.disclaimer || 'This eligibility check is for awareness only and does not guarantee approval. Farmers must verify details on official government portals.'}</span>
      </div>
    `;
  }

  fetchRiskBtn.addEventListener('click', async () => {
    try {
      fetchRiskBtn.disabled = true;
      fetchRiskBtn.textContent = 'Fetching...';
      await fetchRiskLevel();
    } catch (err) {
      console.error(err);
      alert('Unable to fetch risk level. Please check inputs.');
    } finally {
      fetchRiskBtn.disabled = false;
      fetchRiskBtn.innerHTML = '<i class="fa-solid fa-wave-square"></i> Fetch Risk Level';
    }
  });

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    try {
      if(!riskInput.value){
        await fetchRiskLevel();
      }
      const payload = getPayload();
      const resp = await fetch('/api/eligibility', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      renderResult(data);
    } catch (err) {
      console.error(err);
      alert('Eligibility check failed. Please try again.');
    }
  });
});

