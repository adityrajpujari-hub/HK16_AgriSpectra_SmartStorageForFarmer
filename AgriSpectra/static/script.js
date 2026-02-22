document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('riskForm');
  const voiceBtn = document.getElementById('voiceCommandBtn');
  const voiceStatus = document.getElementById('voiceStatus');
  const voiceTranscript = document.getElementById('voiceTranscript');
  const languageSelect = document.getElementById('languageSelect');

  const placeInput = document.getElementById('placeInput');
  const latitudeInput = document.getElementById('latitudeInput');
  const longitudeInput = document.getElementById('longitudeInput');
  const regionInput = document.getElementById('regionInput');
  const locationStatus = document.getElementById('locationStatus');
  const showOnMapBtn = document.getElementById('showOnMapBtn');
  const useLocationBtn = document.getElementById('useLocationBtn');
  const googleMapFrame = document.getElementById('googleMapFrame');
  const weatherInputMode = document.getElementById('weatherInputMode');
  const autofillWeatherBtn = document.getElementById('autofillWeatherBtn');
  const checkAlertsBtn = document.getElementById('checkAlertsBtn');
  const temperatureInput = document.getElementById('temperatureInput');
  const humidityInput = document.getElementById('humidityInput');
  const weatherAlertsPanel = document.getElementById('weatherAlertsPanel');

  const ui = {
    setStatus(message) {
      if (voiceStatus) voiceStatus.textContent = message;
    },
    setTranscript(message) {
      if (voiceTranscript) voiceTranscript.textContent = message;
    },
    setListening(listening) {
      if (!voiceBtn) return;
      voiceBtn.classList.toggle('listening', listening);
      voiceBtn.innerHTML = listening
        ? '<i class="fa-solid fa-microphone-lines"></i> Listening...'
        : '<i class="fa-solid fa-microphone"></i> Voice Command';
    },
    setUnsupported() {
      if (!voiceBtn) return;
      voiceBtn.disabled = true;
      voiceBtn.classList.add('unsupported');
      voiceBtn.innerHTML = '<i class="fa-solid fa-microphone-slash"></i> Voice Unsupported';
    },
    setLocation(message, isError = false) {
      if (!locationStatus) return;
      locationStatus.textContent = message;
      locationStatus.classList.toggle('error', !!isError);
    }
  };

  function inferRegion(lat, lon) {
    const latMid = 22.5;
    const lonMid = 82.5;
    if (Number.isNaN(lat) || Number.isNaN(lon)) return 'North';
    if (lat >= latMid && lon >= lonMid) return 'North';
    if (lat < latMid && lon >= lonMid) return 'East';
    if (lat < latMid && lon < lonMid) return 'South';
    return 'West';
  }

  function updateMap(place) {
    if (!googleMapFrame) return;
    const query = encodeURIComponent(place || 'India');
    googleMapFrame.src = `https://maps.google.com/maps?q=${query}&z=7&output=embed`;
  }

  function setLocationDetails({ place, latitude, longitude, region }) {
    if (place && placeInput) placeInput.value = place;
    if (typeof latitude !== 'undefined' && latitudeInput) latitudeInput.value = latitude;
    if (typeof longitude !== 'undefined' && longitudeInput) longitudeInput.value = longitude;

    const latNum = parseFloat(latitudeInput && latitudeInput.value);
    const lonNum = parseFloat(longitudeInput && longitudeInput.value);
    const fallbackRegion = inferRegion(latNum, lonNum);
    if (regionInput) regionInput.value = region || fallbackRegion;
  }

  function setWeatherMode(mode) {
    const manual = mode === 'manual';
    if (temperatureInput) temperatureInput.readOnly = !manual;
    if (humidityInput) humidityInput.readOnly = !manual;
    if (autofillWeatherBtn) autofillWeatherBtn.disabled = manual;
  }

  if (weatherInputMode) {
    setWeatherMode(weatherInputMode.value || 'auto');
    weatherInputMode.addEventListener('change', (ev) => setWeatherMode(ev.target.value));
  }

  if (showOnMapBtn) {
    showOnMapBtn.addEventListener('click', () => {
      const place = (placeInput && placeInput.value ? placeInput.value : 'India').trim();
      updateMap(place);
      ui.setLocation(`Showing "${place}" on Google Map preview.`);
    });
  }

  function playAlertAlarm() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const gain = ctx.createGain();
      gain.connect(ctx.destination);
      gain.gain.value = 0.05;

      [880, 660, 880].forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        osc.type = 'square';
        osc.frequency.value = freq;
        osc.connect(gain);
        const startAt = ctx.currentTime + (idx * 0.25);
        osc.start(startAt);
        osc.stop(startAt + 0.18);
      });
    } catch (_err) {
      // ignore audio errors silently
    }
  }

  function renderWeatherAlerts(data) {
    if (!weatherAlertsPanel) return;
    const alerts = Array.isArray(data.alerts) ? data.alerts : [];
    if (!alerts.length) {
      weatherAlertsPanel.innerHTML = `
        <h4><i class="fa-solid fa-bell"></i> Weather Safety Alerts</h4>
        <p class="weather-alerts-empty">No heavy rain or cyclone risk found in next ${data.forecast_days_checked || 7} days for ${data.place || 'this place'}.</p>
      `;
      return;
    }

    const severeExists = alerts.some((a) => String(a.severity).toUpperCase() === 'SEVERE');
    if (severeExists) {
      playAlertAlarm();
      window.alert('Weather danger alert: Heavy rain/cyclone risk detected. Move produce to safe storage.');
    }

    weatherAlertsPanel.innerHTML = `
      <h4><i class="fa-solid fa-bell"></i> Weather Safety Alerts for ${data.place || 'Selected Place'}</h4>
      <div class="weather-alerts-list">
        ${alerts.map((a) => `
          <article class="weather-alert-card ${String(a.severity || '').toLowerCase()}">
            <div class="weather-alert-headline">${a.headline || 'Weather alert'}</div>
            <div class="weather-alert-details">${a.details || ''}</div>
            <div class="weather-alert-rec"><strong>Recommended action:</strong> ${(Array.isArray(a.recommendations) ? a.recommendations.join(' ') : '')}</div>
          </article>
        `).join('')}
      </div>
    `;
  }

  async function fetchWeatherAverage(payload) {
    const response = await fetch('/api/weather-average', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Unable to fetch weather data.');
    }
    return data;
  }

  async function fetchWeatherAlerts(payload) {
    const response = await fetch('/api/weather-alerts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Unable to fetch weather alerts.');
    }
    return data;
  }

  async function autofillWeatherFromPlace(payload) {
    const data = await fetchWeatherAverage(payload);
    if (temperatureInput) temperatureInput.value = data.avg_temperature;
    if (humidityInput) humidityInput.value = data.avg_humidity;

    setLocationDetails({
      place: data.place,
      latitude: data.latitude,
      longitude: data.longitude,
      region: data.region
    });

    updateMap(data.place || (placeInput ? placeInput.value : 'India'));
    ui.setLocation(
      `Auto-filled 10-day avg: ${data.avg_temperature} C and ${data.avg_humidity}% RH for ${data.place || 'selected place'}.`
    );

    try {
      const alertsData = await fetchWeatherAlerts({
        place: data.place || (placeInput ? placeInput.value : ''),
        latitude: data.latitude,
        longitude: data.longitude
      });
      renderWeatherAlerts(alertsData);
    } catch (_err) {
      // keep silent if alerts request fails during autofill
    }
  }

  if (checkAlertsBtn) {
    checkAlertsBtn.addEventListener('click', async () => {
      try {
        checkAlertsBtn.disabled = true;
        checkAlertsBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Checking...';
        const payload = {
          place: (placeInput && placeInput.value ? placeInput.value : '').trim(),
          latitude: latitudeInput ? latitudeInput.value : '',
          longitude: longitudeInput ? longitudeInput.value : ''
        };
        const data = await fetchWeatherAlerts(payload);
        if (data.latitude && data.longitude) {
          setLocationDetails({
            place: data.place,
            latitude: data.latitude,
            longitude: data.longitude
          });
        }
        renderWeatherAlerts(data);
      } catch (err) {
        if (weatherAlertsPanel) {
          weatherAlertsPanel.innerHTML = `
            <h4><i class="fa-solid fa-bell"></i> Weather Safety Alerts</h4>
            <p class="weather-alerts-empty">${err.message || 'Unable to fetch alerts right now.'}</p>
          `;
        }
      } finally {
        checkAlertsBtn.disabled = false;
        checkAlertsBtn.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Check Heavy Rain / Cyclone Alerts';
      }
    });
  }

  if (autofillWeatherBtn) {
    autofillWeatherBtn.addEventListener('click', async () => {
      try {
        autofillWeatherBtn.disabled = true;
        autofillWeatherBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Fetching...';

        const place = (placeInput && placeInput.value ? placeInput.value : '').trim();
        const latitude = latitudeInput ? latitudeInput.value : '';
        const longitude = longitudeInput ? longitudeInput.value : '';

        await autofillWeatherFromPlace({ place, latitude, longitude });
      } catch (err) {
        ui.setLocation(err.message || 'Unable to auto-fill weather. Use manual input.', true);
      } finally {
        autofillWeatherBtn.innerHTML = '<i class="fa-solid fa-cloud-sun"></i> Auto-fill 10-day Avg Temp/Humidity';
        if (weatherInputMode && weatherInputMode.value === 'auto') {
          autofillWeatherBtn.disabled = false;
        }
      }
    });
  }

  if (useLocationBtn) {
    useLocationBtn.addEventListener('click', async () => {
      if (!navigator.geolocation) {
        ui.setLocation('Geolocation is not supported in this browser.', true);
        return;
      }

      useLocationBtn.disabled = true;
      useLocationBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Detecting...';
      ui.setLocation('Fetching your current location and weather averages...');

      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          try {
            const latitude = pos.coords.latitude;
            const longitude = pos.coords.longitude;
            await autofillWeatherFromPlace({ latitude, longitude, place: placeInput ? placeInput.value : '' });
          } catch (err) {
            ui.setLocation(err.message || 'Unable to auto-fill from current location.', true);
          } finally {
            useLocationBtn.disabled = false;
            useLocationBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Use My Location';
          }
        },
        () => {
          useLocationBtn.disabled = false;
          useLocationBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Use My Location';
          ui.setLocation('Location permission denied. Enter place manually instead.', true);
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    });
  }

  const speech = {
    speak(text) {
      if (!('speechSynthesis' in window) || !text) return;

      const langKey = languageSelect ? languageSelect.value : 'en';
      const voiceLangMap = { en: 'en-IN', hi: 'hi-IN', od: 'or-IN', te: 'te-IN' };
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = voiceLangMap[langKey] || 'en-IN';
      utterance.rate = 1;
      utterance.pitch = 1;

      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    },
    speakRiskSummary(data) {
      if (!data) return;
      const rec = Array.isArray(data.recommendations) && data.recommendations.length
        ? data.recommendations[0]
        : 'Follow recommended storage precautions.';

      const summary = `Risk level ${data.risk_level}. Risk score ${data.risk_score}. Top recommendation: ${rec}`;
      this.speak(summary);
    }
  };

  function renderResult(data) {
    const existing = document.getElementById('clientResult');
    if (existing) existing.remove();

    const container = document.createElement('section');
    container.id = 'clientResult';
    container.className = 'result';
    const levelClass = String(data.risk_level || '').toLowerCase();

    container.innerHTML = `
      <h3>Result - <span class="level ${levelClass}">${data.risk_level}</span></h3>
      <div class="result-grid">
        <div class="score"><canvas id="clientRiskChart" width="160" height="160"></canvas><div class="score-number">${data.risk_score}</div></div>
        <div class="details">
          <h4>Why</h4>
          <p>${data.explanation || ''}</p>
          <h4>Recommendations</h4>
          <ul>${(data.recommendations || []).map((r) => `<li>${r}</li>`).join('')}</ul>
        </div>
      </div>
      <section id="inlineEligibilityResult" class="content-section" style="margin-top:1rem;">
        <h4><i class="fa-solid fa-filter-circle-dollar"></i> Government Support Eligibility</h4>
        <p>Checking eligibility suggestions...</p>
      </section>
    `;

    const main = document.querySelector('main.container');
    if (main) main.appendChild(container);

    if (window.Chart) {
      const chartEl = document.getElementById('clientRiskChart');
      if (chartEl) {
        const ctx = chartEl.getContext('2d');
        const score = Number(data.risk_score) || 0;
        const color = score > 80 ? '#e74c3c' : score > 50 ? '#e67e22' : score > 20 ? '#f1c40f' : '#2ecc71';

        new Chart(ctx, {
          type: 'doughnut',
          data: { datasets: [{ data: [score, 100 - score], backgroundColor: [color, '#ecf0f1'] }] },
          options: { cutout: '70%', plugins: { legend: { display: false } } }
        });
      }
    }
  }

  function renderEligibilityChecks(checks) {
    const list = Array.isArray(checks) ? checks : [];
    return `
      <div class="eligibility-checklist">
        ${list.map((c) => `
          <div class="eligibility-check ${c.met ? 'met' : 'not-met'}">
            <i class="fa-solid ${c.met ? 'fa-circle-check' : 'fa-circle-minus'}"></i>
            <span>${c.label}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  function renderEligibilityCard(scheme) {
    return `
      <article class="eligibility-card">
        <h4><i class="fa-solid ${scheme.icon || 'fa-badge-check'}"></i> ${scheme.name || 'Scheme'}</h4>
        <p><strong>Purpose:</strong> ${scheme.purpose || '-'}</p>
        <p><strong>Why you may be eligible:</strong> ${scheme.why_eligible || '-'}</p>
        <p><strong>Recommended next action:</strong> ${scheme.recommended_next_action || '-'}</p>
        <p><a href="${scheme.official_link || '#'}" target="_blank" rel="noopener noreferrer">Official verification link</a></p>
      </article>
    `;
  }

  function renderEligibilityResult(data) {
    const target = document.getElementById('inlineEligibilityResult');
    if (!target) return;

    const summary = data.input_summary || {};
    const checks = Array.isArray(data.checks) ? data.checks : [];
    const schemes = Array.isArray(data.possible_schemes) ? data.possible_schemes : [];
    const actions = Array.isArray(data.recommended_actions) ? data.recommended_actions : [];

    target.innerHTML = `
      <h4><i class="fa-solid fa-filter-circle-dollar"></i> Government Support Eligibility</h4>
      <p><strong>Crop:</strong> ${summary.crop_type || '-'} |
      <strong>Region:</strong> ${summary.region || '-'} |
      <strong>Risk Level:</strong> ${summary.risk_level || '-'}</p>
      ${renderEligibilityChecks(checks)}
      <div class="eligibility-grid">
        ${schemes.length ? schemes.map(renderEligibilityCard).join('') : '<p>No schemes matched. Please use the dedicated eligibility checker for deeper profiling.</p>'}
      </div>
      <div class="content-section" style="margin-top:1rem;">
        <h4><i class="fa-solid fa-list"></i> Recommended Next Steps</h4>
        <ul>${actions.map((a) => `<li>${a}</li>`).join('')}</ul>
      </div>
      <div class="eligibility-disclaimer">
        <i class="fa-solid fa-circle-exclamation"></i>
        <span>${data.disclaimer || 'This eligibility check is for awareness only and does not guarantee approval. Farmers must verify details on official government portals.'}</span>
      </div>
      <p style="margin-top:0.8rem;">For more personalized eligibility, use the <a href="/calculator">Risk & Eligibility calculator</a>.</p>
    `;
  }

  const riskApi = {
    async computeFromForm(formEl) {
      const fd = new FormData(formEl);
      const payload = {
        crop_type: fd.get('crop_type'),
        place: fd.get('place'),
        latitude: fd.get('latitude'),
        longitude: fd.get('longitude'),
        region: fd.get('region'),
        temperature: fd.get('temperature'),
        humidity: fd.get('humidity'),
        season: fd.get('season'),
        storage_days: fd.get('storage_days')
      };

      const response = await fetch('/api/risk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      return response.json();
    },
    async computeEligibility(payload) {
      const response = await fetch('/api/eligibility', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      return response.json();
    }
  };

  if (form) {
    form.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      try {
        const riskData = await riskApi.computeFromForm(form);
        renderResult(riskData);
        speech.speakRiskSummary(riskData);

        const fd = new FormData(form);
        const eligibilityPayload = {
          crop_type: fd.get('crop_type'),
          place: fd.get('place'),
          latitude: fd.get('latitude'),
          longitude: fd.get('longitude'),
          region: fd.get('region'),
          temperature: fd.get('temperature'),
          humidity: fd.get('humidity'),
          season: fd.get('season'),
          storage_days: fd.get('storage_days'),
          risk_level: riskData.risk_level,
          state: '',
          farmer_category: '',
          landholding_size: ''
        };

        const eligibilityData = await riskApi.computeEligibility(eligibilityPayload);
        renderEligibilityResult(eligibilityData);
      } catch (err) {
        console.error(err);
        alert('Error computing risk');
      }
    });
  }

  const voiceControl = (() => {
    if (!(form && voiceBtn)) return null;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      ui.setUnsupported();
      ui.setStatus('Microphone is not supported in this browser. You can still use manual form input.');
      return null;
    }

    const cropSelect = form.querySelector('select[name="crop_type"]');
    const seasonSelect = form.querySelector('select[name="season"]');
    const daysInput = form.querySelector('input[name="storage_days"]');

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;

    let listening = false;

    const cropMap = {
      wheat: 'Wheat',
      paddy: 'Paddy',
      rice: 'Rice',
      mustard: 'Mustard',
      sugarcane: 'Sugarcane',
      pepper: 'Black Pepper',
      'black pepper': 'Black Pepper',
      coffee: 'Coffee',
      banana: 'Banana',
      potato: 'Potato',
      onion: 'Onion',
      groundnut: 'Groundnut',
      bajra: 'Bajra'
    };

    const seasonMap = {
      summer: 'Summer',
      monsoon: 'Monsoon',
      winter: 'Winter',
      'post harvest': 'Post-harvest',
      postharvest: 'Post-harvest'
    };

    function setSelectValue(selectEl, value) {
      if (!selectEl) return false;
      for (const opt of selectEl.options) {
        if (String(opt.value).toLowerCase() === String(value).toLowerCase()) {
          opt.selected = true;
          return true;
        }
      }
      return false;
    }

    function setByKeyword(selectEl, keywordMap, transcript) {
      for (const key of Object.keys(keywordMap)) {
        if (transcript.includes(key)) {
          return setSelectValue(selectEl, keywordMap[key]);
        }
      }
      return false;
    }

    function parseNumber(transcript, patterns) {
      for (const pattern of patterns) {
        const match = transcript.match(pattern);
        if (match) return match[1];
      }
      return null;
    }

    function parseLocation(transcript) {
      const patterns = [
        /location(?:\s+is)?\s+([a-zA-Z\s]+)/,
        /place(?:\s+is)?\s+([a-zA-Z\s]+)/,
        /city(?:\s+is)?\s+([a-zA-Z\s]+)/
      ];
      for (const pattern of patterns) {
        const match = transcript.match(pattern);
        if (match && match[1]) return match[1].trim();
      }
      return null;
    }

    function handleCommand(transcript) {
      const t = String(transcript || '').toLowerCase();
      const updated = [];

      if (setByKeyword(cropSelect, cropMap, t)) updated.push('crop');
      if (setByKeyword(seasonSelect, seasonMap, t)) updated.push('season');

      const spokenLocation = parseLocation(t);
      if (spokenLocation && placeInput) {
        placeInput.value = spokenLocation;
        updateMap(spokenLocation);
        updated.push('place');
      }

      const temp = parseNumber(t, [
        /temperature(?:\s+is)?\s+(-?\d+(\.\d+)?)/,
        /(-?\d+(\.\d+)?)\s*(degrees|degree)/
      ]);
      if (temp && temperatureInput) {
        temperatureInput.value = temp;
        updated.push('temperature');
      }

      const humidity = parseNumber(t, [
        /humidity(?:\s+is)?\s+(\d+(\.\d+)?)/,
        /(\d+(\.\d+)?)\s*(percent|percentage)/
      ]);
      if (humidity && humidityInput) {
        humidityInput.value = humidity;
        updated.push('humidity');
      }

      const days = parseNumber(t, [
        /(?:storage duration|duration|storage days|days|day)(?:\s+is)?\s+(\d+)/,
        /(\d+)\s*days?/
      ]);
      if (days && daysInput) {
        daysInput.value = days;
        updated.push('storage duration');
      }

      if (t.includes('reset form') || t.includes('clear form')) {
        form.reset();
        setWeatherMode((weatherInputMode && weatherInputMode.value) || 'auto');
        ui.setStatus('Form reset by voice command.');
        ui.setLocation('Form reset. Choose a place in India for map and weather autofill.');
        return;
      }

      if (t.includes('autofill weather') || t.includes('auto fill weather')) {
        if (autofillWeatherBtn && !autofillWeatherBtn.disabled) {
          autofillWeatherBtn.click();
          ui.setStatus('Fetching weather averages...');
        } else {
          ui.setStatus('Weather autofill is disabled in manual mode.');
        }
        return;
      }

      if (t.includes('calculate risk') || t.includes('check risk') || t.includes('submit')) {
        ui.setStatus('Command received. Calculating risk now...');
        form.requestSubmit();
        return;
      }

      if (updated.length) {
        ui.setStatus(`Updated fields: ${updated.join(', ')}.`);
      } else {
        ui.setStatus('No matching command found. Please try again.');
      }
    }

    recognition.onstart = () => {
      listening = true;
      ui.setListening(true);
      ui.setStatus('Listening... Speak now in English or your selected language.');
      ui.setTranscript('...');
    };

    recognition.onend = () => {
      listening = false;
      ui.setListening(false);
    };

    recognition.onerror = (event) => {
      ui.setListening(false);
      ui.setStatus(`Voice error: ${event.error}. You can continue with manual input.`);
    };

    recognition.onresult = (event) => {
      let finalText = '';
      let interimText = '';

      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const txt = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += `${txt} `;
        else interimText += `${txt} `;
      }

      const live = `${finalText}${interimText}`.trim();
      if (live) ui.setTranscript(live);
      if (finalText.trim()) handleCommand(finalText.trim());
    };

    function currentRecognitionLang() {
      const key = languageSelect ? languageSelect.value : 'en';
      const map = { en: 'en-IN', hi: 'hi-IN', od: 'or-IN', te: 'te-IN' };
      return map[key] || 'en-IN';
    }

    voiceBtn.addEventListener('click', () => {
      if (listening) {
        recognition.stop();
        ui.setStatus('Listening stopped.');
        return;
      }

      recognition.lang = currentRecognitionLang();
      try {
        recognition.start();
      } catch (_err) {
        ui.setStatus('Voice engine is busy. Please wait and try again.');
      }
    });

    return { start: () => voiceBtn.click() };
  })();

  if (voiceControl) {
    ui.setStatus('Voice ready. Use microphone for hands-free form filling and risk calculation.');
  }
});
