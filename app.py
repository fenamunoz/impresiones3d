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

MATERIALES_FILAMENTO = [
    "PLA", "PLA+", "PETG", "TPU", "ABS", "ASA", "PC", "PA", "PVA", "OTRO"
]
STOCK_BAJO_G = 200


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
            "Material": tipo,
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

    respuesta = conectar_db().table("impresiones").insert(fila).execute()

    if not respuesta.data:
        raise RuntimeError("No se pudo guardar la impresión en Supabase.")

    return int(respuesta.data[0]["id"])


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
# INVENTARIO DE FILAMENTO
# =========================================================

def cargar_inventario():
    respuesta = (
        conectar_db()
        .table("inventario_filamento")
        .select("*")
        .order("fecha_compra", desc=False)
        .order("id", desc=False)
        .execute()
    )

    columnas = [
        "id", "fecha_compra", "material", "color", "marca",
        "rollos_comprados", "gramos_por_rollo", "gramos_iniciales",
        "gramos_disponibles", "precio_total", "nota", "created_at"
    ]
    df = pd.DataFrame(respuesta.data or [], columns=columnas)
    if not df.empty:
        df["fecha_compra"] = pd.to_datetime(df["fecha_compra"])
    return df


def cargar_movimientos_inventario(limite=300):
    respuesta = (
        conectar_db()
        .table("movimientos_inventario")
        .select("*")
        .order("id", desc=True)
        .limit(limite)
        .execute()
    )
    columnas = [
        "id", "fecha", "tipo", "inventario_id", "impresion_id",
        "material", "color", "cantidad_g", "detalle"
    ]
    df = pd.DataFrame(respuesta.data or [], columns=columnas)
    if not df.empty and "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"])
    return df


def agregar_filamento(
    fecha_compra,
    material,
    color,
    rollos,
    gramos_por_rollo,
    precio_total=0,
    marca="",
    nota=""
):
    material = str(material).strip().upper()
    color = str(color).strip().upper()
    total_g = _a_float(rollos) * _a_float(gramos_por_rollo)

    fila = {
        "fecha_compra": fecha_compra,
        "material": material,
        "color": color,
        "marca": str(marca or "").strip(),
        "rollos_comprados": _a_float(rollos),
        "gramos_por_rollo": _a_float(gramos_por_rollo),
        "gramos_iniciales": total_g,
        "gramos_disponibles": total_g,
        "precio_total": _a_float(precio_total),
        "nota": str(nota or "").strip()
    }

    respuesta = (
        conectar_db()
        .table("inventario_filamento")
        .insert(fila)
        .execute()
    )

    if not respuesta.data:
        raise RuntimeError("No se pudo agregar el filamento al inventario.")

    inventario_id = int(respuesta.data[0]["id"])

    conectar_db().table("movimientos_inventario").insert({
        "tipo": "compra",
        "inventario_id": inventario_id,
        "impresion_id": None,
        "material": material,
        "color": color,
        "cantidad_g": total_g,
        "detalle": f"Compra de {rollos:g} rollo(s)"
    }).execute()

    return inventario_id


def ajustar_stock_inventario(inventario_id, nuevo_stock_g, detalle="Ajuste manual"):
    inventario = cargar_inventario()
    fila = inventario[inventario["id"] == int(inventario_id)]
    if fila.empty:
        raise ValueError("No encontré ese lote de filamento.")

    fila = fila.iloc[0]
    stock_anterior = numero_seguro(fila["gramos_disponibles"])
    nuevo_stock_g = max(0.0, _a_float(nuevo_stock_g))
    diferencia = nuevo_stock_g - stock_anterior

    (
        conectar_db()
        .table("inventario_filamento")
        .update({"gramos_disponibles": nuevo_stock_g})
        .eq("id", int(inventario_id))
        .execute()
    )

    if abs(diferencia) > 1e-9:
        conectar_db().table("movimientos_inventario").insert({
            "tipo": "ajuste",
            "inventario_id": int(inventario_id),
            "impresion_id": None,
            "material": str(fila["material"]),
            "color": str(fila["color"]),
            "cantidad_g": diferencia,
            "detalle": str(detalle or "Ajuste manual")
        }).execute()


