##############################################################
## Carga de bibliotecas e configuração do Genus              ##
## Adaptado de load.tcl do tutorial (F. Moraes, GAPH/PUCRS)  ##
## Requer a variável SM_ROOT (raiz da pasta stream_merge)    ##
##############################################################

set_db script_search_path [list $SM_ROOT/synthesis $SM_ROOT/synthesis/constraint]
set_db hdl_search_path    $SM_ROOT/rtl
set_db information_level  9

## Nomes "planos" para arrays/barramentos (evita problemas no SDF/ATPG)
set_db hdl_track_filename_row_col true
set_db hdl_array_naming_style        %s_%d
set_db hdl_instance_array_naming_style %s_%d
set_db hdl_generate_index_style      %s_%d
set_db hdl_bus_wire_naming_style     %s_%d

#===============================================================================
#  Bibliotecas STM 65nm (mesmas do tutorial)
#===============================================================================
set DK_PATH "/soft64/design-kits/stm/65nm-cmos065_536"

set_db library [list \
  ${DK_PATH}/CORE65GPSVT_5.1/libs/CORE65GPSVT_nom_1.00V_25C.lib \
  ${DK_PATH}/CLOCK65GPSVT_3.1/libs/CLOCK65GPSVT_nom_1.00V_25C.lib ]

set_db lef_library [list \
  ${DK_PATH}/EncounterTechnoKit_cmos065_7m4x0y2z_AP@5.3.1/TECH/cmos065_7m4x0y2z_AP_Worst.lef \
  ${DK_PATH}/CORE65GPSVT_5.1/CADENCE/LEF/CORE65GPSVT_soc.lef \
  ${DK_PATH}/CLOCK65GPSVT_3.1/CADENCE/LEF/CLOCK65GPSVT_soc.lef ]

set_db cap_table_file ${DK_PATH}/EncounterTechnoKit_cmos065_7m4x0y2z_AP@5.3.1/TECH/cmos065_7m4x0y2z_AP_Worst.captable

## Modelos Verilog das células: usados pelo Modus (build_model) e pela
## simulação dos padrões de teste (xrun/ncsim)
set LIB_FILES "${DK_PATH}/CORE65GPSVT_5.1/behaviour/verilog/CORE65GPSVT.v ${DK_PATH}/CLOCK65GPSVT_3.1/behaviour/verilog/CLOCK65GPSVT.v"
