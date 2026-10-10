#!/usr/bin/env python3
"""
Genera le pagine del sito Astra Gardens: index.html, privacy.html, 404.html, sitemap.xml, robots.txt,
site.webmanifest, CNAME e il file di verifica di Google Search Console.

Uso, da qualsiasi cartella (basta Python 3, nessuna libreria esterna):
    python3 tools/build/build_site.py

Scrive SOLO quei file nella radice del repository e non cancella mai nulla. I testi, i servizi, la
galleria e i collegamenti stanno qui sotto; stile e comportamento in assets/css/style.css e
assets/js/main.js. Le misure delle immagini si leggono dai file in assets/img (nome-LARGHEZZA.webp
più nome-640.jpg di riserva): dopo aver rifatto un'immagine (tools/prima-dopo) o un video
(tools/video) basta rilanciare questo script.
Ogni volta che cambiano stile o script si alza VERSIONE, così i telefoni scaricano i file nuovi.
Controllo dei testi (parole da evitare, emoji):
    python3 tools/build/controlla_testi.py index.html privacy.html 404.html
"""
import json, os, re, html
from urllib.parse import quote

QUI = os.path.dirname(os.path.abspath(__file__))
SITO = os.path.abspath(os.path.join(QUI, "..", ".."))


def misura_webp(percorso):
    """Larghezza e altezza di un WebP lette dall'intestazione del file (lossy, lossless o esteso)."""
    with open(percorso, "rb") as f:
        d = f.read(40)
    if d[:4] != b"RIFF" or d[8:12] != b"WEBP":
        raise SystemExit("non e' un WebP: " + percorso)
    tipo = d[12:16]
    if tipo == b"VP8 ":
        return int.from_bytes(d[26:28], "little") & 0x3FFF, int.from_bytes(d[28:30], "little") & 0x3FFF
    if tipo == b"VP8L":
        b = int.from_bytes(d[21:25], "little")
        return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    if tipo == b"VP8X":
        return int.from_bytes(d[24:27], "little") + 1, int.from_bytes(d[27:30], "little") + 1
    raise SystemExit("WebP sconosciuto: " + percorso)


def leggi_immagini():
    """{nome: {w, h, webp: [larghezze], jpg: larghezza}} dai file in assets/img."""
    cartella = os.path.join(SITO, "assets", "img")
    gruppi = {}
    for f in os.listdir(cartella):
        m = re.match(r"^(.+)-(\d+)\.(webp|jpg)$", f)
        if m:
            gruppi.setdefault(m.group(1), {"webp": [], "jpg": []})[m.group(3)].append(int(m.group(2)))
    man = {}
    for nome, g in gruppi.items():
        if not g["webp"]:
            continue
        g["webp"].sort()
        w, h = misura_webp(os.path.join(cartella, "%s-%d.webp" % (nome, g["webp"][-1])))
        man[nome] = {"w": w, "h": h, "webp": g["webp"],
                     "jpg": 640 if 640 in g["jpg"] else (min(g["jpg"]) if g["jpg"] else None)}
    return man


MAN = leggi_immagini()
BASE = "https://astragardens.it/"
TEL = "+39 334 186 5764"
TEL_LINK = "+393341865764"
WA_NUM = "393341865764"
EMAIL = "astragiardini@gmail.com"
IG = "https://www.instagram.com/astra.gardens/"
FB = "https://www.facebook.com/profile.php?id=61587199321572"
PIVA = "04489190985"
VERSIONE = "20261006b"
VERIFICA_GOOGLE = "googledb139c8fc3e627f5.html"


def e(t):
    return html.escape(t, quote=True)


def wa(msg):
    return "https://wa.me/%s?text=%s" % (WA_NUM, quote("Buongiorno, vi scrivo dal sito Astra Gardens: " + msg, safe=""))


WA_GENERALE = wa("vorrei un sopralluogo per il mio giardino.")


def picture(nome, alt, sizes, classe="", loading="lazy", priorita=None):
    m = MAN[nome]
    webp = ", ".join("assets/img/%s-%d.webp %dw" % (nome, w, w) for w in m["webp"])
    jpg = "assets/img/%s-%d.jpg" % (nome, m["jpg"])
    extra = ' fetchpriority="%s"' % priorita if priorita else ""
    cl = ' class="%s"' % classe if classe else ""
    return ('<picture><source type="image/webp" srcset="%s" sizes="%s">'
            '<img src="%s" alt="%s" width="%d" height="%d" loading="%s" decoding="async"%s%s></picture>'
            % (webp, sizes, jpg, e(alt), m["w"], m["h"], loading, extra, cl))


def grande(nome):
    m = MAN[nome]
    return "assets/img/%s-%d.webp" % (nome, max(m["webp"]))


# Regola fissa di Francesco (06/10/2026, ~/.claude/CLAUDE.md §65): i video si pubblicano solo alla massima
# qualità e solo dagli originali. Una clip di cui manca l'originale ("sorgente": null in tools/video/video.json)
# non ha il file in assets/video/clip/: al suo posto la pagina mostra questa foto, finché l'originale arriva.
RIPIEGO_CLIP = {
    "tree-climbing": ("srv-alberi", "Giardiniere in tree climbing tra i rami di una grande magnolia"),
    "abbattimento": ("srv-abbattimenti", "Abbattimento controllato: il tronco viene ridotto a sezioni dall'alto"),
    "movimento-terra": ("srv-movimento-terra", "Miniescavatore al lavoro e furgone Astra Gardens sullo sfondo"),
    "robot": ("lav-zolle-siepe", "Prato rigoglioso lungo una siepe curata."),
    "fioriture": ("lav-prato-fiorito", "Prato e aiuole fiorite in primavera."),
}


def ha_video(nome):
    return os.path.exists(os.path.join(SITO, "assets", "video", "clip", nome + ".mp4"))


def clip(nome, alt, classe="", sizes="(min-width: 960px) 360px, (min-width: 640px) 45vw, 124px"):
    """Clip breve, muta, in loop, senza comandi, 1080x1920: si scarica e gira solo quando entra nello schermo
    (preload="none" + main.js). Poster sempre presente. Senza il file video: la foto di RIPIEGO_CLIP."""
    cl = (" " + classe) if classe else ""
    if not ha_video(nome):
        foto, alt_foto = RIPIEGO_CLIP[nome]
        return '<div class="clip clip--foto%s">%s</div>' % (cl, picture(foto, alt_foto.rstrip("."), sizes))
    b = "assets/video/clip/" + nome
    return ('<div class="clip%s" data-clip>'
            '<picture><source type="image/webp" srcset="%s-poster.webp"><img src="%s-poster.jpg" alt="%s" width="1080" height="1920" loading="lazy" decoding="async"></picture>'
            # niente attributo poster sul video: il browser lo scaricherebbe subito anche con preload="none";
            # l'immagine d'attesa e' gia' la <picture> qui sopra, che si carica solo vicino allo schermo
            '<video muted loop playsinline preload="none" aria-hidden="true" tabindex="-1">'
            '<source src="%s.mp4" type="video/mp4"></video>'
            '</div>') % (cl, b, b, e(alt), b)


