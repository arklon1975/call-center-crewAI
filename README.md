# 🎧 Sistema de Call Center Multi-Agente con CrewAI

Un sistema completo de call center inteligente que utiliza múltiples agentes de IA para gestionar conversaciones con clientes, con autenticación segura, envío de emails y monitoreo en tiempo real.

## 🌟 Características Principales

### 🤖 Agentes de IA Inteligentes
- **Agente de Atención al Cliente**: Maneja consultas generales y resuelve problemas
- **Agente de Enrutamiento**: Dirige las llamadas al departamento correcto
- **Agente Supervisor**: Gestiona escalaciones y casos complejos
- **Integración con OpenAI GPT-4o**: Respuestas inteligentes y contextuales

### 🔐 Sistema de Autenticación Seguro
- Autenticación JWT con cookies httpOnly
- Roles de usuario (Admin, Supervisor, Agente, Viewer)
- Gestión de sesiones y tokens de refresco
- Bloqueo automático por intentos fallidos

### 📧 Sistema de Emails Automático
- Envío de resúmenes de conversación
- Información solicitada por el cliente
- Emails de seguimiento
- Confirmación del cliente antes del envío
- Plantillas HTML profesionales

### 📊 Dashboard en Tiempo Real
- Monitoreo de llamadas activas
- Estado de agentes
- Métricas de rendimiento
- Colas por departamento
- Gráficos interactivos

### 🗄️ Base de Datos Robusta
- SQLite para desarrollo (configurable para PostgreSQL)
- Gestión de usuarios, llamadas y logs
- Historial completo de conversaciones
- Métricas de calidad

## 🚀 Tecnologías Utilizadas

- **Backend**: FastAPI (Python 3.11+)
- **IA**: CrewAI + OpenAI GPT-4o
- **Base de Datos**: SQLite/PostgreSQL
- **Autenticación**: JWT + bcrypt
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Email**: FastAPI-Mail
- **Templates**: Jinja2

## 📋 Requisitos Previos

- Python 3.11 o superior
- pip o uv (gestor de paquetes)
- Cuenta de OpenAI con API key
- Servidor SMTP para envío de emails (opcional)

## 🛠️ Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/call-center-system.git
cd call-center-system
```

### 2. Instalar Dependencias

```bash
# Usando pip
pip install -r requirements.txt

# O usando uv (recomendado)
uv sync
```

### 3. Configurar Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
# Configuración de Seguridad
SECRET_KEY=tu-clave-secreta-super-segura-aqui
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Configuración de OpenAI
OPENAI_API_KEY=tu-api-key-de-openai

# Configuración de Base de Datos
DATABASE_URL=sqlite:///call_center.db
# Para PostgreSQL: postgresql://username:password@localhost/call_center

# Configuración de Redis (opcional)
REDIS_URL=redis://localhost:6379

# Configuración de Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Configuración CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000

# Configuración del Entorno
ENVIRONMENT=development
PORT=5000

# Configuración SMTP para Emails
MAIL_USERNAME=tu_usuario@tudominio.com
MAIL_PASSWORD=tu_contraseña_de_email
MAIL_FROM=tu_usuario@tudominio.com
MAIL_SERVER=smtp.tudominio.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
SUPPORT_EMAIL=soporte@tudominio.com
```

### 4. Inicializar la Base de Datos

```bash
python init_db.py
```

### 5. Ejecutar la Aplicación

```bash
# Desarrollo
uvicorn main:app --host 0.0.0.0 --port 5000 --reload

# Producción
uvicorn main:app --host 0.0.0.0 --port 5000
```

## 🔧 Configuración Detallada

### Configuración de OpenAI

