/* Oynacha (modal) va forma yordamchilari - tashqi kutubxonasiz */
(function () {
  "use strict";

  var fon = null;

  function qobiq() {
    if (!fon) fon = document.getElementById("oyna-fon");
    return fon;
  }

  function ochish() {
    var q = qobiq();
    if (q) { q.classList.add("ochiq"); document.body.style.overflow = "hidden"; }
  }

  function yopish() {
    var q = qobiq();
    if (q) { q.classList.remove("ochiq"); document.body.style.overflow = ""; }
  }

  window.oynaniYopish = yopish;

  /* Ro'yxatdan bosilganda o'quvchi/xodim oynachasini yuklaydi */
  function oynaniYukla(manzil) {
    var ich = document.getElementById("oyna-ich");
    if (!ich) return;
    var qayerdan = encodeURIComponent(location.pathname + location.search);
    manzil += (manzil.indexOf("?") === -1 ? "?" : "&") + "keyingi=" + qayerdan;
    ich.innerHTML = '<div class="yuklanmoqda">Yuklanmoqda...</div>';
    ochish();
    fetch(manzil, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(function (j) {
        if (!j.ok) throw new Error("xato");
        return j.text();
      })
      .then(function (html) {
        ich.innerHTML = html;
        tolovFormasi(ich);
        var birinchi = ich.querySelector("input[name='summa']");
        if (birinchi) birinchi.focus();
      })
      .catch(function () {
        ich.innerHTML = '<div class="yuklanmoqda">Ma\'lumotni yuklab bo\'lmadi.</div>';
      });
  }
  window.oynaniYukla = oynaniYukla;

  /* To'lov formasi: amal turiga qarab keraksiz maydonlarni yashiradi */
  function tolovFormasi(ildiz) {
    var soha = ildiz || document;
    var turlar = soha.querySelectorAll("[data-tolov-forma]");
    Array.prototype.forEach.call(turlar, function (forma) {
      var tur = forma.querySelector("[name='tur']");
      var usul = forma.querySelector("[name='usul']");
      var usulQuti = forma.querySelector("[data-usul-quti]");
      var kartaQuti = forma.querySelector("[data-karta-quti]");

      function yangila() {
        var pulHarakati = tur && (tur.value === "tolov" || tur.value === "qaytarish"
          || tur.value === "avans" || tur.value === "oylik");
        if (usulQuti) usulQuti.style.display = pulHarakati ? "" : "none";
        var plastik = pulHarakati && usul && usul.value === "plastik";
        if (kartaQuti) kartaQuti.style.display = plastik ? "" : "none";
      }

      if (tur) tur.addEventListener("change", yangila);
      if (usul) usul.addEventListener("change", yangila);
      yangila();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    tolovFormasi(document);

    /* Jadval qatoriga bosilsa oynacha ochiladi */
    document.addEventListener("click", function (h) {
      var qator = h.target.closest("[data-oyna]");
      if (qator && !h.target.closest("a, button, input, label, select")) {
        h.preventDefault();
        oynaniYukla(qator.getAttribute("data-oyna"));
        return;
      }
      var yopuvchi = h.target.closest("[data-yopish]");
      if (yopuvchi) { h.preventDefault(); yopish(); return; }
      if (h.target === qobiq()) yopish();
    });

    document.addEventListener("keydown", function (h) {
      if (h.key === "Escape") yopish();
    });

    /* Sahifadagi oddiy oynachalar: data-ochish="#id" */
    document.addEventListener("click", function (h) {
      var tugma = h.target.closest("[data-ochish]");
      if (!tugma) return;
      h.preventDefault();
      var nishon = document.querySelector(tugma.getAttribute("data-ochish"));
      if (nishon) {
        nishon.classList.add("ochiq");
        document.body.style.overflow = "hidden";
        var birinchi = nishon.querySelector("input:not([type=hidden]), select");
        if (birinchi) birinchi.focus();
      }
    });

    /* Har qanday oddiy oynachani yopish */
    document.addEventListener("click", function (h) {
      if (h.target.classList && h.target.classList.contains("oyna-fon")) {
        h.target.classList.remove("ochiq");
        document.body.style.overflow = "";
      }
      var y = h.target.closest("[data-oddiy-yopish]");
      if (y) {
        h.preventDefault();
        var ota = y.closest(".oyna-fon");
        if (ota) { ota.classList.remove("ochiq"); document.body.style.overflow = ""; }
      }
    });

    /* Filtr o'zgarsa avtomatik yuborish */
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-avto-filtr] select, [data-avto-filtr] input[type=date]"),
      function (maydon) {
        maydon.addEventListener("change", function () { maydon.form.submit(); });
      }
    );
  });
})();
