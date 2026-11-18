"""Fetch pinned browser dependencies and notices from the official npm registry.
Run from any directory: python scripts/setup_vendor.py
Only named archive members are written; package scripts are never executed.
"""
import base64, hashlib, io, tarfile, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKAGES=[
 ('https://registry.npmjs.org/maplibre-gl/-/maplibre-gl-5.6.2.tgz',
  'SEqYThhUCFf6Lm0TckpgpKnto5u4JsdPYdFJb6g12VtuaFsm3nYdBO+fOmnUYddc8dXihgoGnuXvPPooUcRv5w==',
  {'package/dist/maplibre-gl.js':'maplibre.js','package/dist/maplibre-gl.css':'maplibre.css','package/LICENSE.txt':'maplibre.LICENSE.txt'}),
 ('https://registry.npmjs.org/protomaps-leaflet/-/protomaps-leaflet-5.0.0.tgz',
  'abc/0wLIJFmgNhMhMRYHL4Lv9y3MgIJmJE4BldJ82p8L39f0rFRjwb9W7J9D03UR9tcbxXeb8Nqy08JjBTXveQ==',
  {'package/dist/protomaps-leaflet.js':'protomaps-leaflet.js','package/LICENSE':'protomaps-leaflet.LICENSE.txt'})]
def main():
 assets={}
 for url,expected,names in PACKAGES:
  with urllib.request.urlopen(url,timeout=60) as response: data=response.read(30_000_001)
  if len(data)>30_000_000: raise ValueError('Package exceeds download limit')
  if base64.b64encode(hashlib.sha512(data).digest()).decode()!=expected: raise ValueError('Package integrity mismatch')
  with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
   for member,target in names.items():
    info=archive.getmember(member)
    if not info.isfile() or info.size>10_000_000:raise ValueError('Unexpected archive member')
    assets[target]=archive.extractfile(info).read()
 vendor=ROOT/'public'/'vendor';vendor.mkdir(parents=True,exist_ok=True)
 for name,data in assets.items():(vendor/name).write_bytes(data)
 print('Installed pinned browser assets and license notices into public/vendor')
if __name__=='__main__':main()
