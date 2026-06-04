# Cronicle (планировщик задач) из исходников. Одно-серверный режим.
FROM node:18-bookworm-slim

ENV CRONICLE_VERSION=0.9.84
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates tar python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/cronicle
RUN curl -L "https://github.com/jhuckaby/Cronicle/archive/v${CRONICLE_VERSION}.tar.gz" \
      | tar zxvf - --strip-components 1 \
    && npm install --omit=dev \
    && node bin/build.js dist

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 3012
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
