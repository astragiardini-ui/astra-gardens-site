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
  /* «Risparmio dati» attivo o rete da 2G: in cima un solo video, nella striscia solo locandine.
     19/10/2026: la stima di Chrome (effectiveType) NON si ascolta più a metà visita. Misurato: su una linea da
     20 Mbit/s, dopo un minuto di video la stima scendeva a «3g» e 1,5 Mbit/s (la linea era piena dei nostri stessi
     video) e il sito passava ai dati leggeri per sempre: l'apertura si fermava su un video e la striscia restava sulle
     foto. All'apertura vale solo il 2G vero; la linea la misura il primo video (main.js, «lenta»). A metà visita conta
     solo il Risparmio dati scelto dalla persona. */
  var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  var leggeri = false;
  try { leggeri = !!(conn && (conn.saveData || /(^|-)2g$/.test(conn.effectiveType || ""))); } catch (_) {}
  if (leggeri) radice.classList.add("dati-leggeri");
  if (conn && conn.addEventListener) conn.addEventListener("change", function () {
    try {
      if (!leggeri && conn.saveData) {
        leggeri = true;
        radice.classList.add("dati-leggeri");
      }
    } catch (_) {}
  });
  /* telefono (anche in orizzontale): versioni leggere dei video, NOME-tel.mp4 (Francesco 15/10/2026) */
  var heroEl = doc.querySelector("[data-hero]");
  var telefono = window.matchMedia((heroEl && heroEl.getAttribute("data-mq-tel")) || "(max-width: 899.98px), (max-height: 499.98px)").matches;
  /* linea lenta: la misura il primo video in cima mentre si scarica (19/10/2026). Se la linea porta meno di 1,6 volte
     il peso del video, anche sul computer i video successivi e quelli a schermo intero usano le versioni leggere */
  var lenta = false;
  function scegliSrc(el) {
    var t = el.getAttribute("data-src-tel");
    return t && (telefono || lenta) ? t : el.getAttribute("data-src");
  }
  /* i riquadri (striscia, introduzione, chi siamo) sono piccoli: sempre la versione leggera, 1080 pieno a 4,5 Mbit/s */
  function srcRiquadro(el) { return el.getAttribute("data-src-tel") || el.getAttribute("data-src"); }

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
  var alRifiuto = null; /* l'apertura: se il telefono rifiuta l'avvio, la copertina si toglie subito */
  /* Il primo video in cima ha la precedenza su tutta la rete: gli altri video (striscia, introduzione, chi siamo)
     non mettono nemmeno la sorgente finché il primo non ha in memoria il suo primo turno (o è scaricato).
     Lo segnala il blocco dell'apertura; senza apertura (privacy) si parte subito. */
  var primoPronto = !doc.querySelector("[data-hero]");
  var inAttesaPrimo = [];
  function quandoPrimoPronto(fn) { if (primoPronto) fn(); else inAttesaPrimo.push(fn); }
  function primoEPronto() {
    if (primoPronto) return;
    primoPronto = true;
    inAttesaPrimo.splice(0).forEach(function (fn) { try { fn(); } catch (_) {} });
  }
  function scatola(v) { return v.closest("[data-clip]") || v.parentNode; }
  function riquadro(v) { return !!v.closest("[data-clip]"); }
  function visibile(el) {
    var r = el.getBoundingClientRect();
    return r.bottom > -40 && r.top < window.innerHeight + 40 && r.right > 0 && r.left < window.innerWidth && r.width > 0;
  }
  function haSorgente(v) { return !!(v.currentSrc || v.getAttribute("src") || v.querySelector("source")); }
  function parti(v) {
    /* video fuori dall'apertura: l'indirizzo si mette solo adesso (versione leggera sul telefono) */
    if (!haSorgente(v) && !v.classList.contains("hero__v") && v.getAttribute("data-src")) v.src = srcRiquadro(v);
    if (!haSorgente(v)) return;
    if (v.preload !== "auto") v.preload = "auto";
    v.muted = true;
    var p;
    try { p = v.play(); } catch (_) { p = null; }
    if (p && typeof p.then === "function") {
      p.then(function () { if (!riquadro(v)) scatola(v).classList.add("in-play"); })
       .catch(function (err) {
         if (!err || err.name !== "AbortError") {
           serveSblocco = true;
           if (alRifiuto && v.classList.contains("hero__v") && v.classList.contains("attivo")) alRifiuto(err);
         }
       });
    } else if (!v.paused && !riquadro(v)) {
      scatola(v).classList.add("in-play");
    }
  }
  function ferma(v) {
    if (riquadro(v)) scatola(v).classList.remove("in-play"); /* quando torna nello schermo riparte dalla foto */
    if (v.paused) return;
    v._fermatoDaNoi = true;
    v.pause();
  }
  function scaricato(v) {
    try {
      var b = v.buffered;
      return v.readyState >= 4 && b.length && b.end(b.length - 1) >= (v.duration || 0) - 0.3;
    } catch (_) { return true; }
  }
  /* secondi di filmato già in memoria davanti al punto in cui è il video; in loop conta anche l'inizio del giro dopo */
  function avanti(v) {
    try {
      var b = v.buffered, t = v.currentTime, d = v.duration || 0;
      for (var k = 0; k < b.length; k++) {
        if (b.start(k) <= t + 0.1 && b.end(k) > t) {
          var a = b.end(k) - t;
          if (v.loop && d && k > 0 && b.end(k) >= d - 0.1 && b.start(0) <= 0.1) a += b.end(0);
          return a;
        }
      }
    } catch (_) {}
    return 0;
  }
  video.forEach(function (v) {
    v.muted = true; v.defaultMuted = true; v.loop = true; v.playsInline = true;
    v.setAttribute("muted", ""); v.setAttribute("playsinline", ""); v.removeAttribute("controls");
    try { v.disablePictureInPicture = true; } catch (_) {}
    try { v.disableRemotePlayback = true; } catch (_) {}
    v.addEventListener("playing", function () { if (!riquadro(v)) scatola(v).classList.add("in-play"); });
    v.addEventListener("pause", function () {
      if (v._fermatoDaNoi) { v._fermatoDaNoi = false; return; }
      setTimeout(function () {
        var inOnda = !v.classList.contains("hero__v") || v.classList.contains("attivo");
        if (v.paused && inOnda && doc.visibilityState === "visible" && visibile(scatola(v))) parti(v);
      }, 300);
    });
    v.addEventListener("contextmenu", function (e) { e.preventDefault(); });
  });

  /* le clip partono quando entrano nello schermo e si fermano quando escono.
     19/10/2026 (video che si bloccavano): si scarica UNA clip alla volta, fra quelle sullo schermo (la prossima parte
     quando quella prima ha 4 s davanti o è tutta arrivata), così non si rubano la linea; e il video compare sopra la
     foto solo quando gira davvero con almeno 2 s già in memoria, o 1 s con la linea che tiene il passo (Safari sul
     telefono parte con meno di 2 s e la memoria cresce piano: con la sola soglia dei 2 s restava sulla foto). Se si
     ferma, o la memoria sta per finire con la linea che non tiene il passo, torna la foto (dissolvenza rapida) e il
     video ricompare quando ha di nuovo strada davanti: mai un fotogramma fermo. Prima una clip aspettava che finisse lo scarico dello stesso file in cima, e un video in cima fermo fuori
     schermo risultava «in scarico» per sempre: la striscia restava sulle foto. */
  var clip = tutti("[data-clip] video");
  function caricaClip(x) {
    if (!x._avviato || !x._vista || x.error || scaricato(x)) return false;
    if (adesso() - (x._t0 || 0) > 15000) return false; /* linea lentissima: dopo 15 s passa la prossima */
    return x.readyState < 3 || avanti(x) < 4; /* con 4 s davanti regge anche dividendo la linea con la prossima */
  }
  function partiClip(v) {
    clearTimeout(v._attesa);
    if (leggeri) return; /* resta la locandina: il video si guarda toccandolo */
    if (!primoPronto) { if (!v._inCoda) { v._inCoda = true; quandoPrimoPronto(function () { v._inCoda = false; if (v._vista) partiClip(v); }); } return; }
    if (!v._avviato && clip.some(function (x) { return x !== v && caricaClip(x); })) {
      v._attesa = setTimeout(function () { if (v._vista) partiClip(v); }, 400);
      return;
    }
    if (!v._avviato) { v._avviato = true; v._t0 = adesso(); }
    parti(v);
  }
  /* la memoria cresce più in fretta di quanto il video la consuma? (secondi di filmato in arrivo ogni secondo, sull'ultimo
     secondo circa: sopra 1 la linea tiene il passo) */
  function velocita(v) {
    var now = adesso(), fine = 0;
    try { var b = v.buffered; if (b.length) fine = b.end(b.length - 1); } catch (_) {}
    if (!v._bT || now - v._bT >= 1000) {
      if (v._bT) v._vel = (fine - v._bE) / ((now - v._bT) / 1000);
      v._bE = fine; v._bT = now;
    }
    return v._vel || 0;
  }
  function guardaClip(v) {
    if (!v._avviato) return;
    var box = scatola(v), t = v.currentTime, mosso = t !== v._tPrec, vel = velocita(v);
    v._tPrec = t;
    var tutto = scaricato(v), davanti = avanti(v);
    if (box.classList.contains("in-play")) {
      /* fermo da 300 ms, o memoria quasi finita con la linea che non tiene il passo: torna la foto prima del fermo */
      var fermo = !v.paused && !v.seeking && !mosso && ++v._fermo >= 2;
      if (mosso) v._fermo = 0;
      if (fermo || (!v.paused && !tutto && davanti < 0.4 && vel < 1)) {
        box.classList.add("rapido"); box.classList.remove("in-play"); v._fermo = 0;
      }
    } else if (v._vista && mosso && !v.paused && v.readyState >= 3 && (tutto || davanti >= 2 || (davanti >= 1 && vel >= 1.1))) {
      box.classList.remove("rapido");
      box.classList.add("in-play");
    }
  }
  if (haIO) {
    var osservaClip = new IntersectionObserver(function (voci) {
      voci.forEach(function (voce) {
        var v = voce.target.querySelector("video");
        if (!v) return;
        v._vista = voce.isIntersecting;
        if (voce.isIntersecting) partiClip(v); else { clearTimeout(v._attesa); ferma(v); }
      });
    }, { rootMargin: "40px 0px 40px 0px", threshold: 0 });
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
  /* la guardia di tutti i video che si vedono: ogni 150 ms (apertura, riquadri, finestra a schermo intero) */
  var guardie = [function () { clip.forEach(guardaClip); }];
  setInterval(function () {
    if (doc.visibilityState !== "visible") return;
    guardie.forEach(function (g) { try { g(); } catch (_) {} });
  }, 150);

  /* ---------- Apertura: i video interi che si danno il cambio ogni 2 secondi ----------
     Richiesta di Francesco (15/10/2026): «deve cambiare ogni due secondi e continuare in loop».
     - Ogni 2 s (6 s con «riduci movimento») si passa al video successivo GIÀ PRONTO; se nessun altro è pronto
       si resta su quello in onda: mai un fotogramma nero o fermo.
     - Il video nascosto si mette in pausa e quando torna riprende da dove era: a ogni giro si vedono i
       secondi successivi. Ogni video gira anche in loop su se stesso.
     - Il primo (gerani con l'ape) va SEMPRE a velocità normale (Francesco 16/10/2026: «non voglio che lo velocizzi»):
       l'ape vola via a circa 0,9 s di filmato, a 2,6 s parte una dissolvenza morbida di 1,2 s nel video successivo,
       poi il giro normale. Il tempo si conta sul filmato (currentTime), non sull'orologio: se la rete rallenta, il
       taglio cade comunque nello stesso punto della ripresa.
     - Si scaricano uno alla volta, in ordine: il successivo parte quando il precedente ha finito (o quando il
       browser smette da solo di scaricarlo); mai due insieme all'inizio.
     Regole del 19/10/2026 («il video si blocca e non si carica bene»), misurate con Chrome e Safari su linee lente:
     - si passa a un video solo se è PRONTO: scaricato tutto, o con in memoria il suo turno (2,5 s) più 0,5 s di margine;
       se nessuno è pronto si resta su quello in onda, che intanto continua: un'attesa più lunga, mai un fermo;
     - si prepara un video alla volta, nell'ordine del giro, e solo quando quello in onda ha almeno 4 s davanti (o è
       tutto scaricato): quello che si vede ha sempre la precedenza sulla linea;
     - se quello in onda si ferma (o sta per finire la memoria), dissolvenza rapida su uno pronto;
     - la linea si misura sul primo video: se è lenta, sul computer i successivi usano le versioni leggere. */
  var hero = doc.querySelector("[data-hero]");
  if (hero) (function () {
    var mq = window.matchMedia(hero.getAttribute("data-mq"));
    var punti = hero.querySelector(".hero__punti");
    var lista = [], i = 0, tGiro = null, tCoda = null, inVista = true, primoGiro = true;
    /* ---- Primo video e copertina (18/10/2026) ----
       Il primo video di ogni serie ha la sorgente nell'HTML (<source media>) e l'autoplay: il browser lo scarica e lo
       avvia mentre legge la pagina. Qui lo si ADOTTA così com'è: niente nuovo indirizzo, niente salti, niente
       ripartenze. L'altra serie (computer sul telefono e viceversa) non ha scelto nessun file: 0 byte.
       La copertina verde si toglie (0,3 s) appena il video AVANZA davvero: due fotogrammi presentati con il tempo che
       cresce (requestVideoFrameCallback), o il tempo del filmato oltre 0,3 s. Si toglie prima se il telefono rifiuta
       l'avvio (Risparmio energetico: resta la locandina e il video parte al primo tocco) o se il file non arriva; e
       comunque al TETTO, misurato con Safari del simulatore iOS su una rete 4G lenta a cache vuota. */
    /* ms dall'apertura della pagina. Misure 18/10/2026 (Safari iOS 18.6, cache vuota): il video avanza a 2,8 s con
       8 Mbit/s, 3,5 s con 5 Mbit/s, 4,2 s con 3,5 Mbit/s (quanto il video stesso). Oltre i 7 s si mostra la locandina. */
    var TETTO = 7000;
    var copertina = hero.querySelector(".hero__copertina");
    var scoperto = !copertina || getComputedStyle(copertina).display === "none";
    var filmAlloScoperto = 0; /* secondi di filmato già passati quando l'apertura diventa visibile */
    function scopri(motivo) {
      if (scoperto) return;
      scoperto = true;
      var a = lista[i];
      filmAlloScoperto = a && motivo === "moto" ? a.currentTime : 0;
      hero.classList.add("scoperto");
      hero.setAttribute("data-scoperto", motivo + " " + Math.round(adesso()));
    }
    function sceltaNellHtml(v) { /* il file che il browser ha scelto leggendo la pagina, "" se nessuno */
      if (v.currentSrc) return v.currentSrc;
      var s = tutti("source", v).filter(function (x) {
        var m = x.getAttribute("media");
        return !m || window.matchMedia(m).matches;
      })[0];
      return s ? s.src : "";
    }
    tutti("video.hero__v[data-primo]", hero).forEach(function (v) {
      if (sceltaNellHtml(v)) {
        v.setAttribute("data-caricato", "1");
        v._inizioCarico = 0; /* lo scarico è partito con la pagina */
        /* errore vero: il video stesso, o la <source> giusta per questo schermo senza un'altra valida dopo. Una <source>
           con media che non vale manda anch'essa «error» (regola HTML) e il browser passa alla successiva: non conta. */
        v.addEventListener("error", function (e) {
          var t = e.target;
          if (t === v) { scopri("errore"); return; }
          if (!t || t.tagName !== "SOURCE") return;
          var vale = function (x) { var m = x.getAttribute("media"); return !m || window.matchMedia(m).matches; };
          if (!vale(t)) return;
          var tutte = tutti("source", v);
          if (!tutte.slice(tutte.indexOf(t) + 1).some(vale)) scopri("errore");
        }, true);
      } else {
        v.removeAttribute("autoplay"); /* serie che non si vede: parte solo se diventa quella giusta */
      }
    });
    /* «avanza davvero»: un fotogramma presentato con il tempo che cresce, il logo bianco già caricato (niente logo che
       compare dopo il video), e il filmato con un po' di strada davanti: almeno 1 s già in memoria, oppure già 0,4 s
       percorsi senza fermarsi. Visto sul sito vero il 18/10/2026: Safari a volte parte con pochi decimi in memoria,
       va 0,3 s e si ferma quasi un secondo; così quella pausa resta sotto la copertina. Mai più di 1,2 s di filmato
       sotto la copertina: l'ape vola via a 0,9 s. */
    var logoAperta = hero.querySelector(".hero__marchio img");
    function quandoAvanza(v, fn) {
      var fatto = false, ultimo = -1, tPrec = -1;
      function pronto(t) {
        if (t >= 1.2) return true;
        var logo = !logoAperta || logoAperta.complete;
        return logo && (t >= 0.4 || scaricato(v) || avanti(v) >= 1);
      }
      function ok() { if (!fatto) { fatto = true; fn(); } }
      if (typeof v.requestVideoFrameCallback === "function") {
        var cb = function (ora, md) {
          if (fatto) return;
          var t = md && typeof md.mediaTime === "number" ? md.mediaTime : v.currentTime;
          if (!v.paused && ultimo >= 0 && t > ultimo && t > 0.04 && pronto(t)) { ok(); return; }
          if (!v.paused) ultimo = t;
          v.requestVideoFrameCallback(cb);
        };
        v.requestVideoFrameCallback(cb);
      }
      (function guarda() { /* riserva senza requestVideoFrameCallback: il filmato oltre 0,3 s e ancora in movimento */
        if (fatto) return;
        var t = v.currentTime;
        if (!v.paused && v.readyState >= 3 && t > 0.3 && tPrec >= 0 && t > tPrec && pronto(t)) { ok(); return; }
        tPrec = t;
        setTimeout(guarda, 50);
      })();
    }
    if (!scoperto) {
      alRifiuto = function (err) { if (err && err.name === "NotAllowedError") scopri("bloccato"); };
      var tetto = function () {
        if (scoperto) return;
        /* scheda aperta dietro: il tetto vale da quando la pagina si vede, con un po' di margine */
        if (doc.visibilityState !== "visible") {
          var vista = function () {
            if (doc.visibilityState !== "visible") return;
            doc.removeEventListener("visibilitychange", vista);
            setTimeout(function () { scopri("tetto"); }, 2500);
          };
          doc.addEventListener("visibilitychange", vista);
          return;
        }
        scopri("tetto");
      };
      setTimeout(tetto, Math.max(0, TETTO - adesso()));
    }
    var scelta = -1, pausaFino = 0, tScelta = null;
    var NORMALE = 500, MORBIDA = 1200, RAPIDA = 250; /* ms: dissolvenza di ogni cambio, del primo (dopo l'ape) e del soccorso (style.css) */
    function ciclo() { return meno.matches ? 6000 : 2000; }
    /* secondi di filmato del primo video prima della dissolvenza morbida */
    function fineTurno() { return meno.matches ? 6 : 2.6; }
    function sorgente(v) { return scegliSrc(v); }
    function carica(v) {
      if (v.getAttribute("data-caricato")) return;
      v.setAttribute("data-caricato", "1");
      v._inizioCarico = adesso();
      v.poster = v.getAttribute("data-poster");
      v.preload = "auto";
      v.src = sorgente(v);
      try { v.load(); } catch (_) {}
    }
    /* secondi di filmato che servono per un turno intero (il turno più la dissolvenza) più mezzo secondo di margine.
       Basta mezzo secondo perché nessun altro video scarica finché quello in onda non ha 4 s davanti (comodo). */
    function serve() { return (ciclo() + NORMALE) / 1000 + 0.5; }
    /* pronto = scaricato tutto, oppure ha già in memoria il suo turno con il margine */
    function pronto(v) {
      if (!v.getAttribute("data-caricato") || v.readyState < 3 || v._riscalda || v.error) return false;
      return scaricato(v) || avanti(v) >= serve();
    }
    /* Un video fermo il browser lo scarica solo per qualche decimo di secondo: per averne pronto un pezzo
       lo si fa girare nascosto finché ha in memoria il suo turno con il margine, poi lo si ferma e si torna al punto
       di prima (con la chiave ogni secondo il ritorno indietro è immediato). */
    function riscalda(v) {
      if (v._riscalda || v.classList.contains("attivo")) return;
      v._riscalda = true;
      var da = v.currentTime, t0 = adesso();
      function basta() {
        if (!v._riscalda) return;
        if (v.classList.contains("attivo")) { v._riscalda = false; return; }
        if (scaricato(v) || avanti(v) + Math.max(0, v.currentTime - da) >= serve() + 0.5 || adesso() - t0 > 20000) {
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
    /* il primo video ha in memoria tutto il primo turno: fino alla fine della dissolvenza morbida, più un margine */
    function primoTurnoInMemoria(v) {
      var serve = fineTurno() + MORBIDA / 1000 + 0.6;
      try { var b = v.buffered; return scaricato(v) || (b.length && b.end(b.length - 1) >= serve); } catch (_) { return true; }
    }
    /* quello in onda ha strada davanti: si può preparare il prossimo senza togliergli la linea. Il primo video (l'ape),
       finché è in onda per la prima volta, è comodo quando ha in memoria tutto il suo primo turno e la linea è stata
       misurata: così il secondo è pronto per la dissolvenza dopo l'ape e si scarica già nella versione giusta. */
    var misurata = false, primoCambiato = false;
    function comodo(v) {
      /* su linea lenta il primo video non divide la linea finché non ha 4 s davanti: meglio l'ape più a lungo che a scatti */
      if (v === lista[0] && !primoCambiato && !lenta) return misurata && primoTurnoInMemoria(v);
      return (misurata || v !== lista[0]) && (scaricato(v) || avanti(v) >= 4);
    }
    /* un video che si sta preparando (primo scarico o riscaldamento) e non è ancora pronto */
    function inPreparazione(v) {
      if (v._riscalda) return true;
      if (v === lista[i] || !v.getAttribute("data-caricato") || v.error || pronto(v)) return false;
      if (adesso() - (v._inizioCarico || 0) > 20000) return false; /* rete lentissima: dopo 20 s si passa oltre */
      return v.networkState === 2 || v.readyState < 3;
    }
    function coda() {
      clearTimeout(tCoda);
      if (!primoPronto && lista.length && lista[0].getAttribute("data-caricato") &&
          (primoTurnoInMemoria(lista[0]) || adesso() - (lista[0]._inizioCarico || 0) > 25000)) primoEPronto();
      if (leggeri) { if (!primoPronto) tCoda = setTimeout(coda, 400); return; }
      if (!inVista || doc.visibilityState !== "visible" || !lista.length) return;
      tCoda = setTimeout(coda, 300);
      /* il primo turno dell'apertura non si tocca; poi un video alla volta, solo se quello in onda è comodo */
      if (!primoPronto || !comodo(lista[i]) || lista.some(inPreparazione)) return;
      for (var d = 1; d < lista.length; d++) {
        var v = lista[(i + d) % lista.length];
        if (pronto(v)) continue;
        if (!v.getAttribute("data-caricato")) {
          carica(v);
          (function (x) {
            var via = function () { x.removeEventListener("canplay", via); riscalda(x); };
            if (x.readyState >= 3) via(); else x.addEventListener("canplay", via);
          })(v);
        } else {
          riscalda(v);
        }
        return;
      }
    }
    /* la linea si misura sul primo video mentre si scarica (prima che parta qualsiasi altra cosa): secondi di filmato
       arrivati per secondo. Sotto 1,6 la linea porta poco più del peso del video: i successivi vanno leggeri. */
    function misuraLinea(v) {
      var t0 = null, b0 = 0, inizio = adesso();
      (function giro() {
        var b = 0;
        try { if (v.buffered.length) b = v.buffered.end(v.buffered.length - 1); } catch (_) {}
        var now = adesso();
        if (t0 === null && (v.error || now - inizio > 15000)) { misurata = true; coda(); return; } /* il primo non arriva */
        if (t0 === null && b > 0) { t0 = now; b0 = b; }
        if (t0 !== null) {
          var dt = (now - t0) / 1000, r = dt > 0 ? (b - b0) / dt : 0, finito = scaricato(v);
          if (finito || (b - b0 >= 3 && dt >= 1) || dt > 12) {
            if (!finito && r < 1.6) lenta = true;
            misurata = true;
            hero.setAttribute("data-linea", (finito ? "scaricato " : "") + r.toFixed(2) + (lenta ? " lenta" : ""));
            coda();
            return;
          }
        }
        setTimeout(giro, 200);
      })();
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
    /* morbida = la dissolvenza lunga del primo cambio, rapida = il soccorso a un video che si è fermato. Chi entra sale
       sopra, chi esce resta pieno sotto finché è coperto («uscente»), poi si ferma: niente calo di luce a metà. */
    function mostra(k, morbida, rapida) {
      var prec = lista[i];
      if (prec === lista[0] && k !== 0) primoCambiato = true;
      i = k;
      var v = lista[i];
      var durata = morbida ? MORBIDA : rapida ? RAPIDA : NORMALE;
      carica(v);
      hero.classList.toggle("morbida", !!morbida);
      hero.classList.toggle("rapida", !morbida && !!rapida);
      lista.forEach(function (x) { /* un cambio a metà di un altro: chi era sotto si toglie subito */
        if (x !== prec && x !== v && x.classList.contains("uscente")) { clearTimeout(x._tFuori); x.classList.remove("uscente"); ferma(x); }
      });
      if (prec && prec !== v) {
        clearTimeout(prec._tFuori);
        prec.classList.add("uscente");
        prec.classList.remove("attivo");
      }
      clearTimeout(v._tFuori);
      v.classList.remove("uscente");
      v.classList.add("attivo");
      v._dal = adesso(); /* la guardia lo lascia partire prima di giudicarlo */
      if (inVista) parti(v); /* riprende da dove era rimasto, sempre a velocità normale */
      if (prec && prec !== v) {
        prec._tFuori = setTimeout(function () {
          prec.classList.remove("uscente");
          if (!prec.classList.contains("attivo")) ferma(prec);
        }, durata + 100);
      }
      aggiornaPunti();
    }
    /* il prossimo video con il suo turno già in memoria, -1 se nessuno è pronto */
    function prossimo() {
      for (var d = 1; d < lista.length; d++) {
        var j = (i + d) % lista.length;
        if (pronto(lista[j])) return j;
      }
      return -1;
    }
    function giro() {
      if (!inVista || doc.visibilityState !== "visible" || lista.length < 2) return;
      if (leggeri || scelta >= 0 || adesso() < pausaFino) return;
      var j = prossimo();
      if (j >= 0) mostra(j);
    }
    /* Soccorso: il video in onda si è fermato (o ha meno di mezzo secondo in memoria e il file non è finito). Si passa
       con una dissolvenza rapida a un video pronto; se nessuno lo è, a quello con più strada davanti (almeno 1,5 s e
       più di quello in onda). Se non c'è niente di meglio si resta: il video riparte da solo appena arriva il resto. */
    var tPrecA = -1;
    function soccorri() {
      var j = prossimo();
      if (j < 0) {
        var meglio = Math.max(1.5, avanti(lista[i]) + 1);
        lista.forEach(function (x, k) {
          if (k !== i && x.getAttribute("data-caricato") && !x._riscalda && !x.error && x.readyState >= 3 && avanti(x) >= meglio) { j = k; meglio = avanti(x); }
        });
      }
      if (j < 0) return;
      mostra(j, false, true);
      programma(false);
    }
    function guardaHero() {
      var a = lista[i];
      if (!a || !scoperto || !inVista || leggeri || lista.length < 2 || scelta >= 0) { tPrecA = -1; return; }
      var t = a.currentTime, mosso = t !== tPrecA;
      tPrecA = t;
      if (a.paused || a.seeking || adesso() - (a._dal || 0) < 450) return;
      if (!mosso || (!scaricato(a) && avanti(a) < 0.5)) soccorri();
    }
    guardie.push(guardaHero);
    function programma(primo, ritardo) {
      clearTimeout(tGiro);
      if (leggeri) return; /* rete lenta o risparmio dati: un solo video, nessun giro */
      function passo() {
        giro();
        tGiro = setTimeout(passo, ciclo());
      }
      if (!primo) { tGiro = setTimeout(passo, ritardo || ciclo()); return; }
      /* primo turno: l'ape a velocità normale fino a fineTurno() secondi di FILMATO, poi la dissolvenza morbida nel
         primo video pronto (se nessuno è pronto si resta sull'ape, che continua da sola). Dopo il cambio il nuovo
         video resta pieno quanto gli altri (ciclo meno la dissolvenza normale), poi il giro di sempre. */
      var v = lista[i], t0 = adesso();
      (function guarda() {
        if (lista[i] !== v || !v.classList.contains("attivo")) return; /* puntino toccato: decide la scelta */
        if (v.paused && v.currentTime === 0 && adesso() - t0 > 15000) { passo(); return; } /* non parte: giro normale */
        if (scoperto && v.currentTime >= filmAlloScoperto + fineTurno() && inVista && doc.visibilityState === "visible" && scelta < 0) {
          var j = prossimo();
          if (j >= 0) {
            mostra(j, true);
            tGiro = setTimeout(passo, MORBIDA + ciclo() - NORMALE);
            return;
          }
        }
        tGiro = setTimeout(guarda, 40);
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
      if (lista[0].getAttribute("data-caricato") && !lista[0]._misurata) { lista[0]._misurata = true; misuraLinea(lista[0]); }
      else if (!lista[0]._misurata) misurata = true;
      if (!scoperto) {
        var a0 = lista[i];
        if (!sceltaNellHtml(a0) && !a0.getAttribute("src")) scopri("senza-video");
        /* il file era già fallito prima di questo script: nessuna sorgente rimasta */
        else if (a0.error || (a0.networkState === 3 && !a0.currentSrc && !a0.getAttribute("src"))) scopri("errore");
        else quandoAvanza(lista[i], function () { scopri("moto"); });
      }
      programma(primoGiro);
      primoGiro = false;
      coda();
    }
    function riprendi() {
      if (!inVista || doc.visibilityState !== "visible" || !lista.length) return;
      parti(lista[i]);
      coda();
    }
    avvia();
    ascolta(mq, avvia);
    ascolta(meno, function () { programma(false); });
    if (haIO) {
      new IntersectionObserver(function (voci) {
        inVista = voci[0].isIntersecting;
        if (inVista) riprendi(); else { if (lista[i]) ferma(lista[i]); primoEPronto(); } /* scorsa via: tocca al resto */
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
      if (!eroe && leggeri) return;
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
    var gruppo = [], indice = 0, ultimo = null, el = null, w = 0, h = 0, tLb = -1, fermoLb = 0;
    /* video a schermo intero: se non gira (all'inizio o perché la linea non ce la fa) la rotella sopra dice che sta
       arrivando, invece di un fotogramma fermo senza spiegazione */
    guardie.push(function () {
      if (!el || el.tagName !== "VIDEO" || !dialog.open) return;
      var t = el.currentTime, mosso = t !== tLb;
      tLb = t;
      if (!el.paused && mosso) { fermoLb = 0; media.classList.remove("attende"); }
      else if (!el.seeking && ++fermoLb >= 2) media.classList.add("attende");
    });
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
      media.classList.remove("attende");
      if (b.getAttribute("data-media") === "video") {
        el = doc.createElement("video");
        el.muted = true; el.loop = true; el.playsInline = true; el.autoplay = true; el.preload = "auto";
        el.setAttribute("muted", ""); el.setAttribute("playsinline", ""); el.setAttribute("aria-label", alt);
        el.poster = b.getAttribute("data-poster") || "";
        el.src = scegliSrc(b); /* computer: versione piena, o leggera se la linea misurata è lenta; telefono: leggera */
        media.appendChild(el);
        media.classList.add("attende"); /* la rotella finché il video non gira davvero */
        tLb = -1; fermoLb = 0;
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
      media.classList.remove("attende");
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
  /* foto e locandine «pigre» delle file (data-pigro-*): gli indirizzi si mettono quando il primo video in cima ha in
     memoria il suo primo turno e la fila è vicina allo schermo; poi decide il caricamento pigro del browser */
  function svegliaImmagini(box) {
    tutti("[data-pigro-srcset], [data-pigro-src]", box).forEach(function (el) {
      var ss = el.getAttribute("data-pigro-srcset"), sr = el.getAttribute("data-pigro-src");
      if (ss) { el.setAttribute("srcset", ss); el.removeAttribute("data-pigro-srcset"); }
      if (sr) { el.setAttribute("src", sr); el.removeAttribute("data-pigro-src"); }
    });
  }
  tutti("[data-striscia]").forEach(function (box) {
    if (!box.querySelector("[data-pigro-src]")) return;
    quandoPrimoPronto(function () {
      if (!haIO) { svegliaImmagini(box); return; }
      var oss = new IntersectionObserver(function (voci) {
        if (voci[0].isIntersecting) { oss.disconnect(); svegliaImmagini(box); }
      }, { rootMargin: "400px 0px 400px 0px", threshold: 0 });
      oss.observe(box);
    });
  });
  tutti("[data-striscia]").forEach(function (striscia) {
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
      dentro = false; /* si usa il mouse o il dito, non la tastiera */
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
  });

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
  tutti("[data-carosello]").forEach(function (carosello, n) {
    var dopoC = carosello.nextElementSibling;
    var barra = dopoC && dopoC.querySelector("[data-avanzamento]");
    var indietro = n === 0 ? doc.querySelector("[data-carosello-indietro]") : null; /* frecce: solo la fila del computer */
    var avanti = n === 0 ? doc.querySelector("[data-carosello-avanti]") : null;
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
  });

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
