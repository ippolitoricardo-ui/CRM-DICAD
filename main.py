import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date, timedelta
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px
import urllib.parse

st.set_page_config(page_title="CRM DICAD AMÉRICA", layout="wide")

USUARIOS = st.secrets["passwords"]
ADMINISTRADOR = "Ricardo Ippolito"

CODIGOS_PAISES = [
    "🇦🇬 Antigua y Barbuda (+1)", "🇦🇷 Argentina (+54)", "🇧🇸 Bahamas (+1)", "🇧🇧 Barbados (+1)",
    "🇧🇿 Belice (+501)", "🇧🇴 Bolivia (+591)", "🇧🇷 Brasil (+55)", "🇨🇦 Canadá (+1)",
    "🇨🇱 Chile (+56)", "🇨🇴 Colombia (+57)", "🇨🇷 Costa Rica (+506)", "🇨🇺 Cuba (+53)",
    "🇩🇲 Dominica (+1)", "🇪🇨 Ecuador (+593)", "🇸🇻 El Salvador (+503)", "🇪🇸 España (+34)",
    "🇺🇸 Estados Unidos (+1)", "🇬🇩 Granada (+1)", "🇬🇹 Guatemala (+502)", "🇬🇾 Guyana (+592)",
    "🇭🇹 Haití (+509)", "🇭🇳 Honduras (+504)", "🇯🇲 Jamaica (+1)", "🇲🇽 México (+52)",
    "🇲🇿 Mozambique (+258)", "🇳🇮 Nicaragua (+505)", "🇵🇦 Panamá (+507)", "🇵🇾 Paraguay (+595)",
    "🇵🇪 Perú (+51)", "🇵🇹 Portugal (+351)", "🇩🇴 Rep. Dominicana (+1)", "🇰🇳 San Cristóbal y Nieves (+1)",
    "🇻🇨 San Vicente y las Granadinas (+1)", "🇱🇨 Santa Lucía (+1)", "🇸🇷 Surinam (+597)",
    "🇹🇹 Trinidad y Tobago (+1)", "🇺🇾 Uruguay (+598)", "🇻🇪 Venezuela (+58)", "🌎 Otro"
]

def extraer_pais_codigo(seleccion):
    if seleccion == "🌎 Otro": return "Otro", ""
    try: return seleccion.split(" ", 1)[1].split(" (")[0].strip(), seleccion.split(" ", 1)[1].split(" (")[1].replace(")", "").strip()
    except: return "Desconocido", ""

def limpiar_monto_para_suma(val_str):
    texto = str(val_str).upper().replace("USD", "").replace("ARS", "").replace("$", "").strip()
    clean_str = ''.join(c for c in texto if c.isdigit() or c in '.,')
    if not clean_str: return 0.0
    if ',' in clean_str and '.' in clean_str:
        last_sep = ',' if clean_str.rfind(',') > clean_str.rfind('.') else '.'
        clean_str = clean_str.replace(',' if last_sep == '.' else '.', '').replace(last_sep, '.')
    elif ',' in clean_str:
        clean_str = clean_str.replace(',', '.') if len(clean_str.split(',')[-1]) != 3 else clean_str.replace(',', '')
    elif '.' in clean_str:
        if len(clean_str.split('.')[-1]) == 3: clean_str = clean_str.replace('.', '')
    try: return float(clean_str)
    except: return 0.0

def parsear_fecha_hora(fecha_str):
    try:
        parts = str(fecha_str).strip().split()
        f_obj = datetime.strptime(parts[0], "%d/%m/%Y").date()
        h_obj = datetime.strptime(parts[1], "%H:%M").time() if len(parts) > 1 else datetime.strptime("10:00", "%H:%M").time()
        return f_obj, h_obj
    except: return date.today(), datetime.strptime("10:00", "%H:%M").time()

def generar_link_gcal(cliente, empresa, telefono, fecha_str):
    try:
        dt = datetime.strptime(fecha_str, "%d/%m/%Y %H:%M") if len(str(fecha_str)) > 10 else datetime.strptime(fecha_str, "%d/%m/%Y")
        start_str = dt.strftime("%Y%m%dT%H%M%00")
        end_str = (dt + timedelta(minutes=30)).strftime("%Y%m%dT%H%M%00")
        titulo = urllib.parse.quote(f"📞 Llamar a {cliente} ({empresa})")
        detalles = urllib.parse.quote(f"CRM Recordatorio de Llamada.\n\nEmpresa: {empresa}\nTeléfono: {telefono}")
        return f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={titulo}&details={detalles}&dates={start_str}/{end_str}"
    except: return ""

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False; st.session_state.usuario_actual = None

def login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Acceso CRM DICAD")
        with st.form("login_form"):
            user = st.selectbox("Seleccione su nombre", list(USUARIOS.keys()))
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if USUARIOS[user] == password:
                    st.session_state.autenticado = True; st.session_state.usuario_actual = user; st.rerun()
                else: st.error("Contraseña incorrecta")

