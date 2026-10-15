#!/usr/bin/env python3
"""
Controllo dei testi del sito: segnala parole da evitare e emoji in tutto quello che legge una persona
(testo, alt, aria-label, title, didascalie e messaggi precompilati di WhatsApp).

Uso, dalla radice del repository:
    python3 tools/build/controlla_testi.py index.html privacy.html 404.html

Regole dei testi di Astra Gardens: stile Paolo Borzacchiello, parole che nutrono, frasi in positivo;
niente negazioni, niente prezzi, niente garanzie, niente emoji. Il risultato giusto e' «segnalazioni: 0».
I blocchi con l'attributo data-legale (informativa privacy, testo scritto con la verifica legale) o
data-testo-approvato (frase dettata parola per parola, es. la 404 del 15/10/2026) si saltano: li' le
negazioni servono e il testo va tenuto com'e'.
"""
import re, html, sys, json
from html.parser import HTMLParser
VUOTI = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
class T(HTMLParser):
    def __init__(self):
        super().__init__(); self.out = []; self.skip = 0; self.legale = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.legale and tag not in VUOTI: self.legale[-1] += 1
        if "data-legale" in a or "data-testo-approvato" in a: self.legale.append(1)
        if self.legale: return
        if tag in ("script", "style", "svg"): self.skip += 1
        for k in ("alt", "aria-label", "title", "content", "data-didascalia"):
            if a.get(k) and not a[k].startswith(("http", "assets", "#", "width=", "IE=")): self.out.append("[%s] %s" % (k, a[k]))
        if tag == "a" and a.get("href", "").startswith("https://wa.me/"):
            from urllib.parse import unquote
            self.out.append("[wa] " + unquote(a["href"].split("text=", 1)[1]))
    def handle_endtag(self, tag):
        if self.legale:
            self.legale[-1] -= 1
            if not self.legale[-1]: self.legale.pop()
            return
        if tag in ("script", "style", "svg"): self.skip -= 1
    def handle_data(self, d):
        if not self.skip and not self.legale and d.strip(): self.out.append(d.strip())
BAN = r"\b(non|né|senza|niente|nessun[oa]?|mai|meno|problem\w*|difficil\w*|prov(?!inc)\w+|costo|costi|cost(?!ru)\w*|error\w*|guast\w*|sper\w+|disturb\w*|prezz\w*|tariff\w*|€|garanti\w*|anni di esperienza|come promesso)\b"
tot = 0
for f in sys.argv[1:]:
    p = T(); p.feed(open(f, encoding="utf-8").read())
    for line in p.out:
        for m in re.finditer(BAN, line, flags=re.I):
            tot += 1
            print("%s: «%s» -> %s" % (f.split("/")[-1], m.group(0), line[:160]))
    emo = [l for l in p.out if re.search("[\U0001F300-\U0001FAFF☀-➿]", l)]
    for l in emo: print(f, "EMOJI:", l[:100]); tot += 1
print("segnalazioni:", tot)
