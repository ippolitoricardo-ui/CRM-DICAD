# -*- coding: utf-8 -*-
"""Base Prospectos: importa Excel/CSV con columnas en cualquier orden, unifica sin duplicar y alimenta las campañas."""
import io
import re
import datetime
import unicodedata
import pandas as pd
import streamlit as st

EMAIL = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}')

def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9 ]+', ' ', s).strip()

# header synonyms -> field. Evaluated in order; first match wins for a column.
RULES = [
    ('skip',      r'^(utm|survey|ticket|qr|eth|solana|amount|currency|coupon|api id|guest id|referr|created|checked|approval|has joined|google|meta|x click|linkedin click|tiktok|reddit|yandex|custom source|firmentyp|firmennummer|nicht andern|estado del|indice de atencion|puntuacion|su opinion|dejenos|que opinion|desea recibir|interes|programa|utiliza|observ|coment|asig|asesor|designado|reasig|rere|llamar|resultado|intentos|monto|cierre|fecha|datum|hora|edad|documento|condicion|grupo|docente|campus|tipo|participo|asistido|invitado|control|columna\d|codigo postal|cod postal|direccion|descarga|recuento)'),
    ('skip',      r'^(n|no|n o|numero|nro|id|\d+)$'),
    ('email',     r'(correo|e ?mail|^mail|corre+o?$|^corre$)'),
    ('telefono',  r'(telefon|phone|celular|^tel)'),
    ('fullname',  r'^(nombre y apellido|nombre y apellidos|apellido y nombre|nombre completo|nombre apellido|name|participante|participantes|contacto|kontakt|alumno|primarer kontakt|registrados|inscrito|asistentes|usuario)$'),
    ('nombre',    r'^(nombre|nombres|first name|first_name|vorname)'),
    ('apellido',  r'^(apellido|apellidos|appelido|last name|last_name|nachname)'),
    ('empresa',   r'(empresa|organizacion|firmenname|^firma$|compan|institucion|universidad)'),
    ('profesion', r'(profesion|^tit|titulo$)'),
    ('cargo',     r'(cargo|puesto|position|job)'),
    ('pais',      r'(pais|country|^land$|land region|^region$)'),
    ('provincia', r'(provincia|estado$|state)'),
    ('ciudad',    r'(ciudad|localidad|^ort$|adresse 1 ort|city)'),
]
FIELDS = ['nombre', 'apellido', 'fullname', 'email', 'telefono', 'empresa', 'profesion', 'cargo', 'pais', 'provincia', 'ciudad']

def classify(h):
    n = norm(h)
    if not n:
        return None
    for f, rx in RULES:
        if re.search(rx, n):
            return None if f == 'skip' else f
    return None

def find_header(df):
    best, bi = 0, None
    for i in range(min(30, len(df))):
        vals = [v for v in df.iloc[i].dropna().astype(str) if v.strip()]
        if any(EMAIL.search(v) for v in vals):
            continue
        score = sum(1 for v in vals if classify(v))
        if score > best:
            best, bi = score, i
    return bi if best >= 2 else None

def clean_phone(v):
    s = str(v).strip()
    if s.lower() in ('nan', 'none', ''):
        return ''
    if re.fullmatch(r'\d+\.0', s):
        s = s[:-2]
    d = re.sub(r'[^\d+]', '', s)
    digits = re.sub(r'\D', '', d)
    if len(digits) < 7 or len(digits) > 15 or len(set(digits)) <= 2:
        return ''
    return ('+' + digits) if d.startswith('+') or s.startswith('00') else digits

def nice(v):
    s = re.sub(r'\s+', ' ', str(v)).strip(' ,;-"\'')
    s = re.sub(r'^\d{3,}\s*-\s*', '', s)
    s = re.sub(r'^\d+[\s.)-]+(?=[A-Za-zÁÉÍÓÚÑáéíóúñ])', '', s)
    s = re.sub(r'^(mr|mrs|ms|sr|sra|herr|frau)\.?\s+', '', s, flags=re.I)
    if s.lower() in ('nan', 'none', 'n/a', '-', '.', 'null', '0'):
        return ''
    if s.isupper() or s.islower():
        s = ' '.join(w.capitalize() if len(w) > 2 or i == 0 else w.lower() for i, w in enumerate(s.split(' ')))
    return s

