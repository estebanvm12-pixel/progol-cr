# 🐕 ProGol CR — Inteligencia Deportiva

Plataforma local de análisis cuantitativo para fútbol, con picks del Mundial 2026 impulsados por modelos Poisson/Elo/Dixon-Coles y Claude AI (Ryder).

- **Datos en vivo:** TheSportsDB + API-Football
- **IA:** Anthropic Claude (Ryder) — clave propia, nunca sale de tu PC
- **Sin dependencias pip** — corre solo con la librería estándar de Python
- **Acceso remoto:** túnel automático vía localtunnel, link enviado por Telegram al arrancar

---

## Cómo arrancar

**Opción 1 — automático al encender el PC:**
Ya configurado con el VBS en Startup. Arranca servidor + túnel y envía el link a Telegram.

**Opción 2 — con túnel (acceso desde celular):**
```powershell
cd C:\Users\esteb\worldcup-warroom
python server.py --tunnel
```

**Opción 3 — solo local:**
```powershell
python server.py
```

Abre automáticamente `http://127.0.0.1:8765`

---

## Usuarios del sistema

| Usuario | Contraseña | Rol | Permisos |
|---|---|---|---|
| DeadRyder | *(ver backup OneDrive)* | maestro | Todo, incluyendo ⚙️ Configuración |
| ProGolMega | *(ver backup OneDrive)* | mega_premium | Picks + parlays, sin configuración |
| ProGolPremium | *(ver backup OneDrive)* | premium | Picks básicos, sin configuración |

> Solo DeadRyder puede acceder a ⚙️ Configuración.

---

## Funcionalidades

| Feature | Notas |
|---|---|
| Fixtures día por día | ◀ ▶ o selector de fecha |
| Scores en vivo | Auto-refresh cada 45s |
| 🔮 Match Insights | Predicción completa por partido (1X2, goles, BTTS, corners, tarjetas) |
| 🧠 Ryder (chat AI) | Análisis táctico contextual con Claude |
| 📝 Notas del analista | Guardadas en SQLite por fecha |
| DoradoBet | Combinador inteligente con advertencia de picks del mismo partido |
| Acceso remoto | Túnel público automático al arrancar con `--tunnel` |

---

## Modelo de predicción

`model.py` — motor Poisson + corrección Dixon-Coles + ratings Elo:

- Scoreline más probable + tabla de probabilidades
- **1X2**, Doble Oportunidad, BTTS, Over/Under 1.5/2.5/3.5
- Expected Goals (xG), corners esperados, tarjetas esperadas
- **ProGol Index™** 1–10 de confianza
- **Ryder AI deep-dive** — capa táctica encima del modelo matemático

---

## Archivos clave

| Archivo | Propósito |
|---|---|
| `server.py` | Servidor principal: auth, API, proxy Claude, tunnel |
| `db.py` | Capa SQLite: fixtures, notas, calibración |
| `model.py` | Motor Poisson + Elo + Dixon-Coles |
| `index.html` / `styles.css` / `app.js` | Frontend del dashboard |
| `warroom.db` | Base de datos local (git-ignorado) |
| `config.json` | API keys y configuración (git-ignorado) |
| `data/users.json` | Usuarios y contraseñas hasheadas (git-ignorado) |
| `tunnel.bat` | Arrancar túnel manualmente |
| `setup-autostart.bat` | Configurar arranque automático |

---

## Backup automático (Disaster Recovery)

**Cada vez que arranca el servidor**, hace backup automático de los 3 archivos críticos en:
```
C:\Users\esteb\OneDrive\ProGolCR_Backup\progolcr_secrets_YYYYMMDD_HHMMSS.zip
```

Incluye: `config.json` (API keys), `users.json` (contraseñas), `warroom.db` (base de datos).
Conserva los últimos 5 backups y elimina los anteriores.

### Restaurar en PC nueva

```bash
# 1. Instalar requisitos
winget install Python.Python.3
winget install OpenJS.NodeJS

# 2. Clonar el código
git clone https://github.com/DeadRyder/progol-cr.git
cd progol-cr

# 3. Restaurar archivos secretos
# → Descargar el ZIP más reciente de OneDrive/ProGolCR_Backup/
# → Extraer config.json a la raíz del proyecto
# → Extraer users.json a la carpeta data/
# → Extraer warroom.db a la raíz del proyecto

# 4. Arrancar
python server.py --tunnel
```

**Tiempo estimado de recuperación: menos de 10 minutos.**

---

## Seguridad

- Contraseñas hasheadas con `pbkdf2_hmac` SHA-256, 100.000 iteraciones + salt único
- Cookies `HttpOnly; SameSite=Lax` con TTL de 7 días
- `config.json` y `data/users.json` git-ignorados — **nunca van al repositorio**
- La app **nunca ejecuta apuestas** — es solo análisis y recomendación
- Acceso remoto protegido por login obligatorio (no hay token público)

---

## Troubleshooting

- **"No Anthropic API key"** → DeadRyder → ⚙️ → pegar clave
- **Fixtures no cargan** → revisar internet, click ⟳ Refresh
- **Puerto en uso** → cambiar `PORT = 8765` en `server.py`
- **Túnel da 503** → volver a correr `python server.py --tunnel`
- **No llega mensaje Telegram** → verificar token y chat_id en ⚙️ Configuración
