# -*- coding: utf-8 -*-
"""
Módulo de CAMPAÑAS para el CRM DICAD AMÉRICA.
Envíos personalizados por Correo (automático), WhatsApp y LinkedIn (asistidos).

Requiere en .streamlit/secrets.toml una sección [email] (ver INSTRUCCIONES_CAMPANAS.md).
Usa dos hojas nuevas en el mismo Google Sheet (se crean solas al primer uso):
  - "Campanas_Log": historial de todo lo enviado / registrado.
  - "Bajas": emails o teléfonos que pidieron no recibir más mensajes.
"""
import re
import ssl
import time
import smtplib
import urllib.parse
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

import pandas as pd
import streamlit as st

COLUMNS_LOG = ["Fecha", "Asesor", "Canal", "Campaña", "Cliente", "Empresa", "Contacto", "Estado", "Detalle"]
COLUMNS_BAJAS = ["Contacto", "Fecha", "Motivo"]
PREFIJOS_INSTITUCIONES = ('COLEGIO', 'CONSEJO', 'UNIVERSIDAD', 'FACULTAD', 'CAMARA', 'CÁMARA')

VARIABLES_AYUDA = ("**Variables disponibles:** `{saludo}` (nombre para el saludo, editable en la tabla), "
                   "`{cliente}` (nombre completo), `{empresa}`, `{profesion}`, `{cargo}`, `{pais}`, `{ciudad}`, `{asesor}`")

PLANTILLA_EMAIL_ASUNTO = "{saludo}, una herramienta para acelerar sus proyectos estructurales"
PLANTILLA_EMAIL_CUERPO = """Estimado/a {saludo}:

Mi nombre es {asesor} y me comunico de DICAD AMÉRICA, empresa de software de diseño estructural, con su producto STRAKON, con el cual colaboramos con profesionales de la construcción en toda América para reducir tiempos de documentación y errores en obra.

Me gustaría mostrarle en una breve videollamada de 20 minutos cómo STRAKON podría aplicarse a los proyectos de {empresa}.

¿Tendría disponibilidad esta semana o la próxima?

Saludos cordiales,"""

PLANTILLA_WHATSAPP = ("Hola {saludo}, ¿cómo está? Le escribe {asesor} de DICAD AMÉRICA. "
                      "Le había enviado información sobre STRAKON, nuestro software de diseño estructural. "
                      "¿Le parece si coordinamos una breve demo de 20 minutos?")

PLANTILLA_LINKEDIN = ("Hola {saludo}, soy {asesor} de DICAD AMÉRICA. Trabajamos con profesionales de la "
                      "construcción con STRAKON, software de diseño y detallado estructural. "
                      "Me gustaría sumarlo a mi red y compartirle algunos casos que pueden interesarle para {empresa}.")

PIE_BAJA = "Si no desea recibir más comunicaciones de DICAD AMÉRICA, responda este correo con la palabra BAJA."


# ---------------------------------------------------------------- utilidades
class _Seguro(dict):
    """Si una variable no existe en la plantilla, la deja vacía en vez de romper."""
    def __missing__(self, key):
        return ""


def _txt(v):
    s = "" if v is None else str(v).strip()
    return "" if s.lower() in ("nan", "none", "#error!") else s


def saludo_sugerido(cliente):
    """Primer nombre con mayúscula inicial. Se puede corregir a mano en la tabla (ej. 'Juan Carlos')."""
    partes = _txt(cliente).split()
    return partes[0].capitalize() if partes else ""


def completar(plantilla, row, saludo, asesor):
    datos = _Seguro(
        saludo=saludo or saludo_sugerido(row.get("Cliente")),
        cliente=_txt(row.get("Cliente")),
        empresa=_txt(row.get("Empresa")) or "su empresa",
        profesion=_txt(row.get("Profesion")),
        cargo=_txt(row.get("Cargo")),
        pais=_txt(row.get("Pais")),
        ciudad=_txt(row.get("Ciudad")),
        asesor=asesor,
    )
    try:
        return plantilla.format_map(datos)
    except (ValueError, IndexError):
        return plantilla  # llaves sueltas en el texto: se envía tal cual