PAISES = {
 'argentina':'Argentina','ar':'Argentina','arg':'Argentina','mexico':'México','mx':'México','mex':'México','peru':'Perú','pe':'Perú',
 'chile':'Chile','cl':'Chile','colombia':'Colombia','co':'Colombia','bolivia':'Bolivia','bo':'Bolivia','ecuador':'Ecuador','ec':'Ecuador',
 'uruguay':'Uruguay','uy':'Uruguay','paraguay':'Paraguay','py':'Paraguay','venezuela':'Venezuela','ve':'Venezuela','brasil':'Brasil','brazil':'Brasil','br':'Brasil',
 'costa rica':'Costa Rica','cr':'Costa Rica','panama':'Panamá','pa':'Panamá','guatemala':'Guatemala','gt':'Guatemala','honduras':'Honduras','hn':'Honduras',
 'el salvador':'El Salvador','salvador':'El Salvador','sv':'El Salvador','nicaragua':'Nicaragua','ni':'Nicaragua','republica dominicana':'Rep. Dominicana',
 'dominican republic':'Rep. Dominicana','do':'Rep. Dominicana','rep dominicana':'Rep. Dominicana','cuba':'Cuba','puerto rico':'Puerto Rico','espana':'España','spain':'España','es':'España',
 'estados unidos':'Estados Unidos','united states':'Estados Unidos','usa':'Estados Unidos','us':'Estados Unidos','eeuu':'Estados Unidos','portugal':'Portugal',
 'argentinien':'Argentina','mexiko':'México','kolumbien':'Colombia','bolivien':'Bolivia','brasilien':'Brasil','spanien':'España',
}
PAISES.update({'col':'Colombia','otro':'','s p':'','sp':'','eu':'Estados Unidos','mexico df':'México','cdmx':'México','pan':'Panamá','can':'Canadá','canada':'Canadá'})
PREFIJOS = [('54','Argentina'),('52','México'),('51','Perú'),('56','Chile'),('57','Colombia'),('591','Bolivia'),('593','Ecuador'),('598','Uruguay'),
            ('595','Paraguay'),('58','Venezuela'),('55','Brasil'),('506','Costa Rica'),('507','Panamá'),('502','Guatemala'),('504','Honduras'),
            ('503','El Salvador'),('505','Nicaragua'),('34','España')]

def pais_norm(v):
    n = norm(v)
    if not n:
        return ''
    if n in PAISES:
        return PAISES[n]
    for k, p in PAISES.items():
        if len(k) > 3 and k in n:
            return p
    return nice(v)

TYPOS = {'gmail.con': 'gmail.com', 'gmial.com': 'gmail.com', 'gmai.com': 'gmail.com', 'gmail.co': 'gmail.com', 'gmail.cm': 'gmail.com',
         'gamil.com': 'gmail.com', 'gnail.com': 'gmail.com', 'gmail.comm': 'gmail.com', 'gmail.om': 'gmail.com', 'hotmail.con': 'hotmail.com',
         'hotmial.com': 'hotmail.com', 'hotmail.co': 'hotmail.com', 'hotmai.com': 'hotmail.com', 'hotmal.com': 'hotmail.com',
         'outlook.con': 'outlook.com', 'outlok.com': 'outlook.com', 'yahoo.con': 'yahoo.com', 'yaho.com': 'yahoo.com', 'hotmail.es.': 'hotmail.es'}
BLOQUEADOS = re.compile(r'@(dlubal\.|dicad|example\.|test\.|mailinator\.)|^(no-?reply|noreply|info@dlubal)')
TLD = {'ar': 'Argentina', 'mx': 'México', 'pe': 'Perú', 'cl': 'Chile', 'co': 'Colombia', 'bo': 'Bolivia', 'ec': 'Ecuador', 'uy': 'Uruguay',
       'py': 'Paraguay', 've': 'Venezuela', 'br': 'Brasil', 'cr': 'Costa Rica', 'pa': 'Panamá', 'gt': 'Guatemala', 'hn': 'Honduras',
       'sv': 'El Salvador', 'ni': 'Nicaragua', 'do': 'Rep. Dominicana', 'es': 'España', 'cu': 'Cuba'}


