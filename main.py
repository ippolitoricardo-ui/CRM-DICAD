import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px
# --- CONFIGURACION DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="CRM DICAD AMÉRICA", layout="wide")

# --- 1. BASE DE DATOS DE USUARIOS ---
USUARIOS = {
    "Gustavo Carballo": "dicad2026",
    "Ricardo Ippolito": "ventas01",
    "Santiago Yagüe": "strakon02",
    "Joaquin Pons": "america03"
}

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
    # 1. FORZAR EL FONDO AZUL DICAD Y LETRAS BLANCAS
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            background-color: #2E3E57 !important;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 2. LOGO MÁS GRANDE Y CENTRADO PERFECTO (usando columnas)
    st.write("") # Un pequeño espacio arriba
    col1, col2, col3 = st.columns([1, 4, 1]) # Crea 3 columnas (la del medio es más ancha)
    with col2:
        st.image("logo_dicad.png", use_column_width=True) # La imagen se adapta a la columna central
        
    st.markdown("<p style='text-align: center; color:#fff; font-size:16px; margin-top:0.5em; font-weight: bold;'>CRM DICAD AMÉRICA</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True) # Un espacio antes del menú
    
    # EL NUEVO MENÚ PROFESIONAL
    section = option_menu(
        menu_title=None, 
        options=["Negociaciones", "Agregar Cliente", "Calendario"],
        icons=["briefcase", "person-plus", "calendar-date"], 
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "white", "font-size": "18px"}, 
            "nav-link": {"color": "white", "font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#3373c8"},
            "nav-link-selected": {"background-color": "#FF6600"},
        }
    )

# --- CONEXIÓN A GOOGLE SHEETS ---
GSHEET_URL = st.secrets.get("SHEET_URL", "https://docs.google.com/spreadsheets/d/___/edit#gid=0")  # Usa st.secrets!

# Usando el estándar oficial de st.connection
conn = st.connection("gsheets", type=GSheetsConnection)
worksheet_name = "Central Negociaciones"

# --- COLUMNAS REALES DE LA GOOGLE SHEET ---
COLUMNS = [
    "Cliente",
    "Profesion",
    "Direccion",
    "Pais",
    "Ciudad",
    "Estado /Prov.",
    "Empresa",
    "Cargo",
    "Telefono",
    "N° Cotiz.",
    "Monto USD / $",
    "Notas",
    "Proxima llamada",
    "Creado",
    "Asesor",
    "Estado_Nego",
    "Link_PDF"
]

VENDEDORES = ["Alice", "Bob", "Carlos", "Diana"]  # Puedes modificarlo según tus asesores reales

# --- CARGA Y GUARDADO DE DATOS ---
@st.cache_data(ttl=60)
def get_data():
    df = conn.read(spreadsheet=GSHEET_URL)
    if df is None:
        df = pd.DataFrame(columns=COLUMNS)
    else:
        df.columns = df.columns.str.strip()   # Elimina espacios en los nombres de columnas
        # Si faltan columnas en la Sheet, agrégalas vacías:
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[COLUMNS]  # Ordena las columnas conforme a COLUMNS
        df = df.fillna('')  # Limpia valores vacíos por ''
    return df

def save_data(row):
    df = get_data()
    new_df = pd.concat([df, pd.DataFrame([row], columns=COLUMNS)], ignore_index=True)
    conn.update(worksheet=worksheet_name, data=new_df, spreadsheet=GSHEET_URL)
    
def update_estado(indice, nuevo_estado):
    df_actual = get_data()
    df_actual.at[indice, 'Estado_Nego'] = nuevo_estado
    conn.update(worksheet=worksheet_name, data=df_actual, spreadsheet=GSHEET_URL)    

