import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import requests
from io import BytesIO
import io
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from plotly import graph_objects as go
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import streamlit.components.v1 as components
import unicodedata
import re

st.set_page_config(
    page_title="Control de Presupuesto",
    page_icon="🚚", #buscar un icono
    layout="wide"   
)

logo_url = "https://esgari.com.mx/wp-content/uploads/2023/07/logo_esgari_azul.png?v=1"

st.markdown(
    f"""
    <div style="text-align:center;">
        <img src="{logo_url}" width="400">
    </div>
    """,
    unsafe_allow_html=True
)

def init_session_state():
    defaults = {
        "logged_in": False,
        "username": "",
        "rol": "",
        "proyectos": [],
        "cecos": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def ct(texto):
    st.markdown(f"<h1 style='text-align: center;'>{texto}</h1>", unsafe_allow_html=True)


base_ppt = st.secrets["urls"]["presupuesto"]
Usuarios_url = st.secrets["urls"]["usuarios"]
basereal = st.secrets["urls"]["base_2025"]
mapeo_ppt_url = st.secrets["urls"]["mapeo"]
proyectos_url = st.secrets["urls"]["proyectos"]
cecos_url = st.secrets["urls"]["cecos"]
base_2026 = st.secrets["urls"]["base_ppt"]


meses = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
categorias_felx_com = ['COSTO DE PERSONAL', 'GASTO DE PERSONAL', 'NOMINA ADMINISTRATIVOS']

@st.cache_data
def cargar_datos(url):
    response = requests.get(url)
    response.raise_for_status()
    archivo_excel = BytesIO(response.content)
    return pd.read_excel(archivo_excel, engine="openpyxl")

def validar_credenciales(df, username, password):
    usuario_row = df[(df["usuario"] == username) & (df["contraseña"] == password)]
    if not usuario_row.empty:
        fila = usuario_row.iloc[0]
        proyectos = [p.strip() for p in str(fila["proyectos"]).split(",")]
        cecos = [c.strip() for c in str(fila["cecos"]).split(",")]
        return fila["usuario"], fila["rol"], proyectos, cecos
    return None, None, None, None

def filtro_pro(col):
    proyectos_local = proyectos.copy()
    proyectos_local["proyectos"] = proyectos_local["proyectos"].astype(str).str.strip()
    proyectos_local["nombre"] = proyectos_local["nombre"].astype(str).str.strip()
    allowed = [str(x).strip() for x in st.session_state.get("proyectos", [])]
    if allowed == ["ESGARI"]:
        df_visibles = proyectos_local.copy()
        opciones = ["ESGARI"] + df_visibles["nombre"].dropna().tolist()
        proyecto_nombre = col.selectbox("Selecciona un proyecto", opciones)

        if proyecto_nombre == "ESGARI":
            proyecto_codigo = df_visibles["proyectos"].tolist()  # todos
        else:
            proyecto_codigo = df_visibles.loc[df_visibles["nombre"] == proyecto_nombre, "proyectos"].tolist()

    else:
        df_visibles = proyectos_local[proyectos_local["proyectos"].isin(allowed)].copy()
        if df_visibles.empty:
            st.error("No hay proyectos visibles para este usuario. Revisa st.session_state['proyectos'] vs catálogo 'proyectos'.")
            st.stop()
        nombres_visibles = df_visibles["nombre"].dropna().unique().tolist()
        proyecto_nombre = col.selectbox("Selecciona un proyecto", nombres_visibles)
        proyecto_codigo = df_visibles.loc[df_visibles["nombre"] == proyecto_nombre, "proyectos"].astype(str).tolist()
    if not proyecto_codigo:
        st.error("No se encontró código para el proyecto seleccionado. Revisa duplicados o nombres en el catálogo.")
        st.stop()

    return proyecto_codigo, proyecto_nombre


def filtro_meses(col, df_ppt):
    meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.",
                       "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

    meses_disponibles = [m for m in meses_ordenados if m in df_ppt["Mes_A"].unique()]

    if selected == "PPT MENSUAL":
        mes = col.selectbox("Selecciona un mes", meses_disponibles)
        return [mes]

    elif selected == "Ingresos":
        mes_corte = meses_disponibles[-1] if meses_disponibles else None

        return col.multiselect(
            "Selecciona meses (corte)",
            meses_disponibles,
            default=[mes_corte] if mes_corte else []
        )

    else:
        return col.multiselect(
            "Selecciona un mes",
            meses_disponibles,
            default=[meses_disponibles[0]] if meses_disponibles else []
        )


def porcentaje_ingresos(df, meses, pro, codigo_pro):
    if pro == "ESGARI":
        por_ingre = 1
    else:
        df_mes = df[df["Mes_A"].isin(meses)]
        df_ingresos = df_mes[df_mes["Categoria_A"] == "INGRESO"]

        ingreso_total = df_ingresos["Neto_A"].sum()

        df_pro = df_ingresos[df_ingresos["Proyecto_A"].isin(codigo_pro)]
        ingreso_proyecto = df_pro["Neto_A"].sum()

        por_ingre = ingreso_proyecto / ingreso_total if ingreso_total != 0 else 0

    return por_ingre

def ingreso (df, meses, codigo_pro, pro):
    if pro == "ESGARI":
        df_mes = df[df['Mes_A'].isin(meses)]
        df_ingresos = df_mes[df_mes['Categoria_A'] == 'INGRESO']
        ingreso_pro = df_ingresos['Neto_A'].sum()
    else:
        df_mes = df[df['Mes_A'].isin(meses)]
        df_pro = df_mes[df_mes['Proyecto_A'].isin(codigo_pro)]
        df_ingresos = df_pro[df_pro['Categoria_A'] == 'INGRESO']
        ingreso_pro = df_ingresos['Neto_A'].sum()
    return ingreso_pro

def coss(df, meses, codigo_pro, pro, lista_proyectos):
    pat_oh = ["8002", "8003", "8004"]
    if pro == "ESGARI":

        df = df[~df['Proyecto_A'].isin(pat_oh)]
        df_mes = df[df['Mes_A'].isin(meses)]
        df_coss = df_mes[df_mes['Clasificacion_A'] == 'COSS']
        coss_pro = df_coss['Neto_A'].sum()
        mal_clasificados = 0
    
    else:
        df_mes = df[df['Mes_A'].isin(meses)]
        df_pro = df_mes[df_mes['Proyecto_A'].isin(codigo_pro)]
        df_coss = df_pro[df_pro['Clasificacion_A'] == 'COSS']
        coss_pro = df_coss['Neto_A'].sum()
        for x in meses:
            por_ingresos = porcentaje_ingresos(df, [x], pro, codigo_pro)
            df_mes_x = df[df["Mes_A"] == x]
            mal_clasificados = df_mes_x[~df_mes_x["Proyecto_A"].isin(lista_proyectos)]
            mal_clasificados = mal_clasificados[mal_clasificados["Clasificacion_A"].isin(["COSS"])]["Neto_A"].sum() * por_ingresos
            coss_pro += mal_clasificados
    return coss_pro, mal_clasificados

def patio(df, meses, codigo_pro, proyecto_nombre):
    df['Proyecto_A'] = df['Proyecto_A'].astype(str)
    patio_t = 0
    for x in meses:
        proyectos_patio = ["3201", "3002", "1003", "2003"]

        df_mes = df[df['Mes_A'].isin([x])]

        if proyecto_nombre == "ESGARI":
            df_patio = df_mes[df_mes['Proyecto_A'] == "8003"]
            df_patio = df_patio[df_patio['Clasificacion_A'].isin(['COSS', 'G.ADMN'])]
            patio_t += df_patio['Neto_A'].sum()
        
        elif any(pro in proyectos_patio for pro in codigo_pro):
            df_patio = df_mes[df_mes['Proyecto_A'] == "8003"]
            df_patio = df_patio[df_patio['Clasificacion_A'].isin(['COSS', 'G.ADMN'])]
            patio = df_patio['Neto_A'].sum()

            ingre_pat = df_mes[df_mes['Proyecto_A'].isin(proyectos_patio)]
            ingre_pat = ingre_pat[ingre_pat['Clasificacion_A'] == 'INGRESO']
            ingre_pat = ingre_pat['Neto_A'].sum()

            ingreso_pro = ingreso(df, [x], codigo_pro, proyecto_nombre)
            por_patio = ingreso_pro / ingre_pat if ingre_pat != 0 else 0
            patio_t += por_patio * patio
        else:
            patio_t += 0
    return patio_t

def gadmn(df, meses, codigo_pro, pro, lista_proyectos):
    pat_oh = ["8002", "8003", "8004"]
    if pro == "ESGARI":
        df = df[~df['Proyecto_A'].isin(pat_oh)]
        df_mes = df[df['Mes_A'].isin(meses)]
        df_gadmn = df_mes[df_mes['Clasificacion_A'] == 'G.ADMN']
        gadmn_pro = df_gadmn['Neto_A'].sum()
        mal_clasificados = 0
    elif pro == "FLEX DEDICADO":
        df = df[~df['Proyecto_A'].isin(pat_oh)]
        df_mes = df[df['Mes_A'].isin(meses)]
        df_pro = df_mes[df_mes['Proyecto_A'].isin(codigo_pro)]
        df_gadmn = df_pro[df_pro['Clasificacion_A'] == 'G.ADMN']
        gadmn_pro = df_gadmn['Neto_A'].sum()
        gadmn_flexs = df_pro[df_pro['Categoria_A'].isin(categorias_felx_com)]['Neto_A'].sum()*.15
        gadmn_pro = gadmn_pro - gadmn_flexs
        mal_clasificados = 0
        for x in meses:
            por_ingresos = porcentaje_ingresos(df, [x], pro, codigo_pro)
            df_mes_x = df[df["Mes_A"] == x]
            mal_clas = df_mes_x[~df_mes_x["Proyecto_A"].isin(lista_proyectos)]
            mal_clas = mal_clas[mal_clas["Clasificacion_A"].isin(["G.ADMN"])]["Neto_A"].sum() * por_ingresos
            gadmn_pro += mal_clas
            mal_clasificados += mal_clas
    elif pro == "FLEX SPOT":
        df = df[~df['Proyecto_A'].isin(pat_oh)]
        df_mes = df[df['Mes_A'].isin(meses)]
        df_pro = df_mes[df_mes['Proyecto_A'].isin(codigo_pro)]
        df_gadmn = df_pro[df_pro['Clasificacion_A'] == 'G.ADMN']
        gadmn_pro = df_gadmn['Neto_A'].sum()
        df_pro_flexd = df_mes[df_mes['Proyecto_A'].isin(["2001"])]
        gadmn_flexd = df_pro_flexd[df_pro_flexd['Categoria_A'].isin(categorias_felx_com)]['Neto_A'].sum() * .15
        gadmn_pro = gadmn_pro + gadmn_flexd
        mal_clasificados = 0
        for x in meses:
            por_ingresos = porcentaje_ingresos(df, [x], pro, codigo_pro)
            df_mes_x = df[df["Mes_A"] == x]
            mal_clas = df_mes_x[~df_mes_x["Proyecto_A"].isin(lista_proyectos)]
            mal_clas = mal_clas[mal_clas["Clasificacion_A"].isin(["G.ADMN"])]["Neto_A"].sum() * por_ingresos
            gadmn_pro += mal_clas
            mal_clasificados += mal_clas
    else:
        df_mes = df[df['Mes_A'].isin(meses)]
        df_pro = df_mes[df_mes['Proyecto_A'].isin(codigo_pro)]
        df_gadmn = df_pro[df_pro['Clasificacion_A'] == 'G.ADMN']
        gadmn_pro = df_gadmn['Neto_A'].sum()
        mal_clasificados = 0
        for x in meses:
            por_ingresos = porcentaje_ingresos(df, [x], pro, codigo_pro)
            df_mes_x = df[df["Mes_A"] == x]
            mal_clas = df_mes_x[~df_mes_x["Proyecto_A"].isin(lista_proyectos)]
            mal_clas = mal_clas[mal_clas["Clasificacion_A"].isin(["G.ADMN"])]["Neto_A"].sum() * por_ingresos
            gadmn_pro += mal_clas
            mal_clasificados += mal_clas
    return gadmn_pro, mal_clasificados

def oh(df, meses, codigo_pro, nombre_proyecto):
    oh_pro = 0
    for x in meses:
        oh = ["8002", "8004"]
        df_mes = df[df['Mes_A'].isin([x])]
        por_ingre = porcentaje_ingresos(df, [x], nombre_proyecto, codigo_pro)
        df_oh = df_mes[df_mes['Proyecto_A'].isin(oh)]
        df_oh = df_oh[df_oh['Clasificacion_A'].isin(['COSS', 'G.ADMN'])]
        oh_coss = df_oh['Neto_A'].sum()
        oh_pro += oh_coss * por_ingre
    return oh_pro

def gasto_fin (df, meses, codigo_pro, pro, lista_proyectos):
    if pro == "ESGARI":
        df_mes = df[df['Mes_A'].isin(meses)]
        df_gasto_fin = df_mes[df_mes['Clasificacion_A'] == 'GASTOS FINANCIEROS']
        gasto_fin = df_gasto_fin['Neto_A'].sum()
        mal_clasificados = 0
        oh_gasto_fin = 0
    else:
        df_mes = df[df['Mes_A'].isin(meses)]
        df_pro = df_mes[df_mes['Proyecto_A'].isin(codigo_pro)]
        df_gasto_fin = df_pro[df_pro['Clasificacion_A'] == 'GASTOS FINANCIEROS']
        gasto_fin = df_gasto_fin['Neto_A'].sum()
        for x in meses:
            por_ingresos = porcentaje_ingresos(df, [x], pro, codigo_pro)
            df_mes_x = df[df["Mes_A"] == x]
            mal_clasificados = df_mes_x[~df_mes_x["Proyecto_A"].isin(lista_proyectos)]
            mal_clasificados = mal_clasificados[mal_clasificados["Clasificacion_A"].isin(["GASTOS FINANCIEROS"])]["Neto_A"].sum() * por_ingresos
            gasto_fin += mal_clasificados
            oh_gasto_fin = df_mes_x[df_mes_x['Proyecto_A'].isin(["8002", "8003","8004"])]
            oh_gasto_fin = oh_gasto_fin[oh_gasto_fin['Clasificacion_A'].isin(["GASTOS FINANCIEROS"])]
            oh_gasto_fin = oh_gasto_fin['Neto_A'].sum() * por_ingresos
            gasto_fin += oh_gasto_fin

    return gasto_fin, mal_clasificados, oh_gasto_fin

def ingreso_fin (df, meses, codigo_pro, pro, lista_proyectos):
    ing_fin_cat = ["INGRESO POR REVALUACION CAMBIARIA", "INGRESO POR FACTORAJE", "INGRESOS POR INTERESES"]
    if pro == "ESGARI":
        df_mes = df[df['Mes_A'].isin(meses)]
        df_ingreso_fin = df_mes[df_mes['Categoria_A'].isin(ing_fin_cat)]
        ingreso_fin = df_ingreso_fin['Neto_A'].sum()
        mal_clasificados = 0
        oh_ingreso_fin = 0
    else:
        df_mes = df[df['Mes_A'].isin(meses)]
        df_pro = df_mes[df_mes['Proyecto_A'].isin(codigo_pro)]
        df_ingreso_fin = df_pro[df_pro['Categoria_A'].isin(ing_fin_cat)]
        ingreso_fin = df_ingreso_fin['Neto_A'].sum()
        for x in meses:
            por_ingresos = porcentaje_ingresos(df, [x], pro, codigo_pro)
            df_mes_x = df[df["Mes_A"] == x]
            mal_clasificados = df_mes_x[~df_mes_x["Proyecto_A"].isin(lista_proyectos)]
            mal_clasificados = mal_clasificados[mal_clasificados["Categoria_A"].isin(ing_fin_cat)]["Neto_A"].sum() * por_ingresos
            ingreso_fin += mal_clasificados
            oh_ingreso_fin = df_mes_x[df_mes_x['Proyecto_A'].isin(["8002", "8003", "8004"])]
            oh_ingreso_fin = oh_ingreso_fin[oh_ingreso_fin['Categoria_A'].isin(ing_fin_cat)]
            oh_ingreso_fin = oh_ingreso_fin['Neto_A'].sum() * por_ingresos
            ingreso_fin += oh_ingreso_fin


    return ingreso_fin, mal_clasificados, oh_ingreso_fin

def estado_resultado(df_ppt, meses_seleccionado, proyecto_nombre, proyecto_codigo, lista_proyectos):
    estado_resultado = {}

    por_ingre = porcentaje_ingresos(df_ppt, meses_seleccionado, proyecto_nombre, proyecto_codigo)
    ingreso_proyecto = ingreso(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre)
    coss_pro, mal_coss = coss(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre, lista_proyectos)
    patio_pro = patio(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre)
    por_patio = patio_pro / ingreso_proyecto if ingreso_proyecto != 0 else 0
    coss_total = coss_pro + patio_pro
    por_coss = coss_total / ingreso_proyecto if ingreso_proyecto != 0 else 0
    utilidad_bruta = ingreso_proyecto - coss_total
    por_ub = utilidad_bruta / ingreso_proyecto if ingreso_proyecto != 0 else 0
    gadmn_pro, mal_gadmn = gadmn(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre, lista_proyectos)
    por_gadmn = gadmn_pro / ingreso_proyecto if ingreso_proyecto != 0 else 0
    utilidad_operativa = utilidad_bruta - gadmn_pro
    por_utilidad_operativa = utilidad_operativa / ingreso_proyecto if ingreso_proyecto != 0 else 0
    oh_pro = oh(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre)
    por_oh = oh_pro / ingreso_proyecto if ingreso_proyecto != 0 else 0
    ebit = utilidad_operativa - oh_pro
    por_ebit = ebit / ingreso_proyecto if ingreso_proyecto != 0 else 0
    gasto_fin_pro, mal_gfin, oh_pro_gfin = gasto_fin(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre, lista_proyectos)
    por_gasto_fin = gasto_fin_pro / ingreso_proyecto if ingreso_proyecto != 0 else 0
    ingreso_fin_pro, mal_ifin, oh_pro_ifin = ingreso_fin(df_ppt, meses_seleccionado, proyecto_codigo, proyecto_nombre, lista_proyectos)
    por_ingreso_fin = ingreso_fin_pro / ingreso_proyecto if ingreso_proyecto != 0 else 0
    resultado_fin = gasto_fin_pro - ingreso_fin_pro
    por_resultado_fin = resultado_fin / ingreso_proyecto if ingreso_proyecto != 0 else 0
    ebt = ebit - resultado_fin
    por_ebt = ebt / ingreso_proyecto if ingreso_proyecto != 0 else 0

    estado_resultado.update({
        'porcentaje_ingresos': por_ingre,
        'ingreso_proyecto': ingreso_proyecto,
        'coss_pro': coss_pro,
        'mal_coss': mal_coss,
        'patio_pro': patio_pro,
        'por_patio': por_patio,
        'coss_total': coss_total,
        'por_coss': por_coss,
        'utilidad_bruta': utilidad_bruta,
        'por_utilidad_bruta': por_ub,
        'gadmn_pro': gadmn_pro,
        'mal_gadmn': mal_gadmn,
        'por_gadmn': por_gadmn,
        'utilidad_operativa': utilidad_operativa,
        'por_utilidad_operativa': por_utilidad_operativa,
        'oh_pro': oh_pro,
        'por_oh': por_oh,
        'ebit': ebit,
        'por_ebit': por_ebit,
        'gasto_fin_pro': gasto_fin_pro,
        'mal_gfin': mal_gfin,
        'oh_pro_gfin': oh_pro_gfin,
        'por_gasto_fin': por_gasto_fin,
        'ingreso_fin_pro': ingreso_fin_pro,
        'por_ingreso_fin': por_ingreso_fin,
        'mal_ifin': mal_ifin,
        'oh_pro_ifin': oh_pro_ifin,
        'resultado_fin': resultado_fin,
        'por_resultado_fin': por_resultado_fin,
        'ebt': ebt,
        'por_ebt': por_ebt
    })

    return estado_resultado


def filtro_ceco(col):
    df_cecos = cargar_datos(cecos_url)
    df_cecos["ceco"] = df_cecos["ceco"].astype(str).str.strip()
    df_cecos["nombre"] = df_cecos["nombre"].astype(str).str.strip()

    allowed = [str(x).strip() for x in st.session_state.get("cecos", [])]
    if allowed == ["ESGARI"]:
        opciones = ["ESGARI"] + df_cecos["nombre"].dropna().unique().tolist()
        ceco_nombre = col.selectbox("Selecciona un ceco", opciones)

        if ceco_nombre == "ESGARI":
            ceco_codigo = df_cecos["ceco"].dropna().unique().tolist()
        else:
            ceco_codigo = df_cecos.loc[df_cecos["nombre"] == ceco_nombre, "ceco"].dropna().unique().tolist()

        return ceco_codigo, ceco_nombre
    df_visibles = df_cecos[df_cecos["ceco"].isin(allowed)].copy()
    if df_visibles.empty:
        col.error("No tienes CeCos asignados o no coinciden con el catálogo.")
        return [], None
    nombre_a_codigo = dict(zip(df_visibles["nombre"], df_visibles["ceco"]))
    opciones = list(nombre_a_codigo.keys())
    ceco_nombre = col.selectbox("Selecciona un ceco", opciones)
    ceco_codigo = [nombre_a_codigo.get(ceco_nombre)] if ceco_nombre in nombre_a_codigo else []
    return ceco_codigo, ceco_nombre
    
def tabla_comparativa(df_agrid, df_ppt_actual, proyecto_codigo, meses_seleccionado, clasificacion, categoria, titulo):

    st.write(titulo)
    if not meses_seleccionado or not proyecto_codigo:
        st.info("Selecciona por lo menos un mes y un proyecto.")
        return None

    df_agrid = df_agrid.copy()
    df_ppt_actual = df_ppt_actual.copy()
    for df in (df_agrid, df_ppt_actual):
        df["Proyecto_A"] = df["Proyecto_A"].astype(str).str.strip()
        df["Mes_A"] = df["Mes_A"].astype(str).str.strip()
        df[clasificacion] = df[clasificacion].astype(str).str.strip()
        df["Categoria_A"] = df["Categoria_A"].astype(str).str.strip()
        df["Cuenta_Nombre_A"] = df["Cuenta_Nombre_A"].astype(str).str.strip()
        df["Neto_A"] = pd.to_numeric(df["Neto_A"], errors="coerce").fillna(0.0)

    proyecto_codigo = [str(x).strip() for x in proyecto_codigo]
    meses_sel = [str(x).strip() for x in meses_seleccionado]

    group_col = "Categoria_A"
    detalle_col = "Cuenta_Nombre_A"
    group_cols = [group_col, detalle_col]
    df_ppt = df_agrid[
        (df_agrid["Mes_A"].isin(meses_sel)) &
        (df_agrid["Proyecto_A"].isin(proyecto_codigo)) &
        (df_agrid[clasificacion] == categoria)
    ].copy()
    df_ppt = df_ppt.groupby(group_cols, as_index=False).agg(PPT=("Neto_A", "sum"))
    df_ytd = df_ppt_actual[
        (df_ppt_actual["Mes_A"].isin(meses_sel)) &
        (df_ppt_actual["Proyecto_A"].isin(proyecto_codigo)) &
        (df_ppt_actual[clasificacion] == categoria)
    ].copy()
    df_ytd = df_ytd.groupby(group_cols, as_index=False).agg(YTD=("Neto_A", "sum"))
    df_out = pd.merge(df_ppt, df_ytd, on=group_cols, how="outer").fillna(0.0)

    for c in ["PPT", "YTD"]:
        df_out[c] = pd.to_numeric(df_out[c], errors="coerce").fillna(0.0)
    df_out["Diferencia nominal"] = df_out["YTD"] - df_out["PPT"]
    df_out["Variación %"] = np.where(
        df_out["PPT"] != 0,
        ((df_out["YTD"] / df_out["PPT"]) - 1) * 100,
        0.0
    )

    for c in ["Variación %", "Diferencia nominal"]:
        df_out[c] = pd.to_numeric(df_out[c], errors="coerce").fillna(0.0)
    money_fmt = JsCode("""
        function(params){
            if (params.value === null || params.value === undefined) return '';
            return params.value.toLocaleString(
                'es-MX',
                { style: 'currency', currency: 'MXN', minimumFractionDigits: 2 }
            );
        }
    """)

    pct_fmt = JsCode("""
        function(params){
            if (params.value === null || params.value === undefined) return '';
            return params.value.toFixed(2) + ' %';
        }
    """)

    var_value_getter = JsCode("""
        function(params){
            // Group row
            if (params.node && params.node.group) {
                var agg = params.node.aggData || {};
                var ppt = agg.PPT || 0;
                var ytd = agg.YTD || 0;
                if (ppt === 0) return 0;
                return ((ytd / ppt) - 1) * 100;
            }
            // Leaf row
            return params.data ? params.data["Variación %"] : 0;
        }
    """)
    dif_value_getter = JsCode("""
        function(params){
            // Group row
            if (params.node && params.node.group) {
                var agg = params.node.aggData || {};
                var ppt = agg.PPT || 0;
                var ytd = agg.YTD || 0;
                return ytd - ppt;
            }
            // Leaf row
            return params.data ? params.data["Diferencia nominal"] : 0;
        }
    """)

    gb = GridOptionsBuilder.from_dataframe(df_out)
    gb.configure_default_column(resizable=True, sortable=True, filter=True)

    grid_options = gb.build()
    grid_options["columnDefs"] = [
        {"field": group_col, "rowGroup": True, "hide": True},
        {"field": detalle_col, "headerName": "Cuenta_Nombre_A", "minWidth": 320},
        {"field": "PPT", "headerName": "PPT", "type": ["numericColumn"],
         "aggFunc": "sum", "valueFormatter": money_fmt, "cellStyle": {"textAlign": "right"}},
        {"field": "YTD", "headerName": "YTD", "type": ["numericColumn"],
         "aggFunc": "sum", "valueFormatter": money_fmt, "cellStyle": {"textAlign": "right"}},
        {"field": "Diferencia nominal", "headerName": "Diferencia nominal", "type": ["numericColumn"],
         "valueGetter": dif_value_getter, "valueFormatter": money_fmt, "cellStyle": {"textAlign": "right"}},
        {"field": "Variación %", "headerName": "Variación %", "type": ["numericColumn"],
         "valueGetter": var_value_getter, "valueFormatter": pct_fmt, "cellStyle": {"textAlign": "right"}},
    ]
    grid_options["groupDisplayType"] = "singleColumn"
    grid_options["groupDefaultExpanded"] = 0
    grid_options["autoGroupColumnDef"] = {
        "headerName": "Group",
        "minWidth": 260,
        "pinned": "left",
        "cellRendererParams": {"suppressCount": False},
    }

    AgGrid(
        df_out,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        height=520,
        use_checkbox=False,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        key=f"agrid_{titulo}_{'-'.join(proyecto_codigo)}_{'-'.join(meses_sel)}_{categoria}"
    )

    return df_out
def seccion_analisis_especial_porcentual(
    df_ppt, df_real, ingreso,
    meses_seleccionado, proyecto_codigo, proyecto_nombre,
    funcion, nombre_funcion,
    cecos_seleccionados  # ✅ NUEVO
):
    with st.expander(f"{nombre_funcion.upper()}"):

        meses_completos = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        orden = {m: i for i, m in enumerate(meses_completos)}
        meses_sel = sorted(list(set(meses_seleccionado)), key=lambda x: orden.get(x, 999))

        if not meses_sel:
            st.error("Selecciona por lo menos un mes.")
            return

        proy = [str(x).strip() for x in proyecto_codigo]
        cecos_sel = [str(x).strip() for x in (cecos_seleccionados or [])]
        if not cecos_sel:
            st.error("Selecciona por lo menos un CeCo.")
            return

        df_ppt_sel = df_ppt[
            (df_ppt["Mes_A"].isin(meses_sel)) &
            (df_ppt["Proyecto_A"].astype(str).isin(proy)) &
            (df_ppt["CeCo_A"].astype(str).isin(cecos_sel))  
        ].copy()

        df_real_sel = df_real[
            (df_real["Mes_A"].isin(meses_sel)) &
            (df_real["Proyecto_A"].astype(str).isin(proy)) &
            (df_real["CeCo_A"].astype(str).isin(cecos_sel)) 
        ].copy()
        ppt_nom = float(funcion(df_ppt_sel, meses_sel, proy, proyecto_nombre) or 0.0)
        real_nom = float(funcion(df_real_sel, meses_sel, proy, proyecto_nombre) or 0.0)
        dif_nom = real_nom - ppt_nom
        dif_pct = (((real_nom / ppt_nom) - 1) * 100) if ppt_nom != 0 else 0.0
        ingreso_ppt = float(ingreso(df_ppt_sel, meses_sel, proy, proyecto_nombre) or 0.0)
        ingreso_real = float(ingreso(df_real_sel, meses_sel, proy, proyecto_nombre) or 0.0)

        ppt_pct = (ppt_nom / ingreso_ppt * 100) if ingreso_ppt != 0 else 0.0
        real_pct = (real_nom / ingreso_real * 100) if ingreso_real != 0 else 0.0
        dif_s_ing = (dif_nom / ingreso_real * 100) if ingreso_real != 0 else 0.0

        df_out = pd.DataFrame([{
            "PPT NOM": ppt_nom,
            "REAL NOM": real_nom,
            "DIF NOM": dif_nom,
            "DIF %": round(dif_pct, 2),
            "PPT %": round(ppt_pct, 2),
            "REAL %": round(real_pct, 2),
            "%Ingresos": round(dif_s_ing, 2)
        }])

        def resaltar(row):
            styles = [""] * len(row)
            cols = list(row.index)

            if "DIF %" in cols:
                j = cols.index("DIF %")
                v = float(row["DIF %"]) if pd.notnull(row["DIF %"]) else 0.0
                if v > 10:
                    styles[j] = "background-color:#FF0000;color:white;font-weight:800;"
                else:
                    styles[j] = "background-color:#92D050;color:black;font-weight:800;"
            return styles

        st.dataframe(
            df_out.style
                .apply(resaltar, axis=1)
                .format({
                    "PPT NOM": "${:,.2f}",
                    "REAL NOM": "${:,.2f}",
                    "DIF NOM": "${:,.2f}",
                    "DIF %": "{:.2f}%",
                    "PPT %": "{:.2f}%",
                    "REAL %": "{:.2f}%",
                    "%Ingresos": "{:.2f}%"
                }),
            use_container_width=True
        )


def seccion_analisis_por_clasificacion(
    df_ppt, df_real, ingreso,
    meses_seleccionado, proyecto_codigo, proyecto_nombre,
    clasificacion_nombre,
    cecos_seleccionados  # ✅ NUEVO
):
    with st.expander(clasificacion_nombre):

        meses_completos = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        orden = {m: i for i, m in enumerate(meses_completos)}
        meses_sel = sorted(list(set(meses_seleccionado)), key=lambda x: orden.get(x, 999))

        if not meses_sel:
            st.error("Selecciona por lo menos un mes.")
            return

        proy = [str(x).strip() for x in proyecto_codigo]
        excluir_proyectos = {"8002", "8003", "8004"}
        if clasificacion_nombre in ["COSS", "G.ADMN"]:
            proy = [p for p in proy if str(p).strip() not in excluir_proyectos]
        cecos_sel = [str(x).strip() for x in (cecos_seleccionados or [])]
        if not cecos_sel:
            st.error("Selecciona por lo menos un CeCo.")
            return
        df_ppt_sel = df_ppt[
            (df_ppt["Mes_A"].isin(meses_sel)) &
            (df_ppt["Proyecto_A"].astype(str).isin(proy)) &
            (df_ppt["CeCo_A"].astype(str).isin(cecos_sel)) 
        ].copy()

        ingreso_ppt_sel = float(ingreso(df_ppt_sel, meses_sel, proy, proyecto_nombre) or 0.0)
        df_ppt_sel = df_ppt_sel[df_ppt_sel["Categoria_A"] != "INGRESO"]
        df_ppt_sel = df_ppt_sel[df_ppt_sel["Clasificacion_A"] == clasificacion_nombre]
        ppt_cla_nom = df_ppt_sel.groupby(["Clasificacion_A"], as_index=False)["Neto_A"].sum()
        ppt_cat_nom = df_ppt_sel.groupby(["Clasificacion_A", "Categoria_A"], as_index=False)["Neto_A"].sum()
        ppt_cta_nom = df_ppt_sel.groupby(["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"], as_index=False)["Neto_A"].sum()
        ppt_cla_nom["PPT %"] = np.where(ingreso_ppt_sel != 0, (ppt_cla_nom["Neto_A"] / ingreso_ppt_sel) * 100, 0.0)
        cla_total_ppt = float(ppt_cla_nom["Neto_A"].sum()) if not ppt_cla_nom.empty else 0.0
        ppt_cat_nom["Cla_Total"] = cla_total_ppt
        ppt_cat_nom["PPT %"] = np.where(ppt_cat_nom["Cla_Total"] != 0, (ppt_cat_nom["Neto_A"] / ppt_cat_nom["Cla_Total"]) * 100, 0.0)
        cat_map_ppt = dict(zip(ppt_cat_nom["Categoria_A"], ppt_cat_nom["Neto_A"]))
        ppt_cta_nom["Cat_Total"] = ppt_cta_nom["Categoria_A"].map(cat_map_ppt).fillna(0)
        ppt_cta_nom["PPT % CTA"] = np.where(ppt_cta_nom["Cat_Total"] != 0, (ppt_cta_nom["Neto_A"] / ppt_cta_nom["Cat_Total"]) * 100, 0.0)
        df_real_sel = df_real[
            (df_real["Mes_A"].isin(meses_sel)) &
            (df_real["Proyecto_A"].astype(str).isin(proy)) &
            (df_real["CeCo_A"].astype(str).isin(cecos_sel))   
        ].copy()

        ingreso_real_sel = float(ingreso(df_real_sel, meses_sel, proy, proyecto_nombre) or 0.0)

        df_real_sel = df_real_sel[df_real_sel["Categoria_A"] != "INGRESO"]
        df_real_sel = df_real_sel[df_real_sel["Clasificacion_A"] == clasificacion_nombre]

        real_cla_nom = df_real_sel.groupby(["Clasificacion_A"], as_index=False)["Neto_A"].sum()
        real_cat_nom = df_real_sel.groupby(["Clasificacion_A", "Categoria_A"], as_index=False)["Neto_A"].sum()
        real_cta_nom = df_real_sel.groupby(["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"], as_index=False)["Neto_A"].sum()
        real_cla_nom["REAL %"] = np.where(ingreso_real_sel != 0, (real_cla_nom["Neto_A"] / ingreso_real_sel) * 100, 0.0)
        cla_total_real = float(real_cla_nom["Neto_A"].sum()) if not real_cla_nom.empty else 0.0
        real_cat_nom["Cla_Total"] = cla_total_real
        real_cat_nom["REAL %"] = np.where(real_cat_nom["Cla_Total"] != 0, (real_cat_nom["Neto_A"] / real_cat_nom["Cla_Total"]) * 100, 0.0)
        cat_map_real = dict(zip(real_cat_nom["Categoria_A"], real_cat_nom["Neto_A"]))
        real_cta_nom["Cat_Total"] = real_cta_nom["Categoria_A"].map(cat_map_real).fillna(0)
        real_cta_nom["REAL % CTA"] = np.where(real_cta_nom["Cat_Total"] != 0, (real_cta_nom["Neto_A"] / real_cta_nom["Cat_Total"]) * 100, 0.0)
        df_cla = ppt_cla_nom.merge(
            real_cla_nom[["Clasificacion_A", "Neto_A", "REAL %"]].rename(columns={"Neto_A": "REAL NOM"}),
            on="Clasificacion_A",
            how="outer"
        ).rename(columns={"Neto_A": "PPT NOM"}).fillna(0)

        df_cla["DIF NOM"] = df_cla["REAL NOM"] - df_cla["PPT NOM"]
        df_cla["DIF %"] = np.where(df_cla["PPT NOM"] != 0, ((df_cla["REAL NOM"] / df_cla["PPT NOM"]) - 1) * 100, 0.0)
        df_cla["%Ingresos"] = np.where(ingreso_real_sel != 0, (df_cla["DIF NOM"] / ingreso_real_sel) * 100, 0.0)

        def resaltar_dif_pct(row):
            styles = [""] * len(row)
            cols = list(row.index)
            if "DIF %" in cols:
                j = cols.index("DIF %")
                v = float(row["DIF %"]) if pd.notnull(row["DIF %"]) else 0.0
                styles[j] = "background-color:#FF0000;color:white;font-weight:800;" if v > 10 else "background-color:#92D050;color:black;font-weight:800;"
            return styles

        st.dataframe(
            df_cla.set_index("Clasificacion_A").style
                .apply(resaltar_dif_pct, axis=1)
                .format({
                    "PPT NOM": "${:,.2f}",
                    "REAL NOM": "${:,.2f}",
                    "DIF NOM": "${:,.2f}",
                    "DIF %": "{:.2f}%",
                    "PPT %": "{:.2f}%",
                    "REAL %": "{:.2f}%",
                    "%Ingresos": "{:.2f}%"
                }),
            use_container_width=True
        )
        ppt_cat_nom2 = ppt_cat_nom.rename(columns={"Neto_A": "PPT NOM"}).copy()
        real_cat_nom2 = real_cat_nom.rename(columns={"Neto_A": "REAL NOM"}).copy()

        df_cat = ppt_cat_nom2.merge(
            real_cat_nom2[["Clasificacion_A", "Categoria_A", "REAL NOM", "REAL %"]],
            on=["Clasificacion_A", "Categoria_A"],
            how="outer"
        ).fillna(0)

        df_cat["DIF NOM"] = df_cat["REAL NOM"] - df_cat["PPT NOM"]
        df_cat["DIF %"] = np.where(df_cat["PPT NOM"] != 0, ((df_cat["REAL NOM"] / df_cat["PPT NOM"]) - 1) * 100, 0.0)
        df_cat["%Ingresos"] = np.where(ingreso_real_sel != 0, (df_cat["DIF NOM"] / ingreso_real_sel) * 100, 0.0)
        ppt_cta_nom2 = ppt_cta_nom.rename(columns={"Neto_A": "PPT NOM"}).copy()
        real_cta_nom2 = real_cta_nom.rename(columns={"Neto_A": "REAL NOM"}).copy()

        df_cta = ppt_cta_nom2.merge(
            real_cta_nom2[["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A", "REAL NOM", "REAL % CTA"]],
            on=["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"],
            how="outer"
        ).fillna(0)

        df_cta = df_cta.rename(columns={"PPT % CTA": "PPT %", "REAL % CTA": "REAL %"})
        df_cta["DIF NOM"] = df_cta["REAL NOM"] - df_cta["PPT NOM"]
        df_cta["DIF %"] = np.where(df_cta["PPT NOM"] != 0, ((df_cta["REAL NOM"] / df_cta["PPT NOM"]) - 1) * 100, 0.0)
        df_cta["%Ingresos"] = np.where(ingreso_real_sel != 0, (df_cta["DIF NOM"] / ingreso_real_sel) * 100, 0.0)
        df_out = df_cta[[
            "Categoria_A", "Cuenta_Nombre_A",
            "PPT NOM", "REAL NOM", "DIF NOM", "DIF %",
            "PPT %", "REAL %", "%Ingresos"
        ]].copy()

        df_out["ING_PPT"] = float(ingreso_ppt_sel or 0.0)
        df_out["ING_REAL"] = float(ingreso_real_sel or 0.0)
        df_out["CLA_PPT_TOTAL"] = float(cla_total_ppt or 0.0)
        df_out["CLA_REAL_TOTAL"] = float(cla_total_real or 0.0)
        gb = GridOptionsBuilder.from_dataframe(df_out)
        gb.configure_default_column(resizable=True, sortable=True, filter=True)

        group_col = "Categoria_A"
        detalle_col = "Cuenta_Nombre_A"

        currency_formatter = JsCode("""
            function(params) {
                if (params.value === null || params.value === undefined) return '';
                return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(params.value);
            }
        """)

        pct_formatter = JsCode("""
            function(params) {
                if (params.value === null || params.value === undefined) return '';
                return params.value.toFixed(2) + ' %';
            }
        """)

        dif_pct_value_getter = JsCode("""
            function(params){
                if (params.node && params.node.group) {
                    var agg = params.node.aggData || {};
                    var ppt = agg["PPT NOM"] || 0;
                    var real = agg["REAL NOM"] || 0;
                    if (ppt === 0) return 0;
                    return ((real / ppt) - 1) * 100;
                }
                return params.data ? params.data["DIF %"] : 0;
            }
        """)

        # ✅ CAMBIO SOLO EN GROUP:
        ppt_pct_value_getter = JsCode("""
            function(params){
                if (params.node && params.node.group) {
                    var agg = params.node.aggData || {};
                    var ppt = agg["PPT NOM"] || 0;
                    var cla = agg["CLA_PPT_TOTAL"] || 0;
                    if (cla === 0) return 0;
                    return (ppt / cla) * 100;
                }
                return params.data ? params.data["PPT %"] : 0;
            }
        """)

        real_pct_value_getter = JsCode("""
            function(params){
                if (params.node && params.node.group) {
                    var agg = params.node.aggData || {};
                    var real = agg["REAL NOM"] || 0;
                    var cla = agg["CLA_REAL_TOTAL"] || 0;
                    if (cla === 0) return 0;
                    return (real / cla) * 100;
                }
                return params.data ? params.data["REAL %"] : 0;
            }
        """)

        ingresos_pct_value_getter = JsCode("""
            function(params){
                if (params.node && params.node.group) {
                    var agg = params.node.aggData || {};
                    var dif = agg["DIF NOM"] || 0;
                    var ing = (agg["ING_REAL"] || 0);
                    if (ing === 0) return 0;
                    return (dif / ing) * 100;
                }
                return params.data ? params.data["%Ingresos"] : 0;
            }
        """)

        dif_pct_color = JsCode("""
            function(params){
                if (params.value === null || params.value === undefined) return {};
                if (params.value > 10){
                    return { 'backgroundColor': '#FF0000', 'color': 'white', 'fontWeight': '800', 'textAlign':'right' };
                } else {
                    return { 'backgroundColor': '#92D050', 'color': 'black', 'fontWeight': '800', 'textAlign':'right' };
                }
            }
        """)

        gridOptions = gb.build()

        gridOptions["columnDefs"] = [
            {"field": group_col, "rowGroup": True, "hide": True},
            {"field": detalle_col, "headerName": "Cuenta", "minWidth": 320},

            {"field": "PPT NOM", "headerName": "PPT NOM", "type": ["numericColumn"], "aggFunc": "sum",
             "valueFormatter": currency_formatter, "cellStyle": {"textAlign": "right"}},

            {"field": "REAL NOM", "headerName": "REAL NOM", "type": ["numericColumn"], "aggFunc": "sum",
             "valueFormatter": currency_formatter, "cellStyle": {"textAlign": "right"}},

            {"field": "DIF NOM", "headerName": "DIF NOM", "type": ["numericColumn"], "aggFunc": "sum",
             "valueFormatter": currency_formatter, "cellStyle": {"textAlign": "right"}},

            {"field": "DIF %", "headerName": "DIF %", "type": ["numericColumn"],
             "valueGetter": dif_pct_value_getter, "valueFormatter": pct_formatter, "cellStyle": dif_pct_color},

            {"field": "PPT %", "headerName": "PPT %", "type": ["numericColumn"],
             "valueGetter": ppt_pct_value_getter, "valueFormatter": pct_formatter, "cellStyle": {"textAlign": "right"}},

            {"field": "REAL %", "headerName": "REAL %", "type": ["numericColumn"],
             "valueGetter": real_pct_value_getter, "valueFormatter": pct_formatter, "cellStyle": {"textAlign": "right"}},

            {"field": "%Ingresos", "headerName": "%Ingresos", "type": ["numericColumn"],
             "valueGetter": ingresos_pct_value_getter, "valueFormatter": pct_formatter, "cellStyle": {"textAlign": "right"}},

            {"field": "ING_PPT", "hide": True, "aggFunc": "first"},
            {"field": "ING_REAL", "hide": True, "aggFunc": "first"},

            {"field": "CLA_PPT_TOTAL", "hide": True, "aggFunc": "first"},
            {"field": "CLA_REAL_TOTAL", "hide": True, "aggFunc": "first"},
        ]

        gridOptions["groupDisplayType"] = "singleColumn"
        gridOptions["groupDefaultExpanded"] = 0
        gridOptions["autoGroupColumnDef"] = {
            "headerName": "Group",
            "minWidth": 260,
            "pinned": "left",
            "cellRendererParams": {"suppressCount": False},
        }

        gridOptions["suppressAggFuncInHeader"] = True

        meses_key = "-".join(meses_sel)
        grid_key = f"agrid_mix_{clasificacion_nombre}_{'-'.join(proy)}_{meses_key}_{'-'.join(cecos_sel)}"  # ✅ incluye CeCo para evitar cache raro

        AgGrid(
            df_out,
            gridOptions=gridOptions,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=True,
            height=520,
            use_checkbox=False,
            fit_columns_on_grid_load=True,
            theme="streamlit",
            key=grid_key
        )

def agrid_ingreso_con_totales(df):
    df = df.copy()

    df_g = (
        df[df["Categoria_A"] == "INGRESO"]
        .groupby(["Categoria_A", "Cuenta_A", "Cuenta_Nombre_A"], as_index=False)
        .agg({"Neto_A": "sum"})
    )

    currency_formatter = JsCode("""
    function(params) {
        if (params.value === null || params.value === undefined) return "";
        return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(params.value);
    }
    """)

    gb = GridOptionsBuilder.from_dataframe(df_g)
    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_column("Categoria_A", rowGroup=True, hide=True)
    gb.configure_column("Cuenta_A", header_name="Cuenta", pinned="left")
    gb.configure_column("Cuenta_Nombre_A", header_name="Cuenta_Nombre_A", pinned="left")

    gb.configure_column(
        "Neto_A",
        header_name="Total (MXN)",
        type=["numericColumn"],
        aggFunc="sum",
        valueFormatter=currency_formatter
    )

    grid_options = gb.build()
    grid_options.update({
        "groupDisplayType": "groupRows",
        "groupDefaultExpanded": 1,
        "suppressAggFuncInHeader": True
    })

    AgGrid(
        df_g,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=420,
        theme="streamlit",
        key="agrid_ingreso_totales_nominal"
    )

def tabla_proyectos(df_ppt, df_real, meses_seleccionado, df_proyectos):
    """
    Salida:
    PROYECTO | INGRESO REAL | VAR.PPT | COSS REAL | VAR. COSS | G.ADM REAL | VAR. G.ADM

    VAR.PPT   = (INGRESO REAL / INGRESO PPT) - 1
    VAR. COSS = (COSS REAL / COSS PPT) - 1
    VAR. G.ADM= (G.ADM REAL / G.ADM PPT) - 1
    """
    if not meses_seleccionado:
        st.error("Favor de seleccionar por lo menos un mes")
        return None

    meses_sel = [str(m).strip() for m in meses_seleccionado]

    df_ppt = df_ppt.copy()
    df_real = df_real.copy()

    for df in (df_ppt, df_real):
        df["Proyecto_A"] = df["Proyecto_A"].astype(str).str.strip()
        df["CeCo_A"] = df["CeCo_A"].astype(str).str.strip()
        df["Mes_A"] = df["Mes_A"].astype(str).str.strip()
        df["Clasificacion_A"] = df["Clasificacion_A"].astype(str).str.strip()
        df["Categoria_A"] = df["Categoria_A"].astype(str).str.strip()
        df["Neto_A"] = pd.to_numeric(df["Neto_A"], errors="coerce").fillna(0.0)


    df_map = df_proyectos.copy()
    df_map["proyectos"] = df_map["proyectos"].astype(str).str.strip()
    df_map["nombre"] = df_map["nombre"].astype(str).str.strip()
    mapa = dict(zip(df_map["proyectos"], df_map["nombre"]))
    EXCLUIR = {"8002", "8003", "8004", "0"}
    proyectos_visibles = [p for p in df_map["proyectos"].tolist() if p not in EXCLUIR]
    lista_proyectos = list_pro

    rows = []
    for p in proyectos_visibles:
        nombre = mapa.get(p, p)
        codigo_pro = [p]
        pro = nombre  
        ing_ppt = float(ingreso(df_ppt, meses_sel, codigo_pro, pro) or 0.0)
        ing_real = float(ingreso(df_real, meses_sel, codigo_pro, pro) or 0.0)
        coss_ppt, _  = coss(df_ppt,  meses_sel, codigo_pro, pro, lista_proyectos)
        coss_real, _ = coss(df_real, meses_sel, codigo_pro, pro, lista_proyectos)
        coss_ppt  = float(coss_ppt or 0.0)
        coss_real = float(coss_real or 0.0)

        patio_ppt  = float(patio(df_ppt,  meses_sel, codigo_pro, pro) or 0.0)
        patio_real = float(patio(df_real, meses_sel, codigo_pro, pro) or 0.0)

        coss_total_ppt  = coss_ppt  + patio_ppt
        coss_total_real = coss_real + patio_real
        gadm_ppt, _  = gadmn(df_ppt,  meses_sel, codigo_pro, pro, lista_proyectos)
        gadm_real, _ = gadmn(df_real, meses_sel, codigo_pro, pro, lista_proyectos)
        gadm_ppt  = float(gadm_ppt or 0.0)
        gadm_real = float(gadm_real or 0.0)

        rows.append({
            "Proyecto_A": p,
            "PROYECTO": nombre,
            "ING_PPT": ing_ppt,
            "ING_REAL": ing_real,
            "COSS_PPT": coss_total_ppt,     
            "COSS_REAL": coss_total_real,   
            "GADM_PPT": gadm_ppt,
            "GADM_REAL": gadm_real,
        })

    tabla = pd.DataFrame(rows).fillna(0.0)

    # --- variaciones
    tabla["VAR.PPT"] = np.where(
        tabla["ING_PPT"] != 0,
        (tabla["ING_REAL"] / tabla["ING_PPT"]) - 1,
        0.0
    )
    tabla["VAR. COSS"] = np.where(
        tabla["COSS_PPT"] != 0,
        (tabla["COSS_REAL"] / tabla["COSS_PPT"]) - 1,
        0.0
    )
    tabla["VAR. G.ADM"] = np.where(
        tabla["GADM_PPT"] != 0,
        (tabla["GADM_REAL"] / tabla["GADM_PPT"]) - 1,
        0.0
    )

    def _arrow(v, tol=1e-9):
        try:
            v = float(v)
        except:
            return ""
        if v > tol:
            return " ↑"
        if v < -tol:
            return " ↓"
        return " →"

    tabla["VAR.PPT_TXT"]    = tabla["VAR.PPT"].apply(lambda x: f"{x:.2%}{_arrow(x)}")
    tabla["VAR. COSS_TXT"]  = tabla["VAR. COSS"].apply(lambda x: f"{x:.2%}{_arrow(x)}")
    tabla["VAR. G.ADM_TXT"] = tabla["VAR. G.ADM"].apply(lambda x: f"{x:.2%}{_arrow(x)}")

    out = tabla[[
        "PROYECTO",
        "ING_REAL", "VAR.PPT_TXT",
        "COSS_REAL", "VAR. COSS_TXT",
        "GADM_REAL", "VAR. G.ADM_TXT"
    ]].copy()

    # --- TOTAL (con los mismos campos)
    total_ing_real  = float(tabla["ING_REAL"].sum())
    total_ing_ppt   = float(tabla["ING_PPT"].sum())
    total_coss_real = float(tabla["COSS_REAL"].sum())
    total_coss_ppt  = float(tabla["COSS_PPT"].sum())
    total_gadm_real = float(tabla["GADM_REAL"].sum())
    total_gadm_ppt  = float(tabla["GADM_PPT"].sum())

    total_var_ppt  = (total_ing_real / total_ing_ppt - 1) if total_ing_ppt != 0 else 0.0
    total_var_coss = (total_coss_real / total_coss_ppt - 1) if total_coss_ppt != 0 else 0.0
    total_var_gadm = (total_gadm_real / total_gadm_ppt - 1) if total_gadm_ppt != 0 else 0.0

    total_row = pd.DataFrame([{
        "PROYECTO": "TOTAL",
        "ING_REAL": total_ing_real,
        "VAR.PPT_TXT": f"{total_var_ppt:.2%}{_arrow(total_var_ppt)}",
        "COSS_REAL": total_coss_real,
        "VAR. COSS_TXT": f"{total_var_coss:.2%}{_arrow(total_var_coss)}",
        "GADM_REAL": total_gadm_real,
        "VAR. G.ADM_TXT": f"{total_var_gadm:.2%}{_arrow(total_var_gadm)}",
    }])

    out = pd.concat([out, total_row], ignore_index=True)

    BLUE = "#0B2A4A"
    GRIS_1 = "#FFFFFF"
    GRIS_2 = "#F2F2F2"
    BORDE = "#D0D0D0"

    def estilo_filas(row):
        if str(row["PROYECTO"]).upper() == "TOTAL":
            return ["background-color:#FFFFFF; color:black; font-weight:800;"] * len(row)
        bg = GRIS_1 if row.name % 2 == 0 else GRIS_2
        return [f"background-color:{bg}; color:black;"] * len(row)

    st.subheader("Operación por proyecto")

    st.dataframe(
        out.style
            .apply(estilo_filas, axis=1)
            .set_table_styles([
                {"selector": "thead th",
                 "props": f"background-color:{BLUE};color:white;font-weight:900;font-size:13px;border:1px solid {BORDE};text-align:center;"},
                {"selector": "tbody td",
                 "props": f"border:1px solid {BORDE};font-size:12px;"},
                {"selector": "table",
                 "props": "border-collapse:collapse; width:100%;"},
            ])
            .format({
                "ING_REAL": "${:,.2f}",
                "COSS_REAL": "${:,.2f}",
                "GADM_REAL": "${:,.2f}",
                "VAR.PPT_TXT": "{}",
                "VAR. COSS_TXT": "{}",
                "VAR. G.ADM_TXT": "{}",
            })
            .set_properties(subset=["PROYECTO"], **{"text-align": "left", "font-weight": "700"})
            .set_properties(subset=[
                "ING_REAL", "VAR.PPT_TXT",
                "COSS_REAL", "VAR. COSS_TXT",
                "GADM_REAL", "VAR. G.ADM_TXT"
            ], **{"text-align": "right"}),
        use_container_width=True,
        height=420
    )

    return out



init_session_state()
# App principal
df_usuarios = cargar_datos(Usuarios_url)

if not st.session_state["logged_in"]:

    st.title("🔐 Inicio de Sesión presupuesto")

    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar sesión")

        if submitted:
            user, rol, proyectos, cecos = validar_credenciales(df_usuarios, username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = user
                st.session_state["rol"] = rol
                st.session_state["proyectos"] = proyectos
                st.session_state["cecos"] = cecos
                st.success("¡Inicio de sesión exitoso!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
else:
    df_ppt = cargar_datos(base_ppt)
    df_ppt = (
    df_ppt
    .groupby([
        "Mes_A", "Empresa_A", "CeCo_A", "Proyecto_A", "Cuenta_A",
        "Clasificacion_A", "Cuenta_Nombre_A", "Categoria_A"
    ], as_index=False)["Neto_A"]
    .sum()
)

    df_real = cargar_datos(basereal)
    df_real = (
    df_real
    .groupby([
        "Mes_A", "Empresa_A", "CeCo_A", "Proyecto_A", "Cuenta_A",
        "Clasificacion_A", "Cuenta_Nombre_A", "Categoria_A"
    ], as_index=False)["Neto_A"]
    .sum()
)

    df_base = cargar_datos(base_2026)
    df_base = (
    df_base
    .groupby([
        "Mes_A", "Empresa_A", "CeCo_A", "Proyecto_A", "Cuenta_A",
        "Clasificacion_A", "Cuenta_Nombre_A", "Categoria_A"
    ], as_index=False)["Neto_A"]
    .sum()
)
    
    proyectos = cargar_datos(proyectos_url)

    df_ppt["Proyecto_A"] = df_ppt["Proyecto_A"].astype(str).str.strip()
    df_real["Proyecto_A"] = df_real["Proyecto_A"].astype(str).str.strip()
    df_base["Proyecto_A"] = df_base["Proyecto_A"].astype(str).str.strip()
    df_ppt["CeCo_A"] = df_ppt["CeCo_A"].astype(str).str.strip()
    df_real["CeCo_A"] = df_real["CeCo_A"].astype(str).str.strip()
    df_base["CeCo_A"] = df_base["CeCo_A"].astype(str).str.strip()
    proyectos["proyectos"] = proyectos["proyectos"].astype(str).str.strip()
    list_pro = proyectos["proyectos"].tolist()
    st.sidebar.success(f"👤 Usuario: {st.session_state['username']}")

    if st.sidebar.button("Cerrar sesión"):
        for key in ["logged_in", "username", "rol"]:
            st.session_state[key] = "" if key != "logged_in" else False
        st.rerun()
    if st.sidebar.link_button("ESGARI 360", "https://esgari-360.streamlit.app/"):
        pass

    if st.session_state['rol'] == "admin":
        if st.sidebar.button("🔄 Recargar datos"):
            st.cache_data.clear()
            st.rerun()
    if st.session_state["rol"] in ["admin"] and "ESGARI" in st.session_state["proyectos"]:
        selected = option_menu(
            menu_title=None,
            options=["Tablero", "Ingresos", "OH", "Departamentos", "Proyectos", "Consulta", "Meses PPT", "Variaciones","Proyección","YTD","Mensual", "Modificaciones", "Dashboard"],
            icons=[
            "clipboard-data",
            "cash-coin",          # Ingresos
            "building",           # OH (Overhead / oficinas)
            "diagram-3",          # Departamentos
            "kanban",          # Proyectos
            "search",             # Consulta
            "calendar-month",     # Meses PPT
            "arrow-left-right",
            "graph-up-arrow",  
            "bar-chart-line",
            "calendar-month",
            "tools",
            "speedometer2",
        ],
            default_index=0,
            orientation="horizontal",
        )
    elif st.session_state["rol"] == "director" or st.session_state["rol"] == "admin":
        selected = option_menu(
        menu_title=None,
        options=["Tablero", "Ingresos", "OH", "Departamentos", "Proyectos", "Consulta", "Meses PPT", "Variaciones", "Proyección","YTD","Mensual", "Modificaciones", "Dashboard"],
        icons=["clipboard-data", "cash-coin", "building", "diagram-3", "kanban", "search", "calendar-month", "arrow-left-right", "graph-up-arrow", "bar-chart-line", "calendar-month", "tools", "speedometer2"],
        default_index=0,
        orientation="horizontal",)

    elif st.session_state["rol"] == "gerente":
        selected = option_menu(
        menu_title=None,
        options=["Ingresos", "Consulta", "Meses PPT"],
        icons=["bar-chart-steps", "search", "calendar-month"],
        default_index=0,
        orientation="horizontal",)

    elif st.session_state["rol"] == "ceco":
        selected = option_menu(
        menu_title=None,
        options=[ "Departamentos", "Consulta"],
        icons=[ "diagram-3", "search"],
        default_index=0,
        orientation="horizontal",)

    def proyecciones(ingreso_pro_fut, df_ext_var, df_sum, oh_pro, intereses, patio_pro, coss_pro_ori, gadmn_pro_ori):
        utilidad_op = ingreso_pro_fut - coss_pro_ori - gadmn_pro_ori
        por_util_op = utilidad_op / ingreso_pro_fut if ingreso_pro_fut else 0
        ebit = utilidad_op - oh_pro
        ebt = ebit - intereses
        por_ebt = ebt / ingreso_pro_fut if ingreso_pro_fut else 0
        return utilidad_op, por_util_op, ebit, ebt, por_ebt

    def _norm_proy_list(lst):
        if lst is None:
            return []
        out = []
        for x in lst:
            s = str(x).strip()
            if s == "" or s.lower() == "none":
                continue
            s = s.replace(".0", "")
            try:
                s = str(int(float(s)))
            except:
                pass
            out.append(s.strip())
        return out

    def _norm_proy_col(df, col="Proyecto_A"):
        df = df.copy()
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.replace(".0", "", regex=False)
        if "Mes_A" in df.columns:
            df["Mes_A"] = df["Mes_A"].astype(str).str.strip()
        if "Categoria_A" in df.columns:
            df["Categoria_A"] = df["Categoria_A"].astype(str).str.strip()
        if "Clasificacion_A" in df.columns:
            df["Clasificacion_A"] = df["Clasificacion_A"].astype(str).str.strip()
        if "Neto_A" in df.columns:
            df["Neto_A"] = pd.to_numeric(df["Neto_A"], errors="coerce").fillna(0.0)
        return df

    costos_variables = ["FLETES", "CASETAS", "COMBUSTIBLE", "OTROS COSS", "INGRESO"]
    meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
    if isinstance(filtro_pro, (tuple, list)):
        codigo_pro, pro = filtro_pro
    else:
        codigo_pro = st.session_state.get("codigo_pro", [])
        pro = st.session_state.get("pro", "ESGARI")

    codigo_pro = _norm_proy_list(codigo_pro)
    pro = str(pro).strip() if pro is not None else "ESGARI"

    df_ppt_n  = _norm_proy_col(df_ppt,  "Proyecto_A")
    df_real_n = _norm_proy_col(df_real, "Proyecto_A")

    meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
    idx_mes = {m: i for i, m in enumerate(meses_ordenados)}

    def _prev_mes(m):
        i = idx_mes.get(m, None)
        if i is None:
            return None
        return meses_ordenados[i - 1]  
    meses_real_unicos = (
        df_real_n["Mes_A"].astype(str).str.strip().unique().tolist()
        if "Mes_A" in df_real_n.columns else []
    )
    meses_disponibles = [m for m in meses_ordenados if m in meses_real_unicos]

    if len(meses_disponibles) < 2:
        st.warning("No hay suficientes meses en REAL para calcular mes actual y mes anterior.")
        st.stop()

    fecha_url = "https://docs.google.com/spreadsheets/d/1HAZKds5buqJdpq9053T-X9WjxWvITWhNaO7CnSTnoWA/export?format=xlsx"
    fecha_actualizacion = cargar_datos(fecha_url)

    if "fecha" not in fecha_actualizacion.columns or fecha_actualizacion.empty:
        st.warning("No se encontró la columna 'fecha' en fecha_actualizacion; usaré los últimos meses disponibles en REAL.")
        mes_act = meses_disponibles[-1]
        mes_ant = meses_disponibles[-2]
        fecha_act = None
    else:
        fecha_actualizacion["fecha"] = pd.to_datetime(fecha_actualizacion["fecha"], errors="coerce")
        fecha_valida = fecha_actualizacion.dropna(subset=["fecha"])

        if fecha_valida.empty:
            st.warning("La columna 'fecha' no tiene valores válidos; usaré los últimos meses disponibles en REAL.")
            mes_act = meses_disponibles[-1]
            mes_ant = meses_disponibles[-2]
            fecha_act = None
        else:
            fecha_completa = fecha_valida["fecha"].max()  
            fecha_act = int(fecha_completa.day)
            mes_act = meses_ordenados[int(fecha_completa.month) - 1]
            mes_ant = _prev_mes(mes_act)
            if mes_act not in meses_disponibles or mes_ant not in meses_disponibles:
                st.warning(
                    f"Mes(es) por fecha de actualización no disponibles en REAL (mes_act={mes_act}, mes_ant={mes_ant}). "
                    "Usaré los últimos meses disponibles en REAL."
                )
                mes_act = meses_disponibles[-1]
                mes_ant = meses_disponibles[-2]

    st.session_state["PROY_fecha_actualizacion"] = str(fecha_completa) if "fecha_completa" in locals() else None
    st.session_state["PROY_fecha_act_dia"] = fecha_act

    ingreso_sem = "https://docs.google.com/spreadsheets/d/14l6QLudSBpqxmfuwRqVxCXzhSFzRL0AqWJqVuIOaFFQ/export?format=xlsx"
    df_ing = cargar_datos(ingreso_sem)

    df_ing["mes"] = pd.to_datetime(df_ing["fecha"]).dt.day
    idx = (df_ing["mes"] - fecha_act).abs().idxmin()
    dia_ref = int(df_ing.loc[idx, "mes"])

    df_va = df_ing[df_ing["mes"] == dia_ref].copy()
    df_va["ingreso"] = df_va["ingreso"] / dia_ref * fecha_act
    df_va = df_va.drop(columns=["mes", "semana", "fecha"])

    df_fin = df_ing[df_ing["semana"] == 4].drop(columns=["mes", "semana", "fecha"])
    df_merged = pd.merge(df_va, df_fin, on="proyecto", suffixes=("_va", "_fin"))
    df_merged["ingreso_dividido"] = df_merged["ingreso_va"] / df_merged["ingreso_fin"].replace(0, pd.NA)
    df_merged["ingreso_dividido"] = df_merged["ingreso_dividido"].replace([0, float("inf"), -float("inf")], pd.NA)
    df_proyeccion = (
        df_real_n[df_real_n["Mes_A"] == mes_act]
        .loc[df_real_n["Categoria_A"] == "INGRESO"]
        .groupby(["Proyecto_A"], as_index=False)["Neto_A"]
        .sum()
    )

    # merge factor
    df_proyeccion["Proyecto_num"] = pd.to_numeric(df_proyeccion["Proyecto_A"], errors="coerce")
    df_proyeccion = df_proyeccion.merge(
        df_merged,
        left_on="Proyecto_num",
        right_on="proyecto",
        how="left"
    )

    # proyección = REAL_MTD / factor
    df_proyeccion["Neto_A"] = np.where(
        df_proyeccion["ingreso_dividido"].notna(),
        df_proyeccion["Neto_A"] / df_proyeccion["ingreso_dividido"],
        0.0
    )

    df_proyeccion["Proyecto_A"] = df_proyeccion["Proyecto_num"].fillna(0).astype(int).astype(str)
    df_proyeccion = df_proyeccion.drop(columns=["Proyecto_num"])

    # ingreso_pro_fut consolidado por filtro
    if pro == "ESGARI":
        ingreso_pro_fut = float(df_proyeccion["Neto_A"].sum())
    else:
        ingreso_pro_fut = float(df_proyeccion[df_proyeccion["Proyecto_A"].isin(codigo_pro)]["Neto_A"].sum())
    df_sum = df_real_n[df_real_n["Mes_A"] == mes_ant].copy()
    df_sum = df_sum[~df_sum["Categoria_A"].isin(costos_variables)]

    if pro != "ESGARI":
        df_sum = df_sum[df_sum["Proyecto_A"].isin(codigo_pro)]

    # excluye OH
    df_sum = df_sum[~df_sum["Proyecto_A"].isin(["8002", "8003", "8004"])]

    # lo “mueves” a mes_act (como ya hacías)
    df_sum["Mes_A"] = mes_act
    patio_pro = patio(df_real_n, [mes_ant], codigo_pro, pro)
    oh_pro    = oh(df_real_n,    [mes_ant], codigo_pro, pro)
    df_ext_var = df_real_n[df_real_n["Mes_A"] == mes_act].copy()
    df_ext_var = df_ext_var[df_ext_var["Categoria_A"].isin(costos_variables)]

    if pro != "ESGARI":
        df_ext_var = df_ext_var[df_ext_var["Proyecto_A"].isin(codigo_pro)]

    # ingreso base REAL (para ratios)
    ingreso_base = float(df_ext_var.loc[df_ext_var["Categoria_A"] == "INGRESO", "Neto_A"].sum())

    # ratios vs ingreso REAL
    df_ext_var["Neto_normalizado"] = (df_ext_var["Neto_A"] / ingreso_base) if ingreso_base != 0 else 0.0

    # quita INGRESO y reescala
    df_ext_var = df_ext_var[df_ext_var["Categoria_A"] != "INGRESO"].copy()
    df_ext_var["Neto_A"] = df_ext_var["Neto_normalizado"] * ingreso_pro_fut
    df_junto = pd.concat([df_ext_var, df_sum], ignore_index=True)

    coss_pro  = float(df_junto.loc[df_junto["Clasificacion_A"] == "COSS", "Neto_A"].sum()) + float(patio_pro)
    gadmn_pro = float(df_junto.loc[df_junto["Clasificacion_A"] == "G.ADMN", "Neto_A"].sum())

    ingreso_fin_cue = [
        "INGRESO POR REVALUACION CAMBIARIA",
        "INGRESOS POR INTERESES",
        "INGRESO POR REVALUACION DE ACTIVOS",
        "INGRESO POR FACTORAJE",
    ]

    intereses = float(
        df_junto.loc[df_junto["Clasificacion_A"] == "GASTOS FINANCIEROS", "Neto_A"].sum()
        - df_junto.loc[df_junto["Categoria_A"].isin(ingreso_fin_cue), "Neto_A"].sum()
    )

    utilidad_op, por_util_op, ebit, ebt, por_ebt = proyecciones(
        ingreso_pro_fut, df_ext_var, df_sum, oh_pro, intereses, patio_pro, coss_pro, gadmn_pro
    )

    # ---- session_state (igual que ya guardabas)
    st.session_state["PROY_codigo_pro"] = codigo_pro
    st.session_state["PROY_pro"] = pro

    st.session_state["PROY_mes_ant"] = mes_ant
    st.session_state["PROY_mes_act"] = mes_act

    st.session_state["PROY_ingreso_pro_fut"] = ingreso_pro_fut
    st.session_state["PROY_coss_pro"] = coss_pro
    st.session_state["PROY_gadmn_pro"] = gadmn_pro
    st.session_state["PROY_patio_pro"] = patio_pro
    st.session_state["PROY_oh_pro"] = oh_pro
    st.session_state["PROY_intereses"] = intereses

    st.session_state["PROY_utilidad_op"] = utilidad_op
    st.session_state["PROY_por_util_op"] = por_util_op
    st.session_state["PROY_ebit"] = ebit
    st.session_state["PROY_ebt"] = ebt
    st.session_state["PROY_por_ebt"] = por_ebt

    st.session_state["PROY_df_ext_var"] = df_ext_var
    st.session_state["PROY_df_sum"] = df_sum
    st.session_state["PROY_df_junto"] = df_junto
    st.session_state["PROY_df_proyeccion"] = df_proyeccion
    st.session_state["PROY_df_ing"] = df_ing
    st.session_state["PROY_df_merged"] = df_merged

    if selected == "Tablero":

        def fmt_mxn(x):
            try:
                return f"${float(x):,.0f}"
            except:
                return "$0"

        def fmt_pct(x):
            try:
                return f"{x*100:.1f}%"
            except:
                return "0.0%"

        def delta_pct(real, ppt):
            try:
                real = float(real or 0.0)
                ppt = float(ppt or 0.0)
            except:
                return "0.0%"
            if ppt == 0:
                return "0.0%"
            return f"{((real / ppt) - 1) * 100:+.1f}%"
        def uo_objetivos_en_tablero(df_ppt, df_real, fecha_actualizacion, proyectos, list_pro, meses_sel):
            """
            Tabla + gráfica de % Utilidad Operativa por proyecto:
            PPT (objetivo_uo) vs REAL (estado_resultado) vs PROYECTADO (histórico ingreso + fijos LM + variables mes actual)
            """

            # ====== objetivos PPT ======
            objetivo_uo = {
                "ARRAYANES": 0.24,
                "CENTRAL OTROS": 0.29,
                "CHALCO": 0.24,
                "CONTINENTAL": 0.30,
                "FLEX DEDICADO": 0.27,
                "FLEX SPOT": 0.24,
                "INTERNACIONAL FWD": 0.24,
                "WH": 0.21,
                "MANZANILLO": 0.25,
                "NUEVO PROYECTO 1": 0.26,
                "ESGARI": 0.25
            }

            meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
            fecha_completa = pd.to_datetime(fecha_actualizacion["fecha"].iloc[0])
            idx_mes_act = int(fecha_completa.month - 1)
            mes_act = meses_ordenados[idx_mes_act]
            mes_ant_lm = meses_ordenados[(idx_mes_act - 1) % 12]  
            proyectos_local = proyectos.copy()
            proyectos_local["proyectos"] = proyectos_local["proyectos"].astype(str).str.strip()
            proyectos_local["nombre"] = proyectos_local["nombre"].astype(str).str.strip()

            allowed = [str(x).strip() for x in st.session_state.get("proyectos", [])]
            if allowed == ["ESGARI"]:
                df_visibles = proyectos_local.copy()
            else:
                df_visibles = proyectos_local[proyectos_local["proyectos"].isin(allowed)].copy()

            excluir = {"8002", "8003", "8004"}
            df_visibles = df_visibles[~df_visibles["proyectos"].astype(str).isin(excluir)].copy()

            nombres = df_visibles["nombre"].tolist()
            codigos = df_visibles["proyectos"].tolist()
            def _norm_proy_code(x):
                return str(x).strip().replace(".0", "")

            def _safe_str(df, col):
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip().str.replace(".0", "", regex=False)
                return df
            def ingreso_proy_historico(df_base, fecha_actualizacion, mes_act, codigo_list, pro_nombre):
                ingreso_sem = "https://docs.google.com/spreadsheets/d/14l6QLudSBpqxmfuwRqVxCXzhSFzRL0AqWJqVuIOaFFQ/export?format=xlsx"
                df = cargar_datos(ingreso_sem)

                fecha_completa = pd.to_datetime(fecha_actualizacion["fecha"].iloc[0])
                fecha_act = int(fecha_completa.day)

                df = df.copy()
                df["mes"] = pd.to_datetime(df["fecha"]).dt.day

                indice_mas_cercano = (df["mes"] - fecha_act).abs().idxmin()
                valor_mas_cercano = int(df.loc[indice_mas_cercano, "mes"])

                df_va = df[df["mes"] == valor_mas_cercano].copy()
                df_va["ingreso"] = df_va["ingreso"] / valor_mas_cercano * fecha_act
                df_va = df_va.drop(columns=["mes", "semana", "fecha"], errors="ignore")

                df_fin = df[df["semana"] == 4].copy()
                df_fin = df_fin.drop(columns=["mes", "semana", "fecha"], errors="ignore")

                df_merged = pd.merge(df_va, df_fin, on="proyecto", suffixes=("_va", "_fin"), how="inner")
                df_merged["ingreso_dividido"] = df_merged["ingreso_va"] / df_merged["ingreso_fin"]

                df_proyeccion = df_base[df_base["Mes_A"] == mes_act].copy()
                df_proyeccion = _safe_str(df_proyeccion, "Proyecto_A")

                df_proyeccion = df_proyeccion.groupby(["Proyecto_A", "Categoria_A"], as_index=False)["Neto_A"].sum()
                df_proyeccion = df_proyeccion[df_proyeccion["Categoria_A"] == "INGRESO"].drop(columns=["Categoria_A"])

                df_proyeccion["Proyecto_A_num"] = pd.to_numeric(df_proyeccion["Proyecto_A"], errors="coerce")
                df_merged["proyecto_num"] = pd.to_numeric(df_merged["proyecto"], errors="coerce")

                df_proyeccion = pd.merge(
                    df_proyeccion,
                    df_merged[["proyecto_num", "ingreso_dividido"]],
                    left_on="Proyecto_A_num",
                    right_on="proyecto_num",
                    how="left"
                )

                df_proyeccion["ingreso_dividido"] = pd.to_numeric(df_proyeccion["ingreso_dividido"], errors="coerce")
                df_proyeccion["Neto_A"] = pd.to_numeric(df_proyeccion["Neto_A"], errors="coerce").fillna(0.0)

                mask_ok = df_proyeccion["ingreso_dividido"].notna() & (df_proyeccion["ingreso_dividido"].abs() > 1e-9)
                df_proyeccion.loc[mask_ok, "Neto_A"] = df_proyeccion.loc[mask_ok, "Neto_A"] / df_proyeccion.loc[mask_ok, "ingreso_dividido"]
                df_proyeccion.loc[~mask_ok, "Neto_A"] = 0.0  # conservador si no hay ratio

                if pro_nombre != "ESGARI":
                    cods = [str(x).strip() for x in codigo_list]
                    df_proyeccion = df_proyeccion[df_proyeccion["Proyecto_A"].astype(str).isin(cods)]

                return float(df_proyeccion["Neto_A"].sum() or 0.0)
            def calc_pct_uo_proy(df_base, fecha_actualizacion, mes_act, mes_ant_lm, codigo_list, pro_nombre):
                costos_variables = ["FLETES", "CASETAS", "COMBUSTIBLE", "OTROS COSS", "INGRESO"]

                ingreso_proy = ingreso_proy_historico(df_base, fecha_actualizacion, mes_act, codigo_list, pro_nombre)
                if abs(ingreso_proy) < 1e-9:
                    return 0.0

                # FIJOS LM
                df_fix = df_base[df_base["Mes_A"] == mes_ant_lm].copy()
                df_fix = _safe_str(df_fix, "Proyecto_A")
                df_fix = df_fix[~df_fix["Categoria_A"].isin(costos_variables)]

                if pro_nombre != "ESGARI":
                    cods = [str(x).strip() for x in codigo_list]
                    df_fix = df_fix[df_fix["Proyecto_A"].astype(str).isin(cods)]

                df_fix = df_fix[~df_fix["Proyecto_A"].astype(str).isin(["8002", "8003", "8004"])]
                df_var = df_base[df_base["Mes_A"] == mes_act].copy()
                df_var = _safe_str(df_var, "Proyecto_A")
                df_var = df_var[df_var["Categoria_A"].isin(costos_variables)]

                if pro_nombre != "ESGARI":
                    cods = [str(x).strip() for x in codigo_list]
                    df_var = df_var[df_var["Proyecto_A"].astype(str).isin(cods)]

                ingreso_real_base = float(df_var.loc[df_var["Categoria_A"] == "INGRESO", "Neto_A"].sum() or 0.0)

                if abs(ingreso_real_base) < 1e-9:
                    df_var_proj = df_var[df_var["Categoria_A"] != "INGRESO"].copy()
                    df_var_proj["Neto_A"] = 0.0
                else:
                    df_var["Neto_A"] = pd.to_numeric(df_var["Neto_A"], errors="coerce").fillna(0.0)
                    df_var["Neto_normalizado"] = df_var["Neto_A"] / ingreso_real_base
                    df_var_proj = df_var[df_var["Categoria_A"] != "INGRESO"].copy()
                    df_var_proj["Neto_A"] = df_var_proj["Neto_normalizado"] * ingreso_proy


                patio_pro = float(patio(df_base, [mes_ant_lm], codigo_list, pro_nombre) or 0.0)
                df_junto = pd.concat([df_fix, df_var_proj], ignore_index=True)
                coss_pro = float(df_junto.loc[df_junto["Clasificacion_A"] == "COSS", "Neto_A"].sum() or 0.0) + patio_pro
                gadm_pro = float(df_junto.loc[df_junto["Clasificacion_A"] == "G.ADMN", "Neto_A"].sum() or 0.0)

                uo = ingreso_proy - coss_pro - gadm_pro
                return float((uo / ingreso_proy) if abs(ingreso_proy) > 1e-9 else 0.0)
            real_pct = {}
            proy_pct = {}

            for nombre, codigo in zip(nombres, codigos):
                codigo_str = _norm_proy_code(codigo)
                codigo_list = [codigo_str]
                er_real = estado_resultado(df_real, meses_sel, nombre, codigo_list, list_pro)
                real_pct[nombre] = float(er_real.get("por_utilidad_operativa", 0) or 0.0)
                base = df_real if "df_real" in locals() and df_real is not None else df_real
                proy_pct[nombre] = calc_pct_uo_proy(
                    df_base=base,
                    fecha_actualizacion=fecha_actualizacion,
                    mes_act=mes_act,
                    mes_ant_lm=mes_ant_lm,
                    codigo_list=codigo_list,
                    pro_nombre=nombre if nombre != "ESGARI" else "ESGARI"
                )

            ppt_pct = {n: float(objetivo_uo.get(n, 0.0) or 0.0) for n in nombres}

            # ====== render ======
            st.subheader("Utilidad Operativa por Proyecto")

            tabla_excel = pd.DataFrame(
                {n: [ppt_pct.get(n, 0.0), real_pct.get(n, 0.0), proy_pct.get(n, 0.0)] for n in nombres},
                index=["PPT", "REAL", "PROYECTADO"]
            )

            st.dataframe(tabla_excel.style.format("{:.2%}"), use_container_width=True)

            fig = go.Figure()
            fig.add_bar(x=nombres, y=[ppt_pct[n] for n in nombres], name="PPT",
                        text=[f"{ppt_pct[n]*100:.2f}%" for n in nombres], textposition="inside")
            fig.add_bar(x=nombres, y=[real_pct[n] for n in nombres], name="REAL",
                        text=[f"{real_pct[n]*100:.2f}%" for n in nombres], textposition="inside")
            fig.add_bar(x=nombres, y=[proy_pct[n] for n in nombres], name="PROYECTADO",
                        text=[f"{proy_pct[n]*100:.2f}%" for n in nombres], textposition="inside")

            fig.update_layout(
                title="% Utilidad Operativa por Proyecto",
                xaxis_title="Proyecto",
                yaxis_title="Utilidad Operativa (%)",
                barmode="group",
                height=520,
                hovermode="x unified",
                xaxis_tickangle=-25
            )
            st.plotly_chart(fig, use_container_width=True, key="fig_uo_objetivos_tablero")


        def resumen_empresa(df_ppt, df_real):
            st.title("Resumen Presupuestal – ESGARI")
            c1, c2 = st.columns([4, 2])

            with c1:
                meses_ordenados = ["ene.","feb.","mar.","abr.","may.","jun.","jul.","ago.","sep.","oct.","nov.","dic."]
                meses_ppt  = df_ppt["Mes_A"].astype(str).str.strip().unique().tolist() if "Mes_A" in df_ppt.columns else []
                meses_real = df_real["Mes_A"].astype(str).str.strip().unique().tolist() if "Mes_A" in df_real.columns else []
                meses_disponibles = [m for m in meses_ordenados if (m in meses_ppt) or (m in meses_real)]
                default = meses_disponibles[-1:] if meses_disponibles else []

                meses_sel = st.multiselect(
                    "Mes(es)",
                    options=meses_disponibles,
                    default=default,
                    key="meses_empresa"
                )

            with c2:
                vista = st.selectbox("Vista", ["Real vs PPT"], index=0, key="vista_empresa")

            if not meses_sel:
                st.warning("Selecciona por lo menos un mes.")
                return None, []

            pro = "ESGARI"
            codigo_pro = []
            lista_proyectos = list_pro

            ing_ppt  = float(ingreso(df_ppt,  meses_sel, codigo_pro, pro) or 0.0)
            ing_real = float(ingreso(df_real, meses_sel, codigo_pro, pro) or 0.0)

            coss_ppt, _  = coss(df_ppt,  meses_sel, codigo_pro, pro, lista_proyectos)
            coss_real, _ = coss(df_real, meses_sel, codigo_pro, pro, lista_proyectos)
            coss_ppt  = float(coss_ppt or 0.0)
            coss_real = float(coss_real or 0.0)

            gadm_ppt, _  = gadmn(df_ppt,  meses_sel, codigo_pro, pro, lista_proyectos)
            gadm_real, _ = gadmn(df_real, meses_sel, codigo_pro, pro, lista_proyectos)
            gadm_ppt  = float(gadm_ppt or 0.0)
            gadm_real = float(gadm_real or 0.0)
            patio_ppt  = float(patio(df_ppt,  meses_sel, codigo_pro, pro) or 0.0)
            patio_real = float(patio(df_real, meses_sel, codigo_pro, pro) or 0.0)
            coss_total_ppt  = coss_ppt  + patio_ppt
            coss_total_real = coss_real + patio_real
            uo_ppt  = ing_ppt  - coss_total_ppt  - gadm_ppt
            uo_real = ing_real - coss_total_real - gadm_real

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Ingresos", fmt_mxn(ing_real), delta_pct(ing_real, ing_ppt))
            k2.metric("COSS total", fmt_mxn(coss_total_real), delta_pct(coss_total_real, coss_total_ppt))
            k3.metric("G. Adm", fmt_mxn(gadm_real), delta_pct(gadm_real, gadm_ppt))
            k4.metric("Utilidad Operativa", fmt_mxn(uo_real), delta_pct(uo_real, uo_ppt))
            k5.metric(
                "% UO",
                fmt_pct(uo_real / ing_real if ing_real else 0),
                f"{((uo_real/ing_real if ing_real else 0) - (uo_ppt/ing_ppt if ing_ppt else 0)) * 100:+.1f} pp"
            )

            st.divider()

            ing_pro  = float(st.session_state.get("PROY_ingreso_pro_fut", 0.0) or 0.0)
            coss_pro_total = float(st.session_state.get("PROY_coss_pro", 0.0) or 0.0)
            gadm_pro = float(st.session_state.get("PROY_gadmn_pro", 0.0) or 0.0)
            coss_total_pro = coss_pro_total
            uo_pro = ing_pro - coss_total_pro - gadm_pro

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Ingresos proyectado", fmt_mxn(ing_pro), delta_pct(ing_pro, ing_ppt))
            k2.metric("COSS total proyectado", fmt_mxn(coss_total_pro), delta_pct(coss_total_pro, coss_total_ppt))
            k3.metric("G. Adm proyectado", fmt_mxn(gadm_pro), delta_pct(gadm_pro, gadm_ppt))
            k4.metric("Utilidad Operativa proyectada", fmt_mxn(uo_pro), delta_pct(uo_pro, uo_ppt))
            k5.metric(
                "% UO proyectado",
                fmt_pct(uo_pro / ing_pro if ing_pro else 0),
                f"{((uo_pro/ing_pro if ing_pro else 0) - (uo_ppt/ing_ppt if ing_ppt else 0)) * 100:+.1f} pp"
            )

            st.divider()
            meses_ordenados = ["ene.","feb.","mar.","abr.","may.","jun.","jul.","ago.","sep.","oct.","nov.","dic."]
            orden = {m: i for i, m in enumerate(meses_ordenados)}
            meses_sel_ord = sorted(list(dict.fromkeys(meses_sel)), key=lambda x: orden.get(x, 999))

            def ingreso_por_mes(df, meses):
                out = []
                for m in meses:
                    out.append(float(ingreso(df, [m], [], "ESGARI") or 0.0))
                return out

            ing_ppt_mes  = ingreso_por_mes(df_ppt,  meses_sel_ord)
            ing_real_mes = ingreso_por_mes(df_real, meses_sel_ord)

            g1, g2 = st.columns([1.2, 1])

            with g1:
                fig = go.Figure()
                fig.add_trace(go.Bar(name="PPT",  x=meses_sel_ord, y=ing_ppt_mes))
                fig.add_trace(go.Bar(name="REAL", x=meses_sel_ord, y=ing_real_mes))
                fig.update_layout(barmode="group", height=360, title="Ingresos (PPT vs Real)")
                st.plotly_chart(fig, use_container_width=True, key="fig_ing_empresa")

            with g2:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=["COSS", "G. Adm", "Patio"],
                    y=[(coss_real - coss_ppt), (gadm_real - gadm_ppt), (patio_real - patio_ppt)]
                ))
                fig2.update_layout(height=360, title="Drivers de variación vs PPT")
                st.plotly_chart(fig2, use_container_width=True, key="fig_drivers_empresa")

            st.divider()
            df_res = pd.DataFrame([
                ["INGRESO", ing_ppt, ing_real],
                ["COSS total", coss_total_ppt, coss_total_real],
                ["G.ADMN", gadm_ppt, gadm_real],
                ["PATIO", patio_ppt, patio_real],  
                ["U. OPERATIVA", uo_ppt, uo_real],
            ], columns=["Rubro", "PPT", "REAL"])

            df_res["DIF"] = df_res["REAL"] - df_res["PPT"]
            df_res["DIF %"] = np.where(df_res["PPT"] != 0, (df_res["REAL"] / df_res["PPT"] - 1) * 100, 0.0)
            df_res["% sobre Ingreso (REAL)"] = np.where(ing_real != 0, (df_res["REAL"] / ing_real) * 100, 0.0)

            st.subheader("Resumen Ejecutivo (Empresa)")
            st.dataframe(
                df_res.style.format({
                    "PPT": "${:,.0f}",
                    "REAL": "${:,.0f}",
                    "DIF": "${:,.0f}",
                    "DIF %": "{:.2f}%",
                    "% sobre Ingreso (REAL)": "{:.2f}%"
                }),
                use_container_width=True
            )

            return df_res, meses_sel_ord

        # ---- ejecutar tablero
        df_res, meses_sel = resumen_empresa(df_ppt, df_real)

        st.divider()

        # ---- catálogo proyectos y tabla
        df_proyectos = proyectos.copy()
        df_proyectos["proyectos"] = df_proyectos["proyectos"].astype(str).str.strip()
        df_proyectos["nombre"] = df_proyectos["nombre"].astype(str).str.strip()

        tabla_proyectos(
            df_ppt=df_ppt,
            df_real=df_real,
            meses_seleccionado=meses_sel,
            df_proyectos=df_proyectos
        )
        st.divider()
        uo_objetivos_en_tablero(
            df_ppt=df_ppt,
            df_real=df_real,
            fecha_actualizacion=fecha_actualizacion,
            proyectos=proyectos,
            list_pro=list_pro,
            meses_sel=meses_sel
        )

    elif selected == "Ingresos":

        def tabla_ingresos(df_ppt, df_real, meses_seleccionado, proyectos_seleccionados):
            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return

            MESES_ORDENADOS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

            if not proyectos_seleccionados:
                st.error("Favor de seleccionar por lo menos un proyecto")
                return
            orden = {m: i for i, m in enumerate(MESES_ORDENADOS)}
            meses_sel = [str(m).strip() for m in meses_seleccionado]
            meses_sel = [m for m in meses_sel if m in orden]  # limpia valores raros
            meses_sel = sorted(list(dict.fromkeys(meses_sel)), key=lambda x: orden.get(x, 999))

            if not meses_sel:
                st.error("Los meses seleccionados no son válidos.")
                return

            def mes_anterior(m):
                i = orden.get(m, None)
                if i is None or i <= 0:
                    return None
                return MESES_ORDENADOS[i - 1]
            df_ppt_local  = df_ppt.copy()
            df_real_local = df_real.copy()

            for df_ in (df_ppt_local, df_real_local):
                df_["Proyecto_A"] = df_["Proyecto_A"].astype(str).str.replace(".0", "", regex=False).str.strip()
                df_["Mes_A"] = df_["Mes_A"].astype(str).str.strip()
                df_["Categoria_A"] = df_["Categoria_A"].astype(str).str.strip()
                df_["Neto_A"] = pd.to_numeric(df_["Neto_A"], errors="coerce").fillna(0.0)
            proyectos_sel = [str(p).replace(".0", "").strip() for p in proyectos_seleccionados]
            if not proyectos_sel:
                st.error("No se encontraron proyectos válidos.")
                return
            proyectos_ppt = proyectos_sel
            proyectos_real = proyectos_sel
            df_ppt_f = df_ppt_local[
                (df_ppt_local["Mes_A"].isin(meses_sel)) &
                (df_ppt_local["Proyecto_A"].isin(proyectos_ppt)) &
                (df_ppt_local["Categoria_A"] == "INGRESO")
            ].copy()

            df_real_f = df_real_local[
                (df_real_local["Mes_A"].isin(meses_sel)) &
                (df_real_local["Proyecto_A"].isin(proyectos_real)) &
                (df_real_local["Categoria_A"] == "INGRESO")
            ].copy()

            ppt_por_mes = (
                df_ppt_f.groupby("Mes_A", as_index=False)["Neto_A"].sum()
                .rename(columns={"Neto_A": "PPT"})
            )
            real_por_mes = (
                df_real_f.groupby("Mes_A", as_index=False)["Neto_A"].sum()
                .rename(columns={"Neto_A": "REAL"})
            )
            df_proy_hist = st.session_state.get("PROY_df_proyeccion", None)
            mes_act = st.session_state.get("PROY_mes_act", None)

            if df_proy_hist is not None:
                df_proy_hist = df_proy_hist.copy()
                if "Proyecto_A" in df_proy_hist.columns:
                    df_proy_hist["Proyecto_A"] = df_proy_hist["Proyecto_A"].astype(str).str.replace(".0", "", regex=False).str.strip()
                if "Mes_A" in df_proy_hist.columns:
                    df_proy_hist["Mes_A"] = df_proy_hist["Mes_A"].astype(str).str.strip()
                if "Neto_A" in df_proy_hist.columns:
                    df_proy_hist["Neto_A"] = pd.to_numeric(df_proy_hist["Neto_A"], errors="coerce").fillna(0.0)

            proy_rows = []
            for m in meses_sel:
                if mes_act is not None and m == str(mes_act).strip() and df_proy_hist is not None:
                    # PROY historico del mes actual
                    df_m = df_proy_hist.copy()

                    # si no trae Mes_A, se lo asignamos
                    if "Mes_A" in df_m.columns:
                        df_m = df_m[df_m["Mes_A"] == str(mes_act).strip()]
                    else:
                        df_m["Mes_A"] = str(mes_act).strip()

                    if "Proyecto_A" in df_m.columns:
                        df_m = df_m[df_m["Proyecto_A"].isin(proyectos_real)]

                    proy_val = float(df_m["Neto_A"].sum()) if (df_m is not None and not df_m.empty) else 0.0
                    proy_rows.append({"Mes_A": m, "PROYECTADO": proy_val})
                else:
                    # PROY = REAL del mes anterior
                    prev = mes_anterior(m)
                    if prev is None:
                        proy_rows.append({"Mes_A": m, "PROYECTADO": 0.0})
                        continue

                    df_prev = df_real_local[
                        (df_real_local["Mes_A"] == prev) &
                        (df_real_local["Proyecto_A"].isin(proyectos_real)) &
                        (df_real_local["Categoria_A"] == "INGRESO")
                    ].copy()

                    proy_val = float(df_prev["Neto_A"].sum()) if not df_prev.empty else 0.0
                    proy_rows.append({"Mes_A": m, "PROYECTADO": proy_val})

            proy_por_mes = pd.DataFrame(proy_rows)
            tabla = (
                pd.DataFrame({"Mes_A": meses_sel})
                .merge(ppt_por_mes, on="Mes_A", how="left")
                .merge(real_por_mes, on="Mes_A", how="left")
                .merge(proy_por_mes, on="Mes_A", how="left")
                .fillna(0.0)
            )

            tabla["DIF REAL"] = tabla["REAL"] - tabla["PPT"]
            tabla["DIF PROYECTADO"] = tabla["PROYECTADO"] - tabla["PPT"]

            tabla["% REAL"] = np.where(tabla["PPT"] != 0, (tabla["REAL"] / tabla["PPT"] - 1), 0.0)
            tabla["% PROYECTADO"] = np.where(tabla["PPT"] != 0, (tabla["PROYECTADO"] / tabla["PPT"] - 1), 0.0)

            # Orden meses (solo seleccionados)
            tabla["__ord"] = tabla["Mes_A"].map(orden).fillna(999).astype(int)
            tabla = tabla.sort_values("__ord").drop(columns="__ord")

            # Total
            total_ppt = float(tabla["PPT"].sum())
            total_real = float(tabla["REAL"].sum())
            total_proy = float(tabla["PROYECTADO"].sum())

            total_row = pd.DataFrame([{
                "Mes_A": "TOTAL",
                "PPT": total_ppt,
                "REAL": total_real,
                "PROYECTADO": total_proy,
                "DIF REAL": total_real - total_ppt,
                "DIF PROYECTADO": total_proy - total_ppt,
                "% REAL": (total_real / total_ppt - 1) if total_ppt != 0 else 0.0,
                "% PROYECTADO": (total_proy / total_ppt - 1) if total_ppt != 0 else 0.0
            }])

            tabla_final = pd.concat([tabla, total_row], ignore_index=True)

            BLUE = "#00112B"
            styled = (
                tabla_final.style
                .set_table_styles([
                    {"selector": "thead th",
                    "props": f"background-color: {BLUE}; color: white; font-weight: 700; font-size: 14px;"},
                    {"selector": "tbody td", "props": "font-size: 13px;"},
                ])
                .format({
                    "PPT": "${:,.2f}",
                    "REAL": "${:,.2f}",
                    "PROYECTADO": "${:,.2f}",
                    "DIF REAL": "${:,.2f}",
                    "DIF PROYECTADO": "${:,.2f}",
                    "% REAL": "{:.2%}",
                    "% PROYECTADO": "{:.2%}",
                })
            )

            st.subheader("Ingresos YTD")
            st.dataframe(styled, use_container_width=True)

            # Para graficar sin TOTAL
            tabla_plot = tabla.copy()

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=tabla_plot["Mes_A"],
                y=tabla_plot["PPT"] / 1000,
                name="Ingreso PPT",
                text=(tabla_plot["PPT"] / 1000).round(1),
                texttemplate="%{text}k",
                textposition="outside"
            ))
            fig.add_trace(go.Bar(
                x=tabla_plot["Mes_A"],
                y=tabla_plot["REAL"] / 1000,
                name="Ingreso REAL",
                text=(tabla_plot["REAL"] / 1000).round(1),
                texttemplate="%{text}k",
                textposition="outside"
            ))
            fig.add_trace(go.Bar(
                x=tabla_plot["Mes_A"],
                y=tabla_plot["PROYECTADO"] / 1000,
                name="Ingreso PROYECTADO",
                text=(tabla_plot["PROYECTADO"] / 1000).round(1),
                texttemplate="%{text}k",
                textposition="outside"
            ))
            fig.update_layout(
                title="Ingreso PPT vs REAL vs PROYECTADO",
                xaxis_title="Mes",
                yaxis_title="Ingreso (miles)",
                barmode="group",
                hovermode="x unified",
                legend_title="Tipo",
                height=420,
                yaxis=dict(tickformat=",.0f", ticksuffix="k")
            )
            st.plotly_chart(fig, use_container_width=True)

            # Línea
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=tabla_plot["Mes_A"],
                y=tabla_plot["PPT"] / 1000,
                mode="lines+markers+text",
                name="Ingreso PPT",
                text=[f"{v:,.1f}k" for v in (tabla_plot["PPT"] / 1000)],
                textposition="top center"
            ))
            fig_line.add_trace(go.Scatter(
                x=tabla_plot["Mes_A"],
                y=tabla_plot["REAL"] / 1000,
                mode="lines+markers+text",
                name="Ingreso REAL",
                text=[f"{v:,.1f}k" for v in (tabla_plot["REAL"] / 1000)],
                textposition="top center"
            ))
            fig_line.add_trace(go.Scatter(
                x=tabla_plot["Mes_A"],
                y=tabla_plot["PROYECTADO"] / 1000,
                mode="lines+markers+text",
                name="Ingreso PROYECTADO",
                text=[f"{v:,.1f}k" for v in (tabla_plot["PROYECTADO"] / 1000)],
                textposition="top center"
            ))
            fig_line.update_layout(
                title="Ingreso PPT vs REAL vs PROYECTADO (Línea)",
                xaxis_title="Mes",
                yaxis_title="Ingreso (miles)",
                hovermode="x unified",
                height=420,
                yaxis=dict(tickformat=",.0f", ticksuffix="k"),
                uniformtext_minsize=10,
                uniformtext_mode="hide",
                margin=dict(t=70)
            )
            st.plotly_chart(fig_line, use_container_width=True)

            return tabla_final
        col1, col2 = st.columns(2)
        MESES_ORDENADOS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        df_ppt_tmp = df_ppt.copy()
        df_real_tmp = df_real.copy()
        df_ppt_tmp["Mes_A"] = df_ppt_tmp["Mes_A"].astype(str).str.strip()
        df_real_tmp["Mes_A"] = df_real_tmp["Mes_A"].astype(str).str.strip()

        meses_ppt = set(df_ppt_tmp["Mes_A"].unique().tolist())
        meses_real = set(df_real_tmp["Mes_A"].unique().tolist())
        meses_disponibles = [m for m in MESES_ORDENADOS if (m in meses_ppt) or (m in meses_real)]

        with col1:
            meses_seleccionado = st.multiselect(
                "Selecciona un mes",
                options=meses_disponibles,
                default=meses_disponibles[-1:] if meses_disponibles else [],
                key="ingresos_meses_chip"
            )

        with col2:
            proyecto_codigo, proyecto_nombre = filtro_pro(col2)

        tabla_ingresos(df_ppt, df_real, meses_seleccionado, proyecto_codigo)


    elif selected == "OH":

        def tabla_oh_ppt_vs_real(df_ppt, df_real, meses_seleccionado, cecos_seleccionados):
            MESES_ORDENADOS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return None

            if not cecos_seleccionados:
                st.error("Favor de seleccionar por lo menos un ceco")
                return None
            proyectos_oh = ["8002", "8004"]
            clas_oh = ["COSS", "G.ADMN"]
            meses_sel = [str(m).strip() for m in meses_seleccionado if str(m).strip() != ""]
            orden = {m: i for i, m in enumerate(MESES_ORDENADOS)}
            meses_sel = sorted(list(set(meses_sel)), key=lambda x: orden.get(x, 999))
            def mes_anterior(m):
                i = orden.get(m, None)
                if i is None:
                    return None
                return MESES_ORDENADOS[(i - 1) % len(MESES_ORDENADOS)]
            meses_prev = [mes_anterior(m) for m in meses_sel]
            meses_prev = [m for m in meses_prev if m is not None]
            meses_para_real = sorted(list(set(meses_sel + meses_prev)), key=lambda x: orden.get(x, 999))
            df_ppt_f = df_ppt[
                (df_ppt["Mes_A"].astype(str).str.strip().isin(meses_sel)) &
                (df_ppt["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                (df_ppt["Clasificacion_A"].astype(str).isin(clas_oh)) &
                (df_ppt["CeCo_A"].astype(str).isin([str(x) for x in cecos_seleccionados]))
            ].copy()
            df_real_f_all = df_real[
                (df_real["Mes_A"].astype(str).str.strip().isin(meses_para_real)) &
                (df_real["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                (df_real["Clasificacion_A"].astype(str).isin(clas_oh)) &
                (df_real["CeCo_A"].astype(str).isin([str(x) for x in cecos_seleccionados]))
            ].copy()

            # Agregados
            ppt_por_mes = (
                df_ppt_f.groupby("Mes_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "OH PPT"})
            )
            real_all_por_mes = (
                df_real_f_all.groupby("Mes_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "OH REAL"})
            )
            real_sel_por_mes = real_all_por_mes[real_all_por_mes["Mes_A"].isin(meses_sel)].copy()
            tabla = ppt_por_mes.merge(real_sel_por_mes, on="Mes_A", how="outer").fillna(0)
            tabla["__ord"] = tabla["Mes_A"].map(orden).fillna(999).astype(int)
            tabla = tabla.sort_values("__ord").drop(columns="__ord").reset_index(drop=True)
            real_lookup = dict(zip(real_all_por_mes["Mes_A"], real_all_por_mes["OH REAL"]))
            tabla["OH PROYECTADO"] = tabla["Mes_A"].apply(
                lambda m: float(real_lookup.get(mes_anterior(m), 0.0)) if mes_anterior(m) else 0.0
            )
            tabla["DIF REAL"] = tabla["OH REAL"] - tabla["OH PPT"]
            tabla["DIF PROYECTADO"] = tabla["OH PROYECTADO"] - tabla["OH PPT"]
            tabla["% REAL"] = tabla.apply(
                lambda r: (r["OH REAL"] / r["OH PPT"] - 1) if r["OH PPT"] != 0 else 0,
                axis=1
            )
            tabla["% PROYECTADO"] = tabla.apply(
                lambda r: (r["OH PROYECTADO"] / r["OH PPT"] - 1) if r["OH PPT"] != 0 else 0,
                axis=1
            )

            total_ppt = float(tabla["OH PPT"].sum())
            total_real = float(tabla["OH REAL"].sum())
            total_proy = float(tabla["OH PROYECTADO"].sum())
            total_dif_real = float(tabla["DIF REAL"].sum())
            total_dif_proy = float(tabla["DIF PROYECTADO"].sum())
            total_pct_real = (total_real / total_ppt - 1) if total_ppt != 0 else 0
            total_pct_proy = (total_proy / total_ppt - 1) if total_ppt != 0 else 0

            total_row = pd.DataFrame([{
                "Mes_A": "TOTAL",
                "OH PPT": total_ppt,
                "OH REAL": total_real,
                "OH PROYECTADO": total_proy,
                "DIF REAL": total_dif_real,
                "DIF PROYECTADO": total_dif_proy,
                "% REAL": total_pct_real,
                "% PROYECTADO": total_pct_proy
            }])

            tabla_final = pd.concat([tabla, total_row], ignore_index=True)
            BLUE = "#00112B"
            styled = (
                tabla_final.style
                .set_table_styles([
                    {"selector": "thead th",
                    "props": f"background-color: {BLUE}; color: white; font-weight: 700; font-size: 14px;"},
                    {"selector": "tbody td", "props": "font-size: 13px;"},
                ])
                .format({
                    "OH PPT": "${:,.2f}",
                    "OH REAL": "${:,.2f}",
                    "OH PROYECTADO": "${:,.2f}",
                    "DIF REAL": "${:,.2f}",
                    "DIF PROYECTADO": "${:,.2f}",
                    "% REAL": "{:.2%}",
                    "% PROYECTADO": "{:.2%}",
                })
            )

            st.subheader("OH — PPT vs REAL")
            st.dataframe(styled, use_container_width=True)
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=tabla["Mes_A"],
                y=tabla["OH PPT"] / 1000,
                name="PPT",
                text=(tabla["OH PPT"] / 1000).round(1),
                texttemplate="%{text}k",
                textposition="outside"
            ))

            fig.add_trace(go.Bar(
                x=tabla["Mes_A"],
                y=tabla["OH REAL"] / 1000,
                name="REAL",
                text=(tabla["OH REAL"] / 1000).round(1),
                texttemplate="%{text}k",
                textposition="outside"
            ))

            fig.add_trace(go.Bar(
                x=tabla["Mes_A"],
                y=tabla["OH PROYECTADO"] / 1000,
                name="PROYECTADO",
                text=(tabla["OH PROYECTADO"] / 1000).round(1),
                texttemplate="%{text}k",
                textposition="outside"
            ))

            fig.update_layout(
                title="OH PPT vs REAL",
                xaxis_title="Mes",
                yaxis_title="Monto (miles)",
                barmode="group",
                height=420,
                legend_title="Tipo",
                yaxis=dict(
                    tickformat=",.0f",
                    ticksuffix="k"
                )
            )

            st.plotly_chart(fig, use_container_width=True)
            return tabla_final


        def agrid_oh_con_totales(df, filtro_col, filtro_val):
            df = df.copy()
            df = df[df[filtro_col] == filtro_val]
            df_g = (
                df.groupby(["Clasificacion_A", "Categoria_A", "Cuenta_A", "Cuenta_Nombre_A"], as_index=False)
                .agg({"Neto_A": "sum"})
            )
            tot_cuenta = (
                df_g.groupby(["Cuenta_A", "Cuenta_Nombre_A"], as_index=False)["Neto_A"]
                    .sum()
                    .rename(columns={"Neto_A": "Total Cuenta"})
            )
            df_g = df_g.merge(tot_cuenta, on=["Cuenta_A", "Cuenta_Nombre_A"], how="left")

            currency_formatter = JsCode("""
            function(params) {
                if (params.value === null || params.value === undefined) return "";
                return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(params.value);
            }
            """)

            gb = GridOptionsBuilder.from_dataframe(df_g)
            gb.configure_default_column(resizable=True, sortable=True, filter=True)
            gb.configure_column("Clasificacion_A", rowGroup=True, hide=True)
            gb.configure_column("Categoria_A", rowGroup=True, hide=True)
            gb.configure_column("Cuenta_A", header_name="Cuenta", pinned="left")
            gb.configure_column("Cuenta_Nombre_A", header_name="Cuenta Nombre", pinned="left")

            for col in df_g.columns:
                if col not in ["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"]:
                    gb.configure_column(
                        col,
                        type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                        aggFunc="sum",
                        valueFormatter=currency_formatter,
                        cellStyle={'textAlign': 'right'}
                    )

            grid_options = gb.build()
            grid_options.update({
                "groupDisplayType": "groupRows",
                "groupDefaultExpanded": 1,
                "suppressAggFuncInHeader": False
            })

            AgGrid(
                df_g,
                gridOptions=grid_options,
                enable_enterprise_modules=True,
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=True,
                height=520,
                theme="streamlit",
                key=f"agrid_oh_totales_{filtro_col}_{filtro_val}"
            )


        col1, col2 = st.columns(2)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        ceco_codigo, ceco_nombre = filtro_ceco(col2)

        tabla_oh_ppt_vs_real(df_ppt, df_real, meses_seleccionado, ceco_codigo)

        proyectos_oh = ["8002", "8004"]

        if meses_seleccionado and ceco_codigo:
            df_agrid_oh = df_ppt[
                (df_ppt["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                (df_ppt["CeCo_A"].astype(str).isin([str(x) for x in ceco_codigo]))
            ].copy()

            df_actual_oh = df_real[
                (df_real["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                (df_real["CeCo_A"].astype(str).isin([str(x) for x in ceco_codigo]))
            ].copy()

            ventanas = ["COSS", "G.ADMN"]
            tabs = st.tabs(ventanas)

            with tabs[0]:
                tabla_comparativa(
                    df_agrid_oh,
                    df_actual_oh,
                    proyectos_oh,
                    meses_seleccionado,
                    "Clasificacion_A",
                    "COSS",
                    "OH - Tabla COSS"
                )

            with tabs[1]:
                tabla_comparativa(
                    df_agrid_oh,
                    df_actual_oh,
                    proyectos_oh,
                    meses_seleccionado,
                    "Clasificacion_A",
                    "G.ADMN",
                    "OH - Tabla G.ADMN"
                )

    elif selected == "Departamentos":

        def tabla_departamentos(df_ppt, df_real, meses_seleccionado, cecos_seleccionados, df_cecos, ceco_nombre=None):
            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return None

            if not cecos_seleccionados:
                st.error("Favor de seleccionar por lo menos un ceco")
                return None

            proyectos_oh = ["8002", "8004"]
            clas_oh = ["COSS", "G.ADMN"]

            df_ppt = df_ppt.copy()
            df_real = df_real.copy()

            for df in (df_ppt, df_real):
                df["Proyecto_A"] = df["Proyecto_A"].astype(str).str.strip()
                df["CeCo_A"] = df["CeCo_A"].astype(str).str.strip()
                df["Mes_A"] = df["Mes_A"].astype(str).str.strip()
                df["Clasificacion_A"] = df["Clasificacion_A"].astype(str).str.strip()
                if "Categoria_A" in df.columns:
                    df["Categoria_A"] = df["Categoria_A"].astype(str).str.strip()

                df["Neto_A"] = pd.to_numeric(df["Neto_A"], errors="coerce").fillna(0.0)

            cecos_sel = [str(x).strip() for x in cecos_seleccionados]
            df_ppt_f = df_ppt[
                (df_ppt["Mes_A"].isin(meses_seleccionado)) &
                (df_ppt["Proyecto_A"].isin(proyectos_oh)) &
                (df_ppt["Clasificacion_A"].isin(clas_oh)) &
                (df_ppt["CeCo_A"].isin(cecos_sel))
            ].copy()

            df_real_f = df_real[
                (df_real["Mes_A"].isin(meses_seleccionado)) &
                (df_real["Proyecto_A"].isin(proyectos_oh)) &
                (df_real["Clasificacion_A"].isin(clas_oh)) &
                (df_real["CeCo_A"].isin(cecos_sel))
            ].copy()

            ppt_por_ceco = (
                df_ppt_f.groupby("CeCo_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "PPT"})
            )

            real_por_ceco = (
                df_real_f.groupby("CeCo_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "REAL"})
            )

            tabla = ppt_por_ceco.merge(real_por_ceco, on="CeCo_A", how="outer").fillna(0)
            tabla["DIF"] = tabla["REAL"] - tabla["PPT"]
            tabla["%"] = np.where(tabla["PPT"] != 0, (tabla["REAL"] / tabla["PPT"]) - 1, 0.0)

            if "Categoria_A" in df_real.columns:
                df_ing_real_total = df_real[
                    (df_real["Mes_A"].isin(meses_seleccionado)) &
                    (df_real["Categoria_A"] == "INGRESO")
                ].copy()
                ingreso_real_esgari = float(df_ing_real_total["Neto_A"].sum())
            else:
                ingreso_real_esgari = 0.0
            tabla["% s/ ingreso"] = np.where(
                ingreso_real_esgari != 0,
                tabla["DIF"] / ingreso_real_esgari,
                0.0
            )

            df_cecos_map = df_cecos.copy()
            df_cecos_map["ceco"] = df_cecos_map["ceco"].astype(str).str.strip()
            df_cecos_map["nombre"] = df_cecos_map["nombre"].astype(str).str.strip()

            cecos_map = (
                df_cecos_map[df_cecos_map["ceco"].isin(cecos_sel)][["ceco", "nombre"]]
                .drop_duplicates()
            )

            tabla = tabla.merge(
                cecos_map.rename(columns={"ceco": "CeCo_A", "nombre": "ceco"}),
                on="CeCo_A",
                how="left"
            )

            tabla["ceco"] = tabla["ceco"].fillna(tabla["CeCo_A"])
            tabla = tabla[["ceco", "REAL", "PPT", "DIF", "%", "% s/ ingreso"]]

            total_ppt = float(tabla["PPT"].sum())
            total_real = float(tabla["REAL"].sum())
            total_dif = total_real - total_ppt
            total_pct = (total_real / total_ppt - 1) if total_ppt != 0 else 0.0
            total_pct_s_ing = (total_dif / ingreso_real_esgari) if ingreso_real_esgari != 0 else 0.0

            total_row = pd.DataFrame([{
                "ceco": "TOTAL",
                "REAL": total_real,
                "PPT": total_ppt,
                "DIF": total_dif,
                "%": total_pct,
                "% s/ ingreso": total_pct_s_ing
            }])

            tabla_final = pd.concat([tabla, total_row], ignore_index=True)

            def color_fila(row):
                if row["ceco"] == "TOTAL":
                    return ["background-color:#FFFFFF;color:black;font-weight:bold"] * len(row)

                v = float(row["%"]) if pd.notnull(row["%"]) else 0.0
                bg = "#FFFFFF"

                if v <= 0:
                    bg = "#92D050"   # verde
                elif v >= 0.10:
                    bg = "#FF0000"   # rojo

                return [f"background-color:{bg};color:black"] * len(row)

            st.markdown("""
                <style>
                div[data-testid="stDataFrame"] thead tr th {
                    background-color: #f7f6f1 !important;
                    color: black !important;
                    font-weight: 800 !important;
                }
                </style>
            """, unsafe_allow_html=True)

            st.subheader("Departamentos OH")
            st.dataframe(
                tabla_final.style
                    .apply(color_fila, axis=1)
                    .format({
                        "REAL": "${:,.2f}",
                        "PPT": "${:,.2f}",
                        "DIF": "${:,.2f}",
                        "%": "{:.2%}",
                        "% s/ ingreso": "{:.2%}",
                    }),
                use_container_width=True,
                height=520
            )

            tabla_graf = tabla_final[tabla_final["ceco"] != "TOTAL"].copy()

            if not tabla_graf.empty:
                tabla_graf["ceco"] = tabla_graf["ceco"].astype(str)
                es_esgari = str(ceco_nombre).strip().upper() == "ESGARI"

                fig = go.Figure()

                fig.add_bar(
                    x=tabla_graf["ceco"],
                    y=tabla_graf["REAL"],
                    name="REAL",
                    text=[f"${v:,.0f}" for v in tabla_graf["REAL"]],
                    textposition="outside",
                    texttemplate="%{text}",
                    cliponaxis=False,
                )

                fig.add_bar(
                    x=tabla_graf["ceco"],
                    y=tabla_graf["PPT"],
                    name="PPT",
                    text=[f"${v:,.0f}" for v in tabla_graf["PPT"]],
                    textposition="outside",
                    texttemplate="%{text}",
                    cliponaxis=False,
                )

                y_max = float(max(tabla_graf["REAL"].max(), tabla_graf["PPT"].max()) or 0.0)
                y_range_max = y_max * (1.30 if es_esgari else 1.18) if y_max > 0 else 1

                fig.update_layout(
                    title="Departamentos — REAL vs PPT",
                    xaxis_title="CeCo",
                    yaxis_title="MXN",
                    barmode="group",
                    height=(700 if es_esgari else 520),  
                    hovermode="x unified",
                    xaxis_tickangle=(-45 if es_esgari else -25), 
                    yaxis=dict(range=[0, y_range_max]),
                    margin=dict(t=90, b=140 if es_esgari else 80),  
                )

                if es_esgari:
                    fig.update_traces(textposition="outside")
                    fig.update_layout(
                        uniformtext_minsize=8,
                        uniformtext_mode="show"   
                    )
                else:
                    fig.update_layout(
                        uniformtext_minsize=10,
                        uniformtext_mode="hide"
                    )

                st.markdown("Gráfico Departamentos")
                st.plotly_chart(fig, use_container_width=True)

            return tabla_final


        col1, col2 = st.columns(2)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        ceco_codigo, ceco_nombre = filtro_ceco(col2)

        df_cecos = cargar_datos(cecos_url)
        df_cecos["ceco"] = df_cecos["ceco"].astype(str).str.strip()
        df_cecos["nombre"] = df_cecos["nombre"].astype(str).str.strip()

        tabla_final = tabla_departamentos(
            df_ppt=df_ppt,
            df_real=df_real,
            meses_seleccionado=meses_seleccionado,
            cecos_seleccionados=ceco_codigo,
            df_cecos=df_cecos,
            ceco_nombre=ceco_nombre  
        )


    elif selected == "Proyectos":

        def filtro_proyectos_esgari(col, proyectos_oh):
            proyectos_local = proyectos.copy()
            proyectos_local["proyectos"] = proyectos_local["proyectos"].astype(str).str.strip()
            proyectos_local["nombre"] = proyectos_local["nombre"].astype(str).str.strip()

            proyectos_oh_set = set([str(x).strip() for x in proyectos_oh])
            allowed = [str(x).strip() for x in st.session_state.get("proyectos", [])]

            def _excluir_oh(df):
                return df[~df["proyectos"].isin(proyectos_oh_set)].copy()

            if allowed == ["ESGARI"]:
                df_visibles = _excluir_oh(proyectos_local)
                if df_visibles.empty:
                    st.error("No hay proyectos visibles (después de excluir proyectos OH).")
                    st.stop()

                opciones = ["ESGARI"] + df_visibles["nombre"].dropna().tolist()
                proyecto_nombre = col.selectbox("Selecciona un proyecto", opciones, key="proyectos2_select")

                if proyecto_nombre == "ESGARI":
                    proyecto_codigo = df_visibles["proyectos"].astype(str).tolist()
                else:
                    proyecto_codigo = df_visibles.loc[
                        df_visibles["nombre"] == proyecto_nombre, "proyectos"
                    ].astype(str).tolist()

            else:
                df_visibles = proyectos_local[proyectos_local["proyectos"].isin(allowed)].copy()
                df_visibles = _excluir_oh(df_visibles)

                if df_visibles.empty:
                    st.error("No hay proyectos visibles para este usuario")
                    st.stop()

                opciones = ["ESGARI"] + df_visibles["nombre"].dropna().unique().tolist()
                proyecto_nombre = col.selectbox("Selecciona un proyecto", opciones, key="proyectos2_select")

                if proyecto_nombre == "ESGARI":
                    proyecto_codigo = df_visibles["proyectos"].astype(str).tolist()
                else:
                    proyecto_codigo = df_visibles.loc[
                        df_visibles["nombre"] == proyecto_nombre, "proyectos"
                    ].astype(str).tolist()

            if not proyecto_codigo:
                st.error("No se encontró código para el proyecto seleccionado")
                st.stop()

            return proyecto_codigo, proyecto_nombre


        def tabla_proyecto2(df_ppt, df_real, meses_seleccionado, cecos_seleccionados, proyectos_seleccionados, df_cecos):
            MESES_ORDENADOS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
            orden = {m: i for i, m in enumerate(MESES_ORDENADOS)}

            if isinstance(meses_seleccionado, str):
                meses_sel = [meses_seleccionado.strip()]
            else:
                meses_sel = [str(m).strip() for m in (meses_seleccionado or []) if str(m).strip()]

            meses_sel = sorted(list(dict.fromkeys(meses_sel)), key=lambda x: orden.get(x, 999))

            if isinstance(cecos_seleccionados, str):
                cecos_sel = [cecos_seleccionados.strip()]
            else:
                cecos_sel = [str(x).strip() for x in (cecos_seleccionados or []) if str(x).strip()]

            proyectos_sel = [str(x).strip() for x in (proyectos_seleccionados or []) if str(x).strip()]

            if not meses_sel:
                st.error("Favor de seleccionar por lo menos un mes")
                return None, None

            if not cecos_sel:
                st.error("Favor de seleccionar por lo menos un ceco")
                return None, None

            if not proyectos_sel:
                st.error("Favor de seleccionar por lo menos un proyecto")
                return None, None

            proyectos_oh = ["8002", "8003", "8004"]
            clas_oh = ["COSS", "G.ADMN"]

            proyectos_sel = [p for p in proyectos_sel if p not in set([str(x) for x in proyectos_oh])]

            if not proyectos_sel:
                st.info("No hay proyectos válidos (se excluyeron proyectos OH).")
                return None, None

            df_ppt = df_ppt.copy()
            df_real = df_real.copy()

            for df in (df_ppt, df_real):
                df["Proyecto_A"] = df["Proyecto_A"].astype(str).str.strip().str.replace(".0", "", regex=False)
                df["CeCo_A"] = df["CeCo_A"].astype(str).str.strip()
                df["Mes_A"] = df["Mes_A"].astype(str).str.strip()
                df["Clasificacion_A"] = df["Clasificacion_A"].astype(str).str.strip()
                if "Categoria_A" in df.columns:
                    df["Categoria_A"] = df["Categoria_A"].astype(str).str.strip()
                df["Neto_A"] = pd.to_numeric(df["Neto_A"], errors="coerce").fillna(0.0)

            df_ppt_f = df_ppt[
                (df_ppt["Mes_A"].isin(meses_sel)) &
                (df_ppt["Proyecto_A"].isin(proyectos_sel)) &
                (df_ppt["Clasificacion_A"].isin(clas_oh)) &
                (df_ppt["CeCo_A"].isin(cecos_sel))
            ].copy()

            df_real_f = df_real[
                (df_real["Mes_A"].isin(meses_sel)) &
                (df_real["Proyecto_A"].isin(proyectos_sel)) &
                (df_real["Clasificacion_A"].isin(clas_oh)) &
                (df_real["CeCo_A"].isin(cecos_sel))
            ].copy()

            ing_real_total = float(
                df_real[
                    (df_real["Mes_A"].isin(meses_sel)) &
                    (df_real["Proyecto_A"].isin(proyectos_sel)) &
                    (df_real.get("Categoria_A", "") == "INGRESO")
                ]["Neto_A"].sum()
            ) if "Categoria_A" in df_real.columns else 0.0

            ing_ppt_total = float(
                df_ppt[
                    (df_ppt["Mes_A"].isin(meses_sel)) &
                    (df_ppt["Proyecto_A"].isin(proyectos_sel)) &
                    (df_ppt.get("Categoria_A", "") == "INGRESO")
                ]["Neto_A"].sum()
            ) if "Categoria_A" in df_ppt.columns else 0.0

            def _pivot_clas(df_in, col_value_name):
                cols_out = ["CeCo_A", f"{col_value_name}_GADM", f"{col_value_name}_COSS"]
                if df_in.empty:
                    return pd.DataFrame({
                        "CeCo_A": pd.Series([], dtype=str),
                        f"{col_value_name}_GADM": pd.Series([], dtype=float),
                        f"{col_value_name}_COSS": pd.Series([], dtype=float),
                    })[cols_out]

                tmp = df_in.groupby(["CeCo_A", "Clasificacion_A"], as_index=False)["Neto_A"].sum()
                piv = tmp.pivot(index="CeCo_A", columns="Clasificacion_A", values="Neto_A").fillna(0.0).reset_index()

                if "G.ADMN" not in piv.columns:
                    piv["G.ADMN"] = 0.0
                if "COSS" not in piv.columns:
                    piv["COSS"] = 0.0

                piv = piv[["CeCo_A", "G.ADMN", "COSS"]].copy()
                piv = piv.rename(columns={
                    "G.ADMN": f"{col_value_name}_GADM",
                    "COSS": f"{col_value_name}_COSS"
                })
                return piv[cols_out]

            ppt_piv = _pivot_clas(df_ppt_f, "PPT")
            real_piv = _pivot_clas(df_real_f, "REAL")
            base = ppt_piv.merge(real_piv, on="CeCo_A", how="outer").fillna(0.0)

            df_cecos_map = df_cecos.copy()
            df_cecos_map["ceco"] = df_cecos_map["ceco"].astype(str).str.strip()
            df_cecos_map["nombre"] = df_cecos_map["nombre"].astype(str).str.strip()

            cecos_map = df_cecos_map[df_cecos_map["ceco"].isin(cecos_sel)][["ceco", "nombre"]].drop_duplicates()

            base = base.merge(
                cecos_map.rename(columns={"ceco": "CeCo_A", "nombre": "ceco"}),
                on="CeCo_A",
                how="left"
            )
            base["ceco"] = base["ceco"].fillna(base["CeCo_A"])

            t1 = base[["ceco", "REAL_GADM", "PPT_GADM", "REAL_COSS", "PPT_COSS"]].copy()
            t1["DIF GADM"] = t1["REAL_GADM"] - t1["PPT_GADM"]
            t1["DIF COSS"] = t1["REAL_COSS"] - t1["PPT_COSS"]

            t1 = t1.rename(columns={
                "REAL_GADM": "GADM. REAL",
                "PPT_GADM":  "GADM. PPT",
                "REAL_COSS": "COSS REAL",
                "PPT_COSS":  "COSS PPT",
            })[["ceco", "GADM. REAL", "GADM. PPT", "DIF GADM", "COSS REAL", "COSS PPT", "DIF COSS"]]

            total_1 = pd.DataFrame([{
                "ceco": "TOTAL",
                "GADM. REAL": float(t1["GADM. REAL"].sum()),
                "GADM. PPT":  float(t1["GADM. PPT"].sum()),
                "DIF GADM":   float(t1["DIF GADM"].sum()),
                "COSS REAL":  float(t1["COSS REAL"].sum()),
                "COSS PPT":   float(t1["COSS PPT"].sum()),
                "DIF COSS":   float(t1["DIF COSS"].sum()),
            }])
            tabla_nominal = pd.concat([t1, total_1], ignore_index=True)
            t2 = pd.DataFrame()
            t2["ceco"] = base["ceco"]

            t2["GADM REAL %"] = (base["REAL_GADM"] / ing_real_total) if ing_real_total != 0 else 0.0
            t2["GADM PPT %"]  = (base["PPT_GADM"]  / ing_ppt_total)  if ing_ppt_total  != 0 else 0.0
            t2["DIF GADM %"]  = ((base["REAL_GADM"] - base["PPT_GADM"]) / ing_real_total) if ing_real_total != 0 else 0.0

            t2["COSS REAL %"] = (base["REAL_COSS"] / ing_real_total) if ing_real_total != 0 else 0.0
            t2["COSS PPT %"]  = (base["PPT_COSS"]  / ing_ppt_total)  if ing_ppt_total  != 0 else 0.0
            t2["DIF COSS %"]  = ((base["REAL_COSS"] - base["PPT_COSS"]) / ing_real_total) if ing_real_total != 0 else 0.0

            total_2 = pd.DataFrame([{
                "ceco": "TOTAL",
                "GADM REAL %": (float(base["REAL_GADM"].sum()) / ing_real_total) if ing_real_total != 0 else 0.0,
                "GADM PPT %":  (float(base["PPT_GADM"].sum())  / ing_ppt_total)  if ing_ppt_total  != 0 else 0.0,
                "DIF GADM %":  ((float(base["REAL_GADM"].sum()) - float(base["PPT_GADM"].sum())) / ing_real_total) if ing_real_total != 0 else 0.0,
                "COSS REAL %": (float(base["REAL_COSS"].sum()) / ing_real_total) if ing_real_total != 0 else 0.0,
                "COSS PPT %":  (float(base["PPT_COSS"].sum())  / ing_ppt_total)  if ing_ppt_total  != 0 else 0.0,
                "DIF COSS %":  ((float(base["REAL_COSS"].sum()) - float(base["PPT_COSS"].sum())) / ing_real_total) if ing_real_total != 0 else 0.0,
            }])
            tabla_porcentaje = pd.concat([t2, total_2], ignore_index=True)

            if df_ppt_f.empty and df_real_f.empty and ing_real_total == 0 and ing_ppt_total == 0:
                st.warning("Sin datos para los filtros seleccionados (Mes/Proyecto/CeCo).")
                with st.expander("Ver diagnóstico"):
                    st.write("Meses:", meses_sel)
                    st.write("CeCos:", cecos_sel)
                    st.write("Proyectos:", proyectos_sel[:20], "..." if len(proyectos_sel) > 20 else "")
                    st.write("Filas PPT OH:", int(len(df_ppt_f)))
                    st.write("Filas REAL OH:", int(len(df_real_f)))
                    st.write("Ingreso REAL total:", ing_real_total)
                    st.write("Ingreso PPT total:", ing_ppt_total)

            st.markdown("""
                <style>
                div[data-testid="stDataFrame"] thead tr th {
                    background-color: #f7f6f1 !important;
                    color: black !important;
                    font-weight: 800 !important;
                }
                </style>
            """, unsafe_allow_html=True)

            def _bold_total(row):
                if row.get("ceco") == "TOTAL":
                    return ["background-color:#FFFFFF;color:black;font-weight:bold"] * len(row)
                return [""] * len(row)

            st.subheader("Departamentos — Nominal (MXN)")
            st.dataframe(
                tabla_nominal.style
                    .apply(_bold_total, axis=1)
                    .format({
                        "GADM. REAL": "${:,.2f}",
                        "GADM. PPT":  "${:,.2f}",
                        "DIF GADM":   "${:,.2f}",
                        "COSS REAL":  "${:,.2f}",
                        "COSS PPT":   "${:,.2f}",
                        "DIF COSS":   "${:,.2f}",
                    }),
                use_container_width=True,
                height=420
            )

            st.subheader("Departamentos — % sobre Ingresos")

            st.dataframe(
                tabla_porcentaje.style
                    .apply(_bold_total, axis=1)
                    .format({
                        "GADM REAL %": "{:.2%}",
                        "GADM PPT %":  "{:.2%}",
                        "DIF GADM %":  "{:+.2%}",
                        "COSS REAL %": "{:.2%}",
                        "COSS PPT %":  "{:.2%}",
                        "DIF COSS %":  "{:+.2%}",
                    }),
                use_container_width=True,
                height=420
            )

            if "Categoria_A" in df_ppt.columns:
                ing_ppt_total = float(
                    df_ppt[
                        (df_ppt["Mes_A"].isin(meses_sel)) &
                        (df_ppt["Proyecto_A"].isin(proyectos_sel)) &
                        (df_ppt["Categoria_A"].astype(str).str.strip().str.upper() == "INGRESO")
                    ]["Neto_A"].sum() or 0.0
                )
            else:
                ing_ppt_total = 0.0

            # --- INGRESO REAL TOTAL (por proyecto / ESGARI)
            if "Categoria_A" in df_real.columns:
                ing_real_total = float(
                    df_real[
                        (df_real["Mes_A"].isin(meses_sel)) &
                        (df_real["Proyecto_A"].isin(proyectos_sel)) &
                        (df_real["Categoria_A"].astype(str).str.strip().str.upper() == "INGRESO")
                    ]["Neto_A"].sum() or 0.0
                )
            else:
                ing_real_total = 0.0

            base = base.copy()

            # --- Pesos CECO contra INGRESO PPT TOTAL
            base["PESO_GADM_PPT"] = np.where(
                abs(ing_ppt_total) > 1e-9,
                base["PPT_GADM"] / ing_ppt_total,
                0.0
            )

            base["PESO_COSS_PPT"] = np.where(
                abs(ing_ppt_total) > 1e-9,
                base["PPT_COSS"] / ing_ppt_total,
                0.0
            )

            # --- Aplica al INGRESO REAL TOTAL
            base["GADM. S/INGRESOS"] = base["PESO_GADM_PPT"] * ing_real_total
            base["COSS S/INGRESO"]   = base["PESO_COSS_PPT"] * ing_real_total

            tabla_s_ing = pd.DataFrame({
                "CECO": base["ceco"],
                "GADM. REAL": base["REAL_GADM"],
                "GADM. S/INGRESOS": base["GADM. S/INGRESOS"],
                "DIF. GADM": base["GADM. S/INGRESOS"] - base["REAL_GADM"],
                "COSS REAL": base["REAL_COSS"],
                "COSS S/INGRESO": base["COSS S/INGRESO"],
                "DIF. COSS": base["COSS S/INGRESO"] - base["REAL_COSS"],
            }).fillna(0.0)

            # --- TOTAL
            total_row = pd.DataFrame([{
                "CECO": "TOTAL",
                "GADM. REAL": float(tabla_s_ing["GADM. REAL"].sum()),
                "GADM. S/INGRESOS": float(tabla_s_ing["GADM. S/INGRESOS"].sum()),
                "DIF. GADM": float(tabla_s_ing["DIF. GADM"].sum()),
                "COSS REAL": float(tabla_s_ing["COSS REAL"].sum()),
                "COSS S/INGRESO": float(tabla_s_ing["COSS S/INGRESO"].sum()),
                "DIF. COSS": float(tabla_s_ing["DIF. COSS"].sum()),
            }])

            tabla_s_ing = pd.concat([tabla_s_ing, total_row], ignore_index=True)

            st.subheader("Departamentos")
            st.dataframe(
                tabla_s_ing.style
                    .apply(_bold_total, axis=1)
                    .format({
                        "GADM. REAL": "${:,.2f}",
                        "GADM. S/INGRESOS": "${:,.2f}",
                        "DIF. GADM": "${:,.2f}",
                        "COSS REAL": "${:,.2f}",
                        "COSS S/INGRESO": "${:,.2f}",
                        "DIF. COSS": "${:,.2f}",
                    }),
                use_container_width=True,
                height=420
            )


            tabla_graf = tabla_nominal[tabla_nominal["ceco"] != "TOTAL"].copy()

            if not tabla_graf.empty:
                tabla_graf["ceco"] = tabla_graf["ceco"].astype(str)
                es_esgari = str(proyecto_nombre).strip().upper() == "ESGARI"
                fig_gadm = go.Figure()
                fig_gadm.add_bar(
                    x=tabla_graf["ceco"],
                    y=tabla_graf["GADM. REAL"],
                    name="G.ADMN REAL",
                    text=[f"${v:,.0f}" for v in tabla_graf["GADM. REAL"]],
                    textposition="outside",
                    texttemplate="%{text}",
                    cliponaxis=False,
                )
                fig_gadm.add_bar(
                    x=tabla_graf["ceco"],
                    y=tabla_graf["GADM. PPT"],
                    name="G.ADMN PPT",
                    text=[f"${v:,.0f}" for v in tabla_graf["GADM. PPT"]],
                    textposition="outside",
                    texttemplate="%{text}",
                    cliponaxis=False,
                )

                y_max_gadm = float(max(tabla_graf["GADM. REAL"].max(), tabla_graf["GADM. PPT"].max(), 0.0) or 0.0)
                y_range_gadm = y_max_gadm * (1.30 if es_esgari else 1.18) if y_max_gadm > 0 else 1

                fig_gadm.update_layout(
                    title="Departamentos — G.ADMN (REAL vs PPT)",
                    xaxis_title="Departamento",
                    yaxis_title="MXN",
                    barmode="group",
                    height=(700 if es_esgari else 520),
                    hovermode="x unified",
                    xaxis_tickangle=(-45 if es_esgari else -25),
                    yaxis=dict(range=[0, y_range_gadm]),
                    margin=dict(t=90, b=140 if es_esgari else 80),
                    legend_title_text="Serie",
                )
                if es_esgari:
                    fig_gadm.update_traces(textposition="outside")
                    fig_gadm.update_layout(uniformtext_minsize=8, uniformtext_mode="show")
                else:
                    fig_gadm.update_layout(uniformtext_minsize=10, uniformtext_mode="hide")

                st.markdown("### Gráfico G.ADMN")
                st.plotly_chart(fig_gadm, use_container_width=True)

                fig_coss = go.Figure()
                fig_coss.add_bar(
                    x=tabla_graf["ceco"],
                    y=tabla_graf["COSS REAL"],
                    name="COSS REAL",
                    text=[f"${v:,.0f}" for v in tabla_graf["COSS REAL"]],
                    textposition="outside",
                    texttemplate="%{text}",
                    cliponaxis=False,
                )
                fig_coss.add_bar(
                    x=tabla_graf["ceco"],
                    y=tabla_graf["COSS PPT"],
                    name="COSS PPT",
                    text=[f"${v:,.0f}" for v in tabla_graf["COSS PPT"]],
                    textposition="outside",
                    texttemplate="%{text}",
                    cliponaxis=False,
                )

                y_max_coss = float(max(tabla_graf["COSS REAL"].max(), tabla_graf["COSS PPT"].max(), 0.0) or 0.0)
                y_range_coss = y_max_coss * (1.30 if es_esgari else 1.18) if y_max_coss > 0 else 1

                fig_coss.update_layout(
                    title="Departamentos — COSS (REAL vs PPT)",
                    xaxis_title="Departamento",
                    yaxis_title="MXN",
                    barmode="group",
                    height=(700 if es_esgari else 520),
                    hovermode="x unified",
                    xaxis_tickangle=(-45 if es_esgari else -25),
                    yaxis=dict(range=[0, y_range_coss]),
                    margin=dict(t=90, b=140 if es_esgari else 80),
                    legend_title_text="Serie",
                )
                if es_esgari:
                    fig_coss.update_traces(textposition="outside")
                    fig_coss.update_layout(uniformtext_minsize=8, uniformtext_mode="show")
                else:
                    fig_coss.update_layout(uniformtext_minsize=10, uniformtext_mode="hide")

                st.markdown("### Gráfico COSS")
                st.plotly_chart(fig_coss, use_container_width=True)

            return tabla_nominal, tabla_porcentaje
        proyectos_oh = ["8002", "8003", "8004"]

        col1, col2, col3 = st.columns(3)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        ceco_codigo, ceco_nombre = filtro_ceco(col2)
        proyecto_codigo, proyecto_nombre = filtro_proyectos_esgari(col3, proyectos_oh)

        df_cecos = cargar_datos(cecos_url)
        df_cecos["ceco"] = df_cecos["ceco"].astype(str).str.strip()
        df_cecos["nombre"] = df_cecos["nombre"].astype(str).str.strip()

        tabla_nominal, tabla_porcentaje = tabla_proyecto2(
            df_ppt=df_ppt,
            df_real=df_real,
            meses_seleccionado=meses_seleccionado,
            cecos_seleccionados=ceco_codigo,
            proyectos_seleccionados=proyecto_codigo,
            df_cecos=df_cecos
        )

    elif selected == "Consulta":
        def limpiar_texto_excel(s):
            if pd.isna(s):
                return ""
            s = str(s)
            s = unicodedata.normalize("NFKC", s)
            s = s.replace("\u00A0", " ")
            s = re.sub(r"\s+", " ", s)
            return s.strip().upper()

        def tabla_Consultas(df_ppt, df_real, meses_seleccionado, cecos_seleccionados, proyectos_seleccionados):
            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return None
            if not cecos_seleccionados:
                st.error("Favor de seleccionar por lo menos un ceco")
                return None
            if not proyectos_seleccionados:
                st.error("Favor de seleccionar por lo menos un proyecto")
                return None

            df_ppt = df_ppt.copy()
            df_real = df_real.copy()

            for df in (df_ppt, df_real):
                df["Cuenta_A"] = df["Cuenta_A"].astype(str).str.strip()
                df["Cuenta_Nombre_A"] = df["Cuenta_Nombre_A"].apply(limpiar_texto_excel)
                df["Mes_A"] = df["Mes_A"].astype(str).str.strip()
                df["CeCo_A"] = df["CeCo_A"].astype(str).str.strip()
                df["Proyecto_A"] = df["Proyecto_A"].astype(str).str.strip()

            cuentas_df = (
                pd.concat([
                    df_ppt[["Cuenta_Nombre_A"]],
                    df_real[["Cuenta_Nombre_A"]]
                ])
                .drop_duplicates()
                .sort_values("Cuenta_Nombre_A")
            )

            opciones_cuenta = ["TODAS"] + cuentas_df["Cuenta_Nombre_A"].tolist()

            cuenta_seleccionada = st.selectbox(
                "Selecciona una cuenta",
                opciones_cuenta,
                key="consulta_cuenta_select"
            )
            cecos_str = [str(x) for x in cecos_seleccionados]
            proy_str = [str(x) for x in proyectos_seleccionados]

            df_ppt_f = df_ppt[
                (df_ppt["Mes_A"].isin(meses_seleccionado)) &
                (df_ppt["CeCo_A"].isin(cecos_str)) &
                (df_ppt["Proyecto_A"].isin(proy_str))
            ].copy()

            df_real_f = df_real[
                (df_real["Mes_A"].isin(meses_seleccionado)) &
                (df_real["CeCo_A"].isin(cecos_str)) &
                (df_real["Proyecto_A"].isin(proy_str))
            ].copy()
            ingreso_real_total = (
                df_real_f.loc[df_real_f["Categoria_A"] == "INGRESO", "Neto_A"]
                .sum()
            )
            if cuenta_seleccionada != "TODAS":
                df_ppt_f = df_ppt_f[df_ppt_f["Cuenta_Nombre_A"] == cuenta_seleccionada]
                df_real_f = df_real_f[df_real_f["Cuenta_Nombre_A"] == cuenta_seleccionada]

            ppt_resumen = (
                df_ppt_f.groupby("Cuenta_Nombre_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "PPT"})
            )

            real_resumen = (
                df_real_f.groupby("Cuenta_Nombre_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "REAL"})
            )

            tabla = (
                ppt_resumen
                .merge(real_resumen, on="Cuenta_Nombre_A", how="outer")
                .fillna(0)
            )

            tabla["DIF"] = tabla["REAL"] - tabla["PPT"]
            tabla["%"] = np.where(tabla["PPT"] != 0, (tabla["REAL"] / tabla["PPT"]) - 1, 0)
            tabla["%Ingreso"] = np.where(
                ingreso_real_total != 0,
                tabla["DIF"] / ingreso_real_total,
                0
            )

            st.subheader("Consulta por Cuenta")

            st.dataframe(
                tabla.style.format({
                    "PPT": "${:,.2f}",
                    "REAL": "${:,.2f}",
                    "DIF": "${:,.2f}",
                    "%": "{:.2%}",
                    "%Ingreso": "{:.2%}",
                }),
                use_container_width=True
            )

            if not tabla.empty:
                fig = go.Figure()

                fig.add_bar(
                    x=tabla["Cuenta_Nombre_A"],
                    y=tabla["PPT"] / 1000,
                    name="PPT",
                    text=(tabla["PPT"] / 1000).round(1),
                    texttemplate="%{text}k",
                    textposition="outside"
                )

                fig.add_bar(
                    x=tabla["Cuenta_Nombre_A"],
                    y=tabla["REAL"] / 1000,
                    name="REAL",
                    text=(tabla["REAL"] / 1000).round(1),
                    texttemplate="%{text}k",
                    textposition="outside"
                )

                fig.update_layout(
                    title="PPT vs REAL por Cuenta",
                    xaxis_title="Cuenta",
                    yaxis_title="Monto (miles)",
                    barmode="group",
                    height=420,
                    legend_title="Tipo",
                    xaxis_tickangle=-30,
                    yaxis=dict(
                        tickformat=",.0f",
                        ticksuffix="k"
                    )
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin datos con los filtros seleccionados.")

            return tabla

        col1, col2, col3 = st.columns(3)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        ceco_codigo, ceco_nombre = filtro_ceco(col2)
        proyecto_codigo, proyecto_nombre = filtro_pro(col3)

        tabla_Consultas(df_ppt, df_real, meses_seleccionado, ceco_codigo, proyecto_codigo)

    elif selected == "Meses PPT":
        def mostrar_meses_ppt(df_ppt):
            meses_disponibles = df_ppt["Mes_A"].unique().tolist()
            codigo_pro, pro = filtro_pro(st)
            ceco_codi, ceco_nomb = filtro_ceco(st)
            df_ppt["CeCo_A"] = df_ppt["CeCo_A"].astype(str)
            if ceco_nomb != "ESGARI":
                df_ppt = df_ppt[df_ppt["CeCo_A"].isin(ceco_codi)]
            meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.",
                    "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

            meses_disponibles = [mes for mes in meses_ordenados if mes in df_ppt["Mes_A"].unique()]
            meses_filtrados = st.multiselect(
                "Selecciona los meses que deseas incluir:",
                options=meses_disponibles,
                default=meses_disponibles,
                key="filtro_meses_est_res"
            )
            if len(meses_filtrados) <2:
                st.error("Selecionar dos meses o más!")
            else:

                # --- Función principal para generar el estado de resultado mensual ---
                def estado_resultado_por_mes(df_2025, proyecto_nombre, proyecto_codigo, lista_proyectos):
                    meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

                    meses_disponibles = [mes for mes in meses_ordenados if mes in meses_filtrados]
                    resultado_por_mes = {}

                    for mes in meses_disponibles:
                        estado_mes = estado_resultado(
                            df_2025,
                            meses_seleccionado=[mes],
                            proyecto_nombre=proyecto_nombre,
                            proyecto_codigo=proyecto_codigo,
                            lista_proyectos=lista_proyectos
                        )
                        resultado_por_mes[mes] = estado_mes

                    df_resultado = pd.DataFrame(resultado_por_mes)

                    # Diccionario estricto: porcentaje -> métrica base
                    porcentajes_base = {
                        "porcentaje_ingresos": "ingreso_proyecto",
                        "por_patio": "patio_pro",
                        "por_coss": "coss_total",
                        "por_utilidad_bruta": "utilidad_bruta",
                        "por_gadmn": "gadmn_pro",
                        "por_utilidad_operativa": "utilidad_operativa",
                        "por_oh": "oh_pro",
                        "por_ebit": "ebit",
                        "por_gasto_fin": "gasto_fin_pro",
                        "por_ingreso_fin": "ingreso_fin_pro",
                        "por_resultado_fin": "resultado_fin",
                        "por_ebt": "ebt"
                    }

                    # Función para calcular columna Total
                    def calcular_total(row):
                        if row.name in porcentajes_base:
                            base_row = porcentajes_base[row.name]
                            ingreso_total = df_resultado.loc["ingreso_proyecto"].sum(skipna=True)
                            if base_row in df_resultado.index and ingreso_total != 0:
                                base_total = df_resultado.loc[base_row].sum(skipna=True)
                                return base_total / ingreso_total
                            else:
                                return np.nan
                        else:
                            return row.sum(skipna=True)

                    # Agregar columna Total
                    df_resultado["Total"] = df_resultado.apply(calcular_total, axis=1)

                    # Agregar columna Promedio
                    columnas_meses = [col for col in df_resultado.columns if col != "Total"]
                    df_resultado["Promedio"] = df_resultado[columnas_meses].mean(axis=1, skipna=True)
                    return df_resultado

                # Ejecutar función
                tabla_mensual = estado_resultado_por_mes(df_ppt, pro, codigo_pro, list_pro)

                # Diccionario para formateo
                porcentajes_base = {
                    "porcentaje_ingresos": "ingreso_proyecto",
                    "por_patio": "patio_pro",
                    "por_coss": "coss_total",
                    "por_utilidad_bruta": "utilidad_bruta",
                    "por_gadmn": "gadmn_pro",
                    "por_utilidad_operativa": "utilidad_operativa",
                    "por_oh": "oh_pro",
                    "por_ebit": "ebit",
                    "por_gasto_fin": "gasto_fin_pro",
                    "por_ingreso_fin": "ingreso_fin_pro",
                    "por_resultado_fin": "resultado_fin",
                    "por_ebt": "ebt"
                }

                # Crear copia formateada
                tabla_formateada = tabla_mensual.copy()

                for row in tabla_formateada.index:
                    if "por" in row.lower() or row.startswith("%"):
                        tabla_formateada.loc[row] = tabla_formateada.loc[row].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "")
                    else:
                        tabla_formateada.loc[row] = tabla_formateada.loc[row].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "")
                nombres_filas = {
                    "ingreso_proyecto": "Ingresos",
                    "patio_pro": "Patio",            
                    "coss_total": "COSS",
                    "utilidad_bruta": "Utilidad Bruta",
                    "gadmn_pro": "Gastos Admin.",
                    "utilidad_operativa": "Utilidad Operativa",
                    "oh_pro": "OH",
                    "ebit": "EBIT",
                    "gasto_fin_pro": "Gastos Financieros",
                    "oh_pro_gfin": "Gasto financiero OH",
                    "ingreso_fin_pro": "Ingresos Financieros",
                    "ebt": "EBT",
                    "porcentaje_ingresos": "% de Ingresos",
                    "por_patio": "% Patio",
                    "por_coss": "% COSS",
                    "por_utilidad_bruta": "% Utilidad Bruta",
                    "por_gadmn": "% G. Admin",
                    "por_utilidad_operativa": "% Utilidad Operativa",
                    "por_oh": "% Overhead",
                    "por_ebit": "% EBIT",
                    "por_gasto_fin": "% Gasto Financiero",
                    "por_ingreso_fin": "% Ingreso Financiero",
                    "oh_pro_ifin": "Ingreso OH",
                    "por_resultado_fin": "% Resultado Financiero",
                    "por_ebt": "% EBT",
                    
                }
                tabla_mensual_renombrada = tabla_formateada.rename(index=nombres_filas)
                tabla_mensual_renombrada = tabla_mensual_renombrada.drop(
                    index=["coss_pro", "mal_coss", "mal_gadmn", "mal_gfin", "mal_ifin", "resultado_fin", "% de Ingresos"],
                    errors='ignore'
                )
                if st.session_state["rol"] == "gerente":
                    tabla_mensual_renombrada = tabla_mensual_renombrada.drop(
                        index=["OH", "EBIT", "Gastos Financieros", "Gasto financiero OH", "Ingresos Financieros", "EBT", "% Overhead", "% EBIT", "% Gasto Financiero", "% Ingreso Financiero", "Ingreso OH", "% Resultado Financiero", "% EBT"],
                        errors='ignore'
                    )    

                def generar_tabla_con_estilo_mensual(df):
                    df_reset = df.reset_index().rename(columns={"index": "Concepto"})
                    filas_porcentaje = [nombre for nombre in df_reset["Concepto"] if nombre.startswith("%") or "por" in nombre.lower()]

                    def aplicar_estilos(row):
                        if row["Concepto"] == "Promedio Mensual":
                            return ['background-color: #cccccc; color: black; font-weight: bold;' for _ in row]
                        elif row["Concepto"] in filas_porcentaje:
                            return ['background-color: #00112B; color: white;' for _ in row]
                        else:
                            color_fondo = '#ffffff' if row.name % 2 == 0 else '#f2f2f2'
                            return [f'background-color: {color_fondo}; color: black;' for _ in row]

                    estilos_header = [
                        {'selector': 'thead th', 'props': 'background-color: #00112B; color: white; font-weight: bold; font-size: 14px;'}
                    ]

                    html = (
                        df_reset.style
                        .apply(aplicar_estilos, axis=1)
                        .set_table_styles(estilos_header)
                        .set_properties(**{'font-size': '12px', 'text-align': 'right'})
                        .hide(axis='index')
                        .to_html()
                    )

                    responsive_html = f'<div style="overflow-x: auto; width: 100%;">{html}</div>'
                    return responsive_html

                # Mostrar en Streamlit
                st.write(f"### Estado de Resultado por Mes '{pro}'")
                tabla_html = generar_tabla_con_estilo_mensual(tabla_mensual_renombrada)
                st.markdown(tabla_html, unsafe_allow_html=True)
                meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.",
                                "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

                meses_disponibles = [mes for mes in meses_ordenados if mes in meses_filtrados]
                df_meses = df_ppt[df_ppt["Proyecto_A"].isin(codigo_pro)]
                df_meses = df_meses[~(df_meses["Clasificacion_A"].isin(["IMPUESTOS", "OTROS INGRESOS"]))]
                if st.session_state["rol"] == "gerente":
                    df_meses = df_meses[~(df_meses["Clasificacion_A"].isin(["GASTOS FINANCIEROS"]))]
                df_meses = df_meses.groupby(
                    ["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A", "Mes_A"],
                    as_index=False
                )["Neto_A"].sum()

                df_pivot = df_meses.pivot_table(
                    index=["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"],
                    columns="Mes_A",
                    values="Neto_A",
                    aggfunc="sum"
                )

                for mes in meses_disponibles:
                    if mes not in df_pivot.columns:
                        df_pivot[mes] = 0
                df_pivot = df_pivot[meses_disponibles]
                df_pivot = df_pivot.reset_index().fillna(0)
                columnas_mensuales = [col for col in df_pivot.columns if col not in ["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"]]
                df_pivot["Total"] = df_pivot[columnas_mensuales].sum(axis=1)
                df_pivot["Promedio"] = df_pivot[columnas_mensuales].mean(axis=1)

                gb = GridOptionsBuilder.from_dataframe(df_pivot)
                gb.configure_column("Clasificacion_A", rowGroup=True, hide=True)
                gb.configure_column("Categoria_A", rowGroup=True, hide=True)
                gb.configure_column("Cuenta_Nombre_A", pinned='left')
                currency_formatter = JsCode("""
                    function(params) {
                        if (params.value === 0 || params.value === null) {
                            return "$0.00";
                        }
                        return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(params.value);
                    }
                """)
                for col in df_pivot.columns:
                    if col not in ["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"]:
                        gb.configure_column(
                            col,
                            type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                            aggFunc="sum",
                            valueFormatter=currency_formatter,
                            cellStyle={'textAlign': 'right'}
                        )

                gridOptions = gb.build()
                st.write("### Tabla Clasificación, Categoría y Cuenta")
                AgGrid(
                    df_pivot,
                    gridOptions=gridOptions,
                    enable_enterprise_modules=True,
                    fit_columns_on_grid_load=False,
                    allow_unsafe_jscode=True,
                    domLayout='normal',
                    height=600
                )

        mostrar_meses_ppt(df_ppt)
        
    elif selected == "Variaciones":
        col1, col2, col3 = st.columns(3)

        meses_seleccionado = filtro_meses(col1, df_ppt)
        proyecto_codigo, proyecto_nombre = filtro_pro(col2)
        ceco_codigo, ceco_nombre = filtro_ceco(col3)  

        seccion_analisis_por_clasificacion(
            df_ppt, df_real, ingreso,
            meses_seleccionado, proyecto_codigo, proyecto_nombre,
            "COSS",
            ceco_codigo  
        )

        seccion_analisis_por_clasificacion(
            df_ppt, df_real, ingreso,
            meses_seleccionado, proyecto_codigo, proyecto_nombre,
            "G.ADMN",
            ceco_codigo  
        )

        seccion_analisis_especial_porcentual(
            df_ppt, df_real, ingreso,
            meses_seleccionado, proyecto_codigo, proyecto_nombre,
            patio, "Patio",
            ceco_codigo  
        )

        if st.session_state["rol"] == "admin":
            seccion_analisis_por_clasificacion(
                df_ppt, df_real, ingreso,
                meses_seleccionado, proyecto_codigo, proyecto_nombre,
                "GASTOS FINANCIEROS",
                ceco_codigo  
            )

            seccion_analisis_especial_porcentual(
                df_ppt, df_real, ingreso,
                meses_seleccionado, proyecto_codigo, proyecto_nombre,
                oh, "OH",
                ceco_codigo 
            )

    elif selected == "Proyección":
        MESES_ORDENADOS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        orden = {m: i for i, m in enumerate(MESES_ORDENADOS)}

        def norm_mes(x):
            s = str(x).strip().lower()
            if s and not s.endswith("."):
                s += "."
            return s

        def norm_proy(x):
            s = str(x).strip()
            if s.endswith(".0"):
                s = s[:-2]
            return s

        def _norm_clas(s):
            s = str(s).strip().upper()
            if s in ["G.ADM", "GADM", "G ADMN", "G.ADMIN", "GASTOS ADM", "GASTOS ADMIN"]:
                return "G.ADMN"
            if s in ["COSTO", "COSTOS", "COSS"]:
                return "COSS"
            return s

        def _filtrar_gadm_coss(df):
            df1 = df[df["Clasificacion_A"].isin(["COSS", "G.ADMN"])].copy()
            if not df1.empty:
                return df1

            df2 = df[df["Categoria_A"].isin(["COSS", "G.ADMN", "G.ADM", "GADM"])].copy()
            if not df2.empty:
                df2["Clasificacion_A"] = np.where(
                    df2["Categoria_A"].isin(["G.ADMN", "G.ADM", "GADM"]), "G.ADMN",
                    np.where(df2["Categoria_A"] == "COSS", "COSS", df2["Clasificacion_A"])
                )
            return df2

        def _pivot_clas(df_in, col_value_name, cecos_all):
            cols_out = ["CeCo_A", f"{col_value_name}_GADM", f"{col_value_name}_COSS"]

            if not df_in.empty:
                tmp = df_in.groupby(["CeCo_A", "Clasificacion_A"], as_index=False)["Neto_A"].sum()
                piv = tmp.pivot(index="CeCo_A", columns="Clasificacion_A", values="Neto_A").fillna(0.0).reset_index()
                if "G.ADMN" not in piv.columns:
                    piv["G.ADMN"] = 0.0
                if "COSS" not in piv.columns:
                    piv["COSS"] = 0.0
                piv = piv[["CeCo_A", "G.ADMN", "COSS"]].copy()
            else:
                piv = pd.DataFrame({"CeCo_A": sorted(list(cecos_all)), "G.ADMN": 0.0, "COSS": 0.0})

            piv = piv.rename(columns={"G.ADMN": f"{col_value_name}_GADM", "COSS": f"{col_value_name}_COSS"})
            piv = pd.DataFrame({"CeCo_A": sorted(list(cecos_all))}).merge(piv, on="CeCo_A", how="left").fillna(0.0)
            return piv[cols_out]

        def _render_tabla(base, df_cecos):
            # map CECO nombre
            df_cecos_map = df_cecos.copy()
            df_cecos_map["ceco"] = df_cecos_map["ceco"].astype(str).str.strip()
            df_cecos_map["nombre"] = df_cecos_map["nombre"].astype(str).str.strip()
            cecos_map = df_cecos_map[["ceco", "nombre"]].drop_duplicates()

            base = base.merge(
                cecos_map.rename(columns={"ceco": "CeCo_A", "nombre": "CECO"}),
                on="CeCo_A",
                how="left"
            )
            base["CECO"] = base["CECO"].fillna(base["CeCo_A"])

            t1 = base[["CECO", "GADM_PROY.", "PPT_GADM", "COSS_PROY.", "PPT_COSS"]].copy()
            t1["DIF GADM"] = t1["GADM_PROY."] - t1["PPT_GADM"]
            t1["DIF COSS"] = t1["COSS_PROY."] - t1["PPT_COSS"]
            t1 = t1.rename(columns={
                "GADM_PROY.": "G.ADMN PROY",
                "PPT_GADM":   "G.ADMN PPT",
                "COSS_PROY.": "COSS PROY",
                "PPT_COSS":   "COSS PPT",
            })[["CECO", "G.ADMN PROY", "G.ADMN PPT", "DIF GADM", "COSS PROY", "COSS PPT", "DIF COSS"]]

            # TOTAL
            total_1 = pd.DataFrame([{
                "CECO": "TOTAL",
                "G.ADMN PROY": float(t1["G.ADMN PROY"].sum()),
                "G.ADMN PPT":  float(t1["G.ADMN PPT"].sum()),
                "DIF GADM":    float(t1["DIF GADM"].sum()),
                "COSS PROY":   float(t1["COSS PROY"].sum()),
                "COSS PPT":    float(t1["COSS PPT"].sum()),
                "DIF COSS":    float(t1["DIF COSS"].sum()),
            }])

            t1 = pd.concat([t1, total_1], ignore_index=True)

            cols_money = ["G.ADMN PROY", "G.ADMN PPT", "DIF GADM", "COSS PROY", "COSS PPT", "DIF COSS"]

            def _fmt_currency(x):
                try:
                    return f"${float(x):,.0f}"
                except:
                    return "$0"

            def _highlight_total(row):
                return ["font-weight:700; background-color: #f2f2f2;" if row["CECO"] == "TOTAL" else "" for _ in row]

            styled = (
                t1.style
                .format({c: _fmt_currency for c in cols_money})
                .apply(_highlight_total, axis=1)
            )

            st.dataframe(styled, use_container_width=True, hide_index=True)

            # chart
            df_plot = t1[t1["CECO"] != "TOTAL"].copy()
            top_n = 15
            df_plot["ABS_DIF"] = (df_plot["DIF GADM"].abs() + df_plot["DIF COSS"].abs())
            df_plot = df_plot.sort_values("ABS_DIF", ascending=False).head(top_n)
            df_plot = df_plot.set_index("CECO")[["G.ADMN PROY", "G.ADMN PPT", "COSS PROY", "COSS PPT"]]

            st.subheader("Comparativo por CECO")
            st.bar_chart(df_plot)

            return t1
        c1, c2 = st.columns([2, 3])
        meses_seleccionado = filtro_meses(c1, df_ppt)
        proyecto_codigo, proyecto_nombre = filtro_pro(c2)

        df_cecos_local = cargar_datos(cecos_url)
        df_cecos_local["ceco"] = df_cecos_local["ceco"].astype(str).str.strip()
        df_cecos_local["nombre"] = df_cecos_local["nombre"].astype(str).str.strip()
        tab_actual, tab_manual = st.tabs(["Proyección (Actual)", "Proyección (Ingreso manual)"])
        with tab_actual:

            def tabla_mensual(df_ppt, meses_seleccionado, proyectos_seleccionados, df_cecos):
                # ---- normaliza inputs
                if isinstance(meses_seleccionado, str):
                    meses_sel = [norm_mes(meses_seleccionado)]
                else:
                    meses_sel = [norm_mes(m) for m in (meses_seleccionado or []) if str(m).strip()]
                meses_sel = sorted(list(dict.fromkeys(meses_sel)), key=lambda x: orden.get(x, 999))

                proyectos_sel_raw = (proyectos_seleccionados or [])
                proyectos_sel = [norm_proy(x) for x in proyectos_sel_raw if str(x).strip()]

                if not meses_sel:
                    st.error("Favor de seleccionar por lo menos un mes")
                    return None, None
                if not proyectos_sel:
                    st.error("Favor de seleccionar por lo menos un proyecto")
                    return None, None

                df_ppt = df_ppt.copy()
                df_ppt["Proyecto_A"] = df_ppt["Proyecto_A"].apply(norm_proy)
                df_ppt["CeCo_A"] = df_ppt["CeCo_A"].astype(str).str.strip()
                df_ppt["Mes_A"] = df_ppt["Mes_A"].apply(norm_mes)
                df_ppt["Clasificacion_A"] = df_ppt["Clasificacion_A"].astype(str).str.strip().str.upper()

                if "Categoria_A" in df_ppt.columns:
                    df_ppt["Categoria_A"] = df_ppt["Categoria_A"].astype(str).str.strip().str.upper()
                else:
                    df_ppt["Categoria_A"] = ""

                df_ppt["Neto_A"] = pd.to_numeric(df_ppt["Neto_A"], errors="coerce").fillna(0.0)

                proyectos_base = proyectos_sel[:]
                if not proyectos_base:
                    st.warning("No hay proyectos seleccionados.")
                    return None, None

                df_ppt["Clasificacion_A"] = df_ppt["Clasificacion_A"].apply(_norm_clas)

                df_scope = df_ppt[
                    (df_ppt["Mes_A"].isin(meses_sel)) &
                    (df_ppt["Proyecto_A"].isin(proyectos_base))
                ].copy()

                if df_scope.empty:
                    st.warning("Sin datos en PPT para esos meses/proyectos (df_scope vacío).")
                    with st.expander("🛠 Diagnóstico scope", expanded=True):
                        st.write("Meses:", meses_sel)
                        st.write("Proyectos:", proyectos_base[:30])
                        st.write("Mes_A únicos PPT:", sorted(df_ppt["Mes_A"].unique().tolist())[:20])
                        st.write("Proyecto_A únicos PPT:", sorted(df_ppt["Proyecto_A"].unique().tolist())[:20])
                    return None, None

                df_ppt_oh = _filtrar_gadm_coss(df_scope)

                df_ing_ppt = df_scope[df_scope["Categoria_A"] == "INGRESO"].copy()
                ing_ppt_total = float(df_ing_ppt["Neto_A"].sum() or 0.0)

                cecos_scope = set(df_scope["CeCo_A"].dropna().astype(str).str.strip().tolist())
                ppt_piv = _pivot_clas(df_ppt_oh, "PPT", cecos_scope)

                gadm_ppt_total = float(ppt_piv["PPT_GADM"].sum() or 0.0)
                coss_ppt_total = float(ppt_piv["PPT_COSS"].sum() or 0.0)

                pct_gadm = (gadm_ppt_total / ing_ppt_total) if abs(ing_ppt_total) > 1e-9 else 0.0
                pct_coss = (coss_ppt_total / ing_ppt_total) if abs(ing_ppt_total) > 1e-9 else 0.0

                proy_mes_act = norm_mes(st.session_state.get("PROY_mes_act", ""))
                obj = st.session_state.get("PROY_df_proyeccion", None)

                ing_proy_por_proyecto = {p: 0.0 for p in proyectos_base}

                usa_proy = (
                    isinstance(obj, pd.DataFrame) and
                    not obj.empty and
                    "Proyecto_A" in obj.columns and
                    "Neto_A" in obj.columns and
                    (proy_mes_act in meses_sel)
                )

                if usa_proy:
                    tmp = obj.copy()
                    tmp["Proyecto_A"] = tmp["Proyecto_A"].apply(norm_proy)
                    tmp["Neto_A"] = pd.to_numeric(tmp["Neto_A"], errors="coerce").fillna(0.0)
                    agg = tmp.groupby("Proyecto_A", as_index=True)["Neto_A"].sum().to_dict()
                    for p in proyectos_base:
                        ing_proy_por_proyecto[p] = float(agg.get(p, 0.0) or 0.0)
                    ing_proy_total = float(sum(ing_proy_por_proyecto.values()) or 0.0)
                else:
                    tmp_ing = df_scope[df_scope["Categoria_A"] == "INGRESO"].copy()
                    agg = tmp_ing.groupby("Proyecto_A", as_index=True)["Neto_A"].sum().to_dict()
                    for p in proyectos_base:
                        ing_proy_por_proyecto[p] = float(agg.get(p, 0.0) or 0.0)
                    ing_proy_total = float(sum(ing_proy_por_proyecto.values()) or 0.0)

                gadm_proy_total = pct_gadm * ing_proy_total
                coss_proy_total = pct_coss * ing_proy_total

                base = ppt_piv.copy()
                base["share_gadm"] = np.where(abs(gadm_ppt_total) > 1e-9, base["PPT_GADM"] / gadm_ppt_total, 0.0)
                base["share_coss"] = np.where(abs(coss_ppt_total) > 1e-9, base["PPT_COSS"] / coss_ppt_total, 0.0)

                base["GADM_PROY."] = base["share_gadm"] * gadm_proy_total
                base["COSS_PROY."] = base["share_coss"] * coss_proy_total

                t1 = _render_tabla(base, df_cecos)
                return t1, {"pct_gadm": pct_gadm, "pct_coss": pct_coss, "ing_proy_total": ing_proy_total}

            _t1, _stats = tabla_mensual(
                df_ppt=df_ppt,
                meses_seleccionado=meses_seleccionado,
                proyectos_seleccionados=proyecto_codigo,
                df_cecos=df_cecos_local
            )

        with tab_manual:

            def tabla_mensual_ingreso_manual(df_ppt, meses_seleccionado, proyectos_seleccionados, proyecto_nombre, df_cecos):
                # ---- normaliza inputs
                if isinstance(meses_seleccionado, str):
                    meses_sel = [norm_mes(meses_seleccionado)]
                else:
                    meses_sel = [norm_mes(m) for m in (meses_seleccionado or []) if str(m).strip()]
                meses_sel = sorted(list(dict.fromkeys(meses_sel)), key=lambda x: orden.get(x, 999))

                proyectos_sel_raw = (proyectos_seleccionados or [])
                proyectos_base = [norm_proy(x) for x in proyectos_sel_raw if str(x).strip()]

                if not meses_sel:
                    st.error("Favor de seleccionar por lo menos un mes")
                    return None, None
                if not proyectos_base:
                    st.error("Favor de seleccionar por lo menos un proyecto")
                    return None, None

                # ---- normaliza df_ppt
                df_ppt = df_ppt.copy()
                df_ppt["Proyecto_A"] = df_ppt["Proyecto_A"].apply(norm_proy)
                df_ppt["CeCo_A"] = df_ppt["CeCo_A"].astype(str).str.strip()
                df_ppt["Mes_A"] = df_ppt["Mes_A"].apply(norm_mes)
                df_ppt["Clasificacion_A"] = df_ppt["Clasificacion_A"].astype(str).str.strip().str.upper()

                if "Categoria_A" in df_ppt.columns:
                    df_ppt["Categoria_A"] = df_ppt["Categoria_A"].astype(str).str.strip().str.upper()
                else:
                    df_ppt["Categoria_A"] = ""

                df_ppt["Neto_A"] = pd.to_numeric(df_ppt["Neto_A"], errors="coerce").fillna(0.0)
                df_ppt["Clasificacion_A"] = df_ppt["Clasificacion_A"].apply(_norm_clas)

                # ---- scope
                df_scope = df_ppt[
                    (df_ppt["Mes_A"].isin(meses_sel)) &
                    (df_ppt["Proyecto_A"].isin(proyectos_base))
                ].copy()

                if df_scope.empty:
                    st.warning("Sin datos en PPT para esos meses/proyectos (df_scope vacío).")
                    with st.expander("🛠 Diagnóstico scope", expanded=True):
                        st.write("Meses:", meses_sel)
                        st.write("Proyectos:", proyectos_base[:30])
                        st.write("Mes_A únicos PPT:", sorted(df_ppt["Mes_A"].unique().tolist())[:20])
                        st.write("Proyecto_A únicos PPT:", sorted(df_ppt["Proyecto_A"].unique().tolist())[:20])
                    return None, None

                df_ppt_oh = _filtrar_gadm_coss(df_scope)

                # ---- ingreso PPT (para %)
                df_ing_ppt = df_scope[df_scope["Categoria_A"] == "INGRESO"].copy()
                ing_ppt_total = float(df_ing_ppt["Neto_A"].sum() or 0.0)

                cecos_scope = set(df_scope["CeCo_A"].dropna().astype(str).str.strip().tolist())
                ppt_piv = _pivot_clas(df_ppt_oh, "PPT", cecos_scope)

                gadm_ppt_total = float(ppt_piv["PPT_GADM"].sum() or 0.0)
                coss_ppt_total = float(ppt_piv["PPT_COSS"].sum() or 0.0)

                pct_gadm = (gadm_ppt_total / ing_ppt_total) if abs(ing_ppt_total) > 1e-9 else 0.0
                pct_coss = (coss_ppt_total / ing_ppt_total) if abs(ing_ppt_total) > 1e-9 else 0.0
                es_esgari = (str(proyecto_nombre).strip().upper() == "ESGARI")
                ing_manual_por_proyecto = {p: 0.0 for p in proyectos_base}

                with st.expander("✍️ Ingreso proyectado manual", expanded=True):

                    if es_esgari:
                        ing_manual_esgari = st.number_input(
                            "Ingreso proyectado total ESGARI",
                            min_value=0.0,
                            value=float(st.session_state.get("PROY_MANUAL_total_esgari", 0.0) or 0.0),
                            step=1000.0,
                            key="PROY_MANUAL_total_esgari"
                        )

                        # prorrateo por share de ingreso PPT por proyecto dentro del scope
                        tmp_ing = df_scope[df_scope["Categoria_A"] == "INGRESO"].copy()
                        agg_ing = tmp_ing.groupby("Proyecto_A", as_index=True)["Neto_A"].sum().to_dict()
                        ing_ppt_por_proy = {p: float(agg_ing.get(p, 0.0) or 0.0) for p in proyectos_base}
                        suma_base = float(sum(ing_ppt_por_proy.values()) or 0.0)

                        if abs(suma_base) > 1e-9:
                            for p in proyectos_base:
                                share = ing_ppt_por_proy[p] / suma_base
                                ing_manual_por_proyecto[p] = share * float(ing_manual_esgari or 0.0)
                        else:
                            n = max(len(proyectos_base), 1)
                            for p in proyectos_base:
                                ing_manual_por_proyecto[p] = float(ing_manual_esgari or 0.0) / n
                    else:
                        # por cómo funciona tu filtro, aquí viene un solo proyecto
                        p = proyectos_base[0]
                        ing_manual_por_proyecto[p] = st.number_input(
                            f"Ingreso proyectado manual – {proyecto_nombre}",
                            min_value=0.0,
                            value=float(st.session_state.get(f"PROY_MANUAL_ing_{p}", 0.0) or 0.0),
                            step=1000.0,
                            key=f"PROY_MANUAL_ing_{p}"
                        )

                # ---- decide ingreso proyectado total (manual > proy_df > ppt)
                ing_proy_por_proyecto = {p: 0.0 for p in proyectos_base}
                ing_manual_total = float(sum(ing_manual_por_proyecto.values()) or 0.0)

                if ing_manual_total > 0:
                    for p in proyectos_base:
                        ing_proy_por_proyecto[p] = float(ing_manual_por_proyecto.get(p, 0.0) or 0.0)
                    ing_proy_total = float(sum(ing_proy_por_proyecto.values()) or 0.0)
                else:
                    # fallback: igual que tu opción actual
                    proy_mes_act = norm_mes(st.session_state.get("PROY_mes_act", ""))
                    obj = st.session_state.get("PROY_df_proyeccion", None)

                    usa_proy = (
                        isinstance(obj, pd.DataFrame) and
                        not obj.empty and
                        "Proyecto_A" in obj.columns and
                        "Neto_A" in obj.columns and
                        (proy_mes_act in meses_sel)
                    )

                    if usa_proy:
                        tmp = obj.copy()
                        tmp["Proyecto_A"] = tmp["Proyecto_A"].apply(norm_proy)
                        tmp["Neto_A"] = pd.to_numeric(tmp["Neto_A"], errors="coerce").fillna(0.0)
                        agg = tmp.groupby("Proyecto_A", as_index=True)["Neto_A"].sum().to_dict()
                        for p in proyectos_base:
                            ing_proy_por_proyecto[p] = float(agg.get(p, 0.0) or 0.0)
                        ing_proy_total = float(sum(ing_proy_por_proyecto.values()) or 0.0)
                    else:
                        tmp_ing = df_scope[df_scope["Categoria_A"] == "INGRESO"].copy()
                        agg = tmp_ing.groupby("Proyecto_A", as_index=True)["Neto_A"].sum().to_dict()
                        for p in proyectos_base:
                            ing_proy_por_proyecto[p] = float(agg.get(p, 0.0) or 0.0)
                        ing_proy_total = float(sum(ing_proy_por_proyecto.values()) or 0.0)

                # ---- proyección (igual)
                gadm_proy_total = pct_gadm * ing_proy_total
                coss_proy_total = pct_coss * ing_proy_total

                base = ppt_piv.copy()
                base["share_gadm"] = np.where(abs(gadm_ppt_total) > 1e-9, base["PPT_GADM"] / gadm_ppt_total, 0.0)
                base["share_coss"] = np.where(abs(coss_ppt_total) > 1e-9, base["PPT_COSS"] / coss_ppt_total, 0.0)

                base["GADM_PROY."] = base["share_gadm"] * gadm_proy_total
                base["COSS_PROY."] = base["share_coss"] * coss_proy_total

                t1 = _render_tabla(base, df_cecos)
                return t1, {"pct_gadm": pct_gadm, "pct_coss": pct_coss, "ing_proy_total": ing_proy_total}

            _t1m, _statsm = tabla_mensual_ingreso_manual(
                df_ppt=df_ppt,
                meses_seleccionado=meses_seleccionado,
                proyectos_seleccionados=proyecto_codigo,
                proyecto_nombre=proyecto_nombre,
                df_cecos=df_cecos_local
            )

    elif selected == "YTD":

        def tabla_proyectos(df_ppt, df_real, meses_seleccionado, df_proyectos, proyectos_filtrados=None):
            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return None

            meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
            idx_mes = {m: i for i, m in enumerate(meses_ordenados)}

            def norm_mes(x):
                s = str(x).strip().lower()
                if s and not s.endswith("."):
                    s += "."
                return s

            def norm_proy(x):
                s = str(x).strip()
                if s.endswith(".0"):
                    s = s[:-2]
                return s

            def norm_clas(x):
                s = str(x).strip().upper()
                if s in ["G.ADM", "GADM", "G ADMN", "G.ADMIN", "GASTOS ADM", "GASTOS ADMIN"]:
                    return "G.ADMN"
                if s in ["COSTO", "COSTOS", "COSS"]:
                    return "COSS"
                return s

            def norm_cat(x):
                s = str(x).strip().upper()
                if s in ["INGRESOS", "ING", "VENTAS", "REVENUE"]:
                    return "INGRESO"
                return s
            if isinstance(meses_seleccionado, str):
                meses_sel = [norm_mes(meses_seleccionado)]
            else:
                meses_sel = [norm_mes(m) for m in (meses_seleccionado or []) if str(m).strip()]
            meses_sel = sorted(list(dict.fromkeys(meses_sel)), key=lambda x: idx_mes.get(x, 999))

            def _norm_df(df):
                df = df.copy()
                df["Proyecto_A"] = df["Proyecto_A"].apply(norm_proy)
                df["CeCo_A"] = df["CeCo_A"].astype(str).str.strip()
                df["Mes_A"] = df["Mes_A"].apply(norm_mes)
                df["Clasificacion_A"] = df["Clasificacion_A"].apply(norm_clas)
                df["Categoria_A"] = df["Categoria_A"].apply(norm_cat) if "Categoria_A" in df.columns else ""
                df["Neto_A"] = pd.to_numeric(df["Neto_A"], errors="coerce").fillna(0.0)
                return df

            df_ppt = _norm_df(df_ppt)
            df_real = _norm_df(df_real)
            if df_proyectos is None or df_proyectos.empty:
                st.warning("df_proyectos está vacío / None. No puedo armar la tabla YTD.")
                return pd.DataFrame()

            df_map = df_proyectos.copy()
            df_map["proyectos"] = df_map["proyectos"].apply(norm_proy)
            df_map["nombre"] = df_map["nombre"].astype(str).str.strip()
            mapa = dict(zip(df_map["proyectos"], df_map["nombre"]))
            proyectos_visibles = df_map["proyectos"].dropna().astype(str).tolist()
            if proyectos_filtrados:
                sel_set = set([norm_proy(x) for x in proyectos_filtrados])
                proyectos_visibles = [p for p in proyectos_visibles if p in sel_set]

            if not proyectos_visibles:
                st.warning("Sin proyectos para mostrar con el filtro actual.")
                return pd.DataFrame()

            try:
                lista_proyectos = list_pro  # tu lista global
            except NameError:
                lista_proyectos = []

            rows = []
            for p in proyectos_visibles:
                nombre = mapa.get(p, p)
                codigo_pro = [p]
                pro = str(nombre).strip()

                ing_ppt  = float(ingreso(df_ppt,  meses_sel, codigo_pro, pro) or 0.0)
                ing_real = float(ingreso(df_real, meses_sel, codigo_pro, pro) or 0.0)

                coss_ppt, _  = coss(df_ppt,  meses_sel, codigo_pro, pro, lista_proyectos)
                coss_real, _ = coss(df_real, meses_sel, codigo_pro, pro, lista_proyectos)
                coss_ppt  = float(coss_ppt or 0.0)
                coss_real = float(coss_real or 0.0)

                patio_ppt  = float(patio(df_ppt,  meses_sel, codigo_pro, pro) or 0.0)
                patio_real = float(patio(df_real, meses_sel, codigo_pro, pro) or 0.0)

                coss_total_ppt  = coss_ppt  + patio_ppt
                coss_total_real = coss_real + patio_real

                gadm_ppt, _  = gadmn(df_ppt,  meses_sel, codigo_pro, pro, lista_proyectos)
                gadm_real, _ = gadmn(df_real, meses_sel, codigo_pro, pro, lista_proyectos)
                gadm_ppt  = float(gadm_ppt or 0.0)
                gadm_real = float(gadm_real or 0.0)

                coss_pct = (coss_total_ppt / ing_ppt) if abs(ing_ppt) > 1e-9 else 0.0
                gadm_pct = (gadm_ppt / ing_ppt) if abs(ing_ppt) > 1e-9 else 0.0

                coss_calc = coss_pct * ing_real
                gadm_calc = gadm_pct * ing_real

                rows.append({
                    "PROYECTO": nombre,
                    "COSS S/INGRESO": coss_calc,
                    "COSS REAL": coss_total_real,
                    "DIF. COSS": coss_total_real - coss_calc,
                    "G.ADM S/INGRESO": gadm_calc,
                    "G.ADM REAL": gadm_real,
                    "DIF. G.ADM": gadm_real - gadm_calc,
                })

            tabla = pd.DataFrame(rows).fillna(0.0)

            if tabla.empty:
                st.warning("Sin filas para YTD (revisa filtros / catálogo proyectos).")
                return tabla

            # --- total
            total = pd.DataFrame([{
                "PROYECTO": "TOTAL",
                "COSS S/INGRESO": float(tabla["COSS S/INGRESO"].sum()),
                "COSS REAL": float(tabla["COSS REAL"].sum()),
                "DIF. COSS": float(tabla["DIF. COSS"].sum()),
                "G.ADM S/INGRESO": float(tabla["G.ADM S/INGRESO"].sum()),
                "G.ADM REAL": float(tabla["G.ADM REAL"].sum()),
                "DIF. G.ADM": float(tabla["DIF. G.ADM"].sum()),
            }])

            tabla_out = pd.concat([tabla, total], ignore_index=True)

            # --- formato tabla
            cols_money = ["COSS S/INGRESO","COSS REAL","DIF. COSS","G.ADM S/INGRESO","G.ADM REAL","DIF. G.ADM"]

            def _fmt_currency(x):
                try:
                    return f"${float(x):,.0f}"
                except:
                    return "$0"

            def _highlight_total(row):
                if str(row.get("PROYECTO","")) == "TOTAL":
                    return ["font-weight:700; background-color:#f2f2f2;" for _ in row]
                return ["" for _ in row]
            st.dataframe(
                tabla_out.style
                    .format({c: _fmt_currency for c in cols_money})
                    .apply(_highlight_total, axis=1),
                use_container_width=True,
                height=420,
                hide_index=True
            )

            st.subheader("Gráfico — COSS")

            df_plot = tabla_out[tabla_out["PROYECTO"] != "TOTAL"].copy()
            if not df_plot.empty:
                df_plot["ABS_DIF"] = df_plot["DIF. COSS"].abs() + df_plot["DIF. G.ADM"].abs()
                df_plot = df_plot.sort_values("ABS_DIF", ascending=False).head(15)

                chart_coss = df_plot.set_index("PROYECTO")[["COSS S/INGRESO", "COSS REAL"]]
                st.bar_chart(chart_coss)

            st.subheader("Gráfico — G.ADMN")

            if not df_plot.empty:
                chart_gadm = df_plot.set_index("PROYECTO")[["G.ADM S/INGRESO", "G.ADM REAL"]]
                st.bar_chart(chart_gadm)

            return tabla_out
        c1, c2 = st.columns([2, 3])
        meses_seleccionado = filtro_meses(c1, df_ppt)
        proyecto_codigo, proyecto_nombre = filtro_pro(c2)
        proyectos_filtrados = None if proyecto_nombre == "ESGARI" else proyecto_codigo

        if meses_seleccionado:
            _tabla = tabla_proyectos(
                df_ppt=df_ppt,
                df_real=df_real,
                meses_seleccionado=meses_seleccionado,
                df_proyectos=proyectos,              
                proyectos_filtrados=proyectos_filtrados
            )
        else:
            st.info("Selecciona meses")


    elif selected == "Mensual":

        col1, col2 = st.columns(2)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        proyecto_codigo, proyecto_nombre = filtro_pro(col2) 
        df_cecos_local = cargar_datos(cecos_url)
        df_cecos_local["ceco"] = df_cecos_local["ceco"].astype(str).str.strip()
        df_cecos_local["nombre"] = df_cecos_local["nombre"].astype(str).str.strip()
        def tabla_real_vs_ppt_por_ceco(df_ppt, df_real, meses_seleccionado, proyectos_filtrados, df_cecos):
            MESES_ORDENADOS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
            orden = {m: i for i, m in enumerate(MESES_ORDENADOS)}

            def norm_mes(x):
                s = str(x).strip().lower()
                if s and not s.endswith("."):
                    s += "."
                return s

            def norm_proy(x):
                return str(x).strip().replace(".0", "")

            def norm_clas(x):
                s = str(x).strip().upper()
                if s in ["G.ADM", "GADM", "G ADMN", "G.ADMIN", "GASTOS ADM", "GASTOS ADMIN"]:
                    return "G.ADMN"
                if s in ["COSTO", "COSTOS", "COSS"]:
                    return "COSS"
                return s

            def norm_cat(x):
                s = str(x).strip().upper()
                if s in ["INGRESOS", "ING", "VENTAS", "REVENUE"]:
                    return "INGRESO"
                return s

            # ---- meses
            if isinstance(meses_seleccionado, str):
                meses_sel = [norm_mes(meses_seleccionado)]
            else:
                meses_sel = [norm_mes(m) for m in (meses_seleccionado or []) if str(m).strip()]
            meses_sel = sorted(list(dict.fromkeys(meses_sel)), key=lambda x: orden.get(x, 999))

            if not meses_sel:
                st.error("Favor de seleccionar por lo menos un mes")
                return None

            # ---- normaliza dfs
            def _norm_df(df):
                df = df.copy()
                df["Proyecto_A"] = df["Proyecto_A"].astype(str).apply(norm_proy)
                df["CeCo_A"] = df["CeCo_A"].astype(str).str.strip()
                df["Mes_A"] = df["Mes_A"].apply(norm_mes)
                df["Clasificacion_A"] = df["Clasificacion_A"].apply(norm_clas)
                df["Categoria_A"] = df["Categoria_A"].apply(norm_cat) if "Categoria_A" in df.columns else ""
                df["Neto_A"] = pd.to_numeric(df["Neto_A"], errors="coerce").fillna(0.0)
                return df

            df_ppt_n = _norm_df(df_ppt)
            df_real_n = _norm_df(df_real)
            proyectos_base = [norm_proy(p) for p in (proyectos_filtrados or []) if str(p).strip()]

            if not proyectos_base:
                proys_ppt = df_ppt_n.loc[df_ppt_n["Mes_A"].isin(meses_sel), "Proyecto_A"].dropna().unique().tolist()
                proys_real = df_real_n.loc[df_real_n["Mes_A"].isin(meses_sel), "Proyecto_A"].dropna().unique().tolist()
                proyectos_base = sorted(set([norm_proy(x) for x in (proys_ppt + proys_real)]))

            if not proyectos_base:
                st.warning("No hay proyectos para esos meses.")
                return None
            ppt_scope = df_ppt_n[(df_ppt_n["Mes_A"].isin(meses_sel)) & (df_ppt_n["Proyecto_A"].isin(proyectos_base))].copy()
            real_scope = df_real_n[(df_real_n["Mes_A"].isin(meses_sel)) & (df_real_n["Proyecto_A"].isin(proyectos_base))].copy()

            if ppt_scope.empty and real_scope.empty:
                st.warning("Sin datos para esos meses/proyectos.")
                with st.expander("🛠 Diagnóstico scope", expanded=True):
                    st.write("Meses:", meses_sel)
                    st.write("Proyectos:", proyectos_base[:30])
                    st.write("Mes_A únicos PPT:", sorted(df_ppt_n["Mes_A"].unique().tolist())[:20])
                    st.write("Proyecto_A únicos PPT:", sorted(df_ppt_n["Proyecto_A"].unique().tolist())[:20])
                return None
            ing_ppt_total = float(ppt_scope.loc[ppt_scope["Categoria_A"] == "INGRESO", "Neto_A"].sum() or 0.0)
            ing_real_total = float(real_scope.loc[real_scope["Categoria_A"] == "INGRESO", "Neto_A"].sum() or 0.0)
            ppt_gastos = ppt_scope[ppt_scope["Clasificacion_A"].isin(["G.ADMN", "COSS"])].copy()
            if ppt_gastos.empty:
                st.warning("No hay COSS/G.ADMN en PPT para el scope seleccionado.")
                return None

            ppt_grp = (
                ppt_gastos.groupby(["CeCo_A", "Clasificacion_A"], as_index=False)["Neto_A"].sum()
                .pivot(index="CeCo_A", columns="Clasificacion_A", values="Neto_A")
                .fillna(0.0).reset_index()
            )
            if "G.ADMN" not in ppt_grp.columns:
                ppt_grp["G.ADMN"] = 0.0
            if "COSS" not in ppt_grp.columns:
                ppt_grp["COSS"] = 0.0
            ppt_grp = ppt_grp.rename(columns={"G.ADMN": "GADM_PPT_CECO", "COSS": "COSS_PPT_CECO"})
            real_gastos = real_scope[real_scope["Clasificacion_A"].isin(["G.ADMN", "COSS"])].copy()
            if real_gastos.empty:
                real_grp = pd.DataFrame({"CeCo_A": [], "GADM_REAL": [], "COSS_REAL": []})
            else:
                real_grp = (
                    real_gastos.groupby(["CeCo_A", "Clasificacion_A"], as_index=False)["Neto_A"].sum()
                    .pivot(index="CeCo_A", columns="Clasificacion_A", values="Neto_A")
                    .fillna(0.0).reset_index()
                )
                if "G.ADMN" not in real_grp.columns:
                    real_grp["G.ADMN"] = 0.0
                if "COSS" not in real_grp.columns:
                    real_grp["COSS"] = 0.0
                real_grp = real_grp.rename(columns={"G.ADMN": "GADM_REAL", "COSS": "COSS_REAL"})
            cecos_all = sorted(set(ppt_grp["CeCo_A"].tolist()) | set(real_grp["CeCo_A"].tolist()))
            base = pd.DataFrame({"CeCo_A": cecos_all})
            base = base.merge(ppt_grp, on="CeCo_A", how="left").merge(real_grp, on="CeCo_A", how="left").fillna(0.0)
            factor = (ing_real_total / ing_ppt_total) if abs(ing_ppt_total) > 1e-9 else 0.0
            base["GADM S/INGRESOS"] = base["GADM_PPT_CECO"] * factor
            base["COSS S/INGRESO"]  = base["COSS_PPT_CECO"] * factor
            base["DIF. GADM"] = base["GADM_REAL"] - base["GADM S/INGRESOS"]
            base["DIF COSS"]  = base["COSS_REAL"] - base["COSS S/INGRESO"]
            dfm = df_cecos.copy()
            dfm["ceco"] = dfm["ceco"].astype(str).str.strip()
            dfm["nombre"] = dfm["nombre"].astype(str).str.strip() if "nombre" in dfm.columns else dfm["ceco"]
            mapa_ceco = dfm[["ceco", "nombre"]].drop_duplicates()

            base = base.merge(mapa_ceco.rename(columns={"ceco": "CeCo_A", "nombre": "CECO"}), on="CeCo_A", how="left")
            base["CECO"] = base["CECO"].fillna(base["CeCo_A"])

            out = base[[
                "CECO",
                "GADM_REAL",
                "GADM S/INGRESOS",
                "DIF. GADM",
                "COSS_REAL",
                "COSS S/INGRESO",
                "DIF COSS"
            ]].copy()

            total = pd.DataFrame([{
                "CECO": "TOTAL",
                "GADM_REAL": float(out["GADM_REAL"].sum()),
                "GADM S/INGRESOS": float(out["GADM S/INGRESOS"].sum()),
                "DIF. GADM": float(out["DIF. GADM"].sum()),
                "COSS_REAL": float(out["COSS_REAL"].sum()),
                "COSS S/INGRESO": float(out["COSS S/INGRESO"].sum()),
                "DIF COSS": float(out["DIF COSS"].sum()),
            }])
            out = pd.concat([out, total], ignore_index=True)

            st.subheader("Presupuesto ajustado")
            st.dataframe(
                out.style.format({
                    "GADM_REAL": "${:,.2f}",
                    "GADM S/INGRESOS": "${:,.2f}",
                    "DIF. GADM": "${:,.2f}",
                    "COSS_REAL": "${:,.2f}",
                    "COSS S/INGRESO": "${:,.2f}",
                    "DIF COSS": "${:,.2f}",
                }),
                use_container_width=True,
                height=520
            )
            df_plot = out[out["CECO"] != "TOTAL"].copy()

            if not df_plot.empty:
                top_n = 20
                df_plot["ABS_DIF"] = df_plot["DIF. GADM"].abs() + df_plot["DIF COSS"].abs()
                df_plot = df_plot.sort_values("ABS_DIF", ascending=False).head(top_n)

                st.subheader("Gráfico — COSS")
                st.bar_chart(df_plot.set_index("CECO")[["COSS_REAL", "COSS S/INGRESO"]])

                st.subheader("Gráfico — G.ADMN")
                st.bar_chart(df_plot.set_index("CECO")[["GADM_REAL", "GADM S/INGRESOS"]])

            return out
        tabla_out = tabla_real_vs_ppt_por_ceco(
            df_ppt=df_ppt,
            df_real=df_real,
            meses_seleccionado=meses_seleccionado,
            proyectos_filtrados=proyecto_codigo,  
            df_cecos=df_cecos_local               
        )

    elif selected == "Modificaciones":
        st.subheader("Cambios base de datos")

        def tabla_diferencias(df_ppt: pd.DataFrame, df_base: pd.DataFrame):

            if df_base is None or df_base.empty:
                st.warning("df_base está vacío o no existe.")
                return None
            if df_ppt is None or df_ppt.empty:
                st.warning("df_ppt está vacío o no existe.")
                return None
            key_full = [
                "Mes_A", "Empresa_A", "CeCo_A", "Proyecto_A", "Cuenta_A",
                "Clasificacion_A", "Cuenta_Nombre_A", "Categoria_A", "Neto_A"
            ]

            base = df_base.copy()
            ppt  = df_ppt.copy()
            faltan_base = set(key_full) - set(base.columns)
            faltan_ppt  = set(key_full) - set(ppt.columns)
            if faltan_base:
                st.error(f"df_base no contiene columnas requeridas: {sorted(faltan_base)}")
                return None
            if faltan_ppt:
                st.error(f"df_ppt no contiene columnas requeridas: {sorted(faltan_ppt)}")
                return None
            for df in (base, ppt):
                for c in key_full:
                    if c != "Neto_A":
                        df[c] = (
                            df[c].astype(str)
                            .str.replace(r"\s+", " ", regex=True)  
                            .str.strip()
                            .str.upper()                           
                        )

                df["Neto_A"] = (
                    df["Neto_A"].astype(str)
                    .str.replace(",", "", regex=False)
                )
                df["Neto_A"] = pd.to_numeric(df["Neto_A"], errors="coerce").fillna(0.0).round(2)
            def make_key(df):
                partes = [df[c].astype(str) for c in key_full if c != "Neto_A"] + [df["Neto_A"].astype(str)]
                return partes[0].str.cat(partes[1:], sep="||")

            base["_KEY_FULL"] = make_key(base)
            ppt["_KEY_FULL"]  = make_key(ppt)
            base_u = base.drop_duplicates("_KEY_FULL")
            ppt_u  = ppt.drop_duplicates("_KEY_FULL")
            nuevos = ppt_u[~ppt_u["_KEY_FULL"].isin(base_u["_KEY_FULL"])].copy()
            eliminados = base_u[~base_u["_KEY_FULL"].isin(ppt_u["_KEY_FULL"])].copy()

            if nuevos.empty and eliminados.empty:
                st.success("No hay diferencias: todas las combinaciones coinciden (incluyendo Neto).")
                return None

            # Salida
            nuevos_out = nuevos[key_full].copy()
            nuevos_out["TIPO_CAMBIO"] = "NUEVO"
            nuevos_out["Neto_A_BASE"] = 0.0
            nuevos_out["Neto_A_PPT"]  = nuevos_out["Neto_A"]
            nuevos_out["DIF_NETO"]    = nuevos_out["Neto_A_PPT"] - nuevos_out["Neto_A_BASE"]

            elim_out = eliminados[key_full].copy()
            elim_out["TIPO_CAMBIO"] = "ELIMINADO"
            elim_out["Neto_A_BASE"] = elim_out["Neto_A"]
            elim_out["Neto_A_PPT"]  = 0.0
            elim_out["DIF_NETO"]    = elim_out["Neto_A_PPT"] - elim_out["Neto_A_BASE"]

            out_final = pd.concat([nuevos_out, elim_out], ignore_index=True)
            orden = {"NUEVO": 0, "ELIMINADO": 1}
            out_final["__ord"] = out_final["TIPO_CAMBIO"].map(orden).fillna(9)
            out_final = out_final.sort_values(["__ord", "Mes_A", "Empresa_A", "Proyecto_A", "Cuenta_A"]).drop(columns="__ord")

            st.write(
                f"Registros con cambios: **{len(out_final)}** | "
                f"NUEVOS: **{sum(out_final.TIPO_CAMBIO=='NUEVO')}** | "
                f"ELIMINADOS: **{sum(out_final.TIPO_CAMBIO=='ELIMINADO')}**"
            )
            out_show = out_final.drop(columns=["Neto_A"], errors="ignore")
            st.dataframe(
                out_show,
                use_container_width=True,
                height=520
            )

            return out_show

        tabla_diferencias(df_ppt, df_base)

    elif selected == "Dashboard":
        meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

        def _ordenar_meses(df, col_mes="Mes_A"):
            df = df.copy()
            orden = {m: i for i, m in enumerate(meses_ordenados)}
            df["__ord"] = df[col_mes].map(orden).fillna(999).astype(int)
            df = df.sort_values("__ord").drop(columns="__ord")
            return df

        def to_float(x):
            if x is None:
                return 0.0
            if isinstance(x, str):
                x = x.replace("%", "").strip()
                try:
                    v = float(x)
                    return v / 100 if v > 1 else v
                except:
                    return 0.0
            try:
                return float(x)
            except:
                return 0.0

        def _filtrar_proyectos_df(df, proyectos_codigos, pro_nombre="ESGARI"):
            """
            Si pro_nombre == ESGARI => NO filtra (todos).
            Si pro_nombre != ESGARI => filtra por Proyecto_A en proyectos_codigos.
            """
            base = df.copy()
            base.columns = base.columns.astype(str).str.strip()
            if "Proyecto_A" not in base.columns:
                return base

            base["Proyecto_A"] = base["Proyecto_A"].astype(str).str.strip().str.replace(".0", "", regex=False)

            if str(pro_nombre).strip().upper() == "ESGARI":
                return base  # ESGARI = todos

            cods = [str(x).strip().replace(".0", "") for x in (proyectos_codigos or [])]
            if not cods:
                return base.iloc[0:0].copy()
            return base[base["Proyecto_A"].isin(cods)].copy()

        def _serie_por_mes(df, meses, proyectos_codigos, pro_nombre, fn_valor):
            """
            Devuelve DataFrame: Mes_A | VAL
            fn_valor(df, [mes], codigo_pro, pro_nombre) -> float
            """
            orden = {m: i for i, m in enumerate(meses_ordenados)}
            meses_clean = [str(m).strip() for m in (meses or []) if str(m).strip() != ""]
            meses_clean = sorted(list(dict.fromkeys(meses_clean)), key=lambda x: orden.get(x, 999))

            out = []
            for m in meses_clean:
                v = float(fn_valor(df, [m], proyectos_codigos, pro_nombre) or 0.0)
                out.append({"Mes_A": m, "VAL": v})

            df_out = pd.DataFrame(out)
            if df_out.empty:
                return pd.DataFrame({"Mes_A": [], "VAL": []})
            return _ordenar_meses(df_out, "Mes_A")

        def _ingresos_total_por_mes(df, meses, proyectos_codigos, pro_nombre):
            def _calc(df_local, meses_local, cods, pro):
                codigo_pro = [] if str(pro).strip().upper() == "ESGARI" else [
                    str(x).strip().replace(".0", "") for x in (cods or [])
                ]
                return float(ingreso(df_local, meses_local, codigo_pro, pro) or 0.0)

            return _serie_por_mes(df, meses, proyectos_codigos, pro_nombre, _calc).rename(columns={"VAL": "INGRESO"})

        def _COSS_total(df, meses, proyectos_codigos, pro_nombre):
            def _calc(df_local, meses_local, cods, pro):
                codigo_pro = [] if str(pro).strip().upper() == "ESGARI" else [
                    str(x).strip().replace(".0", "") for x in (cods or [])
                ]
                coss_base, _ = coss(df_local, meses_local, codigo_pro, pro, list_pro)
                coss_base = float(coss_base or 0.0)
                pat = float(patio(df_local, meses_local, codigo_pro, pro) or 0.0)
                return coss_base + pat

            return _serie_por_mes(df, meses, proyectos_codigos, pro_nombre, _calc).rename(columns={"VAL": "COSS"})

        def _GADMN_total(df, meses, proyectos_codigos, pro_nombre):
            def _calc(df_local, meses_local, cods, pro):
                codigo_pro = [] if str(pro).strip().upper() == "ESGARI" else [
                    str(x).strip().replace(".0", "") for x in (cods or [])
                ]
                g, _ = gadmn(df_local, meses_local, codigo_pro, pro, list_pro)
                return float(g or 0.0)

            return _serie_por_mes(df, meses, proyectos_codigos, pro_nombre, _calc).rename(columns={"VAL": "G.ADMN"})

        def _linea_ppt_real(df_ppt_mes, df_real_mes, titulo):
            if df_ppt_mes is None:
                df_ppt_mes = pd.DataFrame({"Mes_A": [], "PPT": []})
            if df_real_mes is None:
                df_real_mes = pd.DataFrame({"Mes_A": [], "REAL": []})

            line = df_ppt_mes.merge(df_real_mes, on="Mes_A", how="outer").fillna(0)
            if "PPT" not in line.columns:
                line["PPT"] = 0
            if "REAL" not in line.columns:
                line["REAL"] = 0

            line = _ordenar_meses(line, "Mes_A")
            if line.empty:
                return None

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=line["Mes_A"], y=line["PPT"], mode="lines+markers", name="PPT"))
            fig.add_trace(go.Scatter(x=line["Mes_A"], y=line["REAL"], mode="lines+markers", name="REAL"))
            fig.update_layout(
                title=titulo,
                xaxis_title="Mes",
                yaxis_title="MXN",
                height=380,
                hovermode="x unified"
            )
            return fig

        def _bar_mes_ppt_real(df_ppt_mes, df_real_mes, titulo, unidad="MXN"):
            if df_ppt_mes is None:
                df_ppt_mes = pd.DataFrame({"Mes_A": [], "PPT": []})
            if df_real_mes is None:
                df_real_mes = pd.DataFrame({"Mes_A": [], "REAL": []})

            bar = df_ppt_mes.merge(df_real_mes, on="Mes_A", how="outer").fillna(0)
            if "PPT" not in bar.columns:
                bar["PPT"] = 0
            if "REAL" not in bar.columns:
                bar["REAL"] = 0

            bar = _ordenar_meses(bar, "Mes_A")
            if bar.empty:
                return None

            fig = go.Figure()
            fig.add_bar(
                x=bar["Mes_A"],
                y=bar["PPT"],
                name="PPT",
                text=[f"${v:,.0f}" for v in bar["PPT"]],
                textposition="outside"
            )
            fig.add_bar(
                x=bar["Mes_A"],
                y=bar["REAL"],
                name="REAL",
                text=[f"${v:,.0f}" for v in bar["REAL"]],
                textposition="outside"
            )

            fig.update_layout(
                title=titulo,
                xaxis_title="Mes",
                yaxis_title=unidad,
                barmode="group",
                height=420,
                hovermode="x unified",
                legend_title="Tipo"
            )
            return fig

        df_ppt = df_ppt.copy()
        df_real = df_real.copy()
        df_ppt.columns = df_ppt.columns.astype(str).str.strip()
        df_real.columns = df_real.columns.astype(str).str.strip()

        if "Mes_A" not in df_ppt.columns or "Mes_A" not in df_real.columns:
            st.error("Falta la columna Mes_A en df_ppt o df_real. Revisa nombres de columnas.")
            with st.expander("🛠 Diagnóstico DASHBOARD", expanded=True):
                st.write("Columnas PPT:", list(df_ppt.columns))
                st.write("Columnas REAL:", list(df_real.columns))
            st.stop()

        meses_ppt = df_ppt["Mes_A"].astype(str).str.strip().unique().tolist()
        meses_real = df_real["Mes_A"].astype(str).str.strip().unique().tolist()
        meses_disponibles = [m for m in meses_ordenados if (m in meses_ppt) or (m in meses_real)]

        c_f1, c_f2 = st.columns([1.2, 1])

        with c_f1:
            meses_sel = st.multiselect(
                "Selecciona mes(es):",
                options=meses_disponibles,
                default=meses_disponibles[-1:] if meses_disponibles else [],
                key="dashboard_meses_excel"
            )
            if not meses_sel:
                st.error("Favor de seleccionar por lo menos un mes.")
                st.stop()

        with c_f2:
            proyecto_codigo, proyecto_nombre = filtro_pro(c_f2)  
        ing_ppt_mes  = _ingresos_total_por_mes(df_ppt,  meses_sel, proyecto_codigo, proyecto_nombre).rename(columns={"INGRESO": "PPT"})
        ing_real_mes = _ingresos_total_por_mes(df_real, meses_sel, proyecto_codigo, proyecto_nombre).rename(columns={"INGRESO": "REAL"})
        fig_ing_line = _linea_ppt_real(ing_ppt_mes, ing_real_mes, "INGRESO (línea)")

        coss_ppt_mes  = _COSS_total(df_ppt,  meses_sel, proyecto_codigo, proyecto_nombre).rename(columns={"COSS": "PPT"})
        coss_real_mes = _COSS_total(df_real, meses_sel, proyecto_codigo, proyecto_nombre).rename(columns={"COSS": "REAL"})
        fig_coss_line = _linea_ppt_real(coss_ppt_mes, coss_real_mes, "COSS (línea)")

        gadmn_ppt_mes  = _GADMN_total(df_ppt,  meses_sel, proyecto_codigo, proyecto_nombre).rename(columns={"G.ADMN": "PPT"})
        gadmn_real_mes = _GADMN_total(df_real, meses_sel, proyecto_codigo, proyecto_nombre).rename(columns={"G.ADMN": "REAL"})
        fig_gadmn_line = _linea_ppt_real(gadmn_ppt_mes, gadmn_real_mes, "G.ADMN (línea)")

        fig_ing_bar   = _bar_mes_ppt_real(ing_ppt_mes,  ing_real_mes,  "INGRESO mensual (PPT vs REAL)")
        fig_coss_bar  = _bar_mes_ppt_real(coss_ppt_mes, coss_real_mes, "COSS mensual (PPT vs REAL)")
        fig_gadmn_bar = _bar_mes_ppt_real(gadmn_ppt_mes, gadmn_real_mes, "G.ADMN mensual (PPT vs REAL)")
        excluir_uo = {"8002", "8003", "8004"}

        proyectos_local = proyectos.copy()
        proyectos_local["proyectos"] = proyectos_local["proyectos"].astype(str).str.strip().str.replace(".0", "", regex=False)
        proyectos_local["nombre"] = proyectos_local["nombre"].astype(str).str.strip()
        allowed = [str(x).strip() for x in st.session_state.get("proyectos", [])]

        if allowed == ["ESGARI"]:
            df_visibles = proyectos_local.copy()
        else:
            df_visibles = proyectos_local[proyectos_local["proyectos"].isin(allowed)].copy()

        df_visibles = df_visibles.dropna(subset=["proyectos", "nombre"]).copy()
        if str(proyecto_nombre).strip().upper() != "ESGARI":
            cods_sel = [str(x).strip().replace(".0", "") for x in (proyecto_codigo or [])]
            df_visibles_uo = df_visibles[df_visibles["proyectos"].isin(cods_sel)].copy()
        else:
            df_visibles_uo = df_visibles.copy()
        df_visibles_uo = df_visibles_uo[~df_visibles_uo["proyectos"].isin(excluir_uo)].copy()

        nombres_uo = df_visibles_uo["nombre"].tolist()
        codigos_uo = df_visibles_uo["proyectos"].tolist()

        ppt_pct, real_pct = {}, {}
        for nombre, codigo in zip(nombres_uo, codigos_uo):
            codigo_list = [str(codigo)]
            er_ppt  = estado_resultado(df_ppt,  meses_sel, nombre, codigo_list, list_pro) or {}
            er_real = estado_resultado(df_real, meses_sel, nombre, codigo_list, list_pro) or {}
            ppt_pct[nombre]  = to_float(er_ppt.get("por_utilidad_operativa"))
            real_pct[nombre] = to_float(er_real.get("por_utilidad_operativa"))

        df_uo = pd.DataFrame({
            "Proyecto": nombres_uo,
            "PPT":  [ppt_pct.get(n, 0.0)  for n in nombres_uo],
            "REAL": [real_pct.get(n, 0.0) for n in nombres_uo],
        }).sort_values("REAL", ascending=False)

        fig_uo = go.Figure()
        fig_uo.add_bar(
            x=df_uo["Proyecto"],
            y=df_uo["PPT"],
            name="PPT",
            text=[f"{v*100:.1f}%" for v in df_uo["PPT"]],
            textposition="outside"
        )
        fig_uo.add_bar(
            x=df_uo["Proyecto"],
            y=df_uo["REAL"],
            name="REAL",
            text=[f"{v*100:.1f}%" for v in df_uo["REAL"]],
            textposition="outside"
        )
        fig_uo.update_layout(
            title="% Utilidad Operativa",
            xaxis_title="Proyecto",
            yaxis_title="%",
            barmode="group",
            height=520,
            hovermode="x unified",
            xaxis_tickangle=-25,
            xaxis_tickformat=".0%"
        )

        tab1, tab2 = st.tabs(["Mensual", "YTD"])

        with tab1:
            m1, m2 = st.columns(2)
            with m1:
                if fig_ing_bar is None:
                    st.info("No hay datos de INGRESO para los meses seleccionados.")
                else:
                    st.plotly_chart(fig_ing_bar, use_container_width=True, key="m_ing_bar")

            with m2:
                if fig_coss_bar is None:
                    st.info("No hay datos de COSS para los meses seleccionados.")
                else:
                    st.plotly_chart(fig_coss_bar, use_container_width=True, key="m_coss_bar")

            m3, m4 = st.columns(2)
            with m3:
                if fig_gadmn_bar is None:
                    st.info("No hay datos de G.ADMN para los meses seleccionados.")
                else:
                    st.plotly_chart(fig_gadmn_bar, use_container_width=True, key="m_gadmn_bar")

            with m4:
                if df_uo.empty:
                    st.info("No hay datos para % Utilidad Operativa con los filtros seleccionados.")
                else:
                    st.plotly_chart(fig_uo, use_container_width=True, key="m_uo_bar")

        with tab2:
            st.subheader("YTD")
            c1, c2 = st.columns(2)
            with c1:
                if fig_ing_line is None:
                    st.info("No hay datos de INGRESO para los meses seleccionados.")
                else:
                    st.plotly_chart(fig_ing_line, use_container_width=True, key="ytd_ing_line")

            with c2:
                if fig_coss_line is None:
                    st.info("No hay datos de COSS para los meses seleccionados.")
                else:
                    st.plotly_chart(fig_coss_line, use_container_width=True, key="ytd_coss_line")

            c3, c4 = st.columns(2)
            with c3:
                if fig_gadmn_line is None:
                    st.info("No hay datos de G.ADMN para los meses seleccionados.")
                else:
                    st.plotly_chart(fig_gadmn_line, use_container_width=True, key="ytd_gadmn_line")

            with c4:
                if df_uo.empty:
                    st.info("No hay datos para % Utilidad Operativa con los filtros seleccionados.")
                else:
                    st.plotly_chart(fig_uo, use_container_width=True, key="ytd_uo_bar")
                    





























































































