1. Obtén tu API key en [OpenAI Platform](https://platform.openai.com/)
2. Agrega la key al archivo `.env`
3. El sistema usará automáticamente GPT-4o para las respuestas

### Configuración de Email

#### Gmail
```env
MAIL_USERNAME=tuusuario@gmail.com
MAIL_PASSWORD=contraseña_de_aplicacion
MAIL_FROM=tuusuario@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
```

#### Outlook/Hotmail
```env
MAIL_USERNAME=tuusuario@outlook.com
MAIL_PASSWORD=tu_contraseña
MAIL_FROM=tuusuario@outlook.com
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
```

### Configuración de Base de Datos

#### SQLite (Desarrollo)
```env
DATABASE_URL=sqlite:///call_center.db
```

#### PostgreSQL (Producción)
```env
DATABASE_URL=postgresql://username:password@localhost/call_center
```

## 👥 Usuarios por Defecto

Al inicializar el sistema, se crea automáticamente un usuario administrador:

- **Usuario**: `admin`
- **Contraseña**: `Admin123!`
- **Email**: `admin@callcenter.com`

⚠️ **Importante**: Cambia la contraseña después del primer inicio de sesión.

## 🎯 Uso del Sistema

### 1. Acceso al Sistema

1. Navega a `http://localhost:5000`
2. Inicia sesión con las credenciales de administrador
3. Serás redirigido al dashboard principal

### 2. Gestión de Usuarios

- **Admin**: Puede crear, editar y gestionar todos los usuarios
- **Supervisor**: Puede monitorear agentes y gestionar escalaciones
- **Agente**: Puede manejar llamadas y conversaciones
- **Viewer**: Solo puede ver reportes y métricas

### 3. Manejo de Llamadas

1. **Iniciar Llamada**: Desde el dashboard, inicia una nueva llamada
2. **Enrutamiento Automático**: El sistema dirige la llamada al departamento correcto
3. **Conversación**: Los agentes de IA manejan la conversación
4. **Escalación**: Casos complejos se escalan automáticamente al supervisor
5. **Finalización**: Registra el resultado y métricas de calidad

### 4. Envío de Emails

1. Accede a "Gestión de Emails" desde el menú
2. Selecciona el tipo de email (resumen, información, seguimiento)
3. Completa los datos del cliente y la información
4. **Confirma que el cliente desea recibir el email**
5. Revisa la vista previa y envía

### 5. Monitoreo y Reportes

- **Dashboard en Tiempo Real**: Estado de llamadas y agentes
- **Métricas de Rendimiento**: Tiempo de respuesta, satisfacción
- **Reportes de Calidad**: Evaluación de conversaciones
- **Análisis de Tendencias**: Patrones y mejoras

## 📁 Estructura del Proyecto

```
call-center-system/
├── main.py                 # Punto de entrada principal
├── config.py              # Configuración del sistema
├── crew_manager.py        # Gestión de agentes CrewAI
├── email_service.py       # Servicio de envío de emails
├── init_db.py            # Inicialización de base de datos
├── pyproject.toml        # Dependencias del proyecto
├── requirements.txt      # Dependencias (alternativo)
├── .env                 # Variables de entorno
├── .env.example         # Ejemplo de variables de entorno
├── README.md            # Este archivo
├── SECURITY.md          # Guía de seguridad
├── auth/                # Módulo de autenticación
│   ├── auth_utils.py    # Utilidades de autenticación
│   ├── dependencies.py  # Dependencias de FastAPI
│   ├── models.py        # Modelos de usuario
│   └── routes.py        # Rutas de autenticación
├── api/                 # API REST
│   ├── routes.py        # Rutas principales
│   └── email_routes.py  # Rutas de email
├── agents/              # Agentes de IA
│   ├── customer_service_agent.py
│   ├── call_routing_agent.py
│   └── supervisor_agent.py
├── database/            # Base de datos
│   ├── database.py      # Configuración de BD
│   └── models.py        # Modelos de datos
├── templates/           # Plantillas HTML
│   ├── emails/          # Plantillas de email
│   ├── login.html       # Página de login
│   ├── dashboard.html   # Dashboard principal
│   ├── index.html       # Página principal
│   └── email_manager.html # Gestión de emails
└── static/              # Archivos estáticos
    ├── style.css        # Estilos CSS
    └── dashboard.js     # JavaScript del dashboard
```

## 🔒 Seguridad

### Características de Seguridad Implementadas

- **Autenticación JWT**: Tokens seguros con expiración
- **Cookies httpOnly**: Protección contra XSS
- **Rate Limiting**: Prevención de ataques de fuerza bruta
- **Validación de Entrada**: Sanitización de datos
- **Headers de Seguridad**: Protección adicional
- **Contraseñas Hasheadas**: bcrypt para almacenamiento seguro

### Configuración de Producción

1. **Cambiar credenciales por defecto**
2. **Configurar HTTPS**
3. **Usar base de datos PostgreSQL**
4. **Configurar Redis para sesiones**
5. **Revisar SECURITY.md para más detalles**

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests de autenticación
python test_auth.py

# Tests básicos
python test_simple.py

# Tests rápidos
python quick_test.py
```

### Verificar Funcionalidad

1. **Health Check**: `GET /health`
2. **Login**: `POST /api/auth/login`
3. **Dashboard**: `GET /dashboard`
4. **Email Status**: `GET /api/email/status`

## 🚀 Despliegue

### Docker (Recomendado)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
```

### Nginx + Gunicorn

```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar con gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
```

### Variables de Entorno de Producción

```env
ENVIRONMENT=production
SECRET_KEY=clave-super-secreta-generada-con-openssl
DATABASE_URL=postgresql://user:pass@localhost/callcenter
REDIS_URL=redis://localhost:6379
ALLOWED_ORIGINS=https://tudominio.com
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

### Problemas Comunes

1. **Error de OpenAI API**: Verifica tu API key en `.env`
2. **Error de Email**: Configura correctamente las variables SMTP
3. **Error de Base de Datos**: Ejecuta `python init_db.py`
4. **Error de Autenticación**: Verifica las credenciales por defecto

### Contacto

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/call-center-system/issues)
- **Email**: soporte@callcenter.com
- **Documentación**: [Wiki del Proyecto](https://github.com/tu-usuario/call-center-system/wiki)

## 🔄 Changelog

### v1.0.0 (2024-12-22)
- ✅ Sistema de autenticación JWT con cookies
- ✅ Agentes de IA con CrewAI
- ✅ Sistema de envío de emails
- ✅ Dashboard en tiempo real
- ✅ Gestión de usuarios y roles
- ✅ Base de datos SQLite/PostgreSQL
- ✅ Plantillas HTML profesionales
- ✅ API REST completa
- ✅ Monitoreo y métricas

## 🙏 Agradecimientos

- [CrewAI](https://github.com/joaomdmoura/crewAI) por el framework de agentes
- [FastAPI](https://fastapi.tiangolo.com/) por el framework web
- [OpenAI](https://openai.com/) por los modelos de IA
- [Bootstrap](https://getbootstrap.com/) por el diseño responsive

---

**¡Gracias por usar nuestro Sistema de Call Center Multi-Agente! 🎉** 