def proporzione(nome):
    return MAN[nome]["w"] / MAN[nome]["h"]


def confronto(oggi, progetto, alt_oggi, alt_progetto, titolo, sx="Oggi", dx="Progetto",
              nota="Immagine di progetto · render realizzato con la nostra IA",
              sizes="92vw", classe="", mostra_titolo=True, icona_nota=""):
    """Confronto con cursore da trascinare (mouse, dito e frecce della tastiera).
    Regola fissa di Francesco: ogni prima e dopo del sito si mostra cosi', mai solo affiancato.
    Il riquadro prende le proporzioni della coppia (--ratio): la composizione si vede intera,
    mai un ritaglio fisso."""
    a, b = MAN[oggi], MAN[progetto]
    if (a["w"], a["h"]) != (b["w"], b["h"]):
        raise SystemExit("confronto con misure diverse: %s %dx%d, %s %dx%d" % (oggi, a["w"], a["h"], progetto, b["w"], b["h"]))
    return """      <figure class="confronto-box rivela%s" style="--ratio: %d / %d">
        <div class="confronto" data-confronto data-dx="%s">
          %s
          <div class="confronto__dopo">%s</div>
          <input class="confronto__cursore" type="range" min="0" max="100" value="50" step="1" aria-label="Confronto: %s. Sposta per vedere: %s">
          <span class="confronto__linea" aria-hidden="true"><span class="confronto__maniglia">%s%s</span></span>
          <span class="confronto__etichetta confronto__etichetta--sx" aria-hidden="true">%s</span>
          <span class="confronto__etichetta confronto__etichetta--dx" aria-hidden="true">%s</span>
        </div>
        <figcaption>%s<span class="confronto__nota">%s%s</span></figcaption>
      </figure>""" % ((" " + classe) if classe else "", a["w"], a["h"], e(dx),
                       picture(oggi, alt_oggi, sizes), picture(progetto, alt_progetto, sizes),
                       e(titolo), e(dx.lower()), icona("i-sx"), icona("i-dx"), e(sx), e(dx),
                       ('<span class="confronto__titolo">%s</span>' % e(titolo)) if mostra_titolo else "",
                       icona(icona_nota) if icona_nota else "", e(nota))


def icona(id_, classe="icona"):
    return '<svg class="%s" aria-hidden="true" focusable="false"><use href="#%s" xlink:href="#%s"></use></svg>' % (classe, id_, id_)


SPRITE = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="display:none">
  <symbol id="i-wa" viewBox="0 0 24 24"><path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></symbol>
  <symbol id="i-tel" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></symbol>
  <symbol id="i-mail" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></g></symbol>
  <symbol id="i-ig" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2.6" y="2.6" width="18.8" height="18.8" rx="5.4"/><circle cx="12" cy="12" r="4.3"/></g><circle cx="17.5" cy="6.5" r="1.25" fill="currentColor"/></symbol>
  <symbol id="i-fb" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></symbol>
  <symbol id="i-check" viewBox="0 0 24 24"><polyline fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" points="20 6 9 17 4 12"/></symbol>
  <symbol id="i-menu" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></g></symbol>
  <symbol id="i-x" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></g></symbol>
  <symbol id="i-dx" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></g></symbol>
  <symbol id="i-sx" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></g></symbol>
  <symbol id="i-scudo" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="8.5 12 11 14.5 15.5 10"/></g></symbol>
  <symbol id="i-doc" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></g></symbol>
  <symbol id="i-perito" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11.2v4.6c0 1.6 2.7 3.2 6 3.2s6-1.6 6-3.2v-4.6"/><path d="M22 9v5.5"/></g></symbol>
  <symbol id="i-mezzi" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="1.5" y="6" width="13" height="10" rx="1.2"/><path d="M14.5 9.5h4l3 3.2V16h-7z"/><circle cx="6" cy="18" r="2.2"/><circle cx="17.5" cy="18" r="2.2"/></g></symbol>
  <symbol id="i-foglia" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 19.5C4.5 11 9.8 4.7 20 3.8c-.8 10.3-7.2 15.7-15.5 15.7z"/><path d="M4.5 19.5c3.2-4.6 6.6-7.6 10.6-10.2"/></g></symbol>
  <symbol id="i-chat" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></symbol>
