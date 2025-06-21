# Ecommerce API - Django Ninja Portfolio Project

Este proyecto es una API RESTful y frontend simple para un sistema de ecommerce, desarrollado como parte de mi portfolio profesional. El objetivo es mostrar habilidades técnicas en Django, Django Ninja, autenticación JWT, seguridad avanzada, integración frontend JS y despliegue moderno.

## 🚀 Stack Tecnológico
- **Python 3.12**
- **Django 5.2**
- **Django Ninja** (API tipo FastAPI)
- **JWT Authentication** (django-ninja-jwt)
- **RSA Encryption** (login seguro con clave pública/privada)
- **PostgreSQL** (dj-database-url, psycopg2)
- **WhiteNoise** (estáticos en producción)
- **Gunicorn** (WSGI server)
- **Frontend JS** (vanilla, sin frameworks)

## 📦 Dependencias principales
```
Django, django-ninja, django-ninja-jwt, dj-database-url, psycopg2-binary, whitenoise, gunicorn, python-dotenv, pydantic, pycryptodome
```
Ver `requirements.txt` para la lista completa.

## 🛠️ Funcionalidades principales
- **Registro y login de usuarios con email** (modelo personalizado)
- **Login seguro:** contraseña cifrada con RSA (clave pública expuesta vía endpoint, descifrado backend)
- **Autenticación JWT segura:**
  - Access token en respuesta
  - Refresh token en cookie HttpOnly, Secure, SameSite
  - Endpoint de refresh con cookie
- **Gestión de productos:** listar, crear (solo admin), consultar
- **Gestión de pedidos:** crear pedido, listar pedidos, consultar pedido
- **Validación de stock y control transaccional**
- **Permisos de admin para creación de productos**
- **Rate limiting en login** (anti-brute force)
- **Buenas prácticas de seguridad y organización de código**
- **Frontend JS:**
  - Login, registro, logout
  - Carrito de compras con validación de stock
  - Creación y listado de pedidos del usuario
  - Manejo de sesión vía refresh token (sin localStorage)
  - UX mejorada y mensajes de error claros

## 🔒 Endpoints principales
- `POST /api/users/register` — Registro de usuario
- `POST /api/users/token` — Login (contraseña cifrada, devuelve access y refresh token)
- `POST /api/users/token/refresh` — Refrescar access token (usa cookie)
- `GET /api/users/public-key` — Obtener clave pública RSA para login
- `GET /api/products/` — Listar productos (público)
- `POST /api/products/` — Crear producto (solo admin, protegido)
- `POST /api/orders/` — Crear pedido (protegido)
- `GET /api/orders/` — Listar pedidos del usuario (protegido)

## 🏗️ Estructura de carpetas
```
container/
  api/         # Lógica de negocio, modelos, routers, schemas
  ecommerce/   # Configuración Django
  frontend/    # Frontend JS y HTML
  requirements.txt
```

## ⚙️ Cómo ejecutar localmente
1. Clona el repositorio y entra en la carpeta `container`
2. Instala dependencias:
   ```sh
   pip install -r requirements.txt
   ```
3. Crea un archivo `.env` con tus variables (ejemplo):
   ```env
   SECRET_KEY=tu_clave_secreta
   DEBUG=True
   DATABASE_URL=postgres://usuario:password@host:puerto/dbname
   ```
4. Aplica migraciones:
   ```sh
   python manage.py migrate
   ```
5. Ejecuta el servidor:
   ```sh
   python manage.py runserver
   ```
6. Abre `frontend/index.html` en tu navegador para probar la interfaz (no requiere build, solo abrir el archivo).

## 🧑‍💻 Notas para desarrolladores
- El login requiere obtener la clave pública (`/api/users/public-key`) y cifrar la contraseña en el frontend (ver `main.js`).
- El refresh token se maneja solo por cookie HttpOnly, nunca en JS.
- El backend valida stock y realiza operaciones de pedido de forma atómica.
- El código ha sido limpiado de prints y logs de debug.
- El frontend no usa frameworks, solo JS moderno y fetch API.

## 🌐 Despliegue
- Preparado para Render, Heroku y otros PaaS.
- Usa WhiteNoise para servir estáticos.
- Configuración segura de variables y base de datos por entorno.

---