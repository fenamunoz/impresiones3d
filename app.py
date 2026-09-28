import re
import json
from supabase import create_client, Client
from io import BytesIO
from datetime import date, timedelta

import altair as alt
import pandas as pd
import requests
import streamlit as st


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Impresiones 3D",
    page_icon="🖨️",
    layout="wide"
)

PERSONAS = ["Mauri", "Fabi", "Beto", "Pame", "Feña"]
DESTINOS = PERSONAS + ["Venta"]


CELESTE_UI = "#38BDF8"
CELESTE_UI_CLARO = "#7DD3FC"
CELESTE_UI_HOVER = "#0EA5E9"
AZUL = "#3B82F6"
VERDE = "#22C55E"

CATEGORIAS_GASTO = [
    "Filamento / insumos",
    "Mantención",
    "Repuestos",
    "Herramientas",
    "Envíos",
    "Electricidad extra",
    "Otros"
]

TIPOS_REPARTO = [
    "Fondo común",
    "Dividir entre los 5",
    "Personas específicas",
    "Una persona"
]


# =========================================================
# ESTILO
# =========================================================

st.markdown(
    f"""
    <style>

    :root {{
        --primary-color: {CELESTE_UI};
    }}

    /* =====================================================
       BOTONES PRINCIPALES — CELESTE
       ===================================================== */

    button[data-testid="stBaseButton-primary"] {{
        background-color: {CELESTE_UI} !important;
        border-color: {CELESTE_UI} !important;
        color: #0F172A !important;
        box-shadow: none !important;
    }}

    button[data-testid="stBaseButton-primary"]:hover {{
        background-color: {CELESTE_UI_CLARO} !important;
        border-color: {CELESTE_UI_CLARO} !important;
        color: #0F172A !important;
    }}

    button[data-testid="stBaseButton-primary"]:focus,
    button[data-testid="stBaseButton-primary"]:focus-visible {{
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.35) !important;
        border-color: {CELESTE_UI} !important;
    }}

    /* =====================================================
       PESTAÑAS — CELESTE, SIN ROJO/FUCSIA
       ===================================================== */

    [data-testid="stTabs"] [role="tab"],
    [data-baseweb="tab"] {{
        border-color: transparent !important;
        outline: none !important;
        box-shadow: none !important;
    }}

    [data-testid="stTabs"] [role="tab"][aria-selected="true"],
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] p,
    [data-baseweb="tab"][aria-selected="true"],
    [data-baseweb="tab"][aria-selected="true"] p {{
        color: {CELESTE_UI_CLARO} !important;
        border-color: transparent !important;
        outline: none !important;
        box-shadow: none !important;
    }}

    [data-testid="stTabs"] [role="tab"]:hover,
    [data-testid="stTabs"] [role="tab"]:hover p,
    [data-baseweb="tab"]:hover,
    [data-baseweb="tab"]:hover p {{
        color: {CELESTE_UI_CLARO} !important;
    }}

    [data-testid="stTabs"] [role="tab"]:focus,
    [data-testid="stTabs"] [role="tab"]:focus-visible,
    [data-baseweb="tab"]:focus,
    [data-baseweb="tab"]:focus-visible {{
        outline: none !important;
        box-shadow: none !important;
        border-color: transparent !important;
    }}

    /* Indicador activo: cubrimos las variantes de Streamlit/BaseWeb */
    [data-testid="stTabs"] [data-baseweb="tab-highlight"],
    [data-baseweb="tab-highlight"],
    div[data-baseweb="tab-list"] > div:last-child {{
        background-color: {CELESTE_UI} !important;
        border-color: {CELESTE_UI} !important;
    }}

    [data-testid="stTabs"] [role="tab"][aria-selected="true"],
    div[data-baseweb="tab-list"] button[aria-selected="true"] {{
        border-bottom-color: {CELESTE_UI} !important;
    }}

    /* Línea base neutra de las pestañas */
    [data-testid="stTabs"] [data-baseweb="tab-border"],
    [data-baseweb="tab-border"] {{
        background-color: #2B313B !important;
        border-color: #2B313B !important;
    }}

    /* =====================================================
       INPUTS / SELECTS / TEXTAREA — FOCO CELESTE
       ===================================================== */

    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="base-input"]:focus-within,
    div[data-baseweb="select"]:focus-within,
    div[data-baseweb="textarea"]:focus-within,
    textarea:focus,
    input:focus {{
        border-color: {CELESTE_UI} !important;
        box-shadow: 0 0 0 1px {CELESTE_UI} !important;
        outline: none !important;
    }}

    /* =====================================================
       BOTÓN DEL SIDEBAR CERRADO — PÍLDORA CELESTE
       ===================================================== */

    [data-testid="stSidebarCollapsedControl"] {{
        width: 235px !important;
        min-width: 235px !important;
        height: 42px !important;
        padding: 0 12px !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        background: rgba(56, 189, 248, 0.13) !important;
        border: 1px solid rgba(125, 211, 252, 0.55) !important;
        border-radius: 10px !important;
        color: white !important;
        overflow: visible !important;
    }}

    [data-testid="stSidebarCollapsedControl"]::after {{
        content: "Configuración de costos";
        color: white !important;
        font-size: 0.90rem !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        display: inline-block !important;
    }}

    [data-testid="stSidebarCollapsedControl"]:hover {{
        background: rgba(56, 189, 248, 0.23) !important;
        border-color: {CELESTE_UI_CLARO} !important;
    }}

    [data-testid="stSidebarCollapsedControl"] button {{
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        color: white !important;
    }}

    [data-testid="stSidebarCollapsedControl"] button:focus,
    [data-testid="stSidebarCollapsedControl"] button:focus-visible {{
        outline: none !important;
        box-shadow: none !important;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# FORMATO
# =========================================================

def formatear_clp(valor):
    try:
        numero = int(round(float(valor)))
    except Exception:
        numero = 0
    return "$" + f"{numero:,}".replace(",", ".")


def parsear_clp(texto):
    numeros = re.sub(r"[^\d]", "", str(texto or ""))
    return int(numeros) if numeros else 0


def numero_seguro(valor):
    if pd.isna(valor):
        return 0.0
    return float(valor)


def separar_duracion(horas_decimal):
    """Convierte horas decimales a horas y minutos enteros."""
    total_minutos = int(round(numero_seguro(horas_decimal) * 60))
    horas = total_minutos // 60
    minutos = total_minutos % 60
    return horas, minutos


def formatear_duracion(horas_decimal):
    """Ej.: 2.9 -> '2 horas, 54 minutos'."""
    horas, minutos = separar_duracion(horas_decimal)
    texto_horas = f"{horas} hora" if horas == 1 else f"{horas} horas"
    texto_minutos = (
        f"{minutos} minuto" if minutos == 1 else f"{minutos} minutos"
    )
    return f"{texto_horas}, {texto_minutos}"


def formatear_campo_clp(clave):
    """Formatea un text_input monetario al perder foco / presionar Enter."""
    valor = parsear_clp(st.session_state.get(clave, "0"))
    st.session_state[clave] = formatear_clp(valor)


# =========================================================
# COLORES DE FILAMENTO
# =========================================================

PALETA = {
    "NEGRO": (0, 0, 0),
    "BLANCO": (255, 255, 255),
    "GRIS": (128, 128, 128),
    "ROJO": (220, 38, 38),
    "NARANJO": (249, 115, 22),
    "AMARILLO": (250, 204, 21),
    "VERDE": (34, 197, 94),
    "CELESTE": (56, 189, 248),
    "AZUL": (37, 99, 235),
    "MORADO": (126, 34, 206),
    "VIOLETA": (139, 92, 246),
    "ROSADO": (236, 72, 153),
    "CAFÉ": (120, 72, 48),
    "BEIGE": (220, 205, 170)
}


def nombre_color(codigo):
    if not codigo:
        return "SIN COLOR"

    codigo = codigo.strip().upper()

    if not re.match(r"^#[0-9A-F]{6}$", codigo):
        return "SIN COLOR"

    r = int(codigo[1:3], 16)
    g = int(codigo[3:5], 16)
    b = int(codigo[5:7], 16)

    mejor_nombre = "SIN COLOR"
    mejor_distancia = None

    for nombre, rgb in PALETA.items():
        distancia = (
            (r - rgb[0]) ** 2
            + (g - rgb[1]) ** 2
            + (b - rgb[2]) ** 2
        )

        if mejor_distancia is None or distancia < mejor_distancia:
            mejor_distancia = distancia
            mejor_nombre = nombre

    return mejor_nombre


def emoji_color(nombre):
    return {
        "NEGRO": "⬛",
        "BLANCO": "⬜",
        "ROJO": "🟥",
        "NARANJO": "🟧",
        "AMARILLO": "🟨",
        "VERDE": "🟩",
        "AZUL": "🟦",
        "CELESTE": "🟦",
        "MORADO": "🟪",
        "VIOLETA": "🟪",
        "CAFÉ": "🟫",
    }.get(nombre, "◼️")


# =========================================================
# BASE DE DATOS — SUPABASE
# =========================================================

@st.cache_resource
def conectar_db() -> Client:
    """Crea y reutiliza la conexión a Supabase usando Secrets de Streamlit."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception as exc:
        raise RuntimeError(
            "Faltan SUPABASE_URL y/o SUPABASE_KEY en los Secrets de Streamlit."
        ) from exc

    return create_client(url, key)


def _a_float(valor):
    """Convierte valores de pandas/numpy a float nativo para enviarlos a Supabase."""
    if valor is None or pd.isna(valor):
        return 0.0
    return float(valor)


def _a_int(valor):
    """Convierte ids de pandas/numpy a int nativo."""
    return int(valor)


# =========================================================
# CONFIGURACIÓN DE COSTOS
# =========================================================

CONFIG_DEFAULT = {
    "precio_filamento_kg": 20000,
    "precio_impresora": 1000000,
    "vida_util_horas": 5000,
    "consumo_impresora_w": 150,
    "precio_kwh": 250
}


def cargar_configuracion():
    config = CONFIG_DEFAULT.copy()

    respuesta = (
        conectar_db()
        .table("configuracion")
        .select("clave,valor")
        .execute()
    )

    for fila in (respuesta.data or []):
        config[fila["clave"]] = fila["valor"]

    return config


def guardar_configuracion(config):
    filas = [
        {"clave": clave, "valor": float(valor)}
        for clave, valor in config.items()
    ]

    (
        conectar_db()
        .table("configuracion")
        .upsert(filas, on_conflict="clave")
        .execute()
    )


config_guardada = cargar_configuracion()


# =========================================================
# MAKERWORLD
# =========================================================

def obtener_datos_makerworld(url):
    model_match = re.search(r"/models/(\d+)", url)

    if not model_match:
        raise ValueError("No pude encontrar el ID del modelo.")

    model_id = model_match.group(1)

    instance_match = re.search(r"profileId-(\d+)", url)
    instance_id = instance_match.group(1) if instance_match else None

    api_url = (
        f"https://api.bambulab.com/"
        f"v1/design-service/design/{model_id}"
    )

    respuesta = requests.get(
        api_url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        },
        timeout=20
    )

    if respuesta.status_code != 200:
        raise ValueError(
            f"MakerWorld respondió con error {respuesta.status_code}"
        )

    data = respuesta.json()
    design = data.get("design", data)

    nombre_modelo = design.get("title", "Modelo sin nombre")
    instances = design.get("instances", [])

    if not instances:
        raise ValueError("MakerWorld no entregó perfiles.")

    instancia = None

    if instance_id:
        for item in instances:
            if str(item.get("id")) == str(instance_id):
                instancia = item
                break

        if instancia is None:
            raise ValueError(
                "Encontré el modelo, pero no el perfil indicado en el link."
            )
    else:
        for item in instances:
            if item.get("isDefault"):
                instancia = item
                break

        if instancia is None:
            instancia = instances[0]

    nombre_perfil = instancia.get("title", "Perfil sin nombre")
    segundos = int(instancia.get("prediction", 0) or 0)
    horas = segundos / 3600
    peso = float(instancia.get("weight", 0) or 0)

    filamentos = []

    for filamento in instancia.get("instanceFilaments", []):
        tipo = filamento.get("type", "Desconocido").upper()
        gramos = float(filamento.get("usedG", 0) or 0)
        codigo = filamento.get("color", "").upper()
        color = nombre_color(codigo)

        filamentos.append({
            "Material": f"{tipo} {color}",
            "Gramos": gramos,
            "Color": color
        })

    if not filamentos and peso > 0:
        filamentos.append({
            "Material": "DESCONOCIDO",
            "Gramos": peso,
            "Color": "SIN COLOR"
        })

    return {
        "modelo": nombre_modelo,
        "perfil": nombre_perfil,
        "horas": horas,
        "peso": peso,
        "filamentos": filamentos
    }


