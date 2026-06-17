# Provenance trail — Economics and Information Theory

**Paper ID**: `theil-1967-economics`
**DOI/URL**: https://www.worldcat.org/title/economics-and-information-theory/oclc/489908
**OpenAlex**: _(none)_
**Status**: `full`
**Replicator**: Lucas Freire
**Replication date**: 2024-11-01

✅ **Audit chain complete** — paper DOI → data sources → manifest snapshot → code commits → results.

## 📊 Data sources

| Source | URL | Access date | License | Declared SHA256 |
|---|---|---|---|---|
| IDEB séries iniciais e finais por bairro/RA/AP — Rio de Janeiro | https://www.data.rio/datasets/9fd1a8cc207a48c5bda7131e4e74b1ca | 2024-11-01 | Dados Abertos data.rio | `snapshot-via...` |
| Limite de Bairros — IPP | https://www.data.rio/datasets/dc94b29fc3594a5bb4d297bee0c9a3f2 | 2024-11-01 | Dados Abertos data.rio | `_(not declar...` |

## 🗃️ Manifest snapshot

- **Path**: `data/manifest.json`
- **SHA256**: `8ce61ae28b2c39991fb993a54ac2ea468c13c009d4632266c607d171c14c7bd6`

## 💻 Code (scripts replicadores)

| Script ID | Path | Last commit |
|---|---|---|
| 10 | `analysis/10_theil_ideb.py` | `ddf283a` |
| 16 | `analysis/16_theil_weighted.py` | `8c9d064` |
| 17 | `analysis/17_theil_components.py` | `ea517d6` |
| 18 | `analysis/18_thesha_rio.py` | `1576b26` |

- **HEAD commit no momento do audit**: `4eced2f`

## 📈 Results (data/processed/ outputs)

| File | SHA256 (first 12) |
|---|---|
| `theil_ideb_anos_iniciais.csv` | `ed2402a5c22b...` |
| `theil_ideb_anos_finais.csv` | `46f48ccea8b7...` |
| `theil_bootstrap_ci.csv` | `787b8fad5844...` |

## How to verify

```bash
# 1. Pull repo at the commit above
git checkout 4eced2f

# 2. Re-run replication scripts
python3 analysis/10_theil_ideb.py
python3 analysis/16_theil_weighted.py
python3 analysis/17_theil_components.py
python3 analysis/18_thesha_rio.py

# 3. Verify hashes match
sha256sum data/processed/theil_ideb_anos_iniciais.csv
# Expect: ed2402a5c22bde75d588c855c4944d53f51573750ead285f0c46ecbe6bd010af
sha256sum data/processed/theil_ideb_anos_finais.csv
# Expect: 46f48ccea8b7602bfffdb1f82d8315241fea1b7b3ecec2d667ccb38c4211b24c
sha256sum data/processed/theil_bootstrap_ci.csv
# Expect: 787b8fad584485176942d7ba7a59ae34922acfe6641c542e6b5eab373221d6ee
```

---

_Auto-gerado por `analysis/63_provenance_trail.py`. Audit trail v0.17. CC-BY-4.0._