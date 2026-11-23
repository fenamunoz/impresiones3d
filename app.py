import json
import re
import sqlite3
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
    layout="wide",
)

PERSONAS = ["Mauri", "Fabi", "Beto", "Pame", "Feña"]
DESTINOS = PERSONAS + ["Venta"]
DB = "impresiones3d.db"

MORADO = "#8B5CF6"
MORADO_CLARO = "#A78BFA"
AZUL = "#3B82F6"
VERDE = "#22C55E"


# =========================================================
# ESTILO
# =========================================================

st.markdown(
    f"""
    <style>
    :root {{
        --primary-color: {MORADO};
    }}

    button[data-testid="stBaseButton-primary"] {{
        background-color: {MORADO} !important;
        border-color: {MORADO} !important;
        color: white !important;
    }}

    button[data-testid="stBaseButton-primary"]:hover {{
        background-color: #7C3AED !important;
        border-color: #7C3AED !important;
    }}

    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {MORADO_CLARO} !important;
    }}

    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: {MORADO} !important;
    }}

    div[data-baseweb="input"]:focus-within {{
        border-color: {MORADO} !important;
        box-shadow: 0 0 0 1px {MORADO} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FORMATO
# =========================================================


def formatear_clp(valor):
    try:
        numero = int(round(float(valor)))
    except (TypeError, ValueError):
        numero = 0
    return "$" + f"{numero:,}".replace(",", ".")


def parsear_clp(texto):
    if texto is None:
        return 0
    numeros = re.sub(r"[^\d]", "", str(texto))
    return int(numeros) if numeros else 0


def numero_seguro(valor):
    if pd.isna(valor):
        return 0.0
    return float(valor)


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
    "BEIGE": (220, 205, 170),
}

EMOJI_COLOR = {
    "NEGRO": "⬛",
    "BLANCO": "⬜",
    "GRIS": "◼️",
    "ROJO": "🟥",
    "NARANJO": "🟧",
    "AMARILLO": "🟨",
    "VERDE": "🟩",
    "CELESTE": "🟦",
    "AZUL": "🟦",
    "MORADO": "🟪",
    "VIOLETA": "🟪",
    "ROSADO": "🟪",
    "CAFÉ": "🟫",
    "BEIGE": "🟨",
    "SIN COLOR": "◻️",
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


# =========================================================
# BASE DE DATOS
# =========================================================


def conectar_db():
    return sqlite3.connect(DB)


def crear_base_de_datos():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS impresiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            persona TEXT NOT NULL,
            link TEXT,
            modelo TEXT,
            perfil TEXT,
            horas REAL,
            gramos REAL,
            materiales TEXT,
            costo_material REAL,
            costo_electricidad REAL,
            costo_depreciacion REAL,
            costo_total REAL,
            precio_venta REAL,
            ganancia REAL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            persona TEXT NOT NULL,
            monto REAL NOT NULL,
            nota TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor REAL NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


crear_base_de_datos()


# =========================================================
# CONFIGURACIÓN DE COSTOS
# =========================================================

CONFIG_DEFAULT = {
    "precio_filamento_kg": 20000,
    "precio_impresora": 1000000,
    "vida_util_horas": 5000,
    "consumo_impresora_w": 150,
    "precio_kwh": 250,
}


def cargar_configuracion():
    config = CONFIG_DEFAULT.copy()
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT clave, valor FROM configuracion")
    for clave, valor in cursor.fetchall():
        config[clave] = valor
    conn.close()
    return config


def guardar_configuracion(config):
    conn = conectar_db()
    cursor = conn.cursor()
    for clave, valor in config.items():
        cursor.execute(
            """
            INSERT INTO configuracion (clave, valor)
            VALUES (?, ?)
            ON CONFLICT(clave)
            DO UPDATE SET valor = excluded.valor
            """,
            (clave, valor),
        )
    conn.commit()
    conn.close()


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

    api_url = f"https://api.bambulab.com/v1/design-service/design/{model_id}"
    respuesta = requests.get(
        api_url,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        timeout=20,
    )

    if respuesta.status_code != 200:
        raise ValueError(f"MakerWorld respondió con error {respuesta.status_code}")

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
    muestras_color = []

    for filamento in instancia.get("instanceFilaments", []):
        tipo = filamento.get("type", "Desconocido").upper()
        gramos = float(filamento.get("usedG", 0) or 0)
        codigo = filamento.get("color", "").upper()
        color = nombre_color(codigo)

        filamentos.append({
            "Material": f"{tipo} {color}",
            "Gramos": gramos,
        })

        muestras_color.append({
            "Material": tipo,
            "Color": color,
            "Codigo": codigo,
            "Gramos": gramos,
        })

    if not filamentos and peso > 0:
        filamentos.append({"Material": "DESCONOCIDO", "Gramos": peso})

    return {
        "modelo": nombre_modelo,
        "perfil": nombre_perfil,
        "horas": horas,
        "peso": peso,
        "filamentos": filamentos,
        "muestras_color": muestras_color,
    }


# =========================================================
# CRUD IMPRESIONES / PAGOS
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
    ganancia,
):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO impresiones (
            fecha, persona, link, modelo, perfil, horas, gramos, materiales,
            costo_material, costo_electricidad, costo_depreciacion,
            costo_total, precio_venta, ganancia
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
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
            ganancia,
        ),
    )
    conn.commit()
    conn.close()


def actualizar_impresion(
    registro_id,
    fecha,
    persona,
    modelo,
    horas,
    gramos,
    costo_total,
    precio_venta,
    ganancia,
):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE impresiones
        SET fecha = ?, persona = ?, modelo = ?, horas = ?, gramos = ?,
            costo_total = ?, precio_venta = ?, ganancia = ?
        WHERE id = ?
        """,
        (
            fecha,
            persona,
            modelo,
            horas,
            gramos,
            costo_total,
            precio_venta,
            ganancia,
            registro_id,
        ),
    )
    conn.commit()
    conn.close()


