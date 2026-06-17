# Provenance trail — The widening academic-achievement gap between the rich and the poor: New evidence and possible explanations

**Paper ID**: `reardon-2011-whither`
**DOI/URL**: https://cepa.stanford.edu/sites/default/files/reardon%20whither%20opportunity%20-%20chapter%205.pdf
**OpenAlex**: _(none)_
**Status**: `partial`
**Replicator**: Lucas Freire
**Replication date**: 2024-10-20

✅ **Audit chain complete** — paper DOI → data sources → manifest snapshot → code commits → results.

## 📊 Data sources

| Source | URL | Access date | License | Declared SHA256 |
|---|---|---|---|---|
| IDS (Índice de Desenvolvimento Social) Censo 2010 por bairro/RA — IPP | https://www.data.rio/datasets/fa85ddc76a524380ad7fc60e3006ee97 | 2024-10-20 | Dados Abertos data.rio | `_(not declar...` |
| IDEB séries por bairro/RA — data.rio | https://www.data.rio/datasets/9fd1a8cc207a48c5bda7131e4e74b1ca | 2024-10-20 | Dados Abertos data.rio | `_(not declar...` |

## 🗃️ Manifest snapshot

- **Path**: `data/manifest.json`
- **SHA256**: `8ce61ae28b2c39991fb993a54ac2ea468c13c009d4632266c607d171c14c7bd6`

## 💻 Code (scripts replicadores)

| Script ID | Path | Last commit |
|---|---|---|
| 28 | `analysis/28_fetch_ids.py` | `5ccb0ea` |
| 29 | `analysis/29_vuln_edu.py` | `5ccb0ea` |
| 30 | `analysis/30_vuln_edu_charts.py` | `5ccb0ea` |

- **HEAD commit no momento do audit**: `4eced2f`

## 📈 Results (data/processed/ outputs)

| File | SHA256 (first 12) |
|---|---|
| `vuln_edu_bairros.csv` | `d67cc914faac...` |

## How to verify

```bash
# 1. Pull repo at the commit above
git checkout 4eced2f

# 2. Re-run replication scripts
python3 analysis/28_fetch_ids.py
python3 analysis/29_vuln_edu.py
python3 analysis/30_vuln_edu_charts.py

# 3. Verify hashes match
sha256sum data/processed/vuln_edu_bairros.csv
# Expect: d67cc914faaca61ea7df563058765648493d997617a6d7695670581af3c526c5
```

---

_Auto-gerado por `analysis/63_provenance_trail.py`. Audit trail v0.17. CC-BY-4.0._