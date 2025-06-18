#!/bin/bash
set -e

echo "Instalando dependencias para SubTrace..."

sudo apt-get update
sudo apt-get install -y \
    amass dnsrecon subfinder httpx gowitness nmap wkhtmltopdf python3-pip

sudo pip3 install --no-cache-dir -r requirements.txt

echo "Instalación completada."