def stock_disponible(material, color, inventario_df=None):
    if inventario_df is None:
        inventario_df = cargar_inventario()
    if inventario_df.empty:
        return 0.0

    material = str(material).strip().upper()
    color = str(color).strip().upper()
    mask = (
        inventario_df["material"].fillna("").str.upper().eq(material)
        & inventario_df["color"].fillna("").str.upper().eq(color)
    )
    return float(inventario_df.loc[mask, "gramos_disponibles"].fillna(0).sum())


def agrupar_necesidades_inventario(materiales_df):
    necesidades = {}
    if materiales_df is None or materiales_df.empty:
        return necesidades

    for _, fila in materiales_df.iterrows():
        material = str(fila.get("Material", "")).strip().upper()
        color = str(fila.get("Color", "")).strip().upper()
        total = numero_seguro(fila.get("Total a descontar", 0))
        if material and color and total > 0:
            clave = (material, color)
            necesidades[clave] = necesidades.get(clave, 0.0) + total
    return necesidades


def validar_stock(necesidades, inventario_df=None):
    if inventario_df is None:
        inventario_df = cargar_inventario()

    faltantes = []
    for (material, color), necesario in necesidades.items():
        disponible = stock_disponible(material, color, inventario_df)
        if disponible + 1e-9 < necesario:
            faltantes.append({
                "Material": material,
                "Color": color,
                "Necesario": necesario,
                "Disponible": disponible,
                "Faltan": necesario - disponible
            })
    return faltantes


def descontar_inventario(necesidades, impresion_id):
    inventario = cargar_inventario()

    # Validamos todo antes de tocar un solo gramo.
    faltantes = validar_stock(necesidades, inventario)
    if faltantes:
        detalle = "; ".join(
            f"{f['Material']} {f['Color']}: faltan {f['Faltan']:.0f} g"
            for f in faltantes
        )
        raise ValueError("Stock insuficiente. " + detalle)

    for (material, color), cantidad in necesidades.items():
        restante = float(cantidad)
        lotes = inventario[
            inventario["material"].fillna("").str.upper().eq(material)
            & inventario["color"].fillna("").str.upper().eq(color)
            & (inventario["gramos_disponibles"].fillna(0) > 0)
        ].sort_values(["fecha_compra", "id"])

        for _, lote in lotes.iterrows():
            if restante <= 1e-9:
                break

            disponible = numero_seguro(lote["gramos_disponibles"])
            usar = min(disponible, restante)
            nuevo_stock = disponible - usar

            (
                conectar_db()
                .table("inventario_filamento")
                .update({"gramos_disponibles": nuevo_stock})
                .eq("id", int(lote["id"]))
                .execute()
            )

            conectar_db().table("movimientos_inventario").insert({
                "tipo": "impresion",
                "inventario_id": int(lote["id"]),
                "impresion_id": int(impresion_id),
                "material": material,
                "color": color,
                "cantidad_g": -usar,
                "detalle": f"Consumo impresión #{impresion_id}"
            }).execute()

            restante -= usar


def devolver_stock_impresion(impresion_id):
    respuesta = (
        conectar_db()
        .table("movimientos_inventario")
        .select("*")
        .eq("impresion_id", int(impresion_id))
        .eq("tipo", "impresion")
        .execute()
    )

    movimientos = respuesta.data or []
    for mov in movimientos:
        cantidad = abs(_a_float(mov.get("cantidad_g", 0)))
        inventario_id = mov.get("inventario_id")
        if not inventario_id or cantidad <= 0:
            continue

        lote_resp = (
            conectar_db()
            .table("inventario_filamento")
            .select("gramos_disponibles")
            .eq("id", int(inventario_id))
            .execute()
        )
        if not lote_resp.data:
            continue

        stock_actual = _a_float(lote_resp.data[0]["gramos_disponibles"])
        (
            conectar_db()
            .table("inventario_filamento")
            .update({"gramos_disponibles": stock_actual + cantidad})
            .eq("id", int(inventario_id))
            .execute()
        )

        conectar_db().table("movimientos_inventario").insert({
            "tipo": "devolucion",
            "inventario_id": int(inventario_id),
            "impresion_id": int(impresion_id),
            "material": mov.get("material", ""),
            "color": mov.get("color", ""),
            "cantidad_g": cantidad,
            "detalle": f"Devolución por eliminar impresión #{impresion_id}"
        }).execute()


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


def marcar_purga_manual():
    """Marca que el porcentaje de purga fue editado manualmente."""
    st.session_state["purga_manual"] = True


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
# NAVEGACIÓN
# =========================================================

