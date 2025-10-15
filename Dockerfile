FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install system dependencies and CLI tools required by the OSINT workflow
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        tar \
        unzip \
        amass \
        dnsrecon \
        nmap \
        wkhtmltopdf \
        python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Download Go-based security tools that are not available through apt
ARG SUBFINDER_VERSION=2.6.8
ARG HTTPX_VERSION=1.3.5
ARG GOWITNESS_VERSION=2.5.0
RUN curl -L -o /tmp/subfinder.tar.gz \
        "https://github.com/projectdiscovery/subfinder/releases/download/v${SUBFINDER_VERSION}/subfinder_${SUBFINDER_VERSION}_linux_amd64.tar.gz" \
    && tar -xzf /tmp/subfinder.tar.gz -C /tmp \
    && mv /tmp/subfinder_${SUBFINDER_VERSION}_linux_amd64/subfinder /usr/local/bin/subfinder \
    && chmod +x /usr/local/bin/subfinder \
    && rm -rf /tmp/subfinder*
RUN curl -L -o /tmp/httpx.tar.gz \
        "https://github.com/projectdiscovery/httpx/releases/download/v${HTTPX_VERSION}/httpx_${HTTPX_VERSION}_linux_amd64.tar.gz" \
    && tar -xzf /tmp/httpx.tar.gz -C /tmp \
    && mv /tmp/httpx_${HTTPX_VERSION}_linux_amd64/httpx /usr/local/bin/httpx \
    && chmod +x /usr/local/bin/httpx \
    && rm -rf /tmp/httpx*
RUN curl -L -o /usr/local/bin/gowitness \
        "https://github.com/sensepost/gowitness/releases/download/${GOWITNESS_VERSION}/gowitness-${GOWITNESS_VERSION}-linux-amd64" \
    && chmod +x /usr/local/bin/gowitness

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dns_gui_tool.py entrypoint.sh instalador_osint.sh ./
RUN chmod +x entrypoint.sh instalador_osint.sh

ENTRYPOINT ["./entrypoint.sh"]
