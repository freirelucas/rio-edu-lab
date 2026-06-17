# Binder config — rio-edu-lab

Esta pasta contém os arquivos consumidos pelo **mybinder.org** pra construir um ambiente Jupyter Lab on-demand a partir do branch `main` deste repositório.

## Badge no README principal

```markdown
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/freirelucas/rio-edu-lab/main)
```

## Quando usar

- **Reproduzir Theil decomposition** (`analysis/10_theil_ideb.py` → relatórios 06/07/09/11)
- **Reproduzir Pereira-style accessibility** (`analysis/26_hex_accessibility.py` → relatório 14)
- **Reproduzir VULN-EDU** (`analysis/29_vuln_edu.py` → relatório 15)
- **Inspect funnel state** (read-only, exploratório)

## Limites do mybinder.org

- **RAM**: 1-2 GB
- **Sessão**: máx 6h, 10min idle timeout
- **Egress**: ~1 Mbps
- **Sem GPU**
- **100 concurrent sessions por repo** (federation 2i2c + GESIS + BIDS)

## O que NÃO roda em Binder

- HEX-EDU completo (mapas grandes geopandas → out of memory)
- PM-12 panel data heavy
- LLM extraction (precisa API key)
- Snowball OpenAlex em escala (precisa email + paciência)

Pra essas, use clone local com hardware decente (16+ GB RAM).

## Como funciona

1. mybinder.org clona o repo
2. Detecta `binder/Dockerfile` (este diretório), constrói imagem
3. Spinst container com Jupyter Lab na porta 8888
4. User acessa via URL temporária

Build typicamente leva 5-15min na primeira vez. Após, mybinder cacheia
até próxima mudança em `main`.

## Self-host alternativa

Se Binder degradar (foi caso de Whole Tale em 2026), self-host BinderHub
via Helm em Kubernetes. Veja [BinderHub docs](https://binderhub.readthedocs.io/).
