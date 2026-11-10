"""Grabación headless con Edge (CDP screencast): cuadros nítidos a 1920x1080, cursor visible y
tiempos sincronizados con la narración. No abre ventanas."""
import base64
import pathlib
import subprocess
import time
import wave

AQUI = pathlib.Path(__file__).resolve().parent
NARR = AQUI / "narracion"
PAUSA, INICIO, COLA = 0.45, 0.6, 0.9  # silencio entre líneas, antes de la 1.ª y al final de cada escena

VIEW = {"width": 1440, "height": 810}
ESCALA = 4 / 3  # 1440x810 * 4/3 = 1920x1080

CURSOR_JS = r"""
(() => {
  if (window.__cursor) return; window.__cursor = 1;
  const poner = () => {
    if (!document.body || document.getElementById('cursor-falso')) return;
    const c = document.createElement('div'); c.id = 'cursor-falso';
    c.innerHTML = '<svg width="30" height="30" viewBox="0 0 24 24"><path d="M3 2l7.5 19 2.6-7.9L21 10.5z" fill="#fff" stroke="#000" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, {position:'fixed', left:'0', top:'0', zIndex:2147483647, pointerEvents:'none',
      transform:'translate(-200px,-200px)', filter:'drop-shadow(0 2px 3px rgba(0,0,0,.35))', transition:'none'});
    document.body.appendChild(c);
    const r = document.createElement('div'); r.id = 'cursor-onda';
    Object.assign(r.style, {position:'fixed', left:'0', top:'0', width:'44px', height:'44px', marginLeft:'-22px', marginTop:'-22px',
      borderRadius:'50%', border:'3px solid #FFC72C', zIndex:2147483646, pointerEvents:'none', opacity:'0'});
    document.body.appendChild(r);
  };
  const xy = JSON.parse(sessionStorage.getItem('__cxy') || '[-200,-200]');
  const mover = (x, y) => { const c = document.getElementById('cursor-falso'); if (c) c.style.transform = `translate(${x - 3}px,${y - 2}px)`;
    sessionStorage.setItem('__cxy', JSON.stringify([x, y])); };
  document.addEventListener('DOMContentLoaded', () => { poner(); mover(...xy); });
  poner(); mover(...xy);
  addEventListener('mousemove', e => { poner(); mover(e.clientX, e.clientY); }, true);
  addEventListener('mousedown', e => { const r = document.getElementById('cursor-onda'); if (!r) return;
    r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px';
    r.animate([{opacity: 1, transform: 'scale(.4)'}, {opacity: 0, transform: 'scale(1.4)'}], {duration: 450, easing: 'ease-out'}); }, true);
})();
"""


def duracion_wav(f):
    with wave.open(str(f)) as w:
        return w.getnframes() / w.getframerate()


def tiempos(escena):
    """Inicio de cada línea dentro de la escena y duración total de la escena."""
    t, inicios = INICIO, []
    for i in range(len(escena["lineas"])):
        inicios.append(t)
        f = NARR / f"{escena['id']}_{i:02d}.wav"
        t += (duracion_wav(f) if f.exists() else len(escena["lineas"][i].split()) / 2.7) + PAUSA
    return inicios, t - PAUSA + COLA


class Grabadora:
    def __init__(self, page, destino):
        self.page, self.destino = page, pathlib.Path(destino)
        self.cuadros, self.t0 = [], None

    def _cuadro(self, ev):
        self.cuadros.append((time.monotonic(), ev["data"]))
        try:
            self.cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception:
            pass

    def iniciar(self):
        self.cdp = self.page.context.new_cdp_session(self.page)
        self.cdp.on("Page.screencastFrame", self._cuadro)
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 90, "maxWidth": 1920, "maxHeight": 1080, "everyNthFrame": 1})
        self.t0 = time.monotonic()
        self.cuadros.append((self.t0, base64.b64encode(self.page.screenshot(type="jpeg", quality=90)).decode()))

    def ahora(self):
        return time.monotonic() - self.t0

    def esperar_hasta(self, t):
        falta = t - self.ahora()
        if falta > 0:
            self.page.wait_for_timeout(falta * 1000)

    def terminar(self, duracion):
        self.esperar_hasta(duracion)
        fin = time.monotonic()
        try:
            self.cdp.send("Page.stopScreencast")
        except Exception:
            pass
        carpeta = self.destino.with_suffix("")
        carpeta.mkdir(parents=True, exist_ok=True)
        cuadros = [c for c in self.cuadros if c[0] - self.t0 <= duracion] or self.cuadros[:1]
        lineas = []
        for i, (ts, datos) in enumerate(cuadros):
            f = carpeta / f"{i:06d}.jpg"
            f.write_bytes(base64.b64decode(datos))
            sig = cuadros[i + 1][0] if i + 1 < len(cuadros) else min(fin, self.t0 + duracion)
            lineas.append(f"file '{f.as_posix()}'\nduration {max(sig - ts, 0.001):.4f}")
        lineas.append(f"file '{(carpeta / f'{len(cuadros) - 1:06d}.jpg').as_posix()}'")
        lista = carpeta / "lista.txt"
        lista.write_text("\n".join(lineas), encoding="utf-8")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,format=yuv420p",
                        "-t", f"{duracion:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", str(self.destino)], check=True)
        for f in carpeta.glob("*.jpg"):
            f.unlink()
        print(f"  video {self.destino.name}: {duracion:.1f}s, {len(cuadros)} cuadros", flush=True)


def nuevo_contexto(nav, **kw):
    ctx = nav.new_context(viewport=VIEW, device_scale_factor=ESCALA, **kw)
    ctx.add_init_script(CURSOR_JS)
    return ctx


def mover(page, objetivo, pasos=28, clic=False, pausa=120, nav=False):
    """Mueve el cursor suavemente hasta un selector (o (x, y)) y opcionalmente hace clic."""
    if isinstance(objetivo, str):
        loc = page.locator(objetivo).first
        loc.scroll_into_view_if_needed(timeout=6000)
        b = loc.bounding_box()
        x, y = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    else:
        x, y = objetivo
    page.mouse.move(x, y, steps=pasos)
    page.wait_for_timeout(pausa)
    if clic and nav:
        with page.expect_navigation(wait_until="domcontentloaded"):
            page.mouse.down()
            page.wait_for_timeout(70)
            page.mouse.up()
    elif clic:
        page.mouse.down()
        page.wait_for_timeout(70)
        page.mouse.up()
    return x, y


def escribir(page, selector, texto, retraso=38):
    mover(page, selector, clic=True)
    page.locator(selector).first.fill("")
    page.keyboard.type(texto, delay=retraso)


def desplazar(page, dy, pasos=24, ms=900):
    for _ in range(pasos):
        page.mouse.wheel(0, dy / pasos)
        page.wait_for_timeout(ms / pasos)
