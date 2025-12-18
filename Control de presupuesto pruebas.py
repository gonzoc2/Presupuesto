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


st.set_page_config(
    page_title="Control de Presupuesto",
    page_icon="🚚", #buscar un icono
    layout="wide"   
)

logo_base64 = st.secrets["images"]["logo"]

st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{logo_base64}" alt="Logo de la Empresa" width="300">
    </div>
    """,
    unsafe_allow_html=True,
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
Usuarios_url = st.secrets["urls"]["Usuarios ppt"]
basereal = st.secrets["urls"]["base_2025"]
mapeo_ppt_url = st.secrets["urls"]["mapeo"]
proyectos_url = st.secrets["urls"]["proyectos"]
cecos_url = st.secrets["urls"]["cecos"]


meses = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]

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
        return fila["usuario"], fila["rol"]
    return None, None

def filtro_pro(col):
    proyectos["proyectos"] = proyectos["proyectos"].astype(str).str.strip()
    df_visibles = proyectos[proyectos["proyectos"].astype(str).isin(st.session_state["proyectos"])]
    nombre_a_codigo = dict(zip(df_visibles["nombre"], df_visibles["proyectos"].astype(str)))
    if st.session_state["proyectos"] == ["ESGARI"]:
        opciones = ["ESGARI"] + proyectos["nombre"].tolist()
        proyecto_nombre = col.selectbox("Selecciona un proyecto", opciones)
        if proyecto_nombre == "ESGARI":
            proyecto_codigo = proyectos["proyectos"].astype(str).tolist()
        else:
            proyecto_codigo = proyectos.loc[proyectos["nombre"] == proyecto_nombre, "proyectos"].astype(str).tolist()
    else:
        proyecto_nombre = col.selectbox("Selecciona un proyecto", list(nombre_a_codigo.keys()))
        proyecto_codigo = [nombre_a_codigo[proyecto_nombre]]

    return proyecto_codigo, proyecto_nombre

def filtro_meses(col, df_ppt):
    meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
    meses_disponibles = [m for m in meses_ordenados if m in df_ppt["Mes_A"].unique()]

    if selected == "PPT MENSUAL":
        mes = col.selectbox("Selecciona un mes", meses_disponibles)
        return [mes]

    elif selected == "PPT YTD":
        mes_act = meses_disponibles[-1] if meses_disponibles else None
        index_default = meses_disponibles.index(mes_act) if mes_act in meses_disponibles else 0
        mes_sel = col.selectbox("Selecciona mes corte (YTD)", meses_disponibles, index=index_default)
        idx = meses_disponibles.index(mes_sel)
        return meses_disponibles[:idx + 1]

    else:
        return col.multiselect("Selecciona un mes", meses_disponibles, default=[meses_disponibles[0]] if meses_disponibles else [])

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

def gadmn(df, meses, codigo_pro, pro, lista_proyectos, categorias_flex_com=None):
    """
    categorias_flex_com: lista de categorías para el ajuste de FLEX (si aplica)
    """
    categorias_flex_com = categorias_flex_com or []
    pat_oh = ["8002", "8003", "8004"]

    mal_clasificados_total = 0

    df_base = df[~df["Proyecto_A"].isin(pat_oh)].copy() if pro in ["ESGARI", "FLEX DEDICADO", "FLEX SPOT"] else df.copy()
    df_mes = df_base[df_base["Mes_A"].isin(meses)]

    if pro == "ESGARI":
        df_gadmn = df_mes[df_mes["Clasificacion_A"] == "G.ADMN"]
        return df_gadmn["Neto_A"].sum(), 0

    df_pro = df_mes[df_mes["Proyecto_A"].isin(codigo_pro)]
    df_gadmn = df_pro[df_pro["Clasificacion_A"] == "G.ADMN"]
    gadmn_pro = df_gadmn["Neto_A"].sum()

    if pro == "FLEX DEDICADO":
        gadmn_flexs = df_pro[df_pro["Categoria_A"].isin(categorias_flex_com)]["Neto_A"].sum() * 0.15
        gadmn_pro -= gadmn_flexs

    if pro == "FLEX SPOT":
        df_pro_flexd = df_mes[df_mes["Proyecto_A"].isin(["2001"])]
        gadmn_flexd = df_pro_flexd[df_pro_flexd["Categoria_A"].isin(categorias_flex_com)]["Neto_A"].sum() * 0.15
        gadmn_pro += gadmn_flexd

    for x in meses:
        por_ing = porcentaje_ingresos(df_base, [x], pro, codigo_pro)
        df_mes_x = df_base[df_base["Mes_A"] == x]
        mal = df_mes_x[~df_mes_x["Proyecto_A"].isin(lista_proyectos)]
        mal = mal[mal["Clasificacion_A"].isin(["G.ADMN"])]["Neto_A"].sum() * por_ing
        gadmn_pro += mal
        mal_clasificados_total += mal

    return gadmn_pro, mal_clasificados_total

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


ceco = st.secrets["urls"]["ceco"]
cecos = cargar_datos(ceco)
def filtro_ceco(col):
    cecos["ceco"] = cecos["ceco"].astype(str)
    df_visibles = cecos[cecos["ceco"].isin(st.session_state["cecos"])]
    nombre_a_codigo = dict(zip(df_visibles["nombre"], df_visibles["ceco"]))
    if st.session_state["cecos"] == ["ESGARI"]:
        opciones = ["ESGARI"] + cecos["nombre"].tolist()
        ceco_nombre = col.selectbox("Selecciona un ceco", opciones)
        if ceco_nombre == "ESGARI":
            ceco_codigo = cecos["ceco"].tolist()

        else:
            ceco_codigo = cecos[cecos["nombre"] == ceco_nombre]["ceco"].values.tolist()
    else:
        ceco_nombre = col.selectbox("Selecciona un ceco", list(nombre_a_codigo.keys()))
        ceco_codigo = [nombre_a_codigo[ceco_nombre]]

    return ceco_codigo, ceco_nombre

def tabla_comparativa(tipo_com, df_agrid, df_ppt, proyecto_codigo, meses_seleccionado, clasificacion, categoria, titulo):
    st.write(titulo)
    df_agrid = df_agrid.copy()
    df_ppt = df_ppt.copy()
    df_agrid["Proyecto_A"] = df_agrid["Proyecto_A"].astype(str).str.strip()
    df_ppt["Proyecto_A"] = df_ppt["Proyecto_A"].astype(str).str.strip()
    proyecto_codigo = [str(x) for x in proyecto_codigo]

    columnas = ['Cuenta_Nombre_A', 'Categoria_A']
    df_agrid = df_agrid[df_agrid[clasificacion] == categoria]
    df_agrid = df_agrid.groupby(columnas, as_index=False).agg({"Neto_A": "sum"})
    df_agrid.rename(columns={"Neto_A": f"{tipo_com}"}, inplace=True)
    df_actual = df_ppt[df_ppt['Mes_A'].isin(meses_seleccionado)]
    df_actual = df_actual[df_actual['Proyecto_A'].isin(proyecto_codigo)]
    df_actual = df_actual[df_actual[clasificacion] == categoria]
    df_actual = df_actual.groupby(columnas, as_index=False).agg({"Neto_A": "sum"})
    df_actual.rename(columns={"Neto_A": "YTD"}, inplace=True)
    df_compara = pd.merge(df_agrid, df_actual, on=columnas, how="outer").fillna(0)
    df_compara["Variación % "] = np.where(
        df_compara[f"{tipo_com}"] != 0,
        ((df_compara["YTD"] / df_compara[f"{tipo_com}"]) - 1) * 100,
        0
    )

    cols_out = ['Cuenta_Nombre_A', 'Categoria_A', 'YTD', f"{tipo_com}", "Variación % "]
    df_tabla = df_compara[cols_out].copy()
    df_last = df_tabla.groupby("Categoria_A", as_index=False)[["YTD", f"{tipo_com}"]].sum()
    df_last["Variación % "] = np.where(
        df_last[f"{tipo_com}"] != 0,
        ((df_last["YTD"] / df_last[f"{tipo_com}"]) - 1) * 100,
        0
    )
    df_tabla = pd.concat([df_tabla, df_last], ignore_index=True)
    df_tabla["YTD"] = pd.to_numeric(df_tabla["YTD"], errors="coerce").fillna(0)
    df_tabla[tipo_com] = pd.to_numeric(df_tabla[tipo_com], errors="coerce").fillna(0)
    df_tabla["Variación % "] = pd.to_numeric(df_tabla["Variación % "], errors="coerce").fillna(0)

    # AgGrid (agrupado)
    gb = GridOptionsBuilder.from_dataframe(df_tabla)
    gb.configure_default_column(groupable=True)

    gb.configure_column("Categoria_A", rowGroup=True, hide=True)

    gb.configure_column("YTD", type=["numericColumn"], aggFunc="sum", valueFormatter="`$${value.toLocaleString()}`")
    gb.configure_column(f"{tipo_com}", type=["numericColumn"], aggFunc="sum", valueFormatter="`$${value.toLocaleString()}`")
    gb.configure_column("Variación % ", header_name="Variación % ", type=["numericColumn"], aggFunc="avg", valueFormatter="(value != null) ? value.toFixed(2) + ' %' : ''")

    grid_options = gb.build()
    grid_options.update({
        "groupDisplayType": "groupRows",
        "groupDefaultExpanded": 0
    })

    AgGrid(
        df_tabla,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        height=500,
        use_checkbox=False,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        key=f"agrid_{tipo_com}_{'-'.join(proyecto_codigo)}_{'-'.join(meses_seleccionado)}_{categoria}"
    )
def seccion_analisis_especial_porcentual(
    df_ppt, df_real, ingreso,
    meses_seleccionado, proyecto_codigo, proyecto_nombre,
    ceco_codigo, ceco_nombre,
    funcion, nombre_funcion
):
    with st.expander(f"{nombre_funcion.upper()}"):

        meses_completos = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        orden = {m:i for i, m in enumerate(meses_completos)}
        meses_sel = sorted(list(set(meses_seleccionado)), key=lambda x: orden.get(x, 999))

        if not meses_sel:
            st.error("Selecciona por lo menos un mes.")
            return

        proy = [str(x).strip() for x in proyecto_codigo]
        cecos = [str(x).strip() for x in ceco_codigo]
        df_ppt_sel = df_ppt[
            (df_ppt["Mes_A"].isin(meses_sel)) &
            (df_ppt["Proyecto_A"].astype(str).isin(proy)) &
            (df_ppt["CeCo_A"].astype(str).isin(cecos))
        ].copy()

        ingreso_ppt = ingreso(df_ppt_sel, meses_sel, proy, proyecto_nombre)
        valor_ppt = funcion(df_ppt_sel, meses_sel, proy, proyecto_nombre)
        ppt_pct = (valor_ppt / ingreso_ppt * 100) if ingreso_ppt != 0 else 0.0
        df_real_sel = df_real[
            (df_real["Mes_A"].isin(meses_sel)) &
            (df_real["Proyecto_A"].astype(str).isin(proy)) &
            (df_real["CeCo_A"].astype(str).isin(cecos))
        ].copy()

        ingreso_real = ingreso(df_real_sel, meses_sel, proy, proyecto_nombre)
        valor_real = funcion(df_real_sel, meses_sel, proy, proyecto_nombre)
        real_pct = (valor_real / ingreso_real * 100) if ingreso_real != 0 else 0.0

        dif_pp = real_pct - ppt_pct
        pct_vs_ppt = ((real_pct / ppt_pct) - 1) * 100 if ppt_pct != 0 else 0.0

        df_out = pd.DataFrame([{
            "PPT %": round(ppt_pct, 2),
            "REAL %": round(real_pct, 2),
            "DIF (pp)": round(dif_pp, 2),
            "% vs PPT": round(pct_vs_ppt, 2)
        }])

        def resaltar(row):
            if row["REAL %"] > row["PPT %"]:
                return ['background-color: red; color: white'] * len(row)
            elif row["REAL %"] < row["PPT %"]:
                return ['background-color: green; color: black'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_out.style.apply(resaltar, axis=1).format({
                "PPT %": "{:.2f}%",
                "REAL %": "{:.2f}%",
                "DIF (pp)": "{:.2f}",
                "% vs PPT": "{:.2f}%"
            }),
            use_container_width=True
        )
def seccion_analisis_por_clasificacion(
    df_ppt, df_real, ingreso,
    meses_seleccionado, proyecto_codigo, proyecto_nombre,
    clasificacion_nombre, ceco_codigo, ceco_nombre
):
    with st.expander(clasificacion_nombre):

        meses_completos = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        orden = {m:i for i, m in enumerate(meses_completos)}
        meses_sel = sorted(list(set(meses_seleccionado)), key=lambda x: orden.get(x, 999))

        if not meses_sel:
            st.error("Selecciona por lo menos un mes.")
            return

        proy = [str(x).strip() for x in proyecto_codigo]
        cecos = [str(x).strip() for x in ceco_codigo]
        df_ppt_sel = df_ppt[
            (df_ppt["Mes_A"].isin(meses_sel)) &
            (df_ppt["Proyecto_A"].astype(str).isin(proy)) &
            (df_ppt["CeCo_A"].astype(str).isin(cecos))
        ].copy()

        ingreso_ppt_sel = ingreso(df_ppt_sel, meses_sel, proy, proyecto_nombre)

        df_ppt_sel = df_ppt_sel[df_ppt_sel["Categoria_A"] != "INGRESO"]
        df_ppt_sel = df_ppt_sel[df_ppt_sel["Clasificacion_A"] == clasificacion_nombre]

        ppt_cla_nom = df_ppt_sel.groupby(["Clasificacion_A"], as_index=False)["Neto_A"].sum()
        ppt_cat_nom = df_ppt_sel.groupby(["Clasificacion_A", "Categoria_A"], as_index=False)["Neto_A"].sum()
        ppt_cta_nom = df_ppt_sel.groupby(["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"], as_index=False)["Neto_A"].sum()
        ppt_cla_nom["PPT %"] = np.where(ingreso_ppt_sel != 0, (ppt_cla_nom["Neto_A"] / ingreso_ppt_sel) * 100, 0.0)
        ppt_cat_nom["PPT %"] = np.where(ingreso_ppt_sel != 0, (ppt_cat_nom["Neto_A"] / ingreso_ppt_sel) * 100, 0.0)
        cat_map_ppt = dict(zip(ppt_cat_nom["Categoria_A"], ppt_cat_nom["Neto_A"]))
        ppt_cta_nom["Cat_Total"] = ppt_cta_nom["Categoria_A"].map(cat_map_ppt).fillna(0)
        ppt_cta_nom["PPT % CTA"] = np.where(ppt_cta_nom["Cat_Total"] != 0, (ppt_cta_nom["Neto_A"] / ppt_cta_nom["Cat_Total"]) * 100, 0.0)

        df_real_sel = df_real[
            (df_real["Mes_A"].isin(meses_sel)) &
            (df_real["Proyecto_A"].astype(str).isin(proy)) &
            (df_real["CeCo_A"].astype(str).isin(cecos))
        ].copy()

        ingreso_real_sel = ingreso(df_real_sel, meses_sel, proy, proyecto_nombre)

        df_real_sel = df_real_sel[df_real_sel["Categoria_A"] != "INGRESO"]
        df_real_sel = df_real_sel[df_real_sel["Clasificacion_A"] == clasificacion_nombre]
        real_cla_nom = df_real_sel.groupby(["Clasificacion_A"], as_index=False)["Neto_A"].sum()
        real_cat_nom = df_real_sel.groupby(["Clasificacion_A", "Categoria_A"], as_index=False)["Neto_A"].sum()
        real_cta_nom = df_real_sel.groupby(["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"], as_index=False)["Neto_A"].sum()
        real_cla_nom["REAL %"] = np.where(ingreso_real_sel != 0, (real_cla_nom["Neto_A"] / ingreso_real_sel) * 100, 0.0)
        real_cat_nom["REAL %"] = np.where(ingreso_real_sel != 0, (real_cat_nom["Neto_A"] / ingreso_real_sel) * 100, 0.0)
        cat_map_real = dict(zip(real_cat_nom["Categoria_A"], real_cat_nom["Neto_A"]))
        real_cta_nom["Cat_Total"] = real_cta_nom["Categoria_A"].map(cat_map_real).fillna(0)
        real_cta_nom["REAL % CTA"] = np.where(real_cta_nom["Cat_Total"] != 0, (real_cta_nom["Neto_A"] / real_cta_nom["Cat_Total"]) * 100, 0.0)
        df_cla = ppt_cla_nom.merge(real_cla_nom[["Clasificacion_A", "REAL %"]], on="Clasificacion_A", how="outer").fillna(0)
        df_cla["DIF (pp)"] = df_cla["REAL %"] - df_cla["PPT %"]
        df_cla["% vs PPT"] = np.where(df_cla["PPT %"] != 0, (df_cla["REAL %"] / df_cla["PPT %"] - 1) * 100, 0.0)

        def resaltar(row):
            if row["REAL %"] > row["PPT %"]:
                return ['background-color: red; color: white'] * len(row)
            elif row["REAL %"] < row["PPT %"]:
                return ['background-color: green; color: black'] * len(row)
            return [''] * len(row)

        st.markdown("### Resumen Clasificación (sobre Ingresos)")
        st.dataframe(
            df_cla.set_index("Clasificacion_A").style
                .apply(resaltar, axis=1)
                .format({
                    "PPT %": "{:.2f}%",
                    "REAL %": "{:.2f}%",
                    "DIF (pp)": "{:.2f}",
                    "% vs PPT": "{:.2f}%"
                }),
            use_container_width=True
        )
        df_cat = ppt_cat_nom.merge(real_cat_nom[["Clasificacion_A", "Categoria_A", "REAL %"]], on=["Clasificacion_A", "Categoria_A"], how="outer").fillna(0)
        df_cat["DIF (pp)"] = df_cat["REAL %"] - df_cat["PPT %"]
        df_cat["% vs PPT"] = np.where(df_cat["PPT %"] != 0, (df_cat["REAL %"] / df_cat["PPT %"] - 1) * 100, 0.0)

        df_cta = ppt_cta_nom.merge(
            real_cta_nom[["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A", "REAL % CTA"]],
            on=["Clasificacion_A", "Categoria_A", "Cuenta_Nombre_A"],
            how="outer"
        ).fillna(0)

        df_cta["DIF (pp)"] = df_cta["REAL % CTA"] - df_cta["PPT % CTA"]
        df_cta["% vs PPT"] = np.where(df_cta["PPT % CTA"] != 0, (df_cta["REAL % CTA"] / df_cta["PPT % CTA"] - 1) * 100, 0.0)

        df_cat_out = df_cat[["Categoria_A", "PPT %", "REAL %", "DIF (pp)", "% vs PPT"]].copy()
        df_cat_out["Cuenta_Nombre_A"] = ""

        df_cta_out = df_cta[["Categoria_A", "Cuenta_Nombre_A", "PPT % CTA", "REAL % CTA", "DIF (pp)", "% vs PPT"]].copy()
        df_cta_out = df_cta_out.rename(columns={"PPT % CTA": "PPT %", "REAL % CTA": "REAL %"})

        df_out = pd.concat([df_cat_out, df_cta_out], ignore_index=True)

        gb = GridOptionsBuilder.from_dataframe(df_out)
        gb.configure_default_column(groupable=True)
        gb.configure_column("Categoria_A", rowGroup=True, hide=True)
        gb.configure_column("Cuenta_Nombre_A", header_name="Cuenta", pinned="left")

        pct_formatter = JsCode("""
            function(params) {
                if (params.value === null || params.value === undefined) return '';
                return params.value.toFixed(2) + ' %';
            }
        """)
        for col in ["PPT %", "REAL %", "DIF (pp)", "% vs PPT"]:
            gb.configure_column(col, type=["numericColumn"], aggFunc="last", valueFormatter=pct_formatter)

        gridOptions = gb.build()
        meses_key = "-".join(meses_sel)
        grid_key = f"agrid_cla_{clasificacion_nombre}_{'-'.join(proy)}_{'-'.join(cecos)}_{meses_key}"

        st.markdown("### Categoría (sobre ingresos) + Cuenta (% de su Categoría)")
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
            user, rol = validar_credenciales(df_usuarios, username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = user
                st.session_state["rol"] = rol
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
    
    proyectos = cargar_datos(proyectos_url)

    df_ppt["Proyecto_A"] = df_ppt["Proyecto_A"].astype(str).str.strip()
    df_real["Proyecto_A"] = df_real["Proyecto_A"].astype(str).str.strip()
    proyectos["proyectos"] = proyectos["proyectos"].astype(str).str.strip()
    list_pro = proyectos["proyectos"].tolist()
    st.sidebar.success(f"👤 Usuario: {st.session_state['username']}")

    if st.sidebar.button("Cerrar sesión"):
        for key in ["logged_in", "username", "rol"]:
            st.session_state[key] = "" if key != "logged_in" else False
        st.rerun()
    if st.session_state['rol'] == "admin":
        if st.sidebar.button("🔄 Recargar datos"):
            st.cache_data.clear()
            st.rerun()
    if st.session_state["rol"] in ["admin"] and "ESGARI" in st.session_state["proyectos"]:
        selected = option_menu(
            menu_title=None,
            options=["PPT YTD", "PPT VS ACTUAL", "Ingresos", "OH", "Departamentos", "Consulta", "Meses PPT", "Variaciones", "Comparativa", "Objetivos"],
            icons=[
            "calendar-range",     # PPT YTD
            "bar-chart-steps",    # PPT VS ACTUAL
            "cash-coin",          # Ingresos
            "building",           # OH (Overhead / oficinas)
            "diagram-3",          # Departamentos
            "search",             # Consulta
            "calendar-month",     # Meses PPT
            "arrow-left-right",   # Variaciones
            "bar-chart",          # Comparativa
            "bullseye",           # Objetivos
        ],
            default_index=0,
            orientation="horizontal",
        )
    elif st.session_state["rol"] == "director" or st.session_state["rol"] == "admin":
        selected = option_menu(
        menu_title=None,
        options=["PPT YTD", "PPT VS ACTUAL", "Ingresos", "OH", "Departamentos", "Consulta", "Meses PPT", "Variaciones", "Comparativa", "Objetivos"],
        icons=["Calendar-range", "bar-chart-steps", "cash-coin", "building", "diagram-3", "search", "calendar-month", "arrow-left-right", "bar-chart", "bullseye"],
        default_index=0,
        orientation="horizontal",)

    elif st.session_state["rol"] == "gerente":
        selected = option_menu(
        menu_title=None,
        options=["PPT VS ACTUAL", "Ingresos", "OH", "Departamentos", "Consulta", "Meses PPT"],
        icons=["Calendar-range", "bar-chart-steps", "building", "diagram-3", "search", "calendar-month"],
        default_index=0,
        orientation="horizontal",)

    elif st.session_state["rol"] == "ceco":
        selected = option_menu(
        menu_title=None,
        options=[ "Departamentos", "Consulta"],
        icons=[ "diagram-3", "search"],
        default_index=0,
        orientation="horizontal",)


    if selected == "PPT YTD":

        def tabla_ppt_ytd(df_ppt, mes_corte=None):
            """
            PPT YTD = acumulado desde ene. hasta el mes_corte.
            Si mes_corte es None, toma el último mes disponible en df_ppt.
            """
            meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
            meses_disponibles = [mes for mes in meses_ordenados if mes in df_ppt["Mes_A"].unique().tolist()]

            if not meses_disponibles:
                st.error("No hay meses disponibles en df_ppt (columna Mes_A).")
                return None

            if mes_corte is None:
                mes_corte = meses_disponibles[-1]

            if mes_corte not in meses_disponibles:
                st.error(f"mes_corte inválido: {mes_corte}")
                return None

            idx = meses_disponibles.index(mes_corte)
            meses_ytd = meses_disponibles[:idx + 1]

            # Resumen por proyecto (excluyendo algunos)
            resumen_proyectos = {
                nombre: estado_resultado(
                    df_ppt,
                    meses_ytd,
                    nombre,
                    [str(codigo)],  
                    list_pro
                )
                for nombre, codigo in zip(proyectos["nombre"], proyectos["proyectos"].astype(str))
                if nombre not in {"OFICINAS LUNA", "PATIO", "OFICINAS ANDARES"}
            }
            codigos = proyectos["proyectos"].astype(str).tolist()
            resumen_proyectos["ESGARI"] = estado_resultado(df_ppt, meses_ytd, "ESGARI", codigos, list_pro)

            metricas_seleccionadas = [
                ("Ingreso", "ingreso_proyecto"),
                ("COSS Total", "coss_total"),
                ("Utilidad Bruta", "utilidad_bruta"),
                ("Margen U.B. %", "por_utilidad_bruta"),
                ("G.ADMN", "gadmn_pro"),
                ("Utilidad Operativa", "utilidad_operativa"),
                ("Margen U.O. %", "por_utilidad_operativa"),
                ("OH", "oh_pro"),
                ("EBIT", "ebit"),
                ("Margen EBIT %", "por_ebit"),
                ("Gasto Fin", "gasto_fin_pro"),
                ("Ingreso Fin", "ingreso_fin_pro"),
                ("EBT", "ebt"),
                ("Margen EBT %", "por_ebt"),
            ]

            # Construir tabla
            df_data = []
            for nombre_metrica, clave in metricas_seleccionadas:
                fila = {"Métrica": nombre_metrica}
                for proyecto, datos in resumen_proyectos.items():
                    fila[proyecto] = datos.get(clave, None)
                df_data.append(fila)

            df_tabla = pd.DataFrame(df_data)
            st.subheader(f"PPT YTD")
            st.dataframe(df_tabla, use_container_width=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_tabla.to_excel(writer, index=False, sheet_name="Resumen")
            output.seek(0)

            st.download_button(
                label="📥 Descargar Excel",
                data=output,
                file_name=f"resumen_estado_resultado_PPT_YTD_{mes_corte}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            return df_tabla
        tabla_ppt_ytd(df_ppt, mes_corte=None)


    elif selected == "PPT VS ACTUAL":

        def tabla_variacion_pct(df_ppt, df_real, meses_seleccionado, proyecto_nombre, proyecto_codigo):
            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return None

            ppt = estado_resultado(df_ppt, meses_seleccionado, proyecto_nombre, proyecto_codigo, list_pro)
            real = estado_resultado(df_real, meses_seleccionado, proyecto_nombre, proyecto_codigo, list_pro)

            metricas_base = [
                ("Ingreso", "ingreso_proyecto"),
                ("COSS", "coss_pro"),
                ("COSS Patio", "patio_pro"),
                ("COSS Total", "coss_total"),
                ("Utilidad Bruta", "utilidad_bruta"),
                ("G.ADMN", "gadmn_pro"),
                ("Utilidad Operativa", "utilidad_operativa"),
            ]

            metricas_extra = [
                ("OH", "oh_pro"),
                ("EBIT", "ebit"),
                ("Gasto Fin", "gasto_fin_pro"),
                ("Ingreso Fin", "ingreso_fin_pro"),
                ("EBT", "ebt"),
            ]

            # ✅ Gerente: solo hasta Utilidad Operativa
            if st.session_state.get("rol", "").lower() == "gerente":
                metricas = metricas_base
            else:
                metricas = metricas_base + metricas_extra

            filas = []
            for concepto, clave in metricas:
                ppt_val = ppt.get(clave, 0) or 0
                real_val = real.get(clave, 0) or 0
                var_pct = (real_val / ppt_val - 1) if ppt_val != 0 else 0
                filas.append({"CONCEPTO": concepto, "VARIACIÓN %": var_pct})

            df_out = pd.DataFrame(filas)
            df_out["VARIACIÓN %"] = df_out["VARIACIÓN %"].map(lambda x: f"{x*100:,.2f}%")

            st.subheader(f"Variación % REAL vs PPT — {proyecto_nombre}")
            st.dataframe(df_out, use_container_width=True)
            return df_out


        col1, col2 = st.columns(2)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        proyecto_codigo, proyecto_nombre = filtro_pro(col2)

        df_agrid = df_ppt

        tabla_variacion_pct(df_ppt, df_real, meses_seleccionado, proyecto_nombre, proyecto_codigo)

        # ✅ Tabs: gerente no ve financieros
        if st.session_state.get("rol", "").lower() == "gerente":
            ventanas = ['INGRESO', 'COSS', 'G.ADMN']
        else:
            ventanas = ['INGRESO', 'COSS', 'G.ADMN', 'GASTOS FINANCIEROS', 'INGRESO FINANCIERO']

        tabs = st.tabs(ventanas)
        with tabs[0]:
            tabla_comparativa("PPT", df_agrid, df_real, proyecto_codigo, meses_seleccionado, "Categoria_A", "INGRESO", "Tabla de Ingresos")
        with tabs[1]:
            tabla_comparativa("PPT", df_agrid, df_real, proyecto_codigo, meses_seleccionado, "Clasificacion_A", "COSS", "Tabla de COSS")
        with tabs[2]:
            tabla_comparativa("PPT", df_agrid, df_real, proyecto_codigo, meses_seleccionado, "Clasificacion_A", "G.ADMN", "Tabla de G.ADMN")
        if st.session_state.get("rol", "").lower() != "gerente":
            with tabs[3]:
                tabla_comparativa("PPT", df_agrid, df_real, proyecto_codigo, meses_seleccionado, "Clasificacion_A", "GASTOS FINANCIEROS", "Tabla de Gastos Financieros")
            with tabs[4]:
                tabla_comparativa("PPT", df_agrid, df_real, proyecto_codigo, meses_seleccionado, "Categoria_A", "INGRESO POR REVALUACION CAMBIARIA", "Tabla de Ingreso Financiero")


    elif selected == "Ingresos":

        def tabla_ingresos(df_ppt, df_real, meses_seleccionado, proyectos_seleccionados):
            if not meses_seleccionado:
                st.error("Favor de seleccionar por lo menos un mes")
                return
            MESES_ORDENADOS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
            if not proyectos_seleccionados:
                st.error("Favor de seleccionar por lo menos un proyecto")
                return
            
            if "ESGARI" in proyectos_seleccionados:
                proyectos_ppt = df_ppt["Proyecto_A"].astype(str).unique().tolist()
                proyectos_real = df_real["Proyecto_A"].astype(str).unique().tolist()
            else:
                proyectos_ppt = [str(p) for p in proyectos_seleccionados]
                proyectos_real = [str(p) for p in proyectos_seleccionados]

            df_ppt_f = df_ppt[
                (df_ppt["Mes_A"].isin(meses_seleccionado)) &
                (df_ppt["Proyecto_A"].astype(str).isin(proyectos_ppt)) &
                (df_ppt["Categoria_A"] == "INGRESO")
            ].copy()

            df_real_f = df_real[
                (df_real["Mes_A"].isin(meses_seleccionado)) &
                (df_real["Proyecto_A"].astype(str).isin(proyectos_real)) &
                (df_real["Categoria_A"] == "INGRESO")
            ].copy()

            ppt_por_mes = (
                df_ppt_f
                .groupby("Mes_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "PPT"})
            )

            real_por_mes = (
                df_real_f
                .groupby("Mes_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "REAL"})
            )
            tabla = ppt_por_mes.merge(real_por_mes, on="Mes_A", how="outer").fillna(0)

            tabla["DIF"] = tabla["REAL"] - tabla["PPT"]
            tabla["%"] = tabla.apply(
                lambda r: (r["REAL"] / r["PPT"] - 1) if r["PPT"] != 0 else 0,
                axis=1
            )

            if "MESES_ORDENADOS" in globals():
                orden = {m: i for i, m in enumerate(MESES_ORDENADOS)}
                tabla["__ord"] = tabla["Mes_A"].map(orden).fillna(999).astype(int)
                tabla = tabla.sort_values("__ord").drop(columns="__ord")
            else:
                tabla = tabla.sort_values("Mes_A")

            total_ppt = tabla["PPT"].sum()
            total_real = tabla["REAL"].sum()
            total_dif = total_real - total_ppt
            total_pct = (total_real / total_ppt - 1) if total_ppt != 0 else 0

            total_row = pd.DataFrame([{
                "Mes_A": "TOTAL",
                "PPT": total_ppt,
                "REAL": total_real,
                "DIF": total_dif,
                "%": total_pct
            }])

            tabla_final = pd.concat([tabla, total_row], ignore_index=True)
            st.subheader("📈 Comparativa de Ingresos")
            st.dataframe(tabla_final, use_container_width=True)
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=tabla["Mes_A"],
                y=tabla["PPT"],
                mode="lines+markers",
                name="Ingreso PPT"
            ))

            fig.add_trace(go.Scatter(
                x=tabla["Mes_A"],
                y=tabla["REAL"],
                mode="lines+markers",
                name="Ingreso REAL"
            ))

            fig.update_layout(
                title="Ingreso PPT vs REAL",
                xaxis_title="Mes",
                yaxis_title="Ingreso",
                hovermode="x unified",
                legend_title="Tipo",
                height=420
            )

            st.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        meses_seleccionado = filtro_meses(col1, df_ppt, selected)
        proyecto_codigo, proyecto_nombre = filtro_pro(col2)

        # para reusar tu función que espera lista:
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
            df_ppt_f = df_ppt[
                (df_ppt["Mes_A"].isin(meses_seleccionado)) &
                (df_ppt["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                (df_ppt["Clasificacion_A"].isin(clas_oh)) &
                (df_ppt["CeCo_A"].astype(str).isin([str(x) for x in cecos_seleccionados]))
            ].copy()

            df_real_f = df_real[
                (df_real["Mes_A"].isin(meses_seleccionado)) &
                (df_real["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                (df_real["Clasificacion_A"].isin(clas_oh)) &
                (df_real["CeCo_A"].astype(str).isin([str(x) for x in cecos_seleccionados]))
            ].copy()

            ppt_por_mes = (
                df_ppt_f.groupby("Mes_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "PPT"})
            )

            real_por_mes = (
                df_real_f.groupby("Mes_A", as_index=False)["Neto_A"]
                .sum()
                .rename(columns={"Neto_A": "REAL"})
            )

            tabla = ppt_por_mes.merge(real_por_mes, on="Mes_A", how="outer").fillna(0)
            tabla["DIF"] = tabla["REAL"] - tabla["PPT"]
            tabla["%"] = tabla.apply(lambda r: (r["REAL"] / r["PPT"] - 1) if r["PPT"] != 0 else 0, axis=1)
            orden = {m: i for i, m in enumerate(MESES_ORDENADOS)}
            tabla["__ord"] = tabla["Mes_A"].map(orden).fillna(999).astype(int)
            tabla = tabla.sort_values("__ord").drop(columns="__ord")

            total_ppt = float(tabla["PPT"].sum())
            total_real = float(tabla["REAL"].sum())
            total_dif = total_real - total_ppt
            total_pct = (total_real / total_ppt - 1) if total_ppt != 0 else 0

            total_row = pd.DataFrame([{
                "Mes_A": "TOTAL",
                "PPT": total_ppt,
                "REAL": total_real,
                "DIF": total_dif,
                "%": total_pct
            }])

            tabla_final = pd.concat([tabla, total_row], ignore_index=True)

            st.subheader("📌 OH — PPT vs REAL")
            st.dataframe(tabla_final, use_container_width=True)

            return tabla_final

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
                    "PPT",
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
                    "PPT",
                    df_agrid_oh,
                    df_actual_oh,
                    proyectos_oh,
                    meses_seleccionado,
                    "Clasificacion_A",
                    "G.ADMN",
                    "OH - Tabla G.ADMN"
                )

    elif selected == "Departamentos":
        def tabla_departamentos(df_ppt, df_real, meses_seleccionado, cecos_seleccionados, cecos_df):
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

            df_ppt["Proyecto_A"] = df_ppt["Proyecto_A"].astype(str).str.strip()
            df_real["Proyecto_A"] = df_real["Proyecto_A"].astype(str).str.strip()
            df_ppt["CeCo_A"] = df_ppt["CeCo_A"].astype(str).str.strip()
            df_real["CeCo_A"] = df_real["CeCo_A"].astype(str).str.strip()

            cecos_sel = [str(x) for x in cecos_seleccionados]

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
            tabla["%"] = np.where(tabla["PPT"] != 0, (tabla["REAL"] / tabla["PPT"]) - 1, 0)

            # ---- map CeCo nombre ----
            cecos_map = cecos_df.copy()
            cecos_map["ceco"] = cecos_map["ceco"].astype(str).str.strip()
            cecos_map["nombre"] = cecos_map["nombre"].astype(str).str.strip()

            tabla = tabla.merge(
                cecos_map.rename(columns={"ceco": "CeCo_A", "nombre": "ceco"})[["CeCo_A", "ceco"]],
                on="CeCo_A",
                how="left"
            )
            tabla["ceco"] = tabla["ceco"].fillna(tabla["CeCo_A"])

            tabla = tabla[["ceco", "REAL", "PPT", "DIF", "%"]]

            # ---- total ----
            total_ppt = float(tabla["PPT"].sum())
            total_real = float(tabla["REAL"].sum())
            total_dif = total_real - total_ppt
            total_pct = (total_real / total_ppt - 1) if total_ppt != 0 else 0

            total_row = pd.DataFrame([{
                "ceco": "TOTAL",
                "REAL": total_real,
                "PPT": total_ppt,
                "DIF": total_dif,
                "%": total_pct
            }])

            tabla_final = pd.concat([tabla, total_row], ignore_index=True)

            def color_fila(row):
                if row["ceco"] == "TOTAL":
                    return ["background-color: #1f4e79; color: white; font-weight: bold"] * len(row)
                v = row["%"]
                if v >= 0:
                    bg = "#92D050"
                elif v >= -0.05:
                    bg = "#FFD966"
                else:
                    bg = "#FF0000"
                return [f"background-color: {bg}; color: black"] * len(row)

            styled = (
                tabla_final.style
                .apply(color_fila, axis=1)
                .format({
                    "REAL": "${:,.2f}",
                    "PPT": "${:,.2f}",
                    "DIF": "${:,.2f}",
                    "%": "{:.2%}",
                })
            )

            st.subheader("Departamentos")
            st.dataframe(styled, use_container_width=True)

            return tabla_final
        col1, col2 = st.columns(2)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        ceco_codigo, ceco_nombre = filtro_ceco(col2)

        tabla_final = tabla_departamentos(df_ppt, df_real, meses_seleccionado, ceco_codigo, cecos)
        if tabla_final is not None and not tabla_final.empty:

            ventanas = ["Grafico PPT vs Real", "Grafico PPT", "Grafico Real"]
            tabs = st.tabs(ventanas)

            tabla_graf = (tabla_final[tabla_final["ceco"] != "TOTAL"].sort_values("DIF", ascending=False).copy())

            with tabs[0]:
                if not tabla_graf.empty:
                    fig = go.Figure()
                    fig.add_bar(x=tabla_graf["ceco"], y=tabla_graf["PPT"], name="PPT")
                    fig.add_bar(x=tabla_graf["ceco"], y=tabla_graf["REAL"], name="REAL")
                    fig.update_layout(
                        title="PPT vs REAL por Departamento",
                        xaxis_title="Departamento",
                        yaxis_title="Monto",
                        barmode="group",
                        height=450,
                        legend_title="Tipo",
                        xaxis_tickangle=-25
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with tabs[1]:
                if not tabla_graf.empty:
                    fig = go.Figure()
                    fig.add_bar(x=tabla_graf["ceco"], y=tabla_graf["PPT"], name="PPT")
                    fig.update_layout(
                        title="PPT por Departamento",
                        xaxis_title="Departamento",
                        yaxis_title="Monto PPT",
                        height=450,
                        xaxis_tickangle=-25
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with tabs[2]:
                if not tabla_graf.empty:
                    fig = go.Figure()
                    fig.add_bar(x=tabla_graf["ceco"], y=tabla_graf["REAL"], name="REAL")
                    fig.update_layout(
                        title="REAL por Departamento",
                        xaxis_title="Departamento",
                        yaxis_title="Monto REAL",
                        height=450,
                        xaxis_tickangle=-25
                    )
                    st.plotly_chart(fig, use_container_width=True)
            with st.expander("COSS y G.ADMN", expanded=False):

                if not meses_seleccionado or not ceco_codigo:
                    st.info("Selecciona meses y CeCo para ver el detalle.")
                else:
                    proyectos_oh = ["8002", "8004"]
                    df_agrid_oh = df_ppt[
                        (df_ppt["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                        (df_ppt["CeCo_A"].astype(str).isin([str(x) for x in ceco_codigo]))
                    ].copy()

                    df_actual_oh = df_real[
                        (df_real["Proyecto_A"].astype(str).isin(proyectos_oh)) &
                        (df_real["CeCo_A"].astype(str).isin([str(x) for x in ceco_codigo]))
                    ].copy()

                    st.markdown("### 🔹 COSS")
                    tabla_comparativa(
                        tipo_com="PPT",
                        df_agrid=df_agrid_oh,
                        df_ppt=df_actual_oh,
                        proyecto_codigo=proyectos_oh,
                        meses_seleccionado=meses_seleccionado,
                        clasificacion="Clasificacion_A",
                        categoria="COSS",
                        titulo="COSS"
                    )

                    st.markdown("---")

                    st.markdown("### 🔹 G.ADMN")
                    tabla_comparativa(
                        tipo_com="PPT",
                        df_agrid=df_agrid_oh,
                        df_ppt=df_actual_oh,
                        proyecto_codigo=proyectos_oh,
                        meses_seleccionado=meses_seleccionado,
                        clasificacion="Clasificacion_A",
                        categoria="G.ADMN",
                        titulo="G.ADMN"
                    )

    elif selected == "Consulta":

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

            df_ppt["Cuenta_A"] = df_ppt["Cuenta_A"].astype(str).str.strip()
            df_real["Cuenta_A"] = df_real["Cuenta_A"].astype(str).str.strip()
            df_ppt["Cuenta_Nombre_A"] = df_ppt["Cuenta_Nombre_A"].astype(str).str.strip()
            df_real["Cuenta_Nombre_A"] = df_real["Cuenta_Nombre_A"].astype(str).str.strip()
            cuentas_df = pd.concat([
                df_ppt[["Cuenta_A", "Cuenta_Nombre_A"]],
                df_real[["Cuenta_A", "Cuenta_Nombre_A"]]
            ]).drop_duplicates().sort_values("Cuenta_Nombre_A")

            opciones_cuenta = ["TODAS"] + cuentas_df["Cuenta_Nombre_A"].tolist()

            cuenta_seleccionada = st.selectbox(
                "Selecciona una cuenta",
                opciones_cuenta
            )
            df_ppt_f = df_ppt[
                (df_ppt["Mes_A"].isin(meses_seleccionado)) &
                (df_ppt["CeCo_A"].astype(str).isin([str(x) for x in cecos_seleccionados])) &
                (df_ppt["Proyecto_A"].astype(str).isin([str(x) for x in proyectos_seleccionados]))
            ].copy()

            df_real_f = df_real[
                (df_real["Mes_A"].isin(meses_seleccionado)) &
                (df_real["CeCo_A"].astype(str).isin([str(x) for x in cecos_seleccionados])) &
                (df_real["Proyecto_A"].astype(str).isin([str(x) for x in proyectos_seleccionados]))
            ].copy()
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

            tabla = ppt_resumen.merge(real_resumen, on="Cuenta_Nombre_A", how="outer").fillna(0)
            tabla["DIF"] = tabla["REAL"] - tabla["PPT"]
            tabla["%"] = np.where(
                tabla["PPT"] != 0,
                (tabla["REAL"] / tabla["PPT"]) - 1,
                0
            )

            st.subheader("Consulta por Cuenta")
            st.dataframe(
                tabla.style.format({
                    "PPT": "${:,.2f}",
                    "REAL": "${:,.2f}",
                    "DIF": "${:,.2f}",
                    "%": "{:.2%}"
                }),
                use_container_width=True
            )
            if not tabla.empty:
                fig = go.Figure()

                fig.add_bar(
                    x=tabla["Cuenta_Nombre_A"],
                    y=tabla["PPT"],
                    name="PPT"
                )

                fig.add_bar(
                    x=tabla["Cuenta_Nombre_A"],
                    y=tabla["REAL"],
                    name="REAL"
                )

                fig.update_layout(
                    title="PPT vs REAL por Cuenta",
                    xaxis_title="Cuenta",
                    yaxis_title="Monto",
                    barmode="group",
                    height=420,
                    legend_title="Tipo",
                    xaxis_tickangle=-30
                )

                st.plotly_chart(fig, use_container_width=True)
            return tabla
        
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

                # Renombrar filas
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

                # --- Estilo visual profesional para tabla mensual ---
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
                        .render()
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

                # Aplicar formato visual con el formateador JS
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

                # Mostrar en Streamlit
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

    elif selected == "Variaciones":
        meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        meses_disponibles = [m for m in meses_ordenados if (m in df_ppt["Mes_A"].unique()) or (m in df_real["Mes_A"].unique())]

        meses_sel = st.multiselect(
            "Selecciona mes(es):",
            options=meses_disponibles,
            default=meses_disponibles[-1:] if meses_disponibles else [],
            key="cmp_meses_excel"
        )
        if not meses_sel:
            st.error("Favor de seleccionar por lo menos un mes.")
            st.stop()
        col1, col2, col3 = st.columns(3)
        meses_seleccionado = filtro_meses(col1, df_ppt)
        proyecto_codigo, proyecto_nombre = filtro_pro(col2)
        ceco_codigo, ceco_nombre = filtro_ceco(col3)

        seccion_analisis_por_clasificacion(df_ppt, df_real, ingreso, meses_seleccionado, proyecto_codigo, proyecto_nombre, "COSS", ceco_codigo, ceco_nombre)
        seccion_analisis_especial_porcentual(df_ppt, df_real, ingreso, meses_seleccionado, proyecto_codigo, proyecto_nombre, ceco_codigo, ceco_nombre, patio, "Patio")
        seccion_analisis_por_clasificacion(df_ppt, df_real, ingreso, meses_seleccionado, proyecto_codigo, proyecto_nombre, "G.ADMN", ceco_codigo, ceco_nombre)

        if st.session_state["rol"] == "admin":
            seccion_analisis_por_clasificacion(df_ppt, df_real, ingreso, meses_seleccionado, proyecto_codigo, proyecto_nombre, "GASTOS FINANCIEROS", ceco_codigo, ceco_nombre)
            seccion_analisis_especial_porcentual(df_ppt, df_real, ingreso, meses_seleccionado, proyecto_codigo, proyecto_nombre, ceco_codigo, ceco_nombre, oh, "OH")


    elif selected == "Comparativa":

        st.subheader("Comparativa de Ingresos")
        meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        meses_disponibles = [m for m in meses_ordenados if (m in df_ppt["Mes_A"].unique()) or (m in df_real["Mes_A"].unique())]

        meses_sel = st.multiselect(
            "Selecciona mes(es):",
            options=meses_disponibles,
            default=meses_disponibles[-1:] if meses_disponibles else [],
            key="cmp_meses_excel"
        )
        if not meses_sel:
            st.error("Favor de seleccionar por lo menos un mes.")
            st.stop()
        proyectos_local = proyectos.copy()
        proyectos_local["proyectos"] = proyectos_local["proyectos"].astype(str).str.strip()
        proyectos_local["nombre"] = proyectos_local["nombre"].astype(str).str.strip()

        allowed = [str(x).strip() for x in st.session_state.get("proyectos", [])]
        if allowed == ["ESGARI"]:
            df_visibles = proyectos_local.copy()
        else:
            df_visibles = proyectos_local[proyectos_local["proyectos"].isin(allowed)].copy()
        df_ppt_ing = df_ppt[(df_ppt["Mes_A"].isin(meses_sel)) & (df_ppt["Categoria_A"] == "INGRESO")].copy()
        df_real_ing = df_real[(df_real["Mes_A"].isin(meses_sel)) & (df_real["Categoria_A"] == "INGRESO")].copy()

        df_ppt_ing["Proyecto_A"] = df_ppt_ing["Proyecto_A"].astype(str).str.strip()
        df_real_ing["Proyecto_A"] = df_real_ing["Proyecto_A"].astype(str).str.strip()
        nombres = df_visibles["nombre"].tolist()
        codigos = df_visibles["proyectos"].tolist()
        nombre_por_codigo = dict(zip(codigos, nombres))
        real_por_proy = {nombre_por_codigo[c]: float(df_real_ing.loc[df_real_ing["Proyecto_A"] == c, "Neto_A"].sum()) for c in codigos}
        ppt_por_proy  = {nombre_por_codigo[c]: float(df_ppt_ing.loc[df_ppt_ing["Proyecto_A"] == c, "Neto_A"].sum()) for c in codigos}
        inc_por_proy = {}
        for n in nombres:
            ppt_v = ppt_por_proy.get(n, 0.0)
            real_v = real_por_proy.get(n, 0.0)
            inc_por_proy[n] = (real_v / ppt_v - 1) if ppt_v != 0 else 0.0
        tabla_excel = pd.DataFrame(
            {
                **{n: [real_por_proy.get(n, 0.0), ppt_por_proy.get(n, 0.0), inc_por_proy.get(n, 0.0)] for n in nombres}
            },
            index=["YTD REAL", "PPT", "INCREMENTO %"]
        )

        st.markdown("Tabla")
        st.dataframe(
            tabla_excel.style
            .format(
                {col: "${:,.0f}" for col in tabla_excel.columns},
                subset=pd.IndexSlice[["YTD REAL", "PPT"], :]
            )
            .format(
                {col: "{:.2%}" for col in tabla_excel.columns},
                subset=pd.IndexSlice[["INCREMENTO %"], :]
            ),
            use_container_width=True
        )
        x = nombres
        y_real = [real_por_proy.get(n, 0.0) for n in x]
        y_ppt  = [ppt_por_proy.get(n, 0.0) for n in x]
        y_inc  = [inc_por_proy.get(n, 0.0) for n in x]
        fig = go.Figure()
        fig.add_bar(x=x, y=y_real, name="YTD REAL")
        fig.add_bar(x=x, y=y_ppt,  name="PPT")

        # Etiquetas de incremento %
        for i, n in enumerate(x):
            top = max(y_real[i], y_ppt[i])
            fig.add_annotation(
                x=n,
                y=top * 1.08 if top != 0 else 0,
                text=f"{y_inc[i]*100:,.2f}%",
                showarrow=False
            )

        fig.update_layout(
            title=f"Ingresos — YTD REAL vs PPT ({', '.join(meses_sel)})",
            xaxis_title="Proyecto",
            yaxis_title="MXN",
            barmode="group",
            height=520,
            hovermode="x unified",
            xaxis_tickangle=-25
        )

        st.markdown("### 📈 Gráfico de Ingresos")
        st.plotly_chart(fig, use_container_width=True)


    elif selected == "Objetivos":
        objetivo_uo = {
            "ARRAYANES": 0.24,
            "CENTRAL": 0.29,
            "CHALCO": 0.24,
            "CONTI.": 0.30,
            "F. DED.": 0.27,
            "F. SPOT": 0.24,
            "INT.": 0.24,
            "WH": 0.21,
            "MZN.": 0.25,
            "BAJIO": 0.26,
            "ESGARI": 0.25
        }

        meses_ordenados = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.","jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
        meses_disponibles = [
            m for m in meses_ordenados
            if (m in df_ppt["Mes_A"].unique()) or (m in df_real["Mes_A"].unique())
        ]

        meses_sel = st.multiselect(
            "Selecciona mes(es):",
            options=meses_disponibles,
            default=meses_disponibles[-1:] if meses_disponibles else [],
            key="cmp_meses_uo_manual"
        )

        if not meses_sel:
            st.error("Favor de seleccionar por lo menos un mes.")
            st.stop()
        proyectos_local = proyectos.copy()
        proyectos_local["proyectos"] = proyectos_local["proyectos"].astype(str).str.strip()
        proyectos_local["nombre"] = proyectos_local["nombre"].astype(str).str.strip()

        allowed = [str(x).strip() for x in st.session_state.get("proyectos", [])]

        if allowed == ["ESGARI"]:
            df_visibles = proyectos_local.copy()
        else:
            df_visibles = proyectos_local[proyectos_local["proyectos"].isin(allowed)].copy()

        nombres = df_visibles["nombre"].tolist()
        codigos = df_visibles["proyectos"].tolist()
        real_pct = {}

        for nombre, codigo in zip(nombres, codigos):
            codigo_list = [str(codigo)]

            er_real = estado_resultado(
                df_real,
                meses_sel,
                nombre,
                codigo_list,
                list_pro
            )

            real_pct[nombre] = float(er_real.get("por_utilidad_operativa", 0) or 0)
        ppt_pct = {n: objetivo_uo.get(n, 0) for n in nombres}
        tabla_excel = pd.DataFrame(
            {n: [ppt_pct.get(n, 0), real_pct.get(n, 0)] for n in nombres},
            index=["PPT", "REAL"]
        )

        st.markdown("Utilidad Operativa")
        st.dataframe(
            tabla_excel.style.format("{:.2%}"),
            use_container_width=True
        )

        fig = go.Figure()

        fig.add_bar(
            x=nombres,
            y=[ppt_pct[n] for n in nombres],
            name="PPT",
            text=[f"{ppt_pct[n]*100:.2f}%" for n in nombres],
            textposition="inside"
        )

        fig.add_bar(
            x=nombres,
            y=[real_pct[n] for n in nombres],
            name="REAL",
            text=[f"{real_pct[n]*100:.2f}%" for n in nombres],
            textposition="inside"
        )

        fig.update_layout(
            title=f"% Utilidad Operativa — Objetivo vs Real ({', '.join(meses_sel)})",
            xaxis_title="Proyecto",
            yaxis_title="Porcentaje",
            barmode="group",
            height=520,
            hovermode="x unified",
            xaxis_tickformat=".0%",
            xaxis_tickangle=-25
        )

        st.markdown("Utilidad Operativa")
        st.plotly_chart(fig, use_container_width=True)