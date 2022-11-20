FROM python:3-alpine

WORKDIR /app

COPY requirements.txt ./

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["uwsgi"]

CMD ["--http", "0.0.0.0:5000", "--master", "-p", "4", "-w", "app:app"]
