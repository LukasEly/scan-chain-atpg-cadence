#!/bin/bash
##############################################################################
## Executa o fluxo completo para UMA configuração do stream_merge:
##   Genus (síntese + scan)  ->  Modus (ATPG)  ->  [opcional] simulação
##
## Uso:  scripts/run_one.sh DATA_W DEPTH WMAX
##       NCHAINS=4 SIM=1 scripts/run_one.sh 32 8 7
##
##   NCHAINS  número mínimo de cadeias de scan (default 1)
##   SIM=1    também simula os padrões gerados (run_fullscan_sim)
##   SKIP_MODUS=1  roda só o Genus
##
## Saída: runs/D<DATA_W>_P<DEPTH>_W<WMAX>/{logs,reports,outputs}
##############################################################################
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
DATA_W=${1:-32}
DEPTH=${2:-8}
WMAX=${3:-7}
NCHAINS=${NCHAINS:-1}

# validações do próprio módulo: DEPTH potência de 2 >= 2, WMAX >= 1
if (( DEPTH < 2 || (DEPTH & (DEPTH-1)) != 0 )); then
  echo "ERRO: DEPTH=$DEPTH deve ser potência de 2 e >= 2"; exit 1
fi
if (( WMAX < 1 || DATA_W < 1 )); then
  echo "ERRO: WMAX e DATA_W devem ser >= 1"; exit 1
fi

TAG="D${DATA_W}_P${DEPTH}_W${WMAX}"
[ "$NCHAINS" != "1" ] && TAG="${TAG}_C${NCHAINS}"
RUN="$ROOT/runs/$TAG"

echo "=============================================================="
echo " stream_merge  $TAG   ($(date))"
echo "=============================================================="
rm -rf "$RUN"
mkdir -p "$RUN/logs"
cd "$RUN" || exit 1

export SM_ROOT="$ROOT" DATA_W DEPTH WMAX NCHAINS

## ---- 1) Genus -------------------------------------------------------------
## "< /dev/null": se algum comando falhar, o Genus cai no prompt interativo;
## sem entrada ele recebe EOF e encerra, em vez de ficar travado esperando.
## O progresso aparece na tela só com as linhas de etapa (o log completo fica
## em logs/genus_stdout.log).
genus -no_gui -files "$ROOT/synthesis/run_genus.tcl" -log logs/genus \
  < /dev/null 2>&1 | tee logs/genus_stdout.log \
  | grep --line-buffered -E "^##########|syn_generic|syn_map|syn_opt|Incremental|Error|ERROR|Failed"
if ! grep -q "GENUS OK" logs/genus_stdout.log; then
  echo "ERRO no Genus. Veja $RUN/logs/genus_stdout.log"
  tail -30 logs/genus_stdout.log
  exit 2
fi
echo "[ok] Genus"

[ "${SKIP_MODUS:-0}" = "1" ] && exit 0

## ---- 2) Modus (ATPG) ------------------------------------------------------
## write_dft_atpg gerou outputs/dft/modus_atpg/runmodus.atpg.tcl, que faz:
## build_model -> build_testmode -> verify_test_structures -> build_faultmodel
## -> create_logic_tests (ATPG) -> write_vectors
modus -file outputs/dft/modus_atpg/runmodus.atpg.tcl \
  < /dev/null > logs/modus_stdout.log 2>&1
echo "[ok] Modus (status $?)"
# guarda também os logs internos do Modus, se existirem
find . -path ./logs -prune -o -name "log_*" -type f -print 2>/dev/null \
  | xargs -r -I{} cp {} logs/ 2>/dev/null

## ---- 3) Simulação dos padrões (opcional) ----------------------------------
if [ "${SIM:-0}" = "1" ]; then
  if [ -x outputs/dft/modus_atpg/run_fullscan_sim ]; then
    ( cd outputs/dft/modus_atpg && ./run_fullscan_sim ) > logs/sim_stdout.log 2>&1
    echo "[ok] Simulação (veja logs/sim_stdout.log)"
  else
    echo "[aviso] run_fullscan_sim não encontrado"
  fi
fi

echo "Resultados em $RUN"