# ======================================================================
#  Base Prospectos: hoja aparte del Google Sheet con la base unificada
# ======================================================================
HOJA = "Base Prospectos"
COLS = ['ID', 'Cliente', 'Nombre', 'Apellido', 'Profesion', 'Empresa', 'Cargo', 'Pais', 'Provincia', 'Ciudad', 'Telefono', 'Email',
        'Asesor', 'Estado', 'Eventos', 'Origen', 'Primer_registro', 'Ultimo_registro', 'Fecha_Alta', 'Eventos_detalle']


def limpiar_evento(a):
    """Nombre de archivo -> nombre de evento legible (quita extensiones, 'Informe_de_registros', letras decorativas, etc.)."""
    s = unicodedata.normalize('NFKC', str(a))
    s = re.sub(r'\.(xlsx|xls|csv)$', '', s, flags=re.I)
    s = re.sub(r'\s*-\s*(Informe_de_\w+|Invitados).*$', '', s, flags=re.I)
    s = re.sub(r'\(\d+\)|\(version\s*\d\)', '', s, flags=re.I)
    s = re.sub(r'[_“”"¡!¿?|]+', ' ', s)
    s = re.sub(r'[^\w\s\-.,%+]', '', s)
    return re.sub(r'\s+', ' ', s).strip(' -.')


def compactar(t):
    """minúsculas, sin tildes ni espacios: 'Domina el Ciclo BIM' -> 'dominaelciclobim'."""
    t = unicodedata.normalize('NFKD', unicodedata.normalize('NFKC', str(t))).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', t)


STOP = {'el', 'la', 'los', 'las', 'de', 'del', 'en', 'y', 'con', 'a', 'para', 'por', 'un', 'una', 'webinar', 'seminario'}


def eventos_que_coinciden(todos, consulta):
    """Eventos cuyo nombre contiene todas las palabras de la consulta (sin importar espacios, tildes ni mayúsculas)."""
    palabras = [compactar(w) for w in re.split(r'\s+', consulta) if compactar(w) and compactar(w) not in STOP]
    if not palabras:
        return []
    return [e for e in todos if all(p in compactar(e) for p in palabras)]


def _url():
    try:
        return st.secrets.get("SHEET_URL") or None
    except Exception:
        return None


@st.cache_data(ttl=600, show_spinner="Cargando Base Prospectos…")
def _leer(_conn, _v=0):
    try:
        d = _conn.read(worksheet=HOJA, ttl=0)
    except Exception:
        return pd.DataFrame(columns=COLS)
    if d is None or d.empty:
        return pd.DataFrame(columns=COLS)
    d.columns = d.columns.astype(str).str.strip()
    for c in COLS:
        if c not in d.columns:
            d[c] = ""
    d = d[COLS].dropna(how="all").fillna("").astype(str)
    d["Telefono"] = d["Telefono"].str.replace(r"\.0$", "", regex=True).str.lstrip("'").str.strip()
    d["Eventos"] = pd.to_numeric(d["Eventos"], errors="coerce").fillna(1).astype(int)
    return d


def cargar_base(conn):
    return _leer(conn, st.session_state.get("_pros_v", 0))


def guardar_base(conn, base):
    data = base[COLS].copy()
    data["Telefono"] = data["Telefono"].astype(str).apply(lambda x: f" {x}" if x.startswith("+") else x)  # que Sheets no lo tome como fórmula
    data = data.astype(str)
    for intento in range(2):
        try:
            conn.update(worksheet=HOJA, data=data, spreadsheet=_url())
            break
        except Exception:
            try:
                conn.create(worksheet=HOJA, data=data, spreadsheet=_url())
                break
            except Exception as e:
                err = e
    else:
        st.error(f"🚨 No pude guardar la hoja '{HOJA}': {err}. Si son muchos contactos, cargá el Excel desde Google Sheets "
                 "(Archivo → Importar → Insertar hojas nuevas) y renombrá la pestaña a 'Base Prospectos'.")
        return False
    st.session_state["_pros_v"] = st.session_state.get("_pros_v", 0) + 1
    st.cache_data.clear()
    return True


