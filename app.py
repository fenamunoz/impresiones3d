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
