# 🔒 Guía de Seguridad - Sistema de Call Center

## ⚠️ Información de Seguridad

Este documento contiene información importante sobre la seguridad del Sistema de Call Center Multi-Agente.

## 🛡️ Características de Seguridad Implementadas

### Autenticación y Autorización

- **JWT Tokens**: Tokens seguros con expiración configurable
- **Cookies httpOnly**: Protección contra ataques XSS
- **Refresh Tokens**: Renovación automática de sesiones
- **Rate Limiting**: Prevención de ataques de fuerza bruta
- **Roles de Usuario**: Control granular de permisos
- **Contraseñas Hasheadas**: bcrypt con salt único

### Protección de Datos

- **Validación de Entrada**: Sanitización de todos los datos de entrada
- **Headers de Seguridad**: Configuración de headers HTTP seguros
- **CORS Configurado**: Control de orígenes permitidos
- **SQL Injection Protection**: Uso de ORM con parámetros preparados
- **XSS Protection**: Escape automático de contenido HTML

### Configuración de Producción

#### Variables de Entorno Críticas

```env
# OBLIGATORIO: Cambiar en producción
SECRET_KEY=generar-con-openssl-rand-hex-32
OPENAI_API_KEY=tu-api-key-secreta

# Configuración de seguridad
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# CORS - Solo dominios confiables
ALLOWED_ORIGINS=https://tudominio.com,https://www.tudominio.com
```

#### Generación de Secret Key Segura

```bash
# Generar una clave secreta segura
openssl rand -hex 32

# O usando Python
python -c "import secrets; print(secrets.token_hex(32))"
```

## 🚨 Configuración de Seguridad para Producción

### 1. Cambiar Credenciales por Defecto

**IMPORTANTE**: El sistema viene con un usuario administrador por defecto:

- Usuario: `admin`
- Contraseña: `Admin123!`
- Email: `admin@callcenter.com`

**OBLIGATORIO**: Cambiar estas credenciales inmediatamente después de la instalación.

### 2. Configurar HTTPS

```nginx
# Configuración Nginx con SSL
server {
    listen 443 ssl http2;
    server_name tudominio.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Configurar Firewall

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirección a HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# iptables (CentOS/RHEL)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### 4. Configurar Base de Datos Segura

```env
# PostgreSQL con SSL
DATABASE_URL=postgresql://user:pass@localhost/callcenter?sslmode=require

# Usar usuario dedicado (no root)
# Crear usuario específico para la aplicación
CREATE USER callcenter_user WITH PASSWORD 'password_segura';
GRANT CONNECT ON DATABASE callcenter TO callcenter_user;
GRANT USAGE ON SCHEMA public TO callcenter_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO callcenter_user;
```

### 5. Configurar Redis Seguro

```env
# Redis con autenticación
REDIS_URL=redis://:password@localhost:6379

# Configuración redis.conf
requirepass tu_password_seguro
bind 127.0.0.1
protected-mode yes
```

## 🔍 Auditoría de Seguridad

### Verificaciones Periódicas

1. **Revisar logs de acceso**:
   ```bash
   tail -f /var/log/nginx/access.log
   tail -f /var/log/nginx/error.log
   ```

2. **Verificar intentos de login fallidos**:
   ```sql
   SELECT * FROM auth_logs WHERE success = false ORDER BY timestamp DESC;
   ```

3. **Revisar tokens expirados**:
   ```sql
   SELECT COUNT(*) FROM refresh_tokens WHERE expires_at < NOW();
   ```

4. **Monitorear uso de API**:
   ```bash
   # Verificar uso de OpenAI API
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/usage
   ```

### Escaneo de Vulnerabilidades

```bash
# Instalar herramientas de seguridad
pip install safety bandit

# Verificar dependencias
safety check

# Análisis estático de código
bandit -r . -f json -o bandit-report.json
```

## 🚨 Respuesta a Incidentes

### Detección de Intrusión

1. **Bloquear IP sospechosa**:
   ```bash
   sudo ufw deny from IP_SOSPECHOSA
   ```

2. **Revisar logs de autenticación**:
   ```sql
   SELECT * FROM auth_logs 
   WHERE ip_address = 'IP_SOSPECHOSA' 
   ORDER BY timestamp DESC;
   ```

3. **Invalidar sesiones**:
   ```sql
   DELETE FROM refresh_tokens WHERE user_id = USER_ID_SOSPECHOSO;
   ```

### Recuperación

1. **Cambiar todas las contraseñas**
2. **Regenerar secret keys**
3. **Revisar integridad de la base de datos**
4. **Actualizar certificados SSL**
5. **Notificar a usuarios afectados**

## 📋 Checklist de Seguridad

### Instalación Inicial
- [ ] Cambiar credenciales por defecto
- [ ] Configurar HTTPS
- [ ] Generar secret key segura
- [ ] Configurar firewall
- [ ] Configurar base de datos segura
- [ ] Configurar Redis con autenticación

### Mantenimiento Periódico
- [ ] Actualizar dependencias mensualmente
- [ ] Revisar logs de seguridad semanalmente
- [ ] Rotar secret keys trimestralmente
- [ ] Actualizar certificados SSL
- [ ] Revisar permisos de usuarios
- [ ] Hacer backup de configuración

### Monitoreo Continuo
- [ ] Configurar alertas de login fallidos
- [ ] Monitorear uso de API
- [ ] Revisar métricas de rendimiento
- [ ] Verificar integridad de archivos
- [ ] Monitorear espacio en disco

## 📞 Contacto de Seguridad

Si descubres una vulnerabilidad de seguridad:

1. **NO** la reportes públicamente
2. Envía un email a: security@callcenter.com
3. Incluye detalles técnicos del problema
4. Espera confirmación antes de publicar

### Información a Incluir

- Descripción detallada de la vulnerabilidad
- Pasos para reproducir el problema
- Impacto potencial
- Sugerencias de mitigación
- Tu información de contacto

## 📚 Recursos Adicionales

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Recuerda**: La seguridad es responsabilidad de todos. Mantén tu sistema actualizado y monitoreado constantemente. 