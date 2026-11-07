(() => {
  const stations = Array.isArray(window.STATIONS) ? window.STATIONS : [];
  const shell = document.querySelector(".shell");
  const freqEl = document.getElementById("freq");
  const nameEl = document.getElementById("name");
  const statusEl = document.getElementById("status");
  const powerBtn = document.getElementById("power");
  const prevBtn = document.getElementById("prev");
  const nextBtn = document.getElementById("next");
  const streamEl = document.getElementById("stream");
  const staticEl = document.getElementById("static");
  const listbox = document.getElementById("station-listbox");
  const countEl = document.getElementById("station-count");

  const TUNE_TIMEOUT_MS = 12000;

  let index = 0;
  let powered = false;
  let tuning = false;
  let tuneToken = 0;
  let tuneTimer = null;
  let hls = null;
  let listButtons = [];

  function station() {
    return stations[index] || null;
  }

  function formatFreq(value) {
    if (value == null || Number.isNaN(Number(value))) return "—.—";
    return Number(value).toFixed(1);
  }

  function setStatus(text) {
    statusEl.textContent = text;
  }

  function setTuning(on) {
    tuning = on;
    shell.dataset.tuning = on ? "1" : "0";
  }

  function stopStatic() {
    staticEl.pause();
    try {
      staticEl.currentTime = 0;
    } catch (_) {
      /* ignore */
    }
  }

  function playStatic() {
    staticEl.volume = 0.55;
    const p = staticEl.play();
    if (p && typeof p.catch === "function") p.catch(() => {});
  }

  function destroyHls() {
    if (hls) {
      try {
        hls.destroy();
      } catch (_) {
        /* ignore */
      }
      hls = null;
    }
  }

  function stopStream() {
    destroyHls();
    streamEl.removeAttribute("src");
    streamEl.load();
  }

  function clearTuneTimer() {
    if (tuneTimer) {
      clearTimeout(tuneTimer);
      tuneTimer = null;
    }
  }

  function highlightList() {
    listButtons.forEach((btn, i) => {
      const selected = i === index;
      btn.setAttribute("aria-selected", selected ? "true" : "false");
      if (selected && listbox) {
        const btnTop = btn.offsetTop;
        const btnBottom = btnTop + btn.offsetHeight;
        const viewTop = listbox.scrollTop;
        const viewBottom = viewTop + listbox.clientHeight;
        if (btnTop < viewTop) listbox.scrollTop = btnTop - 8;
        else if (btnBottom > viewBottom) listbox.scrollTop = btnBottom - listbox.clientHeight + 8;
      }
    });
  }

  function updateDisplay() {
    const s = station();
    highlightList();
    if (!powered) {
      freqEl.textContent = "—.—";
      nameEl.textContent = "Radio apagada";
      setStatus("Encendé para sintonizar");
      return;
    }
    if (!s) {
      freqEl.textContent = "—.—";
      nameEl.textContent = "Sin estaciones";
      setStatus("No hay playlist cargada");
      return;
    }
    freqEl.textContent = formatFreq(s.freq);
    nameEl.textContent = s.name;
  }

  function buildList() {
    if (!listbox || !countEl) return;
    countEl.textContent = String(stations.length);
    listbox.replaceChildren();
    listButtons = stations.map((s, i) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "station-list__item";
      btn.setAttribute("role", "option");
      btn.setAttribute("aria-selected", i === index ? "true" : "false");
      btn.innerHTML =
        `<span class="station-list__freq">${formatFreq(s.freq)}</span>` +
        `<span class="station-list__name"></span>`;
      btn.querySelector(".station-list__name").textContent = s.name;
      btn.addEventListener("click", () => selectStation(i));
      listbox.appendChild(btn);
      return btn;
    });
  }

  function selectStation(i) {
    if (i < 0 || i >= stations.length) return;
    index = i;
    updateDisplay();
    if (!powered) {
      powerOn();
      return;
    }
    tune("seek");
  }

  function setPowered(on) {
    powered = on;
    shell.dataset.power = on ? "on" : "off";
    powerBtn.setAttribute("aria-pressed", on ? "true" : "false");
    prevBtn.disabled = !on || stations.length < 2;
    nextBtn.disabled = !on || stations.length < 2;
  }

  function isHlsUrl(url) {
    return /\.m3u8(\?|$)/i.test(url || "");
  }

  function attachNative(url) {
    streamEl.src = url;
    streamEl.load();
    return streamEl.play();
  }

  function attachHls(url) {
    if (window.Hls && window.Hls.isSupported()) {
      destroyHls();
      hls = new window.Hls({ enableWorker: true });
      hls.loadSource(url);
      hls.attachMedia(streamEl);
      return new Promise((resolve, reject) => {
        hls.on(window.Hls.Events.MANIFEST_PARSED, () => {
          streamEl.play().then(resolve).catch(reject);
        });
        hls.on(window.Hls.Events.ERROR, (_e, data) => {
          if (data && data.fatal) reject(new Error(data.type || "hls error"));
        });
      });
    }
    if (streamEl.canPlayType("application/vnd.apple.mpegurl")) {
      return attachNative(url);
    }
    return Promise.reject(new Error("HLS no soportado"));
  }

  function onStreamReady(token) {
    if (token !== tuneToken || !powered) return;
    clearTuneTimer();
    stopStatic();
    setTuning(false);
    const s = station();
    setStatus(s ? "Al aire" : "Listo");
  }

  function onStreamFail(token, reason) {
    if (token !== tuneToken || !powered) return;
    clearTuneTimer();
    stopStatic();
    setTuning(false);
    stopStream();
    setStatus(reason || "No se pudo sintonizar");
  }

  function tune(reason) {
    if (!powered) return;
    const s = station();
    if (!s || !s.url) {
      setStatus("Estación sin URL");
      return;
    }

    const token = ++tuneToken;
    clearTuneTimer();
    stopStream();
    updateDisplay();
    setTuning(true);
    playStatic();
    setStatus(reason === "seek" ? "Sintonizando…" : "Encendiendo…");

    tuneTimer = setTimeout(() => {
      onStreamFail(token, "Sin señal (timeout)");
    }, TUNE_TIMEOUT_MS);

    const start = isHlsUrl(s.url) ? attachHls(s.url) : attachNative(s.url);

    Promise.resolve(start)
      .then(() => {
        if (token !== tuneToken) return;
        // playing started; wait briefly for actual playback if needed
        if (!streamEl.paused) {
          onStreamReady(token);
          return;
        }
        const onPlaying = () => {
          streamEl.removeEventListener("playing", onPlaying);
          onStreamReady(token);
        };
        streamEl.addEventListener("playing", onPlaying);
      })
      .catch(() => {
        onStreamFail(token, "Sin señal");
      });
  }

  function powerOn() {
    if (!stations.length) {
      setPowered(false);
      updateDisplay();
      setStatus("No hay estaciones en stations.js");
      return;
    }
    setPowered(true);
    updateDisplay();
    tune("power");
  }

  function powerOff() {
    tuneToken += 1;
    clearTuneTimer();
    setTuning(false);
    stopStatic();
    stopStream();
    setPowered(false);
    updateDisplay();
  }

  function togglePower() {
    if (powered) powerOff();
    else powerOn();
  }

  function seek(delta) {
    if (!powered || stations.length < 2) return;
    index = (index + delta + stations.length) % stations.length;
    updateDisplay();
    tune("seek");
  }

  powerBtn.addEventListener("click", togglePower);
  prevBtn.addEventListener("click", () => seek(-1));
  nextBtn.addEventListener("click", () => seek(1));

  streamEl.addEventListener("error", () => {
    if (!powered || !tuning) return;
    onStreamFail(tuneToken, "Sin señal");
  });

  document.addEventListener("keydown", (e) => {
    if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    if (e.code === "Space") {
      e.preventDefault();
      togglePower();
    } else if (e.code === "ArrowLeft") {
      e.preventDefault();
      seek(-1);
    } else if (e.code === "ArrowRight") {
      e.preventDefault();
      seek(1);
    }
  });

  // Initial UI
  buildList();
  setPowered(false);
  updateDisplay();
  if (!stations.length) {
    setStatus("No hay estaciones en stations.js");
  }
})();
