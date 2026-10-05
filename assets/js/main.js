/* Astra Gardens — script del sito. Zero cookie, zero tracciamento, zero servizi esterni. */
(function () {
  "use strict";
  var meno = window.matchMedia("(prefers-reduced-motion: reduce)");
  var risparmio = !!(navigator.connection && navigator.connection.saveData);
  var muoviVideo = !meno.matches && !risparmio;
  var haIO = "IntersectionObserver" in window;

  var ICONA_PAUSA = '<svg class="icona" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z"/></svg>';
  var ICONA_PLAY = '<svg class="icona" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 5.5v13l11-6.5z"/></svg>';

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

  /* ---------- Pulsante pausa comune a video d'apertura e clip ---------- */
  function iconaPausa(btn, inPausa) {
    if (!btn) return;
    btn.setAttribute("aria-label", inPausa ? "Riproduci il video" : "Metti in pausa il video");
    btn.innerHTML = inPausa ? ICONA_PLAY : ICONA_PAUSA;
  }
  function avvia(box, video, btn) {
    video.muted = true;
    var p = video.play();
    if (p && p.then) {
      p.then(function () { box.classList.add("in-play"); iconaPausa(btn, false); })
       .catch(function () { iconaPausa(btn, true); });
    } else {
      box.classList.add("in-play");
    }
  }

  /* ---------- Video d'apertura ---------- */
  var media = document.querySelector(".hero__media");
  var video = media ? media.querySelector("video") : null;
  var pausa = media ? media.querySelector(".hero__pausa") : null;
  var fermatoDaUtente = false;
  if (video && muoviVideo) {
    if (pausa) pausa.hidden = false;
    var parti = function () { video.preload = "auto"; avvia(media, video, pausa); };
    if (document.readyState === "complete") parti();
    else window.addEventListener("load", parti);
    if (pausa) {
      pausa.addEventListener("click", function () {
        if (video.paused) { fermatoDaUtente = false; avvia(media, video, pausa); }
        else { fermatoDaUtente = true; video.pause(); iconaPausa(pausa, true); }
      });
    }
    if (haIO) {
      new IntersectionObserver(function (voci) {
        voci.forEach(function (v) {
          if (v.isIntersecting) { if (!fermatoDaUtente && video.paused && media.classList.contains("in-play")) video.play().catch(function () {}); }
          else if (!video.paused) video.pause();
        });
      }, { threshold: 0.15 }).observe(media);
    }
  }

  /* ---------- Clip brevi nelle sezioni: partono solo quando si vedono ---------- */
  var clips = Array.prototype.slice.call(document.querySelectorAll("[data-clip]"));
  if (clips.length && muoviVideo && haIO) {
    var guardaClip = new IntersectionObserver(function (voci) {
      voci.forEach(function (v) {
        var box = v.target, vid = box.querySelector("video"), btn = box.querySelector(".clip__pausa");
        if (v.isIntersecting && v.intersectionRatio >= 0.35) {
          if (!box.hasAttribute("data-fermato") && vid.paused) {
            if (vid.preload !== "auto") vid.preload = "auto";
            avvia(box, vid, btn);
          }
        } else if (!vid.paused) {
          vid.pause();
        }
      });
    }, { threshold: [0, 0.35, 0.7] });
    clips.forEach(function (box) {
      var vid = box.querySelector("video"), btn = box.querySelector(".clip__pausa");
      if (btn) {
        btn.hidden = false;
        btn.addEventListener("click", function () {
          if (vid.paused) { box.removeAttribute("data-fermato"); vid.preload = "auto"; avvia(box, vid, btn); }
          else { box.setAttribute("data-fermato", ""); vid.pause(); iconaPausa(btn, true); }
        });
      }
      guardaClip.observe(box);
    });
  }

  /* ---------- Confronto oggi / progetto con cursore ---------- */
  Array.prototype.slice.call(document.querySelectorAll("[data-confronto]")).forEach(function (box) {
    var input = box.querySelector("input");
    var toccato = false;
    function metti(pct) {
      pct = Math.max(0, Math.min(100, pct));
      box.style.setProperty("--pos", pct + "%");
      input.value = Math.round(pct);
      input.setAttribute("aria-valuetext", "Progetto visibile al " + Math.round(100 - pct) + " per cento");
    }
    function daPuntatore(e) {
      var r = box.getBoundingClientRect();
      metti((e.clientX - r.left) / r.width * 100);
    }
    var trascina = false;
    box.addEventListener("pointerdown", function (e) {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      toccato = true; trascina = true;
      box.classList.add("trascina");
      if (box.setPointerCapture) { try { box.setPointerCapture(e.pointerId); } catch (_) {} }
      daPuntatore(e);
    });
    box.addEventListener("pointermove", function (e) { if (trascina) daPuntatore(e); });
    function fine() { trascina = false; box.classList.remove("trascina"); }
    box.addEventListener("pointerup", fine);
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
    var osserva = new IntersectionObserver(function (voci) {
      voci.forEach(function (v) {
        if (v.isIntersecting) { v.target.classList.add("visibile"); osserva.unobserve(v.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    rivela.forEach(function (el) { osserva.observe(el); });
  } else {
    rivela.forEach(function (el) { el.classList.add("visibile"); });
  }

  /* ---------- WhatsApp sempre a portata ---------- */
  var barra = document.querySelector(".barra-wa");
  var tondo = document.querySelector(".wa-tondo");
  var heroBtn = document.querySelector(".hero .btn--wa");
  var contatti = document.getElementById("contatti");
  var heroVisibile = true, contattiVisibili = false;
  function aggiornaWa() {
    var mostra = !heroVisibile && !contattiVisibili;
    if (barra) barra.classList.toggle("visibile", mostra);
    if (tondo) tondo.classList.toggle("visibile", mostra);
  }
  if (haIO && heroBtn) {
    new IntersectionObserver(function (v) { heroVisibile = v[0].isIntersecting; aggiornaWa(); }).observe(heroBtn);
    if (contatti) new IntersectionObserver(function (v) { contattiVisibili = v[0].isIntersecting; aggiornaWa(); }, { threshold: 0.2 }).observe(contatti);
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
    var gruppo = [], indice = 0, ultimo = null;
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
        ultimo = b;
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
    dialog.addEventListener("close", function () { if (ultimo) ultimo.focus(); });
    var x0 = null;
    dialog.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    dialog.addEventListener("touchend", function (e) {
      if (x0 === null || gruppo.length < 2) { x0 = null; return; }
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 50) mostra(indice + (dx < 0 ? 1 : -1));
      x0 = null;
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
