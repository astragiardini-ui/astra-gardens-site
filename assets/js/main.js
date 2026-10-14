/* Astra Gardens — script del sito (disegno del 14/10/2026).
   Zero cookie, zero archiviazione nel browser, zero servizi esterni: tutto arriva da questo sito. */
(function () {
  "use strict";
  var doc = document, radice = doc.documentElement;
  var meno = window.matchMedia("(prefers-reduced-motion: reduce)");
  var haIO = "IntersectionObserver" in window;
  function tutti(sel, base) { return Array.prototype.slice.call((base || doc).querySelectorAll(sel)); }
  function adesso() { return window.performance && performance.now ? performance.now() : Date.now(); }
  /* focus spostato dallo script: l'anello si vede solo se si sta usando la tastiera (click con detail 0) */
  function metti(el, daTastiera) {
    if (!el) return;
    try { el.focus({ preventScroll: true, focusVisible: !!daTastiera }); } catch (_) { el.focus(); }
  }
  function ascolta(mq, fn) { if (mq.addEventListener) mq.addEventListener("change", fn); else if (mq.addListener) mq.addListener(fn); }

  /* ---------- Testata: ombra quando la pagina scorre ---------- */
  var testata = doc.querySelector(".testata");
  function aggiornaTestata() { if (testata) testata.classList.toggle("scorre", window.scrollY > 8); }
  aggiornaTestata();
  window.addEventListener("scroll", aggiornaTestata, { passive: true });

  /* ---------- Menu a tutto schermo ---------- */
  var apriMenuBtn = doc.querySelector(".apri-menu");
  var menu = doc.getElementById("menu");
  if (apriMenuBtn && menu) {
    var chiudiMenuBtn = menu.querySelector(".chiudi-menu");
    var tMenu = null;
    var apriMenu = function (e) {
      clearTimeout(tMenu);
      menu.hidden = false;
      void menu.offsetWidth; /* fa partire la dissolvenza */
      menu.classList.add("aperto");
      apriMenuBtn.setAttribute("aria-expanded", "true");
      radice.style.overflow = "hidden";
      metti(chiudiMenuBtn, !e || e.detail === 0);
    };
    var chiudiMenu = function (rimettiFocus, daTastiera) {
      menu.classList.remove("aperto");
      apriMenuBtn.setAttribute("aria-expanded", "false");
      radice.style.overflow = "";
      tMenu = setTimeout(function () { menu.hidden = true; }, meno.matches ? 0 : 400);
      if (rimettiFocus) metti(apriMenuBtn, daTastiera);
    };
    apriMenuBtn.addEventListener("click", apriMenu);
    if (chiudiMenuBtn) chiudiMenuBtn.addEventListener("click", function (e) { chiudiMenu(true, e.detail === 0); });
    menu.addEventListener("click", function (e) { if (e.target.closest("a")) chiudiMenu(false); });
    doc.addEventListener("keydown", function (e) {
      if (menu.hidden || !menu.classList.contains("aperto")) return;
      if (e.key === "Escape") { chiudiMenu(true, true); return; }
      if (e.key !== "Tab") return;
      var f = tutti("a[href], button:not([disabled])", menu);
      if (!f.length) return;
      if (e.shiftKey && doc.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && doc.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    });
  }

  /* ---------- Video: muti, in loop, senza comandi ----------
     Scelta di Francesco: nessun pulsante pausa. Fuori dallo schermo si fermano per risparmiare batteria
     e ripartono quando tornano visibili. Se il telefono blocca l'avvio automatico (iPhone in Risparmio
     energetico) resta l'immagine ferma e i video partono al primo tocco. */
  var video = tutti("video");
  var serveSblocco = false;
  function scatola(v) { return v.closest("[data-clip]") || v.parentNode; }
  function visibile(el) {
    var r = el.getBoundingClientRect();
    return r.bottom > -40 && r.top < window.innerHeight + 40 && r.right > 0 && r.left < window.innerWidth && r.width > 0;
  }
  function haSorgente(v) { return !!(v.currentSrc || v.getAttribute("src") || v.querySelector("source")); }
  function parti(v) {
    if (!haSorgente(v)) return;
    if (v.preload !== "auto") v.preload = "auto";
    v.muted = true;
    var p;
    try { p = v.play(); } catch (_) { p = null; }
    if (p && typeof p.then === "function") {
      p.then(function () { scatola(v).classList.add("in-play"); })
       .catch(function (err) { if (!err || err.name !== "AbortError") serveSblocco = true; });
    } else if (!v.paused) {
      scatola(v).classList.add("in-play");
    }
  }
  function ferma(v) {
    if (v.paused) return;
    v._fermatoDaNoi = true;
    v.pause();
  }
  video.forEach(function (v) {
    v.muted = true; v.defaultMuted = true; v.loop = true; v.playsInline = true;
    v.setAttribute("muted", ""); v.setAttribute("playsinline", ""); v.removeAttribute("controls");
    try { v.disablePictureInPicture = true; } catch (_) {}
    try { v.disableRemotePlayback = true; } catch (_) {}
    v.addEventListener("playing", function () { scatola(v).classList.add("in-play"); });
    v.addEventListener("pause", function () {
      if (v._fermatoDaNoi) { v._fermatoDaNoi = false; return; }
      setTimeout(function () {
        var inOnda = !v.classList.contains("hero__v") || v.classList.contains("attivo");
        if (v.paused && inOnda && doc.visibilityState === "visible" && visibile(scatola(v))) parti(v);
      }, 300);
    });
    v.addEventListener("contextmenu", function (e) { e.preventDefault(); });
  });

  /* le clip partono quando entrano nello schermo e si fermano quando escono */
  var clip = tutti("[data-clip] video");
  if (haIO) {
    var osservaClip = new IntersectionObserver(function (voci) {
      voci.forEach(function (voce) {
        var v = voce.target.querySelector("video");
        if (!v) return;
        if (voce.isIntersecting) parti(v); else ferma(v);
      });
    }, { rootMargin: "120px 0px 120px 0px", threshold: 0 });
    /* i video grandi fuori dalla striscia (introduzione e chi siamo sul computer) si scaricano solo quando
       se ne vede almeno un quarto: cosi' all'apertura della pagina non partono insieme a quelli in cima */
    var osservaGrandi = new IntersectionObserver(function (voci) {
      voci.forEach(function (voce) {
        var v = voce.target.querySelector("video");
        if (!v) return;
        if (voce.isIntersecting && voce.intersectionRatio >= 0.25) parti(v); else if (!voce.isIntersecting) ferma(v);
      });
    }, { threshold: [0, 0.25] });
    clip.forEach(function (v) {
      var box = scatola(v);
      (box.closest("[data-striscia]") ? osservaClip : osservaGrandi).observe(box);
    });
  } else {
    clip.forEach(parti);
  }

  /* ---------- Apertura: i video interi che si danno il cambio ----------
     Telefono: tre verticali ogni 6,5 s. Computer: due orizzontali ogni 7 s. Il primo l'ha già avviato lo
     script dentro la pagina; il successivo si scarica solo quando quello in onda ha finito di scaricarsi,
     poco prima del suo turno: mai tre download insieme. */
  var hero = doc.querySelector("[data-hero]");
  if (hero) (function () {
    var mq = window.matchMedia(hero.getAttribute("data-mq"));
    var punti = hero.querySelector(".hero__punti");
    var lista = [], i = 0, tCambio = null, tCarica = null, tScarico = null, attesa = 0, inVista = true, sospeso = false;
    function intervallo() { return mq.matches ? 7000 : 6500; }
    function sorgente(v) {
      var hd = v.getAttribute("data-src-hd");
      return hd && window.innerWidth * (window.devicePixelRatio || 1) > 2000 ? hd : v.getAttribute("data-src");
    }
    function carica(v) {
      if (v.getAttribute("data-caricato")) return;
      v.setAttribute("data-caricato", "1");
      v.poster = v.getAttribute("data-poster");
      v.preload = "auto";
      v.src = sorgente(v);
      try { v.load(); } catch (_) {}
    }
    function scaricato(v) {
      try {
        var b = v.buffered;
        return v.readyState >= 4 && b.length && b.end(b.length - 1) >= (v.duration || 0) - 0.3;
      } catch (_) { return true; }
    }
    function aggiornaPunti() {
      tutti(".hero__punto", punti).forEach(function (b, n) { b.setAttribute("aria-current", n === i ? "true" : "false"); });
    }
    function programma() {
      clearTimeout(tCambio); clearTimeout(tCarica); clearTimeout(tScarico);
      if (lista.length < 2) return;
      var corrente = lista[i], prossimo = lista[(i + 1) % lista.length], durata = intervallo(), t0 = adesso();
      tCarica = setTimeout(function controlla() {
        if (scaricato(corrente) || adesso() - t0 > durata + 6000) carica(prossimo);
        else tScarico = setTimeout(controlla, 400);
      }, Math.max(0, durata - 3200));
      tCambio = setTimeout(prova, durata);
    }
    function prova() {
      if (!inVista || doc.visibilityState !== "visible") { sospeso = true; return; }
      var prossimo = lista[(i + 1) % lista.length];
      carica(prossimo);
      if (prossimo.readyState >= 3 || attesa >= 12) { attesa = 0; mostra(i + 1); }
      else { attesa++; tCambio = setTimeout(prova, 500); }
    }
    function mostra(k) {
      var prec = lista[i];
      i = (k + lista.length) % lista.length;
      var v = lista[i];
      carica(v);
      if (prec && prec !== v) { try { v.currentTime = 0; } catch (_) {} }
      v.classList.add("attivo");
      if (inVista) parti(v);
      if (prec && prec !== v) {
        prec.classList.remove("attivo");
        setTimeout(function () { if (!prec.classList.contains("attivo")) ferma(prec); }, 1700);
      }
      aggiornaPunti();
      programma();
    }
    function avvia() {
      var tipo = mq.matches ? "pc" : "tel";
      tutti("video.hero__v", hero).forEach(function (v) {
        if (v.getAttribute("data-set") !== tipo) { v.classList.remove("attivo"); ferma(v); }
      });
      lista = tutti('video.hero__v[data-set="' + tipo + '"]', hero);
      if (!lista.length) return;
      punti.innerHTML = "";
      if (lista.length > 1) {
        lista.forEach(function (v, k) {
          var b = doc.createElement("button");
          b.type = "button"; b.className = "hero__punto";
          b.setAttribute("aria-label", "Video " + (k + 1) + " di " + lista.length);
          b.addEventListener("click", function () { if (k !== i) { attesa = 0; mostra(k); } });
          punti.appendChild(b);
        });
      }
      var attivi = lista.filter(function (v) { return v.classList.contains("attivo"); });
      i = attivi.length ? lista.indexOf(attivi[0]) : 0;
      lista.forEach(function (v, n) { if (n !== i) v.classList.remove("attivo"); });
      mostra(i);
    }
    function riprendi() {
      if (!inVista || doc.visibilityState !== "visible" || !lista.length) return;
      parti(lista[i]);
      if (sospeso) { sospeso = false; programma(); }
    }
    avvia();
    ascolta(mq, avvia);
    if (haIO) {
      new IntersectionObserver(function (voci) {
        inVista = voci[0].isIntersecting;
        if (inVista) riprendi(); else if (lista[i]) ferma(lista[i]);
      }, { threshold: 0 }).observe(hero);
    }
    doc.addEventListener("visibilitychange", riprendi);
  })();

  /* primo tocco: fa partire quello che il telefono aveva bloccato. Su iPhone ogni video va avviato dentro
     il gesto: quelli che si vedono partono, gli altri vengono avviati e subito fermati. */
  function sblocca() {
    if (!serveSblocco) return;
    serveSblocco = false;
    video.forEach(function (v) {
      if (!v.paused || !haSorgente(v)) return;
      var inOnda = !v.classList.contains("hero__v") || v.classList.contains("attivo");
      if (inOnda && visibile(scatola(v))) { parti(v); return; }
      if (v._sbloccato) return;
      v._sbloccato = true;
      var p;
      try { p = v.play(); } catch (_) { p = null; }
      v._fermatoDaNoi = true;
      try { v.pause(); } catch (_) {}
      if (p && typeof p.catch === "function") {
        p.catch(function (err) { if (err && err.name === "NotAllowedError") { v._sbloccato = false; serveSblocco = true; } });
      }
    });
  }
  ["touchstart", "touchend", "pointerdown", "click", "keydown"].forEach(function (ev) {
    window.addEventListener(ev, sblocca, { passive: true, capture: true });
  });
  doc.addEventListener("visibilitychange", function () {
    if (doc.visibilityState !== "visible") return;
    clip.forEach(function (v) { if (v.paused && visibile(scatola(v))) parti(v); });
  });

  /* ---------- Foto e video a schermo intero ---------- */
  var dialog = doc.getElementById("lightbox");
  var lb = null;
  if (dialog && typeof dialog.showModal === "function") (function () {
    var media = dialog.querySelector(".lightbox__media");
    var didascalia = dialog.querySelector(".lightbox__didascalia");
    var btnPrima = dialog.querySelector("[data-azione=prima]");
    var btnDopo = dialog.querySelector("[data-azione=dopo]");
    var gruppo = [], indice = 0, ultimo = null, el = null, w = 0, h = 0;
    function adatta() {
      if (!el || !w || !h) return;
      el.style.width = ""; el.style.height = "";
      var mh = parseFloat(getComputedStyle(el).maxHeight);
      var W = media.clientWidth, H = Math.min(media.clientHeight, isFinite(mh) ? mh : Infinity);
      if (!W || !H) return;
      var k = Math.min(W / w, H / h);
      el.style.width = Math.floor(w * k) + "px";
      el.style.height = Math.floor(h * k) + "px";
    }
    function mostra(n) {
      indice = (n + gruppo.length) % gruppo.length;
      var b = gruppo[indice];
      var alt = b.getAttribute("data-alt") || "";
      w = +b.getAttribute("data-w") || 0; h = +b.getAttribute("data-h") || 0;
      media.innerHTML = "";
      if (b.getAttribute("data-media") === "video") {
        el = doc.createElement("video");
        el.muted = true; el.loop = true; el.playsInline = true; el.autoplay = true;
        el.setAttribute("muted", ""); el.setAttribute("playsinline", ""); el.setAttribute("aria-label", alt);
        el.poster = b.getAttribute("data-poster") || "";
        el.src = b.getAttribute("data-src");
        media.appendChild(el);
        var p; try { p = el.play(); } catch (_) { p = null; }
        if (p && p.catch) p.catch(function () {});
      } else {
        el = doc.createElement("img");
        el.alt = alt; el.decoding = "async";
        el.src = b.getAttribute("data-src");
        media.appendChild(el);
      }
      didascalia.textContent = alt;
      adatta();
    }
    var daTastiera = false;
    function apri(b, elenco, tastiera) {
      daTastiera = !!tastiera;
      gruppo = elenco;
      var piu = gruppo.length > 1;
      btnPrima.hidden = !piu; btnDopo.hidden = !piu;
      ultimo = b;
      dialog.showModal();
      mostra(Math.max(0, gruppo.indexOf(b)));
      metti(media, daTastiera);
    }
    dialog.querySelector("[data-azione=chiudi]").addEventListener("click", function () { dialog.close(); });
    btnPrima.addEventListener("click", function () { mostra(indice - 1); });
    btnDopo.addEventListener("click", function () { mostra(indice + 1); });
    dialog.addEventListener("keydown", function (e) {
      if (gruppo.length < 2) return;
      if (e.key === "ArrowLeft") mostra(indice - 1);
      if (e.key === "ArrowRight") mostra(indice + 1);
    });
    dialog.addEventListener("click", function (e) { if (e.target === dialog || e.target === media) dialog.close(); });
    dialog.addEventListener("close", function () {
      media.innerHTML = ""; el = null;
      metti(ultimo, daTastiera);
    });
    window.addEventListener("resize", adatta);
    var xs = null;
    dialog.addEventListener("touchstart", function (e) { xs = e.touches[0].clientX; }, { passive: true });
    dialog.addEventListener("touchend", function (e) {
      if (xs === null || gruppo.length < 2) { xs = null; return; }
      var d = e.changedTouches[0].clientX - xs;
      if (Math.abs(d) > 50) mostra(indice + (d < 0 ? 1 : -1));
      xs = null;
    }, { passive: true });
    lb = { apri: apri, aperta: function () { return dialog.open; } };
  })();

  /* ---------- Dai nostri cantieri: striscia che scorre da sola ----------
     Scorre da destra a sinistra senza fine (gli elementi sono due volte di fila); si ferma quando ci si
     passa sopra col mouse, quando la si tocca o la si trascina, e riparte poco dopo. */
  var striscia = doc.querySelector("[data-striscia]");
  if (striscia) (function () {
    var lista = striscia.querySelector(".striscia__lista");
    var bottoni = tutti(".striscia__btn", striscia);
    var originali = bottoni.filter(function (b) { return !b.closest("[aria-hidden='true']"); });
    var VELOCITA = 40; /* px al secondo */
    var pos = 0, impostato = -1, ultimoT = null, raf = null, inVista = false;
    var sopra = false, tocco = false, dentro = false, trascina = false, mosso = false, riprendi = 0;
    var x0 = 0, s0 = 0, bloccaClick = false;
    function periodo() { return lista.offsetWidth / 2; }
    function ferma() { return sopra || tocco || dentro || trascina || (lb && lb.aperta()) || meno.matches || adesso() < riprendi; }
    function passo(t) {
      raf = requestAnimationFrame(passo);
      if (ultimoT === null) { ultimoT = t; pos = striscia.scrollLeft; return; }
      var dt = Math.min(64, t - ultimoT);
      ultimoT = t;
      if (ferma()) { pos = striscia.scrollLeft; return; }
      var P = periodo();
      if (P <= striscia.clientWidth) return;
      pos += VELOCITA * dt / 1000;
      if (pos >= P) pos -= P;
      striscia.scrollLeft = pos;
      impostato = striscia.scrollLeft;
    }
    function accendi() { if (!raf && !meno.matches) { ultimoT = null; raf = requestAnimationFrame(passo); } }
    function spegni() { if (raf) { cancelAnimationFrame(raf); raf = null; } }
    if (haIO) {
      new IntersectionObserver(function (v) {
        inVista = v[0].isIntersecting;
        if (inVista) accendi(); else spegni();
      }, { threshold: 0 }).observe(striscia);
    } else { accendi(); }
    ascolta(meno, function () { if (meno.matches) spegni(); else if (inVista) accendi(); });

    striscia.addEventListener("scroll", function () {
      if (Math.abs(striscia.scrollLeft - impostato) > 2) {
        riprendi = adesso() + 1600; /* l'ha spostata la persona */
        var P = periodo();
        if (!tocco && !trascina && P > striscia.clientWidth && striscia.scrollLeft >= P) {
          striscia.scrollLeft -= P;
          impostato = striscia.scrollLeft;
        }
      }
    }, { passive: true });
    striscia.addEventListener("pointerenter", function (e) { if (e.pointerType === "mouse") sopra = true; });
    striscia.addEventListener("pointerleave", function (e) { if (e.pointerType === "mouse") { sopra = false; riprendi = adesso() + 300; } });
    striscia.addEventListener("touchstart", function () { tocco = true; }, { passive: true });
    function fineTocco() { tocco = false; riprendi = adesso() + 2000; }
    striscia.addEventListener("touchend", fineTocco, { passive: true });
    striscia.addEventListener("touchcancel", fineTocco, { passive: true });
    striscia.addEventListener("focusin", function () { dentro = true; });
    striscia.addEventListener("focusout", function () { dentro = false; riprendi = adesso() + 800; });
    striscia.addEventListener("dragstart", function (e) { e.preventDefault(); });

    /* trascinamento col mouse */
    striscia.addEventListener("pointerdown", function (e) {
      if (e.pointerType !== "mouse" || e.button !== 0) return;
      trascina = true; mosso = false; x0 = e.clientX; s0 = striscia.scrollLeft;
    });
    striscia.addEventListener("pointermove", function (e) {
      if (!trascina || e.pointerType !== "mouse") return;
      var dx = e.clientX - x0;
      if (!mosso) {
        if (Math.abs(dx) < 6) return;
        mosso = true;
        striscia.classList.add("trascina");
        try { striscia.setPointerCapture(e.pointerId); } catch (_) {}
      }
      var P = periodo(), s = s0 - dx;
      if (P > striscia.clientWidth) {
        if (s < 0) { s += P; s0 += P; }
        else if (s >= P) { s -= P; s0 -= P; }
      }
      striscia.scrollLeft = s;
      impostato = striscia.scrollLeft;
      pos = impostato;
    });
    function fineTrascina(e) {
      if (!trascina) return;
      trascina = false;
      striscia.classList.remove("trascina");
      if (mosso) { bloccaClick = true; setTimeout(function () { bloccaClick = false; }, 0); }
      try { striscia.releasePointerCapture(e.pointerId); } catch (_) {}
      riprendi = adesso() + 1200;
    }
    striscia.addEventListener("pointerup", fineTrascina);
    striscia.addEventListener("pointercancel", fineTrascina);
    striscia.addEventListener("click", function (e) {
      if (bloccaClick) { e.preventDefault(); e.stopPropagation(); bloccaClick = false; return; }
      var b = e.target.closest(".striscia__btn");
      if (!b || !lb) return;
      var k = +b.getAttribute("data-indice") || 0;
      lb.apri(originali[k] || b, originali, e.detail === 0);
    }, true);
    /* senza la finestra a schermo intero: si apre il file */
    if (!lb) bottoni.forEach(function (b) {
      b.addEventListener("click", function () { window.location.href = b.getAttribute("data-src"); });
    });
  })();

  /* ---------- Servizi: fisarmonica (uno aperto alla volta) ---------- */
  var voceServizio = {};
  tutti("[data-fisarmonica]").forEach(function (f) {
    var voci = tutti(".fisarmonica__voce", f);
    function imposta(voce, aperta) {
      voce.classList.toggle("aperta", aperta);
      voce.querySelector(".fisarmonica__btn").setAttribute("aria-expanded", aperta ? "true" : "false");
    }
    function apri(voce, segui) {
      var era = voce.classList.contains("aperta");
      voci.forEach(function (x) { if (x !== voce) imposta(x, false); });
      imposta(voce, segui ? true : !era);
      /* se chiudendo una voce sopra quella toccata la pagina "sale", la si riporta in vista */
      setTimeout(function () {
        var top = voce.getBoundingClientRect().top, alto = testata ? testata.offsetHeight : 0;
        if (top < alto + 8) window.scrollBy({ top: top - alto - 16, behavior: meno.matches ? "auto" : "smooth" });
      }, meno.matches ? 0 : 540);
    }
    voci.forEach(function (voce) {
      voce.querySelector(".fisarmonica__btn").addEventListener("click", function () { apri(voce, false); });
      voceServizio["#" + voce.id] = function () { apri(voce, true); };
    });
  });
  function apriDaIndirizzo(h) { if (voceServizio[h]) voceServizio[h](); }
  apriDaIndirizzo(location.hash);
  window.addEventListener("hashchange", function () { apriDaIndirizzo(location.hash); });
  tutti('a[href*="#servizio-"]').forEach(function (a) {
    a.addEventListener("click", function () { apriDaIndirizzo(a.getAttribute("href").replace(/^[^#]*/, "")); });
  });

  /* ---------- I nostri lavori: carosello con barra di avanzamento ---------- */
  var carosello = doc.querySelector("[data-carosello]");
  if (carosello) (function () {
    var barra = doc.querySelector("[data-avanzamento]");
    var indietro = doc.querySelector("[data-carosello-indietro]");
    var avanti = doc.querySelector("[data-carosello-avanti]");
    var listaC = carosello.querySelector(".carosello__lista");
    function aggiorna() {
      var max = carosello.scrollWidth - carosello.clientWidth;
      var w = Math.min(100, carosello.clientWidth / carosello.scrollWidth * 100);
      var r = max > 0 ? carosello.scrollLeft / max : 0;
      if (barra) { barra.style.width = w + "%"; barra.style.left = r * (100 - w) + "%"; }
      if (indietro) indietro.disabled = carosello.scrollLeft <= 2;
      if (avanti) avanti.disabled = carosello.scrollLeft >= max - 2;
    }
    function passo() {
      var s = carosello.querySelector(".scheda");
      var g = parseFloat(getComputedStyle(listaC).columnGap) || 0;
      return s ? s.offsetWidth + g : 300;
    }
    carosello.addEventListener("scroll", aggiorna, { passive: true });
    window.addEventListener("resize", aggiorna);
    if (indietro) indietro.addEventListener("click", function () { carosello.scrollBy({ left: -passo(), behavior: meno.matches ? "auto" : "smooth" }); });
    if (avanti) avanti.addEventListener("click", function () { carosello.scrollBy({ left: passo(), behavior: meno.matches ? "auto" : "smooth" }); });
    aggiorna();
    window.addEventListener("load", aggiorna);
  })();

  /* ---------- Prima e dopo con cursore ---------- */
  tutti("[data-confronto]").forEach(function (box) {
    var input = box.querySelector("input");
    var dx = box.getAttribute("data-dx") || "Progetto";
    var toccato = false;
    function metti(pct) {
      pct = Math.max(0, Math.min(100, pct));
      box.style.setProperty("--pos", pct + "%");
      input.value = Math.round(pct);
      input.setAttribute("aria-valuetext", dx + " visibile al " + Math.round(100 - pct) + " per cento");
    }
    function daPuntatore(e) {
      var r = box.getBoundingClientRect();
      metti((e.clientX - r.left) / r.width * 100);
    }
    var trascina = false, mosso = false, x0 = 0;
    box.addEventListener("pointerdown", function (e) {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      toccato = true; trascina = true; mosso = false; x0 = e.clientX;
      box.classList.add("trascina");
      if (e.pointerType === "mouse") {
        daPuntatore(e);
        try { box.setPointerCapture(e.pointerId); } catch (_) {}
      }
    });
    box.addEventListener("pointermove", function (e) {
      if (!trascina) return;
      if (e.pointerType !== "mouse" && !mosso) {
        if (Math.abs(e.clientX - x0) < 4) return;
        mosso = true;
        try { box.setPointerCapture(e.pointerId); } catch (_) {}
      }
      daPuntatore(e);
    });
    function fine() { trascina = false; box.classList.remove("trascina"); }
    box.addEventListener("pointerup", function (e) {
      if (trascina && e.pointerType !== "mouse" && !mosso) daPuntatore(e); /* un tocco sposta il cursore lì */
      fine();
    });
    box.addEventListener("pointercancel", fine);
    input.addEventListener("input", function () { toccato = true; metti(+input.value); });
    input.addEventListener("keydown", function (e) {
      var p = { ArrowLeft: -5, ArrowDown: -5, ArrowRight: 5, ArrowUp: 5 }[e.key];
      if (p) { e.preventDefault(); toccato = true; metti(+input.value + p); }
    });
    metti(50);
    /* piccolo movimento iniziale per far capire che si può trascinare */
    if (!meno.matches && haIO) {
      var visto = false;
      new IntersectionObserver(function (voci, oss) {
        voci.forEach(function (v) {
          if (!v.isIntersecting || visto) return;
          visto = true; oss.disconnect();
          var t0 = null, durata = 1800;
          function giro(t) {
            if (toccato) return;
            if (t0 === null) t0 = t;
            var k = Math.min(1, (t - t0) / durata);
            metti(50 - 18 * Math.sin(k * Math.PI * 2) * (1 - k * 0.15));
            if (k < 1) requestAnimationFrame(giro); else metti(50);
          }
          setTimeout(function () { requestAnimationFrame(giro); }, 500);
        });
      }, { threshold: 0.6 }).observe(box);
    }
  });

  /* ---------- Comparsa morbida delle sezioni allo scorrere ---------- */
  var rivela = tutti(".rivela");
  if (haIO) {
    radice.classList.add("anima");
    var osservaRivela = new IntersectionObserver(function (voci) {
      voci.forEach(function (v) {
        if (v.isIntersecting) { v.target.classList.add("visibile"); osservaRivela.unobserve(v.target); }
      });
    }, { rootMargin: "0px", threshold: 0 });
    rivela.forEach(function (el) { osservaRivela.observe(el); });
  }

  /* ---------- Barra WhatsApp sul telefono ----------
     Compare quando i video d'apertura sono quasi usciti e i pulsanti dell'introduzione non si vedono;
     sparisce sopra il piè di pagina, che ha già i suoi pulsanti. */
  var barraWa = doc.querySelector(".barra-wa");
  if (barraWa) {
    var aperturaEl = doc.querySelector(".hero"), azioniEl = doc.querySelector(".intro__azioni"), piedeEl = doc.querySelector(".piede");
    if (haIO && aperturaEl && azioniEl && piedeEl) {
      var aperturaV = true, azioniV = false, piedeV = false;
      var aggiornaWa = function () { barraWa.classList.toggle("visibile", !aperturaV && !azioniV && !piedeV); };
      new IntersectionObserver(function (v) { aperturaV = v[0].isIntersecting && v[0].intersectionRatio > 0.3; aggiornaWa(); },
        { threshold: [0, 0.3, 0.6, 1] }).observe(aperturaEl);
      new IntersectionObserver(function (v) { azioniV = v[0].isIntersecting; aggiornaWa(); }).observe(azioniEl);
      new IntersectionObserver(function (v) { piedeV = v[0].isIntersecting; aggiornaWa(); }).observe(piedeEl);
    } else {
      barraWa.classList.add("visibile");
    }
  }
})();
