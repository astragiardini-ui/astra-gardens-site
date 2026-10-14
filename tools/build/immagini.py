#!/usr/bin/env python3
"""
Immagini del sito nuovo (14/10/2026) che non escono da tools/prima-dopo né da tools/video:
- foto-furgone: la foto del furgone nel giardino con piscina (MEDIA/video_hd_14ott/foto-furgone-1080.jpg),
  in WebP a più larghezze più un JPEG di riserva, SEMPRE intera (mai ritagliata);
- il logo bianco (sopra i video) e il logo verde (testata) ad alta definizione, dal logo originale
  3138x641 del gestionale (fatture_Cloud/assets);
- le locandine piccole (540 px) dei video verticali, per la striscia dei cantieri (il video resta 1080);
- l'immagine di anteprima per WhatsApp e social (og-astra-gardens.jpg, 1200x675 = 16:9, il fotogramma
  intero, senza ritagli): un fotogramma del video dei fiori con il logo bianco in alto al centro.

Uso, dalla cartella del sito (serve Pillow e, per l'anteprima, ffmpeg):
    python3 tools/build/immagini.py
Poi si rilancia tools/build/build_site.py, che legge le misure dai file.
"""
import os
import subprocess
import tempfile

from PIL import Image, ImageFilter

QUI = os.path.dirname(os.path.abspath(__file__))
SITO = os.path.abspath(os.path.join(QUI, "..", ".."))
IMG = os.path.join(SITO, "assets", "img")
MEDIA = os.path.expanduser(os.environ.get("ASTRA_MEDIA", "~/Documents/AstraMarketing"))
LOGO = os.path.expanduser(os.environ.get("ASTRA_LOGO", "~/Documents/Progetti_VS_Code/fatture_Cloud/assets/logo-astra.png"))


def varianti(src, nome, larghezze, jpg=640):
    im = Image.open(src).convert("RGB")
    for w in larghezze:
        if w > im.width:
            raise SystemExit("%s: %d px chiesti ma la foto è larga %d (niente ingrandimenti)" % (nome, w, im.width))
        r = im if w == im.width else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        r.save(os.path.join(IMG, "%s-%d.webp" % (nome, w)), "WEBP", quality=82, method=6)
    r = im.resize((jpg, round(im.height * jpg / im.width)), Image.LANCZOS)
    r.save(os.path.join(IMG, "%s-%d.jpg" % (nome, jpg)), "JPEG", quality=82, optimize=True, progressive=True)
    print("  %s: %s + jpg %d (%dx%d)" % (nome, larghezze, jpg, im.width, im.height))


def loghi():
    """Il logo originale è nero su trasparente: si tiene l'alfa e si cambia il colore."""
    base = Image.open(LOGO).convert("RGBA")
    alfa = base.getchannel("A")
    bbox = alfa.getbbox()
    alfa = alfa.crop(bbox)
    # PNG solo alla larghezza che la pagina usa come riserva (<img src>); le altre solo in WebP (srcset)
    for colore, nome, larghezze, png in (((255, 255, 255), "logo-bianco", (640, 960, 1400), 640),
                                          ((15, 81, 50), "logo-verde", (480, 960), 480)):
        tinta = Image.new("RGBA", alfa.size, colore + (255,))
        tinta.putalpha(alfa)
        for w in larghezze:
            r = tinta.resize((w, round(alfa.height * w / alfa.width)), Image.LANCZOS)
            r.save(os.path.join(IMG, "%s-%d.webp" % (nome, w)), "WEBP", lossless=True, method=6)
            if w == png:
                r.save(os.path.join(IMG, "%s-%d.png" % (nome, w)), "PNG", optimize=True)
        print("  %s: %s (%dx%d)" % (nome, larghezze, alfa.width, alfa.height))
    return alfa


def anteprima(alfa):
    video = os.path.join(SITO, "assets", "video", "hero-fiori.mp4")
    tmp = tempfile.mkdtemp(prefix="astra-og-")
    png = os.path.join(tmp, "f.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "2.5", "-i", video, "-frames:v", "1", png], check=True)
    im = Image.open(png).convert("RGB")
    im = im.resize((1200, 675), Image.LANCZOS).convert("RGBA")  # fotogramma intero, mai ritagliato
    w = 560
    a = alfa.resize((w, round(alfa.height * w / alfa.width)), Image.LANCZOS)
    x, y = (1200 - w) // 2, 90
    ombra = Image.new("RGBA", im.size, (0, 0, 0, 0))
    nero = Image.new("RGBA", a.size, (0, 0, 0, 255))
    nero.putalpha(a.point(lambda v: v * 0.5))
    ombra.paste(nero, (x, y + 3), nero)
    ombra = ombra.filter(ImageFilter.GaussianBlur(10))
    im.alpha_composite(ombra)
    bianco = Image.new("RGBA", a.size, (255, 255, 255, 255))
    bianco.putalpha(a)
    im.alpha_composite(bianco, (x, y))
    im.convert("RGB").save(os.path.join(IMG, "og-astra-gardens.jpg"), "JPEG", quality=84, optimize=True, progressive=True)
    os.remove(png)
    os.rmdir(tmp)
    print("  og-astra-gardens.jpg 1200x675")


def locandine_piccole():
    for nome in ("verticale-fiori", "giardino-piscina-1", "giardino-piscina-2"):
        src = os.path.join(SITO, "assets", "video", nome + "-poster.jpg")
        im = Image.open(src).convert("RGB")
        r = im.resize((540, round(im.height * 540 / im.width)), Image.LANCZOS)
        r.save(os.path.join(SITO, "assets", "video", nome + "-poster-540.webp"), "WEBP", quality=80, method=6)
    print("  locandine 540 px dei video verticali")


if __name__ == "__main__":
    varianti(os.path.join(MEDIA, "video_hd_14ott", "foto-furgone-1080.jpg"), "foto-furgone", (480, 720, 1080))
    alfa = loghi()
    anteprima(alfa)
    locandine_piccole()
