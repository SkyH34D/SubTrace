FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dns_gui_tool.py entrypoint.sh instalador_osint.sh ./

ENTRYPOINT ["./entrypoint.sh"]
