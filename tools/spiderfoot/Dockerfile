# SpiderFoot из последнего стабильного релиза (master branch).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
ARG SPIDERFOOT_REF=master

RUN apt-get update && apt-get install -y --no-install-recommends \
      git gcc libxml2-dev libxslt1-dev libffi-dev libssl-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone --depth 1 --branch ${SPIDERFOOT_REF} https://github.com/smicallef/spiderfoot.git
WORKDIR /opt/spiderfoot
# Ставим setuptools посвежее (фиксит cython_sources проблему).
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 5001
CMD ["python", "./sf.py", "-l", "0.0.0.0:5001"]
