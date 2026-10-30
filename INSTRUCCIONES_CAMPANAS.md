# Módulo Campañas: puesta en marcha

## 1. Cuenta de correo desde la que se envía

**Si usan Gmail o Google Workspace:**
1. En la cuenta que va a enviar: activar la *Verificación en 2 pasos*.
2. Ir a https://myaccount.google.com/apppasswords, crear una "contraseña de aplicación" (nombre: CRM) y copiar los 16 caracteres.

**Si usan otro proveedor** (correo del hosting, Outlook, etc.): pedir servidor SMTP, puerto, usuario y contraseña.

## 2. Agregar al final de `.streamlit/secrets.toml`

En la PC (y también en *Settings → Secrets* de Streamlit Cloud si la app está publicada ahí):

```toml
[email]
smtp_server = "smtp.gmail.com"      # Outlook: smtp.office365.com / puerto 587
smtp_port = 465
usuario = "ventas@dicadamerica.com" # cuenta que envía
password = "xxxx xxxx xxxx xxxx"    # contraseña de aplicación
nombre = "DICAD AMÉRICA"            # nombre que ve el cliente como remitente
firma = """Roberto Gómez
Asesor Comercial · DICAD AMÉRICA
STRAKON – Software de diseño estructural
+54 9 11 0000-0000 · www.dicad.com"""

# OPCIONAL: que cada asesor envíe desde su propia casilla.
# Si un asesor no figura acá, usa la cuenta general de arriba.
[email.cuentas."Ricardo Ippolito"]
usuario = "ricardo@dicadamerica.com"
password = "xxxx xxxx xxxx xxxx"
nombre = "Ricardo Ippolito · DICAD AMÉRICA"
firma = """Ricardo Ippolito
DICAD AMÉRICA"""
```

`secrets.toml` no debe subirse a GitHub (debe estar en `.gitignore`).

## 3. Cómo se usa (menú lateral → **Campañas**)

1. **Segmento**: filtrar por asesor, estado, país, profesión. Se excluyen solos los que pidieron baja.
2. **Correo**: editar asunto y texto con variables (`{saludo}`, `{empresa}`, `{profesion}`, `{asesor}`…), corregir el *Saludo* en la tabla (ej. "Juan Carlos"), **enviarse una prueba**, confirmar y enviar. Va despacio a propósito (15 s entre correos).
3. **WhatsApp**: botón por contacto que abre el chat con el mensaje ya escrito; se toca Enviar y luego "Registrar enviado".
4. **LinkedIn**: texto listo para copiar + búsqueda del perfil; se pega en LinkedIn y se registra.
5. **Historial y Bajas**: todo lo enviado, y la lista de no contactar.

Las hojas `Campanas_Log` y `Bajas` se crean solas en el mismo Google Sheet al primer envío.

## 4. Buenas prácticas
- Gmail personal: máx. ~500 correos/día; Workspace: ~2.000. Empezar con 20–50 por día.
- Configurar SPF/DKIM/DMARC del dominio (lo hace quien administra el correo/hosting).
- Incluir siempre la opción de baja (ya va al pie de cada correo) y respetarla (Ley 25.326).