PAGINAS = [
    "➕ Nueva impresión",
    "🧵 Inventario",
    "📋 Historial",
    "💳 Registrar pago",
    "💰 Fondo común",
    "📊 Resumen"
]

pagina_activa = st.segmented_control(
    "Navegación",
    PAGINAS,
    default=PAGINAS[0],
    key="pagina_activa",
    label_visibility="collapsed"
)

if pagina_activa is None:
    pagina_activa = PAGINAS[0]


# =========================================================
# NUEVA IMPRESIÓN
# =========================================================

if pagina_activa == "➕ Nueva impresión":
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
                st.session_state["precio_venta_calculado"] = precio_venta

                plan = []
                for filamento in resultado["filamentos"]:
                    plan.append({
                        "Material": str(filamento.get("Material", "PLA")).upper(),
                        "Color": str(filamento.get("Color", "SIN COLOR")).upper(),
                        "Gramos modelo": numero_seguro(filamento.get("Gramos", 0)),
                        "Purga extra": 0.0
                    })
                st.session_state["materiales_plan"] = pd.DataFrame(plan)
                st.session_state["materiales_editor_version"] = (
                    st.session_state.get("materiales_editor_version", 0) + 1
                )
                # Nueva impresión: volvemos a la purga automática sugerida.
                st.session_state["purga_manual"] = False
                st.session_state.pop("purga_pct", None)
                st.session_state.pop("purga_sugerida_anterior", None)

            except Exception as error:
                st.error(f"No pude leer el modelo: {error}")

    if "resultado" in st.session_state:
        resultado = st.session_state["resultado"]
        destino_actual = st.session_state["destino_calculado"]
        precio_venta_actual = st.session_state["precio_venta_calculado"]

        st.divider()
        st.subheader(resultado["modelo"])
        st.caption(f"Perfil: {resultado['perfil']}")
        st.write("## Datos de impresión")

        horas_iniciales, minutos_iniciales = separar_duracion(resultado["horas"])

        inventario_actual = cargar_inventario()
        plan_df = st.session_state.get("materiales_plan", pd.DataFrame()).copy()

        if plan_df.empty:
            st.error("MakerWorld no entregó materiales para esta impresión.")
        else:
            # ---------------------------------------------------------
            # Opciones REALES del inventario: solo combinaciones con stock.
            # El desplegable muestra el stock disponible, pero internamente
            # seguimos guardando Material + Color por separado.
            # ---------------------------------------------------------
            opciones_inventario = {}

            if not inventario_actual.empty:
                inventario_disponible = inventario_actual[
                    inventario_actual["gramos_disponibles"].fillna(0) > 0
                ].copy()

                if not inventario_disponible.empty:
                    agrupado_stock = (
                        inventario_disponible
                        .groupby(["material", "color"], as_index=False)["gramos_disponibles"]
                        .sum()
                    )

                    for _, fila_stock in agrupado_stock.iterrows():
                        material_stock = str(fila_stock["material"]).strip().upper()
                        color_stock = str(fila_stock["color"]).strip().upper()
                        gramos_stock = numero_seguro(fila_stock["gramos_disponibles"])
                        etiqueta = (
                            f"{emoji_color(color_stock)} {color_stock} — "
                            f"{gramos_stock:.0f} g disponibles ({material_stock})"
                        )
                        opciones_inventario[etiqueta] = {
                            "Material": material_stock,
                            "Color": color_stock,
                            "Disponible": gramos_stock
                        }

            etiquetas_disponibles = list(opciones_inventario.keys())
            opcion_vacia = "— Selecciona un color del inventario —"
            opciones_editor = [opcion_vacia] + etiquetas_disponibles

            if not etiquetas_disponibles:
                st.error(
                    "No hay filamento con stock disponible. Agrega rollos en "
                    "🧵 Inventario antes de registrar la impresión."
                )

            # ---------------------------------------------------------
            # Si MakerWorld trae una combinación que sí existe, la usamos.
            # Si no existe, dejamos la fila pendiente para que el usuario
            # elija explícitamente un color disponible.
            # ---------------------------------------------------------
            def buscar_etiqueta(material, color):
                material = str(material or "").strip().upper()
                color = str(color or "").strip().upper()
                for etiqueta, info in opciones_inventario.items():
                    if info["Material"] == material and info["Color"] == color:
                        return etiqueta
                return opcion_vacia

            editor_base = pd.DataFrame({
                "Color": [
                    buscar_etiqueta(fila.get("Material"), fila.get("Color"))
                    for _, fila in plan_df.iterrows()
                ],
                "Gramos": pd.to_numeric(
                    plan_df.get("Gramos modelo", pd.Series(dtype=float)),
                    errors="coerce"
                ).fillna(0).tolist()
            })

            # ---------------------------------------------------------
            # Primera fila compacta: tiempo | colores | costo total.
            # ---------------------------------------------------------
            col_horas, col_minutos, col_colores, col_total = st.columns(
                [0.55, 0.55, 2.7, 1.25],
                vertical_alignment="top"
            )

            with col_horas:
                st.caption("⏱️ Horas")
                horas_editadas = st.number_input(
                    "Horas",
                    min_value=0,
                    value=horas_iniciales,
                    step=1,
                    key="nueva_imp_horas",
                    label_visibility="collapsed"
                )

            with col_minutos:
                st.caption("Minutos")
                minutos_editados = st.number_input(
                    "Minutos",
                    min_value=0,
                    max_value=59,
                    value=minutos_iniciales,
                    step=1,
                    key="nueva_imp_minutos",
                    label_visibility="collapsed"
                )

            tiempo_editado = horas_editadas + minutos_editados / 60

            with col_colores:
                st.caption("🧵 Colores / filamentos")
                materiales_editor = st.data_editor(
                    editor_base,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    height=max(120, min(250, 38 + 35 * max(len(editor_base), 1))),
                    key=(
                        f"editor_materiales_"
                        f"{st.session_state.get('materiales_editor_version', 0)}"
                    ),
                    column_config={
                        "Color": st.column_config.SelectboxColumn(
                            "Color",
                            options=opciones_editor,
                            required=True,
                            width="large",
                            help=(
                                "Solo aparecen colores/materiales que actualmente "
                                "tienen stock disponible."
                            )
                        ),
                        "Gramos": st.column_config.NumberColumn(
                            "Gramos",
                            min_value=0.0,
                            step=1.0,
                            format="%.0f g",
                            width="small"
                        )
                    }
                )

            # Convertimos la selección visible del inventario a Material + Color.
            filas_reales = []
            filas_sin_color = 0
            for _, fila_editada in materiales_editor.iterrows():
                etiqueta = str(fila_editada.get("Color", opcion_vacia))
                gramos_modelo = numero_seguro(fila_editada.get("Gramos", 0))
                info = opciones_inventario.get(etiqueta)

                if info is None:
                    filas_sin_color += 1
                    filas_reales.append({
                        "Material": "",
                        "Color": "",
                        "Gramos modelo": gramos_modelo
                    })
                else:
                    filas_reales.append({
                        "Material": info["Material"],
                        "Color": info["Color"],
                        "Gramos modelo": gramos_modelo
                    })

            materiales_reales = pd.DataFrame(filas_reales)

            if not materiales_reales.empty:
                # Guardamos las selecciones reales para que persistan en reruns.
                st.session_state["materiales_plan"] = materiales_reales.copy()

            # ---------------------------------------------------------
            # Purga automática: 5% si finalmente se usa un solo color,
            # 10% si se usan dos o más. Siempre editable.
            # ---------------------------------------------------------
            seleccionados_validos = materiales_reales[
                (materiales_reales["Material"].astype(str).str.len() > 0)
                & (materiales_reales["Color"].astype(str).str.len() > 0)
            ] if not materiales_reales.empty else pd.DataFrame()

            combinaciones_usadas = (
                seleccionados_validos[["Material", "Color"]]
                .drop_duplicates()
                if not seleccionados_validos.empty
                else pd.DataFrame()
            )

            purga_sugerida = 5.0 if len(combinaciones_usadas) <= 1 else 10.0

            if "purga_manual" not in st.session_state:
                st.session_state["purga_manual"] = False

            sugerida_anterior = st.session_state.get("purga_sugerida_anterior")
            if (
                "purga_pct" not in st.session_state
                or (
                    not st.session_state.get("purga_manual", False)
                    and sugerida_anterior != purga_sugerida
                )
            ):
                st.session_state["purga_pct"] = purga_sugerida

            st.session_state["purga_sugerida_anterior"] = purga_sugerida

            peso_modelo = (
                float(materiales_reales["Gramos modelo"].fillna(0).sum())
                if not materiales_reales.empty else 0.0
            )

            purga_pct = st.session_state.get("purga_pct", purga_sugerida)
            purga_total = peso_modelo * purga_pct / 100
            consumo_total = peso_modelo + purga_total

            costo_material = consumo_total / 1000 * precio_filamento_kg
            costo_electricidad = (
                tiempo_editado * consumo_impresora_w / 1000 * precio_kwh
            )
            costo_depreciacion = (
                tiempo_editado * precio_impresora / vida_util_horas
            )
            costo_total = costo_material + costo_electricidad + costo_depreciacion

            with col_total:
                st.caption("💰 Costo total")
                st.markdown(f"## {formatear_clp(costo_total)}")
                st.caption(f"Modelo: {peso_modelo:.0f} g")
                st.caption(f"Consumo estimado: {consumo_total:.0f} g")
                st.number_input(
                    "Purga estimada (%)",
                    min_value=0.0,
                    max_value=300.0,
                    step=1.0,
                    key="purga_pct",
                    on_change=marcar_purga_manual,
                    help=(
                        f"Sugerencia automática actual: {purga_sugerida:.0f}% "
                        "(5% un color / 10% multicolor). Puedes editarla."
                    )
                )

            # El number_input puede haber cambiado en esta misma ejecución;
            # recalculamos con el valor definitivo.
            purga_pct = numero_seguro(st.session_state.get("purga_pct", purga_sugerida))
            purga_total = peso_modelo * purga_pct / 100
            consumo_total = peso_modelo + purga_total

            # Repartimos la purga proporcionalmente entre los colores elegidos.
            if not materiales_reales.empty:
                materiales_reales["Purga extra"] = 0.0
                if peso_modelo > 0:
                    materiales_reales["Purga extra"] = (
                        materiales_reales["Gramos modelo"] / peso_modelo * purga_total
                    )
                materiales_reales["Total a descontar"] = (
                    materiales_reales["Gramos modelo"]
                    + materiales_reales["Purga extra"]
                )

            necesidades = agrupar_necesidades_inventario(materiales_reales)
            faltantes = validar_stock(necesidades, inventario_actual)

            # ---------------------------------------------------------
            # Todo en un solo color: solo ofrece stock que realmente existe.
            # ---------------------------------------------------------
            if etiquetas_disponibles:
                with st.expander("🎨 Usar un solo color para toda la impresión"):
                    unico1, unico2 = st.columns([3, 1])
                    with unico1:
                        opcion_unica = st.selectbox(
                            "Color / filamento disponible",
                            etiquetas_disponibles,
                            key="filamento_unico"
                        )
                    with unico2:
                        st.write("")
                        st.write("")
                        if st.button(
                            "Aplicar a todos",
                            use_container_width=True,
                            key="aplicar_filamento_unico"
                        ):
                            info_unica = opciones_inventario[opcion_unica]
                            nuevo_plan = plan_df.copy()
                            nuevo_plan["Material"] = info_unica["Material"]
                            nuevo_plan["Color"] = info_unica["Color"]
                            st.session_state["materiales_plan"] = nuevo_plan[
                                ["Material", "Color", "Gramos modelo"]
                            ].copy()
                            st.session_state["materiales_editor_version"] = (
                                st.session_state.get("materiales_editor_version", 0) + 1
                            )
                            # Si la purga no fue personalizada, pasará sola a 5%.
                            st.rerun()

            # ---------------------------------------------------------
            # Revisión compacta de stock.
            # ---------------------------------------------------------
            if filas_sin_color:
                st.warning(
                    "⚠️ Selecciona un color disponible para todas las filas antes "
                    "de guardar la impresión."
                )

            if necesidades:
                resumen_stock = []
                for (material, color), necesario in necesidades.items():
                    disponible = stock_disponible(material, color, inventario_actual)
                    resumen_stock.append({
                        "Color": f"{emoji_color(color)} {color} ({material})",
                        "Necesario": necesario,
                        "Disponible": disponible,
                        "Quedaría": disponible - necesario
                    })

                with st.expander(
                    "📦 Revisar stock después de esta impresión",
                    expanded=bool(faltantes)
                ):
                    st.dataframe(
                        pd.DataFrame(resumen_stock),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Necesario": st.column_config.NumberColumn(format="%.0f g"),
                            "Disponible": st.column_config.NumberColumn(format="%.0f g"),
                            "Quedaría": st.column_config.NumberColumn(format="%.0f g")
                        }
                    )

            if faltantes:
                for f in faltantes:
                    st.error(
                        f"⚠️ No alcanza {f['Color']} ({f['Material']}): "
                        f"necesitas {f['Necesario']:.0f} g y hay "
                        f"{f['Disponible']:.0f} g. Faltan {f['Faltan']:.0f} g."
                    )

            # El desglose queda disponible sin ocupar espacio permanentemente.
            with st.expander("💰 Ver desglose de costos"):
                d1, d2, d3, d4 = st.columns(4)
                with d1:
                    st.metric("🧵 Material", formatear_clp(costo_material))
                with d2:
                    st.metric("⚡ Electricidad", formatear_clp(costo_electricidad))
                with d3:
                    st.metric("🖨️ Depreciación", formatear_clp(costo_depreciacion))
                with d4:
                    st.metric(
                        "🗑️ Purga",
                        f"{purga_total:.0f} g ({purga_pct:.0f}%)"
                    )

            ganancia = 0
            if destino_actual == "Venta":
                ganancia = precio_venta_actual - costo_total
                st.metric("📈 Ganancia estimada", formatear_clp(ganancia))

            st.divider()
            fecha_impresion = st.date_input(
                "Fecha", value=date.today(), format="DD/MM/YYYY"
            )

            if st.button(
                "💾 Guardar impresión",
                type="primary",
                disabled=(
                    bool(faltantes)
                    or not bool(necesidades)
                    or filas_sin_color > 0
                    or not bool(etiquetas_disponibles)
                )
            ):
                # Revalidamos justo antes de guardar por si otra persona usó stock.
                inventario_ultimo = cargar_inventario()
                faltantes_ultimo = validar_stock(necesidades, inventario_ultimo)

                if faltantes_ultimo:
                    st.error(
                        "El stock cambió antes de guardar. Revisa nuevamente el inventario."
                    )
                else:
                    materiales_json = json.dumps(
                        materiales_reales.fillna("").to_dict(orient="records"),
                        ensure_ascii=False
                    )

                    impresion_id = guardar_impresion(
                        fecha_impresion.isoformat(),
                        destino_actual,
                        st.session_state["link_calculado"],
                        resultado["modelo"],
                        resultado["perfil"],
                        tiempo_editado,
                        peso_modelo,
                        materiales_json,
                        costo_material,
                        costo_electricidad,
                        costo_depreciacion,
                        costo_total,
                        precio_venta_actual,
                        ganancia
                    )

                    try:
                        descontar_inventario(necesidades, impresion_id)
                    except Exception:
                        # Si falla el descuento, quitamos la impresión recién creada
                        # para no dejar un registro que no consumió inventario.
                        eliminar_impresion(impresion_id)
                        raise

                    st.session_state["mensaje"] = (
                        f"Impresión #{impresion_id} guardada para {destino_actual} "
                        f"y stock descontado ✅"
                    )

                    for clave in ["resultado", "materiales_plan"]:
                        st.session_state.pop(clave, None)
                    st.rerun()


