# FieldWay

A lightweight web map for field technicians: upload KML, open the same saved files on another device, view waypoints, and use that device's GPS. Includes recoverable file trash/restore and an experimental offline street-map view.

This repository contains the web application only. Native iOS/Android apps, uploaded jobs, private access keys, deployment infrastructure and map datasets are not included.

## Local setup

Requires Python 3.9+ (standard library only). From this directory:

```sh
python scripts/setup_vendor.py
python server.py
```

Open `http://localhost:8798/fieldway/#YOUR_LOCAL_KEY`, replacing the placeholder with the contents of the newly generated `access.key`. Do not publish or share that key except with intended library users. Anyone with it can read, upload, move and restore files in the shared library. This is a shared-key prototype, not a multi-user account system.

The setup script downloads exact SHA-512-pinned official npm packages and their license notices. It does not run package scripts. The online page also loads pinned Leaflet 1.9.4 and mgrs 2.1.0 from unpkg. Internet is needed for initial dependency installation, those online libraries, map-provider requests and remote file synchronization.

For street maps, separately obtain a compatible Protomaps-schema PMTiles archive and place it at `maps/region.pmtiles`. The archive is deliberately not distributed here. Without it, the online street layer will not render. The satellite layer uses the configured external imagery service; it is not OpenStreetMap satellite imagery. Check provider availability, usage rights, download policies and attribution before deployment. Do not bulk-download public OSM raster tiles.

## Hosting

The backend binds only to `127.0.0.1:8798`. Put it behind an HTTPS reverse proxy, mapping `/fieldway/` to this backend; keep private files outside any public static root. Set `FIELDWAY_ORIGIN` to your exact public origin, such as `https://maps.example.org`, before starting Python. The default is `http://localhost:8798`. Origin must match browser requests. Do not bind this development HTTP server directly to the Internet.

Protect and back up `access.key`, `data/` and `trash/`; these are runtime files, never source files. Limit filesystem access to the service account. The shared key is sent in `X-Field-Key`, not the request URL. Browser location requires HTTPS (or localhost), user permission and an appropriate device GPS. The backend does not receive live GPS positions.

## Offline limitations

The experimental offline page stores imported KML and downloaded vector tiles on each device. Downloads use the configured OpenFreeMap endpoint via the authenticated backend. This is not guaranteed offline navigation: complete the download online, then explicitly test reopening the app and job with networking off. Browser storage may be evicted; keep original KML elsewhere. No background GPS guarantee, routing, live traffic, verified speed limits or truck-clearance guidance is provided. Distances/bearings are straight-line. Not survey-grade or a sole navigation tool.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests run an isolated backend on an ephemeral loopback port with synthetic data, not your running service or real jobs. Device GPS, iPhone/iPad file-picker behavior and offline persistence require manual tests.

## Licensing

No license for FieldWay's own source is selected in this repository. Public availability does not grant additional reuse rights. Third-party components retain their own licenses; see `THIRD_PARTY.md`. No production settings, work data, credentials, signing material or third-party map archives belong in commits.