</svg>"""

SERVIZI_VIDEO = [
    ("manutenzione", "Manutenzione del giardino",
     "Prato, siepi, aiuole e pulizia, anche nei giardini di pregio: su chiamata o con un contratto annuale, il tuo giardino resta curato in ogni stagione.",
     "vorrei informazioni sulla manutenzione del giardino.",
     "Giardino di pregio con alberi dalle foglie arancio e rose in fiore"),
    ("tree-climbing", "Alberi alti e tree climbing",
     "Saliamo sulla pianta con funi e imbrago, oppure con la piattaforma aerea, e potiamo con tagli puliti e mirati.",
     "vorrei far potare un albero ad alto fusto.",
     "Giardiniere in tree climbing tra i rami di un grande cedro"),
    ("abbattimento", "Abbattimenti controllati",
     "Smontiamo l'albero pezzo per pezzo e caliamo i rami con le funi, per proteggere tutto ciò che c'è intorno.",
     "vorrei informazioni per l'abbattimento di un albero.",
     "Abbattimento controllato: una sezione del tronco arriva a terra"),
    ("cippatura", "Cippatura dei rami",
     "Con il cippatore trituriamo rami e potature direttamente in cantiere: il verde tagliato diventa cippato e lo spazio torna subito in ordine.",
     "vorrei informazioni per la cippatura dei rami.",
     "Cippatore al lavoro: il cippato esce dallo scivolo rosso"),
    ("movimento-terra", "Giardini nuovi e movimento terra",
     "Scavi, livellamenti e rimozione delle ceppaie con il miniescavatore, poi piante, prato e finiture: dal terreno al giardino finito.",
     "vorrei realizzare un giardino nuovo.",
     "Miniescavatore al lavoro e furgone Astra Gardens sullo sfondo"),
    ("antizanzare", "Impianti antizanzare",
     "Nebulizzazione lungo siepi e perimetro del giardino: vivi i tuoi spazi esterni con più serenità, anche nelle sere d'estate.",
     "vorrei informazioni su un impianto antizanzare.",
     "Impianto antizanzare: la nebulizzazione lungo la siepe"),
]

SERVIZI_FOTO = [
    ("srv-siepi", "Potatura di siepi e arbusti",
     "Siepi compatte e arbusti in forma, potati nel periodo giusto per ogni pianta.",
     "vorrei far potare siepi e arbusti.",
     "Siepe potata con cura lungo il prato"),
    ("srv-ulivi", "Ulivi",
     "Potatura degli ulivi, anche ornamentali nella forma a pon pon: una chioma ariosa, luminosa e bella da vedere.",
     "vorrei far potare i miei ulivi.",
     "Ulivo ornamentale potato nella forma a pon pon"),
    ("srv-prato", "Prato in zolle e semina",
     "Prepariamo e livelliamo il terreno, poi posiamo le zolle o seminiamo, per un prato verde e uniforme.",
     "vorrei un prato nuovo, in zolle o seminato.",
     "Prato in zolle appena posato tra bossi e vialetti"),
    ("srv-irrigazione", "Impianti di irrigazione",
     "Progettiamo e posiamo l'impianto più adatto al tuo giardino. Con la catenaria scaviamo le tracce anche negli spazi stretti.",
     "vorrei informazioni per un impianto di irrigazione.",
     "Scavo stretto e preciso con la catenaria"),
    ("srv-robot", "Robot rasaerba",
     "Installiamo e regoliamo il robot rasaerba sul tuo prato: l'erba resta corta e ordinata tutta la settimana.",
     "vorrei informazioni su un robot rasaerba.",
     "Robot rasaerba sul prato tra gli ulivi"),
    ("srv-corten", "Bordure in corten",
     "Bordure in acciaio corten sagomate su misura direttamente in giardino: linee pulite tra prato, ghiaia e aiuole.",
     "vorrei informazioni sulle bordure in corten.",
     "Bordura circolare in corten sagomata su misura intorno a un albero"),
    ("srv-sintetico", "Cura dell'erba sintetica",
     "Pulizia e spazzolatura del prato sintetico, per un manto ordinato, morbido e pulito.",
     "vorrei informazioni per la cura dell'erba sintetica.",
     "Prato sintetico con bordura in corten davanti a casa"),
]
SERVIZI = SERVIZI_VIDEO + SERVIZI_FOTO

# Griglia regolare (riquadri 4:5): 12 elementi = righe piene sia a 2 sia a 3 colonne.
# Il quarto campo e' il punto della foto da tenere al centro quando il riquadro la ritaglia.
GALLERIA = [
    ("foto", "lav-ulivi-rose", "Ulivi, rose e un prato curato.", "50% 55%"),
    ("clip", "robot", "Robot rasaerba al lavoro tra gli ulivi.", None),
    ("foto", "lav-cedro", "Tree climbing su un grande cedro.", None),
    ("foto", "lav-posa-zolle", "Posa del prato in zolle: a sinistra il terreno preparato, a destra il prato appena steso.", "22% 50%"),
    ("foto", "lav-chioma", "Ricostruzione della chioma di un albero capitozzato.", None),
    ("foto", "lav-ghiaia-pergola", "Ghiaia bianca, prato e pergola: un giardino facile da vivere.", None),
    ("clip", "fioriture", "Messa a dimora di nuove fioriture.", None),
    ("foto", "lav-piattaforma", "Lavori in quota con la piattaforma aerea.", "50% 50%"),
    ("foto", "lav-ulivo-ponpon", "Ulivo ornamentale a pon pon, appena potato.", None),
    ("foto", "lav-corten-ghiaia", "Bordura in corten tra ghiaia, piante e prato sintetico.", None),
    ("foto", "lav-aiuola-ombra", "Aiuola per una zona d'ombra, con pacciamatura e bordo netto.", None),
    ("clip", "irrigazione", "Irrigazione automatica in funzione.", None),
]

COMUNI = ["Flero", "Brescia", "Castel Mella", "Poncarale", "Roncadelle", "San Zeno Naviglio", "Borgosatollo",
          "Montirone", "Capriano del Colle", "Castenedolo", "Bagnolo Mella", "Azzano Mella", "Torbole Casaglia",
          "Gussago", "Cellatica"]

TITOLO = "Giardiniere a Flero e Brescia sud | Astra Gardens"
DESCRIZIONE = ("Giardinieri a Flero e nel sud di Brescia: manutenzione, potature, tree climbing, prato in zolle "
               "e irrigazione. Scrivici su WhatsApp per un sopralluogo.")


def jsonld():
    dati = {
        "@context": "https://schema.org",
        "@type": "HomeAndConstructionBusiness",
        "@id": BASE + "#azienda",
        "name": "Astra Gardens",
        "legalName": "Astra Gardens di Francesco Guizzardi",
        "description": "Impresa di giardinaggio e cura del verde a Flero (BS), nata nel 2025 da un gruppo di periti "
                       "agrari e laureati in agraria: manutenzione di giardini, potature, tree climbing, abbattimenti "
                       "controllati, cippatura, prato in zolle, irrigazione, impianti antizanzare, progetti con render e "
                       "realizzazione di giardini per privati, condomini e aziende del sud di Brescia.",
        "url": BASE,
        "logo": BASE + "assets/img/logo-quadrato-512.png",
        "image": BASE + "assets/img/og-astra-gardens.jpg",
        "telephone": TEL,
        "email": EMAIL,
        "vatID": "IT" + PIVA,
        "foundingDate": "2025",
        "founder": {"@type": "Person", "name": "Francesco Guizzardi"},
        "address": {"@type": "PostalAddress", "addressLocality": "Flero", "postalCode": "25020",
                    "addressRegion": "BS", "addressCountry": "IT"},
        "areaServed": [{"@type": "City", "name": c} for c in COMUNI],
        "sameAs": [IG, FB],
        "knowsAbout": [s[1] for s in SERVIZI],
        "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": "Servizi per il verde",
            "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s[1], "description": s[2]}}
                                for s in SERVIZI],
        },
    }
    return json.dumps(dati, ensure_ascii=False, indent=1)


def testa(titolo, descrizione, percorso, extra=""):
    url = BASE + percorso
    return """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>%(titolo)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(url)s">
<meta name="theme-color" content="#114232">
<meta name="format-detection" content="telephone=no">
<meta property="og:type" content="website">
<meta property="og:locale" content="it_IT">
<meta property="og:site_name" content="Astra Gardens">
<meta property="og:title" content="%(titolo)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(url)s">
<meta property="og:image" content="%(base)sassets/img/og-astra-gardens.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Astra Gardens, giardinieri a Flero e nel sud di Brescia">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="assets/img/favicon-32.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="site.webmanifest">
<link rel="preload" href="assets/fonts/atkinson-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/fraunces-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/css/style.css?v=%(v)s">
<script>document.documentElement.className += " js";</script>
%(extra)s</head>
""" % {"titolo": e(titolo), "desc": e(descrizione), "url": url, "base": BASE, "v": VERSIONE, "extra": extra}


def testata(home=True):
    p = "" if home else "./"
    return """<a class="salta" href="#contenuto">Vai al contenuto</a>
