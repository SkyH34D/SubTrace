#!/bin/bash
set -e

DOMAIN="$1"

if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain>"
    exit 1
fi

python3 dns_gui_tool.py "$DOMAIN"
