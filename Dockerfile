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
    busybox-static \
    uwsgi-python3
RUN <<EOF
mkdir /app /app/instance /app/mplconfig
mkdir -p /var/spool/cron/crontabs
echo '* * * * * /app/.venv/bin/flask update-model' > /var/spool/cron/crontabs/root
EOF

COPY . /app/
WORKDIR /app/
COPY --from=builder /app/.venv /app/.venv

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

EXPOSE 5000

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["uwsgi"]
CMD ["--http", "0.0.0.0:5000", "--master", "-p", "4", "-w", "wsgi:app"]