def a_formato_campana(base):
    """Adapta la Base Prospectos a las columnas que usa el módulo de campañas."""
    b = base.copy()
    b["Estado_Nego"] = b["Estado"].replace("", "Prospecto")
    b["Estado /Prov."] = b["Provincia"]
    primer = b["Nombre"].str.split().str[0].fillna("")
    b["_saludo"] = primer.where((b["Apellido"] != "") & (primer != ""), b["Cliente"].str.split().str[0].fillna(""))
    return b


# ---------------------------------------------------------------- importador
def _leer_subido(f):
    nombre = f.name
    if nombre.lower().endswith(".csv"):
        raw = f.getvalue()
        for enc in ("utf-8-sig", "utf-16", "latin-1"):
            try:
                txt = raw.decode(enc)
                sep = max([",", ";", "\t"], key=txt[:4000].count)
                return [("csv", pd.read_csv(io.StringIO(txt), header=None, dtype=str, sep=sep, on_bad_lines="skip", engine="python"))]
            except Exception:
                continue
        return []
    try:
        return list(pd.read_excel(f, sheet_name=None, header=None, dtype=str).items())
    except Exception:
        return []


def extraer(files):
    """Lee Excel/CSV con columnas en cualquier orden y devuelve filas en formato Base Prospectos."""
    recs, avisos = [], []
    hoy = datetime.date.today().strftime("%Y-%m-%d")
    for f in files:
        hojas = _leer_subido(f)
        if not hojas:
            avisos.append(f"No pude leer {f.name}"); continue
        for _, df in hojas:
            df = df.dropna(how="all").reset_index(drop=True)
            if df.empty:
                continue
            # ¿ya viene en formato Base Prospectos?
            cab = [str(x).strip() for x in df.iloc[0]]
            if {"Email", "Cliente", "Eventos", "Origen"} <= set(cab):
                d = df.iloc[1:].copy(); d.columns = cab
                d = d.fillna("").astype(str)
                for c in COLS:
                    if c not in d.columns: d[c] = ""
                recs.extend(d[COLS].to_dict("records")); continue
            hi = find_header(df)
            colmap = {}
            if hi is not None:
                for j, h in enumerate(df.iloc[hi]):
                    fld = classify(h) if pd.notna(h) else None
                    if fld and fld not in colmap.values():
                        colmap[j] = fld
                data = df.iloc[hi + 1:]
            else:
                data = df
            if "email" not in colmap.values():
                best, bj = 0, None
                for j in range(df.shape[1]):
                    c = data.iloc[:, j].astype(str).str.contains(EMAIL, na=False).mean()
                    if c > best: best, bj = c, j
                if bj is not None and best > 0.3: colmap[bj] = "email"
            if not colmap:
                avisos.append(f"{f.name}: no reconocí columnas"); continue
            for _, row in data.iterrows():
                r = {k: "" for k in FIELDS}
                for j, fld in colmap.items():
                    v = row.iloc[j]
                    if pd.notna(v): r[fld] = str(v)
                m = EMAIL.search(r["email"]) or next((EMAIL.search(v) for v in row.dropna().astype(str) if EMAIL.search(v)), None)
                email = m.group(0).lower().strip(".") if m else ""
                if email:
                    u, _, dom = email.partition("@"); email = f"{u}@{TYPOS.get(dom, dom)}"
                tel = clean_phone(r["telefono"])
                if not email and not tel:
                    continue
                nom, ape = nice(r["nombre"]), nice(r["apellido"])
                if not (nom or ape): nom = nice(r["fullname"])
                if nom and ape and norm(ape) in norm(nom): ape = ""
                recs.append(dict(ID="", Cliente=(nom + " " + ape).strip(), Nombre=nom, Apellido=ape, Profesion=nice(r["profesion"]),
                                 Empresa=nice(r["empresa"]), Cargo=nice(r["cargo"]), Pais=pais_norm(r["pais"]), Provincia=nice(r["provincia"]),
                                 Ciudad=nice(r["ciudad"]), Telefono=tel, Email=email, Asesor="", Estado="Prospecto", Eventos=1,
                                 Origen=f.name.rsplit(".", 1)[0][:60], Primer_registro=hoy, Ultimo_registro=hoy, Fecha_Alta="",
                                 Eventos_detalle=limpiar_evento(f.name)))
    return pd.DataFrame(recs, columns=COLS), avisos


