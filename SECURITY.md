# 🔒 Guía de Seguridad - Call Center System

## Características de Seguridad Implementadas

### 1. **Autenticación y Autorización**

#### ✅ **JWT (JSON Web Tokens)**
- Tokens de acceso con expiración de 30 minutos
- Tokens de refresh con expiración de 7 días
- Algoritmo HS256 para firma de tokens
- Validación automática de tokens en cada request

#### ✅ **Sistema de Roles**
- **Admin**: Acceso completo al sistema
- **Supervisor**: Gestión de agentes y métricas
- **Agent**: Operaciones básicas de call center
- **Viewer**: Solo lectura

#### ✅ **Protección de Contraseñas**
- Hash bcrypt con salt automático
- Validación de fortaleza de contraseña
- Política de contraseñas seguras:
  - Mínimo 8 caracteres
  - Al menos 1 mayúscula
  - Al menos 1 minúscula
  - Al menos 1 número
  - Al menos 1 carácter especial

### 2. **Protección contra Ataques**

#### ✅ **Protección contra Fuerza Bruta**
- Bloqueo de cuenta después de 5 intentos fallidos
- Bloqueo temporal de 30 minutos
- Registro de intentos de login fallidos

#### ✅ **Gestión de Sesiones**
- Seguimiento de sesiones activas
- Invalidación de sesiones al cambiar contraseña
- Información de IP y User-Agent por sesión
- Logout que invalida todas las sesiones

#### ✅ **Headers de Seguridad**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security` (en producción)

### 3. **Configuración Segura**

#### ✅ **Variables de Entorno**
- API keys y secretos en variables de entorno
- Configuración separada por ambiente
- Validación de variables requeridas

#### ✅ **CORS Configurado**
- Orígenes permitidos específicos
- Credenciales habilitadas solo para dominios confiables

#### ✅ **Logging de Seguridad**
- Registro de todos los requests
- Logging de eventos de autenticación
- Timestamps y información de contexto

## 🚨 Configuración de Producción

### Variables de Entorno Críticas

```bash
# Generar clave secreta segura
SECRET_KEY=$(openssl rand -hex 32)

# Configurar base de datos segura
DATABASE_URL=postgresql://user:password@localhost/callcenter

# Configurar Redis para sesiones
REDIS_URL=redis://localhost:6379

# Configurar CORS restrictivo
ALLOWED_ORIGINS=https://yourdomain.com

# Configurar ambiente
ENVIRONMENT=production
```

### Configuración de Base de Datos

#### PostgreSQL (Recomendado para Producción)
```bash
# Instalar PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Crear base de datos
sudo -u postgres createdb callcenter
sudo -u postgres createuser callcenter_user

# Configurar permisos
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE callcenter TO callcenter_user;
ALTER USER callcenter_user PASSWORD 'secure_password';
```

### Configuración de HTTPS

#### Con Nginx
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🛡️ Mejores Prácticas de Seguridad

### Para Administradores

1. **Cambiar Credenciales por Defecto**
   ```bash
   # Cambiar inmediatamente después de la instalación
   Usuario: admin
   Contraseña: Admin123! → [Nueva contraseña segura]
   ```

2. **Gestión de Usuarios**
   - Crear usuarios específicos para cada persona
   - Asignar roles mínimos necesarios
   - Revisar y desactivar usuarios inactivos

3. **Monitoreo de Seguridad**
   - Revisar logs de autenticación regularmente
   - Monitorear sesiones activas
   - Configurar alertas para actividad sospechosa

### Para Desarrolladores

1. **Manejo de Secretos**
   ```python
   # ❌ NUNCA hacer esto
   SECRET_KEY = "mi-clave-secreta"
   
   # ✅ Usar variables de entorno
   SECRET_KEY = os.getenv("SECRET_KEY")
   ```

2. **Validación de Entrada**
   ```python
   # ✅ Validar todos los inputs
   from pydantic import BaseModel, validator
   
   class UserInput(BaseModel):
       username: str
       
       @validator('username')
       def validate_username(cls, v):
           if len(v) < 3:
               raise ValueError('Username too short')
           return v
   ```

3. **Manejo de Errores**
   ```python
   # ❌ No exponer información sensible
   except Exception as e:
       return {"error": str(e)}  # Puede exponer información
   
   # ✅ Mensajes de error genéricos
   except Exception as e:
       logger.error(f"Error: {e}")
       return {"error": "Internal server error"}
   ```

## 🔍 Auditoría de Seguridad

### Checklist de Seguridad

- [ ] Credenciales por defecto cambiadas
- [ ] Variables de entorno configuradas
- [ ] HTTPS habilitado en producción
- [ ] Base de datos con autenticación
- [ ] Logs de seguridad configurados
- [ ] Backups automáticos configurados
- [ ] Firewall configurado
- [ ] Actualizaciones de seguridad aplicadas

### Herramientas de Auditoría

```bash
# Escanear dependencias vulnerables
pip install safety
safety check

# Análisis de código estático
pip install bandit
bandit -r .

# Verificar configuración SSL
nmap --script ssl-enum-ciphers -p 443 yourdomain.com
```

## 🚨 Respuesta a Incidentes

### En caso de Compromiso de Seguridad

1. **Acción Inmediata**
   - Cambiar todas las contraseñas
   - Invalidar todas las sesiones activas
   - Revisar logs de acceso

2. **Investigación**
   - Identificar el vector de ataque
   - Determinar el alcance del compromiso
   - Documentar el incidente

3. **Recuperación**
   - Aplicar parches de seguridad
   - Restaurar desde backup si es necesario
   - Implementar medidas adicionales

## 📞 Contacto de Seguridad

Para reportar vulnerabilidades de seguridad:
- Email: security@callcenter.com
- Respuesta esperada: 24-48 horas
- Divulgación responsable apreciada

---

**Última actualización**: Diciembre 2024  
**Versión del documento**: 1.0 