if not st.session_state.autenticado: login(); st.stop()

with st.sidebar:
    st.markdown('<style>[data-testid="stSidebar"] {background-color: #2E3E57 !important;}</style>', unsafe_allow_html=True)
    st.columns([1, 4, 1])[1].image("logo_dicad.png", use_column_width=True) 
    st.markdown("<p style='text-align: center; color:#fff; font-size:16px; margin-top:0.5em; font-weight: bold;'>CRM DICAD AMÉRICA</p><br>", unsafe_allow_html=True) 
    section = option_menu(None, ["Potenciales", "Pipeline", "Negociaciones", "Agregar Cliente", "Calendario"], icons=["person-bounding-box", "kanban", "briefcase", "person-plus", "calendar-date"], default_index=2, styles={"container": {"padding": "5px!important", "background-color": "#F0F2F6", "border-radius": "10px"},"icon": {"color": "#333333", "font-size": "18px"}, "nav-link": {"color": "#333333", "font-size": "16px", "text-align": "left", "margin":"2px 0px", "--hover-color": "#E0E0E0"},"nav-link-selected": {"background-color": "#FF6600", "color": "white"}})
    st.markdown("---")
    st.markdown(f"<div style='text-align: center; color: white; font-size: 14px; margin-bottom: 10px;'>{'👑 Admin' if st.session_state.usuario_actual == ADMINISTRADOR else '💼 Asesor'}: <b>{st.session_state.usuario_actual}</b></div>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión", use_container_width=True): st.session_state.autenticado = False; st.session_state.usuario_actual = None; st.rerun()

GSHEET_URL = st.secrets.get("SHEET_URL", "https://docs.google.com/spreadsheets/d/___/edit#gid=0")
conn = st.connection("gsheets", type=GSheetsConnection)
worksheet_name = "Central Negociaciones"
COLUMNS = ["Cliente", "Profesion", "Direccion", "Pais", "Ciudad", "Estado /Prov.", "Empresa", "Cargo", "Telefono", "Email", "N° Cotiz.", "Monto USD / $", "Notas", "Proxima llamada", "Creado", "Asesor", "Estado_Nego", "Link_PDF"]

@st.cache_data(ttl=60)
def get_data():
    df = conn.read(spreadsheet=GSHEET_URL)
    if df is None: df = pd.DataFrame(columns=COLUMNS)
    else:
        df.columns = df.columns.str.strip()
        for col in COLUMNS:
            if col not in df.columns: df[col] = ""
        df = df[COLUMNS].fillna('')
        df['Telefono'] = df['Telefono'].astype(str).str.strip().str.lstrip("'").replace('#ERROR!', '')
    return df

def guardar_datos(df_a_guardar):
    df_safe = df_a_guardar.copy()
    df_safe['Telefono'] = df_safe['Telefono'].astype(str).apply(lambda x: f" {x.strip()}" if x.strip().startswith("+") else x.strip())
    conn.update(worksheet=worksheet_name, data=df_safe, spreadsheet=GSHEET_URL)
    st.cache_data.clear()

def generar_numero_cotizacion(df):
    numeros = [int(''.join(filter(str.isdigit, str(val)))) for val in df['N° Cotiz.'].dropna() if ''.join(filter(str.isdigit, str(val)))]
    return f"{max(max(numeros) + 1 if numeros else 0, 1000):06d}"

def guardar_gestion(indice, nota_existente, nueva_nota, nueva_fecha_str, fecha_anterior_str):
    df_actual = get_data(); fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    texto_agregado = f"[{fecha_hoy}] 📝 {nueva_nota}" if nueva_nota.strip() else ""
    if nueva_fecha_str != str(fecha_anterior_str): texto_agregado += f" | 📅 Reprogramado: {nueva_fecha_str}" if texto_agregado else f"[{fecha_hoy}] 📅 Llamada reprogramada a: {nueva_fecha_str}"
    if texto_agregado: df_actual.at[indice, 'Notas'] = texto_agregado if str(nota_existente).strip() in ["", "nan"] else f"{nota_existente}\n{texto_agregado}"
    df_actual.at[indice, 'Proxima llamada'] = nueva_fecha_str; guardar_datos(df_actual)

df = get_data()
lista_asesores = ["Todos los Asesores"] + list(USUARIOS.keys())
index_inicio = lista_asesores.index(st.session_state.usuario_actual) if st.session_state.usuario_actual in lista_asesores else 0

