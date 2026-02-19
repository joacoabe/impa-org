# Por qué localhost:5010 funciona pero https://imparg.org no

Si ves **http://localhost:5010/admin/** pero **https://imparg.org/** da 502/504 o no carga, el proxy no está llegando al backend.

## 1. Confirmar la IP de la máquina donde corre la app

En la máquina donde ejecutás `runserver` o `bash start.sh` (donde localhost:5010 responde), ejecutá:

```bash
hostname -I | awk '{print $1}'
# o
ip -4 addr show | grep inet
```

Anotá la IP (ej. `192.168.1.51`). **Esa** es la IP que el proxy debe usar.

## 2. En el .conf del proxy debe usarse ESA IP

En tu config del **proxy** (el archivo que está en la VM proxy, no en esta máquina) las ubicaciones de IMPA tienen que apuntar a la IP de la máquina donde corre la app:

- `location /` → `proxy_pass http://LA_IP_DE_ESTA_MAQUINA:5010/`
- `location /impa-static/` → `proxy_pass http://LA_IP_DE_ESTA_MAQUINA:5010/impa-static/`
- `location /media/` → `proxy_pass http://LA_IP_DE_ESTA_MAQUINA:5010/media/`

Si en el .conf pusiste `192.168.1.51` pero esta máquina tiene otra IP (ej. 192.168.1.52), el proxy intenta conectar a 192.168.1.51 y no a donde está la app → 504.

**Qué hacer:** En la VM proxy, editá el .conf de imparg.org y reemplazá `192.168.1.51` por la IP que obtuviste en el paso 1. Luego:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 3. Comprobar que el proxy llega al 5010

Desde la **VM proxy** (no desde esta máquina), ejecutá:

```bash
curl -I http://192.168.1.51:5010/
```

(Sustituí `192.168.1.51` por la IP de la máquina donde corre la app.)

- Si responde **HTTP/1.1 200** (o 302), el proxy puede llegar al backend; si aun así el navegador falla, revisá logs del proxy: `sudo tail -20 /var/log/nginx/error.log`.
- Si **connection refused** o **timeout**: firewall o IP equivocada. En la máquina de la app, abrí el puerto 5010 para la IP del proxy, o probá desde el proxy con la IP correcta.

## 4. Firewall en la máquina de la app

En la máquina donde corre la app (donde localhost:5010 funciona), el puerto 5010 tiene que ser accesible desde la IP del proxy. Ejemplo con `ufw`:

```bash
# Ver IP del proxy y luego, en la máquina de la app:
sudo ufw allow from IP_DEL_PROXY to any port 5010
sudo ufw reload
```

Si no usás firewall, igual verificá que algo escuche en todas las interfaces:

```bash
ss -tlnp | grep 5010
```

Tiene que verse `0.0.0.0:5010` (o `*:5010`), no solo `127.0.0.1:5010`.

## Resumen

| Dónde | Qué comprobar |
|-------|----------------|
| Máquina de la app (donde corre runserver/start.sh) | IP con `hostname -I`; que escuche en `0.0.0.0:5010` |
| .conf del proxy | Que `proxy_pass` use esa IP (no otra) para `/`, `/impa-static/`, `/media/` |
| VM proxy | `curl -I http://IP_APP:5010/` debe responder |
| Firewall en máquina de la app | Permitir al proxy acceso al puerto 5010 |

Cuando el proxy use la IP correcta y pueda conectar al 5010, https://imparg.org/ debería responder igual que http://localhost:5010/.