def email_valido(e):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", _txt(e)))


def telefono_whatsapp(tel):
    """Deja solo dígitos con código de país (wa.me no acepta '+', espacios ni guiones)."""
    dig = re.sub(r"\D", "", _txt(tel))
    if dig.startswith("00"):
        dig = dig[2:]
    return dig if len(dig) >= 8 else ""


def _leer_hoja(conn, nombre, columnas):
    try:
        d = conn.read(worksheet=nombre, ttl=0)
        if d is None or d.empty:
            return pd.DataFrame(columns=columnas)
        d.columns = d.columns.astype(str).str.strip()
        for c in columnas:
            if c not in d.columns:
                d[c] = ""
        return d[columnas].dropna(how="all").fillna("")
    except Exception:
        return pd.DataFrame(columns=columnas)


def _escribir_hoja(conn, nombre, data):
    data = data.astype(str)
    for intento in range(3):
        try:
            conn.update(worksheet=nombre, data=data, spreadsheet=st.secrets.get("SHEET_URL") or None)
            return True
        except Exception:
            try:
                conn.create(worksheet=nombre, data=data, spreadsheet=st.secrets.get("SHEET_URL") or None)
                return True
            except Exception:
                time.sleep(1.5)
    st.error(f"🚨 No pude guardar en la hoja '{nombre}'. Revisá la conexión con Google Sheets.")
    return False


def registrar(conn, filas):
    """Agrega filas al historial Campanas_Log."""
    if not filas:
        return
    log = _leer_hoja(conn, "Campanas_Log", COLUMNS_LOG)
    _escribir_hoja(conn, "Campanas_Log", pd.concat([log, pd.DataFrame(filas, columns=COLUMNS_LOG)], ignore_index=True))


def _fila_log(asesor, canal, campana, row, contacto, estado, detalle=""):
    return [datetime.now().strftime("%d/%m/%Y %H:%M"), asesor, canal, campana,
            _txt(row.get("Cliente")), _txt(row.get("Empresa")), contacto, estado, detalle]


# ---------------------------------------------------------------- correo
def cuenta_correo(usuario_actual):
    """Cuenta SMTP del asesor (si tiene una propia en secrets) o la general."""
    try:
        if "email" not in st.secrets:
            return None
    except Exception:
        return None
    cfg = dict(st.secrets["email"])
    cuentas = cfg.pop("cuentas", {}) or {}
    propia = cuentas.get(usuario_actual)
    if propia:
        cfg.update(dict(propia))
    if not cfg.get("usuario") or not cfg.get("password"):
        return None
    cfg.setdefault("smtp_server", "smtp.gmail.com")
    cfg.setdefault("smtp_port", 465)
    cfg.setdefault("nombre", usuario_actual)
    return cfg


