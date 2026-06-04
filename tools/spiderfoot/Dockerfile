# SpiderFoot как сервис платформы. Клонируем upstream (пин по тегу) и запускаем web+API.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
ARG SPIDERFOOT_REF=v4.0

# Системные зависимости для lxml/cryptography и git для клонирования.
RUN apt-get update && apt-get install -y --no-install-recommends \
      git gcc libxml2-dev libxslt1-dev libffi-dev libssl-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone --depth 1 --branch ${SPIDERFOOT_REF} https://github.com/smicallef/spiderfoot.git
WORKDIR /opt/spiderfoot
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5001
# Слушаем на всех интерфейсах внутри контейнера (доступ только через Traefik+SSO).
CMD ["python", "./sf.py", "-l", "0.0.0.0:5001"]