# --- SECCION NEGOCIACIONES ---
if section == "Negociaciones":
    st.markdown("## :card_index_dividers: Negociaciones")

    df = get_data()
    if df.empty:
        st.info("No hay negociaciones registradas todavía.")
    else:
            # 0. Limpieza automática (Arregla el problema del "0" y los vacíos en los gráficos)
            if 'Estado_Nego' not in df.columns:
                df['Estado_Nego'] = 'En Proceso'
            df['Estado_Nego'] = df['Estado_Nego'].replace(['', '0', 0, None], 'En Proceso').fillna('En Proceso')
            df['Asesor'] = df['Asesor'].replace(['', '0', 0, None], 'Sin Asignar').fillna('Sin Asignar')

# 1. EL FILTRO INTELIGENTE
            st.markdown("### 👔 Vista de Administrador")
            lista_asesores = ["Todos los Asesores"] + list(USUARIOS.keys())
            try:
                index_inicio = lista_asesores.index(st.session_state.usuario_actual)
            except:
                index_inicio = 0
            asesor_seleccionado = st.selectbox("Filtrar métricas por Asesor:", lista_asesores, index=index_inicio)

            # Filtramos la tabla según lo que elijas en el menú
            if asesor_seleccionado == "Todos los Asesores":
                df_tablero = df # Usa todos los datos
            else:
                df_tablero = df[df['Asesor'] == asesor_seleccionado] # Usa solo los de ese asesor

            st.markdown("<br>", unsafe_allow_html=True)

            # 2. LAS TARJETAS NUMÉRICAS (Ahora calculan sobre df_tablero)
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

            # 3. LOS GRÁFICOS (Ahora reaccionan al filtro)
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
                
                # Ojo acá: Usamos una copia para no ensuciar tu Excel original
                df_grafico = df_tablero.copy()
                df_grafico['Plata_USD'] = df_grafico['Monto USD / $'].apply(extraer_usd)
                datos_torta = df_grafico.groupby('Estado_Nego')['Plata_USD'].sum().reset_index()
                
                fig_torta = px.pie(datos_torta, values='Plata_USD', names='Estado_Nego', 
                                 title=f'Monto en Dólares ({asesor_seleccionado})',
                                 hole=0.4,
                                 color='Estado_Nego',
                                 color_discrete_map={'Ganada':'#28a745', 'Perdida':'#dc3545', 'En Proceso':'#ffc107'})
                fig_torta.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_torta, use_container_width=True)

            with col_graf2:
                datos_barras = df_tablero['Asesor'].value_counts().reset_index()
                datos_barras.columns = ['Asesor', 'Cantidad']
                fig_barras = px.bar(datos_barras, x='Asesor', y='Cantidad', 
                                  title='Cantidad de Clientes',
                                  color='Asesor')
                st.plotly_chart(fig_barras, use_container_width=True)
