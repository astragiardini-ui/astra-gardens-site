#!/usr/bin/env python3
"""
Montaggio dei video del sito Astra Gardens (fuori dalla pagina: serve solo a rifarli).

Uso, dalla cartella del sito:
    python3 tools/video/montaggio.py apertura   # video d'apertura + poster
    python3 tools/video/montaggio.py clip       # clip brevi delle sezioni + poster
    python3 tools/video/montaggio.py tutto
    python3 tools/video/montaggio.py poster     # solo le immagini d'attesa delle clip
    python3 tools/video/montaggio.py clip --solo antizanzare   # rifà una clip sola

Ogni clip esce in due misure: 540x960 per il computer e 432x768 per il telefono (-telefono.mp4).
Il video d'apertura esce in 720x1280 in due pesi: sul telefono riempie lo schermo come un Reel,
quindi anche la versione -telefono.mp4 resta a 720 di larghezza, solo un po' più compressa.
La pagina sceglie da sola con <source media="(max-width: 959px)">.

Cosa serve: ffmpeg (Homebrew) e, per i .mov dell'iPhone, avconvert (già dentro macOS).
Pillow (PIL) per i poster.

Le scelte (quali video, da che secondo, quanto lunghi, come ritagliare) stanno tutte in
tools/video/video.json: per aggiungere un video nuovo basta aggiungere una riga lì e
rilanciare il comando. I file sorgente stanno in MEDIA (default ~/Documents/AstraMarketing,
si cambia con la variabile d'ambiente ASTRA_MEDIA) e NON vanno nel repository.

Passaggi:
1. I .mov dell'iPhone sono HDR (HLG, 10 bit): li converto in SDR con avconvert
   (Preset3840x2160, tiene la risoluzione originale fino al 4K e toglie i metadati sensibili,
   per esempio la posizione GPS). Le conversioni restano in una cache e si riusano.
2. Ogni pezzo viene tagliato (-ss/-t), ritagliato in verticale 9:16 e portato a 30 fps.
   "ritaglio": [cx, y0, y1] = zona alta da y0 a y1 (frazioni dell'altezza), centrata in cx
   (frazione della larghezza). null = fotogramma intero.
3. Apertura: i pezzi si uniscono con dissolvenze brevi (xfade). Uscite H.264 senza audio,
   senza metadati, +faststart; il CRF sale da solo finché il file sta sotto "max_kb".
4. Poster: primo fotogramma, in WebP e JPEG.

Esempio di comando ffmpeg per un pezzo (quello che lo script fa per ogni riga):
    ffmpeg -ss 2.0 -t 2.3 -i sorgente.mp4 \\
      -vf "crop=886:1574:853:460,scale=720:1280:flags=lanczos,setsar=1,fps=30,format=yuv420p" \\
      -an -c:v libx264 -preset medium -crf 12 pezzo.mp4
e per l'uscita finale:
    ffmpeg -i montaggio.mp4 -an -map_metadata -1 -c:v libx264 -profile:v high -level 4.0 \\
      -preset veryslow -crf 28 -pix_fmt yuv420p -movflags +faststart astra-gardens-lavori.mp4
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
    """Percorso di un file pronto per ffmpeg: i .mov HDR passano da avconvert (con cache)."""
    src = os.path.join(MEDIA, rel)
    if not os.path.exists(src):
        raise SystemExit("manca il file sorgente: " + src)
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
    cw, ch = int(cw) // 2 * 2, int(ch) // 2 * 2
    x = max(0, min(w - cw, int(x)))
    y = max(0, min(h - ch, int(y)))
    return ("crop=%d:%d:%d:%d,scale=%d:%d:flags=lanczos,setsar=1,fps=30,format=yuv420p"
            % (cw, ch, x, y, ow, oh))


def pezzo(p, out, ow, oh):
    src = sorgente_sdr(p["sorgente"])
    esegui(["ffmpeg", "-v", "error", "-y", "-ss", str(p["inizio"]), "-t", str(p["durata"]), "-i", src,
            "-vf", filtro(src, p.get("ritaglio"), ow, oh), "-an", "-map_metadata", "-1",
            "-c:v", "libx264", "-preset", "medium", "-crf", "12", out])


def codifica(src, out, larghezza, max_kb, crf=26):
    altezza = larghezza * 16 // 9 // 2 * 2
    os.makedirs(os.path.dirname(out), exist_ok=True)
    while True:
        esegui(["ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-map_metadata", "-1", "-map_chapters", "-1",
                "-vf", "scale=%d:%d:flags=lanczos,setsar=1" % (larghezza, altezza),
                "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-preset", "veryslow",
                "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", out])
        kb = os.path.getsize(out) / 1024
        if kb <= max_kb or crf >= 38:
            print("  %s  %dx%d  crf %d  %.0f KB" % (os.path.relpath(out, SITO), larghezza, altezza, crf, kb))
            return
        crf += 1


def poster(video, base, larghezza, larghezza_jpg=None, qualita_jpg=78):
    """Primo fotogramma come immagine d'attesa: WebP per tutti, JPEG di riserva per i browser vecchi."""
    from PIL import Image
    png = base + ".tmp.png"
    esegui(["ffmpeg", "-v", "error", "-y", "-i", video, "-frames:v", "1", png])
    im = Image.open(png).convert("RGB")
    def misura(w):
        return im if im.size[0] == w else im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS)
    misura(larghezza).save(base + ".webp", "WEBP", quality=74, method=6)
    misura(larghezza_jpg or larghezza).save(base + ".jpg", "JPEG", quality=qualita_jpg, optimize=True, progressive=True)
    os.remove(png)


def apertura(cfg):
    a = cfg["apertura"]
    tmp = tempfile.mkdtemp(prefix="astra-apertura-")
    try:
        pezzi = []
        for i, p in enumerate(a["pezzi"]):
            out = os.path.join(tmp, "p%02d.mp4" % i)
            print("  pezzo %d: %s" % (i + 1, p["nome"]))
            pezzo(p, out, 720, 1280)
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
                "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "12", montaggio])
        print("  durata totale: %.1f s" % durata)
        for u in a["uscite"]:
            codifica(montaggio, os.path.join(SITO, u["file"]), u["larghezza"], u["max_kb"])
        poster(os.path.join(SITO, a["uscite"][0]["file"]), os.path.join(SITO, a["poster"]), 720)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def clip(cfg, solo=None):
    tmp = tempfile.mkdtemp(prefix="astra-clip-")
    try:
        for c in cfg["clip"]:
            if solo and c["nome"] != solo:
                continue
            print("  clip:", c["nome"], "-", c["descrizione"])
            grezzo = os.path.join(tmp, c["nome"] + ".mp4")
            pezzo(c, grezzo, 540, 960)
            uscite = cfg.get("uscite_clip", [{"suffisso": "", "larghezza": 540, "max_kb": cfg["max_kb_clip"]}])
            for u in uscite:
                out = os.path.join(SITO, cfg["cartella_clip"], c["nome"] + u["suffisso"] + ".mp4")
                codifica(grezzo, out, u["larghezza"], u["max_kb"], crf=27)
            principale = os.path.join(SITO, cfg["cartella_clip"], c["nome"] + uscite[0]["suffisso"] + ".mp4")
            poster(principale, os.path.join(SITO, cfg["cartella_clip"], c["nome"] + "-poster"), 540,
                   larghezza_jpg=432, qualita_jpg=72)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    cfg = json.load(open(os.path.join(QUI, "video.json"), encoding="utf-8"))
    cosa = sys.argv[1] if len(sys.argv) > 1 else "tutto"
    solo = sys.argv[sys.argv.index("--solo") + 1] if "--solo" in sys.argv else None
    if cosa in ("apertura", "tutto"):
        print("Video d'apertura")
        apertura(cfg)
    if cosa in ("clip", "tutto"):
        print("Clip delle sezioni")
        clip(cfg, solo)
    if cosa == "poster":
        # rifà solo le immagini d'attesa delle clip, dai video già pronti
        for c in cfg["clip"]:
            v = os.path.join(SITO, cfg["cartella_clip"], c["nome"] + ".mp4")
            poster(v, os.path.join(SITO, cfg["cartella_clip"], c["nome"] + "-poster"), 540, larghezza_jpg=432, qualita_jpg=72)
            print("  poster:", c["nome"])


if __name__ == "__main__":
    main()
