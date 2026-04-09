import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date
import pandas as pd

# --- CONFIGURACION DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="CRM DICAD AMÉRICA", layout="wide")
st.markdown("""
    <style>
    /* 1. Recuperar el color negro para que se lea el texto en las tarjetas blancas */
    .crm-neg-card * {
        color: black !important;
    }
    
    /* 2. Estilo limpio para los botones */
    .stButton>button {
        border-radius: 7px;
        border: 1px solid #2261b6;
    }
    
    /* 3. Bloqueo suave del texto azul en el menú lateral (sin romper la app) */
    [data-testid="stSidebar"] label {
        user-select: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.markdown(
    "<h2 style='color:#fff; margin-bottom:1em;'>CRM DICAD AMÉRICA</h2>", 
    unsafe_allow_html=True
)
section = st.sidebar.radio(
    "Ir a:", 
    ["Negociaciones", "Agregar Cliente", "Calendario"], 
    key="choose_section"
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
    "Asesor comercial",
    "Creado"
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

# --- SECCION NEGOCIACIONES ---
if section == "Negociaciones":
    st.markdown("## :card_index_dividers: Negociaciones")

    df = get_data()
    if df.empty:
        st.info("No hay negociaciones registradas todavía.")
    else:
        for idx, row in df.iterrows():
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
                        st.markdown(f"**Asesor comercial:** {row.get('Asesor comercial', '')}")
                        creado = row.get('Creado', '')
                        st.markdown(f"**Creado:** {creado if creado else 'N/A'}")

# --- SECCION AGREGAR CLIENTE ---
if section == "Agregar Cliente":
    st.markdown("## :man-raising-hand: Agregar nuevo cliente/negociación")

    with st.form("nuevo_cliente"):
        col1, col2 = st.columns(2)
        cliente = col1.text_input("Nombre del cliente *")
        profesion = col2.text_input("Profesión")
        direccion = col1.text_input("Dirección")
        pais = col2.text_input("País")
        ciudad = col1.text_input("Ciudad")
        estado_prov = col2.text_input("Estado /Prov.")   # Corrige el label para coincidir con la columna exacta
        empresa = col1.text_input("Empresa")
        cargo = col2.text_input("Cargo")
        telefono = col1.text_input("Teléfono")
        n_cotiz = col2.text_input("N° Cotiz.")
        monto = col1.text_input("Monto USD / $")
        notas = col2.text_area("Notas")
        proxima_llamada = col1.date_input("Proxima llamada", value=date.today(), key="proxima_llamada")  # Sin tilde, para coincidir con columna
        asesor_comercial = col2.selectbox("Asesor comercial", ["Ricardo Ippolito", "Gustavo Carballo", "Santiago Yagüe", "Joaquin Pons"])
        # No se captura 'Creado', se autogenera

        submitted = st.form_submit_button("Agregar")

    if submitted:
        if cliente.strip() == "":
            st.error("El nombre del cliente es obligatorio.")
        else:
            row = [
                cliente,
                profesion,
                direccion,
                pais,
                ciudad,
                estado_prov,
                empresa,
                cargo,
                telefono,
                n_cotiz,
                monto,
                notas,
                proxima_llamada.strftime("%Y-%m-%d") if isinstance(proxima_llamada, (datetime, date)) else proxima_llamada,
                asesor_comercial,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ]
            save_data(row)
            st.success(f"Cliente '{cliente}' agregado correctamente.")

# --- SECCION CALENDARIO ---
if section == "Calendario":
    st.markdown("## :calendar: Calendario de llamadas")

    df = get_data()
    if df.empty:
        st.info("No hay datos de negociaciones aún.")
    else:
        # Maneja conversiones para "Proxima llamada"
        df['Proxima llamada'] = pd.to_datetime(df['Proxima llamada'], errors='coerce').dt.date
        hoy = date.today()
        pendientes = df[df['Proxima llamada'] <= hoy]

        if pendientes.empty:
            st.success("¡No hay llamadas pendientes ni vencidas hoy! 🎉")
        else:
            st.warning(f"Hay {len(pendientes)} llamadas pendientes o vencidas:")
            for idx, row in pendientes.iterrows():
                color = "#2261b6" if row.get("Proxima llamada", '') == hoy else "#e87060"
                st.markdown(
                    f"""
                    <div style="background:white;padding:1em 1.3em;border-radius:9px;
                    margin-bottom:1em; border-left: 6px solid {color}; box-shadow:0 1px 5px #e6eaf2;">
                        <b>Cliente:</b> {row.get('Cliente', '')} <br>
                        <b>Asesor comercial:</b> {row.get('Asesor comercial', '')} <br>
                        <b>Empresa:</b> {row.get('Empresa', '')} <br>
                        <b>Proxima llamada:</b> 
                          <span style="background:{color};color:#fff;padding:2px 7px; border-radius:3px">
                            {row.get('Proxima llamada', '').strftime('%d/%m/%Y') if pd.notnull(row.get('Proxima llamada', '')) and row.get('Proxima llamada', '') else ''}
                          </span>
                        <br>
                        <b>Monto USD / $:</b> {row.get('Monto USD / $', '')} <br>
                        <i>{row.get('Notas', '')}</i>
                    </div>
                    """, unsafe_allow_html=True)