def unir(base, nuevos, asesor):
    """Agrega 'nuevos' a 'base' sin duplicar (por email; si no hay email, por teléfono)."""
    def clave(d):
        tel = d["Telefono"].astype(str).str.replace(r"\D", "", regex=True).str[-8:]
        return d["Email"].astype(str).str.lower().str.strip().where(d["Email"].astype(str).str.strip() != "", "tel:" + tel)
    base = base.copy(); nuevos = nuevos.copy()
    base["_k"] = clave(base) if not base.empty else pd.Series(dtype=str)
    nuevos["_k"] = clave(nuevos)
    nuevos = nuevos.drop_duplicates("_k")
    existentes = nuevos["_k"].isin(set(base["_k"]))
    # los que ya existen: sumar evento y completar datos vacíos
    if existentes.any():
        idx = base.set_index("_k")
        for _, r in nuevos[existentes].iterrows():
            k = r["_k"]
            fila = idx.loc[k] if not isinstance(idx.loc[k], pd.DataFrame) else idx.loc[k].iloc[0]
            for c in ["Cliente", "Nombre", "Apellido", "Profesion", "Empresa", "Cargo", "Pais", "Provincia", "Ciudad", "Telefono"]:
                if not str(fila[c]).strip() and str(r[c]).strip():
                    idx.loc[k, c] = r[c]
            if r["Origen"] and r["Origen"] not in str(fila["Origen"]):
                idx.loc[k, "Eventos"] = int(fila["Eventos"] or 1) + 1
                idx.loc[k, "Origen"] = (r["Origen"] + " | " + str(fila["Origen"]))[:300]
                idx.loc[k, "Ultimo_registro"] = max(str(fila["Ultimo_registro"]), str(r["Ultimo_registro"]))
                det = str(fila.get("Eventos_detalle", "") or "")
                if r["Eventos_detalle"] and r["Eventos_detalle"] not in det:
                    idx.loc[k, "Eventos_detalle"] = (r["Eventos_detalle"] + " | " + det).strip(" |")
        base = idx.reset_index()
    altas = nuevos[~existentes].copy()
    if not altas.empty:
        ult = pd.to_numeric(base["ID"].astype(str).str.extract(r"(\d+)")[0], errors="coerce").max() if not base.empty else 0
        ult = 0 if pd.isna(ult) else int(ult)
        altas["ID"] = [x if str(x).startswith("PR-") else f"PR-{ult + i:05d}" for i, x in enumerate(altas["ID"], start=1)]
        altas["Asesor"] = altas["Asesor"].replace("", asesor)
        altas["Fecha_Alta"] = altas["Fecha_Alta"].replace("", datetime.date.today().strftime("%d/%m/%Y"))
    res = pd.concat([base, altas], ignore_index=True).drop(columns="_k", errors="ignore")
    return res[COLS], len(altas), int(existentes.sum())