<header class="testata">
  <div class="contenitore testata__riga">
    <a class="marchio" href="%(p)s#inizio" aria-label="Astra Gardens, torna all'inizio">
      <picture><source type="image/webp" srcset="assets/img/logo-verde-240.webp 240w, assets/img/logo-verde-480.webp 480w" sizes="196px"><img src="assets/img/logo-verde-480.png" alt="Astra Gardens" width="480" height="98"></picture>
    </a>
    <nav class="menu" aria-label="Menu principale">
      <a href="%(p)s#progetto">Progetto</a>
      <a href="%(p)s#servizi">Servizi</a>
      <a href="%(p)s#come-lavoriamo">Come lavoriamo</a>
      <a href="%(p)s#lavori">Lavori</a>
      <a href="%(p)s#condomini-aziende">Condomini</a>
      <a href="%(p)s#contatti">Contatti</a>
    </nav>
    <a class="btn btn--wa testata__wa" href="%(wa)s" target="_blank" rel="noopener">%(icwa)s<span>Scrivici su WhatsApp</span></a>
    <a class="testata__wa-tondo" href="%(wa)s" target="_blank" rel="noopener" aria-label="Scrivici su WhatsApp">%(icwa)s</a>
    <button class="apri-menu" type="button" aria-expanded="false" aria-controls="menu-telefono">%(icmenu)s<span>Menu</span></button>
  </div>
</header>
<div class="pannello" id="menu-telefono" hidden>
  <div class="pannello__testa">
    <img src="assets/img/logo-bianco-480.png" alt="Astra Gardens" width="480" height="98">
    <button class="chiudi-menu" type="button">%(icx)s<span>Chiudi</span></button>
  </div>
  <nav aria-label="Menu">
    <a href="%(p)s#progetto">Progetto e render</a>
    <a href="%(p)s#servizi">Servizi</a>
    <a href="%(p)s#come-lavoriamo">Come lavoriamo</a>
    <a href="%(p)s#lavori">Lavori</a>
    <a href="%(p)s#condomini-aziende">Condomini e aziende</a>
    <a href="%(p)s#zone">Zone servite</a>
    <a href="%(p)s#contatti">Contatti</a>
  </nav>
  <a class="btn btn--wa btn--largo" href="%(wa)s" target="_blank" rel="noopener">%(icwa)s<span>Scrivici su WhatsApp</span></a>
  <p class="pannello__nota">Flero (BS) e sud di Brescia</p>
</div>
""" % {"p": p, "wa": WA_GENERALE, "icwa": icona("i-wa"), "icmenu": icona("i-menu"), "icx": icona("i-x")}


def piede(home=True):
    p = "" if home else "./"
    return """<footer class="piede">
  <div class="contenitore">
    <div class="piede__alto">
      <div>
        <img src="assets/img/logo-bianco-480.png" alt="Astra Gardens" width="480" height="98" loading="lazy">
        <p class="piede__motto">Pensato con la testa, realizzato con le mani.</p>
      </div>
      <nav aria-label="Collegamenti">
        <ul>
          <li><a href="%(p)s#servizi">Servizi</a></li>
          <li><a href="%(p)s#lavori">Lavori</a></li>
          <li><a href="%(p)s#contatti">Contatti</a></li>
          <li><a href="privacy.html">Privacy</a></li>
          <li><a href="%(ig)s" target="_blank" rel="noopener">Instagram</a></li>
          <li><a href="%(fb)s" target="_blank" rel="noopener">Facebook</a></li>
        </ul>
      </nav>
    </div>
    <div class="piede__basso">
      <p><span class="intero">Astra Gardens di Francesco Guizzardi ·</span> <span class="intero">Flero (BS) ·</span> <span class="intero">P.IVA %(piva)s</span></p>
      <p><span class="intero">© <span id="anno">2026</span> Astra Gardens ·</span> <span class="intero">Zero cookie, zero tracciamento</span></p>
    </div>
  </div>
</footer>
""" % {"p": p, "ig": IG, "fb": FB, "piva": PIVA}


RENDER = ("render-aiuola-progetto", "render-prato-progetto")


def colonne_render():
    """Sul computer i due render stanno affiancati alla stessa altezza: colonne proporzionali."""
    return "--colonne: " + " ".join("minmax(0, %.4ffr)" % proporzione(n) for n in RENDER)


def sizes_render(nome):
    quota = proporzione(nome) / sum(proporzione(n) for n in RENDER)
    return "(min-width: 1200px) %dpx, (min-width: 900px) %dvw, 92vw" % (round(1108 * quota), round(100 * quota))


def index():
    video_html = []
    for nome, titolo, testo, msg, alt in SERVIZI_VIDEO:
        video_html.append("""      <li class="servizio servizio--video rivela">
        %s
        <div class="servizio__testo">
          <h3>%s</h3>
          <p>%s</p>
        </div>
        <a class="link-wa servizio__wa" href="%s" target="_blank" rel="noopener" aria-label="Chiedi su WhatsApp: %s">%s<span>Chiedi su WhatsApp</span></a>
      </li>""" % (clip(nome, alt), e(titolo), e(testo), wa(msg), e(titolo), icona("i-wa")))

    servizi_html = []
    for nome, titolo, testo, msg, alt in SERVIZI_FOTO:
        servizi_html.append("""      <li class="servizio rivela">
        %s
        <div class="servizio__testo">
          <h3>%s</h3>
          <p>%s</p>
        </div>
        <a class="link-wa servizio__wa" href="%s" target="_blank" rel="noopener" aria-label="Chiedi su WhatsApp: %s">%s<span>Chiedi su WhatsApp</span></a>
      </li>""" % (picture(nome, alt, "(min-width: 1200px) 270px, (min-width: 960px) 30vw, (min-width: 640px) 45vw, 120px"),
                  e(titolo), e(testo), wa(msg), e(titolo), icona("i-wa")))
    servizi_html.append("""      <li class="servizio servizio--invito rivela">
        <div class="servizio__testo">
          <img class="foglia" src="assets/img/foglia-salvia.png" alt="" width="216" height="158" loading="lazy">
          <h3>Hai in mente un altro lavoro?</h3>
          <p>Raccontacelo su WhatsApp, anche con una foto: troviamo insieme la soluzione giusta per il tuo verde.</p>
          <a class="btn btn--wa btn--largo" href="%s" target="_blank" rel="noopener">%s<span>Scrivici</span></a>
        </div>
      </li>""" % (wa("vorrei un consiglio per il mio giardino."), icona("i-wa")))

    galleria_html = []
    for tipo, nome, didascalia, fuoco in GALLERIA:
        if tipo == "clip" and not ha_video(nome):
            tipo, (nome, didascalia), fuoco = "foto", RIPIEGO_CLIP[nome], None
        alt = didascalia.rstrip(".")
        if tipo == "clip":
            galleria_html.append("""      <figure class="rivela galleria__clip">
        %s
        <figcaption>%s</figcaption>
      </figure>""" % (clip(nome, alt), e(didascalia)))
        else:
            galleria_html.append("""      <figure class="rivela">
        <button type="button" data-grande="%s" data-didascalia="%s" aria-label="Ingrandisci la foto: %s">%s</button>
        <figcaption>%s</figcaption>
      </figure>""" % (grande(nome), e(didascalia), e(alt),
                      picture(nome, alt, "(min-width: 960px) 360px, 46vw").replace(
                          "<img ", '<img style="object-position: %s" ' % fuoco if fuoco else "<img ", 1),
                      e(didascalia)))

    comuni_html = "\n".join('          <li%s>%s</li>' % (' class="casa"' if c == "Flero" else "", e(c)) for c in COMUNI)

    corpo = """<body>
