# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

# A2A compliance agent service. Build the wheel first, then the image from the repository root:
#   uv build && docker build -f deploy/a2a/Dockerfile -t compliance-a2a .
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COMPLIANCE_PROTOCOL_HOST=0.0.0.0 \
    COMPLIANCE_PROTOCOL_PORT=8101 \
    COMPLIANCE_PROTOCOL_STATE_DIR=/data

COPY dist/*.whl /tmp/wheels/
RUN set -eu; \
    wheel=$(ls /tmp/wheels/*.whl); \
    pip install --no-cache-dir "${wheel}[a2a]"; \
    rm -rf /tmp/wheels; \
    useradd --system --uid 10001 --home-dir /data --shell /usr/sbin/nologin compliance; \
    mkdir -p /data; \
    chown compliance /data; \
    chmod 700 /data

USER compliance
WORKDIR /data
VOLUME ["/data"]
EXPOSE 8101

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ['COMPLIANCE_PROTOCOL_PORT'], timeout=4)"]

# Required at run time: COMPLIANCE_PROTOCOL_BEARER_TOKEN, COMPLIANCE_PROTOCOL_PUBLIC_URL,
# COORDINATOR_MODEL/STRUCTURED_MODEL with provider credentials, and DigitalHub credentials.
CMD ["compliance-a2a"]
