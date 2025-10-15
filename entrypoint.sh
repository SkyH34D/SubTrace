#!/bin/bash
set -euo pipefail

DOMAIN="${1:-}"

if [[ -z "$DOMAIN" ]]; then
    echo "Usage: $0 <domain>"
    exit 1
fi

exec python3 dns_gui_tool.py "$DOMAIN"
