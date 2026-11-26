# Green Topography Simulator: headless image.
#
#   podman run --rm -p 8080:8080 ghcr.io/kshekar16/greentopographysimulator          # browser viewer
#   podman run --rm -v ./data:/data ghcr.io/kshekar16/greentopographysimulator scan -o /data/scan.las
#   podman run --rm -v ./data:/data ghcr.io/kshekar16/greentopographysimulator render -o /data/green.png
#
# Rendering is software OpenGL (OSMesa), so no GPU or display is needed.

FROM python:3.12-slim

LABEL org.opencontainers.image.title="greensim" \
      org.opencontainers.image.description="Golf putting-green topography, ball-roll and LIDAR simulator" \
      org.opencontainers.image.source="https://github.com/kshekar16/GreenTopographySimulator"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLBACKEND=Agg \
    VTK_DEFAULT_OPENGL_WINDOW=vtkOSOpenGLRenderWindow

# Shared libraries the VTK wheel links against, plus OSMesa for off-screen rendering.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libgl1 libegl1 libosmesa6 libx11-6 libxrender1 libxext6 libxcursor1 libxi6 libxinerama1 libxft2 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install ".[web]"

RUN useradd --create-home --uid 1000 greensim && mkdir /data && chown greensim /data
USER greensim
WORKDIR /data

EXPOSE 8080
ENTRYPOINT ["greensim"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8080"]
