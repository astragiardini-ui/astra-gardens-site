/* Astra Gardens — script del sito. Zero cookie, zero tracciamento, zero servizi esterni. */
(function () {
  "use strict";
  var doc = document.documentElement;
  var meno = window.matchMedia("(prefers-reduced-motion: reduce)");

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

  /* ---------- Video in apertura ---------- */
  var media = document.querySelector(".hero__media");
  var video = media ? media.querySelector("video") : null;
  var pausa = media ? media.querySelector(".hero__pausa") : null;
  var risparmio = navigator.connection && navigator.connection.saveData;
  var fermatoDaUtente = false;

  function setPausa(inPausa) {
    if (!pausa) return;
    pausa.setAttribute("aria-label", inPausa ? "Riproduci il video" : "Metti in pausa il video");
    pausa.innerHTML = inPausa
      ? '<svg class="icona" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M8 5.5v13l11-6.5z"/></svg>'
      : '<svg class="icona" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z"/></svg>';
  }
  function avvia() {
    if (!video) return;
    var p = video.play();
    if (p && p.then) {
      p.then(function () { media.classList.add("in-play"); setPausa(false); })
       .catch(function () { setPausa(true); });
    } else {
      media.classList.add("in-play");
    }
  }
  if (video && !meno.matches && !risparmio) {
    if (pausa) pausa.hidden = false;
    var parti = function () {
      video.preload = "auto";
      avvia();
    };
    if (document.readyState === "complete") parti();
    else window.addEventListener("load", parti);
    if (pausa) {
      pausa.addEventListener("click", function () {
        if (video.paused) { fermatoDaUtente = false; avvia(); }
        else { fermatoDaUtente = true; video.pause(); setPausa(true); }
      });
    }
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (voci) {
        voci.forEach(function (v) {
          if (v.isIntersecting) { if (!fermatoDaUtente && video.paused && media.classList.contains("in-play")) video.play().catch(function () {}); }
          else if (!video.paused) video.pause();
        });
      }, { threshold: 0.15 }).observe(media);
    }
  }

  /* ---------- Comparsa morbida delle sezioni ---------- */
  var rivela = document.querySelectorAll(".rivela");
  if ("IntersectionObserver" in window && !meno.matches) {
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
    document.body.classList.toggle("con-barra", mostra);
  }
  if ("IntersectionObserver" in window && heroBtn) {
    new IntersectionObserver(function (v) { heroVisibile = v[0].isIntersecting; aggiornaWa(); }).observe(heroBtn);
    if (contatti) new IntersectionObserver(function (v) { contattiVisibili = v[0].isIntersecting; aggiornaWa(); }, { threshold: 0.2 }).observe(contatti);
  }

  /* ---------- Galleria a schermo intero ---------- */
  var dialog = document.getElementById("lightbox");
  var foto = Array.prototype.slice.call(document.querySelectorAll(".galleria button[data-grande]"));
  if (dialog && typeof dialog.showModal === "function" && foto.length) {
    var img = dialog.querySelector("img");
    var testo = dialog.querySelector("p");
    var indice = 0, ultimo = null;
    var mostra = function (i) {
      indice = (i + foto.length) % foto.length;
      var b = foto[indice];
      img.src = b.getAttribute("data-grande");
      img.alt = b.querySelector("img").alt;
      testo.textContent = b.getAttribute("data-didascalia") || "";
    };
    foto.forEach(function (b, i) {
      b.addEventListener("click", function () {
        ultimo = b;
        mostra(i);
        dialog.showModal();
        var corpo = dialog.querySelector(".lightbox__corpo");
        if (corpo) corpo.focus();
      });
    });
    dialog.querySelector("[data-azione=chiudi]").addEventListener("click", function () { dialog.close(); });
    dialog.querySelector("[data-azione=prima]").addEventListener("click", function () { mostra(indice - 1); });
    dialog.querySelector("[data-azione=dopo]").addEventListener("click", function () { mostra(indice + 1); });
    dialog.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") mostra(indice - 1);
      if (e.key === "ArrowRight") mostra(indice + 1);
    });
    dialog.addEventListener("click", function (e) { if (e.target === dialog) dialog.close(); });
    dialog.addEventListener("close", function () { if (ultimo) ultimo.focus(); });
    var x0 = null;
    dialog.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    dialog.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 50) mostra(indice + (dx < 0 ? 1 : -1));
      x0 = null;
    }, { passive: true });
  } else {
    foto.forEach(function (b) {
      b.addEventListener("click", function () { window.location.href = b.getAttribute("data-grande"); });
    });
  }

  /* ---------- Anno nel piè di pagina ---------- */
  var anno = document.getElementById("anno");
  if (anno) anno.textContent = String(new Date().getFullYear());
})();