# --- EL BUSCADOR Y EL BOTÓN DE REFRESCO ---
            col_busq, col_refresco = st.columns([4, 1])
            
            with col_busq:
                busqueda = st.text_input("🔍 Buscar por Cliente o Empresa:", placeholder="Ej: Juan Perez...")
                
            with col_refresco:
                st.markdown("<br>", unsafe_allow_html=True) # Para alinear con el buscador
                if st.button("🔄 Actualizar"):
                    st.cache_data.clear() # Limpia la memoria
                    st.rerun() # Reinicia la app para traer los datos nuevos
                    
            # Lógica de filtrado
            if busqueda:
                # Convertimos a texto por las dudas y buscamos coincidencias
                df_filtrado = df[
                    df['Cliente'].astype(str).str.contains(busqueda, case=False, na=False) |
                    df['Empresa'].astype(str).str.contains(busqueda, case=False, na=False)  
                    ]
            else:
                df_filtrado = df # Si no buscó nada, mostramos todo
            # ACA EMPIEZA TU BUCLE ORIGINAL PERO CON LOS DATOS FILTRADOS
            for idx, row in df_filtrado.iterrows():
                with st.container():
                    # Cabecera de tarjeta (agrega color oscuro al texto para buena legibilidad)
                    st.markdown(
                        f"""
                        <div class="crm-neg-card" style="background:white;padding:1.3em;border-radius:12px;
                        margin-bottom:0.6em; box-shadow:0 1px 8px #d0d6e1; color:black !important;">
                            <b>Cliente:</b> {row.get('Cliente', '') if row.get('Cliente', '').strip() else 'N/A'} <br>
                            <b>Empresa:</b> {row.get('Empresa', '') if row.get('Empresa', '').strip() else 'N/A'} <br>
                            <b>Monto USD / $:</b> <span style="color:#2261b6">{row.get('Monto USD / $', '')}</span>
                        </div>
                        """, unsafe_allow_html=True
                    )
                # Expander con más detalles
                cliente_str = row.get('Cliente', '')
                with st.expander(f"Ver detalles de {cliente_str}", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Profesión:** {row.get('Profesion', '')}")
                        st.markdown(f"**Dirección:** {row.get('Direccion', '')}")
                        st.markdown(f"**País:** {row.get('Pais', '')}")
                        st.markdown(f"**Ciudad:** {row.get('Ciudad', '')}")
                        st.markdown(f"**Estado /Prov.:** {row.get('Estado /Prov.', '')}")
                        st.markdown(f"**Cargo:** {row.get('Cargo', '')}")
                        st.markdown(f"**Teléfono:** {row.get('Telefono', '')}")
                        st.markdown(f"**N° Cotiz.:** {row.get('N° Cotiz.', '')}")
                    with col2:
                        st.markdown(f"**Notas:** {row.get('Notas', '')}")
                        proxima_llamada = row.get('Proxima llamada', '')
                        st.markdown(f"**Próxima llamada:** {proxima_llamada if proxima_llamada else 'N/A'}")
                        st.markdown(f"**Asesor comercial:** {row.get('Asesor', '')}")
                        creado = row.get('Creado', '')
                        st.markdown(f"**Creado:** {creado if creado else 'N/A'}")
                    # --- 1. BOTÓN PARA VER EL PRESUPUESTO ---
                    if 'Link_PDF' in row and str(row.get('Link_PDF', '')).strip() != "":
                        st.markdown("---")
                        st.link_button("📄 Abrir Presupuesto PDF", row['Link_PDF'], use_container_width=True)
                    
                    # --- 2. BOTONES DE RESOLUCIÓN (GANADA/PERDIDA) ---
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
                        

# --- PESTAÑA: AGREGAR CLIENTE ---
if section == "Agregar Cliente":
    st.markdown("<h2>🙋‍♂️ Agregar nuevo cliente/negociación</h2>", unsafe_allow_html=True)
    
    with st.form("form_nuevo_cliente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Nombre del cliente *")
            direccion = st.text_input("Dirección")
            ciudad = st.text_input("Ciudad")
            empresa = st.text_input("Empresa")
            telefono = st.text_input("Teléfono")
            
            # --- LA MEJORA DEL MONTO Y MONEDA ---
            # Partimos este pedacito en dos columnas invisibles
            col_monto, col_moneda = st.columns([2, 1]) 
            with col_monto:
                monto_valor = st.text_input("Monto numérico")
            with col_moneda:
                moneda = st.selectbox("Moneda", ["USD", "ARS"])
                
            proxima_llamada = st.date_input("Próxima llamada")
            
        with col2:
            profesion = st.text_input("Profesión")
            pais = st.text_input("País")
            estado = st.text_input("Estado /Prov.")
            cargo = st.text_input("Cargo")
            cotizacion = st.text_input("N° Cotiz.")
            notas = st.text_area("Notas")
            vendedores = list(USUARIOS.keys())
            try:
                index_vendedor = vendedores.index(st.session_state.usuario_actual)
            except:
                index_vendedor = 0
            asesor = st.selectbox("Asesor comercial", vendedores, index=index_vendedor)
            
        st.markdown("---")
        link_pdf = st.text_input("🔗 Link al Presupuesto (Google Drive / Dropbox)", placeholder="Pegue aquí el enlace compartido...")    
            
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.form_submit_button("Agregar Negociación", type="primary")
        
        # --- LA LÓGICA DE GUARDADO ---
        if submit_btn:
            if cliente.strip() == "":
                st.warning("⚠️ El Nombre del cliente es obligatorio para crear la ficha.")
            else:
                with st.spinner("Guardando en la base de datos..."):
                    
                    # 1. Unimos la moneda elegida y el número (Ej: "USD 13000")
                    monto_final = f"{moneda} {monto_valor}" if monto_valor.strip() != "" else ""
                    
                    # 2. Fabricamos la fecha de HOY en formato Día/Mes/Año
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y")

                    # 3. Empaquetamos AHORA SÍ todos los datos
                    nuevo_dato = pd.DataFrame([{
                        "Creado": fecha_hoy,  # <- Acá va la fecha automática
                        "Cliente": cliente,
                        "Profesion": profesion,
                        "Direccion": direccion,
                        "Pais": pais,
                        "Ciudad": ciudad,
                        "Estado /Prov.": estado,
                        "Empresa": empresa,
                        "Cargo": cargo,
                        "Telefono": telefono,
                        "N° Cotiz.": cotizacion,
                        "Monto USD / $": monto_final, # <- Acá viaja el monto fusionado
                        "Notas": notas,
                        "Proxima llamada": proxima_llamada.strftime("%d/%m/%Y"),
                        "Asesor": asesor,
                        "Estado_Nego": "En Proceso",
                        "Link_PDF": link_pdf
                    }])
                    
                    try:
                        df_actual = conn.read(worksheet=worksheet_name, usecols=list(range(len(COLUMNS))), names=COLUMNS, ttl=5)
                        df_actualizado = pd.concat([df_actual, nuevo_dato], ignore_index=True)
                        conn.update(worksheet=worksheet_name, data=df_actualizado)
                        st.cache_data.clear() 
                        st.success(f"✅ ¡La negociación con {cliente} se guardó exitosamente por {monto_final}!")
                    except Exception as e:
                        st.error(f"Hubo un error al intentar guardar: {e}")

# --- SECCIÓN CALENDARIO ---
elif section == "Calendario":
    st.markdown("## 📅 Agenda de Seguimientos")
    
    df = get_data()
    
    if df.empty:
        st.info("No hay clientes registrados todavía.")
    else:
        # 1. Filtramos SOLO los que están "En Proceso" (No queremos llamar a los que ya nos compraron o nos rechazaron)
        if 'Estado_Nego' in df.columns:
            df_activos = df[df['Estado_Nego'] == 'En Proceso'].copy()
        else:
            df_activos = df.copy()
        
        if df_activos.empty:
            st.success("¡Todo al día! No hay clientes en proceso esperando seguimiento.")
        else:
            # 2. Convertimos el texto de la fecha a una "Fecha Real" matemática para que Python sepa cuál va antes
            df_activos['Fecha_Orden'] = pd.to_datetime(df_activos['Proxima llamada'], format='%d/%m/%Y', errors='coerce')
            
            # 3. Ordenamos la tabla de la fecha más urgente (vieja) a la más lejana
            df_ordenado = df_activos.sort_values(by='Fecha_Orden', ascending=True)
            
            st.markdown("Estos son los clientes activos ordenados por su fecha de próxima llamada:")
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 4. Dibujamos la lista como si fuera una agenda de celular
            for idx, row in df_ordenado.iterrows():
                fecha_texto = row.get('Proxima llamada', 'Sin fecha')
                cliente = row.get('Cliente', 'Desconocido')
                empresa = row.get('Empresa', 'Sin empresa')
                tel = row.get('Telefono', 'Sin teléfono')
                asesor = row.get('Asesor', '')
                
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background-color: #2E3E57; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #FF6600;">
                            <h4 style="color: white; margin: 0;">📅 {fecha_texto} | {cliente} ({empresa})</h4>
                            <p style="color: #d0d6e1; margin: 5px 0 0 0;">📞 Tel: <b>{tel}</b> | 👔 Asesor: {asesor}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )