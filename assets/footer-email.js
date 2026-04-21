(function () {
  var EMAIL_TEXT = "Email me at: ";
  var EMAIL = "beigi@gwu.edu";
  var COPYRIGHT_TEXT = "Most rights reserved";

  function findFooterRow() {
    var footers = document.querySelectorAll("footer");
    for (var i = 0; i < footers.length; i += 1) {
      var footer = footers[i];
      if (!footer.textContent || footer.textContent.indexOf(COPYRIGHT_TEXT) === -1) continue;
      var row = footer.querySelector("div");
      if (row) return row;
    }
    return null;
  }

  function ensureFooterEmail() {
    var row = findFooterRow();
    if (!row) return false;
    if (row.textContent && row.textContent.indexOf(EMAIL) !== -1) return true;

    row.classList.add("justify-between");

    var emailDiv = document.createElement("div");
    emailDiv.className = "text-ele-text-light text-xs";
    emailDiv.style.marginLeft = "12px";

    var label = document.createTextNode(EMAIL_TEXT);
    var link = document.createElement("a");
    link.className = "hover:text-ele-pink transition-colors";
    link.href = "mailto:" + EMAIL;
    link.textContent = EMAIL;

    emailDiv.appendChild(label);
    emailDiv.appendChild(link);
    row.appendChild(emailDiv);
    return true;
  }

  function init() {
    ensureFooterEmail();

    var observer = new MutationObserver(function () {
      ensureFooterEmail();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    var tries = 0;
    var maxTries = 40;
    var timer = setInterval(function () {
      tries += 1;
      if (ensureFooterEmail() || tries >= maxTries) {
        clearInterval(timer);
      }
    }, 250);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