def _html(texto, firma):
    esc = (texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    cuerpo = esc.replace("\n", "<br>")
    firma_html = firma.replace("\n", "<br>") if firma else ""
    return (f'<div style="font-family:Arial,sans-serif;font-size:14px;color:#222;line-height:1.5">{cuerpo}'
            f'<br><br>{firma_html}'
            f'<br><br><span style="font-size:11px;color:#888">{PIE_BAJA}</span></div>')


def armar_mensaje(cfg, destino, asunto, cuerpo):
    firma = _txt(cfg.get("firma"))
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((cfg["nombre"], cfg["usuario"]))
    msg["To"] = destino
    msg["Subject"] = asunto
    msg["Reply-To"] = cfg.get("responder_a", cfg["usuario"])
    msg["Message-ID"] = make_msgid(domain=cfg["usuario"].split("@")[-1])
    msg["List-Unsubscribe"] = f"<mailto:{cfg.get('responder_a', cfg['usuario'])}?subject=BAJA>"
    texto_plano = f"{cuerpo}\n\n{firma}\n\n{PIE_BAJA}"
    msg.attach(MIMEText(texto_plano, "plain", "utf-8"))
    msg.attach(MIMEText(_html(cuerpo, firma), "html", "utf-8"))
    return msg


def conectar_smtp(cfg):
    puerto = int(cfg["smtp_port"])
    ctx = ssl.create_default_context()
    if puerto == 465:
        srv = smtplib.SMTP_SSL(cfg["smtp_server"], puerto, context=ctx, timeout=30)
    else:
        srv = smtplib.SMTP(cfg["smtp_server"], puerto, timeout=30)
        srv.starttls(context=ctx)
    srv.login(cfg["usuario"], cfg["password"])
    return srv


# ---------------------------------------------------------------- pantalla
def render_campanas(df, conn, usuario_actual, es_admin, lista_asesores):
    st.markdown("## 📣 Campañas: Correo · WhatsApp · LinkedIn")
    st.caption("Mensajes personalizados con los datos de cada contacto. Todo queda registrado en la hoja *Campanas_Log*.")

    # ---------- Segmento (común a los 3 canales)
    with st.expander("🎯 1. Elegir a quién le escribimos", expanded=True):
        base = df.copy()
        for c in ["Cliente", "Empresa", "Profesion", "Pais", "Asesor", "Estado_Nego", "Email", "Telefono"]:
            if c not in base.columns:
                base[c] = ""
        base = base[base["Cliente"].astype(str).str.strip() != ""]
        base = base.drop_duplicates(subset=["Cliente"], keep="last")

        f1, f2, f3 = st.columns(3)
        idx_as = lista_asesores.index(usuario_actual) if usuario_actual in lista_asesores else 0
        asesor_f = f1.selectbox("Asesor (dueño del contacto)", lista_asesores, index=idx_as, key="camp_asesor")
        estados = sorted([e for e in base["Estado_Nego"].astype(str).unique() if _txt(e)])
        estado_f = f2.multiselect("Estado", estados, default=[e for e in ["Potencial", "En Proceso"] if e in estados], key="camp_estado")
        paises = sorted([p for p in base["Pais"].astype(str).unique() if _txt(p)])
        pais_f = f3.multiselect("País", paises, key="camp_pais")

        f4, f5, f6 = st.columns(3)
        profs = sorted([p for p in base["Profesion"].astype(str).unique() if _txt(p)])
        prof_f = f4.multiselect("Profesión", profs, key="camp_prof")
        busq = f5.text_input("Buscar cliente / empresa", key="camp_busq")
        incluir_inst = f6.checkbox("Incluir instituciones (colegios, universidades…)", value=False, key="camp_inst")

        if asesor_f != "Todos los Asesores":
            base = base[base["Asesor"] == asesor_f]
        if estado_f:
            base = base[base["Estado_Nego"].isin(estado_f)]
        if pais_f:
            base = base[base["Pais"].isin(pais_f)]
        if prof_f:
            base = base[base["Profesion"].isin(prof_f)]
        if busq:
            m = (base["Cliente"].astype(str).str.contains(busq, case=False, na=False)
                 | base["Empresa"].astype(str).str.contains(busq, case=False, na=False))
            base = base[m]
        if not incluir_inst:
            base = base[~base["Cliente"].astype(str).str.upper().str.startswith(PREFIJOS_INSTITUCIONES)]

        bajas = _leer_hoja(conn, "Bajas", COLUMNS_BAJAS)
        set_bajas = set(bajas["Contacto"].astype(str).str.strip().str.lower())
        if set_bajas:
            antes = len(base)
            base = base[~base["Email"].astype(str).str.strip().str.lower().isin(set_bajas)]
            base = base[~base["Telefono"].apply(telefono_whatsapp).isin(set_bajas)]
            if antes != len(base):
                st.caption(f"🚫 Se excluyeron {antes - len(base)} contactos que pidieron la baja.")

        st.metric("Contactos en el segmento", len(base))

    if base.empty:
        st.info("No hay contactos con esos filtros.")
        return

    campana = st.text_input("Nombre de la campaña (para el historial y para no repetir envíos)",
                            value=f"STRAKON {datetime.now().strftime('%m-%Y')}", key="camp_nombre")
    asesor_firma = usuario_actual
    log = _leer_hoja(conn, "Campanas_Log", COLUMNS_LOG)

    t_mail, t_wa, t_li, t_hist = st.tabs(["✉️ Correo (automático)", "💬 WhatsApp", "🔗 LinkedIn", "📜 Historial y Bajas"])

    # ================================================================ CORREO
    with t_mail:
        cfg = cuenta_correo(usuario_actual)
        if not cfg:
            st.error("Falta configurar la cuenta de correo en `.streamlit/secrets.toml` (sección `[email]`). "
                     "Ver INSTRUCCIONES_CAMPANAS.md.")
        else:
            st.caption(f"Se envía desde: **{cfg['nombre']} <{cfg['usuario']}>**")

        st.markdown(VARIABLES_AYUDA)
        asunto_tpl = st.text_input("Asunto", value=PLANTILLA_EMAIL_ASUNTO, key="mail_asunto")
        cuerpo_tpl = st.text_area("Mensaje", value=PLANTILLA_EMAIL_CUERPO, height=260, key="mail_cuerpo")

        cand = base[base["Email"].apply(email_valido)].copy()
        sin_mail = len(base) - len(cand)
        ya = set(log[(log["Canal"] == "Correo") & (log["Campaña"] == campana) & (log["Estado"] == "Enviado")]["Contacto"].astype(str).str.lower())
        omitir_repetidos = st.checkbox("No enviar a quienes ya recibieron esta campaña", value=True, key="mail_rep")
        if omitir_repetidos and ya:
            cand = cand[~cand["Email"].astype(str).str.strip().str.lower().isin(ya)]
        if sin_mail:
            st.caption(f"⚠️ {sin_mail} contactos del segmento no tienen email válido y se omiten.")

        tabla = pd.DataFrame({
            "Enviar": True,
            "Saludo": cand["Cliente"].apply(saludo_sugerido),
            "Cliente": cand["Cliente"].astype(str),
            "Empresa": cand["Empresa"].astype(str),
            "Email": cand["Email"].astype(str).str.strip(),
        }, index=cand.index)
        st.markdown("**2. Revisá la lista.** Podés corregir el *Saludo* (ej. 'Juan Carlos', 'Ing. Pérez') y destildar a quien no quieras escribirle.")
        editada = st.data_editor(
            tabla, hide_index=True, use_container_width=True, key="mail_tabla",
            column_config={"Enviar": st.column_config.CheckboxColumn(), "Saludo": st.column_config.TextColumn()},
            disabled=["Cliente", "Empresa", "Email"],
        )
        sel = editada[editada["Enviar"]]

        if not sel.empty:
            i0 = sel.index[0]
            st.markdown("**3. Vista previa (primer contacto):**")
            with st.container(border=True):
                st.markdown(f"**Para:** {sel.loc[i0, 'Email']}  \n**Asunto:** {completar(asunto_tpl, cand.loc[i0], sel.loc[i0, 'Saludo'], asesor_firma)}")
                st.text(completar(cuerpo_tpl, cand.loc[i0], sel.loc[i0, "Saludo"], asesor_firma))

        c1, c2, c3 = st.columns(3)
        limite = c1.number_input("Máximo a enviar en esta tanda", 1, 200, min(30, max(1, len(sel))), key="mail_lim")
        pausa = c2.number_input("Segundos entre correos", 5, 120, 15, key="mail_pausa",
                                help="Enviar despacio protege la reputación del dominio y evita caer en spam.")
        c3.caption(f"Seleccionados: **{len(sel)}**  \nTiempo estimado: ~{int(min(len(sel), limite) * pausa / 60) + 1} min")

        b1, b2 = st.columns(2)
        if b1.button("🧪 Enviarme una prueba a mí", use_container_width=True, disabled=(not cfg or sel.empty)):
            i0 = sel.index[0]
            try:
                srv = conectar_smtp(cfg)
                msg = armar_mensaje(cfg, cfg["usuario"], "[PRUEBA] " + completar(asunto_tpl, cand.loc[i0], sel.loc[i0, "Saludo"], asesor_firma),
                                    completar(cuerpo_tpl, cand.loc[i0], sel.loc[i0, "Saludo"], asesor_firma))
                srv.sendmail(cfg["usuario"], [cfg["usuario"]], msg.as_string())
                srv.quit()
                st.success(f"Prueba enviada a {cfg['usuario']}. Revisá cómo se ve antes de enviar la campaña.")
            except Exception as e:
                st.error(f"No se pudo enviar: {e}")

        confirmar = st.checkbox(f"Confirmo el envío a {min(len(sel), limite)} contactos", key="mail_conf")
        if b2.button("🚀 Enviar campaña", type="primary", use_container_width=True,
                     disabled=(not cfg or sel.empty or not confirmar)):
            lote = sel.head(int(limite))
            barra = st.progress(0.0, text="Conectando…")
            filas, ok, err = [], 0, 0
            try:
                srv = conectar_smtp(cfg)
            except Exception as e:
                st.error(f"No pude conectarme al servidor de correo: {e}")
                srv = None
            if srv:
                for n, (i, r) in enumerate(lote.iterrows(), start=1):
                    row = cand.loc[i]
                    try:
                        msg = armar_mensaje(cfg, r["Email"], completar(asunto_tpl, row, r["Saludo"], asesor_firma),
                                            completar(cuerpo_tpl, row, r["Saludo"], asesor_firma))
                        srv.sendmail(cfg["usuario"], [r["Email"]], msg.as_string())
                        filas.append(_fila_log(asesor_firma, "Correo", campana, row, r["Email"], "Enviado"))
                        ok += 1
                    except smtplib.SMTPServerDisconnected:
                        try:
                            srv = conectar_smtp(cfg)
                            srv.sendmail(cfg["usuario"], [r["Email"]], msg.as_string())
                            filas.append(_fila_log(asesor_firma, "Correo", campana, row, r["Email"], "Enviado"))
                            ok += 1
                        except Exception as e:
                            filas.append(_fila_log(asesor_firma, "Correo", campana, row, r["Email"], "Error", str(e)[:200]))
                            err += 1
                    except Exception as e:
                        filas.append(_fila_log(asesor_firma, "Correo", campana, row, r["Email"], "Error", str(e)[:200]))
                        err += 1
                    barra.progress(n / len(lote), text=f"Enviados {ok} de {len(lote)} · errores {err}")
                    if n < len(lote):
                        time.sleep(int(pausa))
                try:
                    srv.quit()
                except Exception:
                    pass
                registrar(conn, filas)
                st.success(f"✅ Campaña terminada: {ok} enviados, {err} con error. Quedó registrado en el historial.")

    # ================================================================ WHATSAPP
    with t_wa:
        st.info("Cada botón abre WhatsApp (Web o del celular) con el mensaje ya escrito para ese contacto: solo tenés que tocar *Enviar*. "
                "Es gratis y no pone en riesgo tu número. Para envío 100% automático hace falta la API oficial de WhatsApp Business (ver instrucciones).")
        st.markdown(VARIABLES_AYUDA)
        wa_tpl = st.text_area("Mensaje de WhatsApp", value=PLANTILLA_WHATSAPP, height=120, key="wa_tpl")
        cand_wa = base[base["Telefono"].apply(telefono_whatsapp) != ""]
        ya_wa = set(log[(log["Canal"] == "WhatsApp") & (log["Campaña"] == campana)]["Contacto"].astype(str))
        st.caption(f"{len(cand_wa)} contactos con teléfono. Los que ya registraste en esta campaña aparecen con ✅.")
        for i, row in cand_wa.head(100).iterrows():
            tel = telefono_whatsapp(row["Telefono"])
            texto = completar(wa_tpl, row, saludo_sugerido(row["Cliente"]), asesor_firma)
            hecho = tel in ya_wa
            c1, c2, c3 = st.columns([3, 1.2, 1.2])
            c1.markdown(f"{'✅ ' if hecho else ''}**{_txt(row['Cliente'])}** · {_txt(row['Empresa'])} · +{tel}")
            c2.link_button("💬 Abrir chat", f"https://wa.me/{tel}?text={urllib.parse.quote(texto)}", use_container_width=True)
            if c3.button("Registrar enviado", key=f"wa_ok_{i}", disabled=hecho, use_container_width=True):
                registrar(conn, [_fila_log(asesor_firma, "WhatsApp", campana, row, tel, "Enviado")])
                st.rerun()
        if len(cand_wa) > 100:
            st.caption("Se muestran los primeros 100. Ajustá los filtros para ver el resto.")

    # ================================================================ LINKEDIN
    with t_li:
        st.warning("LinkedIn prohíbe los bots de mensajes/conexiones y puede restringir la cuenta. "
                   "Acá el CRM te prepara el mensaje personalizado y te lleva al perfil: vos lo pegás y enviás (unos segundos por contacto).")
        st.markdown(VARIABLES_AYUDA)
        li_tpl = st.text_area("Mensaje / nota de conexión (máx. ~300 caracteres para invitaciones)", value=PLANTILLA_LINKEDIN, height=120, key="li_tpl")
        ya_li = set(log[(log["Canal"] == "LinkedIn") & (log["Campaña"] == campana)]["Cliente"].astype(str))
        for i, row in base.head(100).iterrows():
            cli = _txt(row["Cliente"])
            texto = completar(li_tpl, row, saludo_sugerido(cli), asesor_firma)
            hecho = cli in ya_li
            with st.expander(f"{'✅ ' if hecho else ''}{cli} · {_txt(row['Empresa'])}"):
                if len(texto) > 300:
                    st.caption(f"⚠️ {len(texto)} caracteres: como nota de invitación LinkedIn corta en 300.")
                st.code(texto, language=None)  # el ícono de la esquina copia el texto
                q = urllib.parse.quote(f"{cli} {_txt(row['Empresa'])}".strip())
                c1, c2 = st.columns(2)
                c1.link_button("🔎 Buscar en LinkedIn", f"https://www.linkedin.com/search/results/people/?keywords={q}", use_container_width=True)
                if c2.button("Registrar enviado", key=f"li_ok_{i}", disabled=hecho, use_container_width=True):
                    registrar(conn, [_fila_log(asesor_firma, "LinkedIn", campana, row, "LinkedIn", "Enviado")])
                    st.rerun()

    # ================================================================ HISTORIAL
    with t_hist:
        if log.empty:
            st.info("Todavía no hay envíos registrados.")
        else:
            h1, h2 = st.columns(2)
            canal_h = h1.multiselect("Canal", ["Correo", "WhatsApp", "LinkedIn"], key="h_canal")
            camp_h = h2.multiselect("Campaña", sorted(log["Campaña"].astype(str).unique()), key="h_camp")
            vista = log.copy()
            if canal_h:
                vista = vista[vista["Canal"].isin(canal_h)]
            if camp_h:
                vista = vista[vista["Campaña"].isin(camp_h)]
            if not es_admin:
                vista = vista[vista["Asesor"] == usuario_actual]
            st.dataframe(vista.iloc[::-1], hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🚫 Bajas (no volver a contactar)")
        st.caption("Cuando alguien responda BAJA, cargá acá su email o teléfono. Queda excluido de todas las campañas.")
        with st.form("form_baja", clear_on_submit=True):
            b1, b2 = st.columns([2, 2])
            contacto_baja = b1.text_input("Email o teléfono")
            motivo_baja = b2.text_input("Motivo (opcional)")
            if st.form_submit_button("Agregar a Bajas"):
                c = contacto_baja.strip().lower()
                if not c:
                    st.error("Ingresá un email o teléfono.")
                else:
                    if "@" not in c:
                        c = telefono_whatsapp(c) or c
                    nueva = pd.DataFrame([[c, datetime.now().strftime("%d/%m/%Y"), motivo_baja]], columns=COLUMNS_BAJAS)
                    if _escribir_hoja(conn, "Bajas", pd.concat([bajas, nueva], ignore_index=True)):
                        st.success(f"{c} agregado a Bajas.")
        if not bajas.empty:
            st.dataframe(bajas, hide_index=True, use_container_width=True)
