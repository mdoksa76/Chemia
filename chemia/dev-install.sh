#!/usr/bin/env bash
# Sklopi Chemia.oxt iz src/ i (opcionalno) instaliraj u LibreOffice.
set -e
cd "$(dirname "$0")"
rm -f Chemia.oxt
( cd src && find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null; \
  zip -rq ../Chemia.oxt META-INF Addons.xcu description.xml chemia_addon.py \
      pythonpath description icons -x 'pythonpath/tests/*' -x '*/__pycache__/*' )
echo "Sklopljeno: Chemia.oxt"
# Instalacija (zatvori LibreOffice prije):
#   unopkg add --force Chemia.oxt
# ili GUI: Alati > Upravitelj proširenja > Dodaj…
if command -v unopkg >/dev/null 2>&1; then
  unopkg add --force Chemia.oxt && echo "Instalirano. Pokreni LibreOffice."
else
  echo "unopkg nije nađen — instaliraj ručno kroz Upravitelj proširenja."
fi
