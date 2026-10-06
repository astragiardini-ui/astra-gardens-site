#!/usr/bin/env python3
"""
Coppie OGGI / PROGETTO della sezione «Progetto e render IA» (fuori dalla pagina: serve solo a rifarle).

Il render IA nasce dalla foto di oggi, ma esce con un'altra misura e a volte con l'inquadratura
spostata di qualche pixel. Sotto il cursore le due immagini devono combaciare, e la composizione
si vede INTERA (niente ritagli fissi 3:2): la pagina dà al riquadro le proporzioni della coppia.

Uso (stesso ambiente OpenCV di allinea.py, fuori dal repo):
    /private/tmp/claude-501/allinea/bin/python tools/prima-dopo/render.py tools/prima-dopo/render.json [--ricalcola] [--controllo cartella]

render.json, per ogni coppia:
  "oggi", "progetto"  foto di oggi e render, relativi a MEDIA (~/Documents/AstraMarketing, o ASTRA_MEDIA)
  "omografia"         matrice 3x3 foto ridotta -> render (salvata qui perché il risultato non cambi a
                      ogni giro); null = le due immagini coincidono già
  "zona"              frazione alta dell'immagine dove cercare i punti comuni con --ricalcola
                      (1.0 = tutta l'immagine; 0.45 = solo case e muri, che il render non cambia)
  "uscita"            [nome oggi, nome progetto] in assets/img
  "larghezze"         larghezze WebP oltre a quella piena; il JPEG di riserva è sempre a 640

Passaggi:
1. la foto viene raddrizzata con l'omografia a piena risoluzione e solo dopo ridotta alla misura
   del render (INTER_AREA: niente scalettature, niente doppia sfocatura);
2. si tiene il rettangolo più grande in cui la foto raddrizzata è piena, lo stesso per il render:
   pochi pixel di bordo al massimo, mai la composizione tagliata;
3. uscite WebP in più larghezze + JPEG 640, con gli stessi nomi che usa la pagina
   (tools/build/build_site.py legge le misure direttamente dai file).
Con --controllo salva per ogni coppia un'immagine a strisce alterne: case, muri e pavimenti
devono continuare senza salti.
"""
import json
import os
import re
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter

QUI = os.path.dirname(os.path.abspath(__file__))
SITO = os.path.abspath(os.path.join(QUI, "..", ".."))
MEDIA = os.path.expanduser(os.environ.get("ASTRA_MEDIA", "~/Documents/AstraMarketing"))


