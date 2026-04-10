import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px

# --- CONFIGURACION DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="CRM DICAD AMÉRICA", layout="wide")

# --- 1. BASE DE DATOS DE USUARIOS (Ocultas por seguridad) ---
USUARIOS = st.secrets["passwords"]

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
    # Retiramos el "* {color: white}" para que los botones y el menú se vean bien
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
    
    # EL MENÚ (Ahora con fondo gris claro y letras negras para resaltar)
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
    st.markdown(f"<div style='text-align: center; color: white; font-size: 14px; margin-bottom: 10px;'>👤 Asesor: <b>{st.session_state.usuario_actual}</b></div>", unsafe_allow_html=True)
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
    "Cargo", "Telefono", "N° Cotiz.", "Monto USD / $", "Notas", "Proxima llamada", 
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
    return df

def update_estado(indice, nuevo_estado):
    df_actual = get_data()
    df_actual.at[indice, 'Estado_Nego'] = nuevo_estado
    conn.update(worksheet=worksheet_name, data=df_actual, spreadsheet=GSHEET_URL)    

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
    conn.update(worksheet=worksheet_name, data=df_actual, spreadsheet=GSHEET_URL)

df = get_data()

# --- 0. LÓGICA DE FILTROS GLOBALES ---
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
            with st.container():
                st.markdown(
                    f"""
                    <div style="background:white;padding:1em;border-radius:10px; border-left: 5px solid #6c757d;
                    margin-bottom:0.5em; box-shadow:0 1px 4px #d0d6e1; color:black !important;">
                        <b>Cliente:</b> {row.get('Cliente', '')} | <b>Empresa:</b> {row.get('Empresa', '')} <br>
                        <b>Teléfono:</b> {row.get('Telefono', '')} | <b>Próx. Llamada:</b> {row.get('Proxima llamada', '')}
                    </div>
                    """, unsafe_allow_html=True
                )
            
            with st.expander(f"Ver / Editar a {row.get('Cliente', '')}", expanded=False):
                st.markdown("**📝 Gestión de Seguimiento (Historial):**")
                st.info(row.get('Notas', 'Sin notas previas.'))
                
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
                        st.cache_data.clear()
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
                    
                    conn.update(worksheet=worksheet_name, data=df_actual, spreadsheet=GSHEET_URL)
                    st.cache_data.clear()
                    st.rerun()

# --- PESTAÑA 2: NEGOCIACIONES ---
elif section == "Negociaciones":
    st.markdown("## :card_index_dividers: Negociaciones Activas")

    if df.empty:
        st.info("No hay negociaciones registradas todavía.")
    else:
        st.markdown("### 👔 Vista de Administrador")
        asesor_seleccionado = st.selectbox("Filtrar métricas por Asesor:", lista_asesores, index=index_inicio)

        if asesor_seleccionado == "Todos los Asesores":
            df_tablero = df[(df['Estado_Nego'] != 'Potencial') & (df['Estado_Nego'] != '')]
        else:
            df_tablero = df[(df['Asesor'] == asesor_seleccionado) & (df['Estado_Nego'] != 'Potencial') & (df['Estado_Nego'] != '')]

        st.markdown("<br>", unsafe_allow_html=True)

        total_usd = 0
        total_ars = 0

        for val in df_tablero['Monto USD / $'].dropna():
            val_str = str(val).upper()
            if "USD" in val_str:
                numero = val_str.replace("USD", "").replace(",", "").strip()
                try: total_usd += float(numero)
                except: pass
            elif "ARS" in val_str:
                numero = val_str.replace("ARS", "").replace(",", "").strip()
                try: total_ars += float(numero)
                except: pass

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(label="💰 Total Cotizado (USD)", value=f"USD {total_usd:,.0f}")
        kpi2.metric(label="💵 Total Cotizado (ARS)", value=f"ARS {total_ars:,.0f}")
        kpi3.metric(label="🤝 Negociaciones", value=f"{len(df_tablero)}")

        st.markdown("---") 
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            def extraer_usd(valor):
                texto = str(valor).upper()
                if "USD" in texto:
                    numero = texto.replace("USD", "").replace(",", "").strip()
                    try: return float(numero)
                    except: return 0.0
                return 0.0
            
            df_grafico = df_tablero.copy()
            df_grafico['Plata_USD'] = df_grafico['Monto USD / $'].apply(extraer_usd)
            
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
            with st.container():
                st.markdown(
                    f"""
                    <div class="crm-neg-card" style="background:white;padding:1.3em;border-radius:12px;
                    margin-bottom:0.6em; box-shadow:0 1px 8px #d0d6e1; color:black !important;">
                        <b>Cliente:</b> {row.get('Cliente', '')} <br>
                        <b>Empresa:</b> {row.get('Empresa', '')} <br>
                        <b>Monto USD / $:</b> <span style="color:#2261b6">{row.get('Monto USD / $', '')}</span>
                    </div>
                    """, unsafe_allow_html=True
                )

            with st.expander(f"Ver detalles de {row.get('Cliente', '')}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Teléfono:** {row.get('Telefono', '')}")
                    st.markdown(f"**Empresa:** {row.get('Empresa', '')}")
                    st.markdown(f"**N° Cotiz.:** {row.get('N° Cotiz.', '')}")
                with col2:
                    st.markdown(f"**Próxima llamada:** {row.get('Proxima llamada', '')}")
                    st.markdown(f"**Asesor comercial:** {row.get('Asesor', '')}")
                    st.markdown(f"**Estado Actual:** {row.get('Estado_Nego', '')}")
                
                st.markdown("---")
                st.markdown("**📝 Gestión de Seguimiento (Historial):**")
                st.info(row.get('Notas', 'Sin notas previas.'))
                
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
                        st.cache_data.clear()
                        st.rerun()
                
                st.markdown("---")
                st.markdown("**✏️ Actualizar Datos del Presupuesto:**")
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
                        conn.update(worksheet=worksheet_name, data=df_actual, spreadsheet=GSHEET_URL)
                        st.cache_data.clear()
                        st.success("¡Datos actualizados!")
                        st.rerun()

                if 'Link_PDF' in row and str(row.get('Link_PDF', '')).strip() != "":
                    st.markdown("---")
                    st.link_button("📄 Abrir Presupuesto PDF", row['Link_PDF'], use_container_width=True)
                
                st.markdown("---")
                st.markdown("**💰 Resolución de la Negociación:**")
                col_g, col_p = st.columns(2)
                with col_g:
                    if st.button("✅ Marcar como GANADA", key=f"ganar_{idx}", use_container_width=True):
                        update_estado(idx, "Ganada")
                        st.cache_data.clear()
                        st.rerun()
                with col_p:
                    if st.button("❌ Marcar como PERDIDA", key=f"perder_{idx}", use_container_width=True):
                        update_estado(idx, "Perdida")
                        st.cache_data.clear()
                        st.rerun()    

