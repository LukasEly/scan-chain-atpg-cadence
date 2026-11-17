# Scan chain e geração de padrões de teste com Cadence

Inserção de cadeias de varredura (scan chain) e geração automática de padrões de teste (ATPG) usando o fluxo da Cadence: síntese lógica e inserção de DFT no **Genus**, geração de padrões no **Modus** e simulação dos padrões no **Xcelium**. O trabalho reproduz o tutorial da disciplina (módulo `busca_padrao`) e adapta o fluxo para o módulo `stream_merge`, variando seus parâmetros para medir o custo de área e potência do scan e a cobertura de falhas.

**Relatório com os resultados: [RELATORIO.md](RELATORIO.md)**

## Contexto

Trabalho 2 da disciplina **Confiabilidade e Segurança de Hardware** (PUCRS), 10º semestre de Engenharia de Computação.

## Autores

- Bruno Becker Silva
- Gabriel Eduardo Decian
- Lukas Ely
- Matheus Robin

## Tecnologias

- VHDL (tutorial) e SystemVerilog (`stream_merge`)
- Cadence Genus 21.1 (síntese e DFT), Modus 21.1 (ATPG), Xcelium 23.03 (simulação) e Innovus (físico, só no tutorial)
- Scripts TCL, Bash e Python
- Biblioteca STM 65 nm

## Como executar

Requer acesso às ferramentas Cadence do laboratório (`genus`, `modus` e `xrun` no `PATH`).

### stream_merge

Na raiz do repositório. Para uma configuração (`DATA_W DEPTH WMAX`):

```bash
SIM=1 stream_merge/scripts/run_one.sh 32 8 7
```

Para a varredura completa de parâmetros (15 configurações):

```bash
SIM=1 stream_merge/scripts/sweep.sh
```

- `NCHAINS=<n>` define o número de cadeias de scan.
- `SIM=1` também simula os padrões gerados pelo Modus.
- As saídas de cada rodada ficam em `stream_merge/runs/`.
- O resumo vai para `stream_merge/results/results.csv`.
- Os gráficos são gerados com `python3 stream_merge/scripts/plot.py stream_merge/results` (requer matplotlib).

### Tutorial (busca_padrao)

Na pasta `testa_padrao_scan/synthesis`:

```bash
mkdir -p outputs/dft
genus -no_gui -files comandos_genus.txt
modus -file outputs/dft/modus_atpg/runmodus.atpg.tcl
./outputs/dft/modus_atpg/run_fullscan_sim
```

As etapas físicas no Innovus (`physical.tcl`) e as listas de arquivos para simulação RTL, pós-síntese e com SDF (`testa_padrao_scan/sim/`) são as do tutorial original.

## Estrutura de pastas

```
.
├── RELATORIO.md                   relatório com os resultados
├── apresentacao/                  slides da apresentação
├── stream_merge/
│   ├── rtl/stream_merge.sv        módulo testado (parametrizável)
│   ├── synthesis/
│   │   ├── run_genus.tcl          síntese parametrizada + relatórios pré/pós scan
│   │   ├── dft_setup.tcl          inserção das scan chains e exportação para o Modus
│   │   └── constraint/            restrições de tempo e bibliotecas
│   ├── scripts/
│   │   ├── run_one.sh             Genus → Modus → Xcelium para uma configuração
│   │   ├── sweep.sh               varredura de parâmetros
│   │   ├── collect.py             extrai área, potência e cobertura para CSV
│   │   └── plot.py                gráficos do relatório
│   └── results/                   CSVs, gráficos e relatórios de cada rodada
└── testa_padrao_scan/             tutorial
    ├── rtl/busca_padrao.vhd
    ├── synthesis/                 roteiro do Genus, DFT e etapas do Innovus
    ├── sim/                       testbenches e listas de arquivos
    └── results/                   logs da execução do tutorial
```