# =========================================================
# CRUD IMPRESIONES
# =========================================================

def guardar_impresion(
    fecha,
    persona,
    link,
    modelo,
    perfil,
    horas,
    gramos,
    materiales,
    costo_material,
    costo_electricidad,
    costo_depreciacion,
    costo_total,
    precio_venta,
    ganancia
):
    fila = {
        "fecha": fecha,
        "persona": persona,
        "link": link,
        "modelo": modelo,
        "perfil": perfil,
        "horas": _a_float(horas),
        "gramos": _a_float(gramos),
        "materiales": materiales,
        "costo_material": _a_float(costo_material),
        "costo_electricidad": _a_float(costo_electricidad),
        "costo_depreciacion": _a_float(costo_depreciacion),
        "costo_total": _a_float(costo_total),
        "precio_venta": _a_float(precio_venta),
        "ganancia": _a_float(ganancia)
    }

    conectar_db().table("impresiones").insert(fila).execute()


def actualizar_impresion(
    registro_id,
    fecha,
    persona,
    modelo,
    horas,
    gramos,
    costo_total,
    precio_venta,
    ganancia
):
    cambios = {
        "fecha": fecha,
        "persona": persona,
        "modelo": modelo,
        "horas": _a_float(horas),
        "gramos": _a_float(gramos),
        "costo_total": _a_float(costo_total),
        "precio_venta": _a_float(precio_venta),
        "ganancia": _a_float(ganancia)
    }

    (
        conectar_db()
        .table("impresiones")
        .update(cambios)
        .eq("id", _a_int(registro_id))
        .execute()
    )


def eliminar_impresion(registro_id):
    (
        conectar_db()
        .table("impresiones")
        .delete()
        .eq("id", _a_int(registro_id))
        .execute()
    )


# =========================================================
# CRUD PAGOS
# =========================================================

def guardar_pago(fecha, persona, monto, nota):
    fila = {
        "fecha": fecha,
        "persona": persona,
        "monto": _a_float(monto),
        "nota": nota
    }
    conectar_db().table("pagos").insert(fila).execute()


def actualizar_pago(registro_id, fecha, persona, monto, nota):
    cambios = {
        "fecha": fecha,
        "persona": persona,
        "monto": _a_float(monto),
        "nota": nota
    }
    (
        conectar_db()
        .table("pagos")
        .update(cambios)
        .eq("id", _a_int(registro_id))
        .execute()
    )


def eliminar_pago(registro_id):
    (
        conectar_db()
        .table("pagos")
        .delete()
        .eq("id", _a_int(registro_id))
        .execute()
    )


# =========================================================
# CRUD GASTOS
# =========================================================

def guardar_gasto(
    fecha,
    concepto,
    categoria,
    monto,
    pagado_por,
    tipo_reparto,
    personas,
    nota
):
    fila = {
        "fecha": fecha,
        "concepto": concepto,
        "categoria": categoria,
        "monto": _a_float(monto),
        "pagado_por": pagado_por,
        "tipo_reparto": tipo_reparto,
        "personas": json.dumps(personas, ensure_ascii=False),
        "nota": nota
    }
    conectar_db().table("gastos").insert(fila).execute()


def actualizar_gasto(
    registro_id,
    fecha,
    concepto,
    categoria,
    monto,
    pagado_por,
    tipo_reparto,
    personas,
    nota
):
    cambios = {
        "fecha": fecha,
        "concepto": concepto,
        "categoria": categoria,
        "monto": _a_float(monto),
        "pagado_por": pagado_por,
        "tipo_reparto": tipo_reparto,
        "personas": json.dumps(personas, ensure_ascii=False),
        "nota": nota
    }
    (
        conectar_db()
        .table("gastos")
        .update(cambios)
        .eq("id", _a_int(registro_id))
        .execute()
    )


def eliminar_gasto(registro_id):
    (
        conectar_db()
        .table("gastos")
        .delete()
        .eq("id", _a_int(registro_id))
        .execute()
    )


# =========================================================
# CARGAR DATOS
# =========================================================

