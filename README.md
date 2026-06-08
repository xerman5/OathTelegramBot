# Oath — La Carta del Día 🃏

Bot de Telegram que publica una carta aleatoria de [Oath](https://ledergames.com/products/oath) cada día,
alojado **gratis en GitHub Actions**. Sin servidor, sin coste, sin mantenimiento.

## Estructura del repo

```
send_daily_card.py          ← script principal (stdlib puro, sin pip)
oath_cards.json             ← las 270 cartas de Oath
history.json                ← historial de cartas enviadas (se autogenera)
.github/
  workflows/
    daily_card.yml          ← cron de GitHub Actions
```

---

## Puesta en marcha

### 1. Crear el bot en Telegram

1. Abre [@BotFather](https://t.me/BotFather) → `/newbot`
2. Sigue los pasos y copia el **token** (`123456789:ABC-DEF...`)

### 2. Obtener el Chat ID del canal/grupo

- **Canal público**: usa `@nombre_del_canal` directamente.
- **Canal privado o grupo**: añade el bot como admin, envía un mensaje y visita:
  ```
  https://api.telegram.org/bot<TOKEN>/getUpdates
  ```
  Busca `"chat": {"id": -1001234567890 ...}` en la respuesta.

> En canales, el bot debe ser **administrador** con permiso para publicar mensajes.

### 3. Subir el código a GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/oath-carta-del-dia.git
git push -u origin main
```

### 4. Añadir los Secrets en GitHub

En tu repo: **Settings → Secrets and variables → Actions → New repository secret**

| Nombre                | Valor                          |
|-----------------------|--------------------------------|
| `TELEGRAM_BOT_TOKEN`  | `123456789:ABC-DEF...`         |
| `TELEGRAM_CHAT_ID`    | `@tu_canal` o `-1001234567890` |

> Los secrets están cifrados y nunca aparecen en los logs.

### 5. Probar manualmente

En tu repo: **Actions → Carta del Día → Run workflow**

Si todo va bien, verás la carta en tu canal y un nuevo commit en `history.json`.

---

## Horario

El cron está configurado a las **8:00 UTC**:
- Invierno (CET = UTC+1): llega a las **9:00** hora española
- Verano (CEST = UTC+2): llega a las **10:00**

Para ajustarlo edita `daily_card.yml`:
```yaml
- cron: "0 8 * * *"   # 8:00 UTC → cámbialo a "0 7 * * *" para las 9:00 en verano
```

> GitHub puede retrasar la ejecución entre 5 y 30 minutos en horas punta.
> Para una carta diaria es totalmente irrelevante.

---

## Historial automático (anti-desactivación)

Cada vez que se ejecuta, el workflow hace un commit en `history.json`:

```json
[
  {"date": "2026-06-08", "card_id": "OATH-042"},
  {"date": "2026-06-09", "card_id": "OATH-117"}
]
```

Esto mantiene el repo activo y evita que GitHub desactive el cron por inactividad a los 60 días.

---

## Dependencias

**Ninguna.** `send_daily_card.py` usa solo la biblioteca estándar de Python 3.12.
No hay `requirements.txt` porque no hace falta `pip install` de nada.

---

## Futuras mejoras

- **Imágenes propias**: las URLs actuales apuntan a `cardcdn.buriedgiant.com`.
  Si algún día ese CDN falla, puedes descargar las 270 imágenes y alojarlas
  en una carpeta `/images` del repo o en un GitHub Release.
  El campo `image` de `oath_cards.json` es lo único que habría que cambiar.