def eliminar_impresion(registro_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM impresiones WHERE id = ?", (registro_id,))
    conn.commit()
    conn.close()


def guardar_pago(fecha, persona, monto, nota):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pagos (fecha, persona, monto, nota) VALUES (?, ?, ?, ?)",
        (fecha, persona, monto, nota),
    )
    conn.commit()
    conn.close()


def actualizar_pago(registro_id, fecha, persona, monto, nota):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE pagos
        SET fecha = ?, persona = ?, monto = ?, nota = ?
        WHERE id = ?
        """,
        (fecha, persona, monto, nota, registro_id),
    )
    conn.commit()
    conn.close()


def eliminar_pago(registro_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pagos WHERE id = ?", (registro_id,))
    conn.commit()
    conn.close()


def cargar_impresiones():
    conn = conectar_db()
    df = pd.read_sql_query(
        "SELECT * FROM impresiones ORDER BY fecha DESC, id DESC",
        conn,
    )
    conn.close()
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
    return df


def cargar_pagos():
    conn = conectar_db()
    df = pd.read_sql_query(
        "SELECT * FROM pagos ORDER BY fecha DESC, id DESC",
        conn,
    )
    conn.close()
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
    return df


# =========================================================
# CALLBACKS
# =========================================================


def seleccionar_destino(nombre):
    st.session_state["destino"] = nombre


def seleccionar_persona_pago(nombre):
    st.session_state["persona_pago"] = nombre


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.header("⚙️ Configuración de costos")
    st.caption("Los montos quedan guardados.")

    texto_filamento = st.text_input(
        "Filamento ($/kg)",
        value=formatear_clp(config_guardada["precio_filamento_kg"]),
        key="cfg_filamento",
    )
    precio_filamento_kg = parsear_clp(texto_filamento)

    texto_impresora = st.text_input(
        "Valor impresora",
        value=formatear_clp(config_guardada["precio_impresora"]),
        key="cfg_impresora",
    )
    precio_impresora = parsear_clp(texto_impresora)

    vida_util_horas = st.number_input(
        "Vida útil impresora (h)",
        min_value=1,
        value=int(config_guardada["vida_util_horas"]),
        step=500,
    )

    consumo_impresora_w = st.number_input(
        "Consumo promedio (W)",
        min_value=0,
        value=int(config_guardada["consumo_impresora_w"]),
        step=10,
    )

    texto_kwh = st.text_input(
        "Electricidad ($/kWh)",
        value=formatear_clp(config_guardada["precio_kwh"]),
        key="cfg_kwh",
    )
    precio_kwh = parsear_clp(texto_kwh)

    if st.button(
        "💾 Guardar configuración",
        type="primary",
        use_container_width=True,
    ):
        guardar_configuracion(
            {
                "precio_filamento_kg": precio_filamento_kg,
                "precio_impresora": precio_impresora,
                "vida_util_horas": vida_util_horas,
                "consumo_impresora_w": consumo_impresora_w,
                "precio_kwh": precio_kwh,
            }
        )
        st.success("Configuración guardada ✅")


# =========================================================
# MENSAJES Y ENCABEZADO
# =========================================================

if "mensaje" in st.session_state:
    st.success(st.session_state["mensaje"])
    del st.session_state["mensaje"]

st.title("🖨️ Impresiones 3D")
st.caption("Control de impresiones, costos y pagos")


tab_nueva, tab_resumen, tab_pago, tab_historial = st.tabs(
    [
        "➕ Nueva impresión",
        "📊 Resumen",
        "💳 Registrar pago",
        "📋 Historial",
    ]
)


# =========================================================
# NUEVA IMPRESIÓN
# =========================================================

with tab_nueva:
    st.subheader("Nueva impresión")

    link = st.text_input(
        "Link del modelo",
        placeholder="Pega aquí el link de MakerWorld...",
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
                args=(nombre,),
            )

            if nombre == "Venta" and st.session_state["destino"] == "Venta":
                texto_precio_venta = st.text_input(
                    "Precio de venta",
                    value="$0",
                    key="precio_venta_inline",
                )
                precio_venta = parsear_clp(texto_precio_venta)

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

        tiempo_editado = st.number_input(
            "⏱️ Tiempo de impresión (horas)",
            min_value=0.0,
            value=float(round(resultado["horas"], 2)),
            step=0.1,
        )

        # -------------------------------------------------
        # MATERIALES: TARJETAS SIMPLES + TABLA EDITABLE
        # -------------------------------------------------

        st.write("🧵 **Materiales utilizados**")

        muestras = resultado.get("muestras_color", [])
        if muestras:
            columnas_materiales = st.columns(min(len(muestras), 4))
            for i, muestra in enumerate(muestras):
                with columnas_materiales[i % len(columnas_materiales)]:
                    with st.container(border=True):
                        color_nombre = muestra["Color"]
                        emoji = EMOJI_COLOR.get(color_nombre, "◻️")
                        st.markdown(
                            f"### {emoji} {muestra['Material']} {color_nombre}"
                        )
                        st.caption(f"{muestra['Gramos']:.0f} g")
        else:
            st.info("No se encontraron colores de filamento.")

        df_materiales = pd.DataFrame(resultado["filamentos"])
        materiales_editados = st.data_editor(
            df_materiales,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Material": st.column_config.TextColumn("Material"),
                "Gramos": st.column_config.NumberColumn(
                    "Gramos",
                    min_value=0.0,
                    step=1.0,
                    format="%.0f g",
                ),
            },
        )

        peso_total = materiales_editados["Gramos"].fillna(0).sum()

        c1, c2 = st.columns(2)
        with c1:
            st.metric("⚖️ Peso total", f"{peso_total:.0f} g")
        with c2:
            st.metric("⏱️ Tiempo", f"{tiempo_editado:.1f} h")

        costo_material = peso_total / 1000 * precio_filamento_kg
        costo_electricidad = (
            tiempo_editado * consumo_impresora_w / 1000 * precio_kwh
        )
        costo_depreciacion = (
            tiempo_editado * precio_impresora / vida_util_horas
        )
        costo_total = costo_material + costo_electricidad + costo_depreciacion

        st.divider()
        st.write("## 💰 Costos de impresión")

        a, b, c, d = st.columns(4)
        with a:
            st.metric("🧵 Material", formatear_clp(costo_material))
        with b:
            st.metric("⚡ Electricidad", formatear_clp(costo_electricidad))
        with c:
            st.metric("🖨️ Depreciación", formatear_clp(costo_depreciacion))
        with d:
            st.metric("💰 Costo total", formatear_clp(costo_total))

        ganancia = 0
        if destino_actual == "Venta":
            ganancia = precio_venta_actual - costo_total
            st.metric("📈 Ganancia estimada", formatear_clp(ganancia))

        st.divider()
        fecha_impresion = st.date_input(
            "Fecha",
            value=date.today(),
            format="DD/MM/YYYY",
        )

        if st.button("💾 Guardar impresión", type="primary"):
            materiales_json = json.dumps(
                materiales_editados.fillna("").to_dict(orient="records"),
                ensure_ascii=False,
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
                ganancia,
            )

            st.session_state["mensaje"] = (
                f"Impresión guardada para {destino_actual} ✅"
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

    periodo = st.selectbox(
        "Periodo",
        ["Este mes", "Mes pasado", "Últimos 30 días", "Todo", "Personalizado"],
    )

    hoy = date.today()
    fecha_inicio = None
    fecha_fin = None

    if periodo == "Este mes":
        fecha_inicio = date(hoy.year, hoy.month, 1)
        fecha_fin = hoy
    elif periodo == "Mes pasado":
        primer_dia_mes = date(hoy.year, hoy.month, 1)
        ultimo_dia_anterior = primer_dia_mes - timedelta(days=1)
        fecha_inicio = date(
            ultimo_dia_anterior.year,
            ultimo_dia_anterior.month,
            1,
        )
        fecha_fin = ultimo_dia_anterior
    elif periodo == "Últimos 30 días":
        fecha_inicio = hoy - timedelta(days=29)
        fecha_fin = hoy
    elif periodo == "Personalizado":
        p1, p2 = st.columns(2)
        with p1:
            fecha_inicio = st.date_input(
                "Desde",
                value=hoy.replace(day=1),
                format="DD/MM/YYYY",
            )
        with p2:
            fecha_fin = st.date_input(
                "Hasta",
                value=hoy,
                format="DD/MM/YYYY",
            )

    impresiones_filtradas = impresiones.copy()
    pagos_filtrados = pagos.copy()

    if fecha_inicio is not None and fecha_fin is not None:
        if not impresiones_filtradas.empty:
            impresiones_filtradas = impresiones_filtradas[
                (impresiones_filtradas["fecha"].dt.date >= fecha_inicio)
                & (impresiones_filtradas["fecha"].dt.date <= fecha_fin)
            ]
        if not pagos_filtrados.empty:
            pagos_filtrados = pagos_filtrados[
                (pagos_filtrados["fecha"].dt.date >= fecha_inicio)
                & (pagos_filtrados["fecha"].dt.date <= fecha_fin)
            ]

    resumen = []
    for persona in PERSONAS:
        consumido = 0
        pagado = 0

        if not impresiones_filtradas.empty:
            consumido = impresiones_filtradas[
                impresiones_filtradas["persona"] == persona
            ]["costo_total"].sum()

        if not pagos_filtrados.empty:
            pagado = pagos_filtrados[pagos_filtrados["persona"] == persona][
                "monto"
            ].sum()

        saldo = consumido - pagado
        resumen.append(
            {
                "Persona": persona,
                "Consumido": consumido,
                "Pagado": pagado,
                "Saldo": saldo,
            }
        )

    df_resumen = pd.DataFrame(resumen)

    st.write("### 👥 Cuenta de cada uno")
    columnas = st.columns(len(PERSONAS))

    for i, persona in enumerate(PERSONAS):
        fila = df_resumen[df_resumen["Persona"] == persona].iloc[0]
        saldo = fila["Saldo"]

        with columnas[i]:
            st.write(f"### {persona}")
            st.metric("Consumido", formatear_clp(fila["Consumido"]))
            st.metric("Pagado", formatear_clp(fila["Pagado"]))

            if saldo > 0:
                st.error("Debe " + formatear_clp(saldo))
            elif saldo < 0:
                st.success("A favor " + formatear_clp(abs(saldo)))
            else:
                st.success("Al día ✅")

    # -----------------------------------------------------
    # GRÁFICO SUPERPUESTO: COSTO AZUL + PAGO VERDE
    # -----------------------------------------------------

    st.write("### 📊 Costo vs pagos")
    st.caption(
        "El pago verde se superpone al costo azul: la parte azul visible es lo que falta por cubrir."
    )

    df_grafico = df_resumen.copy()
    df_grafico["Maximo"] = df_grafico[["Consumido", "Pagado"]].max(axis=1)
    df_grafico["SaldoTexto"] = df_grafico["Saldo"].apply(
        lambda x: (
            "Debe " + formatear_clp(x)
            if x > 0
            else ("A favor " + formatear_clp(abs(x)) if x < 0 else "Al día")
        )
    )

    base = alt.Chart(df_grafico).encode(
        x=alt.X("Persona:N", sort=PERSONAS, title=None),
    )

    barra_costo = base.mark_bar(
        size=64,
        color=AZUL,
        opacity=0.72,
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5,
    ).encode(
        y=alt.Y("Consumido:Q", title="Monto ($)"),
        tooltip=[
            alt.Tooltip("Persona:N", title="Persona"),
            alt.Tooltip("Consumido:Q", title="Costo", format=",.0f"),
            alt.Tooltip("Pagado:Q", title="Pagado", format=",.0f"),
            alt.Tooltip("SaldoTexto:N", title="Saldo"),
        ],
    )

    barra_pago = base.mark_bar(
        size=38,
        color=VERDE,
        opacity=0.95,
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5,
    ).encode(
        y=alt.Y("Pagado:Q", title="Monto ($)"),
        tooltip=[
            alt.Tooltip("Persona:N", title="Persona"),
            alt.Tooltip("Consumido:Q", title="Costo", format=",.0f"),
            alt.Tooltip("Pagado:Q", title="Pagado", format=",.0f"),
            alt.Tooltip("SaldoTexto:N", title="Saldo"),
        ],
    )

    etiqueta_saldo = base.mark_text(
        dy=-10,
        fontSize=12,
        fontWeight="bold",
        color="white",
    ).encode(
        y=alt.Y("Maximo:Q"),
        text=alt.Text("SaldoTexto:N"),
    )

    grafico = (
        (barra_costo + barra_pago + etiqueta_saldo)
        .properties(height=350)
        .configure_axis(
            labelColor="white",
            titleColor="white",
            gridColor="#374151",
            domainColor="#6B7280",
            tickColor="#6B7280",
        )
        .configure_legend(
            labelColor="white",
            titleColor="white",
        )
    )

    st.altair_chart(grafico, use_container_width=True)

    st.write("### 🛍️ Ventas")

    if not impresiones_filtradas.empty:
        ventas = impresiones_filtradas[
            impresiones_filtradas["persona"] == "Venta"
        ]
    else:
        ventas = pd.DataFrame()

    total_ventas = 0
    costo_ventas = 0
    ganancia_ventas = 0
    cantidad_ventas = 0

    if not ventas.empty:
        total_ventas = ventas["precio_venta"].sum()
        costo_ventas = ventas["costo_total"].sum()
        ganancia_ventas = ventas["ganancia"].sum()
        cantidad_ventas = len(ventas)

    v1, v2, v3, v4 = st.columns(4)
    with v1:
        st.metric("Ventas", cantidad_ventas)
    with v2:
        st.metric("Ingresos", formatear_clp(total_ventas))
    with v3:
        st.metric("Costo", formatear_clp(costo_ventas))
    with v4:
        st.metric("Ganancia", formatear_clp(ganancia_ventas))


# =========================================================
# REGISTRAR PAGO
# =========================================================

with tab_pago:
    st.subheader("💳 Registrar pago")

    if "persona_pago" not in st.session_state:
        st.session_state["persona_pago"] = "Feña"

    bloque_personas, bloque_monto, bloque_fecha = st.columns([5, 1.6, 2])

    with bloque_personas:
        st.write("**¿Quién pagó?**")
        botones_pago = st.columns(5)
        for columna, persona in zip(botones_pago, PERSONAS):
            with columna:
                st.button(
                    persona,
                    type=(
                        "primary"
                        if st.session_state["persona_pago"] == persona
                        else "secondary"
                    ),
                    use_container_width=True,
                    key=f"pago_persona_{persona}",
                    on_click=seleccionar_persona_pago,
                    args=(persona,),
                )

    with bloque_monto:
        monto_pago = st.number_input(
            "Monto ($)",
            min_value=0,
            value=0,
            step=1000,
            key="monto_pago",
        )

    with bloque_fecha:
        fecha_pago = st.date_input(
            "Fecha",
            value=date.today(),
            format="DD/MM/YYYY",
            key="fecha_pago",
        )

    persona_pago = st.session_state["persona_pago"]

    nota_pago = st.text_input(
        "Nota",
        placeholder="Ej: transferencia septiembre",
    )

    if st.button("Registrar pago", type="primary"):
        if monto_pago <= 0:
            st.error("El monto debe ser mayor a $0.")
        else:
            guardar_pago(
                fecha_pago.isoformat(),
                persona_pago,
                monto_pago,
                nota_pago,
            )
            st.success(
                f"Pago de {formatear_clp(monto_pago)} registrado para {persona_pago} ✅"
            )


# =========================================================
# HISTORIAL
# =========================================================

with tab_historial:
    st.subheader("📋 Historial")

    impresiones = cargar_impresiones()
    pagos = cargar_pagos()

    hist1, hist2 = st.tabs(["🖨️ Impresiones", "💳 Pagos"])

    with hist1:
        if impresiones.empty:
            st.info("Todavía no hay impresiones guardadas.")
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
                    "ganancia",
                ]
            ].copy()

            tabla_impresiones["fecha"] = tabla_impresiones["fecha"].dt.strftime(
                "%d/%m/%Y"
            )
            tabla_impresiones["costo_total"] = tabla_impresiones[
                "costo_total"
            ].apply(formatear_clp)
            tabla_impresiones["precio_venta"] = tabla_impresiones[
                "precio_venta"
            ].apply(formatear_clp)
            tabla_impresiones["ganancia"] = tabla_impresiones["ganancia"].apply(
                formatear_clp
            )

            tabla_impresiones.columns = [
                "ID",
                "Fecha",
                "Persona",
                "Modelo",
                "Horas",
                "Gramos",
                "Costo",
                "Precio venta",
                "Ganancia",
            ]

            st.dataframe(
                tabla_impresiones,
                use_container_width=True,
                hide_index=True,
            )

            st.divider()
            st.write("### ✏️ Editar impresión")

            opciones_impresiones = {
                f"ID {fila['id']} | {fila['persona']} | {fila['modelo']}": int(
                    fila["id"]
                )
                for _, fila in impresiones.iterrows()
            }

            seleccion_impresion = st.selectbox(
                "Selecciona un registro",
                list(opciones_impresiones.keys()),
                key="editar_impresion_select",
            )
            id_impresion = opciones_impresiones[seleccion_impresion]
            registro = impresiones[impresiones["id"] == id_impresion].iloc[0]

            e1, e2 = st.columns(2)

            with e1:
                editar_fecha = st.date_input(
                    "Fecha",
                    value=registro["fecha"].date(),
                    format="DD/MM/YYYY",
                    key=f"editar_imp_fecha_{id_impresion}",
                )
                editar_persona = st.selectbox(
                    "Persona",
                    DESTINOS,
                    index=DESTINOS.index(registro["persona"]),
                    key=f"editar_imp_persona_{id_impresion}",
                )
                editar_modelo = st.text_input(
                    "Modelo",
                    value=str(registro["modelo"]),
                    key=f"editar_imp_modelo_{id_impresion}",
                )
                editar_horas = st.number_input(
                    "Horas",
                    min_value=0.0,
                    value=numero_seguro(registro["horas"]),
                    step=0.1,
                    key=f"editar_imp_horas_{id_impresion}",
                )

            with e2:
                editar_gramos = st.number_input(
                    "Gramos",
                    min_value=0.0,
                    value=numero_seguro(registro["gramos"]),
                    step=1.0,
                    key=f"editar_imp_gramos_{id_impresion}",
                )
                editar_costo = st.number_input(
                    "Costo total ($)",
                    min_value=0.0,
                    value=numero_seguro(registro["costo_total"]),
                    step=100.0,
                    key=f"editar_imp_costo_{id_impresion}",
                )
                editar_precio_venta = st.number_input(
                    "Precio venta ($)",
                    min_value=0.0,
                    value=numero_seguro(registro["precio_venta"]),
                    step=1000.0,
                    key=f"editar_imp_venta_{id_impresion}",
                )
                editar_ganancia = st.number_input(
                    "Ganancia ($)",
                    value=numero_seguro(registro["ganancia"]),
                    step=100.0,
                    key=f"editar_imp_ganancia_{id_impresion}",
                )

            guardar_col, eliminar_col = st.columns(2)

            with guardar_col:
                if st.button(
                    "💾 Guardar cambios",
                    type="primary",
                    use_container_width=True,
                    key=f"guardar_imp_{id_impresion}",
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
                        editar_ganancia,
                    )
                    st.session_state["mensaje"] = "Impresión actualizada ✅"
                    st.rerun()

            with eliminar_col:
                confirmar_eliminar_imp = st.checkbox(
                    "Confirmo que quiero eliminarla",
                    key=f"confirmar_eliminar_imp_{id_impresion}",
                )
                if st.button(
                    "🗑️ Eliminar impresión",
                    use_container_width=True,
                    disabled=not confirmar_eliminar_imp,
                    key=f"eliminar_imp_{id_impresion}",
                ):
                    eliminar_impresion(id_impresion)
                    st.session_state["mensaje"] = "Impresión eliminada 🗑️"
                    st.rerun()

    with hist2:
        if pagos.empty:
            st.info("Todavía no hay pagos registrados.")
        else:
            tabla_pagos = pagos[["id", "fecha", "persona", "monto", "nota"]].copy()
            tabla_pagos["fecha"] = tabla_pagos["fecha"].dt.strftime("%d/%m/%Y")
            tabla_pagos["monto"] = tabla_pagos["monto"].apply(formatear_clp)
            tabla_pagos.columns = ["ID", "Fecha", "Persona", "Monto", "Nota"]

            st.dataframe(
                tabla_pagos,
                use_container_width=True,
                hide_index=True,
            )

            st.divider()
            st.write("### ✏️ Editar pago")

            opciones_pagos = {
                f"ID {fila['id']} | {fila['persona']} | {formatear_clp(fila['monto'])}": int(
                    fila["id"]
                )
                for _, fila in pagos.iterrows()
            }

            seleccion_pago = st.selectbox(
                "Selecciona un pago",
                list(opciones_pagos.keys()),
                key="editar_pago_select",
            )
            id_pago = opciones_pagos[seleccion_pago]
            registro_pago = pagos[pagos["id"] == id_pago].iloc[0]

            p1, p2 = st.columns(2)

            with p1:
                editar_fecha_pago = st.date_input(
                    "Fecha",
                    value=registro_pago["fecha"].date(),
                    format="DD/MM/YYYY",
                    key=f"editar_pago_fecha_{id_pago}",
                )
                editar_persona_pago = st.selectbox(
                    "Persona",
                    PERSONAS,
                    index=PERSONAS.index(registro_pago["persona"]),
                    key=f"editar_pago_persona_{id_pago}",
                )

            with p2:
                editar_monto_pago = st.number_input(
                    "Monto ($)",
                    min_value=0.0,
                    value=numero_seguro(registro_pago["monto"]),
                    step=1000.0,
                    key=f"editar_pago_monto_{id_pago}",
                )
                nota_actual = (
                    ""
                    if pd.isna(registro_pago["nota"])
                    else str(registro_pago["nota"])
                )
                editar_nota_pago = st.text_input(
                    "Nota",
                    value=nota_actual,
                    key=f"editar_pago_nota_{id_pago}",
                )

            pago_guardar_col, pago_eliminar_col = st.columns(2)

            with pago_guardar_col:
                if st.button(
                    "💾 Guardar cambios del pago",
                    type="primary",
                    use_container_width=True,
                    key=f"guardar_pago_{id_pago}",
                ):
                    actualizar_pago(
                        id_pago,
                        editar_fecha_pago.isoformat(),
                        editar_persona_pago,
                        editar_monto_pago,
                        editar_nota_pago,
                    )
                    st.session_state["mensaje"] = "Pago actualizado ✅"
                    st.rerun()

            with pago_eliminar_col:
                confirmar_eliminar_pago = st.checkbox(
                    "Confirmo que quiero eliminarlo",
                    key=f"confirmar_eliminar_pago_{id_pago}",
                )
                if st.button(
                    "🗑️ Eliminar pago",
                    use_container_width=True,
                    disabled=not confirmar_eliminar_pago,
                    key=f"eliminar_pago_{id_pago}",
                ):
                    eliminar_pago(id_pago)
                    st.session_state["mensaje"] = "Pago eliminado 🗑️"
                    st.rerun()