def _dataframe_supabase(tabla, columnas):
    respuesta = (
        conectar_db()
        .table(tabla)
        .select("*")
        .order("fecha", desc=True)
        .order("id", desc=True)
        .execute()
    )

    datos = respuesta.data or []
    df = pd.DataFrame(datos, columns=columnas)

    if not df.empty and "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"])

    return df


def cargar_impresiones():
    return _dataframe_supabase(
        "impresiones",
        [
            "id", "fecha", "persona", "link", "modelo", "perfil",
            "horas", "gramos", "materiales", "costo_material",
            "costo_electricidad", "costo_depreciacion", "costo_total",
            "precio_venta", "ganancia"
        ]
    )


def cargar_pagos():
    return _dataframe_supabase(
        "pagos",
        ["id", "fecha", "persona", "monto", "nota"]
    )


def cargar_gastos():
    return _dataframe_supabase(
        "gastos",
        [
            "id", "fecha", "concepto", "categoria", "monto",
            "pagado_por", "tipo_reparto", "personas", "nota"
        ]
    )


# =========================================================
# LÓGICA DE GASTOS
# =========================================================

def personas_reparto_gasto(fila):
    tipo = fila["tipo_reparto"]

    if tipo == "Fondo común":
        return []

    if tipo == "Dividir entre los 5":
        return PERSONAS.copy()

    try:
        personas = json.loads(fila["personas"] or "[]")
    except Exception:
        personas = []

    return [p for p in personas if p in PERSONAS]


def efectos_gastos_por_persona(gastos_df):
    """
    Devuelve para cada persona:
    - cargo: parte de gastos que le corresponde asumir.
    - adelanto: gasto pagado directamente por esa persona.
    """
    efectos = {
        persona: {
            "cargo": 0.0,
            "adelanto": 0.0
        }
        for persona in PERSONAS
    }

    if gastos_df.empty:
        return efectos

    for _, fila in gastos_df.iterrows():
        monto = numero_seguro(fila["monto"])
        pagado_por = fila["pagado_por"]
        participantes = personas_reparto_gasto(fila)

        if participantes:
            parte = monto / len(participantes)

            for persona in participantes:
                efectos[persona]["cargo"] += parte

        if pagado_por in PERSONAS:
            efectos[pagado_por]["adelanto"] += monto

    return efectos


def calcular_saldo_caja(impresiones_df=None, pagos_df=None, gastos_df=None):
    if impresiones_df is None:
        impresiones_df = cargar_impresiones()
    if pagos_df is None:
        pagos_df = cargar_pagos()
    if gastos_df is None:
        gastos_df = cargar_gastos()

    pagos_totales = (
        pagos_df["monto"].sum()
        if not pagos_df.empty
        else 0
    )

    ventas_totales = (
        impresiones_df[
            impresiones_df["persona"] == "Venta"
        ]["precio_venta"].sum()
        if not impresiones_df.empty
        else 0
    )

    egresos_caja = (
        gastos_df[
            gastos_df["pagado_por"] == "Caja común"
        ]["monto"].sum()
        if not gastos_df.empty
        else 0
    )

    return float(pagos_totales + ventas_totales - egresos_caja)


def crear_excel_historial(impresiones_df, pagos_df, gastos_df):
    salida = BytesIO()

    try:
        with pd.ExcelWriter(salida, engine="xlsxwriter") as writer:
            hojas = {
                "Impresiones": impresiones_df.copy(),
                "Pagos": pagos_df.copy(),
                "Gastos": gastos_df.copy()
            }

            for nombre, df in hojas.items():
                if not df.empty and "fecha" in df.columns:
                    df["fecha"] = df["fecha"].dt.strftime("%d/%m/%Y")

                if nombre == "Impresiones" and not df.empty and "horas" in df.columns:
                    df["Duración"] = df["horas"].apply(formatear_duracion)
                    df = df.drop(columns=["horas"])

                df.to_excel(
                    writer,
                    sheet_name=nombre,
                    index=False
                )

                worksheet = writer.sheets[nombre]
                worksheet.freeze_panes(1, 0)
                worksheet.autofilter(
                    0, 0, max(len(df), 1), max(len(df.columns) - 1, 0)
                )

                for i, columna in enumerate(df.columns):
                    largo = max(
                        len(str(columna)) + 2,
                        min(35, max(
                            [len(str(v)) for v in df[columna].head(200)] + [0]
                        ) + 2)
                    )
                    worksheet.set_column(i, i, largo)

        salida.seek(0)
        return salida.getvalue(), None

    except ModuleNotFoundError:
        return None, (
            "Para descargar Excel instala XlsxWriter una sola vez con: "
            "python -m pip install XlsxWriter"
        )


# =========================================================
# CALLBACKS
# =========================================================

def seleccionar_destino(nombre):
    st.session_state["destino"] = nombre


def alternar_persona_pago(nombre):
    seleccionadas = st.session_state.get("personas_pago", [])
    seleccionadas = list(seleccionadas)

    if nombre in seleccionadas:
        seleccionadas.remove(nombre)
    else:
        seleccionadas.append(nombre)

    st.session_state["personas_pago"] = seleccionadas


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.header("⚙️ Configuración de costos")
    st.caption("Los montos quedan guardados.")

    texto_filamento = st.text_input(
        "Filamento ($/kg)",
        value=formatear_clp(
            config_guardada["precio_filamento_kg"]
        ),
        key="cfg_filamento"
    )
    precio_filamento_kg = parsear_clp(texto_filamento)

    texto_impresora = st.text_input(
        "Valor impresora",
        value=formatear_clp(
            config_guardada["precio_impresora"]
        ),
        key="cfg_impresora"
    )
    precio_impresora = parsear_clp(texto_impresora)

    vida_util_horas = st.number_input(
        "Vida útil impresora (h)",
        min_value=1,
        value=int(config_guardada["vida_util_horas"]),
        step=500
    )

    consumo_impresora_w = st.number_input(
        "Consumo promedio (W)",
        min_value=0,
        value=int(config_guardada["consumo_impresora_w"]),
        step=10
    )

    texto_kwh = st.text_input(
        "Electricidad ($/kWh)",
        value=formatear_clp(
            config_guardada["precio_kwh"]
        ),
        key="cfg_kwh"
    )
    precio_kwh = parsear_clp(texto_kwh)

    if st.button(
        "💾 Guardar configuración",
        type="primary",
        use_container_width=True
    ):
        guardar_configuracion({
            "precio_filamento_kg": precio_filamento_kg,
            "precio_impresora": precio_impresora,
            "vida_util_horas": vida_util_horas,
            "consumo_impresora_w": consumo_impresora_w,
            "precio_kwh": precio_kwh
        })

        st.success("Configuración guardada ✅")


# =========================================================
# MENSAJES
# =========================================================

if "mensaje" in st.session_state:
    st.success(st.session_state["mensaje"])
    del st.session_state["mensaje"]


# =========================================================
# ENCABEZADO
# =========================================================

st.title("🖨️ Impresiones 3D")
st.caption("Control de impresiones, costos, caja y pagos")


# =========================================================
# PESTAÑAS
# =========================================================

tab_nueva, tab_historial, tab_pago, tab_fondo, tab_resumen = st.tabs(
    [
        "➕ Nueva impresión",
        "📋 Historial",
        "💳 Registrar pago",
        "💰 Fondo común",
        "📊 Resumen"
    ]
)


# =========================================================
# NUEVA IMPRESIÓN
# =========================================================

