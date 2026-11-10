"""Monta el video final: intro de Flow + escenas (clips/*.mp4) + narración + subtítulos.

    python montar.py   ->  salida/UniRed - Proyecto I+D (video explicativo).mp4
"""
import array
import pathlib
import subprocess
import sys
import wave

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from grabadora import COLA, INICIO, PAUSA, tiempos  # noqa: E402
from plan import ESCENAS  # noqa: E402

NARR, CLIPS, SAL = AQUI / "narracion", AQUI / "clips", AQUI / "salida"
TMP = SAL / "tmp"
TMP.mkdir(parents=True, exist_ok=True)
INTRO = pathlib.Path(r"C:\Users\sebas\Downloads\Logo_reveal_animation_on_black_384f827f_1080p.mp4")
SR = 48000


def leer_wav(f):
    """Devuelve muestras mono int16 a 48 kHz (re-muestrea con ffmpeg si hace falta)."""
    tmp = TMP / (f.stem + "_48k.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16", str(tmp)], check=True)
    with wave.open(str(tmp)) as w:
        return array.array("h", w.readframes(w.getnframes()))


def silencio(seg):
    return array.array("h", bytes(2 * int(round(seg * SR))))


def tc(seg):
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def trozos(texto, maximo=84):
    """Parte una línea larga en subtítulos de hasta ~2 renglones."""
    palabras, partes, act = texto.split(), [], ""
    for p in palabras:
        if len(act) + len(p) + 1 > maximo and act:
            partes.append(act)
            act = p
        else:
            act = (act + " " + p).strip()
    if act:
        partes.append(act)
    return partes


def main():
    dur_intro = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(INTRO)],
                                     capture_output=True, text=True).stdout)
    audio = array.array("h")
    eventos, capitulos, videos = [], [], []
    # intro con su propio sonido
    intro_v = TMP / "00_intro.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(INTRO), "-vf", "scale=1920:1080,fps=30,format=yuv420p",
                    "-c:v", "libx264", "-crf", "18", "-an", str(intro_v)], check=True)
    videos.append(intro_v)
    intro_a = TMP / "intro_audio.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(INTRO), "-vn", "-ac", "1", "-ar", str(SR), "-sample_fmt", "s16",
                    "-af", "volume=0.55", str(intro_a)], check=True)
    with wave.open(str(intro_a)) as w:
        a = array.array("h", w.readframes(w.getnframes()))
    a.extend(silencio(dur_intro - len(a) / SR)) if len(a) / SR < dur_intro else None
    audio.extend(a[: int(dur_intro * SR)])
    t_global = dur_intro

    for e in ESCENAS:
        clip = CLIPS / f"{e['id']}.mp4"
        if not clip.exists():
            sys.exit(f"Falta el clip {clip.name}")
        T, dur = tiempos(e)
        capitulos.append((t_global, e["id"]))
        pista = silencio(INICIO)
        for i, linea in enumerate(e["lineas"]):
            muestras = leer_wav(NARR / f"{e['id']}_{i:02d}.wav")
            d = len(muestras) / SR
            ini = t_global + T[i]
            # subtítulos proporcionales a la cantidad de texto
            partes = trozos(linea)
            total = sum(len(p) for p in partes)
            t = ini
            for p in partes:
                dp = d * len(p) / total
                eventos.append((t, t + dp, p))
                t += dp
            pista = pista[: int(T[i] * SR)]
            pista.extend(silencio(T[i] - len(pista) / SR))
            pista.extend(muestras)
        pista.extend(silencio(dur - len(pista) / SR))
        audio.extend(pista[: int(round(dur * SR))])
        # el clip se ajusta exactamente a la duración de la escena (congela el último cuadro si falta)
        ajustado = TMP / f"{e['id']}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-vf", f"tpad=stop_mode=clone:stop_duration=5,fps=30,format=yuv420p",
                        "-t", f"{dur:.3f}", "-c:v", "libx264", "-crf", "18", "-an", str(ajustado)], check=True)
        videos.append(ajustado)
        t_global += dur
        print(f"{e['id']}: {dur:.1f}s", flush=True)

    with wave.open(str(TMP / "narracion.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(audio.tobytes())

    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 0", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: Sub,Segoe UI Semibold,44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H9A000000,0,0,0,0,100,100,0,0,4,14,0,2,220,220,42,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for a, b, txt in eventos:
        ass.append(f"Dialogue: 0,{tc(a)},{tc(b)},Sub,,0,0,0,,{txt}")
    (TMP / "subs.ass").write_text("\n".join(ass), encoding="utf-8")
    srt = []
    for i, (a, b, txt) in enumerate(eventos, 1):
        f = lambda s: f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d},{int(s * 1000 % 1000):03d}"
        srt.append(f"{i}\n{f(a)} --> {f(b)}\n{txt}\n")
    (SAL / "UniRed - subtitulos.srt").write_text("\n".join(srt), encoding="utf-8")

    lista = TMP / "videos.txt"
    lista.write_text("\n".join(f"file '{v.as_posix()}'" for v in videos), encoding="utf-8")
    final = SAL / "UniRed - Proyecto I+D (video explicativo).mp4"
    subs = (TMP / "subs.ass").as_posix().replace(":", "\\:")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-i", str(TMP / "narracion.wav"),
                    "-vf", f"ass='{subs}'", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(final)], check=True)
    nombres = {e["id"]: e["lineas"][0][:60] for e in ESCENAS}
    (SAL / "capitulos.txt").write_text("\n".join(f"{int(t // 60)}:{int(t % 60):02d} {nombres[i]}" for t, i in capitulos), encoding="utf-8")
    print("LISTO", final, f"{t_global / 60:.1f} min")


if __name__ == "__main__":
    main()
