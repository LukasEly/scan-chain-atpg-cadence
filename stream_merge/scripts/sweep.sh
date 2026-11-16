#!/bin/bash
##############################################################################
## Varredura de parâmetros do stream_merge.
## Varia UM parâmetro por vez, mantendo os outros no valor default
## (DATA_W=32, DEPTH=8, WMAX=7), para isolar o efeito de cada um sobre área,
## potência, número de flip-flops de scan e cobertura de falhas.
##
## Uso:  scripts/sweep.sh            (varredura completa)
##       QUICK=1 scripts/sweep.sh    (só 3 configurações, para testar o fluxo)
##############################################################################
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)

if [ "${QUICK:-0}" = "1" ]; then
  CONFIGS="8,4,3 32,8,7 64,16,7"
else
  CONFIGS=""
  for d in 8 16 32 64;       do CONFIGS="$CONFIGS $d,8,7";  done   # DATA_W
  for p in 2 4 8 16 32;      do CONFIGS="$CONFIGS 32,$p,7"; done   # DEPTH
  for w in 1 3 7 15 31;      do CONFIGS="$CONFIGS 32,8,$w"; done   # WMAX
  # remove duplicatas (32,8,7 aparece três vezes)
  CONFIGS=$(echo $CONFIGS | tr ' ' '\n' | awk '!seen[$0]++' | tr '\n' ' ')
fi

echo "Configurações: $CONFIGS"
for c in $CONFIGS; do
  IFS=, read -r D P W <<< "$c"
  "$ROOT/scripts/run_one.sh" "$D" "$P" "$W" || echo "!! falhou: $c"
done

mkdir -p "$ROOT/results"
python3 "$ROOT/scripts/collect.py" "$ROOT/runs" "$ROOT/results"