%(sprite)s
%(testata)s
<main id="contenuto">

  <section class="hero" id="inizio" aria-labelledby="titolo-hero">
    <div class="hero__griglia">
      <div class="hero__media">
        <canvas class="hero__alone" width="27" height="48" aria-hidden="true"></canvas>
        <div class="hero__cornice">
          <picture><source type="image/webp" srcset="assets/video/astra-gardens-lavori-poster.webp"><img src="assets/video/astra-gardens-lavori-poster.jpg" alt="" width="1080" height="1920" fetchpriority="high"></picture>
          <video autoplay muted loop playsinline preload="auto" aria-hidden="true" tabindex="-1" poster="assets/video/astra-gardens-lavori-poster.webp">
            <source src="assets/video/astra-gardens-lavori.mp4" type="video/mp4">
          </video>
          <span class="hero__etichetta">Dai nostri cantieri</span>
        </div>
      </div>
      <div class="hero__testo contenitore">
        <h1 id="titolo-hero"><span class="occhiello">Giardinieri a Flero e nel sud di Brescia</span> Il tuo giardino sempre bello. <em>Ci pensiamo noi.</em></h1>
        <p class="hero__lead">Manutenzione, potature, alberi alti e giardini nuovi: scrivici su WhatsApp e veniamo a vedere il tuo verde.</p>
        <a class="btn btn--wa btn--largo" href="%(wa)s" target="_blank" rel="noopener">%(icwa)s<span>Scrivici su WhatsApp</span></a>
        <p class="hero__nota">%(icchat)s<span>Ti rispondiamo direttamente noi.</span></p>
      </div>
    </div>
  </section>

  <section class="fiducia" aria-label="Perché sceglierci">
    <div class="contenitore">
      <ul>
        <li class="rivela"><span class="tondo">%(icperito)s</span><div><strong>Periti e laureati in agraria</strong><span>Una squadra di tecnici che conosce le piante e le loro stagioni.</span></div></li>
        <li class="rivela" data-ritardo="1"><span class="tondo">%(icscudo)s</span><div><strong>Assicurazione RC</strong><span>Lavoriamo con assicurazione di responsabilità civile verso terzi.</span></div></li>
        <li class="rivela" data-ritardo="2"><span class="tondo">%(icmezzi)s</span><div><strong>Mezzi professionali</strong><span>Piattaforma aerea, attrezzatura da tree climbing, miniescavatore e catenaria.</span></div></li>
        <li class="rivela" data-ritardo="3"><span class="tondo">%(icdoc)s</span><div><strong>Preventivo scritto</strong><span>Chiaro e voce per voce, prima di iniziare.</span></div></li>
      </ul>
    </div>
  </section>

  <section class="sezione sezione--salvia progetto" id="progetto" aria-labelledby="titolo-progetto">
    <div class="contenitore">
      <header class="intestazione rivela">
        <p class="occhiello">Progetto e render IA</p>
        <h2 id="titolo-progetto">Vedi il tuo giardino prima di iniziare.</h2>
        <p class="lead">La progettazione nasce dalla nostra competenza e dalla conoscenza delle piante. Per il render e per un preventivo rapido usiamo le nostre intelligenze artificiali, i nostri agenti IA: così vedi subito il risultato finito.</p>
      </header>
      <p class="confronti__aiuto rivela"><span class="frecce" aria-hidden="true">%(icsx)s%(icdx)s</span><span>Trascina il cursore: a sinistra il giardino di oggi, a destra il progetto.</span></p>
      <div class="confronti" style="%(colonne_render)s">
%(confronto_aiuola)s
%(confronto_prato)s
      </div>
      <div class="progetto__piede rivela">
        <ul class="spunte spunte--chiare">
          <li>%(iccheck)s<span>Progetto pensato dalla nostra squadra di tecnici del verde</span></li>
          <li>%(iccheck)s<span>Render realistico del tuo giardino finito</span></li>
          <li>%(iccheck)s<span>Preventivo rapido, scritto e chiaro</span></li>
        </ul>
        <a class="btn btn--wa btn--largo" href="%(wa_render)s" target="_blank" rel="noopener">%(icwa)s<span>Chiedi il tuo render</span></a>
      </div>
    </div>
  </section>

  <section class="sezione" id="servizi" aria-labelledby="titolo-servizi">
    <div class="contenitore">
      <header class="intestazione rivela">
        <p class="occhiello">Servizi</p>
        <h2 id="titolo-servizi">Tutto il tuo verde, con un'unica squadra.</h2>
        <p class="lead">Dal taglio del prato agli alberi più alti, dalla siepe al giardino nuovo. Scegli il lavoro e scrivici: fissiamo insieme il sopralluogo.</p>
      </header>
      <ul class="servizi servizi--video">
%(servizi_video)s
      </ul>
      <h3 class="servizi__altri rivela">Altri servizi per il tuo verde</h3>
      <ul class="servizi">