# --- PESTAÑA 3: AGREGAR CLIENTE ---
elif section == "Agregar Cliente":
    st.markdown("<h2>🙋‍♂️ Cargar nuevo Contacto</h2>", unsafe_allow_html=True)
    
    with st.form("form_nuevo_cliente", clear_on_submit=True):
        st.markdown("### 1. ¿En qué fase está este contacto?")
        tipo_contacto = st.radio("Seleccione el estado inicial:", [
            "🎯 Potencial Cliente (Solo son primeros contactos, aún NO hay presupuesto)", 
            "💼 Negociación Activa (Ya se le envió un presupuesto)"
        ], label_visibility="collapsed")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Nombre del contacto *")
            empresa = st.text_input("Empresa")
            telefono = st.text_input("Teléfono")
            
            col_monto, col_moneda = st.columns([2, 1]) 
            with col_monto:
                monto_valor = st.text_input("Monto numérico (Dejar vacío si es Potencial)")
            with col_moneda:
                moneda = st.selectbox("Moneda", ["USD", "ARS"])
                
            proxima_llamada = st.date_input("Próxima llamada de seguimiento")
            
        with col2:
            profesion = st.text_input("Profesión / Cargo")
            pais = st.text_input("País / Ciudad")
            cotizacion = st.text_input("N° Cotiz. (Si la hay)")
            nota_inicial = st.text_area("Nota Inicial del contacto")
            
            vendedores = list(USUARIOS.keys())
            try:
                index_vendedor = vendedores.index(st.session_state.usuario_actual)
            except:
                index_vendedor = 0
            asesor = st.selectbox("Asesor comercial asignado", vendedores, index=index_vendedor)
            
        st.markdown("---")
        link_pdf = st.text_input("🔗 Link al Presupuesto (Si ya lo tiene)", placeholder="Pegue aquí el enlace a Drive/Dropbox...")    
            
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.form_submit_button("Guardar en la Base de Datos", type="primary")
        
        if submit_btn:
            if cliente.strip() == "":
                st.warning("⚠️ El Nombre es obligatorio.")
            else:
                with st.spinner("Guardando..."):
                    monto_final = f"{moneda} {monto_valor}" if monto_valor.strip() != "" else ""
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                    
                    estado_inicial = "Potencial" if "Potencial" in tipo_contacto else "En Proceso"
                    texto_nota = f"[{fecha_hoy}] 📝 {nota_inicial}" if nota_inicial.strip() else ""

                    nuevo_dato = pd.DataFrame([{
                        "Creado": fecha_hoy,
                        "Cliente": cliente,
                        "Profesion": profesion,
                        "Direccion": "", "Pais": pais, "Ciudad": "", "Estado /Prov.": "",
                        "Empresa": empresa, "Cargo": "", "Telefono": telefono,
                        "N° Cotiz.": cotizacion,
                        "Monto USD / $": monto_final,
                        "Notas": texto_nota,
                        "Proxima llamada": proxima_llamada.strftime("%d/%m/%Y"),
                        "Asesor": asesor,
                        "Estado_Nego": estado_inicial,
                        "Link_PDF": link_pdf
                    }])
                    
                    try:
                        df_actual = conn.read(worksheet=worksheet_name, usecols=list(range(len(COLUMNS))), names=COLUMNS, ttl=5)
                        df_actualizado = pd.concat([df_actual, nuevo_dato], ignore_index=True)
                        conn.update(worksheet=worksheet_name, data=df_actualizado)
                        st.cache_data.clear() 
                        st.success(f"✅ ¡{cliente} guardado exitosamente como {estado_inicial}!")
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

# --- PESTAÑA 4: CALENDARIO ---
elif section == "Calendario":
    # Agregamos el botón de refresco al lado del título
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
                
                etiqueta = "🎯 Potencial" if estado == "Potencial" else "💼 En Proceso"
                
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background-color: #2E3E57; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #FF6600;">
                            <h4 style="color: white; margin: 0;">📅 {fecha_texto} | {cliente} <span style="font-size: 14px; font-weight: normal; background-color: #556B8D; padding: 3px 8px; border-radius: 5px; margin-left: 10px;">{etiqueta}</span></h4>
                            <p style="color: #d0d6e1; margin: 5px 0 0 0;">📞 Tel: <b>{row.get('Telefono', '')}</b> | 👔 Asesor: {row.get('Asesor', '')}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )