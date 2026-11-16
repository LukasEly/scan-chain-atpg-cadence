##############################################################
## Restrições de síntese - stream_merge                     ##
## Baseado em busca_padrao.sdc do tutorial (GAPH/PUCRS)      ##
##############################################################
set sdc_version 1.5
set_load_unit -picofarads 1

## Clock: 4 ns (250 MHz). Período folgado de propósito, para que todas as
## configurações da varredura (inclusive DATA_W=64 / DEPTH=32, com mux de
## leitura grande) fechem timing e a comparação de área não seja distorcida
## por upsizing de células para cumprir timing.
create_clock -name {clk} -period 4.0 [get_ports {clk}]

## O reset (rst_n) é SÍNCRONO neste módulo, então ele faz parte do caminho de
## dados e continua sendo analisado em timing (diferente do tutorial, onde o
## reset é assíncrono e recebe false path).

## INPUTS
set_input_delay -clock clk -max 0.4 [all_inputs]
set_input_transition -min -rise 0.003 [all_inputs]
set_input_transition -max -rise 0.16  [all_inputs]
set_input_transition -min -fall 0.003 [all_inputs]
set_input_transition -max -fall 0.16  [all_inputs]

## OUTPUTS
set_output_delay -clock clk -max 0.4 [all_outputs]
set_load -min 0.0014 [all_outputs]
set_load -max 0.32   [all_outputs]
