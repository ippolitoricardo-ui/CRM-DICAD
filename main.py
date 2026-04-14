import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date
import pandas as pd
from streamlit_option_menu import option_menu
import json
import io
import openpyxl
from openpyxl.styles import PatternFill, Border, Side, Alignment

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CRM DICAD AMÉRICA", layout="wide")

# Colores para el intercalado (Gris muy clarito y Blanco)
FILL_GRIS = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
FILL_BLANCO = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

def procesar_excel(row, obs, tipo_doc):
    """
    Motor de Excel basado en coordenadas exactas del usuario.
    """
    try:
        # 1. Cargar la plantilla (Asegurate de que se llame así y esté en la carpeta)
        archivo_plantilla = "plantilla_presupuesto.xlsx"
        wb = openpyxl.load_workbook(archivo_plantilla)
        ws = wb.active
    except Exception as e:
        return None, f"🚨 No se encontró '{archivo_plantilla}'. Subilo a la carpeta del proyecto."

    # 2. Extraer datos de productos
    try:
        prods_data = json.loads(row['Productos Seleccionados'])
    except:
        prods_data = [{
            "nombre": str(row.get('Productos Seleccionados', 'Cotización')),
            "desc": "Cotización Manual",
            "cantidad": "1 pcs.",
            "precio": row['Monto USD / $'],
            "desc_val": "0",
            "importe": row['Monto USD / $']
        }]

    # 3. Inyectar datos en celdas fijas (CABECERA)
    ws['B10'] = row['Cliente']
    ws['B11'] = row['Empresa']
    ws['B12'] = row['Telefono']
    
    ws['A15'] = row['Asesor']
    ws['B15'] = date.today().strftime("%d/%m/%Y")
    ws['C15'] = row['N° Cotiz.']
    ws['D15'] = "USD" if "USD" in str(row['Monto USD / $']).upper() else "ARS"

    # 4. Inyectar PRODUCTOS (Inicia en fila 18)
    fila_inicio = 18
    for i, p in enumerate(prods_data):
        curr_row = fila_inicio + i
        
        # Insertar valores
        ws[f'A{curr_row}'] = p['nombre']
        ws[f'B{curr_row}'] = p['desc']
        ws[f'C{curr_row}'] = p['cantidad']
        ws[f'D{curr_row}'] = p['precio']
        ws[f'E{curr_row}'] = p['desc_val']
        ws[f'F{curr_row}'] = p['importe']

        # Aplicar intercalado de colores (Bandeado)
        relleno = FILL_GRIS if i % 2 == 0 else FILL_BLANCO
        for col in ['A', 'B', 'C', 'D', 'E', 'F']:
            ws[f'{col}{curr_row}'].fill = relleno
            # Mantener alineación vertical arriba para descripciones largas
            ws[f'{col}{curr_row}'].alignment = Alignment(vertical="top", wrap_text=True)

    # 5. Inyectar TOTALES (Celdas fijas F22-F25 según tu mapa)
    # Nota: Si usas fórmulas en el Excel, podrías no necesitar inyectar esto, 
    # pero lo hacemos para asegurar que coincida con el CRM.
    
    # Calculamos montos para los totales
    def limpiar(val):
        try: return float(str(val).replace('USD','').replace('ARS','').replace('$','').replace(',','').strip())
        except: return 0.0

    monto_base = limpiar(row['Monto USD / $'])
    impuesto_pct = 0.21 if "Argentina" in tipo_doc else 0.05
    val_impuestos = monto_base * impuesto_pct
    total_final = monto_base + val_impuestos

    ws['F22'] = monto_base
    ws['F23'] = 0 # Descuento (ya aplicado en el monto base del CRM)
    ws['F24'] = val_impuestos
    ws['F25'] = total_final

    # 6. Observaciones (A31)
    ws['A31'] = f"Observaciones: {obs}"

    # 7. Guardar en memoria para descarga
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue(), "OK"

# --- EL RESTO DEL CÓDIGO DEL CRM (main.py) SIGUE IGUAL ---
# (Asegurate de cambiar la llamada de procesar_word por procesar_excel en el botón)