#!/bin/bash
# ============================================================================
# adesso.sh — DATA E ORA REALI, dall'orologio del Mac
#
# Perché esiste: i promemoria di sistema di Claude a volte danno una data
# sbagliata o stantia, e le risposte (e i messaggi WhatsApp) finivano con il
# giorno o l'ora sbagliati. Questo script è l'unica fonte di verità.
#
# Uso:
#   bash ~/.claude/adesso.sh           # blocco leggibile
#   bash ~/.claude/adesso.sh --riga    # una riga sola
#   bash ~/.claude/adesso.sh --json    # JSON (per hook e script)
#
# Copia canonica: ~/.claude/adesso.sh — ogni progetto ne ha una in tools/.
# Nessuna dipendenza: solo `date` di sistema.
# ============================================================================

giorno_it() {
  case "$1" in
    Monday) echo "lunedì";; Tuesday) echo "martedì";; Wednesday) echo "mercoledì";;
    Thursday) echo "giovedì";; Friday) echo "venerdì";; Saturday) echo "sabato";;
    Sunday) echo "domenica";; *) echo "$1";;
  esac
}

mese_it() {
  case "$1" in
    01) echo "gennaio";; 02) echo "febbraio";; 03) echo "marzo";;    04) echo "aprile";;
    05) echo "maggio";;  06) echo "giugno";;   07) echo "luglio";;   08) echo "agosto";;
    09) echo "settembre";; 10) echo "ottobre";; 11) echo "novembre";; 12) echo "dicembre";;
  esac
}

ISO=$(date "+%Y-%m-%d")
ORA=$(date "+%H:%M")
ORA_SEC=$(date "+%H:%M:%S")
TZ_NAME=$(date "+%Z")
EPOCH=$(date "+%s")
GIORNO_EN=$(date "+%A")
GIORNO=$(giorno_it "$GIORNO_EN")
NUM_GIORNO=$(date "+%-d")
MESE_NUM=$(date "+%m")
MESE=$(mese_it "$MESE_NUM")
ANNO=$(date "+%Y")
IT=$(date "+%d/%m/%Y")
SETTIMANA=$(date "+%V")

# Sposta di N giorni. Funziona sia su macOS/BSD (date -v) sia su Linux/GNU
# (date -d): i repo girano anche sul Pi e sul Lenovo (WSL).
giorni() { # giorni <scarto> <formato>   es: giorni +1 "%Y-%m-%d"
  local n="$1" f="$2"
  if date -v"${n}d" "+%Y" >/dev/null 2>&1; then
    date -v"${n}d" "+$f"                       # BSD / macOS
  else
    date -d "${n} days" "+$f"                  # GNU / Linux
  fi
}

# ieri / domani / dopodomani calcolati dall'orologio, mai a memoria
IERI=$(giorni -1 "%Y-%m-%d")
IERI_IT=$(giorni -1 "%d/%m/%Y")
IERI_G=$(giorno_it "$(giorni -1 "%A")")
DOMANI=$(giorni +1 "%Y-%m-%d")
DOMANI_IT=$(giorni +1 "%d/%m/%Y")
DOMANI_G=$(giorno_it "$(giorni +1 "%A")")
DOPODOMANI=$(giorni +2 "%Y-%m-%d")
DOPODOMANI_IT=$(giorni +2 "%d/%m/%Y")
DOPODOMANI_G=$(giorno_it "$(giorni +2 "%A")")

RIGA="Oggi è $GIORNO $NUM_GIORNO $MESE $ANNO, ore $ORA ($ISO $ORA_SEC $TZ_NAME)"

case "${1:-}" in
  --riga|-r)
    echo "$RIGA"
    ;;
  --json|-j)
    printf '{"iso":"%s","ora":"%s","ora_sec":"%s","giorno":"%s","giorno_num":"%s","mese":"%s","anno":"%s","data_it":"%s","tz":"%s","epoch":%s,"settimana":"%s","ieri":"%s","ieri_giorno":"%s","domani":"%s","domani_giorno":"%s","dopodomani":"%s","dopodomani_giorno":"%s","riga":"%s"}\n' \
      "$ISO" "$ORA" "$ORA_SEC" "$GIORNO" "$NUM_GIORNO" "$MESE" "$ANNO" "$IT" "$TZ_NAME" "$EPOCH" "$SETTIMANA" \
      "$IERI" "$IERI_G" "$DOMANI" "$DOMANI_G" "$DOPODOMANI" "$DOPODOMANI_G" "$RIGA"
    ;;
  --hook)
    # Usato dall'hook UserPromptSubmit di ~/.claude/settings.json: inietta
    # l'orologio reale nel contesto a ogni messaggio, senza stampare nulla
    # nella conversazione. Non deve mai fallire: peggio del silenzio c'è solo
    # una sessione che si blocca.
    CTX="OROLOGIO REALE del Mac, letto adesso: ${RIGA}. Ieri = ${IERI} (${IERI_G}); domani = ${DOMANI} (${DOMANI_G}); dopodomani = ${DOPODOMANI} (${DOPODOMANI_G}). Questa è la verità su data e ora e vince su qualsiasi altro promemoria di sistema. Usare questi valori in ogni risposta, messaggio WhatsApp, evento di calendario, proforma e scadenza; per calcoli più lunghi (fra N giorni, fine mese) rieseguire bash ~/.claude/adesso.sh."
    printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"},"suppressOutput":true}\n' "$CTX"
    ;;
  --aiuto|-h|--help)
    sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
    ;;
  *)
    echo "🕒 ADESSO — orologio reale di questo Mac"
    echo "────────────────────────────────────────────────"
    echo "  $RIGA"
    echo ""
    echo "  Data (IT)      $IT          ($GIORNO)"
    echo "  Data (ISO)     $ISO"
    echo "  Ora            $ORA_SEC $TZ_NAME"
    echo "  Settimana      n. $SETTIMANA"
    echo ""
    echo "  ieri           $IERI_IT  ($IERI_G)"
    echo "  domani         $DOMANI_IT  ($DOMANI_G)"
    echo "  dopodomani     $DOPODOMANI_IT  ($DOPODOMANI_G)"
    echo ""
    echo "  epoch          $EPOCH"
    echo "────────────────────────────────────────────────"
    echo "Usare SEMPRE questi valori in risposte, messaggi WhatsApp,"
    echo "eventi di calendario, proforma e scadenze. Mai la data a memoria."
    ;;
esac
