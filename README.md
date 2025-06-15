# Ecommerce API - Django Ninja Portfolio Project

Este proyecto es una API RESTful para un sistema de ecommerce, desarrollada como parte de mi portfolio profesional.  El objetivo es mostrar habilidades técnicas en herramientas como Django, Django Ninja, autenticación JWT, PostgreSQL, buenas prácticas de seguridad y despliegue moderno.

## 🚀 Stack Tecnológico
- **Python 3.12**
- **Django 5.2**
- **Django Ninja** (framework API basado en FastAPI)
- **JWT Authentication** (django-ninja-jwt)
- **PostgreSQL** (usando dj-database-url y psycopg2)
- **WhiteNoise** (servir archivos estáticos en producción)
- **Gunicorn** (WSGI server para producción)

## 📦 Dependencias principales
```
Django, django-ninja, django-ninja-jwt, dj-database-url, psycopg2-binary, whitenoise, gunicorn, python-dotenv, pydantic
```
Ver `requirements.txt` para la lista completa.

## 🛠️ Funcionalidades principales
- **Registro y login de usuarios con email** (modelo de usuario personalizado)
- **Autenticación JWT segura** (login, refresh, endpoints protegidos)
- **Gestión de productos** (listar, crear, consultar)
- **Gestión de pedidos y sus items** (crear pedido, listar pedidos, consultar pedido)
- **Permisos de admin para creación de productos**
- **Buenas prácticas de seguridad y organización de código**

## 🔒 Endpoints principales
- `POST /api/users/register` — Registro de usuario
- `POST /api/users/token` — Login (devuelve access y refresh token)
- `POST /api/users/token/refresh` — Refrescar token
- `GET /api/products/` — Listar productos (público)
- `POST /api/products/` — Crear producto (solo admin, protegido)
- `POST /api/orders/` — Crear pedido (protegido)
- `GET /api/orders/` — Listar pedidos del usuario (protegido)

## 🏗️ Estructura de carpetas
```
container/
  api/         # Lógica de negocio, modelos, routers, schemas
  ecommerce/   # Configuración Django
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

## 🌐 Despliegue
- Preparado para Render, Heroku y otros PaaS.
- Usa WhiteNoise para servir estáticos.
- Configuración segura de variables y base de datos por entorno.

## 💡 Habilidades demostradas
- Django avanzado y modelos personalizados
- APIs RESTful modernas y tipadas
- Seguridad con JWT y buenas prácticas
- Uso profesional de variables de entorno y despliegue cloud
- Código limpio, mantenible y documentado

---