with tab_nueva:
    st.subheader("Nueva impresión")

    link = st.text_input(
        "Link del modelo",
        placeholder="Pega aquí el link de MakerWorld..."
    )

    st.write("**¿Para quién es?**")

    if "destino" not in st.session_state:
        st.session_state["destino"] = None

    columnas_personas = st.columns(6)
    precio_venta = 0

    for columna, nombre in zip(columnas_personas, DESTINOS):
        with columna:
            seleccionado = st.session_state["destino"] == nombre

            st.button(
                nombre,
                type="primary" if seleccionado else "secondary",
                use_container_width=True,
                key=f"persona_{nombre}",
                on_click=seleccionar_destino,
                args=(nombre,)
            )

            if (
                nombre == "Venta"
                and st.session_state["destino"] == "Venta"
            ):
                precio_venta = st.number_input(
                    "Precio de venta",
                    min_value=0,
                    value=0,
                    step=1000,
                    label_visibility="collapsed",
                    key="precio_venta_inline"
                )

    destino = st.session_state["destino"]

    if st.button("Calcular", type="primary"):
        if not link:
            st.error("Primero pega un link de MakerWorld.")

        elif destino is None:
            st.error("Selecciona para quién es la impresión.")

        else:
            try:
                with st.spinner("Leyendo MakerWorld..."):
                    resultado = obtener_datos_makerworld(link)

                st.session_state["resultado"] = resultado
                st.session_state["link_calculado"] = link
                st.session_state["destino_calculado"] = destino
                st.session_state[
                    "precio_venta_calculado"
                ] = precio_venta

            except Exception as error:
                st.error(
                    f"No pude leer el modelo: {error}"
                )

    if "resultado" in st.session_state:
        resultado = st.session_state["resultado"]
        destino_actual = st.session_state["destino_calculado"]
        precio_venta_actual = st.session_state[
            "precio_venta_calculado"
        ]

        st.divider()

        st.subheader(resultado["modelo"])
        st.caption(f"Perfil: {resultado['perfil']}")

        st.write("## Datos de impresión")

        horas_iniciales, minutos_iniciales = separar_duracion(
            resultado["horas"]
        )

        tiempo_horas_col, tiempo_minutos_col = st.columns(2)

        with tiempo_horas_col:
            horas_editadas = st.number_input(
                "⏱️ Horas",
                min_value=0,
                value=horas_iniciales,
                step=1,
                key="nueva_imp_horas"
            )

        with tiempo_minutos_col:
            minutos_editados = st.number_input(
                "Minutos",
                min_value=0,
                max_value=59,
                value=minutos_iniciales,
                step=1,
                key="nueva_imp_minutos"
            )

        tiempo_editado = horas_editadas + minutos_editados / 60

        st.write("🧵 **Materiales utilizados**")

        materiales_base = pd.DataFrame(resultado["filamentos"])

        if not materiales_base.empty:
            columnas_materiales = st.columns(
                min(len(materiales_base), 4)
            )

            for i, fila in materiales_base.iterrows():
                color_nombre = fila.get("Color", "SIN COLOR")

                with columnas_materiales[
                    i % len(columnas_materiales)
                ]:
                    st.markdown(
                        f"**{emoji_color(color_nombre)} "
                        f"{fila['Material']} — "
                        f"{fila['Gramos']:.0f} g**"
                    )

        df_materiales = materiales_base[
            ["Material", "Gramos"]
        ].copy()

        materiales_editados = st.data_editor(
            df_materiales,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Material": st.column_config.TextColumn(
                    "Material"
                ),
                "Gramos": st.column_config.NumberColumn(
                    "Gramos",
                    min_value=0.0,
                    step=1.0,
                    format="%.0f g"
                )
            }
        )

        peso_total = (
            materiales_editados["Gramos"]
            .fillna(0)
            .sum()
        )

        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                "⚖️ Peso total",
                f"{peso_total:.0f} g"
            )

        with c2:
            st.metric(
                "⏱️ Tiempo",
                formatear_duracion(tiempo_editado)
            )

        costo_material = (
            peso_total / 1000 * precio_filamento_kg
        )

        costo_electricidad = (
            tiempo_editado
            * consumo_impresora_w
            / 1000
            * precio_kwh
        )

        costo_depreciacion = (
            tiempo_editado
            * precio_impresora
            / vida_util_horas
        )

        costo_total = (
            costo_material
            + costo_electricidad
            + costo_depreciacion
        )

        st.divider()
        st.write("## 💰 Costos de impresión")

        a, b, c, d = st.columns(4)

        with a:
            st.metric(
                "🧵 Material",
                formatear_clp(costo_material)
            )

        with b:
            st.metric(
                "⚡ Electricidad",
                formatear_clp(costo_electricidad)
            )

        with c:
            st.metric(
                "🖨️ Depreciación",
                formatear_clp(costo_depreciacion)
            )

        with d:
            st.metric(
                "💰 Costo total",
                formatear_clp(costo_total)
            )

        ganancia = 0

        if destino_actual == "Venta":
            ganancia = precio_venta_actual - costo_total

            st.metric(
                "📈 Ganancia estimada",
                formatear_clp(ganancia)
            )

        st.divider()

        fecha_impresion = st.date_input(
            "Fecha",
            value=date.today(),
            format="DD/MM/YYYY"
        )

        if st.button(
            "💾 Guardar impresión",
            type="primary"
        ):
            materiales_json = json.dumps(
                materiales_editados
                .fillna("")
                .to_dict(orient="records"),
                ensure_ascii=False
            )

            guardar_impresion(
                fecha_impresion.isoformat(),
                destino_actual,
                st.session_state["link_calculado"],
                resultado["modelo"],
                resultado["perfil"],
                tiempo_editado,
                peso_total,
                materiales_json,
                costo_material,
                costo_electricidad,
                costo_depreciacion,
                costo_total,
                precio_venta_actual,
                ganancia
            )

            st.session_state["mensaje"] = (
                f"Impresión guardada para "
                f"{destino_actual} ✅"
            )

            del st.session_state["resultado"]
            st.rerun()


# =========================================================
# RESUMEN
# =========================================================

