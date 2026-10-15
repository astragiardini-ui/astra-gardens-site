#!/usr/bin/env python3
"""
Montaggio dei video del sito Astra Gardens (fuori dalla pagina: serve solo a rifarli).

Regola fissa di Francesco (06/10/2026, «i video sono sgranati, voglio la massima qualità»):
- si parte SOLO dagli originali dell'iPhone (4K o 1080), mai da copie scaricate da Instagram o già
  compresse: lo script rifiuta i file delle cartelle instagram*/ e ogni sorgente sotto i 1080 px;
- ogni video esce in verticale 1080x1920, H.264 CRF 20, preset slow, yuv420p, +faststart, senza
  audio e senza metadati: un file solo, uguale per telefono e computer;
- niente viene ingrandito: se un ritaglio è più stretto di 1080 px lo script si ferma e chiede di
  allargarlo;
- il peso della pagina si gestisce caricando le clip solo quando entrano nello schermo
  (preload="none" + assets/js/main.js), mai abbassando la qualità.

Uso, dalla cartella del sito (Pillow serve per i poster: stesso venv di tools/prima-dopo):
    /private/tmp/claude-501/allinea/bin/python tools/video/montaggio.py apertura   # apertura + poster + copia per Google
    /private/tmp/claude-501/allinea/bin/python tools/video/montaggio.py clip       # clip delle sezioni + poster
    /private/tmp/claude-501/allinea/bin/python tools/video/montaggio.py clip --solo antizanzare
    /private/tmp/claude-501/allinea/bin/python tools/video/montaggio.py interi     # i due video interi dell'apertura
    python3 tools/video/montaggio.py hd       # video HD del 14/10/2026: copia + furgone 2560 + poster
    /private/tmp/claude-501/allinea/bin/python tools/video/montaggio.py tutto
    python3 tools/video/montaggio.py controlla   # ffprobe di tutti i video pubblicati

Cosa serve: ffmpeg (Homebrew) e, per i .mov dell'iPhone, avconvert (già dentro macOS).

Le scelte (quali video, da che secondo, quanto lunghi, come ritagliare) stanno tutte in
tools/video/video.json. I file sorgente stanno in MEDIA (default ~/Documents/AstraMarketing, si
cambia con la variabile d'ambiente ASTRA_MEDIA) e NON vanno nel repository. Una riga con
"sorgente": null è un video di cui manca l'originale: nell'apertura quel pezzo resta fuori, e al
posto della clip la pagina mostra una foto (RIPIEGO_CLIP in tools/build/build_site.py). Quando
arriva l'originale basta scriverne il percorso, rilanciare questo script e poi
tools/build/build_site.py.

Passaggi:
1. I .mov dell'iPhone sono HDR (HLG, 10 bit): avconvert li porta in SDR con la conversione di Apple
   (Preset3840x2160: tiene la risoluzione originale fino al 4K e toglie i metadati sensibili, per
   esempio la posizione GPS). Le conversioni restano in una cache e si riusano.
2. Ogni pezzo viene tagliato (-ss/-t), ritagliato in verticale 9:16, portato a 1080x1920 e a 30 fps,
   in un file intermedio quasi senza perdite (CRF 6).
   "ritaglio": [cx, y0, y1] = zona da y0 a y1 (frazioni dell'altezza), centrata in cx (frazione della
   larghezza); con un 4K verticale (2160x3840) y1 - y0 deve valere almeno 0,5. null = fotogramma intero.
3. Apertura: i pezzi si uniscono con dissolvenze brevi (xfade), poi l'uscita finale.
4. Poster: primo fotogramma, 1080x1920, in WebP e JPEG.

Comando ffmpeg dell'uscita finale (uguale per apertura e clip):
    ffmpeg -i intermedio.mp4 -an -map_metadata -1 -c:v libx264 -profile:v high -level 4.1 \\
      -preset slow -crf 20 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 \\
      -color_trc bt709 -color_range tv -movflags +faststart uscita.mp4
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

QUI = os.path.dirname(os.path.abspath(__file__))
SITO = os.path.abspath(os.path.join(QUI, "..", ".."))
MEDIA = os.path.expanduser(os.environ.get("ASTRA_MEDIA", "~/Documents/AstraMarketing"))
CACHE = os.path.join(tempfile.gettempdir(), "astra-video-cache")
LATO_MINIMO = 1080


def esegui(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(" ".join(cmd) + "\n" + r.stderr[-2000:] + "\n")
        raise SystemExit("comando fallito")
    return r.stdout


def info(path):
    out = esegui(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                  "stream=width,height,color_transfer:stream_side_data=rotation",
                  "-of", "json", path])
    s = json.loads(out)["streams"][0]
    w, h = s["width"], s["height"]
    rot = 0
    for sd in s.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if abs(rot) == 90:
        w, h = h, w
    return w, h, s.get("color_transfer", "")


def sorgente_sdr(rel):
    """Percorso di un ORIGINALE pronto per ffmpeg: i .mov HDR passano da avconvert (con cache)."""
    if rel.replace("\\", "/").split("/")[0].lower().startswith("instagram"):
        raise SystemExit("%s è una copia scaricata da Instagram: serve l'originale dell'iPhone" % rel)
    src = os.path.join(MEDIA, rel)
    if not os.path.exists(src):
        raise SystemExit("manca il file sorgente: " + src)
    w, h, _ = info(src)
    if min(w, h) < LATO_MINIMO:
        raise SystemExit("%s è %dx%d: sotto i %d px non si pubblica, serve l'originale" % (rel, w, h, LATO_MINIMO))
    if not rel.lower().endswith(".mov"):
        return src
    os.makedirs(CACHE, exist_ok=True)
    st = os.stat(src)
    dst = os.path.join(CACHE, "%s-%d-%d.mp4" % (os.path.basename(rel)[:-4], st.st_size, int(st.st_mtime)))
    if not os.path.exists(dst):
        print("  converto in SDR:", rel)
        esegui(["avconvert", "-s", src, "-p", "Preset3840x2160", "-o", dst, "--replace"])
    return dst


def filtro(path, ritaglio, ow, oh):
    w, h, _ = info(path)
    if ritaglio:
        cx, y0, y1 = ritaglio
        ch = (y1 - y0) * h
        cw = ch * 9 / 16
        if cw > w:
            cw = w
            ch = cw * 16 / 9
        x = cx * w - cw / 2
        y = y0 * h
    else:
        if w / h > 9 / 16:
            ch, cw = h, h * 9 / 16
        else:
            cw, ch = w, w * 16 / 9
        x, y = (w - cw) / 2, (h - ch) / 2
    cw, ch = int(round(cw)) // 2 * 2, int(round(ch)) // 2 * 2
    if cw < ow - 2:
        raise SystemExit("il ritaglio %s di %s è largo %d px: verrebbe ingrandito fino a %d. Allargalo "
                         "(y1 - y0 almeno %.2f)" % (ritaglio, os.path.basename(path), cw, ow, oh / h))
    x = max(0, min(w - cw, int(round(x))))
    y = max(0, min(h - ch, int(round(y))))
    scala = "" if (cw, ch) == (ow, oh) else ",scale=%d:%d:flags=lanczos" % (ow, oh)
    return "crop=%d:%d:%d:%d%s,setsar=1,fps=30,format=yuv420p" % (cw, ch, x, y, scala)


def pezzo(p, out, ow, oh):
    """Pezzo intermedio quasi senza perdite (CRF 6): la compressione vera si fa una volta sola, alla fine."""
    src = sorgente_sdr(p["sorgente"])
    esegui(["ffmpeg", "-v", "error", "-y", "-ss", str(p["inizio"]), "-t", str(p["durata"]), "-i", src,
            "-vf", filtro(src, p.get("ritaglio"), ow, oh), "-an", "-map_metadata", "-1",
            "-c:v", "libx264", "-preset", "fast", "-crf", "6", out])


def descrivi(path):
    s = json.loads(esegui(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=width,height,bit_rate:format=duration,size", "-of", "json", path]))
    v, f = s["streams"][0], s["format"]
    return int(v["width"]), int(v["height"]), int(v.get("bit_rate") or 0), float(f["duration"]), int(f["size"])


def codifica(src, out, q):
    """Uscita finale: 1080x1920, CRF 20, preset slow. Il peso non abbassa MAI la qualità."""
    w = int(q["larghezza"])
    h = w * 16 // 9 // 2 * 2
    os.makedirs(os.path.dirname(out), exist_ok=True)
    esegui(["ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-map_metadata", "-1", "-map_chapters", "-1",
            "-vf", "scale=%d:%d:flags=lanczos,setsar=1" % (w, h),
            "-c:v", "libx264", "-profile:v", "high", "-level", "5.1" if w > 1080 else "4.1", "-preset", q["preset"],
            "-crf", str(q["crf"]), "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart", out])
    W, H, br, dur, size = descrivi(out)
    print("  %s  %dx%d  crf %s %s  %.1f s  %.1f Mbit/s  %.1f MB"
          % (os.path.relpath(out, SITO), W, H, q["crf"], q["preset"], dur, br / 1e6, size / 1048576))


def poster(video, base, larghezza=1080):
    """Primo fotogramma come immagine d'attesa: WebP per tutti, JPEG di riserva per i browser vecchi."""
    from PIL import Image
    png = base + ".tmp.png"
    esegui(["ffmpeg", "-v", "error", "-y", "-i", video, "-frames:v", "1", png])
    im = Image.open(png).convert("RGB")
    if im.size[0] != larghezza:
        im = im.resize((larghezza, round(im.size[1] * larghezza / im.size[0])), Image.LANCZOS)
    im.save(base + ".webp", "WEBP", quality=80, method=6)
    im.save(base + ".jpg", "JPEG", quality=82, optimize=True, progressive=True)
    os.remove(png)