# =========================================================
# INVENTARIO
# =========================================================

if pagina_activa == "🧵 Inventario":
    st.subheader("🧵 Inventario de filamento")
    st.caption(
        "Registra los rollos que compran. Las impresiones descuentan automáticamente "
        "el consumo real (modelo + purga) desde los lotes más antiguos."
    )

    inventario = cargar_inventario()

    total_disponible = (
        inventario["gramos_disponibles"].fillna(0).sum()
        if not inventario.empty else 0
    )
    total_inicial = (
        inventario["gramos_iniciales"].fillna(0).sum()
        if not inventario.empty else 0
    )

    i1, i2, i3 = st.columns(3)
    with i1:
        st.metric("Stock disponible", f"{total_disponible / 1000:.2f} kg")
    with i2:
        st.metric("Equivalente", f"{total_disponible / 1000:.2f} rollos de 1 kg")
    with i3:
        consumido_hist = max(0.0, total_inicial - total_disponible)
        st.metric("Consumido / ajustado", f"{consumido_hist / 1000:.2f} kg")

    st.divider()
    st.write("### ➕ Agregar compra de filamento")

    c1, c2, c3 = st.columns(3)
    with c1:
        inv_material = st.selectbox("Material", MATERIALES_FILAMENTO, key="inv_material")
        inv_color = st.text_input(
            "Color", placeholder="Ej: Negro / Blanco / Burgundy", key="inv_color"
        )
    with c2:
        inv_rollos = st.number_input(
            "Cantidad de rollos", min_value=1, value=1, step=1, key="inv_rollos"
        )
        inv_gramos_rollo = st.number_input(
            "Gramos por rollo", min_value=1, value=1000, step=50, key="inv_gramos_rollo"
        )
    with c3:
        inv_marca = st.text_input("Marca (opcional)", key="inv_marca")
        inv_fecha = st.date_input(
            "Fecha de compra", value=date.today(), format="DD/MM/YYYY", key="inv_fecha"
        )

    inv_precio = st.number_input(
        "Precio total de la compra (opcional)", min_value=0, value=0, step=1000,
        key="inv_precio"
    )
    inv_nota = st.text_input("Nota (opcional)", key="inv_nota")

    total_compra_g = inv_rollos * inv_gramos_rollo
    st.info(
        f"Se agregarán **{inv_rollos} rollo(s)** = **{total_compra_g / 1000:.2f} kg** "
        f"de {inv_material} {inv_color.strip().upper() if inv_color.strip() else '—'}."
    )

    if st.button("📦 Agregar al inventario", type="primary"):
        if not inv_color.strip():
            st.error("Escribe el color del filamento.")
        else:
            agregar_filamento(
                inv_fecha.isoformat(), inv_material, inv_color, inv_rollos,
                inv_gramos_rollo, inv_precio, inv_marca, inv_nota
            )
            st.session_state["mensaje"] = (
                f"Agregados {inv_rollos} rollo(s) de {inv_material} "
                f"{inv_color.strip().upper()} al inventario ✅"
            )
            st.rerun()

    st.divider()
    st.write("### 📦 Stock actual")

    if inventario.empty:
        st.info("Todavía no hay rollos registrados.")
    else:
        resumen_inv = (
            inventario.groupby(["material", "color"], as_index=False)
            .agg(
                Stock_g=("gramos_disponibles", "sum"),
                Comprado_g=("gramos_iniciales", "sum"),
                Lotes=("id", "count")
            )
            .sort_values(["material", "color"])
        )
        resumen_inv["Stock_kg"] = resumen_inv["Stock_g"] / 1000
        resumen_inv["Estado"] = resumen_inv["Stock_g"].apply(
            lambda x: "⚠️ Stock bajo" if x <= STOCK_BAJO_G else "✅ OK"
        )
        resumen_mostrar = resumen_inv[
            ["material", "color", "Stock_g", "Stock_kg", "Lotes", "Estado"]
        ].copy()
        resumen_mostrar.columns = [
            "Material", "Color", "Stock (g)", "Stock (kg)", "Lotes", "Estado"
        ]
        st.dataframe(
            resumen_mostrar,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Stock (g)": st.column_config.NumberColumn(format="%.0f g"),
                "Stock (kg)": st.column_config.NumberColumn(format="%.2f kg")
            }
        )

        bajos = resumen_inv[resumen_inv["Stock_g"] <= STOCK_BAJO_G]
        for _, fila in bajos.iterrows():
            st.warning(
                f"Stock bajo: {fila['material']} {fila['color']} — "
                f"quedan {fila['Stock_g']:.0f} g."
            )

        with st.expander("🔧 Ajustar stock de un lote"):
            opciones_lotes = {}
            for _, lote in inventario.iterrows():
                etiqueta = (
                    f"Lote #{int(lote['id'])} | {lote['material']} {lote['color']} | "
                    f"{numero_seguro(lote['gramos_disponibles']):.0f} g disponibles"
                )
                opciones_lotes[etiqueta] = int(lote["id"])

            etiqueta_lote = st.selectbox("Lote", list(opciones_lotes.keys()))
            lote_id = opciones_lotes[etiqueta_lote]
            lote_sel = inventario[inventario["id"] == lote_id].iloc[0]
            nuevo_stock = st.number_input(
                "Stock real disponible (g)",
                min_value=0.0,
                value=numero_seguro(lote_sel["gramos_disponibles"]),
                step=1.0,
                key=f"ajuste_stock_{lote_id}"
            )
            motivo_ajuste = st.text_input(
                "Motivo", placeholder="Ej: pesamos el rollo / merma / corrección"
            )
            if st.button("Guardar ajuste de stock"):
                ajustar_stock_inventario(lote_id, nuevo_stock, motivo_ajuste)
                st.session_state["mensaje"] = "Stock ajustado ✅"
                st.rerun()

    st.divider()
    st.write("### 🧾 Movimientos recientes")
    movimientos = cargar_movimientos_inventario()
    if movimientos.empty:
        st.info("Todavía no hay movimientos de inventario.")
    else:
        tabla_mov = movimientos.copy()
        tabla_mov["fecha"] = tabla_mov["fecha"].dt.strftime("%d/%m/%Y %H:%M")
        tabla_mov = tabla_mov[
            ["fecha", "tipo", "material", "color", "cantidad_g", "impresion_id", "detalle"]
        ]
        tabla_mov.columns = [
            "Fecha", "Tipo", "Material", "Color", "Movimiento (g)", "Impresión", "Detalle"
        ]
        st.dataframe(
            tabla_mov,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Movimiento (g)": st.column_config.NumberColumn(format="%+.0f g")
            }
        )