with tab_resumen:
    st.subheader("📊 Resumen")

    impresiones = cargar_impresiones()
    pagos = cargar_pagos()
    gastos = cargar_gastos()

    # -----------------------------------------------------
    # CAJA ACUMULADA
    # -----------------------------------------------------

    pagos_totales = (
        pagos["monto"].sum()
        if not pagos.empty
        else 0
    )

    ventas_df = (
        impresiones[
            impresiones["persona"] == "Venta"
        ]
        if not impresiones.empty
        else pd.DataFrame()
    )

    ingresos_ventas_totales = (
        ventas_df["precio_venta"].sum()
        if not ventas_df.empty
        else 0
    )

    gastos_caja = (
        gastos[
            gastos["pagado_por"] == "Caja común"
        ]["monto"].sum()
        if not gastos.empty
        else 0
    )

    saldo_caja = (
        pagos_totales
        + ingresos_ventas_totales
        - gastos_caja
    )

    efectos_gastos_total = efectos_gastos_por_persona(
        gastos
    )

    # Por cobrar y a favor de socios se calculan con todo el historial
    por_cobrar_total = 0
    a_favor_total = 0

    for persona in PERSONAS:
        consumo_personal = (
            impresiones[
                impresiones["persona"] == persona
            ]["costo_total"].sum()
            if not impresiones.empty
            else 0
        )

        pago_personal = (
            pagos[
                pagos["persona"] == persona
            ]["monto"].sum()
            if not pagos.empty
            else 0
        )

        cargo_gastos = efectos_gastos_total[
            persona
        ]["cargo"]

        adelanto_gastos = efectos_gastos_total[
            persona
        ]["adelanto"]

        saldo_persona = (
            consumo_personal
            + cargo_gastos
            - pago_personal
            - adelanto_gastos
        )

        if saldo_persona > 0:
            por_cobrar_total += saldo_persona
        elif saldo_persona < 0:
            a_favor_total += abs(saldo_persona)

    gastos_totales = (
        gastos["monto"].sum()
        if not gastos.empty
        else 0
    )

    st.write("### 💼 Caja común")

    caja1, caja2, caja3, caja4, caja5 = st.columns(5)

    with caja1:
        st.metric(
            "💰 Saldo en caja",
            formatear_clp(saldo_caja)
        )

    with caja2:
        st.metric(
            "💳 Por cobrar",
            formatear_clp(por_cobrar_total)
        )

    with caja3:
        st.metric(
            "↩️ A favor de socios",
            formatear_clp(a_favor_total)
        )

    with caja4:
        st.metric(
            "🛍️ Ventas acumuladas",
            formatear_clp(ingresos_ventas_totales)
        )

    with caja5:
        st.metric(
            "💸 Gastos acumulados",
            formatear_clp(gastos_totales)
        )

    st.caption(
        "Saldo en caja = pagos recibidos + ventas - gastos "
        "pagados directamente desde la caja común."
    )

    st.divider()

    # -----------------------------------------------------
    # FILTRO DE PERÍODO
    # -----------------------------------------------------

    periodo = st.selectbox(
        "Periodo",
        [
            "Este mes",
            "Mes pasado",
            "Últimos 30 días",
            "Todo",
            "Personalizado"
        ]
    )

    hoy = date.today()
    fecha_inicio = None
    fecha_fin = None

    if periodo == "Este mes":
        fecha_inicio = date(
            hoy.year,
            hoy.month,
            1
        )
        fecha_fin = hoy

    elif periodo == "Mes pasado":
        primer_dia_mes = date(
            hoy.year,
            hoy.month,
            1
        )
        ultimo_dia_anterior = (
            primer_dia_mes
            - timedelta(days=1)
        )
        fecha_inicio = date(
            ultimo_dia_anterior.year,
            ultimo_dia_anterior.month,
            1
        )
        fecha_fin = ultimo_dia_anterior

    elif periodo == "Últimos 30 días":
        fecha_inicio = hoy - timedelta(days=29)
        fecha_fin = hoy

    elif periodo == "Personalizado":
        f1, f2 = st.columns(2)

        with f1:
            fecha_inicio = st.date_input(
                "Desde",
                value=hoy.replace(day=1),
                format="DD/MM/YYYY"
            )

        with f2:
            fecha_fin = st.date_input(
                "Hasta",
                value=hoy,
                format="DD/MM/YYYY"
            )

    impresiones_periodo = impresiones.copy()
    pagos_periodo = pagos.copy()
    gastos_periodo = gastos.copy()

    if (
        fecha_inicio is not None
        and fecha_fin is not None
    ):
        if not impresiones_periodo.empty:
            impresiones_periodo = impresiones_periodo[
                (
                    impresiones_periodo["fecha"].dt.date
                    >= fecha_inicio
                )
                &
                (
                    impresiones_periodo["fecha"].dt.date
                    <= fecha_fin
                )
            ]

        if not pagos_periodo.empty:
            pagos_periodo = pagos_periodo[
                (
                    pagos_periodo["fecha"].dt.date
                    >= fecha_inicio
                )
                &
                (
                    pagos_periodo["fecha"].dt.date
                    <= fecha_fin
                )
            ]

        if not gastos_periodo.empty:
            gastos_periodo = gastos_periodo[
                (
                    gastos_periodo["fecha"].dt.date
                    >= fecha_inicio
                )
                &
                (
                    gastos_periodo["fecha"].dt.date
                    <= fecha_fin
                )
            ]

    efectos_periodo = efectos_gastos_por_persona(
        gastos_periodo
    )

    resumen = []

    for persona in PERSONAS:
        consumido_periodo = (
            impresiones_periodo[
                impresiones_periodo["persona"] == persona
            ]["costo_total"].sum()
            if not impresiones_periodo.empty
            else 0
        )

        pagado_periodo = (
            pagos_periodo[
                pagos_periodo["persona"] == persona
            ]["monto"].sum()
            if not pagos_periodo.empty
            else 0
        )

        cargo_gasto_periodo = efectos_periodo[
            persona
        ]["cargo"]

        adelanto_periodo = efectos_periodo[
            persona
        ]["adelanto"]

        movimiento_periodo = (
            consumido_periodo
            + cargo_gasto_periodo
            - pagado_periodo
            - adelanto_periodo
        )

        consumido_total = (
            impresiones[
                impresiones["persona"] == persona
            ]["costo_total"].sum()
            if not impresiones.empty
            else 0
        )

        pagado_total = (
            pagos[
                pagos["persona"] == persona
            ]["monto"].sum()
            if not pagos.empty
            else 0
        )

        cargo_gasto_total = efectos_gastos_total[
            persona
        ]["cargo"]

        adelanto_total = efectos_gastos_total[
            persona
        ]["adelanto"]

        saldo_acumulado = (
            consumido_total
            + cargo_gasto_total
            - pagado_total
            - adelanto_total
        )

        resumen.append({
            "Persona": persona,
            "Consumido periodo": consumido_periodo,
            "Gastos periodo": cargo_gasto_periodo,
            "Pagado periodo": pagado_periodo,
            "Adelantos periodo": adelanto_periodo,
            "Movimiento periodo": movimiento_periodo,
            "Saldo acumulado": saldo_acumulado
        })

    df_resumen = pd.DataFrame(resumen)

    # -----------------------------------------------------
    # TARJETAS PERSONAS
    # -----------------------------------------------------

    st.write("### 👥 Cuenta de cada uno")
    st.caption(
        "El período muestra impresiones, gastos repartidos, "
        "pagos y adelantos. El saldo total considera todo el historial."
    )

    columnas = st.columns(len(PERSONAS))

    for i, persona in enumerate(PERSONAS):
        fila = df_resumen[
            df_resumen["Persona"] == persona
        ].iloc[0]

        saldo_acumulado = fila["Saldo acumulado"]

        with columnas[i]:
            st.write(f"### {persona}")

            st.metric(
                "Impresiones",
                formatear_clp(
                    fila["Consumido periodo"]
                )
            )

            st.metric(
                "Gastos comunes",
                formatear_clp(
                    fila["Gastos periodo"]
                )
            )

            st.metric(
                "Pagado / adelantado",
                formatear_clp(
                    fila["Pagado periodo"]
                    + fila["Adelantos periodo"]
                )
            )

            if saldo_acumulado > 0:
                st.error(
                    "Saldo total: Debe "
                    + formatear_clp(
                        saldo_acumulado
                    )
                )

            elif saldo_acumulado < 0:
                st.success(
                    "Saldo total: A favor "
                    + formatear_clp(
                        abs(saldo_acumulado)
                    )
                )

            else:
                st.success(
                    "Saldo total: Al día ✅"
                )

    # -----------------------------------------------------
    # GRÁFICO SUPERPUESTO
    # -----------------------------------------------------

    st.write("### 📊 Costo vs pagos del período")
    st.caption(
        "Azul = cargos del período (impresiones + gastos). "
        "Verde = pagos y adelantos."
    )

    base = df_resumen.copy()

    base["Cargo periodo"] = (
        base["Consumido periodo"]
        + base["Gastos periodo"]
    )

    base["Pago efectivo periodo"] = (
        base["Pagado periodo"]
        + base["Adelantos periodo"]
    )

    base["AlturaTexto"] = base[
        ["Cargo periodo", "Pago efectivo periodo"]
    ].max(axis=1)

    def texto_movimiento(fila):
        valor = (
            fila["Cargo periodo"]
            - fila["Pago efectivo periodo"]
        )

        if valor > 0:
            return "Debe " + formatear_clp(valor)

        if valor < 0:
            return "A favor " + formatear_clp(
                abs(valor)
            )

        return "Al día"

    base["Texto"] = base.apply(
        texto_movimiento,
        axis=1
    )

    barras_costo = (
        alt.Chart(base)
        .mark_bar(
            color=AZUL,
            size=68,
            opacity=0.80,
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5
        )
        .encode(
            x=alt.X(
                "Persona:N",
                sort=PERSONAS,
                title=None,
                axis=alt.Axis(
                    labelColor="white",
                    titleColor="white",
                    labelAngle=0
                )
            ),
            y=alt.Y(
                "Cargo periodo:Q",
                title="Monto ($)",
                axis=alt.Axis(
                    labelColor="white",
                    titleColor="white",
                    gridColor="#374151"
                )
            ),
            tooltip=[
                "Persona:N",
                alt.Tooltip(
                    "Cargo periodo:Q",
                    title="Cargos",
                    format=",.0f"
                )
            ]
        )
    )

    barras_pago = (
        alt.Chart(base)
        .mark_bar(
            color=VERDE,
            size=42,
            opacity=0.95,
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5
        )
        .encode(
            x=alt.X(
                "Persona:N",
                sort=PERSONAS
            ),
            y=alt.Y(
                "Pago efectivo periodo:Q"
            ),
            tooltip=[
                "Persona:N",
                alt.Tooltip(
                    "Pago efectivo periodo:Q",
                    title="Pagos + adelantos",
                    format=",.0f"
                )
            ]
        )
    )

    etiquetas = (
        alt.Chart(base)
        .mark_text(
            dy=-10,
            color="white",
            fontSize=13,
            fontWeight="bold"
        )
        .encode(
            x=alt.X(
                "Persona:N",
                sort=PERSONAS
            ),
            y=alt.Y(
                "AlturaTexto:Q"
            ),
            text="Texto:N"
        )
    )

    grafico = (
        barras_costo
        + barras_pago
        + etiquetas
    ).properties(
        height=360
    )

    st.altair_chart(
        grafico,
        use_container_width=True
    )

    # -----------------------------------------------------
    # VENTAS DEL PERÍODO
    # -----------------------------------------------------

    st.write("### 🛍️ Ventas")

    ventas_periodo = (
        impresiones_periodo[
            impresiones_periodo["persona"] == "Venta"
        ]
        if not impresiones_periodo.empty
        else pd.DataFrame()
    )

    total_ventas = (
        ventas_periodo["precio_venta"].sum()
        if not ventas_periodo.empty
        else 0
    )

    costo_ventas = (
        ventas_periodo["costo_total"].sum()
        if not ventas_periodo.empty
        else 0
    )

    ganancia_ventas = (
        ventas_periodo["ganancia"].sum()
        if not ventas_periodo.empty
        else 0
    )

    cantidad_ventas = len(ventas_periodo)

    v1, v2, v3, v4 = st.columns(4)

    with v1:
        st.metric(
            "Ventas",
            cantidad_ventas
        )

    with v2:
        st.metric(
            "Ingresos",
            formatear_clp(total_ventas)
        )

    with v3:
        st.metric(
            "Costo",
            formatear_clp(costo_ventas)
        )

    with v4:
        st.metric(
            "Ganancia",
            formatear_clp(ganancia_ventas)
        )