%(servizi)s
      </ul>
    </div>
  </section>

  <section class="sezione sezione--bianca" id="chi-siamo" aria-labelledby="titolo-chi">
    <div class="contenitore duo">
      <div class="duo__foto rivela">
        %(foto_furgone)s
        <p class="bollo">Astra Gardens<small>Flero (BS) · dal 2025</small></p>
      </div>
      <div class="rivela" data-ritardo="1">
        <p class="occhiello">Chi siamo</p>
        <h2 id="titolo-chi">Una squadra giovane, nata a Flero.</h2>
        <p class="lead">Astra Gardens nasce nel 2025 da un gruppo di periti agrari e laureati in agraria. Siamo giovani, con una grande conoscenza tecnica del settore e una mentalità aperta, sempre rivolta al futuro.</p>
        <p>Nei giardini di Flero e del sud di Brescia portiamo competenza, mezzi professionali e tanta cura per i dettagli: ascoltiamo chi vive il giardino, scegliamo il momento giusto per ogni pianta e a fine lavoro lasciamo tutto pulito e in ordine.</p>
        <p class="citazione">«Pensato con la testa, realizzato con le mani.»</p>
        <ul class="mezzi" aria-label="I nostri mezzi">
          <li>%(icfoglia)sTree climbing</li>
          <li>%(icfoglia)sPiattaforma aerea</li>
          <li>%(icfoglia)sMiniescavatore</li>
          <li>%(icfoglia)sCatenaria</li>
          <li>%(icfoglia)sCippatore</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="sezione sezione--salvia" id="come-lavoriamo" aria-labelledby="titolo-come">
    <div class="contenitore">
      <header class="intestazione rivela">
        <p class="occhiello">Come lavoriamo</p>
        <h2 id="titolo-come">Quattro passi chiari, dal primo messaggio al lavoro finito.</h2>
      </header>
      <ol class="passi" role="list">
        <li class="passo rivela"><span class="passo__numero" aria-hidden="true">1</span><h3>Sopralluogo</h3><p>Ci scrivi su WhatsApp, fissiamo insieme un giorno e veniamo a vedere il tuo giardino. Ascoltiamo cosa desideri.</p></li>
        <li class="passo rivela" data-ritardo="1"><span class="passo__numero" aria-hidden="true">2</span><h3>Progetto e preventivo</h3><p>Ricevi un preventivo scritto, voce per voce, e quando serve anche il render del progetto: vedi subito il risultato finito.</p></li>
        <li class="passo rivela" data-ritardo="2"><span class="passo__numero" aria-hidden="true">3</span><h3>Cantiere organizzato</h3><p>Prima di partire ti mostriamo il piano di cantiere. Poi arriviamo nel giorno concordato con le persone e i mezzi giusti.</p></li>
        <li class="passo rivela" data-ritardo="3"><span class="passo__numero" aria-hidden="true">4</span><h3>Pulizia e foto finali</h3><p>A fine lavoro puliamo tutto e ti mandiamo le foto del lavoro finito: vedi il risultato anche da lontano.</p></li>
      </ol>
      <div class="cantiere">
        <div class="cantiere__testa rivela">
          <p class="occhiello">Il cantiere</p>
          <h3 class="cantiere__titolo">Il cantiere organizzato prima di partire.</h3>
          <p class="lead">Prima di iniziare ti mostriamo cosa facciamo, dove appoggiamo rami e materiali e dove si ferma il camion: così tutto è chiaro e ordinato fin dal primo giorno.</p>
        </div>
        <figure class="cantiere__piano rivela">
          <button type="button" data-grande="assets/img/piano-cantiere-1672.webp" data-didascalia="Esempio di piano di cantiere: gli alberi da abbattere, l'area per i rami e l'area di carico e scarico." aria-label="Ingrandisci l'esempio di piano di cantiere">
            %(piano)s
            <span class="cantiere__bollino">Esempio di piano di cantiere</span>
          </button>
          <figcaption>Alberi da abbattere, area per i rami e area di carico e scarico, segnati sulla vista dall'alto. Tocca l'immagine per vederla grande.</figcaption>
        </figure>
        <ul class="cantiere__media">
          <li class="rivela"><figure>%(gru)s<figcaption>Materiali consegnati con la gru, direttamente dove servono.</figcaption></figure></li>
          <li class="rivela" data-ritardo="1"><figure>%(clip_terra)s<figcaption>Terra nuova scaricata dal camion e stesa con il miniescavatore.</figcaption></figure></li>
          <li class="rivela" data-ritardo="2"><figure>%(terreno)s<figcaption>Terreno livellato e pronto per il nuovo prato.</figcaption></figure></li>
        </ul>
      </div>
      <div class="passi__invito rivela">
        <a class="btn btn--wa btn--largo" href="%(wa)s" target="_blank" rel="noopener" aria-label="Fissa il sopralluogo su WhatsApp">%(icwa)s<span>Fissa il sopralluogo</span></a>
      </div>
    </div>
  </section>

  <section class="sezione sezione--bianca" id="lavori" aria-labelledby="titolo-lavori">
    <div class="contenitore">
      <header class="intestazione rivela">
        <p class="occhiello">Lavori</p>
        <h2 id="titolo-lavori">Guarda i nostri lavori.</h2>
        <p class="lead">Foto e video veri dei nostri cantieri, girati dalla squadra. Tocca una foto per vederla grande.</p>
      </header>
      <div class="prima-dopo">
%(confronto_vero)s
        <div class="prima-dopo__testo rivela" data-ritardo="1">
          <h3>Da terreno spoglio a giardino finito.</h3>
          <p>Prato, aiuola pacciamata, un ulivo e nuove piante. Le due foto mostrano lo stesso angolo del giardino, prima e dopo il nostro lavoro.</p>
          <p class="confronti__aiuto"><span class="frecce" aria-hidden="true">%(icsx)s%(icdx)s</span><span>Trascina il cursore: a sinistra prima, a destra dopo.</span></p>
        </div>
      </div>
      <div class="galleria" data-galleria>
%(galleria)s
      </div>
      <p class="instagram-invito rivela">%(icig)s<span>Altre foto e video dai nostri cantieri sul profilo Instagram <a href="%(ig)s" target="_blank" rel="noopener">@astra.gardens</a></span></p>
    </div>
  </section>

  <section class="sezione sezione--verde" id="condomini-aziende" aria-labelledby="titolo-condomini">
    <div class="contenitore duo duo--inverso">
      <div class="duo__foto rivela">
        %(foto_condomini)s
      </div>
      <div class="rivela" data-ritardo="1">
        <p class="occhiello">Condomini e aziende</p>
        <h2 id="titolo-condomini">Il verde del tuo condominio o della tua azienda, sempre in ordine.</h2>
        <p class="lead">Per amministratori, condomini e aziende organizziamo la manutenzione programmata del verde, con un referente unico che segue ogni intervento.</p>
        <ul class="spunte">
          <li>%(iccheck)s<span>Manutenzione programmata del verde, tutto l'anno</span></li>
          <li>%(iccheck)s<span>Un referente unico per ogni richiesta</span></li>
          <li>%(iccheck)s<span>Alberi alti con piattaforma aerea e tree climbing</span></li>
          <li>%(iccheck)s<span>Cantiere segnalato e assicurazione RC verso terzi</span></li>
          <li>%(iccheck)s<span>Preventivo scritto e foto a fine intervento</span></li>
        </ul>
        <a class="btn btn--wa btn--largo" href="%(wa_cond)s" target="_blank" rel="noopener">%(icwa)s<span>Chiedi un sopralluogo</span></a>
      </div>
    </div>
  </section>

  <section class="sezione" id="zone" aria-labelledby="titolo-zone">
    <div class="contenitore zone">
      <figure class="zone__foto rivela">
        %(foto_zone)s
        <figcaption>Brescia, il centro storico</figcaption>
      </figure>
      <div class="rivela" data-ritardo="1">
        <p class="occhiello">Zone servite</p>
        <h2 id="titolo-zone">Vicino a te: Flero, Brescia e dintorni.</h2>
        <p class="lead">Partiamo da Flero e lavoriamo in questi comuni:</p>
        <ul class="comuni">
