"""ACEC — Atlas Cibernético da Educação Carioca.

Pacote Python compartilhado entre os produtos do ACEC-Hub. Promovido a
partir do `rio-edu-lab` em maio/2026 (Sessão 11 do plano de MVP).

Entry points:
  - acec.stats: Theil-T entropy index + additive decomposition.
  - acec.transform.ideb_parser: hierarchical AP→RP→RA→bairro Excel parser.
  - acec.geo.h3_grid: H3 grid generation + bairro spatial join.
  - acec.ingest.arcgis: ArcGIS Hub client for data.rio.

Quick smoke test::

    >>> from acec.stats import theil_t
    >>> theil_t([1, 1, 1])
    0.0
"""

__version__ = "0.1.0"

from acec.stats import theil_decompose, theil_decompose_nested, theil_t

__all__ = ["__version__", "theil_t", "theil_decompose", "theil_decompose_nested"]
