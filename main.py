import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px

# --- CONFIGURACION DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="CRM DICAD AMÉRICA", layout="wide")

# --- 1. BASE DE DATOS DE USUARIOS Y PAÍSES ---
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
    try:
        partes = seleccion.split(" ", 1)
        sub_partes = partes[1].split(" (")
        pais = sub_partes[0].strip()
        codigo = sub_partes[1].replace(")", "").strip()
        return pais, codigo
    except:
        return "Desconocido", ""

# --- MOTOR DE LECTURA DE DINERO INTELIGENTE ---
def limpiar_monto_para_suma(val_str):
    texto = str(val_str).upper()
    if "USD" not in texto and "ARS" not in texto:
        return 0.0
    clean_str = ''.join(c for c in texto if c.isdigit() or c in '.,')
    if not clean_str: return 0.0
    
    if ',' in clean_str and '.' in clean_str:
        last_sep = ',' if clean_str.rfind(',') > clean_str.rfind('.') else '.'
        clean_str = clean_str.replace(',' if last_sep == '.' else '.', '')
        clean_str = clean_str.replace(last_sep, '.')
    elif ',' in clean_str:
        if len(clean_str.split(',')[-1]) != 3: 
            clean_str = clean_str.replace(',', '.')
        else:
            clean_str = clean_str.replace(',', '')
    elif '.' in clean_str:
        if len(clean_str.split('.')[-1]) == 3:
            clean_str = clean_str.replace('.', '')
    try:
        return float(clean_str)
    except:
        return 0.0

# --- 2. GESTIÓN DE SESIÓN (LOGIN) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_actual = None

def login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Acceso CRM DICAD")
        with st.form("login_form"):
            user = st.selectbox("Seleccione su nombre", list(USUARIOS.keys()))
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submit:
                if USUARIOS[user] == password:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = user
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")

