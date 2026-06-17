# Provenance trail — Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras — 2019

**Paper ID**: `pereira-2019-ipea`
**DOI/URL**: https://hdl.handle.net/10419/240730
**OpenAlex**: _(none)_
**Status**: `partial`
**Replicator**: Lucas Freire
**Replication date**: 2024-09-15

⚠️ **Audit chain partial** — alguns elos faltam. Veja seções abaixo.

## 📊 Data sources

| Source | URL | Access date | License | Declared SHA256 |
|---|---|---|---|---|
| Escolas Municipais (Feature Service) — Mapa Digital data.rio | https://www.data.rio/datasets/498e637753bd4e0da76e90103dd21eb7 | 2024-09-15 | Dados Abertos data.rio | `_(not declar...` |
| IDEB séries — data.rio | https://www.data.rio/datasets/9fd1a8cc207a48c5bda7131e4e74b1ca | 2024-09-15 | Dados Abertos data.rio | `_(not declar...` |
| Limite de Bairros — IPP | https://www.data.rio/datasets/dc94b29fc3594a5bb4d297bee0c9a3f2 | 2024-09-15 | Dados Abertos data.rio | `_(not declar...` |

## 🗃️ Manifest snapshot

- **Path**: `data/manifest.json`
- **SHA256**: `8ce61ae28b2c39991fb993a54ac2ea468c13c009d4632266c607d171c14c7bd6`

## 💻 Code (scripts replicadores)

| Script ID | Path | Last commit |
|---|---|---|
| 25 | `analysis/25_fetch_escolas_municipais.py` | `20d47d9` |
| 26 | `analysis/26_hex_accessibility.py` | `20d47d9` |
| 27 | `analysis/27_accessibility_charts.py` | `20d47d9` |

- **HEAD commit no momento do audit**: `4eced2f`

## 📈 Results (data/processed/ outputs)

_(no processed CSVs found for this paper_id)_

## How to verify

```bash
# 1. Pull repo at the commit above
git checkout 4eced2f

# 2. Re-run replication scripts
python3 analysis/25_fetch_escolas_municipais.py
python3 analysis/26_hex_accessibility.py
python3 analysis/27_accessibility_charts.py

# 3. Verify hashes match
```

---

_Auto-gerado por `analysis/63_provenance_trail.py`. Audit trail v0.17. CC-BY-4.0._