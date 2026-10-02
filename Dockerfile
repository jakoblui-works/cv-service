FROM python:3.13-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends perl wget ca-certificates fontconfig \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY texlive.profile /tmp/texlive.profile

RUN mkdir /tmp/install-tl \
 && wget -qO- https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz \
    | tar -xz -C /tmp/install-tl --strip-components=1 \
 && perl /tmp/install-tl/install-tl \
      --profile=/tmp/texlive.profile \
      --repository=https://mirror.ctan.org/systems/texlive/tlnet \
 && rm -rf /tmp/install-tl /tmp/texlive.profile

ENV PATH="/opt/texlive/bin/x86_64-linux:$PATH"

RUN tlmgr install collection-xetex latexmk tex-gyre fontawesome fontspec geometry pgf xcolor enumitem hyperref titlesec microtype tcolorbox

RUN cp "$(kpsewhich -var-value TEXMFSYSVAR)/fonts/conf/texlive-fontconfig.conf" \
       /etc/fonts/conf.d/09-texlive.conf \
 && fc-cache -fsv

COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev

COPY ./app ./app

ENV PATH="/app/.venv/bin:$PATH"

CMD ["taskiq", "worker", "app.core.broker:broker", "--fs-discover", "--workers", "1"]