# --- POTENCIALES ---
if section == "Potenciales":
    st.markdown("## 🎯 Clientes Potenciales")
    asesor_sel = st.selectbox("Filtrar por Asesor:", lista_asesores, index=index_inicio)
    df_pot = df[df['Estado_Nego'] == 'Potencial']
    if asesor_sel != "Todos los Asesores": df_pot = df_pot[df_pot['Asesor'] == asesor_sel]
    st.metric("Total de Leads", len(df_pot)); st.markdown("---")

    for idx, row in df_pot.iterrows():
        puede_editar = (st.session_state.usuario_actual == ADMINISTRADOR) or (st.session_state.usuario_actual == row.get('Asesor', ''))
        st.markdown(f'<div style="background:white;padding:1em;border-radius:10px;border-left:5px solid #6c757d;margin-bottom:0.5em;box-shadow:0 1px 4px #d0d6e1;color:black;"><b>Cliente:</b> {row.get("Cliente", "")} | <b>Empresa:</b> {row.get("Empresa", "")} <br> <b>Teléfono:</b> {row.get("Telefono", "")} | <b>Próx:</b> {row.get("Proxima llamada", "")}</div>', unsafe_allow_html=True)
        
        with st.expander("📞 ASISTENTE DE LLAMADA (Guiones de Descubrimiento)", expanded=False):
            st.warning("🗣️ **Objetivo de esta llamada:** Descubrir el dolor del cliente y generar interés para enviar presupuesto.")
            st.markdown("💡 **Tip 1:** ¿Qué desafío estructural o de tiempos los motivó a buscar nuevas herramientas?")
            st.markdown("💡 **Tip 2:** ¿Qué software están usando hoy y qué es lo que más les frustra de ese proceso?")
            st.markdown("💡 **Tip 3:** Si pudieras resolver [su problema] hoy mismo, ¿cuánto tiempo/dinero ahorraría tu equipo?")
        
        with st.expander(f"Ver / Editar a {row.get('Cliente', '')}"):
            if puede_editar:
                with st.expander("⚙️ Editar Ficha"):
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        e_cli = st.text_input("Nombre", row.get('Cliente',''), key=f"e_cli_p_{idx}"); e_emp = st.text_input("Empresa", row.get('Empresa',''), key=f"e_emp_p_{idx}")
                        e_prof = st.text_input("Profesión", row.get('Profesion',''), key=f"e_prof_p_{idx}"); e_cargo = st.text_input("Cargo", row.get('Cargo',''), key=f"e_cargo_p_{idx}")
                    with ce2:
                        idx_p = next((i for i, p in enumerate(CODIGOS_PAISES) if str(row.get('Pais','')).lower() in p.lower() and row.get('Pais','') != ""), 0)
                        e_pais_sel = st.selectbox("País", CODIGOS_PAISES, index=idx_p, key=f"e_pais_p_{idx}"); e_ciu = st.text_input("Ciudad", row.get('Ciudad',''), key=f"e_ciu_p_{idx}")
                        e_tel = st.text_input("Teléfono", row.get('Telefono',''), key=f"e_tel_p_{idx}"); e_mail = st.text_input("Email", row.get('Email',''), key=f"e_mail_p_{idx}")
                    if st.button("💾 Guardar Cambios", key=f"btn_e_p_{idx}"):
                        p_f, c_f = extraer_pais_codigo(e_pais_sel)
                        tel_f = f"{c_f} {e_tel}" if (e_tel.strip() and not e_tel.startswith("+") and c_f) else e_tel
                        df_act = get_data(); df_act.loc[idx, ['Cliente','Empresa','Profesion','Cargo','Pais','Ciudad','Telefono','Email']] = [e_cli, e_emp, e_prof, e_cargo, p_f, e_ciu, tel_f, e_mail]
                        guardar_datos(df_act); st.rerun()

            st.info(f"**Historial:**\n{row.get('Notas', 'Sin notas.')}")
            if puede_editar:
                c_n1, c_n2, c_n3 = st.columns([1.8, 2, 1])
                with c_n1:
                    f_o, h_o = parsear_fecha_hora(row.get('Proxima llamada', ''))
                    cc1, cc2 = st.columns(2)
                    with cc1: n_f = st.date_input("Día", value=f_o, key=f"f_p_{idx}")
                    with cc2: n_h = st.time_input("Hora", value=h_o, key=f"h_p_{idx}")
                with c_n2: n_n = st.text_input("Nota hoy", key=f"n_p_{idx}")
                with c_n3: 
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾 Guardar", key=f"b_p_{idx}"):
                        fh_str = f"{n_f.strftime('%d/%m/%Y')} {n_h.strftime('%H:%M')}"
                        guardar_gestion(idx, row.get('Notas',''), n_n, fh_str, row.get('Proxima llamada','')); st.rerun()
                st.markdown("---")
                c_p1, c_p2 = st.columns(2)
                with c_p1: n_m_p = st.text_input("Monto Cotizado (Ej: USD 5000)", key=f"pm_{idx}")
                with c_p2: n_l_p = st.text_input("Link PDF", key=f"pl_{idx}")
                if st.button("🚀 Promover a Negociación", key=f"prov_{idx}", type="primary"):
                    df_a = get_data(); df_a.at[idx, 'Estado_Nego'] = "En Proceso"
                    if n_m_p: df_a.at[idx, 'Monto USD / $'] = n_m_p
                    if n_l_p: df_a.at[idx, 'Link_PDF'] = n_l_p
                    if not str(df_a.at[idx, 'N° Cotiz.']).strip(): df_a.at[idx, 'N° Cotiz.'] = generar_numero_cotizacion(df_a)
                    guardar_datos(df_a); st.rerun()

