
# 🌐 SubTrace

  <p>
    <a align="center" href="https://github.com/SkyH34D/SubTrace" target="_blank">
      <img
        width="50%"
        src="https://github.com/SkyH34D/SubTrace/blob/a496eb9bf470966f5fd67c2b740e65d09102cd32/media/SubTrace.png"
      >
    </a>
  </p>

🚧**WORK IN PROGRESS**🚧

**SubTrace** es una herramienta gráfica y automatizada para el reconocimiento pasivo de DNS y subdominios. Combina potentes utilidades OSINT como `dnsrecon`, `amass`, `subfinder`, `httpx`, `gowitness` y `nmap` para consolidar inteligencia sobre la superficie expuesta de un dominio.

---

## ✨ Características

- 🧠 GUI en Python con `customtkinter`
- 🌐 Integración con herramientas OSINT líderes (amass, dnsrecon, subfinder…)
- 📸 Captura visual con `gowitness`
- 📄 Exportación automática de reportes en HTML y PDF
- 🐳 Versión Dockerizada para análisis aislados
- ⚙️ Script de instalación para Kali/Parrot OS

---

## 🚀 Modo de uso

### ▶️ GUI (Python)
```bash
python3 dns_gui_tool.py
```

### 🐳 Docker
```bash
docker build -t subtrace .
docker run --rm -v $(pwd)/resultados:/output subtrace dominio.com
```

### 🛠️ Instalador (Kali/Parrot)
```bash
sudo ./instalador_osint.sh
```

---

## 📁 Estructura de salida

```
dominio.com-recon/
├── amass.txt
├── dnsrecon.txt
├── subfinder.txt
├── subdominios.txt
├── vivos.txt
├── gowitness/
│   └── shots/
├── nmap.txt
├── dominio_reporte.html
└── dominio_reporte.pdf
```

---

## ⚠️ Uso Ético

> SubTrace debe utilizarse exclusivamente en entornos autorizados:
> - Laboratorios de prácticas
> - Auditorías legales
> - Red teaming bajo contrato

El uso sin permiso de esta herramienta puede ser ilegal.

---

## 👤 Autor

**Cristian "SkyH34D" Franco**  
Offensive Security | Pentester | Red Team | IA Enthusiast | Agents & MCP Servers | CEH v13
