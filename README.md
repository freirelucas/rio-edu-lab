# rio-edu-lab

Laboratório exploratório sobre o Grupo Educação do [data.rio](https://www.data.rio/search?groupIds=91117c15dceb41eaa08df881fa9f9310). Sandbox que precede e alimenta o produto **ACEC-Hub** (cuja estrutura-alvo está versionada em `reference/`).

Site publicado: <https://freirelucas.github.io/rio-edu-lab/> (após primeiro merge em `main` com Pages habilitado).

## Estrutura

```
rio-edu-lab/
├── data/
│   ├── manifest.json              # snapshot canônico dos 186 itens
│   ├── manifest_enriched.csv      # derivado: granularidade + temas heurísticos
│   └── raw/probe/                 # respostas brutas do probe da API
├── analysis/
│   ├── 01_manifest_eda.py         # gera CSV enriquecido + relatório 01
│   └── 02_ingestion_probe.py      # probe da API + relatório 02
├── docs/                          # fonte do site (MkDocs Material)
│   ├── index.md
│   ├── data-rio-api.md            # documentação dos endpoints validados
│   └── reports/                   # gerados pelos scripts em analysis/
├── reference/
│   ├── README-acec-hub.md         # descrição do produto-alvo
│   └── acec-hub/                  # esqueleto Python do ACEC-Hub
├── mkdocs.yml
└── .github/workflows/pages.yml    # deploy automático em pushes para main
```

## Reproduzir as análises

```bash
python3 analysis/01_manifest_eda.py
python3 analysis/02_ingestion_probe.py
```

Sem dependências externas; só stdlib do Python 3.10+.

## Site local

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

## Próximos passos

1. Triagem temática dos 127 Excels para shortlist do HEX-EDU.
2. Comparação com ATLAS ESCOLAR (158k views) como baseline de valor.
3. Implementar o pipeline de ingestão lote em `reference/acec-hub/`.
