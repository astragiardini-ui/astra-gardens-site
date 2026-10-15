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
  /* scorrimenti fatti dallo script: subito, senza l'animazione morbida della pagina */
  function scorriSubito(fn) {
    var prima = radice.style.scrollBehavior;
    radice.style.scrollBehavior = "auto";
    try { fn(); } finally { radice.style.scrollBehavior = prima; }
  }
  /* «Risparmio dati» attivo o rete più lenta del 4G: in cima un solo video, nella striscia solo locandine */
  var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  var leggeri = false;
  try { leggeri = !!(conn && (conn.saveData || (conn.effectiveType && conn.effectiveType !== "4g"))); } catch (_) {}
  if (leggeri) radice.classList.add("dati-leggeri");
  /* la stima della rete arriva anche dopo: se diventa lenta si passa ai dati leggeri (mai il contrario) */
  if (conn && conn.addEventListener) conn.addEventListener("change", function () {
    try {
      if (!leggeri && (conn.saveData || (conn.effectiveType && conn.effectiveType !== "4g"))) {
        leggeri = true;
        radice.classList.add("dati-leggeri");
      }
    } catch (_) {}
  });
  /* telefono (anche in orizzontale): versioni leggere dei video, NOME-tel.mp4 (Francesco 15/10/2026) */
  var heroEl = doc.querySelector("[data-hero]");
  var telefono = window.matchMedia((heroEl && heroEl.getAttribute("data-mq-tel")) || "(max-width: 899.98px), (max-height: 499.98px)").matches;
  function scegliSrc(el) {
    var t = el.getAttribute("data-src-tel");
    return t && telefono ? t : el.getAttribute("data-src");
  }

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
    var tMenu = null, yMenu = 0;
    var apriMenu = function (e) {
      clearTimeout(tMenu);
      menu.hidden = false;
      void menu.offsetWidth; /* fa partire la dissolvenza */
      menu.classList.add("aperto");
      apriMenuBtn.setAttribute("aria-expanded", "true");
      yMenu = window.scrollY || window.pageYOffset || 0;
      doc.body.style.top = -yMenu + "px";
      doc.body.classList.add("menu-aperto");
      metti(chiudiMenuBtn, !e || e.detail === 0);
    };
    var chiudiMenu = function (rimettiFocus, daTastiera) {
      menu.classList.remove("aperto");
      apriMenuBtn.setAttribute("aria-expanded", "false");
      if (doc.body.classList.contains("menu-aperto")) {
        doc.body.classList.remove("menu-aperto");
        doc.body.style.top = "";
        scorriSubito(function () { window.scrollTo(0, yMenu); });
      }
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
  if (telefono) tutti("video[data-src-tel]").forEach(function (v) {
    var s = v.querySelector("source");
    if (s && !v.classList.contains("hero__v")) {
      s.setAttribute("src", v.getAttribute("data-src-tel"));
      try { v.load(); } catch (_) {} /* rifà la scelta della sorgente; con preload="none" non scarica nulla */
    }
  });
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
  function urlDi(v) {
    var s = v.currentSrc || v.getAttribute("src") || "";
    if (!s && v.classList.contains("hero__v")) s = scegliSrc(v) || "";
    if (!s) { var so = v.querySelector("source"); if (so) s = so.getAttribute("src") || ""; }
    try { return new URL(s, location.href).href; } catch (_) { return s; }
  }
  function scaricato(v) {
    try {
      var b = v.buffered;
      return v.readyState >= 4 && b.length && b.end(b.length - 1) >= (v.duration || 0) - 0.3;
    } catch (_) { return true; }
  }
  function avanti(v) {
    try {
      var b = v.buffered, t = v.currentTime;
      for (var k = 0; k < b.length; k++) if (b.start(k) <= t + 0.1 && b.end(k) > t) return b.end(k) - t;
    } catch (_) {}
    return 0;
  }
  function inScarico(v) {
    if (!(v.getAttribute("data-caricato") || v._avviato) || scaricato(v) || v.error) return false;
    return v.networkState === 2 || v.readyState < 3;
  }
  /* lo stesso file lo sta già scaricando un altro video della pagina: si aspetta e poi lo dà la cache */
  function doppione(v) {
    var u = urlDi(v);
    return !!u && video.some(function (x) { return x !== v && urlDi(x) === u && inScarico(x); });
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
  function partiClip(v) {
    clearTimeout(v._attesa);
    if (leggeri) return; /* resta la locandina: il video si guarda toccandolo */
    if (doppione(v)) { v._attesa = setTimeout(function () { if (v._vista) partiClip(v); }, 500); return; }
    v._avviato = true;
    parti(v);
  }
  if (haIO) {
    var osservaClip = new IntersectionObserver(function (voci) {
      voci.forEach(function (voce) {
        var v = voce.target.querySelector("video");
        if (!v) return;
        v._vista = voce.isIntersecting;
        if (voce.isIntersecting) partiClip(v); else { clearTimeout(v._attesa); ferma(v); }
      });
    }, { rootMargin: "120px 0px 120px 0px", threshold: 0 });
    /* i video grandi fuori dalla striscia (introduzione e chi siamo sul computer) si scaricano solo quando
       se ne vede almeno un quarto: cosi' all'apertura della pagina non partono insieme a quelli in cima */
    var osservaGrandi = new IntersectionObserver(function (voci) {
      voci.forEach(function (voce) {
        var v = voce.target.querySelector("video");
        if (!v) return;
        v._vista = voce.isIntersecting;
        if (voce.isIntersecting && voce.intersectionRatio >= 0.25) partiClip(v); else if (!voce.isIntersecting) { clearTimeout(v._attesa); ferma(v); }
      });
    }, { threshold: [0, 0.25] });
    clip.forEach(function (v) {
      var box = scatola(v);
      (box.closest("[data-striscia]") ? osservaClip : osservaGrandi).observe(box);
    });
  } else {
    clip.forEach(function (v) { v._vista = true; partiClip(v); });
  }

  /* ---------- Apertura: i video interi che si danno il cambio ogni 2 secondi ----------
     Richiesta di Francesco (15/10/2026): «deve cambiare ogni due secondi e continuare in loop».
     - Ogni 2 s (6 s con «riduci movimento») si passa al video successivo GIÀ PRONTO; se nessun altro è pronto
       si resta su quello in onda: mai un fotogramma nero o fermo.
     - Il video nascosto si mette in pausa e quando torna riprende da dove era: a ogni giro si vedono i
       secondi successivi. Ogni video gira anche in loop su se stesso.
     - Il primo (gerani con l'ape) resta in onda 4 s al primo caricamento, poi parte il giro.
     - Si scaricano uno alla volta, in ordine: il successivo parte quando il precedente ha finito (o quando il
       browser smette da solo di scaricarlo); mai due insieme all'inizio. */
  var hero = doc.querySelector("[data-hero]");
  if (hero) (function () {
    var mq = window.matchMedia(hero.getAttribute("data-mq"));
    var punti = hero.querySelector(".hero__punti");
    var lista = [], i = 0, tGiro = null, tCoda = null, inVista = true, primoGiro = true;
    var scelta = -1, pausaFino = 0, tScelta = null;
    function ciclo() { return meno.matches ? 6000 : 2000; }
    function sorgente(v) {
      var hd = v.getAttribute("data-src-hd"), t = v.getAttribute("data-src-tel");
      if (t && telefono) return t;
      return hd && window.innerWidth * (window.devicePixelRatio || 1) > 2000 ? hd : v.getAttribute("data-src");
    }
    function carica(v) {
      if (v.getAttribute("data-caricato")) return;
      v.setAttribute("data-caricato", "1");
      v._inizioCarico = adesso();
      v.poster = v.getAttribute("data-poster");
      v.preload = "auto";
      v.src = sorgente(v);
      try { v.load(); } catch (_) {}
    }
    /* pronto = scaricato tutto, oppure ha già in memoria almeno il pezzo che servirà nel suo turno */
    function pronto(v) {
      if (!v.getAttribute("data-caricato") || v.readyState < 3 || v._riscalda) return false;
      return scaricato(v) || avanti(v) >= 2;
    }
    /* Un video fermo il browser lo scarica solo per qualche decimo di secondo: per averne pronto un pezzo
       lo si fa girare nascosto finché ha in memoria 2,6 secondi, poi lo si ferma e si torna al punto di prima. */
    function riscalda(v) {
      if (v._riscalda || v.classList.contains("attivo")) return;
      v._riscalda = true;
      var da = v.currentTime, t0 = adesso();
      function basta() {
        if (!v._riscalda) return;
        if (v.classList.contains("attivo")) { v._riscalda = false; return; }
        if (scaricato(v) || avanti(v) + (v.currentTime - da) >= 2.6 || adesso() - t0 > 20000) {
          v._riscalda = false;
          v._fermatoDaNoi = true;
          try { v.pause(); v.currentTime = da; } catch (_) {}
          coda();
        } else {
          setTimeout(basta, 250);
        }
      }
      v.muted = true;
      var p;
      try { p = v.play(); } catch (_) { p = null; }
      if (p && p.catch) p.catch(function () { v._riscalda = false; });
      setTimeout(basta, 250);
    }
    function staScaricando(v) {
      if (v._riscalda) return true;
      if (!v.getAttribute("data-caricato") || scaricato(v) || v.error) return false;
      /* quello in onda, se ha già 3,5 secondi in memoria, lascia spazio al prossimo: il giro parte prima */
      if (v.classList.contains("attivo") && avanti(v) >= 3.5) return false;
      if (v.networkState !== 2 && v.readyState >= 3) return false; /* il browser ha smesso da solo */
      if (!v._inizioCarico) v._inizioCarico = adesso();
      return adesso() - v._inizioCarico < 20000; /* rete lentissima: dopo 20 s si passa comunque al successivo */
    }
    function coda() {
      clearTimeout(tCoda);
      if (leggeri) return;
      if (!inVista || doc.visibilityState !== "visible" || !lista.length) return;
      if (lista.some(staScaricando)) { tCoda = setTimeout(coda, 400); return; }
      var dopo = lista.filter(function (v) { return !v.getAttribute("data-caricato"); })[0];
      if (dopo && doppione(dopo)) { tCoda = setTimeout(coda, 500); return; } /* lo sta scaricando la striscia */
      if (dopo) {
        carica(dopo);
        var via = function () { dopo.removeEventListener("canplay", via); riscalda(dopo); };
        if (dopo.readyState >= 3) via(); else dopo.addEventListener("canplay", via);
        tCoda = setTimeout(coda, 400);
        return;
      }
      /* tutti avviati: chi è rimasto con poco in memoria si riscalda, uno alla volta */
      var corto = lista.filter(function (v) {
        return !v.classList.contains("attivo") && v.readyState >= 1 && !scaricato(v) && avanti(v) < 2.5;
      })[0];
      if (corto) riscalda(corto);
    }
    function aggiornaPunti() {
      tutti(".hero__punto", punti).forEach(function (b, n) {
        b.setAttribute("aria-current", n === i ? "true" : "false");
        b.classList.toggle("in-attesa", n === scelta);
      });
    }
    /* puntino toccato: il video scelto si prepara e va in onda solo quando è pronto; il giro automatico
       si ferma per 8 secondi e poi riparte da lì, senza mai tornare indietro da solo */
    function attendiScelta() {
      clearTimeout(tScelta);
      if (scelta < 0) return;
      if (pronto(lista[scelta])) {
        var k = scelta;
        scelta = -1;
        mostra(k);
        pausaFino = adesso() + 8000;
        programma(false, 8000);
      } else {
        tScelta = setTimeout(attendiScelta, 250);
      }
    }
    function scegli(k) {
      if (k === i && scelta < 0) return;
      if (k === i) { scelta = -1; aggiornaPunti(); return; }
      scelta = k;
      pausaFino = adesso() + 8000;
      var v = lista[k];
      if (!pronto(v)) {
        carica(v);
        var via = function () { v.removeEventListener("canplay", via); riscalda(v); };
        if (v.readyState >= 3) via(); else v.addEventListener("canplay", via);
      }
      aggiornaPunti();
      attendiScelta();
    }
    function mostra(k) {
      var prec = lista[i];
      i = k;
      var v = lista[i];
      carica(v);
      v.classList.add("attivo");
      if (inVista) parti(v); /* riprende da dove era rimasto */
      if (prec && prec !== v) {
        clearTimeout(prec._tVel); clearTimeout(prec._tGuarda);
        prec.playbackRate = 1; /* ai giri successivi tutti a velocità normale */
        prec.classList.remove("attivo");
        setTimeout(function () { if (!prec.classList.contains("attivo")) ferma(prec); }, 600);
      }
      aggiornaPunti();
    }
    function giro() {
      if (!inVista || doc.visibilityState !== "visible" || lista.length < 2) return;
      if (leggeri || scelta >= 0 || adesso() < pausaFino) return;
      for (var d = 1; d < lista.length; d++) {
        var j = (i + d) % lista.length;
        if (pronto(lista[j])) { mostra(j); return; }
      }
    }
    /* cambio di velocità a piccoli passi (6 passi in 0,3 s), mai uno scatto */
    function velocita(v, da, a, fatto) {
      clearTimeout(v._tVel);
      var k = 0;
      (function passo() {
        k++;
        try { v.playbackRate = da + (a - da) * k / 6; } catch (_) {}
        if (k < 6) v._tVel = setTimeout(passo, 50); else if (fatto) fatto();
      })();
    }
    function primaVelocita(v) {
      v._tVel = setTimeout(function () {
        if (!v.classList.contains("attivo") || avanti(v) < 3) return; /* poco in memoria: resta a velocità normale */
        velocita(v, 1, 2);
        (function guarda() {
          if (!v.classList.contains("attivo")) return;
          if (v.playbackRate > 1 && avanti(v) < 1.5) { clearTimeout(v._tVel); v.playbackRate = 1; return; }
          v._tGuarda = setTimeout(guarda, 200);
        })();
      }, 2000);
    }
    function finePrimo(v) {
      clearTimeout(v._tVel); clearTimeout(v._tGuarda);
      if (v.playbackRate !== 1) {
        if (v.classList.contains("attivo")) velocita(v, v.playbackRate, 1); else v.playbackRate = 1;
      }
    }
    function programma(primo, ritardo) {
      clearTimeout(tGiro);
      if (leggeri) return; /* rete lenta o risparmio dati: un solo video, nessun giro */
      function passo() {
        giro();
        tGiro = setTimeout(passo, ciclo());
      }
      if (!primo) { tGiro = setTimeout(passo, ritardo || ciclo()); return; }
      /* primo giro (Francesco 15/10/2026): circa 5 secondi contati da quando il video parte davvero; i primi 2
         a velocità normale (l'ape si vede con calma), poi si passa piano a 2x per mostrare anche l'aiuola,
         l'ulivo e l'ingresso. Il 2x solo con almeno 3 secondi già in memoria, così non si ferma mai. */
      var v = lista[i];
      var via = function () {
        clearTimeout(tGiro);
        if (!meno.matches) primaVelocita(v);
        tGiro = setTimeout(function () { finePrimo(v); passo(); }, Math.max(ciclo(), 5000));
      };
      /* «parte davvero» = in riproduzione con i dati: lo si controlla ogni 100 ms (l'evento playing può essere
         già passato prima che questo script arrivasse) */
      var t0 = adesso(), fatto = false;
      var via0 = via;
      via = function () { if (fatto) return; fatto = true; v.removeEventListener("playing", via); via0(); };
      v.addEventListener("playing", via);
      (function controlla() {
        if (fatto) return;
        if ((!v.paused && v.readyState >= 3 && v.currentTime > 0) || adesso() - t0 > 15000) { via(); return; }
        tGiro = setTimeout(controlla, 100);
      })();
    }
    function avvia() {
      var tipo = mq.matches ? "pc" : "tel";
      tutti("video.hero__v", hero).forEach(function (v) {
        if (v.getAttribute("data-set") !== tipo) { v.classList.remove("attivo"); ferma(v); }
      });
      lista = tutti('video.hero__v[data-set="' + tipo + '"]', hero);
      if (!lista.length) return;
      punti.innerHTML = "";
      if (leggeri) { /* solo il primo video */
        lista = [lista.filter(function (v) { return v.classList.contains("attivo"); })[0] || lista[0]];
      }
      if (lista.length > 1) {
        lista.forEach(function (v, k) {
          var b = doc.createElement("button");
          b.type = "button"; b.className = "hero__punto";
          b.setAttribute("aria-label", "Video " + (k + 1) + " di " + lista.length);
          b.addEventListener("click", function () { scegli(k); });
          punti.appendChild(b);
        });
      }
      var attivi = lista.filter(function (v) { return v.classList.contains("attivo"); });
      i = attivi.length ? lista.indexOf(attivi[0]) : 0;
      lista.forEach(function (v, n) { if (n !== i) v.classList.remove("attivo"); });
      mostra(i);
      programma(primoGiro);
      primoGiro = false;
      if (!leggeri) coda();
    }
    function riprendi() {
      if (!inVista || doc.visibilityState !== "visible" || !lista.length) return;
      parti(lista[i]);
      if (!leggeri) coda();
    }
    avvia();
    ascolta(mq, avvia);
    ascolta(meno, function () { programma(false); });
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
      var eroe = v.classList.contains("hero__v");
      if (!eroe && (leggeri || doppione(v))) return;
      var inOnda = !eroe || v.classList.contains("attivo");
      if (inOnda && visibile(scatola(v))) { if (eroe) parti(v); else partiClip(v); return; }
      if (eroe && !v.getAttribute("data-caricato")) return; /* i video in cima li prepara il loro giro */
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
    clip.forEach(function (v) { if (v.paused && visibile(scatola(v))) partiClip(v); });
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
        el.src = scegliSrc(b);
        media.appendChild(el);
        var p; try { p = el.play(); } catch (_) { p = null; }
        if (p && p.catch) p.catch(function () {});
      } else {
        el = doc.createElement("img");
        el.alt = alt; el.decoding = "async";
        if (b.getAttribute("data-srcset")) { el.sizes = "(min-width: 900px) 80vw, 100vw"; el.srcset = b.getAttribute("data-srcset"); }
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
      radice.classList.add("lightbox-aperta");
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
      radice.classList.remove("lightbox-aperta");
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
    var pos = 0, impostato = -1, ultimoT = null, raf = null, inVista = false, ultimoUtente = -1e9;
    var sopra = false, tocco = false, dentro = false, trascina = false, mosso = false, riprendi = 0;
    var x0 = 0, s0 = 0, bloccaClick = false;
    function periodo() { return lista.offsetWidth / 2; }
    function ferma() { return sopra || tocco || dentro || trascina || (lb && lb.aperta()) || meno.matches || adesso() < riprendi; }
    function passo(t) {
      raf = requestAnimationFrame(passo);
      if (ultimoT === null) { ultimoT = t; pos = striscia.scrollLeft; return; }
      var dt = Math.min(64, t - ultimoT);
      ultimoT = t;
      var P = periodo();
      /* ritorno all'inizio del giro (gli elementi sono due volte di fila): mai mentre la persona trascina o
         mentre la striscia scivola per inerzia, altrimenti su iPhone salta */
      if (!tocco && !trascina && adesso() - ultimoUtente > 800 && P > striscia.clientWidth && striscia.scrollLeft >= P) {
        striscia.scrollLeft -= P;
        impostato = striscia.scrollLeft;
        pos = impostato;
      }
      if (ferma()) { pos = striscia.scrollLeft; return; }
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
        ultimoUtente = adesso();
      }
    }, { passive: true });
    striscia.addEventListener("pointerenter", function (e) { if (e.pointerType === "mouse") sopra = true; });
    striscia.addEventListener("pointerleave", function (e) { if (e.pointerType === "mouse") { sopra = false; riprendi = adesso() + 300; } });
    striscia.addEventListener("touchstart", function () { tocco = true; }, { passive: true });
    function fineTocco() { tocco = false; riprendi = adesso() + 2000; ultimoUtente = adesso(); }
    striscia.addEventListener("touchend", fineTocco, { passive: true });
    striscia.addEventListener("touchcancel", fineTocco, { passive: true });
    /* si ferma per il focus solo se arriva dalla tastiera: dopo un clic, un trascinamento o la chiusura
       della foto a schermo intero deve ripartire */
    striscia.addEventListener("focusin", function (e) {
      var daTastiera = true;
      try { daTastiera = e.target.matches(":focus-visible"); } catch (_) {}
      dentro = daTastiera;
    });
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
      ultimoUtente = adesso();
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
    function apri(voce, segui, daLink) {
      var era = voce.classList.contains("aperta");
      voci.forEach(function (x) { if (x !== voce) imposta(x, false); });
      imposta(voce, segui ? true : !era);
      if (daLink) return; /* lo scorrimento lo fa apriDaIndirizzo */
      /* se chiudendo una voce sopra quella toccata la pagina "sale", la si riporta in vista */
      setTimeout(function () {
        var top = voce.getBoundingClientRect().top, alto = testata ? testata.offsetHeight : 0;
        if (top < alto + 8) window.scrollBy({ top: top - alto - 16, behavior: meno.matches ? "auto" : "smooth" });
      }, meno.matches ? 0 : 540);
    }
    voci.forEach(function (voce) {
      voce.querySelector(".fisarmonica__btn").addEventListener("click", function () { apri(voce, false); });
      voceServizio["#" + voce.id] = function () {
        /* aperta da un link: niente animazioni, così la voce chiusa sopra non sposta la pagina dopo */
        f.classList.add("senza-transizione");
        apri(voce, true, true);
        setTimeout(function () { f.classList.remove("senza-transizione"); }, 800);
        return voce;
      };
    });
  });
  function apriDaIndirizzo(h) {
    if (!voceServizio[h]) return;
    var voce = voceServizio[h]();
    var vai = function () { scorriSubito(function () { voce.scrollIntoView({ block: "start", behavior: "auto" }); }); };
    setTimeout(vai, 600);
    if (doc.readyState !== "complete") window.addEventListener("load", function () { setTimeout(vai, 50); }, { once: true });
  }
  apriDaIndirizzo(location.hash);
  window.addEventListener("hashchange", function () { apriDaIndirizzo(location.hash); });
  tutti('a[href*="#servizio-"]').forEach(function (a) {
    a.addEventListener("click", function () {
      var h = a.getAttribute("href").replace(/^[^#]*/, "");
      if (location.hash === h) apriDaIndirizzo(h); /* stesso link di prima: hashchange non arriva */
    });
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