# =========================================================
# REGISTRAR PAGO
# =========================================================

with tab_pago:
    st.subheader("💳 Registrar pago / aporte")

    st.caption(
        "Puedes registrar a una o varias personas al mismo tiempo. "
        "Si alguien paga más de lo que debe, queda con saldo a favor "
        "y esa plata entra al fondo común."
    )

    if "personas_pago" not in st.session_state:
        st.session_state["personas_pago"] = ["Feña"]

    # Si acabamos de guardar pagos, limpiamos los montos ANTES de crear
    # los widgets. Streamlit no permite modificar el valor de un widget
    # después de que ese widget ya fue instanciado en la misma ejecución.
    if st.session_state.pop("reset_montos_pago", False):
        for persona in PERSONAS:
            st.session_state[f"monto_pago_{persona}"] = "$0"

    st.write("**¿Quiénes pagan o aportan?**")

    botones_pago = st.columns(5)

    for columna, persona in zip(botones_pago, PERSONAS):
        with columna:
            seleccionado = persona in st.session_state["personas_pago"]

            st.button(
                persona,
                type="primary" if seleccionado else "secondary",
                use_container_width=True,
                key=f"pago_persona_{persona}",
                on_click=alternar_persona_pago,
                args=(persona,)
            )

    personas_pago = st.session_state["personas_pago"]

    if personas_pago:
        st.write("**Monto por persona**")
        columnas_montos = st.columns(len(personas_pago))
        montos_pago = {}

        for columna, persona in zip(columnas_montos, personas_pago):
            with columna:
                clave = f"monto_pago_{persona}"

                if clave not in st.session_state:
                    st.session_state[clave] = "$0"

                texto_monto = st.text_input(
                    persona,
                    key=clave,
                    on_change=formatear_campo_clp,
                    args=(clave,),
                    placeholder="$0"
                )

                montos_pago[persona] = parsear_clp(texto_monto)

        fecha_pago = st.date_input(
            "Fecha",
            value=date.today(),
            format="DD/MM/YYYY",
            key="fecha_pago"
        )

        nota_pago = st.text_input(
            "Nota",
            placeholder="Ej: aporte al fondo común / transferencia septiembre"
        )

        if st.button(
            "Registrar pagos / aportes",
            type="primary"
        ):
            montos_validos = {
                persona: monto
                for persona, monto in montos_pago.items()
                if monto > 0
            }

            if not montos_validos:
                st.error("Ingresa al menos un monto mayor a $0.")

            else:
                for persona, monto in montos_validos.items():
                    guardar_pago(
                        fecha_pago.isoformat(),
                        persona,
                        monto,
                        nota_pago
                    )

                total = sum(montos_validos.values())
                nombres = ", ".join(montos_validos.keys())

                st.session_state["mensaje"] = (
                    f"Aportes registrados por {formatear_clp(total)} "
                    f"({nombres}) ✅"
                )

                # La limpieza se hace en la próxima ejecución, antes de
                # volver a crear los campos de monto.
                st.session_state["reset_montos_pago"] = True

                st.rerun()

    else:
        st.info("Selecciona al menos una persona.")


# =========================================================
# FONDO COMÚN
# =========================================================

with tab_fondo:
    st.subheader("💰 Fondo común")

    impresiones_fondo = cargar_impresiones()
    pagos_fondo = cargar_pagos()
    gastos_fondo = cargar_gastos()
    saldo_fondo_actual = calcular_saldo_caja(
        impresiones_fondo, pagos_fondo, gastos_fondo
    )

    st.metric(
        "💰 Saldo disponible en fondo común",
        formatear_clp(saldo_fondo_actual)
    )

    st.caption(
        "Registra compras, mantenciones, repuestos u otros gastos. "
        "Si el fondo común no alcanza, la app no permitirá cargar el gasto "
        "a la caja: tendrás que repartirlo o registrar aportes primero."
    )

    g1, g2 = st.columns(2)

    with g1:
        concepto_gasto = st.text_input(
            "Concepto",
            placeholder="Ej: Mantención impresora"
        )

        categoria_gasto = st.selectbox(
            "Categoría",
            CATEGORIAS_GASTO
        )

    with g2:
        monto_gasto = st.number_input(
            "Monto ($)",
            min_value=0,
            value=0,
            step=1000
        )

        fecha_gasto = st.date_input(
            "Fecha",
            value=date.today(),
            format="DD/MM/YYYY",
            key="fecha_gasto"
        )

    st.write("**¿Quién pagó?**")

    pagado_por = st.radio(
        "Quién pagó",
        ["Caja común"] + PERSONAS,
        horizontal=True,
        label_visibility="collapsed"
    )

    fondo_insuficiente = (
        pagado_por == "Caja común"
        and monto_gasto > saldo_fondo_actual
    )

    if fondo_insuficiente:
        st.warning(
            "⚠️ No hay saldo suficiente en el fondo común para pagar este gasto. "
            "Debes dividirlo entre todos (o entre las personas que corresponda) "
            "y/o registrar aportes al fondo primero."
        )

    tipo_reparto = st.selectbox(
        "¿Cómo se reparte?",
        TIPOS_REPARTO
    )

    personas_gasto = []

    if tipo_reparto == "Dividir entre los 5":
        personas_gasto = PERSONAS.copy()

        st.info(
            "Se dividirá en partes iguales entre "
            "Mauri, Fabi, Beto, Pame y Feña."
        )

    elif tipo_reparto == "Personas específicas":
        personas_gasto = st.multiselect(
            "¿Entre quiénes?",
            PERSONAS
        )

    elif tipo_reparto == "Una persona":
        persona_unica = st.selectbox(
            "¿A quién corresponde?",
            PERSONAS
        )
        personas_gasto = [persona_unica]

    elif tipo_reparto == "Fondo común":
        st.info(
            "Este gasto no genera deuda individual. "
            "Si lo pagó una persona, quedará como un adelanto "
            "a favor de esa persona."
        )

    if personas_gasto and monto_gasto > 0:
        parte = monto_gasto / len(personas_gasto)

        st.caption(
            "Parte por persona: "
            + formatear_clp(parte)
        )

    nota_gasto = st.text_input(
        "Nota",
        placeholder="Opcional"
    )

    if st.button(
        "💾 Guardar gasto",
        type="primary"
    ):
        if not concepto_gasto.strip():
            st.error(
                "Escribe un concepto para el gasto."
            )

        elif monto_gasto <= 0:
            st.error(
                "El monto debe ser mayor a $0."
            )

        elif fondo_insuficiente:
            st.error(
                "No puedes cargar este gasto al fondo común porque no alcanza. "
                "Debes dividirlo entre todos (o entre quienes corresponda) "
                "o registrar aportes antes."
            )

        elif (
            tipo_reparto == "Personas específicas"
            and not personas_gasto
        ):
            st.error(
                "Selecciona al menos una persona."
            )

        else:
            guardar_gasto(
                fecha_gasto.isoformat(),
                concepto_gasto.strip(),
                categoria_gasto,
                monto_gasto,
                pagado_por,
                tipo_reparto,
                personas_gasto,
                nota_gasto
            )

            st.session_state["mensaje"] = (
                f"Gasto '{concepto_gasto}' guardado ✅"
            )

            st.rerun()


# =========================================================
# HISTORIAL
# =========================================================

