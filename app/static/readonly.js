// Lese-Benutzer: Bearbeitungsformulare sperren (der Server lehnt Änderungen ohnehin ab).
document.querySelectorAll('form[method="post"]:not(.allow-ro)').forEach(function (f) {
  f.querySelectorAll("input, select, textarea").forEach(function (i) { i.disabled = true; });
  f.querySelectorAll("button").forEach(function (b) { b.remove(); });
  if (!f.querySelector("input:not([type=hidden]), select, textarea")) f.style.display = "none";
});
document.querySelectorAll('a[href$="/edit"], a[href="/events/new"], a[href^="/events/new?"], a[href$="/research"], a[href$="/photos"].btn, a[href="/venues/new"]').forEach(function (a) { a.remove(); });
document.querySelectorAll("details").forEach(function (d) {
  if (!d.querySelector("input:not([disabled]):not([type=hidden]), a, table, p")) d.style.display = "none";
});
