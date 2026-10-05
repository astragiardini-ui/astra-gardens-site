/* Astra Gardens — script del sito. Zero cookie, zero tracciamento, zero servizi esterni. */
(function () {
  "use strict";
  var meno = window.matchMedia("(prefers-reduced-motion: reduce)");
  var haIO = "IntersectionObserver" in window;

  /* ---------- Testata: ombra quando la pagina scorre ---------- */
  var testata = document.querySelector(".testata");
  function aggiornaTestata() {
    if (testata) testata.classList.toggle("scorre", window.scrollY > 8);
  }
  aggiornaTestata();
  window.addEventListener("scroll", aggiornaTestata, { passive: true });

  /* ---------- Menu su telefono ---------- */
  var apri = document.querySelector(".apri-menu");
  var pannello = document.getElementById("menu-telefono");
  var chiudi = pannello ? pannello.querySelector(".chiudi-menu") : null;
  function apriMenu() {
    pannello.hidden = false;
    apri.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
    if (chiudi) chiudi.focus();
  }
  function chiudiMenu(rimettiFocus) {
    pannello.hidden = true;
    apri.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
    if (rimettiFocus) apri.focus();
  }
  if (apri && pannello) {
    apri.addEventListener("click", apriMenu);
    if (chiudi) chiudi.addEventListener("click", function () { chiudiMenu(true); });
    pannello.addEventListener("click", function (e) {
      if (e.target.closest("a")) chiudiMenu(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !pannello.hidden) chiudiMenu(true);
    });
  }

  /* ---------- Video: girano sempre, da soli, muti, in loop ----------
     Scelta di Francesco: nessun pulsante pausa e nessun comando. Partono anche con
     "riduci movimento". Fuori dallo schermo si fermano per risparmiare batteria e
     ripartono da soli quando tornano visibili. Se il telefono blocca l'avvio automatico
     (iPhone in Risparmio energetico) resta l'immagine ferma e i video partono al primo
     tocco o scorrimento. */
  var video = Array.prototype.slice.call(document.querySelectorAll("video"));
  var serveSblocco = false;

  function scatola(v) { return v.closest("[data-clip]") || v.closest(".hero__media") || v.parentNode; }
  function visibile(v) {
    var r = scatola(v).getBoundingClientRect();
    return r.bottom > -40 && r.top < window.innerHeight + 40 && r.right > 0 && r.left < window.innerWidth && r.width > 0;
  }
  function parti(v) {
    var box = scatola(v);
    if (v.preload !== "auto") v.preload = "auto";
    v.muted = true;
    var p;
    try { p = v.play(); } catch (_) { p = null; }
    if (p && typeof p.then === "function") {
      p.then(function () { box.classList.add("in-play"); })
       .catch(function (err) {
         /* AbortError = l'abbiamo fermato noi mentre partiva; ogni altro errore = avvio bloccato dal telefono */
         if (!err || err.name !== "AbortError") serveSblocco = true;
       });
    } else if (!v.paused) {
      box.classList.add("in-play");
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
    /* se qualcosa li ferma (non noi) e si vedono, ripartono */
    v.addEventListener("pause", function () {
      if (v._fermatoDaNoi) { v._fermatoDaNoi = false; return; }
      setTimeout(function () {
        if (v.paused && document.visibilityState === "visible" && visibile(v)) parti(v);
      }, 300);
    });
    v.addEventListener("contextmenu", function (e) { e.preventDefault(); });
  });

  /* il video d'apertura parte subito */
  var hero = document.querySelector(".hero__media video");
  if (hero) parti(hero);

  /* le clip partono quando entrano nello schermo e si fermano quando escono */
  var clip = Array.prototype.slice.call(document.querySelectorAll("[data-clip] video"));
  if (haIO) {
    var osserva = new IntersectionObserver(function (voci) {
      voci.forEach(function (voce) {
        var v = voce.target.matches("video") ? voce.target : voce.target.querySelector("video");
        if (!v) return;
        if (voce.isIntersecting) parti(v); else ferma(v);
      });
    }, { rootMargin: "160px 0px 160px 0px", threshold: 0 });
    clip.forEach(function (v) { osserva.observe(scatola(v)); });
    if (hero) osserva.observe(scatola(hero));
  } else {
    clip.forEach(parti);
  }

  /* primo tocco (anche quello che fa scorrere la pagina): fa partire tutto quello che il telefono
     aveva bloccato. Su iPhone ogni video va avviato dentro il gesto: quelli visibili partono, gli
     altri vengono avviati e subito fermati, così poi ripartono da soli quando si vedono. */
  function sblocca() {
    if (!serveSblocco) return;
    serveSblocco = false;
    video.forEach(function (v) {
      if (!v.paused) return;
      if (visibile(v)) { parti(v); return; }
      if (v._sbloccato) return;
      v._sbloccato = true;
      v.muted = true;
      var p;
      try { p = v.play(); } catch (_) { p = null; }
      v._fermatoDaNoi = true;
      try { v.pause(); } catch (_) {}
      if (p && typeof p.catch === "function") {
        p.catch(function (err) {
          if (err && err.name === "NotAllowedError") { v._sbloccato = false; serveSblocco = true; }
        });
      }
    });
  }
  ["touchstart", "touchend", "pointerdown", "pointerup", "click", "keydown"].forEach(function (ev) {
    window.addEventListener(ev, sblocca, { passive: true, capture: true });
  });
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState !== "visible") return;
    video.forEach(function (v) { if (v.paused && visibile(v)) parti(v); });
  });

  /* ---------- Alone sfocato dietro la cornice: segue il video d'apertura ---------- */
  var alone = document.querySelector(".hero__alone");
  if (alone && alone.getContext && hero) {
    var ctx = alone.getContext("2d");
    var locandina = document.querySelector(".hero__cornice img");
    var dipingi = function (sorgente) {
      try { ctx.drawImage(sorgente, 0, 0, alone.width, alone.height); } catch (_) {}
    };
    if (locandina) {
      if (locandina.complete && locandina.naturalWidth) dipingi(locandina);
      else locandina.addEventListener("load", function () { if (hero.paused) dipingi(locandina); });
    }
    var ultimo = 0;
    if ("requestVideoFrameCallback" in hero) {
      var giro = function (ora) {
        if (ora - ultimo > 140) { dipingi(hero); ultimo = ora; }
        hero.requestVideoFrameCallback(giro);
      };
      hero.requestVideoFrameCallback(giro);
    } else {
      setInterval(function () {
        if (!hero.paused && hero.readyState >= 2 && visibile(hero)) dipingi(hero);
      }, 150);
    }
  }

  /* ---------- Confronto prima / dopo con cursore ---------- */
  Array.prototype.slice.call(document.querySelectorAll("[data-confronto]")).forEach(function (box) {
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
      /* un tocco senza trascinare sposta il cursore lì */
      if (trascina && e.pointerType !== "mouse" && !mosso) daPuntatore(e);
      fine();
    });
    box.addEventListener("pointercancel", fine);
    input.addEventListener("input", function () { toccato = true; metti(+input.value); });
    input.addEventListener("keydown", function (e) {
      var passo = { ArrowLeft: -5, ArrowDown: -5, ArrowRight: 5, ArrowUp: 5 }[e.key];
      if (passo) { e.preventDefault(); toccato = true; metti(+input.value + passo); }
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
          function passo(t) {
            if (toccato) return;
            if (t0 === null) t0 = t;
            var k = Math.min(1, (t - t0) / durata);
            metti(50 - 18 * Math.sin(k * Math.PI * 2) * (1 - k * 0.15));
            if (k < 1) requestAnimationFrame(passo); else metti(50);
          }
          setTimeout(function () { requestAnimationFrame(passo); }, 500);
        });
      }, { threshold: 0.6 }).observe(box);
    }
  });

  /* ---------- Comparsa morbida delle sezioni ---------- */
  var rivela = document.querySelectorAll(".rivela");
  if (haIO && !meno.matches) {
    var osservaRivela = new IntersectionObserver(function (voci) {
      voci.forEach(function (v) {
        if (v.isIntersecting) { v.target.classList.add("visibile"); osservaRivela.unobserve(v.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    rivela.forEach(function (el) { osservaRivela.observe(el); });
  } else {
    rivela.forEach(function (el) { el.classList.add("visibile"); });
  }

  /* ---------- WhatsApp sempre a portata ----------
     La barra in basso compare appena il pulsante grande dell'apertura non si vede per intero
     (anche se è tagliato dal bordo dello schermo) e sparisce sopra i contatti. */
  var barra = document.querySelector(".barra-wa");
  var tondo = document.querySelector(".wa-tondo");
  var heroBtn = document.querySelector(".hero .btn--wa");
  var contatti = document.getElementById("contatti");
  var heroIntero = false, contattiVisibili = false;
  function aggiornaWa() {
    var mostra = !heroIntero && !contattiVisibili;
    if (barra) barra.classList.toggle("visibile", mostra);
    if (tondo) tondo.classList.toggle("visibile", mostra);
  }
  if (haIO && heroBtn) {
    new IntersectionObserver(function (v) {
      heroIntero = v[0].isIntersecting && v[0].intersectionRatio >= 0.95;
      aggiornaWa();
    }, { threshold: [0, 0.5, 0.95, 1] }).observe(heroBtn);
    if (contatti) new IntersectionObserver(function (v) { contattiVisibili = v[0].isIntersecting; aggiornaWa(); }, { threshold: 0.2 }).observe(contatti);
  } else {
    if (barra) barra.classList.add("visibile");
  }

  /* ---------- Foto a schermo intero (galleria e piano di cantiere) ---------- */
  var dialog = document.getElementById("lightbox");
  var tutte = Array.prototype.slice.call(document.querySelectorAll("button[data-grande]"));
  if (dialog && typeof dialog.showModal === "function" && tutte.length) {
    var img = dialog.querySelector("img");
    var testo = dialog.querySelector("p");
    var corpo = dialog.querySelector(".lightbox__corpo");
    var btnPrima = dialog.querySelector("[data-azione=prima]");
    var btnDopo = dialog.querySelector("[data-azione=dopo]");
    var gruppo = [], indice = 0, ultimoBtn = null;
    var mostra = function (i) {
      indice = (i + gruppo.length) % gruppo.length;
      var b = gruppo[indice];
      img.src = b.getAttribute("data-grande");
      var interno = b.querySelector("img");
      img.alt = interno ? interno.alt : "";
      testo.textContent = b.getAttribute("data-didascalia") || "";
    };
    tutte.forEach(function (b) {
      b.addEventListener("click", function () {
        var contenitore = b.closest("[data-galleria]");
        gruppo = contenitore ? Array.prototype.slice.call(contenitore.querySelectorAll("button[data-grande]")) : [b];
        var piu = gruppo.length > 1;
        btnPrima.hidden = !piu; btnDopo.hidden = !piu;
        ultimoBtn = b;
        mostra(gruppo.indexOf(b));
        dialog.showModal();
        if (corpo) corpo.focus();
      });
    });
    dialog.querySelector("[data-azione=chiudi]").addEventListener("click", function () { dialog.close(); });
    btnPrima.addEventListener("click", function () { mostra(indice - 1); });
    btnDopo.addEventListener("click", function () { mostra(indice + 1); });
    dialog.addEventListener("keydown", function (e) {
      if (gruppo.length < 2) return;
      if (e.key === "ArrowLeft") mostra(indice - 1);
      if (e.key === "ArrowRight") mostra(indice + 1);
    });
    dialog.addEventListener("click", function (e) { if (e.target === dialog) dialog.close(); });
    dialog.addEventListener("close", function () { if (ultimoBtn) ultimoBtn.focus(); });
    var xs = null;
    dialog.addEventListener("touchstart", function (e) { xs = e.touches[0].clientX; }, { passive: true });
    dialog.addEventListener("touchend", function (e) {
      if (xs === null || gruppo.length < 2) { xs = null; return; }
      var d = e.changedTouches[0].clientX - xs;
      if (Math.abs(d) > 50) mostra(indice + (d < 0 ? 1 : -1));
      xs = null;
    }, { passive: true });
  } else {
    tutte.forEach(function (b) {
      b.addEventListener("click", function () { window.location.href = b.getAttribute("data-grande"); });
    });
  }

  /* ---------- Anno nel piè di pagina ---------- */
  var anno = document.getElementById("anno");
  if (anno) anno.textContent = String(new Date().getFullYear());
})();
