# Política de dados do ACEC-Hub

Este diretório guarda os dados utilizados pelos produtos do ACEC-Hub. **Apenas dados pequenos e processados são versionados no Git.**

## Estrutura

```
data/
├── raw/         # Download bruto do data.rio (gitignored)
├── interim/     # Limpeza intermediária (gitignored)
└── processed/   # Parquet final, leve, commitado
```

## Princípios

1. **Raw é descartável**: o `data/raw/` pode ser regenerado a qualquer momento via `acec ingest download`. Nada lá é commitado.

2. **Intermediate é volátil**: limpeza, deduplicação, normalização. Útil pra debug, mas não merece ser commitado.

3. **Processed é o produto**: Parquet pequeno (< 1 MB por arquivo idealmente), formato canônico, **commitado**. É o que outros produtos consomem.

4. **Arquivos grandes**: usar [Git LFS](https://git-lfs.com) ou armazenamento externo (Zenodo, OSF) para qualquer coisa acima de ~10 MB. Já está configurado em `.gitattributes`.

5. **Atribuição obrigatória**: todo dataset processado deve manter, no Parquet ou em um JSON de metadados ao lado, referência ao `id` original do item no `manifest.json` da raiz.

## Como regenerar tudo

```bash
acec manifest refresh
acec ingest download --all
# Notebooks de cada produto regeneram interim/ e processed/
```

## Licenciamento

- Dados brutos: licença original do data.rio / IPP / Prefeitura do Rio de Janeiro.
- Dados processados (em `processed/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), com atribuição obrigatória ao IPP e ao ACEC-Hub.
