FROM python:3.11-slim as build
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    build-essential gcc patch

WORKDIR /app
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY . /app/stage
RUN pip install --no-cache-dir -r /app/stage/requirements.txt

WORKDIR /app/stage/fo_services/kgstuff/kgat_pytorch/data_loader
RUN /usr/bin/patch < /app/stage/patches/loader_base.patch

FROM python:3.11-slim@sha256:161a52751dd68895c01350e44e9761e3965e4cef0f983bc5b6c57fd36d7e513c

RUN groupadd -g 999 python \
    && useradd -r -u 999 -g python python

RUN mkdir /app /app/instance \
    && chown python:python /app /app/instance
WORKDIR /app

COPY --chown=python:python --from=build /app/venv ./venv
COPY --chown=python:python --from=build /app/stage .

USER 999

EXPOSE 5000

ENV PATH="/app/venv/bin:$PATH"
ENTRYPOINT ["uwsgi"]
CMD ["--http", "0.0.0.0:5000", "--master", "-p", "4", "-w", "wsgi:app"]