with tab_historial:
    st.subheader("📋 Historial")

    impresiones = cargar_impresiones()
    pagos = cargar_pagos()
    gastos = cargar_gastos()

    excel_bytes, excel_error = crear_excel_historial(
        impresiones, pagos, gastos
    )

    if excel_bytes is not None:
        st.download_button(
            "⬇️ Descargar historial en Excel",
            data=excel_bytes,
            file_name=f"historial_impresiones3d_{date.today().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    elif excel_error:
        st.info(excel_error)

    hist1, hist2, hist3 = st.tabs(
        [
            "🖨️ Impresiones",
            "💳 Pagos",
            "💸 Gastos"
        ]
    )

    # -----------------------------------------------------
    # HISTORIAL IMPRESIONES
    # -----------------------------------------------------

    with hist1:
        if impresiones.empty:
            st.info(
                "Todavía no hay impresiones guardadas."
            )

        else:
            tabla_impresiones = impresiones[
                [
                    "id",
                    "fecha",
                    "persona",
                    "modelo",
                    "horas",
                    "gramos",
                    "costo_total",
                    "precio_venta",
                    "ganancia"
                ]
            ].copy()

            tabla_impresiones["fecha"] = (
                tabla_impresiones["fecha"]
                .dt.strftime("%d/%m/%Y")
            )

            tabla_impresiones["horas"] = (
                tabla_impresiones["horas"]
                .apply(formatear_duracion)
            )

            tabla_impresiones["costo_total"] = (
                tabla_impresiones["costo_total"]
                .apply(formatear_clp)
            )

            tabla_impresiones["precio_venta"] = (
                tabla_impresiones["precio_venta"]
                .apply(formatear_clp)
            )

            tabla_impresiones["ganancia"] = (
                tabla_impresiones["ganancia"]
                .apply(formatear_clp)
            )

            tabla_impresiones.columns = [
                "ID",
                "Fecha",
                "Persona",
                "Modelo",
                "Duración",
                "Gramos",
                "Costo",
                "Precio venta",
                "Ganancia"
            ]

            st.dataframe(
                tabla_impresiones,
                use_container_width=True,
                hide_index=True
            )

            st.divider()
            st.write("### ✏️ Editar impresión")

            opciones_impresiones = {}

            for _, fila in impresiones.iterrows():
                texto = (
                    f"ID {fila['id']} | "
                    f"{fila['persona']} | "
                    f"{fila['modelo']}"
                )
                opciones_impresiones[
                    texto
                ] = int(fila["id"])

            seleccion_impresion = st.selectbox(
                "Selecciona un registro",
                list(opciones_impresiones.keys()),
                key="editar_impresion_select"
            )

            id_impresion = opciones_impresiones[
                seleccion_impresion
            ]

            registro = impresiones[
                impresiones["id"] == id_impresion
            ].iloc[0]

            e1, e2 = st.columns(2)

            with e1:
                editar_fecha = st.date_input(
                    "Fecha",
                    value=registro["fecha"].date(),
                    format="DD/MM/YYYY",
                    key="editar_imp_fecha"
                )

                editar_persona = st.selectbox(
                    "Persona",
                    DESTINOS,
                    index=DESTINOS.index(
                        registro["persona"]
                    ),
                    key="editar_imp_persona"
                )

                editar_modelo = st.text_input(
                    "Modelo",
                    value=str(registro["modelo"]),
                    key="editar_imp_modelo"
                )

                horas_actuales, minutos_actuales = separar_duracion(
                    registro["horas"]
                )

                editar_tiempo_horas_col, editar_tiempo_minutos_col = st.columns(2)

                with editar_tiempo_horas_col:
                    editar_horas_enteras = st.number_input(
                        "Horas",
                        min_value=0,
                        value=horas_actuales,
                        step=1,
                        key="editar_imp_horas"
                    )

                with editar_tiempo_minutos_col:
                    editar_minutos = st.number_input(
                        "Minutos",
                        min_value=0,
                        max_value=59,
                        value=minutos_actuales,
                        step=1,
                        key="editar_imp_minutos"
                    )

                editar_horas = editar_horas_enteras + editar_minutos / 60

            with e2:
                editar_gramos = st.number_input(
                    "Gramos",
                    min_value=0.0,
                    value=numero_seguro(
                        registro["gramos"]
                    ),
                    step=1.0,
                    key="editar_imp_gramos"
                )

                editar_costo_texto = st.text_input(
                    "Costo total ($)",
                    value=formatear_clp(
                        registro["costo_total"]
                    ),
                    key="editar_imp_costo"
                )
                editar_costo = parsear_clp(
                    editar_costo_texto
                )

                editar_precio_venta_texto = st.text_input(
                    "Precio venta ($)",
                    value=formatear_clp(
                        registro["precio_venta"]
                    ),
                    key="editar_imp_venta"
                )
                editar_precio_venta = parsear_clp(
                    editar_precio_venta_texto
                )

                editar_ganancia = (
                    editar_precio_venta - editar_costo
                    if editar_persona == "Venta"
                    else 0
                )

                st.text_input(
                    "Ganancia ($)",
                    value=formatear_clp(editar_ganancia),
                    disabled=True,
                    key=f"editar_imp_ganancia_mostrada_{id_impresion}"
                )

            guardar_col, eliminar_col = st.columns(2)

            with guardar_col:
                if st.button(
                    "💾 Guardar cambios",
                    type="primary",
                    use_container_width=True
                ):
                    actualizar_impresion(
                        id_impresion,
                        editar_fecha.isoformat(),
                        editar_persona,
                        editar_modelo,
                        editar_horas,
                        editar_gramos,
                        editar_costo,
                        editar_precio_venta,
                        editar_ganancia
                    )

                    st.session_state["mensaje"] = (
                        "Impresión actualizada ✅"
                    )

                    st.rerun()

            with eliminar_col:
                if st.button(
                    "🗑️ Eliminar impresión",
                    use_container_width=True,
                    key=f"pedir_eliminar_imp_{id_impresion}"
                ):
                    st.session_state[
                        "confirmar_eliminar_imp_id"
                    ] = id_impresion

                if (
                    st.session_state.get(
                        "confirmar_eliminar_imp_id"
                    )
                    == id_impresion
                ):
                    st.warning(
                        "¿Seguro que quieres eliminar esta impresión? "
                        "Esta acción no se puede deshacer."
                    )

                    confirmar_col, cancelar_col = st.columns(2)

                    with confirmar_col:
                        if st.button(
                            "Sí, eliminar",
                            type="primary",
                            use_container_width=True,
                            key=f"confirmar_eliminar_imp_{id_impresion}"
                        ):
                            eliminar_impresion(id_impresion)
                            st.session_state.pop(
                                "confirmar_eliminar_imp_id",
                                None
                            )
                            st.session_state["mensaje"] = (
                                "Impresión eliminada 🗑️"
                            )
                            st.rerun()

                    with cancelar_col:
                        if st.button(
                            "Cancelar",
                            use_container_width=True,
                            key=f"cancelar_eliminar_imp_{id_impresion}"
                        ):
                            st.session_state.pop(
                                "confirmar_eliminar_imp_id",
                                None
                            )
                            st.rerun()

    # -----------------------------------------------------
    # HISTORIAL PAGOS
    # -----------------------------------------------------

    with hist2:
        if pagos.empty:
            st.info(
                "Todavía no hay pagos registrados."
            )

        else:
            tabla_pagos = pagos[
                [
                    "id",
                    "fecha",
                    "persona",
                    "monto",
                    "nota"
                ]
            ].copy()

            tabla_pagos["fecha"] = (
                tabla_pagos["fecha"]
                .dt.strftime("%d/%m/%Y")
            )

            tabla_pagos["monto"] = (
                tabla_pagos["monto"]
                .apply(formatear_clp)
            )

            tabla_pagos.columns = [
                "ID",
                "Fecha",
                "Persona",
                "Monto",
                "Nota"
            ]

            st.dataframe(
                tabla_pagos,
                use_container_width=True,
                hide_index=True
            )

            st.divider()
            st.write("### ✏️ Editar pago")

            opciones_pagos = {}

            for _, fila in pagos.iterrows():
                texto = (
                    f"ID {fila['id']} | "
                    f"{fila['persona']} | "
                    f"{formatear_clp(fila['monto'])}"
                )

                opciones_pagos[
                    texto
                ] = int(fila["id"])

            seleccion_pago = st.selectbox(
                "Selecciona un pago",
                list(opciones_pagos.keys()),
                key="editar_pago_select"
            )

            id_pago = opciones_pagos[
                seleccion_pago
            ]

            registro_pago = pagos[
                pagos["id"] == id_pago
            ].iloc[0]

            p1, p2 = st.columns(2)

            with p1:
                editar_fecha_pago = st.date_input(
                    "Fecha",
                    value=registro_pago["fecha"].date(),
                    format="DD/MM/YYYY",
                    key="editar_pago_fecha"
                )

                editar_persona_pago = st.selectbox(
                    "Persona",
                    PERSONAS,
                    index=PERSONAS.index(
                        registro_pago["persona"]
                    ),
                    key="editar_pago_persona"
                )

            with p2:
                editar_monto_pago_texto = st.text_input(
                    "Monto ($)",
                    value=formatear_clp(
                        registro_pago["monto"]
                    ),
                    key="editar_pago_monto"
                )
                editar_monto_pago = parsear_clp(
                    editar_monto_pago_texto
                )

                nota_actual = (
                    ""
                    if pd.isna(registro_pago["nota"])
                    else str(registro_pago["nota"])
                )

                editar_nota_pago = st.text_input(
                    "Nota",
                    value=nota_actual,
                    key="editar_pago_nota"
                )

            pago_guardar_col, pago_eliminar_col = st.columns(2)

            with pago_guardar_col:
                if st.button(
                    "💾 Guardar cambios del pago",
                    type="primary",
                    use_container_width=True
                ):
                    actualizar_pago(
                        id_pago,
                        editar_fecha_pago.isoformat(),
                        editar_persona_pago,
                        editar_monto_pago,
                        editar_nota_pago
                    )

                    st.session_state["mensaje"] = (
                        "Pago actualizado ✅"
                    )

                    st.rerun()

            with pago_eliminar_col:
                confirmar_eliminar_pago = st.checkbox(
                    "Confirmo que quiero eliminarlo",
                    key="confirmar_eliminar_pago"
                )

                if st.button(
                    "🗑️ Eliminar pago",
                    use_container_width=True,
                    disabled=not confirmar_eliminar_pago
                ):
                    eliminar_pago(id_pago)

                    st.session_state["mensaje"] = (
                        "Pago eliminado 🗑️"
                    )

                    st.rerun()

    # -----------------------------------------------------
    # HISTORIAL GASTOS
    # -----------------------------------------------------

    with hist3:
        if gastos.empty:
            st.info(
                "Todavía no hay gastos registrados."
            )

        else:
            tabla_gastos = gastos[
                [
                    "id",
                    "fecha",
                    "concepto",
                    "categoria",
                    "monto",
                    "pagado_por",
                    "tipo_reparto",
                    "nota"
                ]
            ].copy()

            tabla_gastos["fecha"] = (
                tabla_gastos["fecha"]
                .dt.strftime("%d/%m/%Y")
            )

            tabla_gastos["monto"] = (
                tabla_gastos["monto"]
                .apply(formatear_clp)
            )

            tabla_gastos.columns = [
                "ID",
                "Fecha",
                "Concepto",
                "Categoría",
                "Monto",
                "Pagado por",
                "Reparto",
                "Nota"
            ]

            st.dataframe(
                tabla_gastos,
                use_container_width=True,
                hide_index=True
            )

            st.divider()
            st.write("### ✏️ Editar gasto")

            opciones_gastos = {}

            for _, fila in gastos.iterrows():
                texto = (
                    f"ID {fila['id']} | "
                    f"{fila['concepto']} | "
                    f"{formatear_clp(fila['monto'])}"
                )

                opciones_gastos[
                    texto
                ] = int(fila["id"])

            seleccion_gasto = st.selectbox(
                "Selecciona un gasto",
                list(opciones_gastos.keys()),
                key="editar_gasto_select"
            )

            id_gasto = opciones_gastos[
                seleccion_gasto
            ]

            registro_gasto = gastos[
                gastos["id"] == id_gasto
            ].iloc[0]

            try:
                personas_actuales = json.loads(
                    registro_gasto["personas"] or "[]"
                )
            except Exception:
                personas_actuales = []

            eg1, eg2 = st.columns(2)

            with eg1:
                editar_fecha_gasto = st.date_input(
                    "Fecha",
                    value=registro_gasto["fecha"].date(),
                    format="DD/MM/YYYY",
                    key="editar_gasto_fecha"
                )

                editar_concepto_gasto = st.text_input(
                    "Concepto",
                    value=str(
                        registro_gasto["concepto"]
                    ),
                    key="editar_gasto_concepto"
                )

                editar_categoria_gasto = st.selectbox(
                    "Categoría",
                    CATEGORIAS_GASTO,
                    index=(
                        CATEGORIAS_GASTO.index(
                            registro_gasto["categoria"]
                        )
                        if registro_gasto["categoria"]
                        in CATEGORIAS_GASTO
                        else 0
                    ),
                    key="editar_gasto_categoria"
                )

                editar_monto_gasto = st.number_input(
                    "Monto ($)",
                    min_value=0.0,
                    value=numero_seguro(
                        registro_gasto["monto"]
                    ),
                    step=1000.0,
                    key="editar_gasto_monto"
                )

            with eg2:
                opciones_pagador = ["Caja común"] + PERSONAS

                editar_pagado_por = st.selectbox(
                    "Pagado por",
                    opciones_pagador,
                    index=(
                        opciones_pagador.index(
                            registro_gasto["pagado_por"]
                        )
                        if registro_gasto["pagado_por"]
                        in opciones_pagador
                        else 0
                    ),
                    key="editar_gasto_pagador"
                )

                editar_tipo_reparto = st.selectbox(
                    "Reparto",
                    TIPOS_REPARTO,
                    index=(
                        TIPOS_REPARTO.index(
                            registro_gasto["tipo_reparto"]
                        )
                        if registro_gasto["tipo_reparto"]
                        in TIPOS_REPARTO
                        else 0
                    ),
                    key="editar_gasto_reparto"
                )

                if editar_tipo_reparto == "Fondo común":
                    editar_personas_gasto = []

                elif editar_tipo_reparto == "Dividir entre los 5":
                    editar_personas_gasto = PERSONAS.copy()

                elif editar_tipo_reparto == "Personas específicas":
                    editar_personas_gasto = st.multiselect(
                        "Personas",
                        PERSONAS,
                        default=[
                            p for p in personas_actuales
                            if p in PERSONAS
                        ],
                        key="editar_gasto_personas"
                    )

                else:
                    default_unica = (
                        personas_actuales[0]
                        if personas_actuales
                        and personas_actuales[0] in PERSONAS
                        else PERSONAS[0]
                    )

                    persona_unica_editar = st.selectbox(
                        "Persona",
                        PERSONAS,
                        index=PERSONAS.index(
                            default_unica
                        ),
                        key="editar_gasto_persona_unica"
                    )

                    editar_personas_gasto = [
                        persona_unica_editar
                    ]

                editar_nota_gasto = st.text_input(
                    "Nota",
                    value=(
                        ""
                        if pd.isna(registro_gasto["nota"])
                        else str(registro_gasto["nota"])
                    ),
                    key="editar_gasto_nota"
                )

            gasto_guardar_col, gasto_eliminar_col = st.columns(2)

            with gasto_guardar_col:
                if st.button(
                    "💾 Guardar cambios del gasto",
                    type="primary",
                    use_container_width=True
                ):
                    saldo_disponible_edicion = calcular_saldo_caja(
                        impresiones, pagos, gastos
                    )

                    if registro_gasto["pagado_por"] == "Caja común":
                        saldo_disponible_edicion += numero_seguro(
                            registro_gasto["monto"]
                        )

                    if (
                        editar_pagado_por == "Caja común"
                        and editar_monto_gasto > saldo_disponible_edicion
                    ):
                        st.error(
                            "No hay saldo suficiente en el fondo común para guardar "
                            "este cambio. Debes dividir el gasto o registrar aportes primero."
                        )
                    else:
                        actualizar_gasto(
                            id_gasto,
                            editar_fecha_gasto.isoformat(),
                            editar_concepto_gasto,
                            editar_categoria_gasto,
                            editar_monto_gasto,
                            editar_pagado_por,
                            editar_tipo_reparto,
                            editar_personas_gasto,
                            editar_nota_gasto
                        )

                        st.session_state["mensaje"] = (
                            "Gasto actualizado ✅"
                        )

                        st.rerun()

            with gasto_eliminar_col:
                confirmar_eliminar_gasto = st.checkbox(
                    "Confirmo que quiero eliminarlo",
                    key="confirmar_eliminar_gasto"
                )

                if st.button(
                    "🗑️ Eliminar gasto",
                    use_container_width=True,
                    disabled=not confirmar_eliminar_gasto
                ):
                    eliminar_gasto(id_gasto)

                    st.session_state["mensaje"] = (
                        "Gasto eliminado 🗑️"
                    )

                    st.rerun()
