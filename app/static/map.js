(function () {
  const el = document.getElementById("map");
  if (!el) return;
  const map = L.map(el).setView([50.5, 9.5], 6);
  L.tileLayer(el.dataset.tiles, { maxZoom: 19, attribution: el.dataset.attribution }).addTo(map);
  const cluster = L.markerClusterGroup({ showCoverageOnHover: false });
  map.addLayer(cluster);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  fetch("/api/venues.geojson" + window.location.search)
    .then((r) => r.json())
    .then((data) => {
      const layer = L.geoJSON(data, {
        pointToLayer: (f, latlng) => L.marker(latlng),
        onEachFeature: (f, m) => {
          const p = f.properties;
          const evs = p.events.map((e) => `<li><a href="/events/${e.id}">${esc(e.date)} – ${esc(e.title)}</a> <span class="muted">${esc(e.sport)}</span></li>`).join("");
          m.bindPopup(`<b><a href="/venues/${p.id}">${esc(p.name)}</a></b><br>${esc(p.city || "")}<br>${p.visits} Besuch(e)<ul style="padding-left:1rem;margin:.3rem 0">${evs}</ul>`);
        },
      });
      cluster.addLayer(layer);
      if (data.features.length) map.fitBounds(cluster.getBounds(), { padding: [30, 30], maxZoom: 13 });
      const miss = document.getElementById("missing");
      if (miss && data.without_coordinates.length) {
        miss.innerHTML = "Ohne Koordinaten (nicht auf der Karte): " +
          data.without_coordinates.map((v) => `<a href="/venues/${v.id}/edit">${esc(v.name)}</a>`).join(", ");
      }
    });
})();