def stima_omografia(foto_ridotta, render, zona):
    """SIFT + MAGSAC sulla zona alta (o su tutta l'immagine): omografia foto ridotta -> render."""
    g1 = cv2.cvtColor(foto_ridotta, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(render, cv2.COLOR_BGR2GRAY)
    cl = cv2.createCLAHE(2.0, (8, 8))
    g1, g2 = cl.apply(g1), cl.apply(g2)
    m1, m2 = np.zeros_like(g1), np.zeros_like(g2)
    m1[:int(zona * g1.shape[0])] = 255
    m2[:int(zona * g2.shape[0])] = 255
    sift = cv2.SIFT_create(nfeatures=8000)
    k1, d1 = sift.detectAndCompute(g1, m1)
    k2, d2 = sift.detectAndCompute(g2, m2)
    buoni = [a for a, b in cv2.BFMatcher(cv2.NORM_L2).knnMatch(d1, d2, k=2) if a.distance < 0.75 * b.distance]
    p1 = np.float32([k1[g.queryIdx].pt for g in buoni])
    p2 = np.float32([k2[g.trainIdx].pt for g in buoni])
    H, msk = cv2.findHomography(p1, p2, cv2.USAC_MAGSAC, 3.0, maxIters=20000, confidence=0.999)
    inl = msk.ravel().astype(bool)
    q = cv2.perspectiveTransform(p1[inl].reshape(-1, 1, 2), H).reshape(-1, 2)
    print("    punti comuni %d, tenuti %d, errore medio %.2f px (senza raddrizzare: %.2f px)"
          % (len(buoni), inl.sum(), np.hypot(*(q - p2[inl]).T).mean(), np.hypot(*(p1[inl] - p2[inl]).T).mean()))
    return H


def rettangolo_pieno(valido):
    """Colonne piene, poi righe piene dentro quelle colonne: il rettangolo senza bordi vuoti."""
    col = np.where(valido.all(axis=0))[0]
    x0, x1 = col.min(), col.max() + 1
    rig = np.where(valido[:, x0:x1].all(axis=1))[0]
    return int(x0), int(rig.min()), int(x1), int(rig.max() + 1)


def esporta(img, nome, larghezze):
    im = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    W, H = im.size
    cartella = os.path.join(SITO, "assets", "img")
    for w in sorted(set([x for x in larghezze if x < W] + [W])):
        r = im if w == W else im.resize((w, round(H * w / W)), Image.LANCZOS).filter(
            ImageFilter.UnsharpMask(radius=0.7, percent=40, threshold=2))
        r.save(os.path.join(cartella, "%s-%d.webp" % (nome, w)), "WEBP", quality=(78 if w <= 900 else 74), method=6)
    im.resize((640, round(H * 640 / W)), Image.LANCZOS).save(
        os.path.join(cartella, "%s-640.jpg" % nome), "JPEG", quality=78, optimize=True, progressive=True)
    print("    %s: %dx%d" % (nome, W, H))


def main():
    percorso = sys.argv[1]
    cfg = json.load(open(percorso, encoding="utf-8"))
    ricalcola = "--ricalcola" in sys.argv
    controllo = sys.argv[sys.argv.index("--controllo") + 1] if "--controllo" in sys.argv else None
    for c in cfg["coppie"]:
        print("coppia:", c["uscita"][1])
        foto = cv2.imread(os.path.join(MEDIA, c["oggi"]))
        rend = cv2.imread(os.path.join(MEDIA, c["progetto"]))
        if foto is None or rend is None:
            raise SystemExit("foto sorgente mancanti per " + c["uscita"][1])
        hr, wr = rend.shape[:2]
        hp, wp = foto.shape[:2]
        s0 = wr / wp
        if abs(hp * s0 - hr) > 2:
            raise SystemExit("foto e render hanno proporzioni diverse: %s contro %s" % (foto.shape, rend.shape))
        if ricalcola:
            ridotta = cv2.resize(foto, (wr, hr), interpolation=cv2.INTER_AREA)
            H = stima_omografia(ridotta, rend, float(c.get("zona", 1.0)))
            c["omografia"] = [[round(float(v), 9) for v in riga] for riga in H]
        H = np.array(c["omografia"], float) if c.get("omografia") else np.eye(3)
        # raddrizzo a piena risoluzione (coordinate del render ingrandite a quelle della foto), poi riduco
        S = np.diag([s0, s0, 1.0])
        Hg = np.linalg.inv(S) @ H @ S
        grande = cv2.warpPerspective(foto, Hg, (wp, hp), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT)
        piena = cv2.warpPerspective(np.full((hp, wp), 255, np.uint8), Hg, (wp, hp), flags=cv2.INTER_NEAREST)
        oggi = cv2.resize(grande, (wr, hr), interpolation=cv2.INTER_AREA)
        valido = cv2.resize(piena, (wr, hr), interpolation=cv2.INTER_AREA) >= 254
        x0, y0, x1, y1 = rettangolo_pieno(valido)
        print("    tengo %d..%d x %d..%d di %dx%d" % (x0, x1, y0, y1, wr, hr))
        oggi, prog = oggi[y0:y1, x0:x1], rend[y0:y1, x0:x1]
        esporta(oggi, c["uscita"][0], c["larghezze"])
        esporta(prog, c["uscita"][1], c["larghezze"])
        if controllo:
            os.makedirs(controllo, exist_ok=True)
            strisce = prog.copy()
            passo = max(40, prog.shape[1] // 12)
            for x in range(0, prog.shape[1], 2 * passo):
                strisce[:, x:x + passo] = oggi[:, x:x + passo]
            cv2.imwrite(os.path.join(controllo, c["uscita"][1] + "-strisce.jpg"), strisce, [cv2.IMWRITE_JPEG_QUALITY, 88])
    if ricalcola:
        testo = json.dumps(cfg, ensure_ascii=False, indent=1)
        # liste di numeri su una riga sola, così il file resta leggibile
        testo = re.sub(r"\[\s+([^\[\]{}]*?)\s+\]", lambda m: "[" + re.sub(r"\s*\n\s*", " ", m.group(1)) + "]", testo)
        with open(percorso, "w", encoding="utf-8") as f:
            f.write(testo + "\n")
        print("omografie salvate in", percorso)


if __name__ == "__main__":
    main()
