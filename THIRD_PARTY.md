# Third-party components

Vendored build artifacts are intentionally excluded from Git. `python scripts/setup_vendor.py` retrieves these exact official npm packages, checks the recorded SHA-512 integrity values and copies their complete license notices alongside the browser assets:

- MapLibre GL JS **5.6.2**, BSD-3-Clause and notices included in its LICENSE.txt: https://github.com/maplibre/maplibre-gl-js/blob/v5.6.2/LICENSE.txt
- Protomaps Leaflet **5.0.0**, BSD-3-Clause: https://www.npmjs.com/package/protomaps-leaflet/v/5.0.0 . The package's `LICENSE` is extracted intact.

The online HTML references these version-pinned CDN assets (not distributed in this repository):

- Leaflet **1.9.4**, BSD-2-Clause: https://github.com/Leaflet/Leaflet/blob/v1.9.4/LICENSE
- mgrs **2.1.0**, MIT: https://www.npmjs.com/package/mgrs/v/2.1.0

Keep all upstream notices when distributing downloaded assets. Map data and imagery are separate from library code and subject to their respective licenses/terms. Preserve the attribution displayed by the frontend, including OpenStreetMap contributors, Protomaps and imagery-provider credits. Obtain your own compatible PMTiles data; none is included here. No license for the author's original code is selected by this notice.
