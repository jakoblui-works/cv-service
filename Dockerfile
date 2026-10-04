FROM python:3.13-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends perl wget ca-certificates fontconfig \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ARG CTAN_MIRROR=https://mirrors.dotsrc.org/ctan/systems/texlive/tlnet

COPY texlive.profile /tmp/texlive.profile

RUN wget -nv ---tries=5 --retry-connrefused --waitretry=5 -O /tmp/install-tl.tar.gz "$CTAN_MIRROR/install-tl-unx.tar.gz" \
 && mkdir /tmp/install-tl \
 && tar -xzf /tmp/install-tl.tar.gz -C /tmp/install-tl --strip-components=1 \
 && perl /tmp/install-tl/install-tl \
      --profile=/tmp/texlive.profile \
      --repository="$CTAN_MIRROR" \
 && rm -rf /tmp/install-tl /tmp/install-tl.tar.gz /tmp/texlive.profile

ENV PATH="/opt/texlive/bin/x86_64-linux:$PATH"

RUN tlmgr install collection-xetex latexmk tex-gyre fontawesome fontspec geometry pgf xcolor enumitem hyperref titlesec microtype tcolorbox

RUN cp "$(kpsewhich -var-value TEXMFSYSVAR)/fonts/conf/texlive-fontconfig.conf" \
       /etc/fonts/conf.d/09-texlive.conf \
 && fc-cache -fsv

COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev

COPY ./app ./app

COPY scripts/smoke_check.py ./scripts/smoke_check.py

COPY alembic.ini ./
COPY migrations ./migrations

ENV PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home --uid 1000 worker
USER worker

CMD ["taskiq", "worker", "app.core.broker:broker", "--fs-discover", "--tasks-pattern", "app/**/tasks.py", "--workers", "1"]