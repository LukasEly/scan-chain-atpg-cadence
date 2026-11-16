##########################################################################################
## Inserção de scan (DFT) - stream_merge                                                ##
## Adaptado de dft_setup.tcl do tutorial. Chamado por run_genus.tcl.                    ##
## Usa: DESIGN, NCHAINS, LIB_FILES, _DFT_PATH, _REPORTS_PATH                            ##
##########################################################################################

## 1) CONFIGURAÇÃO GERAL DE DFT --------------------------------------------------------

## Estilo muxed-scan: cada flip-flop vira um "scan FF" com um mux na entrada D
## (D funcional x SI de teste), selecionado pelo sinal shift enable.
set_db dft_scan_style muxed_scan

## Prefixo dos pinos/objetos criados pelo DFT (chip_scan_se, chip_sdi_1, ...)
set_db dft_prefix chip_

## Detecta automaticamente o clock de topo (clk) como clock de teste
set_db dft_identify_top_level_test_clocks true
## Detecta set/reset ASSÍNCRONOS e os controla no teste. No stream_merge o
## reset é síncrono, então não há sinais assíncronos a tratar.
set_db dft_identify_test_signals true
set_db dft_identify_internal_test_clocks false
set_db use_scan_seqs_for_non_dft false
set_db designs .dft_mix_clock_edges_in_scan_chains false

## Pinos de teste novos: shift enable (SE) e test mode (TM)
define_dft shift_enable -name se -create_port -active high chip_scan_se
define_dft test_mode    -name tm -create_port -active high chip_scan_tm

## Número mínimo de cadeias. Com 1 cadeia, todo o estado (FIFO + árbitro) fica
## numa única cadeia longa; aumentar NCHAINS reduz o tempo de shift.
set_db [current_design] .dft_min_number_of_scan_chains $NCHAINS

## 2) CRIAÇÃO DAS CADEIAS --------------------------------------------------------------
check_dft_rules > $_REPORTS_PATH/dft_rules_pre.txt

## troca flip-flops comuns por scan flip-flops
replace_scan
## prévia (apenas relatório) e inserção de fato
connect_scan_chains -auto_create_chains -preview -pack > $_REPORTS_PATH/dft_preview.txt
connect_scan_chains -auto_create_chains -pack

## 3) SÍNTESE INCREMENTAL (otimiza a lógica de scan recém inserida) ------------------------
puts "################ Incremental Synthesis (Post DfT) #############"
syn_opt -incremental

## 4) RELATÓRIOS E EXPORTAÇÃO --------------------------------------------------------------
check_dft_rules -advanced > $_REPORTS_PATH/dft_rules_post.txt
## (o tutorial usa a sintaxe "report dft_chains"; tentamos as duas formas)
if {[catch { report_scan_chains > $_REPORTS_PATH/dft_chains.txt }]} {
  catch { report dft_chains > $_REPORTS_PATH/dft_chains.txt }
}
if {[catch { report_scan_setup > $_REPORTS_PATH/dft_setup.txt }]} {
  catch { report dft_setup > $_REPORTS_PATH/dft_setup.txt }
}
if {[catch { report_scan_registers > $_REPORTS_PATH/dft_registers.txt }]} {
  catch { report dft_registers > $_REPORTS_PATH/dft_registers.txt }
}

## informação de cadeias para o físico e interface para o ATPG
write_scandef > ${_DFT_PATH}/${DESIGN}.scandef
write_atpg -stil > ${_DFT_PATH}/${DESIGN}_atpg.stil

## Gera o projeto do Modus (runmodus.atpg.tcl) e o script de simulação dos
## padrões (run_fullscan_sim) usando os modelos Verilog das células.
write_dft_atpg -library ${LIB_FILES} -directory ${_DFT_PATH}/modus_atpg -ncsim_library ${LIB_FILES}
