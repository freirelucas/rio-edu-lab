# Binder Dockerfile pro rio-edu-lab
#
# Pra "Launch in Binder" badge: mybinder.org constrói esta imagem a partir
# do branch main + roda Jupyter Lab interativo. User pode rerodar análises
# (Theil, Pereira-style, VULN-EDU) sem instalar nada local.
#
# Stack:
#   - Python 3.12 (matches CI primary)
#   - requirements.txt (PyYAML + geopandas + plotly + matplotlib etc.)
#   - acec package em editable mode
#
# Limites Binder: 1-2GB RAM, 6h session, ~1 Mbps egress, sem GPU.
# Adequado pra reproduzir Theil + Pereira-style + VULN-EDU. PM-12 e
# HEX-EDU mais pesados podem precisar máquina local.

FROM python:3.12-slim

# Binder requires a user with UID 1000
ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}

# System deps pra geopandas (GDAL, PROJ) — slim base não traz
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    gdal-bin \
    libgdal-dev \
    proj-bin \
    libproj-dev \
    libgeos-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy repo
COPY --chown=${NB_USER}:${NB_USER} . ${HOME}/rio-edu-lab
WORKDIR ${HOME}/rio-edu-lab

# Python deps — pin pip pra evitar mudanças quebradoras
RUN pip install --no-cache-dir --upgrade "pip>=24,<26" && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir jupyterlab notebook ipykernel && \
    pip install --no-cache-dir -e reference/acec-hub || \
    echo "[warn] acec install skipped (reference/acec-hub may not be vendored)"

USER ${NB_USER}

# Bind tools
EXPOSE 8888

# Default entrypoint Binder espera Jupyter Lab
ENTRYPOINT ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