# --- PIPELINE KANBAN ---
elif section == "Pipeline":
    c_t, c_b = st.columns([4, 1])
    with c_t: st.markdown("## 📊 Pipeline de Ventas")
    with c_b: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar Tablero", use_container_width=True): st.cache_data.clear(); st.rerun()
        
    asesor_sel = st.selectbox("Filtrar Tablero por Asesor:", lista_asesores, index=index_inicio)
    df_pipe = df if asesor_sel == "Todos los Asesores" else df[df['Asesor'] == asesor_sel]
    
    estados_kanban = ["Potencial", "En Proceso", "Ganada", "Perdida"]
    cols_kanban = st.columns(4)
    
    for i, estado in enumerate(estados_kanban):
        with cols_kanban[i]:
            df_col = df_pipe[df_pipe['Estado_Nego'] == estado]
            tot_usd = sum(limpiar_monto_para_suma(x) for x in df_col['Monto USD / $'] if 'ARS' not in str(x).upper())
            
            color_header = "#6c757d" if estado=="Potencial" else "#ffc107" if estado=="En Proceso" else "#28a745" if estado=="Ganada" else "#dc3545"
            st.markdown(f"<div style='background-color:{color_header}; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold; margin-bottom:15px;'>{estado.upper()} ({len(df_col)})<br>USD {tot_usd:,.0f}</div>", unsafe_allow_html=True)
            
            for idx, row in df_col.iterrows():
                puede = (st.session_state.usuario_actual == ADMINISTRADOR) or (st.session_state.usuario_actual == row.get('Asesor', ''))
                
                st.markdown(f"""
                <div style="background:white; padding:12px; border-radius:8px; box-shadow:0 2px 5px rgba(0,0,0,0.15); margin-bottom:5px; border-left:4px solid {color_header}; color:black;">
                    <b style="font-size:14px;">{row.get('Cliente','')}</b><br>
                    <span style="font-size:12px; color:#555;">{row.get('Empresa','')}</span><br>
                    <b style="font-size:13px; color:#2261b6;">{row.get('Monto USD / $','')}</b><br>
                    <span style="font-size:11px; color:#888;">📅 {row.get('Proxima llamada','')}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if puede:
                    opciones_mover = ["Mover a..."] + [e for e in estados_kanban if e != estado]
                    nuevo_est = st.selectbox("Acción", opciones_mover, key=f"mov_{idx}", label_visibility="collapsed")
                    if nuevo_est != "Mover a...":
                        df_actual = get_data()
                        df_actual.at[idx, 'Estado_Nego'] = nuevo_est
                        if nuevo_est == "En Proceso" and not str(df_actual.at[idx, 'N° Cotiz.']).strip():
                            df_actual.at[idx, 'N° Cotiz.'] = generar_numero_cotizacion(df_actual)
                        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                        nota_cambio = f"[{fecha_hoy}] 🔄 Movido en Pipeline a: {nuevo_est.upper()}"
                        nota_previa = str(df_actual.at[idx,'Notas'])
                        df_actual.at[idx, 'Notas'] = nota_cambio if nota_previa.strip() in ["", "nan"] else f"{nota_previa}\n{nota_cambio}"
                        guardar_datos(df_actual)
                        st.rerun()

# --- NEGOCIACIONES ---
elif section == "Negociaciones":
    st.markdown("## :card_index_dividers: Negociaciones Activas")
    df_nego = df[(df['Estado_Nego'] != 'Potencial') & (df['Estado_Nego'] != '')]

    if st.session_state.usuario_actual == ADMINISTRADOR:
        st.markdown("### 🏢 PANEL ESTRATÉGICO (Admin)")
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Total Empresa (USD)", f"USD {sum(limpiar_monto_para_suma(x) for x in df_nego['Monto USD / $'] if 'ARS' not in str(x).upper()):,.0f}")
        c2.metric("💵 Total Empresa (ARS)", f"ARS {sum(limpiar_monto_para_suma(x) for x in df_nego['Monto USD / $'] if 'ARS' in str(x).upper()):,.0f}")
        c3.metric("🤝 Negociaciones Totales", len(df_nego))
        
        st.markdown("#### 📊 Desempeño Detallado por Asesor")
        df_nego_calc = df_nego.copy()
        df_nego_calc['Suma_USD'] = df_nego_calc['Monto USD / $'].apply(lambda x: limpiar_monto_para_suma(x) if "ARS" not in str(x).upper() else 0.0)
        df_nego_calc['Suma_ARS'] = df_nego_calc['Monto USD / $'].apply(lambda x: limpiar_monto_para_suma(x) if "ARS" in str(x).upper() else 0.0)
        st.dataframe(df_nego_calc.groupby('Asesor').agg({'Suma_USD': 'sum', 'Suma_ARS': 'sum', 'Cliente': 'count'}).reset_index().rename(columns={'Suma_USD': 'Total USD', 'Suma_ARS': 'Total ARS', 'Cliente': 'Negociaciones'}).style.format({'Total USD': 'USD {:,.0f}', 'Total ARS': 'ARS {:,.0f}'}), use_container_width=True)
        st.markdown("---")

    st.markdown("### 👔 Detalles por Asesor")
    asesor_sel = st.selectbox("Seleccionar Asesor:", lista_asesores, index=index_inicio)
    df_tab = df_nego if asesor_sel == "Todos los Asesores" else df_nego[df_nego['Asesor'] == asesor_sel]

    k1, k2, k3 = st.columns(3)
    k1.metric("💰 Cotizado (USD)", f"USD {sum(limpiar_monto_para_suma(x) for x in df_tab['Monto USD / $'] if 'ARS' not in str(x).upper()):,.0f}")
    k2.metric("💵 Cotizado (ARS)", f"ARS {sum(limpiar_monto_para_suma(x) for x in df_tab['Monto USD / $'] if 'ARS' in str(x).upper()):,.0f}")
    k3.metric("🤝 Cantidad", len(df_tab))

    st.markdown("---"); g1, g2 = st.columns(2)
    with g1:
        df_g = df_tab.copy()
        df_g['VAL'] = df_g['Monto USD / $'].apply(lambda x: 0.0 if "ARS" in str(x).upper() else limpiar_monto_para_suma(x))
        if df_g['VAL'].sum() > 0:
            datos_torta = df_g.groupby('Estado_Nego')['VAL'].sum().reset_index()
            fig_torta = px.pie(datos_torta, values='VAL', names='Estado_Nego', title='Dólares por Estado', hole=0.4, color='Estado_Nego', color_discrete_map={'Ganada':'#28a745','Perdida':'#dc3545','En Proceso':'#ffc107'})
            fig_torta.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_torta, use_container_width=True)
        else:
            st.info("No hay montos en USD para graficar.")
    with g2:
        if not df_tab.empty:
            datos_barras = df_tab['Asesor'].value_counts().reset_index()
            datos_barras.columns = ['Asesor', 'Cantidad']
            fig_barras = px.bar(datos_barras, x='Asesor', y='Cantidad', title='Cantidad de Negociaciones', color='Asesor')
            st.plotly_chart(fig_barras, use_container_width=True)

    c_b, c_r = st.columns([4, 1])
    with c_b: busq = st.text_input("🔍 Buscar Cliente/Empresa:")
    with c_r: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar Datos"): st.cache_data.clear(); st.rerun()
                
    df_f = df_tab[df_tab['Cliente'].astype(str).str.contains(busq, case=False) | df_tab['Empresa'].astype(str).str.contains(busq, case=False)] if busq else df_tab

    for idx, row in df_f.iterrows():
        est = row.get('Estado_Nego', 'En Proceso'); color = "#28a745" if est == 'Ganada' else "#dc3545" if est == 'Perdida' else "#ffc107"
        st.markdown(f'<div style="background:white;padding:1.3em;border-radius:12px;margin-bottom:0.6em;box-shadow:0 1px 8px #d0d6e1;border-left:6px solid {color};color:black;"><span style="float:right;background:{color};color:white;padding:4px 8px;border-radius:6px;font-size:12px;font-weight:bold;">{"✅" if est=="Ganada" else "❌" if est=="Perdida" else "⏳"} {est.upper()}</span><b>Cliente:</b> {row.get("Cliente", "")} | <b>Cotiz:</b> {row.get("N° Cotiz.", "N/A")}<br><b>Monto:</b> <span style="color:#2261b6;font-weight:bold;">{row.get("Monto USD / $", "")}</span></div>', unsafe_allow_html=True)
        
        with st.expander("📞 ASISTENTE DE LLAMADA (Manejo de Objeciones de Cierre)", expanded=False):
            st.warning("🎯 **Modo Cierre Activado:** Aislá la objeción antes de responder o ceder precio.")
            st.markdown("🛡️ **Si dicen:** *'Llamame la semana que viene'* <br> **Tu respuesta:** *'Entiendo {}. Exactamente, ¿qué va a cambiar de esta semana a la próxima que haga diferente la decisión?'*".format(row.get('Cliente','').split(' ')[0]), unsafe_allow_html=True)
            st.markdown("🛡️ **Si dicen:** *'Está muy caro / Se va de presupuesto'* <br> **Tu respuesta:** *'Aparte del precio, ¿hay alguna otra cosa que te impida avanzar hoy con nosotros?'*", unsafe_allow_html=True)
            st.markdown("🛡️ **Si dicen:** *'Lo tengo que consultar con mi socio'* <br> **Tu respuesta:** *'Perfecto. Y vos personalmente, ¿qué le vas a recomendar a tu socio que hagan?'*", unsafe_allow_html=True)

        with st.expander("Ver Ficha Completa"):
            puede = (st.session_state.usuario_actual == ADMINISTRADOR) or (st.session_state.usuario_actual == row.get('Asesor', ''))
            if puede:
                with st.expander("⚙️ Editar Contacto"):
                    c_e1, c_e2 = st.columns(2)
                    with c_e1: ec = st.text_input("Nombre", row.get('Cliente',''), key=f"ecn_{idx}"); ee = st.text_input("Empresa", row.get('Empresa',''), key=f"een_{idx}"); e_prof = st.text_input("Profesión", row.get('Profesion',''), key=f"eprn_{idx}"); e_cargo = st.text_input("Cargo", row.get('Cargo',''), key=f"ecrn_{idx}")
                    with c_e2:
                        idx_pa = next((i for i, p in enumerate(CODIGOS_PAISES) if str(row.get('Pais','')).lower() in p.lower() and row.get('Pais','') != ""), 0)
                        ep = st.selectbox("País", CODIGOS_PAISES, index=idx_pa, key=f"epn_{idx}"); e_ciu = st.text_input("Ciudad", row.get('Ciudad',''), key=f"eciun_{idx}")
                        em = st.text_input("Email", row.get('Email',''), key=f"emn_{idx}"); etel = st.text_input("Teléfono", row.get('Telefono',''), key=f"eteln_{idx}")
                    if st.button("💾 Actualizar", key=f"becn_{idx}"):
                        p_n, c_n = extraer_pais_codigo(ep)
                        tel_f = f"{c_n} {etel}" if (etel.strip() and not etel.startswith("+") and c_n) else etel
                        df_u = get_data(); df_u.loc[idx, ['Cliente','Empresa','Profesion','Cargo','Pais','Ciudad','Email','Telefono']] = [ec, ee, e_prof, e_cargo, p_n, e_ciu, em, tel_f]
                        guardar_datos(df_u); st.rerun()

            col1, col2 = st.columns(2)
            with col1: st.write(f"**Prof:** {row.get('Profesion','')} | **Cargo:** {row.get('Cargo','')}"); st.write(f"**País:** {row.get('Pais','')} | **Ciudad:** {row.get('Ciudad','')}"); st.write(f"**Tel:** {row.get('Telefono','')}"); st.write(f"**Email:** {row.get('Email','')}")
            with col2: st.write(f"**Empresa:** {row.get('Empresa','')}"); st.write(f"**Cotiz:** {row.get('N° Cotiz.','')}"); st.write(f"**Asesor:** {row.get('Asesor','')}")
            if row.get('Link_PDF'): st.link_button("📄 Ver PDF", row['Link_PDF'], use_container_width=True)

            st.markdown("---"); st.markdown("### 🗂️ Historial Cotizaciones")
            c_ref = str(row.get('Email','')).lower() if row.get('Email','') else str(row.get('Telefono',''))
            df_c = df_nego[df_nego['Email'].str.lower() == c_ref] if row.get('Email','') else df_nego[df_nego['Telefono'] == c_ref]
            st.info(f"**💰 Total Cliente:** USD {sum(limpiar_monto_para_suma(m) for m in df_c['Monto USD / $'] if 'ARS' not in str(m).upper()):,.0f} ({len(df_c)} cotiz.)")
            
            if puede:
                with st.expander("➕ Nueva Cotización"):
                    cc1, cc2 = st.columns(2)
                    with cc1: ncm = st.text_input("Monto", key=f"ncm_{idx}"); ncmony = st.selectbox("Moneda", ["USD","ARS"], key=f"ncmy_{idx}")
                    with cc2: ncc = st.text_input("N° (Vacío=Auto)", key=f"ncc_{idx}"); ncp = st.text_input("PDF", key=f"ncp_{idx}")
                    if st.button("✅ Crear", key=f"bnc_{idx}"):
                        df_n = get_data(); f_h = datetime.now().strftime("%d/%m/%Y"); num_c = ncc if ncc else generar_numero_cotizacion(df_n)
                        new_r = pd.DataFrame([{"Creado":f_h,"Cliente":row['Cliente'],"Empresa":row['Empresa'],"Profesion":row['Profesion'],"Cargo":row['Cargo'],"Pais":row['Pais'],"Ciudad":row['Ciudad'],"Telefono":row['Telefono'],"Email":row['Email'],"N° Cotiz.":num_c,"Monto USD / $":f"{ncmony} {ncm}" if ncm else "","Asesor":row['Asesor'],"Estado_Nego":"En Proceso","Link_PDF":ncp}])
                        guardar_datos(pd.concat([df_n, new_r], ignore_index=True)); st.rerun()

            st.markdown("**📝 Seguimiento:**"); st.caption(row.get('Notas',''))
            if puede:
                cn1, cn2, cn3 = st.columns([1.8, 2, 1])
                with cn1:
                    f_o, h_o = parsear_fecha_hora(row.get('Proxima llamada', ''))
                    cc1, cc2 = st.columns(2)
                    with cc1: nf = st.date_input("Día", value=f_o, key=f"fgn_{idx}")
                    with cc2: nh = st.time_input("Hora", value=h_o, key=f"hgn_{idx}")
                with cn2: nn = st.text_input("Nota", key=f"ngn_{idx}")
                with cn3: 
                    st.markdown("<br>", unsafe_allow_html=True); 
                    if st.button("💾", key=f"bgn_{idx}"): 
                        fh_str = f"{nf.strftime('%d/%m/%Y')} {nh.strftime('%H:%M')}"
                        guardar_gestion(idx, row.get('Notas',''), nn, fh_str, row.get('Proxima llamada','')); st.rerun()
                
                st.markdown("---"); ce1, ce2, ce3 = st.columns([1.5, 2, 1])
                with ce1: edm = st.text_input("Monto", row.get('Monto USD / $',''), key=f"edm_{idx}")
                with ce2: edl = st.text_input("Link", row.get('Link_PDF',''), key=f"edl_{idx}")
                with ce3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾 Actualizar", key=f"bed_{idx}"): df_a = get_data(); df_a.loc[idx, ['Monto USD / $','Link_PDF']] = [edm, edl]; guardar_datos(df_a); st.rerun()

                st.markdown("---")
                if est in ['Ganada','Perdida']:
                    if st.button("🔄 Reabrir", key=f"re_{idx}"): df_r = get_data(); df_r.at[idx, 'Estado_Nego'] = "En Proceso"; guardar_datos(df_r); st.rerun()
                else:
                    cg, cp = st.columns(2)
                    with cg: 
                        if st.button("✅ GANADA", key=f"g_{idx}", use_container_width=True): df_g = get_data(); df_g.at[idx, 'Estado_Nego'] = "Ganada"; df_g.at[idx, 'Notas'] = str(df_g.at[idx,'Notas']) + f"\n[{datetime.now().strftime('%d/%m/%Y')}] 🏆 GANADA"; guardar_datos(df_g); st.rerun()
                    with cp: 
                        if st.button("❌ PERDIDA", key=f"p_{idx}", use_container_width=True): df_p = get_data(); df_p.at[idx, 'Estado_Nego'] = "Perdida"; df_p.at[idx, 'Notas'] = str(df_p.at[idx,'Notas']) + f"\n[{datetime.now().strftime('%d/%m/%Y')}] ❌ PERDIDA"; guardar_datos(df_p); st.rerun()

elif section == "Agregar Cliente":
    st.markdown("## 🙋‍♂️ Nuevo Contacto")
    if 'f_k' not in st.session_state: st.session_state.f_k = 0
    fk = st.session_state.f_k
    
    tipo = st.radio("Fase:", ["🎯 Potencial", "💼 Negociación Activa"], key=f"t_{fk}", horizontal=True); st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        cli = st.text_input("Nombre *", key=f"c_{fk}"); emp = st.text_input("Empresa", key=f"e_{fk}")
        p_s = st.selectbox("País", CODIGOS_PAISES, key=f"p_{fk}"); ciu = st.text_input("Ciudad", key=f"ci_{fk}")
        c_m, c_mo = st.columns([2, 1])
        with c_m: m_v = st.text_input("Monto (Vacío=Potencial)", key=f"mv_{fk}")
        with c_mo: m_n = st.selectbox("Moneda", ["USD", "ARS"], key=f"mn_{fk}")
    with c2:
        prof = st.text_input("Profesión", key=f"pr_{fk}"); car = st.text_input("Cargo", key=f"ca_{fk}")
        tel = st.text_input("Teléfono (Sin código)", key=f"te_{fk}"); eml = st.text_input("Email", key=f"em_{fk}")
        cc1, cc2 = st.columns(2)
        with cc1: px_l = st.date_input("Próxima llamada", key=f"px_{fk}")
        with cc2: px_h = st.time_input("Hora", value=datetime.strptime("10:00", "%H:%M").time(), key=f"pxh_{fk}")
        cot = st.text_input("N° Cotiz (Vacío=Auto)", key=f"co_{fk}")
        
    ase = st.selectbox("Asesor", list(USUARIOS.keys()), index=list(USUARIOS.keys()).index(st.session_state.usuario_actual) if st.session_state.usuario_actual in USUARIOS else 0, key=f"as_{fk}") if st.session_state.usuario_actual == ADMINISTRADOR else st.session_state.usuario_actual
    if st.session_state.usuario_actual != ADMINISTRADOR: st.write(f"**Asesor:** {ase}")
    
    st.markdown("---"); n_i = st.text_area("Nota", key=f"ni_{fk}"); l_p = st.text_input("PDF", key=f"pd_{fk}")
    
    if st.button("💾 GUARDAR", type="primary", use_container_width=True):
        if not cli.strip(): st.warning("Nombre obligatorio.")
        else:
            with st.spinner("Guardando..."):
                df_t = get_data(); p_f, c_f = extraer_pais_codigo(p_s)
                tel_f = f"{c_f} {tel}" if (tel.strip() and not tel.startswith("+") and c_f) else tel
                em_l, te_l = eml.strip().lower(), tel_f.replace(" ","").replace("+","").replace("-","")
                if any((str(r['Email']).lower().strip() == em_l and em_l) or (str(r['Telefono']).replace(" ","").replace("+","").replace("-","") == te_l and te_l) for _, r in df_t.iterrows()): st.error("🚨 ¡CLIENTE EXISTENTE! Usá 'Nueva Cotización' en Negociaciones.")
                else:
                    est_i = "Potencial" if "Potencial" in tipo else "En Proceso"; cot_f = cot.strip() if cot.strip() else (generar_numero_cotizacion(df_t) if est_i == "En Proceso" else "")
                    fh_str = f"{px_l.strftime('%d/%m/%Y')} {px_h.strftime('%H:%M')}"
                    new = pd.DataFrame([{"Creado":datetime.now().strftime("%d/%m/%Y"),"Cliente":cli,"Profesion":prof,"Pais":p_f,"Ciudad":ciu,"Empresa":emp,"Cargo":car,"Telefono":tel_f,"Email":eml,"N° Cotiz.":cot_f,"Monto USD / $":f"{m_n} {m_v}" if m_v else "","Notas":f"[{datetime.now().strftime('%d/%m/%Y')}] 📝 {n_i}" if n_i else "","Proxima llamada":fh_str,"Asesor":ase,"Estado_Nego":est_i,"Link_PDF":l_p}])
                    guardar_datos(pd.concat([df_t, new], ignore_index=True)); st.session_state.f_k += 1; st.success("Guardado!"); st.rerun()

elif section == "Calendario":
    c_t, c_b = st.columns([4, 1])
    with c_t: st.markdown("## 📅 Agenda")
    with c_b: 
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar", use_container_width=True): st.cache_data.clear(); st.rerun()
    df_a = df[df['Estado_Nego'].isin(['En Proceso', 'Potencial'])].copy()
    if df_a.empty: st.success("Al día.")
    else:
        df_a['F'] = pd.to_datetime(df_a['Proxima llamada'], format='%d/%m/%Y %H:%M', errors='coerce').fillna(pd.to_datetime(df_a['Proxima llamada'], format='%d/%m/%Y', errors='coerce'))
        for idx, r in df_a.sort_values('F').iterrows():
            link_cal = generar_link_gcal(r['Cliente'], r['Empresa'], r['Telefono'], r['Proxima llamada'])
            btn_cal = f"<a href='{link_cal}' target='_blank' style='text-decoration:none; background-color:#4285F4; color:white; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold; margin-left:10px;'>📅 Añadir a Google Calendar</a>" if link_cal else ""
            
            st.markdown(f'<div style="background:#2E3E57;padding:15px;border-radius:10px;margin-bottom:10px;border-left:5px solid #FF6600;"><h4 style="color:white;margin:0;">📅 {r["Proxima llamada"]} hs | {r["Cliente"]} <span style="font-size:12px;background:#556B8D;padding:3px 8px;border-radius:5px;margin-left:5px;">{"🎯" if r["Estado_Nego"]=="Potencial" else "💼"}</span> {btn_cal}</h4><p style="color:#d0d6e1;margin:5px 0;">📞 {r["Telefono"]} | ✉️ {r["Email"]} | 👔 {r["Asesor"]}</p></div>', unsafe_allow_html=True)
            
            if (st.session_state.usuario_actual == ADMINISTRADOR) or (st.session_state.usuario_actual == r.get('Asesor', '')):
                with st.expander("⚙️ Editar"):
                    c_e1, c_e2 = st.columns(2)
                    with c_e1: ec = st.text_input("Nombre", r.get('Cliente',''), key=f"ec_{idx}"); ee = st.text_input("Empresa", r.get('Empresa',''), key=f"ee_{idx}"); e_prof = st.text_input("Profesión", r.get('Profesion',''), key=f"epr_{idx}"); e_cargo = st.text_input("Cargo", r.get('Cargo',''), key=f"eca_{idx}")
                    with c_e2:
                        idx_pa = next((i for i, p in enumerate(CODIGOS_PAISES) if str(r.get('Pais','')).lower() in p.lower() and r.get('Pais','') != ""), 0)
                        ep = st.selectbox("País", CODIGOS_PAISES, index=idx_pa, key=f"ep_{idx}"); e_ciu = st.text_input("Ciudad", r.get('Ciudad',''), key=f"eci_{idx}")
                        em = st.text_input("Email", r.get('Email',''), key=f"em_{idx}"); etel = st.text_input("Teléfono", r.get('Telefono',''), key=f"ete_{idx}")
                    if st.button("💾 Guardar", key=f"be_{idx}"):
                        p_n, c_n = extraer_pais_codigo(ep)
                        tel_f = f"{c_n} {etel}" if (etel.strip() and not etel.startswith("+") and c_n) else etel
                        df_u = get_data(); df_u.loc[idx, ['Cliente','Empresa','Profesion','Cargo','Pais','Ciudad','Email','Telefono']] = [ec, ee, e_prof, e_cargo, p_n, e_ciu, em, tel_f]
                        guardar_datos(df_u); st.rerun()