"""Genera narracion/<escena>_<nn>.wav para cada línea de plan.py con VoiceStudio (http://127.0.0.1:8787).
Cachea por texto: si el .txt al lado coincide, no regenera."""
import pathlib
import sys
import time

import requests

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from plan import ESCENAS, VOZ, para_voz  # noqa: E402

out = AQUI / "narracion"
out.mkdir(exist_ok=True)
todo = [(f"{e['id']}_{i:02d}", para_voz(l)) for e in ESCENAS for i, l in enumerate(e["lineas"])]
for n, (lid, texto) in enumerate(todo, 1):
    wav, txt = out / f"{lid}.wav", out / f"{lid}.txt"
    if wav.exists() and txt.exists() and txt.read_text(encoding="utf-8") == texto:
        continue
    t = time.time()
    for intento in range(3):
        r = requests.post("http://127.0.0.1:8787/v1/audio/speech", timeout=900, json={
            "model": "omnivoice", "input": texto, "voice": VOZ, "language": "es",
            "response_format": "wav", "speed": 0.98, "seed": 21})
        if r.status_code == 200:
            break
        print(f"  {lid} error {r.status_code}: {r.text[:200]}", flush=True)
    else:
        sys.exit(f"falló {lid}")
    wav.write_bytes(r.content)
    txt.write_text(texto, encoding="utf-8")
    print(f"[{n}/{len(todo)}] {lid} {time.time() - t:.0f}s", flush=True)
print("VOZ LISTA")