# =========================================================
# RESUMEN
# =========================================================

if pagina_activa == "📊 Resumen":
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

if pagina_activa == "💳 Registrar pago":
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

if pagina_activa == "💰 Fondo común":
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

if pagina_activa == "📋 Historial":
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

    HISTORIALES = [
        "🖨️ Impresiones",
        "💳 Pagos",
        "💸 Gastos"
    ]

    historial_activo = st.segmented_control(
        "Tipo de historial",
        HISTORIALES,
        default=HISTORIALES[0],
        key="historial_activo",
        label_visibility="collapsed"
    )

    if historial_activo is None:
        historial_activo = HISTORIALES[0]

    # -----------------------------------------------------
    # HISTORIAL IMPRESIONES
    # -----------------------------------------------------

    if historial_activo == "🖨️ Impresiones":
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
                editar_gramos = numero_seguro(registro["gramos"])
                st.number_input(
                    "Gramos del modelo",
                    min_value=0.0,
                    value=editar_gramos,
                    step=1.0,
                    disabled=True,
                    key=f"editar_imp_gramos_{id_impresion}"
                )
                st.caption(
                    "El consumo de material y la purga quedan amarrados al inventario "
                    "y no se editan desde el historial."
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
                            devolver_stock_impresion(id_impresion)
                            eliminar_impresion(id_impresion)
                            st.session_state.pop(
                                "confirmar_eliminar_imp_id",
                                None
                            )
                            st.session_state["mensaje"] = (
                                "Impresión eliminada y filamento devuelto al inventario 🗑️🧵"
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

    if historial_activo == "💳 Pagos":
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
                if st.button(
                    "🗑️ Eliminar pago",
                    use_container_width=True,
                    key=f"pedir_eliminar_pago_{id_pago}"
                ):
                    st.session_state[
                        "confirmar_eliminar_pago_id"
                    ] = id_pago

                if (
                    st.session_state.get(
                        "confirmar_eliminar_pago_id"
                    )
                    == id_pago
                ):
                    st.warning(
                        "¿Seguro que quieres eliminar este pago? "
                        "Esta acción no se puede deshacer."
                    )

                    confirmar_pago_col, cancelar_pago_col = st.columns(2)

                    with confirmar_pago_col:
                        if st.button(
                            "Sí, eliminar",
                            type="primary",
                            use_container_width=True,
                            key=f"confirmar_eliminar_pago_{id_pago}"
                        ):
                            eliminar_pago(id_pago)
                            st.session_state.pop(
                                "confirmar_eliminar_pago_id",
                                None
                            )
                            st.session_state["mensaje"] = (
                                "Pago eliminado 🗑️"
                            )
                            st.rerun()

                    with cancelar_pago_col:
                        if st.button(
                            "Cancelar",
                            use_container_width=True,
                            key=f"cancelar_eliminar_pago_{id_pago}"
                        ):
                            st.session_state.pop(
                                "confirmar_eliminar_pago_id",
                                None
                            )
                            st.rerun()

    # -----------------------------------------------------
    # HISTORIAL GASTOS
    # -----------------------------------------------------

    if historial_activo == "💸 Gastos":
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
