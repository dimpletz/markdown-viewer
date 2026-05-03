/**
 * Legacy browser check.
 * Detect if the browser supports ES6 arrow functions, which is our baseline.
 * If not, display a friendly error message instead of a broken page.
 */
(function () {
  "use strict";
  try {
    new Function("() => {}")();
  } catch (e) {
    document.addEventListener("DOMContentLoaded", function () {
      document.body.style.cssText =
        "margin:0;font-family:sans-serif;background:#fff";
      document.body.innerHTML =
        '<div style="max-width:600px;margin:80px auto;padding:40px;text-align:center;' +
        'border:1px solid #e0e0e0;border-radius:8px;">' +
        '<h2 style="color:#cc0000">&#x26A0; Browser Not Supported</h2>' +
        "<p>This application requires a modern browser.</p>" +
        "<p>Please open this page in one of the following browsers:</p>" +
        "<p><strong>Chrome &bull; Firefox &bull; Edge &bull; Brave &bull; Safari &bull; Opera</strong></p>" +
        "</div>";
    });
    throw new Error("Legacy browser detected");
  }
})();
