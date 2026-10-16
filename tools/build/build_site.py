#!/usr/bin/env python3
"""
Genera le pagine del sito Astra Gardens: index.html, privacy.html, 404.html, sitemap.xml, robots.txt,
site.webmanifest, CNAME e il file di verifica di Google Search Console.

Uso, da qualsiasi cartella (basta Python 3, nessuna libreria esterna):
    python3 tools/build/build_site.py

Scrive SOLO quei file nella radice del repository e non cancella mai nulla. I testi, i servizi, la
galleria e i collegamenti stanno qui sotto; stile e comportamento in assets/css/style.css e
assets/js/main.js. Le misure delle immagini si leggono dai file in assets/img (nome-LARGHEZZA.webp
più nome-640.jpg di riserva) e dai poster dei video: dopo aver rifatto un'immagine (tools/prima-dopo,
tools/build/immagini.py) o un video (tools/video) basta rilanciare questo script.
Ogni volta che cambiano stile o script si alza VERSIONE, così i telefoni scaricano i file nuovi.

Disegno del 14/10/2026 (approvato da Francesco): stile ispirato a vivaiodelgarda.it, caratteri
Instrument Serif + DM Sans ospitati qui (nessuna richiesta a Google Fonts o ad altri), verde #2A381B.
Regole fisse: ogni foto e ogni video si vede INTERO (il riquadro prende le proporzioni del file, mai
ritagli, CLAUDE.md §75) e i video sono sempre gli originali alla massima qualità (§65).

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
TEL_BREVE = "334 186 5764"
TEL_LINK = "+393341865764"
WA_NUM = "393341865764"
EMAIL = "astragiardini@gmail.com"
IG = "https://www.instagram.com/astra.gardens/"
FB = "https://www.facebook.com/profile.php?id=61587199321572"
GOOGLE = "https://www.google.com/maps?cid=2402155065646157496"
PIVA = "04489190985"
REA = "BS-618970"
PEC = "astra.gardens@pec.it"
# Sede: SOLO dove lo chiede la legge, cioe' la riga legale in fondo a ogni pagina e la privacy (Francesco
# 15/10/2026 10:34: la sede non e' ancora pronta per ricevere, niente indicazioni ne' indirizzo in vista).
# Nessun link alle indicazioni (maps/dir), nessuna via nei dati strutturati, finche' Francesco non dice che la
# sede e' pronta. Il link GOOGLE (maps?cid) resta: porta alla scheda Google per le recensioni, e sulla scheda
# l'indirizzo e' nascosto (si vede solo la zona servita, dal 15/10/2026).
INDIRIZZO = "Via Passere 2, 25020 Flero (BS)"
# Denominazione nell'ordine del registro VIES (verifica legale del 14/10/2026)
DENOMINAZIONE = "Astra Gardens di Guizzardi Francesco"
# Avviso sotto ogni immagine di progetto fatta con l'IA (Codice del Consumo art. 21, AI Act art. 50)
AVVISO_RENDER = ("Il render è un'immagine indicativa: forme, colori e dimensioni delle piante reali possono differire, "
                 "soprattutto nei primi mesi.")
VERSIONE = "20261017b"
VERIFICA_GOOGLE = "googledb139c8fc3e627f5.html"
# Quando la pagina usa i video orizzontali (computer, tablet, telefono girato): stessa regola in CSS e JS.
MQ_PC = "(min-width: 900px), (orientation: landscape)"
# Telefono (anche girato in orizzontale): si usano le versioni leggere NOME-tel.mp4 (Francesco 15/10/2026).
MQ_TEL = "(max-width: 899.98px), (max-height: 499.98px)"


def e(t):
    return html.escape(t, quote=True)


def wa(msg):
    return "https://wa.me/%s?text=%s" % (WA_NUM, quote("Buongiorno, vi scrivo dal sito Astra Gardens: " + msg, safe=""))


WA_GENERALE = wa("vorrei un sopralluogo per il mio giardino.")


def picture(nome, alt, sizes, classe="", loading="lazy", priorita=None, pigra=False):
    """pigra=True: niente indirizzi nell'HTML (data-pigro-*), li mette main.js quando il primo video in cima ha in
    memoria il suo primo turno e la fila è vicina allo schermo (17/10/2026: su Fast 4G le foto della striscia
    partivano a 0,5 s insieme al primo video e ne ritardavano l'avvio)."""
    m = MAN[nome]
    webp = ", ".join("assets/img/%s-%d.webp %dw" % (nome, w, w) for w in m["webp"])
    jpg = "assets/img/%s-%d.jpg" % (nome, m["jpg"])
    extra = ' fetchpriority="%s"' % priorita if priorita else ""
    cl = ' class="%s"' % classe if classe else ""
    a = "data-pigro-" if pigra else ""
    # --ratio: il riquadro prende le proporzioni del file, cosi' la foto si vede intera (mai ritagli)
    return ('<picture%s style="--ratio: %d / %d"><source type="image/webp" %ssrcset="%s" sizes="%s">'
            '<img %ssrc="%s" alt="%s" width="%d" height="%d" loading="%s" decoding="async" draggable="false"%s></picture>'
            % (cl, m["w"], m["h"], a, webp, sizes, a, jpg, e(alt), m["w"], m["h"], loading, extra))


def srcset(nome):
    m = MAN[nome]
    return ", ".join("assets/img/%s-%d.webp %dw" % (nome, w, w) for w in m["webp"])


def grande(nome):
    m = MAN[nome]
    return "assets/img/%s-%d.webp" % (nome, max(m["webp"]))


def proporzione(nome):
    return MAN[nome]["w"] / MAN[nome]["h"]


def misura_video(nome):
    """Misure del video lette dal suo poster (stessa larghezza e altezza del fotogramma)."""
    return misura_webp(os.path.join(SITO, "assets", "video", nome + "-poster.webp"))


def poster_srcset(nome):
    """Locandina del video: quella piccola (540 px i verticali, 960 gli orizzontali) se c'e', piu' quella grande."""
    w, _ = misura_video(nome)
    b = "assets/video/" + nome
    for piccola in (540, 960):
        if os.path.exists(os.path.join(SITO, "%s-poster-%d.webp" % (b, piccola))):
            return "%s-poster-%d.webp %dw, %s-poster.webp %dw" % (b, piccola, piccola, b, w)
    return "%s-poster.webp %dw" % (b, w)


def tel(nome):
    """Versione leggera per il telefono, se c'e' (tools/video/montaggio.py telefono)."""
    f = "assets/video/%s-tel.mp4" % nome
    return f if os.path.exists(os.path.join(SITO, f)) else None


def video_box(nome, alt, sizes, classe="", tag="div", pigra=False):
    """Video muto in loop, senza comandi, INTERO (il riquadro ha le proporzioni del video).
    Si scarica e gira solo quando entra nello schermo: nessuna sorgente nell'HTML, l'indirizzo sta in data-src
    (data-src-tel sul telefono) e main.js lo mette solo quando serve (dopo il primo video in cima).
    Niente attributo poster: lo scaricherebbe subito; l'attesa e' la <picture> qui sotto, pigra."""
    w, h = misura_video(nome)
    b = "assets/video/" + nome
    a = "data-pigro-" if pigra else ""
    return ('<%s class="video-box%s" data-clip style="--ratio: %d / %d">'
            '<picture><source type="image/webp" %ssrcset="%s" sizes="%s"><img %ssrc="%s-poster.jpg" alt="%s" width="%d" height="%d" loading="lazy" decoding="async" draggable="false"></picture>'
            '<video muted loop playsinline preload="none" aria-hidden="true" tabindex="-1" data-src="%s.mp4"%s></video></%s>'
            % (tag, (" " + classe) if classe else "", w, h, a, poster_srcset(nome), sizes, a, b, e(alt), w, h,
               b, (' data-src-tel="%s"' % tel(nome)) if tel(nome) else "", tag))


def icona(id_, classe="icona"):
    return '<svg class="%s" aria-hidden="true" focusable="false"><use href="#%s" xlink:href="#%s"></use></svg>' % (classe, id_, id_)


SPRITE = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="display:none">
  <symbol id="i-wa" viewBox="0 0 24 24"><path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></symbol>
  <symbol id="i-tel" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></symbol>
  <symbol id="i-foglia" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 19c0-8 5-13 14-14-1 9-6 14-14 14z"/><path d="M5 19l7-7"/></g></symbol>
  <symbol id="i-freccia" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M8 7h9v9"/></g></symbol>
  <symbol id="i-giu" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12l7 7 7-7"/></symbol>
  <symbol id="i-dx" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></symbol>
  <symbol id="i-sx" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M15 5l-7 7 7 7"/></symbol>
  <symbol id="i-x" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" d="M5 5l14 14M19 5L5 19"/></symbol>
  <symbol id="i-cursore" viewBox="0 0 20 12"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M6 1L1 6l5 5M14 1l5 5-5 5"/></symbol>
</svg>"""


# ---------------------------------------------------------------- contenuti

# In cima alla pagina, interi. Telefono: tre verticali. Computer: due orizzontali (furgone con targa sfocata).
# In cima, giro ogni 2 secondi (main.js). Il primo e' il video dei gerani con l'ape (Francesco 15/10/2026, «c'è
# un'ape che mi piace moltissimo»): sul telefono nel ritaglio verticale, unico video ritagliato del sito.
HERO_TEL = [
    ("gerani-villa-verticale", "Un'ape su un geranio, poi l'ulivo, la villa e il vialetto di pietra"),
    ("verticale-fiori", "Verbena e piscina in un giardino curato da noi"),
    ("giardino-piscina-2", "Giardino con piscina, agavi e ulivi"),
    ("fico-verbene-verticale", "Giovane fico tra verbene e graminacee"),
    ("giardino-piscina-1", "Giardino con piscina e vista sulle colline"),
]
HERO_PC = [
    ("gerani-villa", "Un'ape su un geranio, poi l'ulivo, la villa e il vialetto di pietra", "gerani-villa-2560"),
    ("hero-furgone", "Il furgone Astra Gardens nel giardino con piscina", "hero-furgone-2560"),
    ("hero-fiori", "Verbena, doccia e piscina affacciate sulle colline", None),
    ("giro-giardino-fontana", "Il giardino con la fontana e le aiuole rialzate in pietra", None),
]

# Striscia «Dai nostri cantieri»: foto e video verticali, nell'ordine della bozza approvata.
GALLERIA = [
    ("video", "verticale-fiori", "Verbena e piscina in un giardino curato da noi"),
    ("foto", "lav-uliveto-collina", "Uliveto in collina: prato nuovo, rose e ulivi messi a dimora"),
    ("foto", "lav-ulivo-ponpon", "Ulivo ornamentale potato a pon pon"),
    ("foto", "lav-cedro", "Tree climbing su un grande cedro"),
    ("video", "gerani-villa", "Gerani, ulivo e graminacee nel giardino di una villa"),
    ("video", "giardino-piscina-2", "Giardino con piscina, agavi e ulivi"),
    ("foto", "lav-ulivi-rose", "Ulivi, rose e un prato curato"),
    ("foto", "lav-corten-ghiaia", "Bordura in corten tra ghiaia, piante e prato"),
    ("foto", "lav-aiuola-ghiaia", "Aiuola minerale: graminacee, echinacee e rosmarino strisciante su ghiaia bianca con il bordo in tufo"),
    ("video", "fico-verbene-verticale", "Giovane fico tra verbene e graminacee"),
    ("foto", "foto-furgone", "Il furgone Astra Gardens in un giardino con piscina curato da noi"),
    ("video", "giardino-piscina-1", "Giardino con piscina e vista sulle colline"),
    ("video", "terrazzo-fioriera", "Fioriera alta sul terrazzo con un rampicante e succulente fiorite"),
    ("foto", "lav-erba-sintetica", "Erba sintetica e ciottoli di marmo bianco con un acero giapponese"),
    ("foto", "lav-aiuola-ombra", "Aiuola per la mezz'ombra con pacciamatura e bordo netto"),
    ("foto", "lav-zolle-siepe", "Prato in zolla lungo la siepe"),
    ("video", "giro-giardino-fontana", "Il giardino con la fontana e le aiuole rialzate in pietra"),
    ("foto", "lav-ghiaia-pergola", "Ghiaia bianca, prato e pergola: un giardino facile da vivere"),
    ("foto", "lav-chioma", "Ricostruzione della chioma di un albero"),
]
ALTEZZA_STRISCIA = (320, 480)  # px: telefono, computer
# Sul TELEFONO (MQ_TEL) la striscia si divide in due file che non mischiano i formati (Francesco 15/10/2026: «fai
# un carosello separato sotto per i video orizzontali e non mischiarli con quelli verticali»): prima tutte le
# voci verticali di GALLERIA nello stesso ordine, sotto le orizzontali, con in più i due video orizzontali
# dell'apertura del computer (il furgone con la targa sfocata e i fiori). Sul computer la striscia resta UNA,
# mista, com'è (Francesco 16/10/2026: «dal web si vede bene sia l'orizzontale che il verticale»).
STRISCIA_TEL_ORIZZONTALI = [
    ("video", "gerani-villa", "Gerani, ulivo e graminacee nel giardino di una villa"),
    ("foto", "lav-uliveto-collina", "Uliveto in collina: prato nuovo, rose e ulivi messi a dimora"),
    ("video", "hero-furgone", "Il furgone Astra Gardens nel giardino con piscina"),
    ("video", "giro-giardino-fontana", "Il giardino con la fontana e le aiuole rialzate in pietra"),
    ("foto", "lav-erba-sintetica", "Erba sintetica e ciottoli di marmo bianco con un acero giapponese"),
    ("video", "hero-fiori", "Verbena, doccia e piscina affacciate sulle colline"),
]

# Servizi nell'ordine del lavoro: dalla prima visita alla cura di ogni stagione.
SERVIZI = [
    ("sopralluogo", "Sopralluogo",
     "Il lavoro inizia dal tuo giardino: misuriamo lo spazio, guardiamo esposizione, terreno e piante esistenti, e raccogliamo i tuoi desideri.",
     "chi-siamo-furgone", "Il furgone Astra Gardens sotto l'arcobaleno, pronto per il sopralluogo", None),
    ("progetto", "Progetto e render",
     "Disegniamo il giardino su misura e te lo mostriamo con un render realistico: vedi il risultato prima ancora di iniziare.",
     "render-aiuola-progetto", "Render di progetto: aiuola d'ingresso con bordura in corten, graminacee e luci",
     "Immagine di progetto · render IA"),
    ("studio-botanico", "Studio botanico",
     "Scegliamo con te le piante giuste per luce, terreno e tempo che vuoi dedicare al giardino: belle oggi e sane negli anni.",
     "lav-ulivi-rose", "Ulivi, rose e prato: piante scelte per la luce e il terreno del giardino", None),
    ("preventivo", "Preventivo",
     "Un preventivo scritto e chiaro in ogni voce, con le condizioni nero su bianco prima di iniziare.",
     None, None, None),
    ("realizzazione", "Realizzazione e movimento terra",
     "Scavi, terra nuova, aiuole, bordure e piantagioni: costruiamo il giardino con mezzi nostri e la nostra squadra.",
     "srv-movimento-terra", "Miniescavatore al lavoro e furgone Astra Gardens sullo sfondo", None),
    ("corten", "Bordure in corten",
     "Bordure in acciaio corten su misura, fatte dai nostri fabbri di fiducia: linee nette tra prato, aiuole e ghiaia.",
     "srv-corten", "Bordura circolare in corten saldata su misura intorno a un albero", None),
    ("opere", "Opere in ferro e lavori edili",
     "Recinzioni, cancelli, muretti, scalini e vialetti: con i nostri artigiani di fiducia portiamo a termine anche le opere intorno al verde.",
     None, None, None),
    ("prati", "Prati in zolla",
     "Terreno preparato e livellato, zolle posate con cura: un prato verde e uniforme.",
     "srv-prato", "Prato in zolla appena posato tra bossi e vialetti", None),
    ("sintetico", "Erba sintetica",
     "Posa di erba sintetica di qualità dove il prato vero fatica: terrazzi, zone d'ombra, bordi piscina.",
     "lav-erba-buddha", "Prato sintetico dal bordo curvo, ghiaia rosa e un'aiuola di ciottoli bianchi con succulente", None),
    ("irrigazione", "Irrigazione automatica",
     "Impianti a goccia e irrigatori a scomparsa, studiati zona per zona: l'acqua giusta, al momento giusto.",
     "srv-irrigazione", "Scavo stretto e preciso con la catenaria per l'impianto di irrigazione", None),
    ("illuminazione", "Illuminazione",
     "Luci per vialetti, alberi e aiuole: il giardino si vive anche la sera.",
     None, None, None),
    ("antizanzare", "Impianto antizanzare",
     "Impianti a nebulizzazione per vivere il giardino la sera: progettati e installati da noi, con la manutenzione nel tempo.",
     "srv-antizanzare", "Impianto antizanzare: la nebulizzazione lungo la siepe", None),
    ("arredo", "Arredo e complementi",
     "Fioriere, vasi, bordure e complementi scelti insieme a te per completare il progetto.",
     "lav-ghiaia-pergola", "Ghiaia bianca, prato, pergola e piante in vaso a completare il giardino", None),
    ("potature", "Potature e tree climbing",
     "Saliamo sulla pianta con funi e imbrago o con la piattaforma aerea, e potiamo con tagli puliti che rispettano la forma naturale.",
     "srv-alberi", "Giardiniere in tree climbing tra i rami di una grande magnolia", None),
    ("abbattimenti", "Abbattimenti controllati",
     "Alberi alti smontati a sezioni, in sicurezza, anche negli spazi più stretti, con il cantiere lasciato pulito.",
     "srv-abbattimenti", "Abbattimento controllato: il tronco viene ridotto a sezioni dall'alto", None),
    ("ulivi", "Cura degli ulivi",
     "Potatura a vaso e forme ornamentali come il pon pon, per ulivi sani ed eleganti.",
     "srv-ulivi", "Ulivo ornamentale potato nella forma a pon pon", None),
    ("robot", "Robot rasaerba",
     "Installazione e cavo perimetrale: il prato si taglia da solo, ogni giorno, in silenzio.",
     "srv-robot", "Robot rasaerba sul prato tra gli ulivi", None),
    ("manutenzione", "Manutenzione",
     "Prato, siepi, aiuole e pulizia con un calendario su misura: il tuo giardino resta curato in ogni stagione.",
     "srv-siepi", "Siepe potata con cura lungo il prato", None),
]

PROGETTI = [
    ("lav-uliveto-collina", "Uliveto in collina",
     "Prato nuovo, un'aiuola di rose e ulivi messi a dimora con i tutori: un giardino che si apre sul paesaggio.",
     "Giardino in collina con prato nuovo, rose e ulivi con i tutori, e il furgone Astra Gardens"),
    ("lav-erba-sintetica", "Prato sintetico e aiuola minerale",
     "Ciottoli di marmo bianco, un acero giapponese e una siepe di tassi: verde tutto l'anno e facile da curare.",
     "Erba sintetica e ciottoli di marmo bianco con un acero giapponese e una siepe di tassi"),
    ("lav-aiuola-ghiaia", "Aiuola minerale",
     "Graminacee, echinacee e rosmarino strisciante su ghiaia bianca, con il bordo in tufo: colore per tutta l'estate, pensata per il sole pieno.",
     "Aiuola su ghiaia bianca con graminacee, echinacee, rosmarino strisciante e bordo in tufo"),
    ("foto-furgone", "Vista sulle colline",
     "Un giardino con piscina che si apre sul paesaggio: prato, graminacee e bordure curate per valorizzare la vista.",
     "Giardino con piscina, prato e graminacee affacciato sulle colline, con il furgone Astra Gardens"),
    ("lav-corten-ghiaia", "Linee in corten",
     "Bordure in acciaio corten su misura e ghiaia drenante: geometrie pulite, belle in ogni stagione.",
     "Bordura in corten su misura tra ghiaia drenante e piante"),
    ("lav-cedro", "Il cedro, in sicurezza",
     "Abbattimento in tree climbing di un cedro alto, smontato a sezioni con funi e imbrago.",
     "Giardiniere in tree climbing sul cedro, con funi e imbrago"),
    ("lav-zolle-siepe", "Un prato nuovo",
     "Prato in zolla lungo la siepe: terreno livellato e posa curata, per un verde uniforme.",
     "Prato in zolla appena posato lungo la siepe"),
    ("lav-ulivo-ponpon", "Ulivi scolpiti",
     "Potatura ornamentale a pon pon: ulivi trasformati in sculture verdi.",
     "Ulivo potato a pon pon in un giardino"),
    ("lav-aiuola-ombra", "Ombra fiorita",
     "Un'aiuola pensata per la mezz'ombra: piante scelte con cura, pacciamatura e bordo netto.",
     "Aiuola per la mezz'ombra con pacciamatura e bordo netto"),
]

# Nastro che scorre nella sezione «zona»: solo foto, decorative (le stesse sono descritte altrove).
NASTRO = ["srv-siepi", "srv-alberi", "srv-prato", "srv-ulivi", "srv-corten", "srv-irrigazione",
          "srv-movimento-terra", "srv-robot", "lav-aiuola-ombra", "lav-zolle-siepe"]
ALTEZZA_NASTRO = (200, 300)

TITOLO = "Astra Gardens · Giardiniere a Flero e in provincia di Brescia"
DESCRIZIONE = ("Giardinieri a Flero, in tutta la provincia di Brescia: progettiamo, realizziamo e curiamo giardini "
               "su misura. Manutenzione, potature e tree climbing, prati in zolla, irrigazione. Scrivici su WhatsApp.")


def jsonld():
    dati = {
        "@context": "https://schema.org",
        "@type": "HomeAndConstructionBusiness",
        "additionalType": "http://www.productontology.org/id/Landscaping",
        "@id": BASE + "#azienda",
        "name": "Astra Gardens",
        "legalName": DENOMINAZIONE,
        "description": "Giardinieri a Flero (BS), nati nel 2023 da un gruppo di diplomati e laureati in agraria e guidati "
                       "da un perito agrario iscritto all'albo: progettiamo, realizziamo e curiamo giardini chiavi in mano "
                       "in tutta la provincia di Brescia, dal sopralluogo con progetto, render e studio botanico alla "
                       "realizzazione, con la nostra squadra e artigiani di fiducia: movimento terra, bordure in corten, "
                       "opere in ferro e lavori edili, prati in zolla ed erba sintetica, irrigazione automatica, "
                       "illuminazione, impianti antizanzare, arredo, potature e tree climbing, abbattimenti controllati, "
                       "cura degli ulivi, robot rasaerba e manutenzione.",
        "url": BASE,
        "logo": BASE + "assets/img/logo-quadrato-512.png",
        "image": BASE + "assets/img/og-astra-gardens.jpg",
        "telephone": TEL,
        "email": EMAIL,
        "vatID": "IT" + PIVA,
        "foundingDate": "2023",
        "founder": {"@type": "Person", "name": "Francesco Guizzardi"},
        "address": {"@type": "PostalAddress", "postalCode": "25020", "addressLocality": "Flero",
                    "addressRegion": "BS", "addressCountry": "IT"},
        "areaServed": {"@type": "AdministrativeArea", "name": "Provincia di Brescia"},
        "sameAs": [IG, FB, GOOGLE],
        "knowsAbout": [s[1] for s in SERVIZI],
        "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": "Servizi per il verde",
            "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s[1], "description": s[2]}}
                                for s in SERVIZI],
        },
    }
    return json.dumps(dati, ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- parti comuni

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
<meta name="theme-color" content="#2A381B">
<meta name="format-detection" content="telephone=no">
<meta property="og:type" content="website">
<meta property="og:locale" content="it_IT">
<meta property="og:site_name" content="Astra Gardens">
<meta property="og:title" content="%(titolo)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(url)s">
<meta property="og:image" content="%(base)sassets/img/og-astra-gardens.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="675">
<meta property="og:image:alt" content="Astra Gardens, giardinieri a Flero e in provincia di Brescia">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="assets/img/favicon-32.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="site.webmanifest">
<link rel="preload" href="assets/fonts/dm-sans-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/instrument-serif.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/css/style.css?v=%(v)s">
<script>document.documentElement.className += " js";</script>
%(extra)s</head>
""" % {"titolo": e(titolo), "desc": e(descrizione), "url": url, "base": BASE, "v": VERSIONE, "extra": extra}


MENU_VOCI = [("cantieri", "Dai nostri cantieri"), ("chi-siamo", "Chi siamo"), ("servizi", "Servizi"),
             ("lavori", "I nostri lavori"), ("prima-e-dopo", "Prima e dopo"), ("zone", "Dove lavoriamo"),
             ("contatti", "Contatti")]


def testata(home=True):
    p = "" if home else "./"
    voci = "\n".join('      <li><a href="%s#%s">%s</a></li>' % (p, a, e(t)) for a, t in MENU_VOCI)
    return """<a class="salta" href="#contenuto">Vai al contenuto</a>
<header class="testata">
  <div class="testata__riga">
    <a class="marchio" href="%(p)s#inizio" aria-label="Astra Gardens, torna all'inizio">
      <picture><source type="image/webp" srcset="assets/img/logo-verde-480.webp 480w, assets/img/logo-verde-960.webp 960w" sizes="(min-width: 900px) 147px, 118px"><img src="assets/img/logo-verde-480.png" alt="Astra Gardens" width="480" height="98"></picture>
    </a>
    <div class="testata__azioni">
      <a class="btn btn--pieno btn--testata solo-pc" href="tel:%(tel)s">Chiamaci</a>
      <a class="btn btn--pieno btn--testata solo-pc" href="%(wa)s" target="_blank" rel="noopener">Scrivici su WhatsApp</a>
      <a class="testata__tel solo-tel" href="tel:%(tel)s" aria-label="Chiamaci al %(tel_breve)s"><span>%(ictel)s</span></a>
      <button class="apri-menu" type="button" aria-expanded="false" aria-controls="menu">Menu<span class="apri-menu__righe" aria-hidden="true"></span></button>
    </div>
  </div>
</header>
<div class="menu" id="menu" role="dialog" aria-modal="true" aria-label="Menu" hidden>
  <div class="menu__testa">
    <picture><source type="image/webp" srcset="assets/img/logo-bianco-640.webp"><img src="assets/img/logo-bianco-640.png" alt="Astra Gardens" width="640" height="131" loading="lazy" decoding="async"></picture>
    <button class="chiudi-menu" type="button">Chiudi%(icx)s</button>
  </div>
  <nav class="menu__voci" aria-label="Sezioni della pagina">
    <ul role="list">
%(voci)s
    </ul>
  </nav>
  <div class="menu__piede">
    <a class="pillola-grande pillola-grande--chiara" href="%(wa)s" target="_blank" rel="noopener">Scrivici su WhatsApp</a>
    <a class="pillola-grande pillola-grande--chiara" href="tel:%(tel)s">Chiamaci · %(tel_breve)s</a>
    <p class="menu__social"><a href="%(ig)s" target="_blank" rel="noopener">Instagram</a><a href="%(fb)s" target="_blank" rel="noopener">Facebook</a><a href="%(google)s" target="_blank" rel="noopener">Recensioni su Google</a></p>
  </div>
</div>
""" % {"p": p, "wa": WA_GENERALE, "tel": TEL_LINK, "tel_breve": TEL_BREVE, "ictel": icona("i-tel"),
       "icx": icona("i-x"), "voci": voci, "ig": IG, "fb": FB, "google": GOOGLE}


def piede(home=True):
    p = "" if home else "./"
    servizi = [("Manutenzione", "manutenzione"), ("Realizzazioni chiavi in mano", "realizzazione"),
               ("Potature e abbattimenti", "potature"), ("Prati e irrigazione", "prati"), ("Antizanzare", "antizanzare")]
    lista_servizi = "".join('<li><a href="%s#servizio-%s">%s</a></li>' % (p, a, e(t)) for t, a in servizi)
    return """<footer class="piede" id="contatti">
  <div class="contenitore">
    <div class="piede__pulsanti">
      <a class="pillola-grande pillola-grande--chiara" href="%(wa)s" target="_blank" rel="noopener">Scrivici su WhatsApp</a>
      <a class="pillola-grande pillola-grande--chiara" href="tel:%(tel)s">Chiamaci</a>
    </div>
    <p class="piede__gigante" aria-hidden="true">Astra <br class="solo-tel">Gardens</p>
    <div class="piede__colonne">
      <div><p class="piede__titoletto">Servizi</p><ul role="list">%(servizi)s</ul></div>
      <div><p class="piede__titoletto">Dove lavoriamo</p><ul role="list"><li>Sede a Flero</li><li>Brescia città</li><li>Tutta la provincia</li></ul></div>
      <div><p class="piede__titoletto">Contatti</p><ul role="list"><li><a href="tel:%(tel)s">%(tel_breve)s</a></li><li><a href="mailto:%(email)s">%(email_capo)s</a></li></ul></div>
      <div><p class="piede__titoletto">Social</p><ul role="list"><li><a href="%(ig)s" target="_blank" rel="noopener">Instagram</a></li><li><a href="%(fb)s" target="_blank" rel="noopener">Facebook</a></li><li><a href="%(google)s" target="_blank" rel="noopener">Recensioni su Google</a></li></ul></div>
    </div>
    <div class="piede__legale">
      <picture><source type="image/webp" srcset="assets/img/logo-bianco-640.webp"><img src="assets/img/logo-bianco-640.png" alt="Astra Gardens" width="640" height="131" loading="lazy"></picture>
      <p>%(legale)s</p>
    </div>
  </div>
</footer>
""" % {"wa": WA_GENERALE, "tel": TEL_LINK, "tel_breve": TEL_BREVE, "servizi": lista_servizi, "email": EMAIL,
       "email_capo": EMAIL.replace("@", "<wbr>@"), "ig": IG, "fb": FB, "google": GOOGLE, "legale": riga_legale("privacy.html")}


def riga_legale(privacy_href):
    """Riga legale in fondo a OGNI pagina, 404 compresa (verifica legale 14/10/2026): denominazione come in
    VIES, sede (pubblica dal 15/10/2026, decisione di Francesco), P.IVA, REA e link alla privacy."""
    return ('<span class="intero">%s ·</span> <span class="intero">%s ·</span> <span class="intero">P.IVA %s ·</span> '
            '<span class="intero">REA %s ·</span> <a class="intero" href="%s">Privacy</a>'
            % (e(DENOMINAZIONE), e(INDIRIZZO), PIVA, REA, privacy_href))


# ---------------------------------------------------------------- sezioni della pagina

def hero():
    """Video in cima: tutti nel DOM senza src; il primo lo avvia subito lo script qui sotto, gli altri
    main.js li scarica poco prima del loro turno (mai tutti insieme)."""
    wt, ht = misura_video(HERO_TEL[0][0])
    wp, hp = misura_video(HERO_PC[0][0])
    video = []
    for nome, alt in HERO_TEL:
        b = "assets/video/" + nome
        video.append('      <video class="hero__v" data-set="tel" data-src="%s" data-poster="%s-poster.webp" muted loop playsinline preload="none" aria-hidden="true" tabindex="-1" data-alt="%s"></video>'
                     % (tel(nome) or b + ".mp4", b, e(alt)))
    for nome, alt, hd in HERO_PC:
        b = "assets/video/" + nome
        extra = (' data-src-hd="assets/video/%s.mp4"' % hd if hd else "") + (' data-src-tel="%s"' % tel(nome) if tel(nome) else "")
        video.append('      <video class="hero__v" data-set="pc" data-src="%s.mp4"%s data-poster="%s-poster.webp" muted loop playsinline preload="none" aria-hidden="true" tabindex="-1" data-alt="%s"></video>'
                     % (b, extra, b, e(alt)))
    avvio = ("<script>(function(){var b=document.querySelector('[data-hero]');if(!b)return;"
             "var s=matchMedia(b.getAttribute('data-mq')).matches?'pc':'tel';"
             "var v=b.querySelector('video[data-set='+s+']');if(!v)return;"
             "var hd=v.getAttribute('data-src-hd'),t=v.getAttribute('data-src-tel');"
             "v.src=t&&matchMedia('" + MQ_TEL + "').matches?t:hd&&innerWidth*(devicePixelRatio||1)>2000?hd:v.getAttribute('data-src');"
             "v.setAttribute('data-caricato','1');v.preload='auto';v.muted=true;v.className+=' attivo';"
             "try{var p=v.play();if(p&&p.catch)p.catch(function(){})}catch(_){}})();</script>")
    return """  <section class="hero" id="inizio" aria-label="I nostri giardini in video">
    <div class="hero__schermo" data-hero data-mq="%(mq)s" data-mq-tel="%(mqtel)s" style="--ratio-tel: %(wt)d / %(ht)d; --ratio-pc: %(wp)d / %(hp)d">
      <picture class="hero__poster">
        <source media="%(mq)s" type="image/webp" srcset="assets/video/%(pc)s-poster.webp">
        <source media="%(mq)s" srcset="assets/video/%(pc)s-poster.jpg">
        <source type="image/webp" srcset="assets/video/%(tel)s-poster.webp">
        <img src="assets/video/%(tel)s-poster.jpg" alt="Giardino curato da Astra Gardens" width="%(wt)d" height="%(ht)d" fetchpriority="high" decoding="async">
      </picture>
%(video)s
      <div class="hero__marchio">
        <picture><source type="image/webp" srcset="assets/img/logo-bianco-640.webp 640w, assets/img/logo-bianco-960.webp 960w, assets/img/logo-bianco-1400.webp 1400w" sizes="(min-width: 900px) clamp(200px, 23vw, 360px), 176px"><img src="assets/img/logo-bianco-640.png" alt="Astra Gardens" width="640" height="131"></picture>
        <p class="hero__pillola">Progettazione • Realizzazione • Manutenzione</p>
        <p class="hero__sottotitolo">Dal 2023 progettiamo, realizziamo e curiamo giardini in tutta la provincia di Brescia, su misura per ogni esigenza e ogni gusto.</p>
      </div>
      <div class="hero__punti" role="group" aria-label="Scegli il video"></div>
      <a class="hero__giu" href="#intro" aria-label="Scorri alla presentazione">%(icgiu)s</a>
    </div>
    %(avvio)s
  </section>
""" % {"mq": MQ_PC, "mqtel": MQ_TEL, "wt": wt, "ht": ht, "wp": wp, "hp": hp, "pc": HERO_PC[0][0], "tel": HERO_TEL[0][0],
       "video": "\n".join(video), "avvio": avvio, "icgiu": icona("i-giu")}


def intro():
    return """  <section class="intro" id="intro" aria-labelledby="titolo-intro">
    <div class="contenitore intro__griglia">
      <div class="intro__testo">
        <p class="occhiello solo-tel rivela">Giardinieri a Flero · in tutta la provincia di Brescia</p>
        <h1 id="titolo-intro" class="rivela" style="--ritardo: .1s">Il tuo giardino sempre bello.<br> <em>Ci&nbsp;pensiamo noi.</em></h1>
        <p class="intro__lead rivela" style="--ritardo: .2s">Una squadra giovane, guidata da un perito agrario iscritto all'albo: dal primo sopralluogo alla cura di ogni stagione, il tuo verde è in buone mani.</p>
        <div class="intro__azioni rivela" style="--ritardo: .3s">
          <a class="btn btn--pieno btn--grande btn--wa" href="%(wa)s" target="_blank" rel="noopener">%(icwa)s<span>Scrivici su WhatsApp</span></a>
          <a class="btn btn--vuoto btn--grande" href="tel:%(tel)s">Chiamaci · %(tel_breve)s</a>
        </div>
        <p class="intro__nota rivela" style="--ritardo: .4s">Dal 2023 · Flero (BS) · sopralluogo e render prima di iniziare</p>
      </div>
      <div class="intro__media solo-pc rivela" style="--ritardo: .2s">
        %(video)s
      </div>
    </div>
  </section>
""" % {"wa": WA_GENERALE, "icwa": icona("i-wa"), "tel": TEL_LINK, "tel_breve": TEL_BREVE,
       "video": video_box("giardino-piscina-1", "Giardino con piscina e vista sulle colline", "430px")}


def misure(tipo, nome):
    return (MAN[nome]["w"], MAN[nome]["h"]) if tipo == "foto" else misura_video(nome)


def voci_striscia(elenco, sizes_foto, sizes_video):
    """Le voci di una fila, due volte di fila (la fila scorre senza fine). sizes_*(w, h) -> attributo sizes."""
    voci = []
    for copia in (0, 1):
        for i, (tipo, nome, alt) in enumerate(elenco):
            nascosta = ' aria-hidden="true"' if copia else ""
            tab = ' tabindex="-1"' if copia else ""
            w, h = misure(tipo, nome)
            larga = w > h
            if tipo == "foto":
                media = picture(nome, alt, sizes_foto(w, h), pigra=True)
                dati = 'data-media="foto" data-src="%s" data-srcset="%s" data-w="%d" data-h="%d"' % (grande(nome), srcset(nome), w, h)
                etichetta = "Apri la foto: " + alt
            else:
                # tutti i video della striscia partono da soli quando entrano nello schermo, anche gli
                # orizzontali (Francesco 15/10/2026 21:51); sul telefono le versioni leggere NOME-tel.mp4
                media = video_box(nome, alt, sizes_video(w, h), tag="span", pigra=True)
                dati = 'data-media="video" data-src="assets/video/%s.mp4"%s data-poster="assets/video/%s-poster.jpg" data-w="%d" data-h="%d"' % (
                    nome, (' data-src-tel="%s"' % tel(nome)) if tel(nome) else "", nome, w, h)
                etichetta = "Apri il video: " + alt
            classe = "striscia__voce striscia__voce--larga" if tipo == "video" and larga else "striscia__voce"
            voci.append('        <li class="%s" style="--ratio: %d / %d"%s><button class="striscia__btn" type="button" %s data-indice="%d" data-alt="%s" aria-label="%s"%s>%s</button></li>'
                        % (classe, w, h, nascosta, dati, i, e(alt), e(etichetta), tab, media))
    return "\n".join(voci)


def orizzontale(voce):
    w, h = misure(voce[0], voce[1])
    return w > h


def galleria():
    ht, hp = ALTEZZA_STRISCIA
    # computer: la striscia di sempre, mista (le stesse misure di prima: sizes in px del telefono e del computer)
    pc = voci_striscia(
        GALLERIA,
        lambda w, h: "(min-width: 900px) %dpx, %dpx" % (round(hp * w / h), round(ht * w / h)),
        lambda w, h: ("(min-width: 900px) %dpx, 88vw" % round(hp * w / h)) if w > h else
                     "(min-width: 900px) %dpx, %dpx" % (round(hp * w / h), round(ht * w / h)))
    # telefono: le verticali alte ht, le orizzontali alte quanto serve per stare in 88vw
    verticali = [v for v in GALLERIA if not orizzontale(v)]
    tel_v = voci_striscia(verticali, lambda w, h: "%dpx" % round(ht * w / h), lambda w, h: "%dpx" % round(ht * w / h))
    tel_o = voci_striscia(STRISCIA_TEL_ORIZZONTALI, lambda w, h: "calc(88vw * %d / %d * 9 / 16)" % (w, h),
                          lambda w, h: "calc(88vw * %d / %d * 9 / 16)" % (w, h))
    return """  <section class="cantieri sezione--chiara" id="cantieri" aria-labelledby="titolo-cantieri">
    <div class="contenitore cantieri__testa">
      <div class="rivela">
        <p class="pillola">Dai nostri cantieri</p>
        <h2 id="titolo-cantieri">Lasciati ispirare dai nostri giardini.</h2>
      </div>
      <p class="cantieri__aiuto rivela" style="--ritardo: .15s">Scorri, tocca una foto o un video per vederlo in grande.</p>
    </div>
    <div class="striscia rivela vista-pc" data-striscia tabindex="0" role="region" aria-label="Foto e video dai nostri cantieri, scorrono da soli" style="--h-tel: %(ht)dpx; --h-pc: %(hp)dpx">
      <ul class="striscia__lista" role="list">
%(pc)s
      </ul>
    </div>
    <div class="striscia striscia--tel rivela vista-tel" data-striscia tabindex="0" role="region" aria-label="Foto e video verticali dai nostri cantieri, scorrono da soli" style="--h-tel: %(ht)dpx">
      <ul class="striscia__lista" role="list">
%(tel_v)s
      </ul>
    </div>
    <div class="striscia striscia--tel striscia--orizzontale rivela vista-tel" data-striscia tabindex="0" role="region" aria-label="Foto e video orizzontali dai nostri cantieri, scorrono da soli" style="--h-tel: %(ht)dpx; --ritardo: .1s">
      <ul class="striscia__lista" role="list">
%(tel_o)s
      </ul>
    </div>
  </section>
""" % {"pc": pc, "tel_v": tel_v, "tel_o": tel_o, "ht": ht, "hp": hp}


def chi_siamo():
    return """  <section class="chi contenitore" id="chi-siamo" aria-labelledby="titolo-chi">
    <div class="chi__testa rivela">
      <p class="pillola">Chi siamo</p>
      <h2 id="titolo-chi">Il verde è il nostro mestiere. Flero è casa nostra.</h2>
    </div>
    <div class="chi__media rivela" style="--ritardo: .1s">
      <div class="solo-tel">%(foto)s</div>
      %(video)s
    </div>
    <div class="chi__corpo rivela" style="--ritardo: .2s">
      <div class="chi__paragrafi">
        <p>Astra Gardens nasce a Flero nel 2023 da un gruppo di diplomati e laureati in agraria. Ci unisce la passione per il verde e un'idea semplice: un giardino deve essere bello, sano e facile da vivere.</p>
        <p>Ogni progetto parte dall'ascolto: studiamo lo spazio, la luce e il terreno, e prima di iniziare ti mostriamo il risultato con un render. Poi lo realizziamo e lo curiamo nel tempo, stagione dopo stagione.</p>
      </div>
      <a class="link-freccia" href="#servizi">Scopri cosa facciamo%(icfreccia)s</a>
    </div>
  </section>
""" % {"foto": picture("foto-furgone", "Il furgone Astra Gardens in un giardino con piscina affacciato sulle colline", "(min-width: 600px) 560px, calc(100vw - 40px)"),
       "video": video_box("giardino-piscina-2", "Giardino con piscina, agavi e ulivi", "430px", "solo-pc"),
       "icfreccia": icona("i-freccia")}


def servizi():
    voci = []
    for i, (slug, titolo, testo, foto, alt, nota) in enumerate(SERVIZI):
        aperto = i == 0
        nota_html = '<p class="fisarmonica__nota">%s</p>' % e(nota) if nota else ""
        voci.append("""        <li class="fisarmonica__voce%(cl)s" id="servizio-%(slug)s">
          <h3><button class="fisarmonica__btn" type="button" id="srv-%(slug)s-btn" aria-expanded="%(esp)s" aria-controls="srv-%(slug)s">%(icfoglia)s<span class="fisarmonica__titolo">%(titolo)s</span><span class="fisarmonica__segno" aria-hidden="true"></span></button></h3>
          <div class="fisarmonica__pannello" id="srv-%(slug)s">
            <div class="fisarmonica__interno">
              <div class="fisarmonica__testo"><p>%(testo)s</p>%(avviso)s</div>
              %(figura)s
            </div>
          </div>
        </li>""" % {"cl": " aperta" if aperto else "", "slug": slug, "esp": "true" if aperto else "false",
                    "icfoglia": icona("i-foglia", "icona fisarmonica__icona"), "titolo": e(titolo), "testo": e(testo),
                    "figura": ('<figure class="fisarmonica__foto">%s%s</figure>' % (
                        picture(foto, alt, "(min-width: 900px) 260px, calc(100vw - 74px)"), nota_html)) if foto else "",
                    "avviso": '<p class="avviso-render">%s</p>' % e(AVVISO_RENDER) if slug == "progetto" else ""})
    return """  <section class="servizi" id="servizi" aria-labelledby="titolo-servizi">
    <div class="contenitore servizi__griglia">
      <div class="servizi__testa rivela">
        <p class="pillola">Servizi</p>
        <h2 id="titolo-servizi">Il tuo giardino dalla A alla Z, chiavi in mano.</h2>
        <p class="servizi__sotto">Dal sopralluogo alla manutenzione, con la nostra squadra e gli artigiani di fiducia per ferro, opere edili e luci: ti consegniamo il giardino finito.</p>
      </div>
      <ol class="fisarmonica rivela" role="list" data-fisarmonica style="--ritardo: .1s">
%(voci)s
      </ol>
    </div>
  </section>
""" % {"voci": "\n".join(voci)}


ALTEZZA_SCHEDA = (350, 475)  # px dell'immagine: telefono, computer (le schede 4:5 restano 280x350 e 380x475)


def schede(elenco, sizes):
    """Ogni scheda prende le proporzioni della sua foto: altezza fissa della fila, larghezza = altezza x proporzione.
    Così la foto riempie la scheda da bordo a bordo, intera (niente bande vuote, niente ritagli; 17/10/2026)."""
    out = []
    for foto, titolo, testo, alt in elenco:
        w, h = MAN[foto]["w"], MAN[foto]["h"]
        out.append("""        <li class="scheda" style="--ratio: %d / %d">
          %s
          <h3>%s</h3>
          <p>%s</p>
        </li>""" % (w, h, picture(foto, alt, sizes(w, h), classe="scheda__foto"), e(titolo), e(testo)))
    return "\n".join(out)


def progetti():
    ht, hp = ALTEZZA_SCHEDA
    pc = schede(PROGETTI, lambda w, h: "%dpx" % round(hp * w / h))
    # telefono (Francesco 15/10/2026: i formati non si mischiano): le verticali, e sotto le orizzontali
    vert = [p for p in PROGETTI if MAN[p[0]]["w"] <= MAN[p[0]]["h"]]
    oriz = [p for p in PROGETTI if MAN[p[0]]["w"] > MAN[p[0]]["h"]]
    tel_v = schede(vert, lambda w, h: "%dpx" % round(ht * w / h))
    tel_o = schede(oriz, lambda w, h: "calc(88vw * %d / %d * 9 / 16)" % (w, h))
    return """  <section class="progetti" id="lavori" aria-labelledby="titolo-progetti">
    <div class="contenitore progetti__testa">
      <div class="rivela">
        <p class="pillola">I nostri lavori</p>
        <h2 id="titolo-progetti">I nostri lavori più belli.</h2>
      </div>
      <div class="progetti__frecce vista-pc">
        <button class="freccia" type="button" data-carosello-indietro aria-label="Lavoro precedente">%(icsx)s</button>
        <button class="freccia freccia--piena" type="button" data-carosello-avanti aria-label="Lavoro successivo">%(icdx)s</button>
      </div>
    </div>
    <div class="vista-pc">
      <div class="carosello rivela" data-carosello tabindex="0" role="region" aria-label="I nostri lavori più belli, scorri per vederli tutti" style="--ritardo: .1s; --h-scheda: %(hp)dpx">
        <ul class="carosello__lista" role="list">
%(pc)s
        </ul>
      </div>
      <div class="contenitore"><div class="avanzamento" aria-hidden="true"><span class="avanzamento__barra" data-avanzamento></span></div></div>
    </div>
    <div class="vista-tel">
      <div class="carosello rivela" data-carosello tabindex="0" role="region" aria-label="I nostri lavori più belli in verticale, scorri per vederli tutti" style="--ritardo: .1s; --h-scheda: %(ht)dpx">
        <ul class="carosello__lista" role="list">
%(tel_v)s
        </ul>
      </div>
      <div class="contenitore"><div class="avanzamento" aria-hidden="true"><span class="avanzamento__barra" data-avanzamento></span></div></div>
      <div class="carosello carosello--orizzontale rivela" data-carosello tabindex="0" role="region" aria-label="I nostri lavori più belli in orizzontale, scorri per vederli tutti" style="--ritardo: .1s; --h-scheda: min(%(ht)dpx, calc(88vw * 9 / 16))">
        <ul class="carosello__lista" role="list">
%(tel_o)s
        </ul>
      </div>
      <div class="contenitore"><div class="avanzamento" aria-hidden="true"><span class="avanzamento__barra" data-avanzamento></span></div></div>
    </div>
  </section>
""" % {"pc": pc, "tel_v": tel_v, "tel_o": tel_o, "ht": ht, "hp": hp, "icsx": icona("i-sx"), "icdx": icona("i-dx")}


def confronto(oggi, progetto, alt_oggi, alt_progetto, titolo, sx, dx, nota, sizes, didascalia=""):
    """Confronto con cursore da trascinare (mouse, dito e frecce della tastiera).
    Regola fissa di Francesco (§58): ogni prima e dopo del sito si mostra cosi', mai solo affiancato.
    Il riquadro prende le proporzioni della coppia (--ratio): la composizione si vede intera."""
    a, b = MAN[oggi], MAN[progetto]
    if (a["w"], a["h"]) != (b["w"], b["h"]):
        raise SystemExit("confronto con misure diverse: %s %dx%d, %s %dx%d" % (oggi, a["w"], a["h"], progetto, b["w"], b["h"]))
    vero = "foto vere" in nota
    return """      <figure class="confronto-box rivela%s" style="--ratio: %d / %d">
        <div class="confronto" data-confronto data-dx="%s">
          %s
          <div class="confronto__dopo">%s</div>
          <input class="confronto__cursore" type="range" min="0" max="100" value="50" step="1" aria-label="Confronto: %s. Sposta per vedere: %s">
          <span class="confronto__linea" aria-hidden="true"><span class="confronto__maniglia">%s</span></span>
          <span class="confronto__etichetta confronto__etichetta--sx" aria-hidden="true">%s</span>
          <span class="confronto__etichetta confronto__etichetta--dx" aria-hidden="true">%s</span>
        </div>
        <figcaption><span class="confronto__titolo">%s</span>%s<span class="confronto__nota">%s</span>%s</figcaption>
      </figure>""" % (" confronto-box--vero" if vero else "", a["w"], a["h"], e(dx), picture(oggi, alt_oggi, sizes), picture(progetto, alt_progetto, sizes),
                       e(titolo), e(dx.lower()), icona("i-cursore", "icona icona--cursore"), e(sx), e(dx), e(titolo),
                       ('<span class="confronto__didascalia">%s</span>' % e(didascalia)) if didascalia else "", e(nota),
                       '<span class="avviso-render">%s</span>' % e(AVVISO_RENDER) if "render" in nota else "")


CONFRONTI = [
    ("lavoro2-prima", "lavoro2-dopo",
     "Prima: prato secco e spelacchiato, una vecchia siepe di fotinia cresciuta a dismisura e l'albero da frutto al centro",
     "Dopo: prato nuovo in zolla, bordura in acciaio corten e un'aiuola pacciamata con una siepe giovane lungo la recinzione",
     "Un giardino rinato", "Prima", "Dopo", "Lavoro realizzato · foto vere",
     "Prato nuovo in zolla, bordura in acciaio corten e una siepe giovane al posto di quella vecchia: lo stesso spazio, "
     "finalmente da vivere."),
    ("lavoro-prima", "lavoro-dopo", "Prima: un grande fico piegato sul giardino, terra spoglia e oggetti accatastati dietro la recinzione",
     "Dopo: aiuola pacciamata con nuove piante, prato e recinzione in ordine",
     "Un giardino trasformato", "Prima", "Dopo", "Lavoro realizzato · foto vere"),
    ("render-aiuola-oggi", "render-aiuola-progetto", "Oggi: l'aiuola d'ingresso prima del progetto",
     "Progetto: aiuola con bordura in corten, graminacee, fioriture e luci",
     "Aiuola d'ingresso", "Oggi", "Progetto", "Immagine di progetto · render IA"),
    ("render-prato-oggi", "render-prato-progetto", "Oggi: il prato davanti a casa prima del progetto",
     "Progetto: prato nuovo con bordura in corten e fioriture",
     "Prato nuovo con bordura in corten", "Oggi", "Progetto", "Immagine di progetto · render IA"),
    # 15/10/2026: progetto di un cliente (mai il nome ne' il comune), render IA allineati con tools/prima-dopo/render.py
    ("render-giardino-oggi", "render-giardino-progetto", "Oggi: il prato con l'ulivo e la porta da calcio",
     "Progetto: prato nuovo in zolla, l'ulivo al centro e una lagerstroemia in fiore",
     "Un giardino da vivere", "Oggi", "Progetto", "Immagine di progetto · render IA",
     "Prato nuovo in zolla, l'ulivo valorizzato al centro e una lagerstroemia che fiorisce per tutta l'estate: "
     "uno spazio pensato per giocare e stare all'aperto."),
    ("render-piscina-oggi", "render-piscina-progetto", "Oggi: l'angolo del prato accanto alla casa",
     "Progetto: piano livellato, bordura in corten e spaccato bianco di Botticino intorno alla piscina",
     "L'angolo della piscina", "Oggi", "Progetto", "Immagine di progetto · render IA",
     "Piano livellato, bordura in acciaio corten e spaccato bianco di Botticino: un fondo drenante e luminoso, "
     "con le lastre per arrivare comodi fino all'acqua."),
]


def prima_dopo():
    """Prima i LAVORI VERI (foto prima e dopo), poi i progetti con il render. Sul computer i confronti stanno
    in fila alla stessa altezza (colonne proporzionali), due per riga; sul telefono uno sotto l'altro."""
    veri = [c for c in CONFRONTI if "foto vere" in c[7]]
    render = [c for c in CONFRONTI if "foto vere" not in c[7]]
    gruppi = [veri] + [render[k:k + 2] for k in range(0, len(render), 2)]
    righe = []
    for gruppo in gruppi:
        if not gruppo:
            continue
        tot = sum(proporzione(c[0]) for c in gruppo)
        colonne = " ".join("minmax(0, %.4ffr)" % proporzione(c[0]) for c in gruppo)
        figure = []
        for c in gruppo:
            quota = proporzione(c[0]) / tot
            sizes = "(min-width: 1000px) %dpx, (min-width: 600px) 80vw, calc(100vw - 40px)" % round(1100 * quota)
            figure.append(confronto(*c[:8], sizes=sizes, didascalia=c[8] if len(c) > 8 else ""))
        righe.append('    <div class="contenitore confronti" style="--colonne: %s">\n%s\n    </div>' % (colonne, "\n".join(figure)))
    return """  <section class="primadopo sezione--chiara" id="prima-e-dopo" aria-labelledby="titolo-primadopo">
    <div class="contenitore primadopo__testa rivela">
      <p class="pillola">Prima e dopo</p>
      <h2 id="titolo-primadopo">Com'era. Come diventa.</h2>
      <p class="primadopo__aiuto">Trascina il cursore e guarda il giardino cambiare.</p>
    </div>
%s
  </section>
""" % "\n".join(righe)


def zona():
    ht, hp = ALTEZZA_NASTRO
    foto = []
    for copia in (0, 1):
        for nome in NASTRO:
            r = proporzione(nome)
            foto.append('        <li style="--ratio: %d / %d">%s</li>' % (
                MAN[nome]["w"], MAN[nome]["h"], picture(nome, "", "(min-width: 900px) %dpx, %dpx" % (round(hp * r), round(ht * r)))))
    return """  <section class="zona" id="zone" aria-labelledby="titolo-zona">
    <div class="contenitore zona__testa">
      <h2 id="titolo-zona" class="rivela">Siamo a Flero. Lavoriamo in tutta la provincia di Brescia.</h2>
      <div class="zona__corpo rivela" style="--ritardo: .15s">
        <p>Raccontaci il tuo giardino con una foto su WhatsApp: ti rispondiamo con un'idea e fissiamo un sopralluogo.</p>
        <a class="link-freccia" href="%(wa)s" target="_blank" rel="noopener">Scrivici su WhatsApp%(icfreccia)s</a>
        <p class="zona__appuntamento">In sede riceviamo solo su appuntamento.</p>
      </div>
    </div>
    <div class="nastro" aria-hidden="true" style="--h-tel: %(ht)dpx; --h-pc: %(hp)dpx">
      <ul class="nastro__binario" role="list">
%(foto)s
      </ul>
    </div>
  </section>
""" % {"wa": wa("vi mando una foto del mio giardino."), "icfreccia": icona("i-freccia"),
       "foto": "\n".join(foto), "ht": ht, "hp": hp}


def index():
    corpo = """<body>
%(sprite)s
%(testata)s
<main id="contenuto">

%(hero)s
%(intro)s
%(galleria)s
%(chi)s
%(servizi)s
%(progetti)s
%(primadopo)s
%(zona)s
</main>
%(piede)s
<div class="barra-wa">
  <a class="btn btn--pieno btn--wa" href="%(wa)s" target="_blank" rel="noopener">%(icwa)s<span>Scrivici su WhatsApp</span></a>
</div>

<dialog class="lightbox" id="lightbox" aria-label="Foto e video dai nostri cantieri">
  <div class="lightbox__media" tabindex="-1"></div>
  <p class="lightbox__didascalia"></p>
  <button class="lightbox__btn lightbox__btn--chiudi" type="button" data-azione="chiudi" aria-label="Chiudi">%(icx)s</button>
  <button class="lightbox__btn lightbox__btn--prima" type="button" data-azione="prima" aria-label="Precedente">%(icsx)s</button>
  <button class="lightbox__btn lightbox__btn--dopo" type="button" data-azione="dopo" aria-label="Successivo">%(icdx)s</button>
</dialog>

<script type="application/ld+json">
%(jsonld)s
</script>
<script src="assets/js/main.js?v=%(v)s" defer></script>
</body>
</html>
""" % {
        "sprite": SPRITE, "testata": testata(True), "piede": piede(True),
        "hero": hero(), "intro": intro(), "galleria": galleria(), "chi": chi_siamo(), "servizi": servizi(),
        "progetti": progetti(), "primadopo": prima_dopo(), "zona": zona(),
        "wa": WA_GENERALE, "icwa": icona("i-wa"), "icx": icona("i-x"), "icsx": icona("i-sx"), "icdx": icona("i-dx"),
        "jsonld": jsonld(), "v": VERSIONE,
    }
    return testa(TITOLO, DESCRIZIONE, "") + corpo


def privacy():
    """Informativa (GDPR art. 13) scritta con la verifica legale del 14/10/2026: testo da tenere com'è."""
    gh = "https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement"
    corpo = """<body class="pagina-testo">
%(sprite)s
%(testata)s
<main id="contenuto" class="pagina">
  <div class="contenitore pagina__corpo">
    <a class="link-freccia link-freccia--indietro" href="./">%(icsx)s<span>Torna alla pagina principale</span></a>
    <p class="pillola">Privacy</p>
    <h1>Informativa privacy</h1>
    <div class="pagina__testo" data-legale>
      <p><strong>Chi tratta i tuoi dati.</strong> %(denominazione)s, impresa individuale, P.IVA %(piva)s, REA %(rea)s, sede in %(indirizzo)s. Contatti: <a href="mailto:%(email)s">%(email)s</a> · PEC <a href="mailto:%(pec)s">%(pec)s</a> · <a href="tel:%(tel_link)s">%(tel)s</a>.</p>
      <p><strong>Questo sito.</strong> Non usa cookie, strumenti di analisi o pubblicità e non carica nulla da altri siti. Non ci sono moduli: attraverso il sito non raccogliamo dati. Il sito è ospitato da GitHub (GitHub, Inc., USA), che per sicurezza registra l'indirizzo IP dei visitatori come titolare autonomo, secondo la <a href="%(gh)s" target="_blank" rel="noopener">propria informativa</a>; GitHub aderisce al Data Privacy Framework UE-USA. Noi non riceviamo questi dati. I pulsanti WhatsApp e i link a Instagram e Facebook ti portano sui servizi di Meta, dove vale anche la loro informativa.</p>
      <p><strong>Quando ci contatti (WhatsApp, telefono, email).</strong> Trattiamo nome, numero o email, messaggi, foto e vocali che ci mandi e l'indirizzo del giardino, se ce lo dai: per rispondere, fissare il sopralluogo, preparare preventivo e render e svolgere il lavoro (misure precontrattuali e contratto, art. 6.1.b GDPR; se scrivi per un condominio o un'azienda, il nostro legittimo interesse a risponderti, art. 6.1.f); per fatture e obblighi fiscali (obbligo di legge, art. 6.1.c); per difenderci in caso di contestazioni (legittimo interesse, art. 6.1.f). Darci i dati non è obbligatorio, ma senza recapito e indirizzo del giardino non possiamo fare il preventivo né il lavoro.</p>
      <p><strong>Foto dei lavori.</strong> Pubblichiamo foto e video dei giardini solo con il tuo consenso (art. 6.1.a), senza persone riconoscibili, targhe, numeri civici né indirizzo. Puoi ritirarlo quando vuoi: le togliamo entro 30 giorni.</p>
      <p><strong>Chi vede i dati.</strong> Solo noi e i collaboratori che lavorano al tuo intervento, più i fornitori che ci servono: messaggistica (WhatsApp, Meta), posta, calendario e fogli di lavoro (Google), fatturazione elettronica (Fatture in Cloud, TeamSystem), il commercialista, la banca e servizi di intelligenza artificiale che ci aiutano a preparare render e testi (OpenAI, Anthropic). Alcuni hanno sede negli Stati Uniti: il trasferimento avviene con le garanzie del GDPR (Data Privacy Framework o clausole contrattuali standard). Non vendiamo i dati e non li usiamo per pubblicità.</p>
      <p><strong>Per quanto tempo.</strong> Richieste senza seguito: 24 mesi dall'ultimo messaggio. Clienti: per la durata del rapporto; preventivi, fatture e documenti contabili 10 anni (art. 2220 c.c.). Foto pubblicate: finché non ritiri il consenso.</p>
      <p><strong>I tuoi diritti.</strong> Puoi chiedere di vedere, correggere o cancellare i tuoi dati, limitarne l'uso, riceverli in formato leggibile e opporti al trattamento basato sul legittimo interesse; puoi ritirare il consenso alle foto. Scrivi a <a href="mailto:%(email)s">%(email)s</a>: rispondiamo entro 30 giorni. Puoi anche fare reclamo al Garante per la protezione dei dati personali (<a href="https://www.garanteprivacy.it/" target="_blank" rel="noopener">www.garanteprivacy.it</a>). Non prendiamo decisioni automatizzate che ti riguardano.</p>
      <p class="pagina__data">Ultimo aggiornamento: 15 ottobre 2026</p>
    </div>
  </div>
</main>
%(piede)s
<script src="assets/js/main.js?v=%(v)s" defer></script>
</body>
</html>
""" % {"sprite": SPRITE, "testata": testata(False), "piede": piede(False), "icsx": icona("i-sx"),
           "denominazione": e(DENOMINAZIONE), "piva": PIVA, "rea": REA, "email": EMAIL, "pec": PEC,
           "tel": TEL, "tel_link": TEL_LINK, "gh": gh, "v": VERSIONE, "indirizzo": e(INDIRIZZO)}
    return testa("Privacy · Astra Gardens", "Informativa privacy di Astra Gardens di Guizzardi Francesco, Flero (BS): "
                 "il sito usa zero cookie e zero strumenti di analisi.", "privacy.html") + corpo


def pagina_404():
    # Pagina autonoma: deve funzionare a qualsiasi profondità di percorso, quindi stile in linea e logo incorporato.
    import base64
    logo = base64.b64encode(open(os.path.join(SITO, "assets/img/logo-bianco-640.webp"), "rb").read()).decode()
    return """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Questo sentiero porta altrove · Astra Gardens</title>
<meta name="robots" content="noindex">
<meta name="theme-color" content="#2A381B">
<style>
  @font-face{font-family:"DM Sans";src:url("/assets/fonts/dm-sans-var.woff2") format("woff2");font-weight:400 600;font-display:swap}
  @font-face{font-family:"Instrument Serif";src:url("/assets/fonts/instrument-serif.woff2") format("woff2");font-weight:400;font-display:swap}
  html{height:100%%}
  body{margin:0;min-height:100%%;display:flex;flex-direction:column;align-items:center;font-family:"DM Sans",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;background:#2A381B;color:#fff;text-align:center;padding:24px 24px 0;box-sizing:border-box;font-size:17px;line-height:1.6}
  main{max-width:560px;margin:auto 0;padding:24px 0}
  img{width:220px;height:auto;margin:0 auto 36px;display:block}
  h1{font-family:"Instrument Serif",Georgia,"Times New Roman",serif;font-weight:400;font-size:clamp(40px,9vw,64px);line-height:1;margin:0 0 .4em}
  p{color:#D6DCCB;margin:0 0 28px}
  a{display:inline-flex;align-items:center;justify-content:center;min-height:54px;padding:10px 28px;border-radius:999px;border:1px solid #fff;color:#fff;font-family:"Instrument Serif",Georgia,serif;font-size:22px;text-decoration:none;margin:6px}
  a:hover{background:#fff;color:#2A381B}
  footer{position:static;margin-top:auto;padding:16px 0 calc(16px + env(safe-area-inset-bottom));font-size:12px;color:#D6DCCB}
  footer a{display:inline-block;min-height:0;padding:13px 0;margin:0;border:0;border-radius:0;font-family:inherit;font-size:inherit;color:#D6DCCB;text-decoration:underline}
  footer a:hover{background:none;color:#fff}
  .intero{white-space:nowrap}
</style>
</head>
<body>
<main>
  <img src="data:image/webp;base64,%(logo)s" alt="Astra Gardens" width="640" height="131">
  <h1>Questo sentiero porta altrove.</h1>
  <p data-testo-approvato>Questa pagina non c'è, o ha cambiato indirizzo.</p>
  <a id="casa" href="/">Torna alla pagina principale</a>
  <a href="%(wa)s" target="_blank" rel="noopener">Scrivici su WhatsApp</a>
</main>
<footer>%(legale)s</footer>
<script>
  (function () {
    var p = location.pathname, base = "/";
    if (/^\\/astra-gardens-site(\\/|$)/.test(p)) base = "/astra-gardens-site/";
    document.getElementById("casa").href = base;
    document.getElementById("privacy").href = base + "privacy.html";
  })();
</script>
</body>
</html>
""" % {"logo": logo, "wa": WA_GENERALE,
       "legale": riga_legale("/privacy.html").replace('<a class="intero" href="/privacy.html">', '<a class="intero" id="privacy" href="/privacy.html">')}


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
        "start_url": "./", "display": "browser", "background_color": "#ffffff", "theme_color": "#2A381B",
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