%(comuni)s
        </ul>
        <p>Abiti in un comune vicino? Scrivici su WhatsApp e valutiamo insieme.</p>
      </div>
    </div>
  </section>

  <section class="sezione sezione--verde contatti" id="contatti" aria-labelledby="titolo-contatti">
    <div class="contenitore contatti__griglia">
      <div class="rivela">
        <p class="occhiello">Contatti</p>
        <h2 id="titolo-contatti">Parliamo del tuo giardino.</h2>
        <p class="lead">Il modo più facile è WhatsApp: scrivici due righe e, se vuoi, aggiungi qualche foto del tuo verde. Ti rispondiamo direttamente noi.</p>
        <a class="btn btn--wa btn--largo" href="%(wa)s" target="_blank" rel="noopener">%(icwa)s<span>Scrivici su WhatsApp</span></a>
      </div>
      <div class="recapiti rivela" data-ritardo="1">
        <a class="recapito recapito--wa" href="%(wa)s" target="_blank" rel="noopener"><span class="tondo">%(icwa)s</span><span><small>WhatsApp</small><strong>%(tel)s</strong></span></a>
        <a class="recapito" href="tel:%(tel_link)s"><span class="tondo">%(ictel)s</span><span><small>Telefono</small><strong>%(tel)s</strong></span></a>
        <a class="recapito" href="mailto:%(email)s"><span class="tondo">%(icmail)s</span><span><small>Email</small><strong>%(email_capo)s</strong></span></a>
        <a class="recapito" href="%(ig)s" target="_blank" rel="noopener"><span class="tondo">%(icig)s</span><span><small>Instagram</small><strong>@astra.gardens</strong></span></a>
        <a class="recapito" href="%(fb)s" target="_blank" rel="noopener"><span class="tondo">%(icfb)s</span><span><small>Facebook</small><strong>Astra Gardens</strong></span></a>
        <div class="recapito"><span class="tondo">%(icfoglia)s</span><span><small>Dove siamo</small><strong>Flero (BS) e sud di Brescia</strong></span></div>
      </div>
    </div>
  </section>

</main>
%(piede)s
<div class="barra-wa">
  <a class="btn btn--wa" href="%(wa)s" target="_blank" rel="noopener">%(icwa)s<span>Scrivici su WhatsApp</span></a>
</div>
<a class="wa-tondo" href="%(wa)s" target="_blank" rel="noopener" aria-label="Scrivici su WhatsApp">%(icwa)s</a>

<dialog class="lightbox" id="lightbox" aria-label="Foto ingrandita">
  <div class="lightbox__corpo" tabindex="-1" autofocus>
    <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" alt="">
    <div class="lightbox__piede">
      <p></p>
      <button type="button" data-azione="prima" aria-label="Foto precedente">%(icsx)s</button>
      <button type="button" data-azione="dopo" aria-label="Foto successiva">%(icdx)s</button>
      <button type="button" data-azione="chiudi" aria-label="Chiudi">%(icx)s</button>
    </div>
  </div>
</dialog>

<script type="application/ld+json">
%(jsonld)s
</script>
<script src="assets/js/main.js?v=%(v)s" defer></script>
</body>
</html>
""" % {
        "sprite": SPRITE, "testata": testata(True), "piede": piede(True),
        "wa": WA_GENERALE, "wa_cond": wa("vorrei un sopralluogo per il verde di un condominio o di un'azienda."),
        "icwa": icona("i-wa"), "icchat": icona("i-chat"), "icperito": icona("i-perito"), "icscudo": icona("i-scudo"),
        "icmezzi": icona("i-mezzi"), "icdoc": icona("i-doc"), "icfoglia": icona("i-foglia"), "iccheck": icona("i-check"),
        "icig": icona("i-ig"), "ictel": icona("i-tel"), "icmail": icona("i-mail"), "icsx": icona("i-sx"),
        "icdx": icona("i-dx"), "icx": icona("i-x"),
        "servizi": "\n".join(servizi_html), "servizi_video": "\n".join(video_html),
        "galleria": "\n".join(galleria_html), "comuni": comuni_html,
        "wa_render": wa("vorrei un progetto con render per il mio giardino."),
        "colonne_render": colonne_render(),
        "confronto_aiuola": confronto("render-aiuola-oggi", "render-aiuola-progetto",
                                      "Oggi: l'aiuola d'ingresso prima del progetto",
                                      "Progetto: aiuola con bordura in corten, graminacee, fioriture e luci",
                                      "Aiuola con bordura in corten", sizes=sizes_render("render-aiuola-progetto")),
        "confronto_prato": confronto("render-prato-oggi", "render-prato-progetto",
                                     "Oggi: il prato davanti a casa prima del progetto",
                                     "Progetto: prato nuovo con bordura in corten e fioriture",
                                     "Prato nuovo con bordura in corten", sizes=sizes_render("render-prato-progetto")),
        "piano": picture("piano-cantiere", "Vista dall'alto del cantiere con i due cedri da abbattere, l'area di stoccaggio dei rami e l'area di carico e scarico",
                         "(min-width: 1200px) 680px, (min-width: 960px) 56vw, 92vw"),
        "gru": picture("consegna-gru", "Camion con gru che scarica un big bag di materiale vicino al giardino",
                       "(min-width: 720px) 360px, 120px"),
        "clip_terra": clip("cantiere-terra", "Camion che scarica la terra e miniescavatore che la stende"),
        "terreno": picture("lav-terreno-pronto", "Terreno livellato e pronto per il nuovo prato, con un grande cedro",
                           "(min-width: 720px) 360px, 120px"),
        "foto_furgone": picture("chi-siamo-furgone", "Furgone Astra Gardens con l'arcobaleno sullo sfondo",
                                "(min-width: 960px) 480px, 92vw"),
        "foto_condomini": picture("condomini-siepe", "Potatura di una siepe lungo la strada con il cantiere segnalato",
                                  "(min-width: 960px) 520px, 92vw"),
        "foto_zone": ('<picture>'
                      '<source media="(min-width: 960px)" type="image/webp" srcset="assets/img/zone-brescia-alta-600.webp 600w, assets/img/zone-brescia-alta-1080.webp 1080w" sizes="560px">'
                      '<source media="(min-width: 960px)" srcset="assets/img/zone-brescia-alta-640.jpg 640w" sizes="560px">'
                      '<source type="image/webp" srcset="assets/img/zone-brescia-640.webp 640w, assets/img/zone-brescia-1080.webp 1080w" sizes="92vw">'
                      '<img src="assets/img/zone-brescia-640.jpg" alt="Tetti del centro storico di Brescia con la cupola del Duomo" width="1080" height="810" loading="lazy" decoding="async">'
                      '</picture>'),
        "confronto_vero": confronto("lavoro-prima", "lavoro-dopo",
                                    "Prima: terreno spoglio e secco dietro la recinzione",
                                    "Dopo: aiuola pacciamata con nuove piante, prato e recinzione in ordine",
                                    "Da terreno spoglio a giardino finito", sx="Prima", dx="Dopo",
                                    nota="Lavoro realizzato · foto vere",
                                    sizes="(min-width: 1200px) 660px, (min-width: 960px) 56vw, 92vw",
                                    classe="confronto-box--vero", mostra_titolo=False, icona_nota="i-check"),
        "ig": IG, "fb": FB, "icfb": icona("i-fb"), "tel": TEL, "tel_link": TEL_LINK, "email": EMAIL,
        "email_capo": EMAIL.replace("@", "<wbr>@"),
        "jsonld": jsonld(), "v": VERSIONE,
    }
    return testa(TITOLO, DESCRIZIONE, "") + corpo


def privacy():
    corpo = """<body>