# ---------------------------------------------------------------- pantalla
def render_base_prospectos(conn, df_crm, usuario_actual, guardar_crm=None, nuevo_numero_nego=None):
    base = cargar_base(conn)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prospectos", f"{len(base):,}".replace(",", "."))
    c2.metric("Con email", f"{(base['Email'] != '').sum():,}".replace(",", "."))
    c3.metric("Con teléfono", f"{(base['Telefono'] != '').sum():,}".replace(",", "."))
    c4.metric("Ya pasados al CRM", int((base["Estado"] == "En CRM").sum()))

    t_imp, t_bus = st.tabs(["📥 Importar Excel / CSV", "🔎 Buscar y pasar al CRM"])

    with t_imp:
        st.info("Subí uno o varios Excel/CSV **con las columnas en cualquier orden** (registros de webinars, listas, exportaciones). "
                "El sistema reconoce nombre, apellido, email, teléfono, empresa, cargo, profesión, país y ciudad, "
                "y **no duplica** a quien ya esté en la base: le suma un evento y completa los datos que falten.")
        subidos = st.file_uploader("Archivos", type=["xlsx", "xls", "csv"], accept_multiple_files=True, key="pros_up")
        if subidos and st.button("🔍 Analizar archivos", key="pros_an"):
            nuevos, avisos = extraer(subidos)
            st.session_state["_pros_nuevos"] = nuevos
            for a in avisos: st.warning(a)
        nuevos = st.session_state.get("_pros_nuevos")
        reemplazar = st.checkbox("Reemplazar TODA la Base Prospectos con este archivo (solo para recargar la base completa)",
                                 value=False, key="pros_reemplazar")
        if nuevos is not None and not nuevos.empty:
            enc_crm = set(df_crm["Email"].astype(str).str.lower().str.strip()) - {""}
            ya_crm = nuevos["Email"].str.lower().isin(enc_crm).sum()
            base_ref = base[base["Estado"] == "En CRM"] if reemplazar else base
            res, altas, act = unir(base_ref, nuevos, usuario_actual)
            if reemplazar:
                st.warning("Modo reemplazo: la base actual se descarta y queda la del archivo (se conservan las marcas 'En CRM').")
            st.success(f"Encontré **{len(nuevos):,}** filas con contacto → **{altas:,} nuevos** y **{act:,} que ya estaban** "
                       f"(se actualizan). {ya_crm} ya son contactos del CRM principal.".replace(",", "."))
            st.dataframe(nuevos.head(50)[["Cliente", "Email", "Telefono", "Empresa", "Pais", "Origen"]], hide_index=True, use_container_width=True)
            if st.button(f"✅ Guardar en Base Prospectos", type="primary", key="pros_save"):
                with st.spinner("Guardando en Google Sheets…"):
                    if guardar_base(conn, res):
                        st.session_state.pop("_pros_nuevos", None)
                        st.success("Base Prospectos actualizada."); st.rerun()

    with t_bus:
        q = st.text_input("Buscar por nombre, email o empresa", key="pros_q")
        if q:
            m = (base["Cliente"].str.contains(q, case=False, na=False) | base["Email"].str.contains(q, case=False, na=False)
                 | base["Empresa"].str.contains(q, case=False, na=False))
            res = base[m].head(30)
            if res.empty:
                st.info("Sin resultados.")
            for i, r in res.iterrows():
                with st.expander(f"{r['Cliente'] or r['Email']} · {r['Empresa']} · {r['Pais']} · {r['Eventos']} eventos · {r['Estado']}"):
                    st.write(f"📧 {r['Email']}  |  📞 {r['Telefono']}  |  💼 {r['Cargo']} {r['Profesion']}  |  📍 {r['Ciudad']} {r['Provincia']}")
                    st.caption(f"Origen: {r['Origen']}  ·  Primer registro {r['Primer_registro']} · Último {r['Ultimo_registro']}")
                    if r["Estado"] == "En CRM":
                        st.success("Ya está en el CRM principal.")
                    elif guardar_crm and nuevo_numero_nego and st.button("➕ Pasar al CRM como Potencial", key=f"pros_pasar_{i}"):
                        if r["Email"] and (df_crm["Email"].astype(str).str.lower().str.strip() == r["Email"].lower()).any():
                            st.warning("Ese email ya existe en el CRM principal.")
                        else:
                            hoy = datetime.datetime.now()
                            nueva = pd.DataFrame([{"N° Nego": nuevo_numero_nego(df_crm), "Creado": hoy.strftime("%d/%m/%Y"), "Cliente": r["Cliente"] or r["Email"],
                                                   "Profesion": r["Profesion"], "Direccion": "", "Estado /Prov.": r["Provincia"], "Pais": r["Pais"],
                                                   "Ciudad": r["Ciudad"], "Empresa": r["Empresa"], "Cargo": r["Cargo"], "Telefono": r["Telefono"],
                                                   "Email": r["Email"], "N° Cotiz.": "", "Monto USD / $": "",
                                                   "Notas": f"[{hoy.strftime('%d/%m/%Y')}] 📥 Desde Base Prospectos ({r['Eventos']} eventos). Origen: {r['Origen'][:120]}",
                                                   "Proxima llamada": "", "Asesor": usuario_actual, "Estado_Nego": "Potencial", "Link_PDF": "",
                                                   "Productos Seleccionados": "", "Descuento Aplicado": ""}])
                            guardar_crm(pd.concat([df_crm, nueva], ignore_index=True))
                            b2 = base.copy(); b2.loc[i, "Estado"] = "En CRM"
                            guardar_base(conn, b2)
                            st.success("Agregado al CRM como Potencial."); st.rerun()
