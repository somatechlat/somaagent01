# syntax=docker/dockerfile:1.5
FROM alpine:3.20

ARG OPENFGA_VERSION=1.8.3
ARG OPENFGA_TAG=v${OPENFGA_VERSION}

RUN apk add --no-cache curl unzip ca-certificates \
    && curl -sSL "https://github.com/openfga/openfga/releases/download/${OPENFGA_TAG}/openfga_${OPENFGA_VERSION}_linux_amd64.tar.gz" -o /tmp/openfga.tar.gz \
    && tar -xzf /tmp/openfga.tar.gz -C /usr/local/bin openfga \
    && chmod +x /usr/local/bin/openfga \
    && rm -f /tmp/openfga.tar.gz

COPY entrypoint-openfga.sh /usr/local/bin/entrypoint-openfga.sh
RUN chmod +x /usr/local/bin/entrypoint-openfga.sh

WORKDIR /app

ENTRYPOINT ["/usr/local/bin/entrypoint-openfga.sh"]
