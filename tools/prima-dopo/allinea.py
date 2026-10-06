#!/usr/bin/env python3
"""
Allinea due foto PRIMA / DOPO dello stesso giardino per il confronto col cursore del sito.

Regola fissa di Francesco: ogni prima e dopo si mostra col cursore da trascinare, mai solo
affiancato. Perché il cursore funzioni, muro, recinzione e cordolo devono combaciare: le due
foto vanno portate nella stessa prospettiva.

Uso (OpenCV in un ambiente temporaneo FUORI dal repo, niente pip di sistema):
    python3 -m venv /private/tmp/claude-501/allinea
    /private/tmp/claude-501/allinea/bin/pip install opencv-python-headless numpy pillow
    /private/tmp/claude-501/allinea/bin/python tools/prima-dopo/allinea.py tools/prima-dopo/lavoro-01.json [controllo.jpg]

Il file .json descrive il lavoro (vedi lavoro-01.json):
  "prima", "dopo"   foto sorgente, relative a MEDIA (~/Documents/AstraMarketing, o ASTRA_MEDIA)
  "punti"           almeno 4 coppie [x_prima, y_prima, x_dopo, y_dopo] su elementi FISSI e sullo
                    stesso piano (es. cima e base dei due pali della recinzione): danno l'omografia
                    che porta il PRIMA nella prospettiva del DOPO
  "linee"           (facoltative) coppie di rette y = m x + q dello stesso bordo nelle due foto
                    (es. spigoli del cordolo): correggono il terreno, che sta su un altro piano,
                    con una deformazione morbida (thin plate spline) solo in perpendicolare al bordo
  "linee_x"         (facoltativo) [x_min, x_max] nel DOPO: dove i bordi esistono davvero; fuori resta
                    l'omografia pura (niente correzioni inventate dove il cordolo non c'e')
  "ritaglio"        [x0, y0, x1, y1] nelle coordinate del DOPO: largo, in modo che si veda tutto il
                    giardino (niente civici, targhe o volti leggibili)
  "tono"            0..1, quanto avvicinare colori e luce del PRIMA a quelli del DOPO
  "tono_x_min/max"  (facoltativi) zona orizzontale usata per misurare il tono (pavimento e cordolo)
  "uscita"          nomi dei file in assets/img e larghezze da esportare

Prima si prova l'automatico (SIFT + RANSAC sugli elementi fissi): con foto scattate in giorni,
stagioni e luci diverse spesso non regge (qui: 5 punti buoni su 78). Allora i punti si mettono a
mano, leggendoli su ritagli ingranditi con la griglia, e si controlla il risultato a strisce
alterne: le linee di recinzione e cordolo devono continuare senza salti.
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter

QUI = os.path.dirname(os.path.abspath(__file__))
SITO = os.path.abspath(os.path.join(QUI, "..", ".."))
MEDIA = os.path.expanduser(os.environ.get("ASTRA_MEDIA", "~/Documents/AstraMarketing"))


def applica(H, pts):
    p = np.c_[np.asarray(pts, float), np.ones(len(pts))] @ H.T
    return p[:, :2] / p[:, 2:]


def piede(p, m, q):
    """Proiezione ortogonale del punto p sulla retta y = m x + q."""
    t = (p[0] + m * (p[1] - q)) / (1 + m * m)
    return np.array([t, m * t + q])


def tps(ctrl, val, lam=1e-6, scala=1000.0):
    """Thin plate spline 2D: restituisce una funzione che interpola gli spostamenti 'val' nei punti 'ctrl'."""
    C = np.asarray(ctrl, float) / scala
    n = len(C)

    def U(r2):
        with np.errstate(divide="ignore", invalid="ignore"):
            u = r2 * np.log(r2)
        u[r2 == 0] = 0
        return u

    K = U(((C[:, None, :] - C[None, :, :]) ** 2).sum(-1))
    P = np.c_[np.ones(n), C]
    A = np.zeros((n + 3, n + 3))
    A[:n, :n] = K + lam * np.eye(n)
    A[:n, n:] = P
    A[n:, :n] = P.T
    B = np.zeros((n + 3, 2))
    B[:n] = val
    Wt = np.linalg.solve(A, B)

    def f(q):
        q = np.asarray(q, float) / scala
        out = np.zeros((len(q), 2))
        for i in range(0, len(q), 150000):
            qq = q[i:i + 150000]
            k = U(((qq[:, None, :] - C[None, :, :]) ** 2).sum(-1))
            out[i:i + 150000] = k @ Wt[:n] + np.c_[np.ones(len(qq)), qq] @ Wt[n:]
        return out
    return f


def main():
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    prima = cv2.imread(os.path.join(MEDIA, cfg["prima"]))
    dopo = cv2.imread(os.path.join(MEDIA, cfg["dopo"]))
    if prima is None or dopo is None:
        raise SystemExit("foto sorgente mancanti")
    x0, y0, x1, y1 = cfg["ritaglio"]

    # 1) omografia dai punti fissi (PRIMA -> DOPO), poi la sua inversa per campionare
    pts = np.float32(cfg["punti"])
    H, _ = cv2.findHomography(pts[:, :2], pts[:, 2:], 0)
    Hi = np.linalg.inv(H)
    res = np.hypot(*(applica(H, pts[:, :2]) - pts[:, 2:]).T)
    print("omografia: residuo sui punti (px) max %.1f" % res.max())

    # 2) correzione del terreno lungo i bordi indicati
    gx, gy = np.meshgrid(np.arange(x0, x1, dtype=np.float64), np.arange(y0, y1, dtype=np.float64))
    Q = np.c_[gx.ravel(), gy.ravel()]
    src = applica(Hi, Q)
    linee = cfg.get("linee", [])
    if linee:
        lx0, lx1 = cfg.get("linee_x", [x0 - 100, x1 + 100])
        xs_tutti = np.arange(x0 - 100, x1 + 101, 50.0)
        xs = xs_tutti[(xs_tutti >= lx0) & (xs_tutti <= lx1)]
        ctrl, val = [], []
        corr = []
        for l in linee:
            (mp, qp), (md, qd) = l["prima"], l["dopo"]
            riga = []
            for x in xs:
                yq = md * x + qd
                p0 = applica(Hi, [[x, yq]])[0]
                riga.append((yq, piede(p0, mp, qp) - p0))
            corr.append(riga)
        # punti sulle linee, a metà fra linee vicine e sotto l'ultima
        for i, x in enumerate(xs):
            for k in range(len(corr)):
                y, d = corr[k][i]
                ctrl.append([x, y]); val.append(d)
                if k + 1 < len(corr):
                    y2, d2 = corr[k + 1][i]
                    ctrl.append([x, (y + y2) / 2]); val.append((d + d2) / 2)
            y, d = corr[-1][i]
            for extra in cfg.get("sotto_ultima", [60, 220]):
                ctrl.append([x, y + extra]); val.append(d)
        # dove il cordolo non c'e' (fuori da linee_x) resta l'omografia pura
        for x in xs_tutti:
            if lx0 <= x <= lx1:
                continue
            for l in linee:
                md_, qd_ = l["dopo"]
                ctrl.append([x, md_ * x + qd_]); val.append([0.0, 0.0])
        # sopra la prima linea (recinzione e sfondo) resta l'omografia pura
        md, qd = linee[0]["dopo"]
        fascia = cfg.get("fascia", 60)
        for x in xs_tutti:
            ctrl.append([x, md * x + qd - fascia]); val.append([0.0, 0.0])
        for y in np.arange(y0 - 200, y1, 200.0):
            for x in np.arange(x0 - 200, x1 + 201, 250.0):
                if y < md * x + qd - 150:
                    ctrl.append([x, y]); val.append([0.0, 0.0])
        f = tps(np.array(ctrl), np.array(val))
        # la deformazione e' morbida: si calcola su una griglia rada e poi si interpola (molto piu' veloce)
        passo = 8
        gxs, gys = np.meshgrid(np.arange(x0, x1 + passo, passo, dtype=np.float64), np.arange(y0, y1 + passo, passo, dtype=np.float64))
        d = f(np.c_[gxs.ravel(), gys.ravel()]).reshape(gxs.shape + (2,)).astype(np.float32)
        dx = cv2.resize(d[..., 0], (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC)
        dy = cv2.resize(d[..., 1], (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC)
        src = src + np.c_[dx.ravel(), dy.ravel()]
        print("correzione terreno: %d punti di controllo, spostamento max %.1f px" % (len(ctrl), np.abs(val).max()))
    mx = src[:, 0].reshape(gx.shape).astype(np.float32)
    my = src[:, 1].reshape(gx.shape).astype(np.float32)
    fuori = int(((mx < 0) | (my < 0) | (mx > prima.shape[1] - 1) | (my > prima.shape[0] - 1)).sum())
    if fuori:
        print("ATTENZIONE: %d pixel del ritaglio cadono fuori dalla foto PRIMA" % fuori)
    A = cv2.remap(prima, mx, my, cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    B = dopo[y0:y1, x0:x1].copy()

    # 3) tono: avvicina il PRIMA al DOPO (Lab) sulle zone indicate, o su tutta l'immagine
    k = float(cfg.get("tono", 0))
    if k > 0:
        la = cv2.cvtColor(A, cv2.COLOR_BGR2LAB).astype(np.float32)
        lb = cv2.cvtColor(B, cv2.COLOR_BGR2LAB).astype(np.float32)
        maschera = np.ones(A.shape[:2], bool)
        if linee and cfg.get("tono_sotto_prima_linea", True):
            md, qd = linee[0]["dopo"]
            maschera = gy > md * gx + qd + 10
            if "tono_x_max" in cfg:
                maschera &= gx < cfg["tono_x_max"]
            if "tono_x_min" in cfg:
                maschera &= gx > cfg["tono_x_min"]
        ma, sa = la[maschera].mean(axis=0), la[maschera].std(axis=0)
        mb, sb = lb[maschera].mean(axis=0), lb[maschera].std(axis=0)
        for c in range(3):
            la[..., c] = (la[..., c] - ma[c]) * (sb[c] / sa[c]) ** k + ma[c] + (mb[c] - ma[c]) * k
        A = cv2.cvtColor(np.clip(la, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)

    # 4) esportazione per il sito
    out = cfg["uscita"]
    cartella = os.path.join(SITO, "assets", "img")
    for nome, img in ((out["prima"], A), (out["dopo"], B)):
        im = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        W, Hh = im.size
        for w in out["larghezze"]:
            r = im.resize((w, round(Hh * w / W)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=0.7, percent=40, threshold=2))
            r.save(os.path.join(cartella, "%s-%d.webp" % (nome, w)), "WEBP", quality=(78 if w <= 900 else 72), method=6)
        r = im.resize((640, round(Hh * 640 / W)), Image.LANCZOS)
        r.save(os.path.join(cartella, "%s-640.jpg" % nome), "JPEG", quality=76, optimize=True, progressive=True)
        print("esportato", nome, im.size)
    if len(sys.argv) > 2:
        # strisce alterne PRIMA/DOPO: le linee fisse devono continuare senza salti
        S = B.copy()
        passo = 120
        for x in range(0, A.shape[1], 2 * passo):
            S[:, x:x + passo] = A[:, x:x + passo]
        cv2.imwrite(sys.argv[2], cv2.resize(S, (1200, round(S.shape[0] * 1200 / S.shape[1]))))
        print("controllo a strisce:", sys.argv[2])


if __name__ == "__main__":
    main()
