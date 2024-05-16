FROM python:3.12-alpine as build

RUN apk add --no-cache \
    build-base \
    linux-headers

WORKDIR /app
RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"

COPY pyproject.toml poetry.lock ./
RUN . ./venv/bin/activate \
    && pip install poetry \
    && poetry install --only main --no-root --no-directory

COPY src/ ./src
RUN . ./venv/bin/activate && poetry install --only main

FROM python:3.12-alpine@sha256:ef097620baf1272e38264207003b0982285da3236a20ed829bf6bbf1e85fe3cb

RUN apk add --no-cache \
    uwsgi-python3
RUN addgroup --system python \
    && adduser --system --no-create-home --ingroup python --uid 1001 python \
    && mkdir /app /app/instance /app/src /app/mplconfig \
    && chown --recursive python:python /app /app/instance /app/src /app/mplconfig

WORKDIR /app

COPY --chown=python:python --from=build /app/venv ./venv
# COPY --chown=python:python . .

USER 1001

EXPOSE 5000

ENV PATH="/app/venv/bin:$PATH"
ENTRYPOINT ["uwsgi"]
WORKDIR /app/src
CMD ["--http", "0.0.0.0:5000", "--master", "-p", "4", "-w", "wsgi:app"]
