# rio-edu-lab

Laboratório exploratório sobre o Grupo Educação do [data.rio](https://www.data.rio/search?groupIds=91117c15dceb41eaa08df881fa9f9310). Sandbox que precede e alimenta o produto **ACEC-Hub** (cuja estrutura-alvo está versionada em `reference/`).

## Estrutura

```
rio-edu-lab/
├── data/
│   ├── manifest.json              # snapshot canônico dos 186 itens (fetched 2026-05-05)
│   └── manifest_enriched.csv      # derivado: granularidade + temas heurísticos
├── analysis/
│   ├── 01_manifest_eda.py         # gera o relatório e o CSV enriquecido
│   └── reports/
│       └── 01_manifest_eda.md     # achados do manifest
└── reference/
    ├── README-acec-hub.md         # descrição do produto-alvo
    └── acec-hub/                  # esqueleto Python (src/acec, products/hex-edu, ...)
```

## Reproduzir as análises

```bash
python3 analysis/01_manifest_eda.py
```

Sem dependências externas; usa apenas a stdlib.

## Próximos passos

Ver `analysis/reports/01_manifest_eda.md` para os achados que orientam:
1. Probe de ingestão para resolver URLs ausentes (170 de 186 itens).
2. Triagem temática dos 127 Excels para shortlist do HEX-EDU.
3. Comparação com ATLAS ESCOLAR (158k views) como baseline de valor.