def apertura(cfg):
    a, q = cfg["apertura"], cfg["qualita"]
    w = int(q["larghezza"])
    h = w * 16 // 9 // 2 * 2
    usati = [p for p in a["pezzi"] if p.get("sorgente")]
    for p in a["pezzi"]:
        if not p.get("sorgente"):
            print("  RESTA FUORI (manca l'originale): %s. %s" % (p["nome"], p.get("_manca", "")))
    tmp = tempfile.mkdtemp(prefix="astra-apertura-")
    try:
        pezzi = []
        for i, p in enumerate(usati):
            out = os.path.join(tmp, "p%02d.mp4" % i)
            print("  pezzo %d: %s" % (i + 1, p["nome"]))
            pezzo(p, out, w, h)
            pezzi.append((out, float(p["durata"])))
        f = float(a["dissolvenza"])
        args, filtri = [], []
        for out, _ in pezzi:
            args += ["-i", out]
        ultimo, durata = "[0:v]", pezzi[0][1]
        for i in range(1, len(pezzi)):
            nome = "[x%d]" % i
            filtri.append("%s[%d:v]xfade=transition=fade:duration=%.2f:offset=%.3f%s"
                          % (ultimo, i, f, durata - f, nome))
            ultimo, durata = nome, durata + pezzi[i][1] - f
        montaggio = os.path.join(tmp, "montaggio.mp4")
        esegui(["ffmpeg", "-v", "error", "-y"] + args +
               ["-filter_complex", ";".join(filtri) + ";%sformat=yuv420p[out]" % ultimo, "-map", "[out]",
                "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "6", montaggio])
        print("  durata totale: %.1f s" % durata)
        uscita = os.path.join(SITO, a["file"])
        codifica(montaggio, uscita, q)
        poster(uscita, os.path.join(SITO, a["poster"]), w)
        if a.get("copia_google"):
            # scheda Google: stesso file, massimo 30 secondi e 75 MB
            dst = os.path.expanduser(a["copia_google"])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(uscita, dst)
            _, _, _, dur, size = descrivi(dst)
            if dur > 30 or size > 75 * 1048576:
                raise SystemExit("la copia per Google supera 30 s o 75 MB: %.1f s, %.1f MB" % (dur, size / 1048576))
            print("  copia per la scheda Google:", dst)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def interi(cfg):
    """Video INTERI, nell'inquadratura originale dell'iPhone (nessun ritaglio, nessun ingrandimento):
    sono i due video in cima alla pagina (Francesco 13/10/2026: «voglio l'inquadratura originale»).
    Stessa conversione HDR -> SDR di avconvert, poi H.264 col CRF di "interi" (18), preset slow."""
    v_cfg = cfg["interi"]
    for v in v_cfg["video"]:
        src = sorgente_sdr(v["sorgente"])
        w, h, _ = info(src)
        if abs(w / h - 9 / 16) > 0.005:
            raise SystemExit("%s non è 9:16 (%dx%d): l'inquadratura originale non entra nel riquadro" % (v["nome"], w, h))
        ow = int(v["larghezza"])
        oh = ow * 16 // 9 // 2 * 2
        if ow > w:
            raise SystemExit("%s: %d px chiesti ma l'originale è largo %d: niente ingrandimenti" % (v["nome"], ow, w))
        out = os.path.join(SITO, v_cfg["cartella"], v["nome"] + ".mp4")
        print("  video intero: %s (%dx%d -> %dx%d)" % (v["nome"], w, h, ow, oh))
        q = {"larghezza": ow, "crf": v_cfg["crf"], "preset": v_cfg["preset"]}
        tmp = tempfile.mkdtemp(prefix="astra-intero-")
        try:
            grezzo = os.path.join(tmp, "grezzo.mp4")
            durata = ["-t", str(v["durata"])] if v.get("durata") else []
            esegui(["ffmpeg", "-v", "error", "-y", "-ss", str(v.get("inizio", 0))] + durata + ["-i", src,
                    "-vf", "setsar=1,fps=30,format=yuv420p", "-an", "-map_metadata", "-1",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "6", grezzo])
            codifica(grezzo, out, q)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        poster(out, os.path.join(SITO, v_cfg["cartella"], v["nome"] + "-poster"), ow)


def clip(cfg, solo=None):
    q = cfg["qualita"]
    w = int(q["larghezza"])
    h = w * 16 // 9 // 2 * 2
    tmp = tempfile.mkdtemp(prefix="astra-clip-")
    try:
        for c in cfg["clip"]:
            if solo and c["nome"] != solo:
                continue
            if not c.get("sorgente"):
                print("  clip %s: manca l'originale, sul sito resta la foto di ripiego. %s" % (c["nome"], c.get("_manca", "")))
                continue
            print("  clip:", c["nome"], "-", c["descrizione"])
            grezzo = os.path.join(tmp, c["nome"] + ".mp4")
            pezzo(c, grezzo, w, h)
            out = os.path.join(SITO, cfg["cartella_clip"], c["nome"] + ".mp4")
            codifica(grezzo, out, q)
            poster(out, os.path.join(SITO, cfg["cartella_clip"], c["nome"] + "-poster"), w)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def hd(cfg, solo=None):
    """Video HD del sito ("hd" in video.json). I file "copia" sono già l'uscita finale (H.264 SDR,
    faststart): si copiano senza ricodificarli. I file "rendi" si portano alla larghezza chiesta partendo
    dal master (furgone 2560 dal 4K con la targa sfocata) o dall'ORIGINALE dell'iPhone (.mov HDR: passa
    da avconvert come le clip). Poster ("poster": larghezza): primo fotogramma, WebP e JPEG.
    Il nome dell'originale non sfocato del furgone ("vietati") fa fermare tutto. --solo NOME = una voce."""
    c = cfg["hd"]
    cartella = os.path.join(SITO, c["cartella"])
    def sorgente(rel):
        if any(v.lower() in rel.lower() for v in c.get("vietati", [])):
            raise SystemExit("%s è l'originale NON sfocato: si usa solo il master con la targa sfocata" % rel)
        src = os.path.join(MEDIA, rel)
        if not os.path.exists(src):
            raise SystemExit("manca il file sorgente: " + src)
        w, h, trc = info(src)
        if min(w, h) < LATO_MINIMO:
            raise SystemExit("%s è %dx%d: sotto i %d px non si pubblica" % (rel, w, h, LATO_MINIMO))
        if trc in ("arib-std-b67", "smpte2084"):
            if rel.lower().endswith(".mov"):
                return sorgente_sdr(rel)  # originale dell'iPhone: HDR -> SDR con avconvert
            raise SystemExit("%s è HDR (%s): serve la versione SDR" % (rel, trc))
        return src
    for v in c["copia"]:
        if solo and v["nome"] != solo:
            continue
        src = sorgente(v["file"])
        out = os.path.join(cartella, v["nome"] + ".mp4")
        shutil.copyfile(src, out)
        W, H, br, dur, size = descrivi(out)
        print("  copia %s  %dx%d  %.1f s  %.1f Mbit/s  %.1f MB" % (os.path.relpath(out, SITO), W, H, dur, br / 1e6, size / 1048576))
        poster(out, os.path.join(cartella, v["nome"] + "-poster"), int(v["poster"]))
    for v in c["rendi"]:
        if solo and v["nome"] != solo:
            continue
        src = sorgente(v["file"])
        w, h, _ = info(src)
        ow = int(v["larghezza"])
        oh = round(ow * h / w) // 2 * 2
        if ow > w:
            raise SystemExit("%s: %d px chiesti ma il master è largo %d: niente ingrandimenti" % (v["nome"], ow, w))
        out = os.path.join(cartella, v["nome"] + ".mp4")
        esegui(["ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-map_metadata", "-1", "-map_chapters", "-1",
                "-vf", "scale=%d:%d:flags=lanczos,setsar=1,format=yuv420p" % (ow, oh),
                "-c:v", "libx264", "-profile:v", "high", "-preset", v["preset"], "-crf", str(v["crf"]),
                "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                "-color_range", "tv", "-movflags", "+faststart", out])
        W, H, br, dur, size = descrivi(out)
        print("  rendi %s  %dx%d  crf %s %s  %.1f s  %.1f Mbit/s  %.1f MB"
              % (os.path.relpath(out, SITO), W, H, v["crf"], v["preset"], dur, br / 1e6, size / 1048576))
        if v.get("poster"):
            poster(out, os.path.join(cartella, v["nome"] + "-poster"), int(v["poster"]))


def controlla():
    """ffprobe di ogni video pubblicato: lato corto almeno 1080 px."""
    cartella = os.path.join(SITO, "assets", "video")
    male = 0
    for radice, _, files in os.walk(cartella):
        for f in sorted(files):
            if not f.endswith(".mp4"):
                continue
            p = os.path.join(radice, f)
            W, H, br, dur, size = descrivi(p)
            ok = min(W, H) >= LATO_MINIMO
            male += not ok
            print("%-48s %4dx%-5d %5.1f s  %5.1f Mbit/s  %5.1f MB  %s"
                  % (os.path.relpath(p, SITO), W, H, dur, br / 1e6, size / 1048576, "ok" if ok else "SOTTO 1080 px"))
    if male:
        raise SystemExit("%d video sotto i %d px" % (male, LATO_MINIMO))


def main():
    cfg = json.load(open(os.path.join(QUI, "video.json"), encoding="utf-8"))
    cosa = sys.argv[1] if len(sys.argv) > 1 else "tutto"
    solo = sys.argv[sys.argv.index("--solo") + 1] if "--solo" in sys.argv else None
    if cosa in ("apertura", "tutto"):
        print("Video d'apertura")
        apertura(cfg)
    if cosa in ("interi", "tutto"):
        print("Video interi dell'apertura")
        interi(cfg)
    if cosa in ("clip", "tutto"):
        print("Clip delle sezioni")
        clip(cfg, solo)
    if cosa in ("hd", "tutto"):
        print("Video HD del sito (14/10/2026)")
        hd(cfg, solo)
    if cosa in ("controlla", "tutto"):
        print("Controllo dei video pubblicati")
        controlla()


if __name__ == "__main__":
    main()
