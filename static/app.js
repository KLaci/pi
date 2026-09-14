(function () {
  const $ = (id) => document.getElementById(id);
  let state = null;
  let editing = null; // uid whose name input has focus, skip re-render of that input

  function toast(msg) {
    const t = $("toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove("show"), 2500);
  }

  async function api(method, url, body, isForm) {
    const opts = { method };
    if (body) {
      opts.body = isForm ? body : JSON.stringify(body);
      if (!isForm) opts.headers = { "Content-Type": "application/json" };
    }
    const res = await fetch(url, opts);
    let data = {};
    try { data = await res.json(); } catch (e) { /* no body */ }
    if (!res.ok) throw new Error(data.error || ("Request failed (" + res.status + ")"));
    return data;
  }

  const cardUrl = (uid, tail) => "/api/cards/" + encodeURIComponent(uid) + tail;

  function fmtSize(n) {
    if (n == null) return "";
    return n >= 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.round(n / 1024) + " KB";
  }

  function fmtTs(iso) {
    if (!iso) return "never";
    const d = new Date(iso);
    const today = new Date();
    const time = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    if (d.toDateString() === today.toDateString()) return time;
    return d.toLocaleDateString([], { month: "short", day: "numeric" }) + " " + time;
  }

  function cardName(uid) {
    const c = state && state.cards.find((x) => x.uid === uid);
    return c && c.name ? c.name + " (" + uid + ")" : uid;
  }

  function el(tag, attrs, children) {
    const e = document.createElement(tag);
    for (const k in attrs || {}) {
      if (k === "class") e.className = attrs[k];
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), attrs[k]);
      else if (k === "text") e.textContent = attrs[k];
      else e.setAttribute(k, attrs[k]);
    }
    for (const c of children || []) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    return e;
  }

  function renderBanner() {
    const now = state.now;
    const dot = $("dot");
    dot.className = "dot" + (now.now_playing ? " on" : now.card_present ? " present" : "");
    $("now").textContent = now.now_playing
      ? cardName(now.now_playing) + (now.source === "dashboard" ? " (test play)" : "")
      : "Idle";
    $("present").textContent = now.card_present || "None";
    $("stopBtn").disabled = !now.now_playing;
  }

  function uploadControl(card) {
    const input = el("input", { type: "file", accept: ".mp3,audio/mpeg", hidden: "" });
    const btn = el("button", { class: card.assigned ? "" : "primary",
      text: card.assigned ? "Replace mp3" : "Upload mp3", onclick: () => input.click() });
    input.addEventListener("change", async () => {
      if (!input.files.length) return;
      const fd = new FormData();
      fd.append("file", input.files[0]);
      btn.disabled = true;
      btn.textContent = "Uploading...";
      try {
        await api("POST", cardUrl(card.uid, "/file"), fd, true);
        toast("Uploaded " + input.files[0].name);
        await refresh();
      } catch (e) {
        toast(e.message);
        btn.disabled = false;
        btn.textContent = card.assigned ? "Replace mp3" : "Upload mp3";
      }
    });
    return [btn, input];
  }

  function renderCards() {
    const tbody = $("cards");
    tbody.innerHTML = "";
    $("cardsEmpty").hidden = state.cards.length > 0;
    for (const card of state.cards) {
      const nameInput = el("input", { type: "text", value: card.name || "", placeholder: "Add a name",
        maxlength: "60",
        onfocus: () => { editing = card.uid; },
        onblur: async (ev) => {
          editing = null;
          const v = ev.target.value.trim();
          if (v === (card.name || "")) return;
          try { await api("POST", cardUrl(card.uid, "/name"), { name: v }); toast("Name saved"); await refresh(); }
          catch (e) { toast(e.message); }
        },
        onkeydown: (ev) => { if (ev.key === "Enter") ev.target.blur(); } });

      const fileCell = card.assigned
        ? el("div", {}, [
            el("span", { class: "badge ok", text: "assigned" }),
            el("div", { class: "muted", text: (card.original_filename || card.uid + ".mp3") + " " + fmtSize(card.file_size) }),
            el("audio", { controls: "", preload: "none", src: cardUrl(card.uid, "/file") + "?v=" + encodeURIComponent(card.file_mtime || "") }),
          ])
        : el("span", { class: "badge none", text: "no file" });

      const actions = el("div", { class: "actions" }, uploadControl(card));
      if (card.assigned) {
        actions.appendChild(el("button", { text: "Play test", onclick: async () => {
          try { await api("POST", cardUrl(card.uid, "/play")); toast("Playing " + cardName(card.uid)); await refresh(); }
          catch (e) { toast(e.message); }
        } }));
        actions.appendChild(el("button", { class: "danger", text: "Remove", onclick: async () => {
          if (!confirm("Remove the mp3 for " + cardName(card.uid) + "?")) return;
          try { await api("DELETE", cardUrl(card.uid, "/file")); toast("File removed"); await refresh(); }
          catch (e) { toast(e.message); }
        } }));
      }

      const isNow = state.now.card_present === card.uid;
      tbody.appendChild(el("tr", {}, [
        el("td", { class: "uid" }, [card.uid + (isNow ? " *" : "")]),
        el("td", { "data-label": "Name" }, [nameInput]),
        el("td", { "data-label": "File" }, [fileCell]),
        el("td", { class: "hide", "data-label": "Taps", text: String(card.taps) }),
        el("td", { class: "hide muted", "data-label": "Last seen", text: fmtTs(card.last_seen) }),
        el("td", {}, [actions]),
      ]));
    }
  }

  function describe(ev) {
    switch (ev.type) {
      case "tap": return ev.action === "played" ? "played" : ev.action === "no_file" ? "no file" : "no speaker";
      case "stop": return "stopped";
      case "upload": return "uploaded " + (ev.filename || "");
      case "remove": return "file removed";
      case "rename": return "renamed to " + (ev.name || "(empty)");
      case "test_play": return "test play";
      default: return ev.type;
    }
  }

  function renderEvents() {
    const ul = $("events");
    ul.innerHTML = "";
    $("eventsEmpty").hidden = state.events.length > 0;
    for (const ev of state.events.slice(0, 100)) {
      const cls = ev.type === "tap" ? ev.action : ev.type;
      ul.appendChild(el("li", {}, [
        el("span", { class: "ts", text: fmtTs(ev.ts) }),
        el("span", { class: "type " + cls, text: describe(ev) }),
        el("span", { class: "uid", text: cardName(ev.uid) }),
      ]));
    }
  }

  async function refresh() {
    try {
      state = await api("GET", "/api/state");
    } catch (e) {
      $("now").textContent = "Server unreachable";
      return;
    }
    $("dev").hidden = state.mode !== "dev";
    renderBanner();
    if (!editing) renderCards();
    renderEvents();
  }

  $("stopBtn").addEventListener("click", async () => {
    try { await api("POST", "/api/stop"); await refresh(); } catch (e) { toast(e.message); }
  });
  $("devTap").addEventListener("click", async () => {
    try {
      await api("POST", "/api/dev/tap", { uid: $("devUid").value.trim(), hold: Number($("devHold").value) || 4 });
      toast("Tap simulated");
      setTimeout(refresh, 400);
    } catch (e) { toast(e.message); }
  });
  $("devRelease").addEventListener("click", async () => {
    try { await api("POST", "/api/dev/release"); setTimeout(refresh, 1200); } catch (e) { toast(e.message); }
  });

  refresh();
  setInterval(refresh, 2000);
})();