if not st.session_state.autenticado:
    login()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {background-color: #2E3E57 !important;}
        </style>
    """, unsafe_allow_html=True)
    
    st.write("") 
    col1, col2, col3 = st.columns([1, 4, 1]) 
    with col2:
        st.image("logo_dicad.png", use_column_width=True) 
        
    st.markdown("<p style='text-align: center; color:#fff; font-size:16px; margin-top:0.5em; font-weight: bold;'>CRM DICAD AMÉRICA</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True) 
    
    section = option_menu(
        menu_title=None, 
        options=["Potenciales", "Negociaciones", "Agregar Cliente", "Calendario"],
        icons=["person-bounding-box", "briefcase", "person-plus", "calendar-date"], 
        default_index=1,
        styles={
            "container": {"padding": "5px!important", "background-color": "#F0F2F6", "border-radius": "10px"},
            "icon": {"color": "#333333", "font-size": "18px"}, 
            "nav-link": {"color": "#333333", "font-size": "16px", "text-align": "left", "margin":"2px 0px", "--hover-color": "#E0E0E0"},
            "nav-link-selected": {"background-color": "#FF6600", "color": "white"},
        }
    )

    st.markdown("---")
    rol_badge = "👑 Admin" if st.session_state.usuario_actual == ADMINISTRADOR else "💼 Asesor"
    st.markdown(f"<div style='text-align: center; color: white; font-size: 14px; margin-bottom: 10px;'>{rol_badge}: <b>{st.session_state.usuario_actual}</b></div>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = None
        st.rerun()

# --- CONEXIÓN A GOOGLE SHEETS ---
GSHEET_URL = st.secrets.get("SHEET_URL", "https://docs.google.com/spreadsheets/d/___/edit#gid=0")

conn = st.connection("gsheets", type=GSheetsConnection)
worksheet_name = "Central Negociaciones"

COLUMNS = [
    "Cliente", "Profesion", "Direccion", "Pais", "Ciudad", "Estado /Prov.", "Empresa", 
    "Cargo", "Telefono", "Email", "N° Cotiz.", "Monto USD / $", "Notas", "Proxima llamada", 
    "Creado", "Asesor", "Estado_Nego", "Link_PDF"
]

@st.cache_data(ttl=60)
def get_data():
    df = conn.read(spreadsheet=GSHEET_URL)
    if df is None:
        df = pd.DataFrame(columns=COLUMNS)
    else:
        df.columns = df.columns.str.strip()
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[COLUMNS]
        df = df.fillna('')
        
        # Limpiamos los espacios invisibles y los errores viejos para el CRM
        df['Telefono'] = df['Telefono'].astype(str).str.strip()
        df['Telefono'] = df['Telefono'].replace('#ERROR!', '')
        
    return df

# --- ESCUDO INFALIBLE CONTRA EL FORMULA PARSE ERROR ---
def guardar_datos(df_a_guardar):
    df_safe = df_a_guardar.copy()
    
    # Truco del Espacio: Si arranca con "+", le clavamos un espacio en blanco al principio
    # Google Sheets ve el espacio y dice "Ah, esto es texto, no calculo nada".
    df_safe['Telefono'] = df_safe['Telefono'].astype(str).apply(
        lambda x: f" {x.strip()}" if x.strip().startswith("+") else x.strip()
    )
    
    conn.update(worksheet=worksheet_name, data=df_safe, spreadsheet=GSHEET_URL)
    st.cache_data.clear()

def update_estado(indice, nuevo_estado):
    df_actual = get_data()
    df_actual.at[indice, 'Estado_Nego'] = nuevo_estado
    guardar_datos(df_actual)    

def guardar_gestion(indice, nota_existente, nueva_nota, nueva_fecha_obj, fecha_anterior_str):
    df_actual = get_data()
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    nueva_fecha_str = nueva_fecha_obj.strftime("%d/%m/%Y")

    texto_agregado = ""
    if nueva_nota.strip():
        texto_agregado += f"[{fecha_hoy}] 📝 {nueva_nota}"
    if nueva_fecha_str != str(fecha_anterior_str):
        if texto_agregado:
            texto_agregado += f" | 📅 Reprogramado para: {nueva_fecha_str}"
        else:
            texto_agregado = f"[{fecha_hoy}] 📅 Llamada reprogramada para: {nueva_fecha_str}"

    if texto_agregado:
        nota_previa = str(nota_existente)
        if nota_previa.strip() == "" or nota_previa.lower() == "nan":
            nota_final = texto_agregado
        else:
            nota_final = f"{nota_previa}\n{texto_agregado}"
        df_actual.at[indice, 'Notas'] = nota_final
    
    df_actual.at[indice, 'Proxima llamada'] = nueva_fecha_str
    guardar_datos(df_actual)

def generar_numero_cotizacion(df):
    numeros = []
    for val in df['N° Cotiz.'].dropna():
        digitos = ''.join(filter(str.isdigit, str(val)))
        if digitos:
            numeros.append(int(digitos))
    if not numeros:
        return "001000"
    maximo = max(numeros)
    siguiente = maximo + 1
    if siguiente < 1000:
        siguiente = 1000
    return f"{siguiente:06d}"

df = get_data()

lista_asesores = ["Todos los Asesores"] + list(USUARIOS.keys())
try:
    index_inicio = lista_asesores.index(st.session_state.usuario_actual)
except:
    index_inicio = 0

# --- PESTAÑA 1: POTENCIALES (LEADS) ---
if section == "Potenciales":
    st.markdown("## 🎯 Clientes Potenciales (Aún sin Presupuesto)")
    
    if df.empty:
        st.info("No hay registros todavía.")
    else:
        asesor_seleccionado = st.selectbox("Filtrar por Asesor:", lista_asesores, index=index_inicio)
        
        if asesor_seleccionado == "Todos los Asesores":
            df_potenciales = df[df['Estado_Nego'] == 'Potencial']
        else:
            df_potenciales = df[(df['Asesor'] == asesor_seleccionado) & (df['Estado_Nego'] == 'Potencial')]
            
        st.metric("Total de Clientes Potenciales", len(df_potenciales))
        st.markdown("---")

        for idx, row in df_potenciales.iterrows():
            puede_editar = (st.session_state.usuario_actual == ADMINISTRADOR) or (st.session_state.usuario_actual == row.get('Asesor', ''))

            with st.container():
                st.markdown(
                    f"""
                    <div style="background:white;padding:1em;border-radius:10px; border-left: 5px solid #6c757d;
                    margin-bottom:0.5em; box-shadow:0 1px 4px #d0d6e1; color:black !important;">
                        <b>Cliente:</b> {row.get('Cliente', '')} | <b>Empresa:</b> {row.get('Empresa', '')} <br>
                        <b>Teléfono:</b> {row.get('Telefono', '')} | <b>Email:</b> {row.get('Email', '')} <br>
                        <b>Próx. Llamada:</b> {row.get('Proxima llamada', '')}
                    </div>
                    """, unsafe_allow_html=True
                )
            
            with st.expander(f"Ver / Editar a {row.get('Cliente', '')}", expanded=False):
                if puede_editar:
                    with st.expander("⚙️ Editar Ficha del Cliente", expanded=False):
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            e_cli = st.text_input("Nombre", value=row.get('Cliente',''), key=f"e_cli_pot_{idx}")
                            e_emp = st.text_input("Empresa", value=row.get('Empresa',''), key=f"e_emp_pot_{idx}")
                            e_prof = st.text_input("Profesión", value=row.get('Profesion',''), key=f"e_prof_pot_{idx}")
                            e_cargo = st.text_input("Cargo", value=row.get('Cargo',''), key=f"e_cargo_pot_{idx}")
                            
                        with ce2:
                            pais_actual = str(row.get('Pais',''))
                            idx_pais = 0
                            for i, p in enumerate(CODIGOS_PAISES):
                                if pais_actual.lower() in p.lower() and pais_actual != "":
                                    idx_pais = i
                                    break
                                    
                            e_pais_sel = st.selectbox("País", CODIGOS_PAISES, index=idx_pais, key=f"e_pais_sel_pot_{idx}")
                            e_ciu = st.text_input("Ciudad", value=row.get('Ciudad',''), key=f"e_ciu_pot_{idx}")
                            e_tel = st.text_input("Teléfono (Sin código de país)", value=row.get('Telefono',''), key=f"e_tel_pot_{idx}")
                            e_email = st.text_input("Correo Electrónico", value=row.get('Email',''), key=f"e_mail_pot_{idx}")
                            
                        if st.button("💾 Guardar Cambios de Ficha", key=f"btn_e_pot_{idx}"):
                            p_fin, c_fin = extraer_pais_codigo(e_pais_sel)
                            
                            if e_tel.strip() == "" or e_tel.startswith("+") or c_fin == "":
                                tel_final_edit = e_tel
                            else:
                                if c_fin in e_tel:
                                    tel_final_edit = e_tel
                                else:
                                    tel_final_edit = f"{c_fin} {e_tel}"
                                    
                            df_act = get_data()
                            df_act.at[idx, 'Cliente'] = e_cli
                            df_act.at[idx, 'Empresa'] = e_emp
                            df_act.at[idx, 'Profesion'] = e_prof
                            df_act.at[idx, 'Cargo'] = e_cargo
                            df_act.at[idx, 'Pais'] = p_fin if p_fin != "Otro" else pais_actual
                            df_act.at[idx, 'Ciudad'] = e_ciu
                            df_act.at[idx, 'Telefono'] = tel_final_edit
                            df_act.at[idx, 'Email'] = e_email
                            guardar_datos(df_act)
                            st.rerun()

                st.markdown("**📝 Gestión de Seguimiento (Historial):**")
                st.info(row.get('Notas', 'Sin notas previas.'))
                
                if puede_editar:
                    try:
                        fecha_actual_obj = datetime.strptime(str(row.get('Proxima llamada', '')).strip(), "%d/%m/%Y").date()
                    except:
                        fecha_actual_obj = date.today()
                    
                    col_n1, col_n2, col_n3 = st.columns([1.2, 2.5, 1])
                    with col_n1:
                        nueva_fecha = st.date_input("📅 Reprogramar llamada", value=fecha_actual_obj, key=f"fecha_pot_{idx}")
                    with col_n2:
                        nueva_nota = st.text_input("Agregar nota de hoy:", key=f"nota_pot_{idx}", placeholder="Ej: Me pidió que lo llame el martes...")
                    with col_n3:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("💾 Guardar Gestión", key=f"btn_nota_pot_{idx}", use_container_width=True):
                            guardar_gestion(idx, row.get('Notas', ''), nueva_nota, nueva_fecha, row.get('Proxima llamada', ''))
                            st.rerun()
                    
                    st.markdown("---")
                    st.markdown("**🚀 Promover a Negociación Activa:**")
                    st.caption("Si ya le armaste un presupuesto, agregá los datos aquí antes de promoverlo.")
                    
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        nuevo_monto_prom = st.text_input("Monto Cotizado (Ej: USD 5000)", key=f"prom_m_{idx}")
                    with col_p2:
                        nuevo_link_prom = st.text_input("Link al PDF del Presupuesto", key=f"prom_l_{idx}")

                    if st.button("Confirmar y Promover a Negociación", key=f"promover_{idx}", type="primary", use_container_width=True):
                        df_actual = get_data()
                        df_actual.at[idx, 'Estado_Nego'] = "En Proceso"
                        if nuevo_monto_prom.strip(): df_actual.at[idx, 'Monto USD / $'] = nuevo_monto_prom
                        if nuevo_link_prom.strip(): df_actual.at[idx, 'Link_PDF'] = nuevo_link_prom
                        
                        if not str(df_actual.at[idx, 'N° Cotiz.']).strip():
                            df_actual.at[idx, 'N° Cotiz.'] = generar_numero_cotizacion(df_actual)
                            
                        guardar_datos(df_actual)
                        st.rerun()
                else:
                    st.warning("🔒 Modo Lectura: Solo el Administrador o el Asesor asignado pueden editar este contacto.")

# --- PESTAÑA 2: NEGOCIACIONES ---
elif section == "Negociaciones":
    st.markdown("## :card_index_dividers: Negociaciones Activas")

    if df.empty:
        st.info("No hay negociaciones registradas todavía.")
    else:
        if st.session_state.usuario_actual == ADMINISTRADOR:
            st.markdown("### 🏢 TOTAL GLOBAL EMPRESA (Todos los Asesores)")
            df_global = df[(df['Estado_Nego'] != 'Potencial') & (df['Estado_Nego'] != '')]
            
            tot_g_usd = sum(limpiar_monto_para_suma(x) for x in df_global['Monto USD / $'] if "USD" in str(x).upper())
            tot_g_ars = sum(limpiar_monto_para_suma(x) for x in df_global['Monto USD / $'] if "ARS" in str(x).upper())
            
            cg1, cg2, cg3 = st.columns(3)
            cg1.metric("💰 USD Total Global", f"USD {tot_g_usd:,.0f}")
            cg2.metric("💵 ARS Total Global", f"ARS {tot_g_ars:,.0f}")
            cg3.metric("🤝 Total Negociaciones Históricas", len(df_global))
            st.markdown("---")

        st.markdown("### 👔 Vista por Asesor")
        asesor_seleccionado = st.selectbox("Filtrar métricas por Asesor:", lista_asesores, index=index_inicio)

        if asesor_seleccionado == "Todos los Asesores":
            df_tablero = df[(df['Estado_Nego'] != 'Potencial') & (df['Estado_Nego'] != '')]
        else:
            df_tablero = df[(df['Asesor'] == asesor_seleccionado) & (df['Estado_Nego'] != 'Potencial') & (df['Estado_Nego'] != '')]

        st.markdown("<br>", unsafe_allow_html=True)

        total_usd = sum(limpiar_monto_para_suma(x) for x in df_tablero['Monto USD / $'] if "USD" in str(x).upper())
        total_ars = sum(limpiar_monto_para_suma(x) for x in df_tablero['Monto USD / $'] if "ARS" in str(x).upper())

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(label="💰 Cotizado (USD)", value=f"USD {total_usd:,.0f}")
        kpi2.metric(label="💵 Cotizado (ARS)", value=f"ARS {total_ars:,.0f}")
        kpi3.metric(label="🤝 Negociaciones Filtradas", value=f"{len(df_tablero)}")

        st.markdown("---") 
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            df_grafico = df_tablero.copy()
            df_grafico['Plata_USD'] = df_grafico['Monto USD / $'].apply(lambda x: limpiar_monto_para_suma(x) if "USD" in str(x).upper() else 0.0)
            
            if not df_grafico.empty and df_grafico['Plata_USD'].sum() > 0:
                datos_torta = df_grafico.groupby('Estado_Nego')['Plata_USD'].sum().reset_index()
                fig_torta = px.pie(datos_torta, values='Plata_USD', names='Estado_Nego', 
                                 title=f'Monto en Dólares ({asesor_seleccionado})',
                                 hole=0.4, color='Estado_Nego',
                                 color_discrete_map={'Ganada':'#28a745', 'Perdida':'#dc3545', 'En Proceso':'#ffc107'})
                fig_torta.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_torta, use_container_width=True)
            else:
                st.info("No hay montos en USD para graficar.")

        with col_graf2:
            if not df_tablero.empty:
                datos_barras = df_tablero['Asesor'].value_counts().reset_index()
                datos_barras.columns = ['Asesor', 'Cantidad']
                fig_barras = px.bar(datos_barras, x='Asesor', y='Cantidad', title='Cantidad de Negociaciones', color='Asesor')
                st.plotly_chart(fig_barras, use_container_width=True)

        col_busq, col_refresco = st.columns([4, 1])
        with col_busq:
            busqueda = st.text_input("🔍 Buscar Cliente/Empresa en Negociaciones:")
        with col_refresco:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Actualizar Datos"):
                st.cache_data.clear()
                st.rerun()
                
        if busqueda:
            df_filtrado = df_tablero[
                df_tablero['Cliente'].astype(str).str.contains(busqueda, case=False, na=False) |
                df_tablero['Empresa'].astype(str).str.contains(busqueda, case=False, na=False)  
            ]
        else:
            df_filtrado = df_tablero

        for idx, row in df_filtrado.iterrows():
            estado_actual = row.get('Estado_Nego', 'En Proceso')
            puede_editar = (st.session_state.usuario_actual == ADMINISTRADOR) or (st.session_state.usuario_actual == row.get('Asesor', ''))

            if estado_actual == 'Ganada':
                borde_color = "#28a745"
                badge = "<span style='float:right; background-color:#28a745; color:white; padding:4px 8px; border-radius:6px; font-size:12px; font-weight:bold;'>✅ GANADA</span>"
            elif estado_actual == 'Perdida':
                borde_color = "#dc3545"
                badge = "<span style='float:right; background-color:#dc3545; color:white; padding:4px 8px; border-radius:6px; font-size:12px; font-weight:bold;'>❌ PERDIDA</span>"
            else:
                borde_color = "#ffc107"
                badge = "<span style='float:right; background-color:#ffc107; color:black; padding:4px 8px; border-radius:6px; font-size:12px; font-weight:bold;'>⏳ EN PROCESO</span>"

            with st.container():
                st.markdown(
                    f"""
                    <div class="crm-neg-card" style="background:white;padding:1.3em;border-radius:12px;
                    margin-bottom:0.6em; box-shadow:0 1px 8px #d0d6e1; border-left: 6px solid {borde_color}; color:black !important;">
                        {badge}
                        <b>Cliente:</b> {row.get('Cliente', '')} | <b>N° Cotiz:</b> <span style="color:#6c757d">{row.get('N° Cotiz.', 'N/A')}</span><br>
                        <b>Empresa:</b> {row.get('Empresa', '')} <br>
                        <b>Monto USD / $:</b> <span style="color:#2261b6; font-weight:bold;">{row.get('Monto USD / $', '')}</span>
                    </div>
                    """, unsafe_allow_html=True
                )

            with st.expander(f"Ver Ficha Completa de {row.get('Cliente', '')}", expanded=False):
                if puede_editar:
                    with st.expander("⚙️ Editar Datos del Contacto", expanded=False):
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            e_cli = st.text_input("Nombre", value=row.get('Cliente',''), key=f"e_cli_neg_{idx}")
                            e_emp = st.text_input("Empresa", value=row.get('Empresa',''), key=f"e_emp_neg_{idx}")
                            e_prof = st.text_input("Profesión", value=row.get('Profesion',''), key=f"e_prof_neg_{idx}")
                            e_cargo = st.text_input("Cargo", value=row.get('Cargo',''), key=f"e_cargo_neg_{idx}")
                            
                        with ce2:
                            pais_actual = str(row.get('Pais',''))
                            idx_pais = 0
                            for i, p in enumerate(CODIGOS_PAISES):
                                if pais_actual.lower() in p.lower() and pais_actual != "":
                                    idx_pais = i
                                    break
                                    
                            e_pais_sel = st.selectbox("País", CODIGOS_PAISES, index=idx_pais, key=f"e_pais_sel_neg_{idx}")
                            e_ciu = st.text_input("Ciudad", value=row.get('Ciudad',''), key=f"e_ciu_neg_{idx}")
                            e_tel = st.text_input("Teléfono (Sin código de país)", value=row.get('Telefono',''), key=f"e_tel_neg_{idx}")
                            e_email = st.text_input("Correo Electrónico", value=row.get('Email',''), key=f"e_mail_neg_{idx}")
                            
                        if st.button("💾 Guardar Cambios de Contacto", key=f"btn_e_neg_{idx}"):
                            p_fin, c_fin = extraer_pais_codigo(e_pais_sel)
                            
                            if e_tel.strip() == "" or e_tel.startswith("+") or c_fin == "":
                                tel_final_edit = e_tel
                            else:
                                if c_fin in e_tel:
                                    tel_final_edit = e_tel
                                else:
                                    tel_final_edit = f"{c_fin} {e_tel}"
                                    
                            df_act = get_data()
                            df_act.at[idx, 'Cliente'] = e_cli
                            df_act.at[idx, 'Empresa'] = e_emp
                            df_act.at[idx, 'Profesion'] = e_prof
                            df_act.at[idx, 'Cargo'] = e_cargo
                            df_act.at[idx, 'Pais'] = p_fin if p_fin != "Otro" else pais_actual
                            df_act.at[idx, 'Ciudad'] = e_ciu
                            df_act.at[idx, 'Telefono'] = tel_final_edit
                            df_act.at[idx, 'Email'] = e_email
                            guardar_datos(df_act)
                            st.rerun()

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Profesión:** {row.get('Profesion', '')} | **Cargo:** {row.get('Cargo', '')}")
                    st.markdown(f"**Empresa:** {row.get('Empresa', '')}")
                    st.markdown(f"**País:** {row.get('Pais', '')} | **Ciudad:** {row.get('Ciudad', '')}")
                    st.markdown(f"**Teléfono:** {row.get('Telefono', '')}")
                    st.markdown(f"**Email:** {row.get('Email', '')}")
                with col2:
                    st.markdown(f"**N° Cotiz.:** {row.get('N° Cotiz.', '')}")
                    st.markdown(f"**Próxima llamada:** {row.get('Proxima llamada', '')}")
                    st.markdown(f"**Asesor comercial:** {row.get('Asesor', '')}")
                    st.markdown(f"**Estado Actual:** {row.get('Estado_Nego', '')}")
                
                if 'Link_PDF' in row and str(row.get('Link_PDF', '')).strip() != "":
                    st.link_button("📄 Abrir Presupuesto PDF", row['Link_PDF'], use_container_width=True)

                # --- HISTORIAL Y MÚLTIPLES COTIZACIONES ---
                st.markdown("---")
                st.markdown("### 🗂️ Historial y Múltiples Cotizaciones")
                
                cliente_email = str(row.get('Email', '')).strip().lower()
                cliente_tel = str(row.get('Telefono', '')).replace(" ", "").replace("+", "")
                
                if cliente_email:
                    df_cliente = df_tablero[df_tablero['Email'].str.lower().str.strip() == cliente_email]
                else:
                    df_cliente = df_tablero[df_tablero['Telefono'].str.replace(" ", "").str.replace("+", "") == cliente_tel]
                    
                total_cliente_usd = sum(limpiar_monto_para_suma(m) for m in df_cliente['Monto USD / $'] if "USD" in str(m).upper())
                st.info(f"**💰 Monto Total Cotizado a {row.get('Cliente', '')}:** USD {total_cliente_usd:,.0f} (En {len(df_cliente)} cotizaciones activas/cerradas)")
                
                if puede_editar:
                    with st.expander("➕ Agregar Nueva Cotización a este Cliente", expanded=False):
                        st.markdown("Genera un nuevo presupuesto para este cliente sin tener que cargar todos sus datos de nuevo.")
                        col_nc1, col_nc2 = st.columns(2)
                        with col_nc1:
                            nc_monto = st.text_input("Nuevo Monto Numérico", key=f"nc_m_{idx}")
                            nc_moneda = st.selectbox("Moneda", ["USD", "ARS"], key=f"nc_mon_{idx}")
                        with col_nc2:
                            nc_cotiz = st.text_input("N° Cotiz (Vacío = Auto)", key=f"nc_cot_{idx}")
                            nc_pdf = st.text_input("Link al PDF", key=f"nc_pdf_{idx}")
                            
                        if st.button("✅ Generar Nueva Cotización", key=f"btn_nc_{idx}"):
                            df_actual = get_data()
                            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                            cotiz_final = nc_cotiz.strip() if nc_cotiz.strip() else generar_numero_cotizacion(df_actual)
                            monto_final = f"{nc_moneda} {nc_monto}" if nc_monto.strip() else ""
                            
                            nuevo_dato = pd.DataFrame([{
                                "Creado": fecha_hoy,
                                "Cliente": row.get('Cliente', ''),
                                "Profesion": row.get('Profesion', ''),
                                "Direccion": row.get('Direccion', ''), 
                                "Pais": row.get('Pais', ''), 
                                "Ciudad": row.get('Ciudad', ''), 
                                "Estado /Prov.": row.get('Estado /Prov.', ''),
                                "Empresa": row.get('Empresa', ''), 
                                "Cargo": row.get('Cargo', ''), 
                                "Telefono": row.get('Telefono', ''), 
                                "Email": row.get('Email', ''),
                                "N° Cotiz.": cotiz_final,
                                "Monto USD / $": monto_final,
                                "Notas": f"[{fecha_hoy}] 📝 Se agregó una cotización adicional para el cliente.",
                                "Proxima llamada": row.get('Proxima llamada', ''),
                                "Asesor": row.get('Asesor', ''),
                                "Estado_Nego": "En Proceso",
                                "Link_PDF": nc_pdf.strip()
                            }])
                            
                            df_actualizado = pd.concat([df_actual, nuevo_dato], ignore_index=True)
                            guardar_datos(df_actualizado)
                            st.success("Nueva cotización agregada con éxito.")
                            st.rerun()

                st.markdown("---")
                st.markdown("**📝 Gestión de Llamadas:**")
                st.info(row.get('Notas', 'Sin notas previas.'))
                
                if puede_editar:
                    try:
                        fecha_actual_obj = datetime.strptime(str(row.get('Proxima llamada', '')).strip(), "%d/%m/%Y").date()
                    except:
                        fecha_actual_obj = date.today()
                    
                    col_n1, col_n2, col_n3 = st.columns([1.2, 2.5, 1])
                    with col_n1:
                        nueva_fecha = st.date_input("📅 Reprogramar llamada", value=fecha_actual_obj, key=f"fecha_neg_{idx}")
                    with col_n2:
                        nueva_nota = st.text_input("Agregar nota de hoy:", key=f"nota_neg_{idx}", placeholder="Ej: Quedó en ver el PDF...")
                    with col_n3:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("💾 Guardar Gestión", key=f"btn_nota_neg_{idx}", use_container_width=True):
                            guardar_gestion(idx, row.get('Notas', ''), nueva_nota, nueva_fecha, row.get('Proxima llamada', ''))
                            st.rerun()
                    
                    st.markdown("---")
                    st.markdown("**✏️ Modificar Cotización Actual:**")
                    col_e1, col_e2, col_e3 = st.columns([1.5, 2, 1])
                    with col_e1:
                        edit_monto = st.text_input("Monto Cotizado", value=str(row.get('Monto USD / $', '')), key=f"edit_m_{idx}")
                    with col_e2:
                        edit_link = st.text_input("Link al PDF", value=str(row.get('Link_PDF', '')), key=f"edit_l_{idx}")
                    with col_e3:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("💾 Actualizar", key=f"save_edit_{idx}"):
                            df_actual = get_data()
                            df_actual.at[idx, 'Monto USD / $'] = edit_monto
                            df_actual.at[idx, 'Link_PDF'] = edit_link
                            guardar_datos(df_actual)
                            st.success("¡Datos actualizados!")
                            st.rerun()

                    st.markdown("---")
                    st.markdown("**💰 Resolución de la Negociación:**")
                    
                    if estado_actual in ['Ganada', 'Perdida']:
                        st.info(f"Esta negociación ya se encuentra cerrada como **{estado_actual.upper()}**.")
                        if st.button("🔄 Reabrir Negociación a 'En Proceso'", key=f"reabrir_{idx}"):
                            df_actual = get_data()
                            df_actual.at[idx, 'Estado_Nego'] = "En Proceso"
                            guardar_datos(df_actual)
                            st.rerun()
                    else:
                        col_g, col_p = st.columns(2)
                        with col_g:
                            if st.button("✅ Marcar como GANADA", key=f"ganar_{idx}", use_container_width=True):
                                df_actual = get_data()
                                df_actual.at[idx, 'Estado_Nego'] = "Ganada"
                                fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                                texto = f"[{fecha_hoy}] 🏆 NEGOCIACIÓN CERRADA COMO GANADA"
                                nota_previa = str(df_actual.at[idx, 'Notas'])
                                if nota_previa.strip() == "" or nota_previa.lower() == "nan":
                                    df_actual.at[idx, 'Notas'] = texto
                                else:
                                    df_actual.at[idx, 'Notas'] = f"{nota_previa}\n{texto}"
                                guardar_datos(df_actual)
                                st.rerun()
                        with col_p:
                            if st.button("❌ Marcar como PERDIDA", key=f"perder_{idx}", use_container_width=True):
                                df_actual = get_data()
                                df_actual.at[idx, 'Estado_Nego'] = "Perdida"
                                fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                                texto = f"[{fecha_hoy}] ❌ NEGOCIACIÓN MARCADA COMO PERDIDA"
                                nota_previa = str(df_actual.at[idx, 'Notas'])
                                if nota_previa.strip() == "" or nota_previa.lower() == "nan":
                                    df_actual.at[idx, 'Notas'] = texto
                                else:
                                    df_actual.at[idx, 'Notas'] = f"{nota_previa}\n{texto}"
                                guardar_datos(df_actual)
                                st.rerun()    
                else:
                    st.warning("🔒 Modo Lectura: Solo el Administrador o el Asesor asignado pueden modificar o cerrar esta negociación.")

# --- PESTAÑA 3: AGREGAR CLIENTE ---
elif section == "Agregar Cliente":
    st.markdown("<h2>🙋‍♂️ Cargar nuevo Contacto</h2>", unsafe_allow_html=True)
    st.info("💡 Consejo: Completa los datos y haz clic en 'Guardar'. (Si presionas la tecla ENTER por error, la página se recargará por seguridad para evitar guardar datos incompletos).")
    
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0
    fk = st.session_state.form_key
    
    st.markdown("### 1. ¿En qué fase está este contacto?")
    tipo_contacto = st.radio("Seleccione el estado inicial:", [
        "🎯 Potencial Cliente (Solo son primeros contactos, aún NO hay presupuesto)", 
        "💼 Negociación Activa (Ya se le envió un presupuesto)"
    ], label_visibility="collapsed", key=f"tc_{fk}")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        cliente = st.text_input("Nombre del contacto *", key=f"cli_{fk}")
        empresa = st.text_input("Empresa", key=f"emp_{fk}")
        
        pais_seleccionado = st.selectbox("País (Seleccione para autocompletar código)", CODIGOS_PAISES, key=f"pais_sel_{fk}")
        ciudad = st.text_input("Ciudad", key=f"ciu_{fk}")
        
        col_monto, col_moneda = st.columns([2, 1]) 
        with col_monto:
            monto_valor = st.text_input("Monto numérico (Vacío si Potencial)", key=f"mon_{fk}")
        with col_moneda:
            moneda = st.selectbox("Moneda", ["USD", "ARS"], key=f"div_{fk}")
            
    with col2:
        profesion = st.text_input("Profesión", key=f"prof_{fk}")
        cargo = st.text_input("Cargo", key=f"cargo_{fk}")
        
        telefono = st.text_input("Teléfono (Sin código de país)", key=f"tel_{fk}")
        email = st.text_input("Correo Electrónico", key=f"mail_{fk}")
            
        proxima_llamada = st.date_input("Próxima llamada", key=f"prox_{fk}")
        cotizacion = st.text_input("N° Cotiz. (Dejar vacío para autogenerar)", key=f"cot_{fk}")
        
        vendedores = list(USUARIOS.keys())
        try:
            index_vendedor = vendedores.index(st.session_state.usuario_actual)
        except:
            index_vendedor = 0
        
        if st.session_state.usuario_actual == ADMINISTRADOR:
            asesor = st.selectbox("Asesor asignado", vendedores, index=index_vendedor, key=f"ase_{fk}")
        else:
            st.markdown(f"<br>**Asesor asignado:** {st.session_state.usuario_actual}", unsafe_allow_html=True)
            asesor = st.session_state.usuario_actual
        
    st.markdown("---")
    nota_inicial = st.text_area("Nota Inicial del contacto", key=f"notain_{fk}")
    link_pdf = st.text_input("🔗 Link al Presupuesto", placeholder="Enlace a Drive/Dropbox...", key=f"pdf_{fk}")    
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("💾 Guardar en la Base de Datos", type="primary", use_container_width=True):
        if cliente.strip() == "":
            st.warning("⚠️ El Nombre es obligatorio para guardar.")
        else:
            with st.spinner("Guardando y verificando duplicados..."):
                df_actual_temp = conn.read(worksheet=worksheet_name, usecols=list(range(len(COLUMNS))), names=COLUMNS, ttl=5)
                
                pais_final, cod_final = extraer_pais_codigo(pais_seleccionado)
                if telefono.strip() == "" or telefono.startswith("+") or cod_final == "":
                    tel_final = telefono
                else:
                    tel_final = f"{cod_final} {telefono}"

                email_limpio = email.strip().lower()
                tel_limpio = tel_final.replace(" ", "").replace("+", "").replace("-", "")
                
                es_duplicado = False
                for i, r in df_actual_temp.iterrows():
                    r_email = str(r.get('Email', '')).strip().lower()
                    r_tel = str(r.get('Telefono', '')).replace(" ", "").replace("+", "").replace("-", "")
                    
                    if email_limpio != "" and email_limpio == r_email:
                        es_duplicado = True
                        break
                    if tel_limpio != "" and tel_limpio == r_tel:
                        es_duplicado = True
                        break

                if es_duplicado:
                    st.error("🚨 ¡ESTE CLIENTE YA ESTÁ CARGADO! El sistema detectó que este correo o teléfono ya existe en la base de datos. Si quieres agregarle una nueva cotización, búscalo en la pestaña 'Negociaciones' y usa el botón '➕ Nueva Cotización'.")
                else:
                    monto_final = f"{moneda} {monto_valor}" if monto_valor.strip() != "" else ""
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                    estado_inicial = "Potencial" if "Potencial" in tipo_contacto else "En Proceso"
                    
                    cotizacion_final = cotizacion.strip()
                    if estado_inicial == "En Proceso" and cotizacion_final == "":
                        cotizacion_final = generar_numero_cotizacion(df_actual_temp)

                    texto_nota = f"[{fecha_hoy}] 📝 {nota_inicial}" if nota_inicial.strip() else ""

                    nuevo_dato = pd.DataFrame([{
                        "Creado": fecha_hoy,
                        "Cliente": cliente,
                        "Profesion": profesion,
                        "Direccion": "", 
                        "Pais": pais_final, 
                        "Ciudad": ciudad, 
                        "Estado /Prov.": "",
                        "Empresa": empresa, 
                        "Cargo": cargo, 
                        "Telefono": tel_final, 
                        "Email": email,
                        "N° Cotiz.": cotizacion_final,
                        "Monto USD / $": monto_final,
                        "Notas": texto_nota,
                        "Proxima llamada": proxima_llamada.strftime("%d/%m/%Y"),
                        "Asesor": asesor,
                        "Estado_Nego": estado_inicial,
                        "Link_PDF": link_pdf
                    }])
                    
                    try:
                        df_actualizado = pd.concat([df_actual_temp, nuevo_dato], ignore_index=True)
                        guardar_datos(df_actualizado)
                        st.session_state.form_key += 1
                        st.success(f"✅ ¡{cliente} guardado exitosamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

# --- PESTAÑA 4: CALENDARIO ---
elif section == "Calendario":
    col_t1, col_t2 = st.columns([4, 1])
    with col_t1:
        st.markdown("## 📅 Agenda de Seguimientos")
    with col_t2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar Agenda", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
    df = get_data()
    
    if df.empty:
        st.info("No hay clientes registrados todavía.")
    else:
        df_activos = df[df['Estado_Nego'].isin(['En Proceso', 'Potencial'])].copy()
        
        if df_activos.empty:
            st.success("¡Todo al día! No hay clientes esperando seguimiento.")
        else:
            df_activos['Fecha_Orden'] = pd.to_datetime(df_activos['Proxima llamada'], format='%d/%m/%Y', errors='coerce')
            df_ordenado = df_activos.sort_values(by='Fecha_Orden', ascending=True)
            
            st.markdown("Contactos activos ordenados por su fecha de próxima llamada:")
            st.markdown("<br>", unsafe_allow_html=True)
            
            for idx, row in df_ordenado.iterrows():
                fecha_texto = row.get('Proxima llamada', 'Sin fecha')
                cliente = row.get('Cliente', 'Desconocido')
                estado = row.get('Estado_Nego', '')
                puede_editar = (st.session_state.usuario_actual == ADMINISTRADOR) or (st.session_state.usuario_actual == row.get('Asesor', ''))
                
                etiqueta = "🎯 Potencial" if estado == "Potencial" else "💼 En Proceso"
                
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background-color: #2E3E57; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #FF6600;">
                            <h4 style="color: white; margin: 0;">📅 {fecha_texto} | {cliente} <span style="font-size: 14px; font-weight: normal; background-color: #556B8D; padding: 3px 8px; border-radius: 5px; margin-left: 10px;">{etiqueta}</span></h4>
                            <p style="color: #d0d6e1; margin: 5px 0 0 0;">📞 Tel: <b>{row.get('Telefono', '')}</b> | ✉️ <b>{row.get('Email', 'N/A')}</b> | 👔 Asesor: {row.get('Asesor', '')}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                
                if puede_editar:
                    with st.expander(f"⚙️ Editar Ficha de {cliente}", expanded=False):
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            e_cli = st.text_input("Nombre", value=row.get('Cliente',''), key=f"e_cli_cal_{idx}")
                            e_emp = st.text_input("Empresa", value=row.get('Empresa',''), key=f"e_emp_cal_{idx}")
                            e_prof = st.text_input("Profesión", value=row.get('Profesion',''), key=f"e_prof_cal_{idx}")
                            e_cargo = st.text_input("Cargo", value=row.get('Cargo',''), key=f"e_cargo_cal_{idx}")
                            
                        with ce2:
                            pais_actual = str(row.get('Pais',''))
                            idx_pais = 0
                            for i, p in enumerate(CODIGOS_PAISES):
                                if pais_actual.lower() in p.lower() and pais_actual != "":
                                    idx_pais = i
                                    break
                                    
                            e_pais_sel = st.selectbox("País", CODIGOS_PAISES, index=idx_pais, key=f"e_pais_sel_cal_{idx}")
                            e_ciu = st.text_input("Ciudad", value=row.get('Ciudad',''), key=f"e_ciu_cal_{idx}")
                            e_tel = st.text_input("Teléfono (Sin código de país)", value=row.get('Telefono',''), key=f"e_tel_cal_{idx}")
                            e_email = st.text_input("Correo Electrónico", value=row.get('Email',''), key=f"e_mail_cal_{idx}")
                            
                        if st.button("💾 Guardar Cambios de Ficha", key=f"btn_e_cal_{idx}"):
                            p_fin, c_fin = extraer_pais_codigo(e_pais_sel)
                            
                            if e_tel.strip() == "" or e_tel.startswith("+") or c_fin == "":
                                tel_final_edit = e_tel
                            else:
                                if c_fin in e_tel:
                                    tel_final_edit = e_tel
                                else:
                                    tel_final_edit = f"{c_fin} {e_tel}"
                                    
                            df_act = get_data()
                            df_act.at[idx, 'Cliente'] = e_cli
                            df_act.at[idx, 'Empresa'] = e_emp
                            df_act.at[idx, 'Profesion'] = e_prof
                            df_act.at[idx, 'Cargo'] = e_cargo
                            df_act.at[idx, 'Pais'] = p_fin if p_fin != "Otro" else pais_actual
                            df_act.at[idx, 'Ciudad'] = e_ciu
                            df_act.at[idx, 'Telefono'] = tel_final_edit
                            df_act.at[idx, 'Email'] = e_email
                            guardar_datos(df_act)
                            st.rerun()