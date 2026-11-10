/* UniRed: interacciones compartidas. */
(() => {
  const csrf = document.querySelector('meta[name="csrf"]')?.content || "";
  window.UNIRED = { csrf };

  // Todo formulario POST lleva el token CSRF (incluidos los del panel original).
  document.querySelectorAll('form[method="post" i]').forEach(f => {
    if (!f.querySelector('input[name="csrf"]')) {
      const i = document.createElement("input");
      i.type = "hidden"; i.name = "csrf"; i.value = csrf; f.prepend(i);
    }
  });

  // ---------- avisos: se ocultan solos ----------
  document.querySelectorAll(".aviso").forEach((a, i) => setTimeout(() => a.remove(), 5200 + i * 600));

  // ---------- pantalla de carga (logo animado) ----------
  const carga = document.getElementById("carga");
  const reducir = matchMedia("(prefers-reduced-motion: reduce)").matches;
  function cerrarCarga() {
    if (!carga || carga.hidden) return;
    carga.classList.add("saliendo");
    setTimeout(() => { carga.hidden = true; carga.classList.remove("saliendo"); carga.querySelector("video")?.pause(); }, 520);
  }
  // Muestra la animación mientras algo tarda. Devuelve una función para cerrarla.
  window.UNIRED.cargando = (texto = "") => {
    if (!carga || reducir) return cerrarCarga;
    const v = carga.querySelector("video");
    carga.querySelector("[data-carga-texto]").textContent = texto;
    carga.hidden = false; v.loop = false; v.currentTime = 0; v.play().catch(() => {});
    v.onended = () => { v.currentTime = 6.2; v.play().catch(() => {}); };  // se queda en el logo animando
    return cerrarCarga;
  };
  if (carga && carga.classList.contains("intro")) {
    const v = carga.querySelector("video");
    if (reducir) carga.hidden = true;
    else {
      v.addEventListener("ended", cerrarCarga);
      v.addEventListener("error", cerrarCarga);
      setTimeout(cerrarCarga, 9500);
      v.play().catch(cerrarCarga);
    }
    carga.querySelector("[data-carga-saltar]")?.addEventListener("click", cerrarCarga);
    document.addEventListener("keydown", e => { if (e.key === "Escape") cerrarCarga(); });
  }
  // Subir un video puede tardar: se muestra la animación hasta que el servidor responde.
  document.querySelectorAll("form[enctype='multipart/form-data']").forEach(f => f.addEventListener("submit", () => {
    const a = f.querySelector("input[type=file]")?.files?.[0];
    if (a && (a.type.startsWith("video") || a.size > 4e6)) window.UNIRED.cargando("Subiendo " + (a.type.startsWith("video") ? "tu video" : "el archivo") + "…");
  }));

  // ---------- «Ver Cypher» ----------
  const panel = document.getElementById("cy-panel");
  const velo = document.querySelector(".cy-velo");
  const KW = /\b(MATCH|OPTIONAL|WHERE|RETURN|WITH|CREATE|MERGE|SET|DELETE|DETACH|REMOVE|ORDER BY|ORDER|BY|LIMIT|SKIP|UNWIND|AS|AND|OR|NOT|IN|IS|NULL|CASE|WHEN|THEN|ELSE|END|DISTINCT|COUNT|COLLECT|EXISTS|CALL|YIELD|UNION|ALL|ON|FOREACH|DESC|ASC|shortestPath|SHOW|CONSTRAINTS|true|false|count|collect|size|round|toLower|coalesce|datetime|date|duration|labels|type|nodes|relationships|length|left|toString|toInteger|elementId)\b/g;
  function resaltar(pre) {
    const esc = s => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const tokens = [];
    let t = pre.textContent
      .replace(/\/\/[^\n]*/g, m => `\u0000${tokens.push(`<span class="cy-com">${esc(m)}</span>`) - 1}\u0000`)
      .replace(/'(?:[^'\\]|\\.)*'/g, m => `\u0000${tokens.push(`<span class="cy-str">${esc(m)}</span>`) - 1}\u0000`);
    t = esc(t)
      .replace(/\[:?([A-Z_|]+)(\*[^\]]*)?\]/g, (m) => `<span class="cy-rel">${m}</span>`)
      .replace(/-\[(\w+):([A-Z_|]+)/g, (m, v, r) => `-[${v}:<span class="cy-rel">${r}</span>`)
      .replace(/(\(|\s)(\w*):([A-Z][a-zA-Z]+)/g, (m, a, v, l) => `${a}${v}:<span class="cy-lbl">${l}</span>`)
      .replace(/\$\w+/g, m => `<span class="cy-par">${m}</span>`)
      .replace(KW, m => `<span class="cy-kw">${m}</span>`);
    pre.innerHTML = t.replace(/\u0000(\d+)\u0000/g, (m, i) => tokens[+i]);
  }
  let resaltado = false;
  function abrir() {
    if (!panel) return;
    if (!resaltado) { panel.querySelectorAll("pre.cy").forEach(resaltar); resaltado = true; }
    panel.classList.add("abierto"); panel.setAttribute("aria-hidden", "false"); velo.hidden = false;
    panel.querySelector("[data-cy-cerrar]")?.focus();
  }
  function cerrar() {
    if (!panel) return;
    panel.classList.remove("abierto"); panel.setAttribute("aria-hidden", "true"); velo.hidden = true;
  }
  document.querySelectorAll("[data-cy-abrir]").forEach(b => b.addEventListener("click", abrir));
  document.querySelectorAll("[data-cy-cerrar]").forEach(b => b.addEventListener("click", cerrar));
  document.addEventListener("keydown", e => { if (e.key === "Escape") cerrar(); });
  document.querySelectorAll("[data-copiar]").forEach(b => b.addEventListener("click", () => {
    navigator.clipboard?.writeText(b.parentElement.querySelector("pre").textContent);
    b.textContent = "Copiado"; setTimeout(() => (b.textContent = "Copiar"), 1400);
  }));

  // ---------- «ver más» en publicaciones largas ----------
  document.querySelectorAll(".post-texto").forEach(p => {
    if (p.scrollHeight > 150) {
      p.classList.add("recortado");
      const b = document.createElement("button");
      b.className = "ver-mas"; b.type = "button"; b.textContent = "…ver más";
      b.onclick = () => { p.classList.remove("recortado"); b.remove(); };
      p.after(b);
    }
  });

  // ---------- reacciones sin recargar ----------
  const INFO = window.REACCIONES || {};
  function pintarReacciones(post, datos) {
    const conteo = {};
    datos.reacciones.forEach(t => (conteo[t] = (conteo[t] || 0) + 1));
    const top = Object.entries(conteo).sort((a, b) => b[1] - a[1]).slice(0, 3);
    const zona = post.querySelector(".burbujas");
    if (zona) {
      zona.innerHTML = top.map(([t]) => `<span class="ic" style="background:${INFO[t].color}"><i class="bi ${INFO[t].icono}"></i></span>`).join("")
        + (datos.reacciones.length ? `<span class="num">${datos.reacciones.length}</span>` : "");
    }
    const btn = post.querySelector(".btn-reaccion");
    const mia = datos.mia[0];
    if (btn) {
      const info = mia ? INFO[mia] : INFO.recomendar;
      btn.dataset.mia = mia || "";
      btn.classList.toggle("reaccion-mia", !!mia);
      btn.style.setProperty("--c", info.color);
      btn.querySelector("i").className = "bi " + (mia ? info.icono : "bi-hand-thumbs-up");
      btn.querySelector("span").textContent = mia ? info.nombre : "Recomendar";
      btn.setAttribute("aria-pressed", mia ? "true" : "false");
    }
  }
  async function reaccionar(post, tipo) {
    const fd = new FormData(); fd.append("tipo", tipo); fd.append("csrf", csrf);
    const r = await fetch(`/p/${post.dataset.id}/reaccion`, { method: "POST", body: fd,
      headers: { "X-Requested-With": "fetch" } });
    if (r.ok) pintarReacciones(post, await r.json());
  }
  document.querySelectorAll(".post[data-id]").forEach(post => {
    const btn = post.querySelector(".btn-reaccion");
    btn?.addEventListener("click", () => reaccionar(post, btn.dataset.mia || "recomendar"));
    post.querySelectorAll(".paleta button").forEach(b => b.addEventListener("click", e => {
      e.stopPropagation(); reaccionar(post, b.dataset.tipo); b.blur(); btn?.focus(); btn?.blur();
    }));
    post.querySelector(".btn-comentar")?.addEventListener("click", () => {
      const f = post.querySelector(".comentarios form");
      f.hidden = false; f.querySelector("input[name=texto]").focus();
    });
    post.querySelector("[data-mas-comentarios]")?.addEventListener("click", e => {
      post.querySelectorAll(".comentario[hidden]").forEach(k => (k.hidden = false)); e.target.remove();
    });
    // En pantallas táctiles: mantener presionado abre la paleta de reacciones.
    const paleta = post.querySelector(".paleta");
    let t = null, largo = false;
    btn?.addEventListener("touchstart", () => { largo = false; t = setTimeout(() => { largo = true; paleta.classList.add("abierta"); }, 450); }, { passive: true });
    btn?.addEventListener("touchend", e => { clearTimeout(t); if (largo) e.preventDefault(); });
    btn?.addEventListener("contextmenu", e => e.preventDefault());
    document.addEventListener("click", e => { if (!post.contains(e.target)) paleta?.classList.remove("abierta"); });
    paleta?.addEventListener("click", () => paleta.classList.remove("abierta"));
  });

  // ---------- crear publicación: vista previa del archivo ----------
  const archivo = document.getElementById("archivo-post");
  if (archivo) {
    const prev = document.getElementById("vista-previa");
    document.querySelectorAll("[data-adjuntar]").forEach(b => b.addEventListener("click", () => {
      archivo.accept = b.dataset.adjuntar; archivo.click();
    }));
    archivo.addEventListener("change", () => {
      prev.innerHTML = ""; prev.hidden = true;
      const f = archivo.files[0]; if (!f) return;
      const url = URL.createObjectURL(f);
      const el = document.createElement(f.type.startsWith("video") ? "video" : "img");
      el.src = url; if (el.tagName === "VIDEO") el.controls = true;
      prev.append(el); prev.hidden = false;
      document.getElementById("modal-publicar")?.querySelector("textarea")?.focus();
    });
  }
})();
