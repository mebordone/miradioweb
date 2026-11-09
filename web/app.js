(() => {
  const stations = Array.isArray(window.STATIONS) ? window.STATIONS : [];
  const TUNE_TIMEOUT_MS = 12_000;
  const VOLUME_KEY = "dialfm-volume";

  const elements = {
    shell: document.querySelector(".shell"),
    frequency: document.getElementById("freq"),
    stationName: document.getElementById("name"),
    status: document.getElementById("status"),
    power: document.getElementById("power"),
    previous: document.getElementById("prev"),
    next: document.getElementById("next"),
    stream: document.getElementById("stream"),
    static: document.getElementById("static"),
    volume: document.getElementById("volume"),
    list: document.getElementById("station-listbox"),
    stationCount: document.getElementById("station-count"),
    bars: Array.from(document.querySelectorAll(".display__bars span")),
  };

  const state = {
    index: 0,
    powered: false,
    tuning: false,
    tuneId: 0,
    tuneTimer: null,
    hls: null,
    volume: readVolume(),
  };

  const ui = createUi(elements, stations);
  const audio = createAudioPlayer(elements, state);
  const visualizer = createVisualizer(elements.bars);

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function readVolume() {
    try {
      const saved = Number(localStorage.getItem(VOLUME_KEY));
      return Number.isFinite(saved) ? clamp(saved, 0, 100) : 80;
    } catch (_) {
      return 80;
    }
  }

  function currentStation() {
    return stations[state.index] || null;
  }

  function updateUi() {
    const station = currentStation();
    const playing = state.powered && (state.tuning || audio.isPlaying());

    elements.shell.dataset.power = state.powered ? "on" : "off";
    elements.shell.dataset.tuning = state.tuning ? "1" : "0";
    elements.shell.dataset.playing = playing ? "1" : "0";
    elements.power.setAttribute("aria-pressed", String(state.powered));
    elements.previous.disabled = !state.powered || stations.length < 2;
    elements.next.disabled = !state.powered || stations.length < 2;
    elements.volume.disabled = !state.powered;

    ui.setSelected(state.index);

    if (!state.powered) {
      ui.showStation(null);
      ui.setStatus("Encendé para sintonizar");
      return;
    }

    if (!station) {
      ui.showStation(null, "Sin estaciones");
      ui.setStatus("No hay playlist cargada");
      return;
    }

    ui.showStation(station);
  }

  function setTuning(tuning) {
    state.tuning = tuning;
    updateUi();
  }

  function clearTuneTimer() {
    clearTimeout(state.tuneTimer);
    state.tuneTimer = null;
  }

  function finishTuning(tuneId) {
    if (tuneId !== state.tuneId || !state.powered) return;

    clearTuneTimer();
    audio.stopStatic();
    setTuning(false);
    ui.setStatus("Al aire");
    visualizer.start();
    updateUi();
  }

  function failTuning(tuneId, status = "Sin señal") {
    if (tuneId !== state.tuneId || !state.powered) return;

    clearTuneTimer();
    audio.stopStatic();
    audio.stopStream();
    setTuning(false);
    ui.setStatus(status);
    visualizer.stop();
    updateUi();
  }

  function tune(status) {
    const station = currentStation();
    if (!state.powered || !station?.url) {
      ui.setStatus("Estación sin URL");
      return;
    }

    const tuneId = ++state.tuneId;
    clearTuneTimer();
    audio.stopStream();
    audio.playStatic();
    setTuning(true);
    ui.setStatus(status);
    visualizer.start();

    state.tuneTimer = setTimeout(
      () => failTuning(tuneId, "Sin señal (timeout)"),
      TUNE_TIMEOUT_MS,
    );

    audio.playStream(station.url).then(
      () => finishTuning(tuneId),
      () => failTuning(tuneId),
    );
  }

  function powerOn() {
    if (!stations.length) {
      ui.setStatus("No hay estaciones en stations.js");
      return;
    }

    state.powered = true;
    updateUi();
    tune("Encendiendo…");
  }

  function powerOff() {
    state.tuneId += 1;
    clearTuneTimer();
    state.powered = false;
    state.tuning = false;
    audio.stop();
    visualizer.stop();
    updateUi();
  }

  function togglePower() {
    if (state.powered) powerOff();
    else powerOn();
  }

  function selectStation(index, status = "Sintonizando…") {
    if (index < 0 || index >= stations.length) return;

    state.index = index;
    updateUi();
    if (state.powered) tune(status);
    else powerOn();
  }

  function moveStation(direction) {
    if (!state.powered || stations.length < 2) return;
    selectStation((state.index + direction + stations.length) % stations.length);
  }

  function bindEvents() {
    elements.power.addEventListener("click", togglePower);
    elements.previous.addEventListener("click", () => moveStation(-1));
    elements.next.addEventListener("click", () => moveStation(1));
    elements.volume.addEventListener("input", () => {
      state.volume = Number(elements.volume.value);
      audio.setVolume(state.volume);
      try {
        localStorage.setItem(VOLUME_KEY, String(state.volume));
      } catch (_) {
        /* The player still works when browser storage is unavailable. */
      }
    });

    elements.stream.addEventListener("error", () => {
      if (state.powered && state.tuning) failTuning(state.tuneId);
    });

    document.addEventListener("keydown", (event) => {
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(event.target?.tagName)) return;

      if (event.code === "Space") {
        event.preventDefault();
        togglePower();
      } else if (event.code === "ArrowLeft") {
        event.preventDefault();
        moveStation(-1);
      } else if (event.code === "ArrowRight") {
        event.preventDefault();
        moveStation(1);
      }
    });
  }

  function createUi(dom, radioStations) {
    const buttons = radioStations.map((station, index) => {
      const button = document.createElement("button");
      const frequency = document.createElement("span");
      const name = document.createElement("span");

      button.type = "button";
      button.className = "station-list__item";
      button.setAttribute("role", "option");
      frequency.className = "station-list__freq";
      frequency.textContent = formatFrequency(station.freq);
      name.className = "station-list__name";
      name.textContent = station.name;
      button.append(frequency, name);
      button.addEventListener("click", () => selectStation(index));
      dom.list.append(button);
      return button;
    });

    dom.stationCount.textContent = String(radioStations.length);
    dom.volume.value = String(state.volume);

    return {
      setStatus(text) {
        dom.status.textContent = text;
      },
      showStation(station, offName = "Radio apagada") {
        dom.frequency.textContent = station ? formatFrequency(station.freq) : "—.—";
        dom.stationName.textContent = station ? station.name : offName;
      },
      setSelected(index) {
        buttons.forEach((button, buttonIndex) => {
          const selected = buttonIndex === index;
          button.setAttribute("aria-selected", String(selected));
          if (selected) keepVisible(button, dom.list);
        });
      },
    };
  }

  function keepVisible(element, container) {
    const top = element.offsetTop;
    const bottom = top + element.offsetHeight;
    if (top < container.scrollTop) container.scrollTop = top - 8;
    if (bottom > container.scrollTop + container.clientHeight) {
      container.scrollTop = bottom - container.clientHeight + 8;
    }
  }

  function formatFrequency(value) {
    return Number(value).toFixed(1);
  }

  function createAudioPlayer(dom, playerState) {
    function clearHls() {
      playerState.hls?.destroy();
      playerState.hls = null;
    }

    function setVolume(percent) {
      const volume = clamp(percent / 100, 0, 1);
      dom.stream.volume = volume;
      dom.static.volume = volume * 0.7;
    }

    function stopStatic() {
      dom.static.pause();
      dom.static.currentTime = 0;
    }

    function stopStream() {
      clearHls();
      dom.stream.pause();
      dom.stream.removeAttribute("src");
      dom.stream.load();
    }

    function stop() {
      stopStatic();
      stopStream();
    }

    function playStatic() {
      setVolume(playerState.volume);
      dom.static.play().catch(() => {});
    }

    function playNative(url) {
      dom.stream.src = url;
      dom.stream.load();
      setVolume(playerState.volume);
      return dom.stream.play();
    }

    function playHls(url) {
      if (window.Hls?.isSupported()) {
        clearHls();
        playerState.hls = new window.Hls({ enableWorker: true });
        playerState.hls.loadSource(url);
        playerState.hls.attachMedia(dom.stream);

        return new Promise((resolve, reject) => {
          playerState.hls.on(window.Hls.Events.MANIFEST_PARSED, () => {
            setVolume(playerState.volume);
            dom.stream.play().then(resolve, reject);
          });
          playerState.hls.on(window.Hls.Events.ERROR, (_event, data) => {
            if (data?.fatal) reject(new Error(data.type));
          });
        });
      }

      if (dom.stream.canPlayType("application/vnd.apple.mpegurl")) {
        return playNative(url);
      }
      return Promise.reject(new Error("HLS no soportado"));
    }

    return {
      isPlaying: () => !dom.stream.paused || !dom.static.paused,
      setVolume,
      stop,
      stopStatic,
      stopStream,
      playStatic,
      playStream: (url) => (
        /\.m3u8(\?|$)/i.test(url) ? playHls(url) : playNative(url)
      ),
    };
  }

  function createVisualizer(bars) {
    const minHeight = 6;
    const maxHeight = 26;
    let animationFrame = null;
    let lastTime = 0;
    let levels = bars.map(() => 0.2);

    function draw(values) {
      bars.forEach((bar, index) => {
        const level = clamp(values[index] || 0, 0, 1);
        bar.style.height = `${minHeight + level * (maxHeight - minHeight)}px`;
        bar.style.opacity = String(0.45 + level * 0.55);
      });
    }

    function tick(time) {
      const elapsed = Math.min(50, time - lastTime || 16);
      lastTime = time;
      levels = levels.map((level, index) => {
        const target = 0.25 + Math.random() * 0.75;
        const speed = 0.08 + (index % 3) * 0.03;
        return level + (target - level) * Math.min(1, speed * elapsed / 16);
      });
      draw(levels.map((level, index) => (
        level * (0.85 + 0.15 * Math.sin(index + time / 180))
      )));
      animationFrame = requestAnimationFrame(tick);
    }

    return {
      start() {
        if (animationFrame) return;
        lastTime = 0;
        animationFrame = requestAnimationFrame(tick);
      },
      stop() {
        cancelAnimationFrame(animationFrame);
        animationFrame = null;
        draw(bars.map(() => 0.08));
      },
    };
  }

  audio.setVolume(state.volume);
  ui.showStation(null);
  ui.setStatus(stations.length ? "Encendé para sintonizar" : "No hay estaciones en stations.js");
  visualizer.stop();
  updateUi();
  bindEvents();
})();