%(sprite)s
%(testata)s
<main id="contenuto" class="pagina">
  <div class="contenitore">
    <a class="torna" href="./">%(icdx)s<span>Torna alla pagina principale</span></a>
    <h1>Privacy</h1>
    <p class="lead">Questo sito è una vetrina semplice: zero cookie, zero strumenti di analisi, zero pubblicità.</p>

    <h2>Titolare del trattamento</h2>
    <p>Astra Gardens di Francesco Guizzardi, Flero (BS), P.IVA %(piva)s.<br>Per qualsiasi richiesta sulla privacy: <a href="mailto:%(email)s">%(email)s</a>.</p>

    <h2>Cookie e tracciamento</h2>
    <p>Il sito usa zero cookie e zero sistemi di tracciamento. Caratteri, immagini e video arrivano tutti da questo stesso sito.</p>

    <h2>Ospitalità del sito</h2>
    <p>Il sito è ospitato da GitHub Pages (GitHub Inc.). Per la sicurezza del servizio GitHub può registrare dati tecnici delle visite, come l'indirizzo IP. Trovi i dettagli nell'informativa di GitHub: <a href="https://docs.github.com/it/site-policy/privacy-policies/github-general-privacy-statement" target="_blank" rel="noopener">GitHub Privacy Statement</a>.</p>

    <h2>Quando ci contatti</h2>
    <p>Se ci scrivi su WhatsApp, per email o ci chiami, usiamo i tuoi dati (nome, numero, messaggi e foto che ci mandi) per risponderti, organizzare il sopralluogo, preparare il preventivo e svolgere il lavoro. Li conserviamo per il tempo necessario a seguire la tua richiesta e per gli obblighi di legge, per esempio fiscali.</p>
    <p>Il pulsante WhatsApp e i link a Instagram e Facebook aprono i servizi di Meta: lì vale anche la loro informativa.</p>

    <h2>I tuoi diritti</h2>
    <p>Puoi chiedere in ogni momento di vedere, correggere o cancellare i tuoi dati, oppure di limitarne l'uso, scrivendo a <a href="mailto:%(email)s">%(email)s</a>. Puoi anche rivolgerti al <a href="https://www.garanteprivacy.it/" target="_blank" rel="noopener">Garante per la protezione dei dati personali</a>.</p>

    <p><small>Ultimo aggiornamento: 5 ottobre 2026.</small></p>
  </div>
</main>
%(piede)s
<script src="assets/js/main.js?v=%(v)s" defer></script>
</body>
</html>
""" % {"sprite": SPRITE, "testata": testata(False), "piede": piede(False), "icdx": icona("i-dx"),
           "piva": PIVA, "email": EMAIL, "v": VERSIONE}
    return testa("Privacy | Astra Gardens", "Informativa privacy del sito Astra Gardens di Francesco Guizzardi, Flero (BS): zero cookie e zero tracciamento.",
                 "privacy.html") + corpo


def pagina_404():
    # Pagina autonoma: deve funzionare a qualsiasi profondità di percorso, quindi stile in linea.
    import base64
    logo = base64.b64encode(open(os.path.join(SITO, "assets/img/logo-bianco-240.png"), "rb").read()).decode()
    return """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Questo sentiero porta altrove | Astra Gardens</title>
<meta name="robots" content="noindex">
<meta name="theme-color" content="#114232">
<style>
  html,body{margin:0;height:100%%}
  body{font-family:"Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif;background:#114232;color:#fff;display:grid;place-items:center;text-align:center;padding:24px;box-sizing:border-box;font-size:19px;line-height:1.6}
  main{max-width:560px}
  img{width:200px;height:auto;margin:0 auto 32px;display:block}
  h1{font-family:Georgia,"Times New Roman",serif;font-weight:600;font-size:2.2rem;line-height:1.15;margin:0 0 .5em}
  p{color:rgba(255,255,255,.9);margin:0 0 28px}
  a{display:inline-flex;align-items:center;justify-content:center;min-height:58px;padding:12px 28px;border-radius:999px;font-weight:700;text-decoration:none;margin:6px}
  .wa{background:#25d366;color:#0b2e23}
  .casa{border:2px solid rgba(255,255,255,.7);color:#fff}
</style>
</head>
<body>
<main>
  <img src="data:image/png;base64,%(logo)s" alt="Astra Gardens" width="240" height="49">
  <h1>Questo sentiero porta altrove.</h1>
  <p>La pagina che cerchi ha cambiato posto. Torna alla pagina principale e scopri i nostri servizi per il tuo giardino.</p>
  <a class="casa" id="casa" href="/">Torna alla pagina principale</a>
  <a class="wa" href="%(wa)s" target="_blank" rel="noopener">Scrivici su WhatsApp</a>
</main>
<script>
  (function () {
    var p = location.pathname, base = "/";
    if (/^\\/astra-gardens-site(\\/|$)/.test(p)) base = "/astra-gardens-site/";
    document.getElementById("casa").href = base;
  })();
</script>
</body>
</html>
""" % {"logo": logo, "wa": WA_GENERALE}


def sitemap():
    import datetime
    oggi = datetime.date.today().isoformat()
    return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>%(b)s</loc><lastmod>%(oggi)s</lastmod><changefreq>monthly</changefreq><priority>1.0</priority></url>
  <url><loc>%(b)sprivacy.html</loc><lastmod>%(oggi)s</lastmod><changefreq>yearly</changefreq><priority>0.2</priority></url>
</urlset>
""" % {"b": BASE, "oggi": oggi}


def robots():
    return "User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % BASE


def manifest():
    return json.dumps({
        "name": "Astra Gardens", "short_name": "Astra Gardens", "lang": "it",
        "start_url": "./", "display": "browser", "background_color": "#f7f4ec", "theme_color": "#114232",
        "icons": [{"src": "assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"}],
    }, ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    for nome, contenuto in (("index.html", index()), ("privacy.html", privacy()), ("404.html", pagina_404()),
                            ("sitemap.xml", sitemap()), ("robots.txt", robots()), ("site.webmanifest", manifest()),
                            ("CNAME", "astragardens.it"),
                            # Verifica Google Search Console (astragiardini@gmail.com): MAI togliere
                            (VERIFICA_GOOGLE, "google-site-verification: " + VERIFICA_GOOGLE)):
        with open(os.path.join(SITO, nome), "w", encoding="utf-8") as f:
            f.write(contenuto)
        print("scritto", nome, len(contenuto))
