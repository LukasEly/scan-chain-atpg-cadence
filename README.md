# Scan chain e geração de padrões de teste com Cadence

Inserção de cadeias de varredura (scan chain) e geração automática de padrões de teste (ATPG) para um circuito digital, usando o fluxo da Cadence: síntese lógica e inserção de DFT no **Genus**, geração de padrões no **Modus** e etapas físicas no **Innovus**. O trabalho reproduz o tutorial da disciplina e adapta o fluxo para testar o módulo `busca_padrao`.

## Contexto

Trabalho 2 da disciplina **Confiabilidade e Segurança de Hardware** (PUCRS), 10º semestre de Engenharia de Computação. Trabalho em andamento.

## Autores

- Lukas Ely
- Bruno Becker Silva

## Tecnologias

- VHDL
- Cadence Genus (síntese e DFT), Modus (ATPG) e Innovus (físico)
- Scripts TCL e simulação com e sem atrasos (SDF)

## Como executar

Requer acesso às ferramentas Cadence do laboratório. Na pasta `testa_padrao_scan/synthesis`:

1. No Genus, execute os comandos de `comandos_genus.txt`: síntese, relatórios de área, tempo e potência, e inserção das scan chains (`dft_setup.tcl`).
2. No Innovus, execute `physical.tcl`, que chama as etapas de `physical/` até a geração da netlist e do SDF.

As listas de arquivos para simulação RTL, pós-síntese e com SDF estão em `testa_padrao_scan/sim/`.

## Estrutura de pastas

```
.
└── testa_padrao_scan/
    ├── rtl/busca_padrao.vhd       módulo testado
    ├── synthesis/
    │   ├── comandos_genus.txt     roteiro de síntese
    │   ├── dft_setup.tcl          configuração das scan chains
    │   ├── constraint/            restrições de tempo e bibliotecas
    │   └── physical/              etapas do Innovus
    └── sim/
        ├── tb/                    testbenches RTL e de netlist
        └── rtl/ synth/ sdf/       listas de arquivos de cada simulação
```
