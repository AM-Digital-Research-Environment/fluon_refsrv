FROM python:3.12-alpine AS builder

RUN apk add --no-cache \
    build-base \
    linux-headers

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN --mount=type=cache,target=/root/.cache/uv\
    uv sync --frozen --no-install-project

FROM python:3.12-alpine@sha256:ef097620baf1272e38264207003b0982285da3236a20ed829bf6bbf1e85fe3cb

RUN apk add --no-cache \
    uwsgi-python3
RUN <<EOF
addgroup --system python
adduser --system --ingroup python --uid 1001 python
mkdir /app /app/instance /app/mplconfig
chown --recursive python:python /app /app/instance /app/mplconfig
EOF

COPY . /app/
WORKDIR /app/
COPY --from=builder --chown=python:python /app/.venv /app/.venv

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

USER 1001

EXPOSE 5000

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["uwsgi"]
CMD ["--http", "0.0.0.0:5000", "--master", "-p", "4", "-w", "wsgi:app"]
