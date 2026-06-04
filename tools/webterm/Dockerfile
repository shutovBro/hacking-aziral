# Web-terminal (ttyd) с предустановленными интерактивными инструментами:
# recon-ng, hackingtool, clifm. Доступ только через Traefik + SSO.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 DEBIAN_FRONTEND=noninteractive
ARG TARGETARCH=amd64
ARG TTYD_VERSION=1.7.7

RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl ca-certificates bash sudo \
      gcc libssl-dev libffi-dev \
      clifm \
    && rm -rf /var/lib/apt/lists/*

# ttyd — статический бинарь под архитектуру (amd64/arm64).
RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) TT=ttyd.x86_64 ;; \
      arm64) TT=ttyd.aarch64 ;; \
      *) TT=ttyd.x86_64 ;; \
    esac; \
    curl -fsSL "https://github.com/tsl0922/ttyd/releases/download/${TTYD_VERSION}/${TT}" -o /usr/local/bin/ttyd; \
    chmod +x /usr/local/bin/ttyd

# recon-ng (клон + зависимости).
WORKDIR /opt
RUN git clone --depth 1 https://github.com/lanmaster53/recon-ng.git \
    && pip install --no-cache-dir -r recon-ng/REQUIREMENTS \
    && printf '#!/bin/bash\ncd /opt/recon-ng && exec python ./recon-ng "$@"\n' > /usr/local/bin/recon-ng \
    && chmod +x /usr/local/bin/recon-ng

# hackingtool (клон; запускается как python меню).
RUN git clone --depth 1 https://github.com/Z4nzu/hackingtool.git \
    && printf '#!/bin/bash\ncd /opt/hackingtool && exec python hackingtool.py "$@"\n' > /usr/local/bin/hackingtool \
    && chmod +x /usr/local/bin/hackingtool

# Непривилегированный пользователь для shell-сессий.
RUN useradd -m -s /bin/bash operator
WORKDIR /home/operator
USER operator

EXPOSE 7681
# ttyd запускает интерактивный bash. -W даёт запись (ввод команд).
CMD ["ttyd", "-p", "7681", "-W", "bash"]
