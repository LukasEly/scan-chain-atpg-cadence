##############################################################################
## Síntese + inserção de scan do stream_merge (Genus)                       ##
##                                                                          ##
## Parâmetros vêm de variáveis de ambiente (definidas por scripts/run_one.sh):
##   SM_ROOT  raiz da pasta stream_merge
##   DATA_W, DEPTH, WMAX   parâmetros do módulo
##   NCHAINS  número mínimo de cadeias de scan (default 1)
##
## Deve ser executado DENTRO do diretório da rodada (runs/<TAG>), pois todas
## as saídas são escritas em caminhos relativos (reports/, outputs/).
##############################################################################

proc envd {name def} {
  if {[info exists ::env($name)] && $::env($name) ne ""} { return $::env($name) }
  return $def
}

set SM_ROOT [envd SM_ROOT [file normalize [file join [file dirname [info script]] ..]]]
set DATA_W  [envd DATA_W 32]
set DEPTH   [envd DEPTH 8]
set WMAX    [envd WMAX 7]
set NCHAINS [envd NCHAINS 1]

set DESIGN  stream_merge
set TAG     "D${DATA_W}_P${DEPTH}_W${WMAX}"
puts "########## stream_merge: DATA_W=$DATA_W DEPTH=$DEPTH WMAX=$WMAX NCHAINS=$NCHAINS ##########"

set _REPORTS_PATH reports
set _OUTPUTS_PATH outputs
set _DFT_PATH     ${_OUTPUTS_PATH}/dft
file mkdir $_REPORTS_PATH $_DFT_PATH

## 1) bibliotecas e configuração
source $SM_ROOT/synthesis/constraint/load.tcl

## Mantém o nome do módulo como "stream_merge" mesmo com parâmetros
## sobrescritos (por padrão o Genus renomeia para stream_merge_DATA_W32_...).
## Isso deixa os nomes de design/arquivos iguais em todas as rodadas.
catch { set_db hdl_parameter_naming_style "" }

## 2) leitura e elaboração com os parâmetros desta rodada
read_hdl -sv stream_merge.sv
elaborate $DESIGN -parameters [list [list DATA_W $DATA_W] [list DEPTH $DEPTH] [list WMAX $WMAX]]
check_design -unresolved > $_REPORTS_PATH/check_design.txt

## 3) restrições
read_sdc $SM_ROOT/synthesis/constraint/stream_merge.sdc

## 4) síntese
syn_generic
syn_map
syn_opt

## 5) relatórios ANTES da inserção de scan (linha de base)
report_area          > $_REPORTS_PATH/pre_dft_area.txt
report_gates         > $_REPORTS_PATH/pre_dft_gates.txt
report_power -unit mW > $_REPORTS_PATH/pre_dft_power.txt
report_timing        > $_REPORTS_PATH/pre_dft_timing.txt
report_qor           > $_REPORTS_PATH/pre_dft_qor.txt
write_netlist [current_design] > $_OUTPUTS_PATH/${DESIGN}_noscan.v

## 6) inserção das cadeias de scan + exportação para o Modus
source $SM_ROOT/synthesis/dft_setup.tcl

## 7) relatórios DEPOIS da inserção de scan
report_area          > $_REPORTS_PATH/post_dft_area.txt
report_gates         > $_REPORTS_PATH/post_dft_gates.txt
report_power -unit mW > $_REPORTS_PATH/post_dft_power.txt
report_timing        > $_REPORTS_PATH/post_dft_timing.txt
report_qor           > $_REPORTS_PATH/post_dft_qor.txt

## 8) netlist final com scan
write_netlist [current_design] > $_OUTPUTS_PATH/${DESIGN}_scan.v
write_sdc     > $_OUTPUTS_PATH/${DESIGN}_scan.sdc

## arquivo-resumo com os parâmetros (lido por scripts/collect.py)
set fh [open $_REPORTS_PATH/params.txt w]
puts $fh "DATA_W=$DATA_W"
puts $fh "DEPTH=$DEPTH"
puts $fh "WMAX=$WMAX"
puts $fh "NCHAINS=$NCHAINS"
close $fh

puts "########## GENUS OK: $TAG ##########"
exit
