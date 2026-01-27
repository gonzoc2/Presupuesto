import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from functools import reduce
import numpy as np
from streamlit_option_menu import option_menu
import re

st.set_page_config(
    page_title="Balance General",
    page_icon="🚚", 
    layout="wide"    
)

logo_base64 = """
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
"""

st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{logo_base64}" alt="Logo de la Empresa" width="300">
    </div>
    """,
    unsafe_allow_html=True,
)


EMPRESAS = ["HOLDING", "FWD", "WH", "UBIKARGA", "EHM", "RESA", "GREEN"]
COLUMNAS_CUENTA = ["Cuenta", "Descripción"]
NUMERO_CUENTA = ["Cuenta"]
COLUMNAS_MONTO = ["Saldo final", "Saldo"]
CLASIFICACIONES_PRINCIPALES = ["ACTIVO", "PASIVO", "CAPITAL"]

balance_url = st.secrets["urls"]["balance_url"]
balance_ly = st.secrets["urls"]["balance_ly"]
mapeo_url = st.secrets["urls"]["mapeo_url"]
info_manual_url = st.secrets["urls"]["info_manual"]  

with st.sidebar:
    st.title("Controles")
    if st.button("🔄 Recargar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

def limpiar_cuenta(x):
    """Convierte cuenta a int, quitando comas/espacios/texto (ej: '400,000,006' -> 400000006)."""
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]

    s = re.sub(r"[^\d-]", "", s)

    if s == "" or s == "-":
        return pd.NA

    try:
        return int(s)
    except:
        return pd.NA


def _encontrar_columna(df, candidatos):
    return next((c for c in candidatos if c in df.columns), None)

def _to_numeric_money(series):
    s = series.astype(str).replace(r"[\$,]", "", regex=True)
    return pd.to_numeric(s, errors="coerce").fillna(0)

@st.cache_data(show_spinner="Cargando Excel (URL)...")
def load_excel_from_url(url: str) -> pd.DataFrame:
    r = requests.get(url)
    r.raise_for_status()
    file = BytesIO(r.content)
    df = pd.read_excel(file, engine="openpyxl")
    df.columns = df.columns.str.strip()
    return df

@st.cache_data(show_spinner="Cargando mapeo de cuentas...")
def cargar_mapeo(url: str) -> pd.DataFrame:
    df_mapeo = load_excel_from_url(url)
    if "Cuenta" not in df_mapeo.columns:
        st.error("❌ El mapeo debe contener una columna llamada 'Cuenta'.")
        return pd.DataFrame()

    df_mapeo["Cuenta"] = df_mapeo["Cuenta"].apply(limpiar_cuenta)
    df_mapeo = df_mapeo.dropna(subset=["Cuenta"]).drop_duplicates(subset=["Cuenta"], keep="first")
    return df_mapeo

@st.cache_data(show_spinner="Cargando hojas del balance...")
def cargar_balance_multi_hojas(url: str, hojas: list[str]) -> dict[str, pd.DataFrame]:
    r = requests.get(url)
    r.raise_for_status()
    file = BytesIO(r.content)

    data = {}
    for hoja in hojas:
        try:
            file.seek(0)  
            df = pd.read_excel(file, sheet_name=hoja, engine="openpyxl")
            df.columns = df.columns.str.strip()
            data[hoja] = df
        except Exception as e:
            data[hoja] = pd.DataFrame()
            st.warning(f"⚠️ No se pudo leer la hoja {hoja}: {e}")
    return data


OPTIONS = [
    "BALANCE GENERAL",
    "BALANCE POR EMPRESA", "ESTADO DE RESULTADOS", "ESCENARIOS EDR", "ESCENARIOS BALANCE"
]

selected = option_menu(
    menu_title=None,
    options=OPTIONS,
    icons=["building", "bar-chart-line", "clipboard-data", "graph-up-arrow", "bar-chart-line"],
    default_index=0,
    orientation="horizontal",
)

def autoclasificar_resultados(df_merged, col_cuenta):
    """
    Si no viene en mapeo:
    400,000,000 a 499,999,999  -> RESULTADOS / INGRESO
    >= 500,000,000             -> RESULTADOS / GASTO
    """

    df_merged[col_cuenta] = pd.to_numeric(df_merged[col_cuenta], errors="coerce")
    mask_no_map = df_merged["CLASIFICACION"].isna()
    mask_ing = mask_no_map & (df_merged[col_cuenta] >= 400000000) & (df_merged[col_cuenta] < 500000000)
    mask_gas = mask_no_map & (df_merged[col_cuenta] >= 500000000)
    df_merged.loc[mask_ing, "CLASIFICACION"] = "RESULTADOS"
    df_merged.loc[mask_ing, "CATEGORIA"] = "INGRESO"
    df_merged.loc[mask_gas, "CLASIFICACION"] = "RESULTADOS"
    df_merged.loc[mask_gas, "CATEGORIA"] = "GASTO"

    return df_merged


def tabla_balance_por_empresa():
    st.subheader("Balance General por Empresa")

    df_mapeo_local = cargar_mapeo(mapeo_url)
    if df_mapeo_local.empty:
        st.stop()

    data_empresas = cargar_balance_multi_hojas(balance_url, EMPRESAS)
    resultados_balance = []
    balances_detallados = {}
    cuentas_no_mapeadas = []
    for empresa in EMPRESAS:
        df = data_empresas.get(empresa, pd.DataFrame()).copy()
        if df.empty:
            continue

        col_cuenta = _encontrar_columna(df, COLUMNAS_CUENTA)
        col_monto = _encontrar_columna(df, COLUMNAS_MONTO)

        if not col_cuenta or not col_monto:
            st.warning(f"⚠️ {empresa}: columnas inválidas (Cuenta / Saldo).")
            continue

        df[col_cuenta] = df[col_cuenta].apply(limpiar_cuenta)
        df[col_monto] = _to_numeric_money(df[col_monto])
        df = df.dropna(subset=[col_cuenta])
        df = df.groupby(col_cuenta, as_index=False)[col_monto].sum()
        df_merged = df.merge(
            df_mapeo_local[["Cuenta", "CLASIFICACION", "CATEGORIA"]],
            left_on=col_cuenta,
            right_on="Cuenta",
            how="left",
        )

        df_merged["EN_MAPEO"] = df_merged["CLASIFICACION"].notna()
        df_merged = autoclasificar_resultados(df_merged, col_cuenta)
        no_mapeadas = df_merged[~df_merged["EN_MAPEO"]].copy()

        if not no_mapeadas.empty:
            no_mapeadas["EMPRESA"] = empresa
            cuentas_no_mapeadas.append(
                no_mapeadas[[col_cuenta, col_monto, "EMPRESA"]]
                .rename(columns={col_cuenta: "Cuenta", col_monto: "Saldo"})
            )

        df_merged = df_merged[~df_merged["CLASIFICACION"].isna()].copy()
        if df_merged.empty:
            st.warning(f"⚠️ {empresa}: sin coincidencias con el mapeo.")
            continue

        df_balance = df_merged[df_merged["CLASIFICACION"].isin(["ACTIVO", "PASIVO", "CAPITAL"])].copy()
        if df_balance.empty:
            st.warning(f"⚠️ {empresa}: sin coincidencias para BALANCE (ACTIVO/PASIVO/CAPITAL).")
            continue

        resumen = (
            df_balance.groupby(["CLASIFICACION", "CATEGORIA"])[col_monto]
            .sum()
            .reset_index()
            .rename(columns={col_monto: empresa})
        )

        resultados_balance.append(resumen)
        balances_detallados[empresa] = df_merged.copy()

    if not resultados_balance:
        st.error("❌ No se pudo generar información consolidada.")
        return

    data_resultados = []
    for empresa in EMPRESAS:
        df_raw = data_empresas.get(empresa, pd.DataFrame()).copy()
        if df_raw.empty:
            continue

        col_cuenta_raw = _encontrar_columna(df_raw, NUMERO_CUENTA)
        col_monto_raw = _encontrar_columna(df_raw, COLUMNAS_MONTO)
        if not col_cuenta_raw or not col_monto_raw:
            st.warning(f"⚠️ {empresa}: no encontré columnas de Cuenta/Saldo para resultados.")
            continue
        df_raw[col_cuenta_raw] = df_raw[col_cuenta_raw].apply(limpiar_cuenta)
        df_raw[col_monto_raw] = _to_numeric_money(df_raw[col_monto_raw])
        df_raw = df_raw.dropna(subset=[col_cuenta_raw])
        df_cta = df_raw.groupby(col_cuenta_raw, as_index=False)[col_monto_raw].sum()
        ingreso = df_cta.loc[
            (df_cta[col_cuenta_raw] > 400000000) & (df_cta[col_cuenta_raw] < 500000000),
            col_monto_raw
        ].sum()
        gasto = df_cta.loc[
            (df_cta[col_cuenta_raw] > 500000000),
            col_monto_raw
        ].sum()
        utilidad = ingreso + gasto
        data_resultados.append({
            "EMPRESA": empresa,
            "INGRESO": float(ingreso),
            "GASTO": float(gasto),
            "UTILIDAD": float(utilidad),
        })

    df_resultados = pd.DataFrame(data_resultados)
    st.markdown("### Estado de Resultados por Empresa")
    if df_resultados.empty:
        st.info("No se pudo calcular estado de resultados (revisa hojas/columnas).")
    else:
        df_resultados_t = (
            df_resultados.set_index("EMPRESA")
            .T
            .reset_index()
            .rename(columns={"index": "CONCEPTO"})
        )
        df_resultados_t["TOTAL"] = df_resultados_t[
            [c for c in df_resultados_t.columns if c != "CONCEPTO"]
        ].sum(axis=1)

        for col in df_resultados_t.columns:
            if col != "CONCEPTO":
                df_resultados_t[col] = df_resultados_t[col].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_resultados_t, use_container_width=True, hide_index=True)
        utilidad_total = df_resultados["UTILIDAD"].sum()

    utilidad_por_empresa = {}
    utilidad_total = 0.0

    if not df_resultados.empty:
        utilidad_por_empresa = df_resultados.set_index("EMPRESA")["UTILIDAD"].to_dict()
        utilidad_total = float(df_resultados["UTILIDAD"].sum())

    df_final = reduce(
        lambda l, r: pd.merge(l, r, on=["CLASIFICACION", "CATEGORIA"], how="outer"),
        resultados_balance
    ).fillna(0)
    df_final["TOTAL ACUMULADO"] = df_final[EMPRESAS].sum(axis=1)
    for clasif in CLASIFICACIONES_PRINCIPALES:
        st.markdown(f"### 🔹 {clasif}")
        df_clasif = df_final[df_final["CLASIFICACION"] == clasif].copy()
        if df_clasif.empty:
            st.info(f"No hay cuentas clasificadas como {clasif}.")
            continue
        subtotal = pd.DataFrame({
            "CLASIFICACION": [clasif],
            "CATEGORIA": [f"TOTAL {clasif}"]
        })

        if clasif == "CAPITAL" and utilidad_por_empresa:
            # TOTAL CAPITAL = UTILIDAD (por empresa)
            for emp in EMPRESAS:
                subtotal[emp] = float(utilidad_por_empresa.get(emp, 0.0))
            subtotal["TOTAL ACUMULADO"] = float(utilidad_total)
        else:
            # resto igual: suma normal por clasificación
            for col in EMPRESAS + ["TOTAL ACUMULADO"]:
                subtotal[col] = df_clasif[col].sum()

        df_clasif = pd.concat([df_clasif, subtotal], ignore_index=True)

        for col in EMPRESAS + ["TOTAL ACUMULADO"]:
            df_clasif[col] = df_clasif[col].apply(lambda x: f"${x:,.2f}")
        with st.expander(f"{clasif}", expanded=(clasif == "CAPITAL")):
            st.dataframe(
                df_clasif.drop(columns=["CLASIFICACION"]),
                use_container_width=True,
                hide_index=True
            )

    totales = {
        c: df_final[df_final["CLASIFICACION"] == c]["TOTAL ACUMULADO"].sum()
        for c in CLASIFICACIONES_PRINCIPALES
    }

    if utilidad_por_empresa:
        totales["CAPITAL"] = float(utilidad_total) + totales["CAPITAL"]

    diferencia = totales["ACTIVO"] + (totales["PASIVO"] + totales["CAPITAL"])
    resumen_final = pd.DataFrame({
        "Concepto": ["TOTAL ACTIVO", "TOTAL PASIVO", "TOTAL CAPITAL", "DIFERENCIA"],
        "Monto Total": [
            f"${totales['ACTIVO']:,.2f}",
            f"${totales['PASIVO']:,.2f}",
            f"${totales['CAPITAL']:,.2f}",
            f"${diferencia:,.2f}",
        ]
    })

    st.markdown("### Resumen Consolidado")
    st.dataframe(resumen_final, use_container_width=True, hide_index=True)

    if abs(diferencia) < 1:
        st.success("✅ El balance está cuadrado (ACTIVO = PASIVO + CAPITAL).")
    else:
        st.error("❌ El balance no cuadra. Revisa cuentas/mapeo.")
    if cuentas_no_mapeadas:
        st.markdown("## ⚠️ Cuentas NO mapeadas detectadas (NO existen en el mapeo)")
        df_no_map = pd.concat(cuentas_no_mapeadas, ignore_index=True)

        df_no_map_res = (
            df_no_map.groupby("Cuenta", as_index=False)["Saldo"]
            .sum()
            .sort_values("Saldo", ascending=False)
        )
        st.markdown("### Consolidado (por Cuenta)")
        st.dataframe(df_no_map_res, use_container_width=True, hide_index=True)

        st.markdown("### Detalle (Cuenta x Empresa)")
        st.dataframe(
            df_no_map.sort_values(["EMPRESA", "Cuenta"]),
            use_container_width=True,
            hide_index=True
        )

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for empresa, df_emp in balances_detallados.items():
            df_emp.to_excel(writer, index=False, sheet_name=empresa[:31])
        df_final.to_excel(writer, index=False, sheet_name="Consolidado")
        resumen_final.to_excel(writer, index=False, sheet_name="Resumen")
        if not df_resultados.empty:
            df_resultados.to_excel(writer, index=False, sheet_name="Resultados")

    st.download_button(
        label="💾 Descargar Excel Consolidado",
        data=output.getvalue(),
        file_name="Balance_Consolidado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

def tabla_balance_general_acumulado():
    col1, col2 = st.columns([1, 1])

    OPCIONES_EMPRESA = ["ACUMULADO"] + EMPRESAS
    empresa_sel = col1.selectbox("Empresa", OPCIONES_EMPRESA, index=0)

    df_mapeo_local = cargar_mapeo(mapeo_url)
    if df_mapeo_local.empty:
        st.stop()

    if empresa_sel == "ACUMULADO":
        empresas_cargar = EMPRESAS[:] 
    else:
        empresas_cargar = [empresa_sel]
    data_empresas = cargar_balance_multi_hojas(balance_url, empresas_cargar)
    data_empresas_ly = cargar_balance_multi_hojas(balance_ly, empresas_cargar)
    if empresa_sel == "ACUMULADO":
        dfs_act = [data_empresas.get(e, pd.DataFrame()).copy() for e in empresas_cargar]
        dfs_ly  = [data_empresas_ly.get(e, pd.DataFrame()).copy() for e in empresas_cargar]
        df_emp = pd.concat([d for d in dfs_act if not d.empty], ignore_index=True) if any([not d.empty for d in dfs_act]) else pd.DataFrame()
        df_emp_ly = pd.concat([d for d in dfs_ly if not d.empty], ignore_index=True) if any([not d.empty for d in dfs_ly]) else pd.DataFrame()
    else:
        df_emp = data_empresas.get(empresa_sel, pd.DataFrame()).copy()
        df_emp_ly = data_empresas_ly.get(empresa_sel, pd.DataFrame()).copy()

    if df_emp.empty:
        st.warning(f"⚠️ No hay datos para {empresa_sel}.")
        st.stop()

    col_cuenta = _encontrar_columna(df_emp, COLUMNAS_CUENTA)
    col_monto = _encontrar_columna(df_emp, COLUMNAS_MONTO)
    col_cuenta_ly = _encontrar_columna(df_emp_ly, COLUMNAS_CUENTA)
    col_monto_ly = _encontrar_columna(df_emp_ly, COLUMNAS_MONTO)

    if not col_cuenta or not col_monto:
        st.error(f"❌ {empresa_sel}: columnas inválidas")
        st.stop()


    data_resultados = []
    for empresa in EMPRESAS:
        df_raw = data_empresas.get(empresa, pd.DataFrame()).copy()
        if df_raw.empty:
            continue

        col_cuenta_raw = _encontrar_columna(df_raw, NUMERO_CUENTA)
        col_monto_raw = _encontrar_columna(df_raw, COLUMNAS_MONTO)

        if not col_cuenta_raw or not col_monto_raw:
            st.warning(f"⚠️ {empresa}: no encontré columnas de Cuenta/Saldo para resultados.")
            continue
        df_raw[col_cuenta_raw] = df_raw[col_cuenta_raw].apply(limpiar_cuenta)
        df_raw[col_monto_raw] = _to_numeric_money(df_raw[col_monto_raw])

        df_raw = df_raw.dropna(subset=[col_cuenta_raw])
        df_cta = df_raw.groupby(col_cuenta_raw, as_index=False)[col_monto_raw].sum()

        ingreso = df_cta.loc[
            (df_cta[col_cuenta_raw] > 400000000) & (df_cta[col_cuenta_raw] < 500000000),
            col_monto_raw
        ].sum()

        gasto = df_cta.loc[
            (df_cta[col_cuenta_raw] > 500000000),
            col_monto_raw
        ].sum()

        utilidad = ingreso + gasto

        data_resultados.append({
            "EMPRESA": empresa,
            "INGRESO": float(ingreso),
            "GASTO": float(gasto),
            "UTILIDAD": float(utilidad),
        })

    df_resultados = pd.DataFrame(data_resultados)

    if empresa_sel == "ACUMULADO" and not df_resultados.empty:
        df_total = pd.DataFrame([{
            "EMPRESA": "TOTAL",
            "INGRESO": float(df_resultados["INGRESO"].sum()),
            "GASTO": float(df_resultados["GASTO"].sum()),
            "UTILIDAD": float(df_resultados["UTILIDAD"].sum()),
        }])
        df_resultados = pd.concat([df_resultados, df_total], ignore_index=True)

    st.markdown("### Estado de Resultados por Empresa")
    st.dataframe(df_resultados, use_container_width=True, hide_index=True)


    df_emp[col_cuenta] = df_emp[col_cuenta].apply(limpiar_cuenta)
    df_emp[col_monto] = _to_numeric_money(df_emp[col_monto])
    df_emp = df_emp.dropna(subset=[col_cuenta])
    df_emp = df_emp.groupby(col_cuenta, as_index=False)[col_monto].sum()

    df_emp_ly[col_cuenta_ly] = df_emp_ly[col_cuenta_ly].apply(limpiar_cuenta)
    df_emp_ly[col_monto_ly] = _to_numeric_money(df_emp_ly[col_monto_ly])
    df_emp_ly = df_emp_ly.dropna(subset=[col_cuenta_ly])
    df_emp_ly = df_emp_ly.groupby(col_cuenta_ly, as_index=False)[col_monto_ly].sum()

    df_merged = df_emp.merge(
        df_mapeo_local[["Cuenta", "CLASIFICACION", "CATEGORIA"]],
        left_on=col_cuenta,
        right_on="Cuenta",
        how="left",
    )

    df_merged_ly = df_emp_ly.merge(
        df_mapeo_local[["Cuenta", "CLASIFICACION", "CATEGORIA"]],
        left_on=col_cuenta_ly,
        right_on="Cuenta",
        how="left",
    )

    df_no_mapeadas = df_merged[df_merged["CLASIFICACION"].isna()].copy()
    df_ok = df_merged[~df_merged["CLASIFICACION"].isna()].copy()
    df_ok_ly = df_merged_ly[~df_merged_ly["CLASIFICACION"].isna()].copy()

    if df_ok.empty:
        st.warning(f"⚠️ {empresa_sel}: sin coincidencias con el mapeo.")
        st.stop()

    ORDEN = ("ACTIVO", "PASIVO", "CAPITAL")

    df_ok["CLASIFICACION"] = df_ok["CLASIFICACION"].astype(str).str.upper().str.strip()
    df_ok["CATEGORIA"] = df_ok["CATEGORIA"].astype(str).str.strip()
    df_ok[col_monto] = pd.to_numeric(df_ok[col_monto], errors="coerce").fillna(0.0)

    df_ok = df_ok[df_ok["CLASIFICACION"].isin(ORDEN)].copy()
    df_ok = df_ok[df_ok["CATEGORIA"].str.upper().ne("MAYOR")].copy()

    df_grp = (
        df_ok.groupby(["CLASIFICACION", "CATEGORIA"], as_index=False)[col_monto]
        .sum()
        .rename(columns={col_monto: "MONTO"})
    )
    df_merged_ly = df_emp_ly.merge(
        df_mapeo_local[["Cuenta", "CLASIFICACION", "CATEGORIA"]],
        left_on=col_cuenta_ly,
        right_on="Cuenta",
        how="left",
    )

    df_ok_ly = df_merged_ly[~df_merged_ly["CLASIFICACION"].isna()].copy()

    df_ok_ly["CLASIFICACION"] = df_ok_ly["CLASIFICACION"].astype(str).str.upper().str.strip()
    df_ok_ly["CATEGORIA"] = df_ok_ly["CATEGORIA"].astype(str).str.strip()
    df_ok_ly[col_monto_ly] = pd.to_numeric(df_ok_ly[col_monto_ly], errors="coerce").fillna(0.0)

    df_ok_ly = df_ok_ly[df_ok_ly["CLASIFICACION"].isin(ORDEN)].copy()
    df_ok_ly = df_ok_ly[df_ok_ly["CATEGORIA"].str.upper().ne("MAYOR")].copy()

    df_grp_ly = (
        df_ok_ly.groupby(["CLASIFICACION", "CATEGORIA"], as_index=False)[col_monto_ly]
        .sum()
        .rename(columns={col_monto_ly: "MONTO_LY"})
    )

    df_base = df_grp.merge(df_grp_ly, on=["CLASIFICACION", "CATEGORIA"], how="outer")
    df_base["MONTO"] = pd.to_numeric(df_base["MONTO"], errors="coerce").fillna(0.0)
    df_base["MONTO_LY"] = pd.to_numeric(df_base["MONTO_LY"], errors="coerce").fillna(0.0)
    df_base["% VARIACION"] = np.where(
        df_base["MONTO_LY"].abs() > 1e-9,
        (df_base["MONTO"] / df_base["MONTO_LY"]) - 1.0,
        np.nan
    )

    rows = []
    totales = {}
    totales_ly = {}

    for clasif in ORDEN:
        sub = df_base[df_base["CLASIFICACION"] == clasif].copy()

        total_act = float(sub["MONTO"].sum()) if not sub.empty else 0.0
        total_ly  = float(sub["MONTO_LY"].sum()) if not sub.empty else 0.0
        totales[clasif] = total_act
        totales_ly[clasif] = total_ly

        rows.append({
            "SECCION": clasif,
            "CUENTA": "",
            "MONTO": total_act,
            "MONTO_LY": total_ly,
            "% VARIACION": (total_act / total_ly - 1.0) if abs(total_ly) > 1e-9 else np.nan
        })
        if not sub.empty:
            sub = sub.sort_values("CATEGORIA")
            for _, r in sub.iterrows():
                rows.append({
                    "SECCION": "",
                    "CUENTA": str(r["CATEGORIA"]),
                    "MONTO": float(r["MONTO"]),
                    "MONTO_LY": float(r["MONTO_LY"]),
                    "% VARIACION": float(r["% VARIACION"]) if pd.notna(r["% VARIACION"]) else np.nan
                })

        rows.append({"SECCION": "", "CUENTA": "", "MONTO": None, "MONTO_LY": None, "% VARIACION": None})

    if df_resultados.empty:
        utilidad_sel = 0.0
    else:
        if empresa_sel == "ACUMULADO":
            utilidad_sel = float(df_resultados.loc[df_resultados["EMPRESA"] != "TOTAL", "UTILIDAD"].sum())
        else:
            s = df_resultados.loc[df_resultados["EMPRESA"] == empresa_sel, "UTILIDAD"]
            utilidad_sel = float(s.iloc[0]) if not s.empty else 0.0
  
    totales["CAPITAL"] = float(totales.get("CAPITAL", 0.0)) + utilidad_sel
    totales_ly["CAPITAL"] = float(totales_ly.get("CAPITAL", 0.0)) + utilidad_sel

    dif = float(totales.get("ACTIVO", 0.0) + (totales.get("PASIVO", 0.0) + totales.get("CAPITAL", 0.0)))
    dif_ly = float(totales_ly.get("ACTIVO", 0.0) + (totales_ly.get("PASIVO", 0.0) + totales_ly.get("CAPITAL", 0.0)))

    rows.append({
        "SECCION": "RESUMEN",
        "CUENTA": "DIFERENCIA",
        "MONTO": dif,
        "MONTO_LY": dif_ly,
        "% VARIACION": (dif / dif_ly - 1.0) if abs(dif_ly) > 1e-9 else np.nan
    })

    df_out_raw = pd.DataFrame(rows)
    def fmt_money(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        return f"${float(x):,.2f}"

    def fmt_pct(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        return f"{x*100:,.1f}%"

    df_out_show = df_out_raw.copy()
    df_out_show["MONTO"] = df_out_show["MONTO"].apply(fmt_money)
    df_out_show["MONTO_LY"] = df_out_show["MONTO_LY"].apply(fmt_money)
    df_out_show["% VARIACION"] = df_out_show["% VARIACION"].apply(fmt_pct)

    def estilo_reporte(row):
        t = row.get("")
        if t == "header":
            return ["font-weight:700; border-top:2px solid #999; border-bottom:1px solid #999;"] * len(row)
        if t == "blank":
            return ["background-color:#fff;"] * len(row)
        return [""] * len(row)

    st.markdown(f"### {empresa_sel}")
    st.dataframe(
        df_out_show[["SECCION", "CUENTA", "MONTO", "MONTO_LY", "% VARIACION"]]
            .style
            .apply(estilo_reporte, axis=1)
            .hide(axis="columns"),
        use_container_width=True,
        hide_index=True
    )

    if abs(dif) < 1:
        st.success("✅ El balance está cuadrado")
    else:
        st.error("❌ El balance no cuadra. Revisa mapeo/cuentas.")

    if not df_no_mapeadas.empty:
        st.markdown("## ⚠️ Cuentas NO mapeadas")
        cols_show = [col_cuenta, col_monto]
        cols_show = [c for c in cols_show if c in df_no_mapeadas.columns]
        df_nm = df_no_mapeadas[cols_show].copy().rename(columns={col_cuenta: "Cuenta", col_monto: "Saldo"})
        st.dataframe(df_nm, use_container_width=True, hide_index=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_ok.to_excel(writer, index=False, sheet_name=f"{empresa_sel[:25]}_detalle")
        df_grp.to_excel(writer, index=False, sheet_name=f"{empresa_sel[:25]}_agrupado")
        if not df_no_mapeadas.empty:
            df_no_mapeadas.to_excel(writer, index=False, sheet_name="No_mapeadas")
    st.markdown(f"### {empresa_sel}")

    nombre_archivo = "Balance_Acumulado_TODAS.xlsx" if empresa_sel == "ACUMULADO" else f"Balance_Acumulado_{empresa_sel}.xlsx"

    st.download_button(
        label=f"💾 Descargar Excel ({empresa_sel})",
        data=output.getvalue(),
        file_name=f"Balance_Acumulado_{empresa_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

def tabla_estado_resultados():
    st.subheader("Estado de Resultados")

    col1, col2 = st.columns([1, 1])
    empresa_sel = col1.selectbox("Empresa", EMPRESAS, index=0)

    df_mapeo_local = cargar_mapeo(mapeo_url)
    if df_mapeo_local.empty:
        st.stop()

    req = {"Cuenta", "CLASIFICACION_A", "CATEGORIA_A"}
    if not req.issubset(df_mapeo_local.columns):
        st.error(f"❌ Al mapeo le faltan columnas: {req - set(df_mapeo_local.columns)}")
        st.stop()

    df_map = df_mapeo_local.copy()

    df_map["CLASIFICACION_A"] = (
        df_map["CLASIFICACION_A"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    df_map["CATEGORIA_A"] = (
        df_map["CATEGORIA_A"]
        .astype("string")
        .str.strip()
    )

    df_map = df_map.dropna(subset=["CLASIFICACION_A", "CATEGORIA_A"])
    df_map = df_map[(df_map["CLASIFICACION_A"] != "") & (df_map["CATEGORIA_A"] != "")]

    data_2025 = cargar_balance_multi_hojas(balance_url, [empresa_sel])
    data_2024 = cargar_balance_multi_hojas(balance_ly,  [empresa_sel])

    df_25_raw = data_2025.get(empresa_sel, pd.DataFrame()).copy()
    df_24_raw = data_2024.get(empresa_sel, pd.DataFrame()).copy()

    if df_25_raw.empty:
        st.warning(f"⚠️ No hay datos 2025 para {empresa_sel}.")
        st.stop()
    if df_24_raw.empty:
        st.warning(f"⚠️ No hay datos 2024 para {empresa_sel}.")
        st.stop()

    col_cta_25 = _encontrar_columna(df_25_raw, NUMERO_CUENTA) or _encontrar_columna(df_25_raw, COLUMNAS_CUENTA)
    col_amt_25 = _encontrar_columna(df_25_raw, COLUMNAS_MONTO)

    col_cta_24 = _encontrar_columna(df_24_raw, NUMERO_CUENTA) or _encontrar_columna(df_24_raw, COLUMNAS_CUENTA)
    col_amt_24 = _encontrar_columna(df_24_raw, COLUMNAS_MONTO)

    if not col_cta_25 or not col_amt_25:
        st.error("❌ 2025: columnas inválidas (Cuenta/Saldo).")
        st.stop()
    if not col_cta_24 or not col_amt_24:
        st.error("❌ 2024: columnas inválidas (Cuenta/Saldo).")
        st.stop()

    def prep(df_raw, col_cta, col_amt, nombre_monto):
        df = df_raw.copy()
        df[col_cta] = df[col_cta].apply(limpiar_cuenta)
        df[col_amt] = _to_numeric_money(df[col_amt])
        df = df.dropna(subset=[col_cta])
        df = df.groupby(col_cta, as_index=False)[col_amt].sum()
        df = df.rename(columns={col_cta: "Cuenta", col_amt: nombre_monto})
        return df

    df_25 = prep(df_25_raw, col_cta_25, col_amt_25, "2025")
    df_24 = prep(df_24_raw, col_cta_24, col_amt_24, "2024")

    df_cta = df_25.merge(df_24, on="Cuenta", how="outer").fillna(0.0)
    df_pl = df_cta.merge(
        df_map[["Cuenta", "CLASIFICACION_A", "CATEGORIA_A"]],
        on="Cuenta",
        how="inner"
    )

    if df_pl.empty:
        st.warning("⚠️ No hay cuentas mapeadas a CLASIFICACION_A para esta empresa.")
        st.stop()
    # ✅ INGRESO en positivo (si viene negativo)
    mask_ing = df_pl["CLASIFICACION_A"].astype(str).str.upper().str.strip().eq("INGRESO")
    df_pl.loc[mask_ing, ["2025", "2024"]] = df_pl.loc[mask_ing, ["2025", "2024"]] * -1

    df_tot = df_pl.groupby("CLASIFICACION_A", as_index=False)[["2025", "2024"]].sum()


    def tot(*nombres):
        """Suma total por una o varias CLASIFICACION_A (case-insensitive)."""
        if len(nombres) == 1 and isinstance(nombres[0], (list, tuple, set)):
            nombres = tuple(nombres[0])
        claves = [str(x).upper().strip() for x in nombres]
        sub = df_tot[df_tot["CLASIFICACION_A"].isin(claves)]
        return float(sub["2025"].sum()), float(sub["2024"].sum())

    def pct(a, b):
        return (a / b - 1.0) if abs(b) > 1e-9 else None

    ing_25, ing_24 = tot("INGRESO")
    ing_25, ing_24 = -ing_25, -ing_24 
    coss_25, coss_24 = tot("COSS")
    gadm_25, gadm_24 = tot("G.ADMN") 
    coss_25, coss_24 = tot("COSS")
    gadm_25, gadm_24 = tot("G.ADMN")
    otros_ing_25, otros_ing_24 = tot("OTROS INGRESOS", "OTROS INGRESO", "OTROS INGRESOS/EGRESOS")

    gasto_fin_25, gasto_fin_24 = tot("GASTO FIN", "GASTO FINANCIERO")
    ingreso_fin_25, ingreso_fin_24 = tot("INGRESO FIN", "INGRESO FINANCIERO")

    imp_25, imp_24 = tot("IMPUESTOS")
    dep_25, dep_24 = tot("DEPRECIACION")
    amo_25, amo_24 = tot("AMORTIZACION")
    ub_25 = ing_25 - coss_25
    ub_24 = ing_24 - coss_24

    uo_25 = ub_25 - gadm_25
    uo_24 = ub_24 - gadm_24

    ebit_25 = uo_25 + otros_ing_25
    ebit_24 = uo_24 + otros_ing_24
    ebt_25 = ebit_25 - gasto_fin_25 + ingreso_fin_25
    ebt_24 = ebit_24 - gasto_fin_24 + ingreso_fin_24

    udi_25 = ebt_25 - imp_25
    udi_24 = ebt_24 - imp_24

    ebitda_25 = ebit_25 + dep_25 + amo_25
    ebitda_24 = ebit_24 + dep_24 + amo_24

    panel = [
        ("INGRESO", ing_25, ing_24, "money"),
        ("COSS", coss_25, coss_24, "money"),
        ("UTILIDAD BRUTA", ub_25, ub_24, "money_bold"),
        ("% UB", (ub_25/ing_25 if abs(ing_25)>1e-9 else None), (ub_24/ing_24 if abs(ing_24)>1e-9 else None), "pct"),
        ("G.ADMN", gadm_25, gadm_24, "money"),
        ("UTILIDAD OPERATIVA", uo_25, uo_24, "money_bold"),
        ("%UO", (uo_25/ing_25 if abs(ing_25)>1e-9 else None), (uo_24/ing_24 if abs(ing_24)>1e-9 else None), "pct"),
        ("OTROS INGRESOS", otros_ing_25, otros_ing_24, "money"),
        ("EBIT", ebit_25, ebit_24, "money_bold"),
        ("% EBIT", (ebit_25/ing_25 if abs(ing_25)>1e-9 else None), (ebit_24/ing_24 if abs(ing_24)>1e-9 else None), "pct"),
        ("GASTO FIN", gasto_fin_25, gasto_fin_24, "money"),
        ("INGRESO FIN", ingreso_fin_25, ingreso_fin_24, "money"),
        ("EBT", ebt_25, ebt_24, "money_bold"),
        ("% EBT", (ebt_25/ing_25 if abs(ing_25)>1e-9 else None), (ebt_24/ing_24 if abs(ing_24)>1e-9 else None), "pct"),
        ("IMPUESTOS", imp_25, imp_24, "money"),
        ("Utilidad D.Imp.", udi_25, udi_24, "money_bold"),
        ("%UDI", (udi_25/ing_25 if abs(ing_25)>1e-9 else None), (udi_24/ing_24 if abs(ing_24)>1e-9 else None), "pct"),
        ("EBITDA", ebitda_25, ebitda_24, "money_bold"),
    ]

    df_panel = pd.DataFrame(panel, columns=["CONCEPTO", "2025", "2024", "_fmt"])
    df_panel["% CAMBIO"] = df_panel.apply(lambda r: pct(r["2025"], r["2024"]) if r["_fmt"] != "pct" else None, axis=1)

    def fmt_money(v):
        if v is None or (isinstance(v, float) and pd.isna(v)): return ""
        return f"$ {float(v):,.0f}"

    def fmt_pct(v):
        if v is None or (isinstance(v, float) and pd.isna(v)): return ""
        return f"{float(v)*100:,.2f}%"

    df_show = df_panel.copy()
    is_pct = df_show["_fmt"].eq("pct")

    df_show.loc[~is_pct, "2025"] = df_show.loc[~is_pct, "2025"].apply(fmt_money)
    df_show.loc[~is_pct, "2024"] = df_show.loc[~is_pct, "2024"].apply(fmt_money)
    df_show.loc[~is_pct, "% CAMBIO"] = df_show.loc[~is_pct, "% CAMBIO"].apply(lambda x: "" if x is None else f"{x*100:,.0f}%")
    df_show.loc[is_pct, "2025"] = df_show.loc[is_pct, "2025"].apply(fmt_pct)
    df_show.loc[is_pct, "2024"] = df_show.loc[is_pct, "2024"].apply(fmt_pct)
    df_show.loc[is_pct, "% CAMBIO"] = ""

    def style_panel(row):
        concepto = str(row.get("CONCEPTO", "")).upper().strip()
        if concepto in ["UTILIDAD BRUTA", "UTILIDAD OPERATIVA", "EBIT", "EBT", "UTILIDAD DESPUÉS DE IMP.", "EBITDA"]:
            return ["font-weight:800; background:#f2f2f2;"] * len(row)
        if concepto in ["INGRESO", "COSS", "G.ADMN", "OTROS INGRESOS", "GASTO FIN", "INGRESO FIN", "IMPUESTOS"]:
            return ["font-weight:700;"] * len(row)
        return [""] * len(row)

    st.markdown(f"### {empresa_sel}  \n**Miles MXN**")
    st.dataframe(
        df_show[["CONCEPTO", "2025", "2024", "% CAMBIO"]]
          .style.apply(style_panel, axis=1),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.markdown("### Detalle por Categoría")

    df_cat = (
        df_pl.groupby(["CLASIFICACION_A", "CATEGORIA_A"], as_index=False)[["2025", "2024"]]
        .sum()
    )

    def _pct(a, b):
        return (a / b - 1.0) if abs(b) > 1e-9 else np.nan

    def _fmt_money(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        v = float(v)
        if v < 0:
            return f"-$ {abs(v):,.0f}"
        return f"$ {v:,.0f}"

    def _fmt_pct(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        return f"{float(v)*100:,.0f}%"

    SECCIONES_DETALLE = ["INGRESO", "COSS", "G.ADMN", "OTROS INGRESOS", "GASTO FIN", "INGRESO FIN", "IMPUESTOS"]
    rows = []

    def add_header(nombre, v25, v24, is_pct=False):
        rows.append({
            "SECCION": nombre,
            "CATEGORIA": "",
            "2025": v25,
            "CATEGORIA2": "",
            "2024": v24,
            "% CAMBIO": (None if is_pct else _pct(v25, v24)),
            "_t": "header",
            "_is_pct": bool(is_pct)
        })

    def add_detail(cat, v25, v24):
        rows.append({
            "SECCION": "",
            "CATEGORIA": str(cat),
            "2025": v25,
            "CATEGORIA2": str(cat),
            "2024": v24,
            "% CAMBIO": _pct(v25, v24),
            "_t": "detail",
            "_is_pct": False
        })

    add_header("INGRESO", ing_25, ing_24)
    sub = df_cat[df_cat["CLASIFICACION_A"].astype(str).str.upper().str.strip().eq("INGRESO")].copy()
    if not sub.empty:
        sub = sub.sort_values("CATEGORIA_A")
        for _, r in sub.iterrows():
            add_detail(r["CATEGORIA_A"], float(r["2025"]), float(r["2024"]))

    add_header("COSS", coss_25, coss_24)
    sub = df_cat[df_cat["CLASIFICACION_A"].astype(str).str.upper().str.strip().eq("COSS")].copy()
    if not sub.empty:
        sub = sub.sort_values("CATEGORIA_A")
        for _, r in sub.iterrows():
            add_detail(r["CATEGORIA_A"], float(r["2025"]), float(r["2024"]))

    add_header("UTILIDAD BRUTA", ub_25, ub_24)
    add_header("% UB",
            (ub_25 / ing_25) if abs(ing_25) > 1e-9 else np.nan,
            (ub_24 / ing_24) if abs(ing_24) > 1e-9 else np.nan,
            is_pct=True)


    add_header("G.ADMN", gadm_25, gadm_24)
    sub = df_cat[df_cat["CLASIFICACION_A"].astype(str).str.upper().str.strip().eq("G.ADMN")].copy()
    if not sub.empty:
        sub = sub.sort_values("CATEGORIA_A")
        for _, r in sub.iterrows():
            add_detail(r["CATEGORIA_A"], float(r["2025"]), float(r["2024"]))

    add_header("UTILIDAD OPERATIVA", uo_25, uo_24)
    add_header("%UO",
            (uo_25 / ing_25) if abs(ing_25) > 1e-9 else np.nan,
            (uo_24 / ing_24) if abs(ing_24) > 1e-9 else np.nan,
            is_pct=True)

    add_header("OTROS INGRESOS", otros_ing_25, otros_ing_24)
    sub = df_cat[df_cat["CLASIFICACION_A"].astype(str).str.upper().str.strip().isin(
        ["OTROS INGRESOS", "OTROS INGRESO", "OTROS INGRESOS/EGRESOS"]
    )].copy()
    if not sub.empty:
        sub = sub.sort_values("CATEGORIA_A")
        for _, r in sub.iterrows():
            add_detail(r["CATEGORIA_A"], float(r["2025"]), float(r["2024"]))

    add_header("EBIT", ebit_25, ebit_24)
    add_header("% EBIT",
            (ebit_25 / ing_25) if abs(ing_25) > 1e-9 else np.nan,
            (ebit_24 / ing_24) if abs(ing_24) > 1e-9 else np.nan,
            is_pct=True)

    add_header("GASTO FIN", gasto_fin_25, gasto_fin_24)
    sub = df_cat[df_cat["CLASIFICACION_A"].astype(str).str.upper().str.strip().isin(
        ["GASTO FIN", "GASTO FINANCIERO"]
    )].copy()
    if not sub.empty:
        sub = sub.sort_values("CATEGORIA_A")
        for _, r in sub.iterrows():
            add_detail(r["CATEGORIA_A"], float(r["2025"]), float(r["2024"]))

    add_header("INGRESO FIN", ingreso_fin_25, ingreso_fin_24)
    sub = df_cat[df_cat["CLASIFICACION_A"].astype(str).str.upper().str.strip().isin(
        ["INGRESO FIN", "INGRESO FINANCIERO"]
    )].copy()
    if not sub.empty:
        sub = sub.sort_values("CATEGORIA_A")
        for _, r in sub.iterrows():
            add_detail(r["CATEGORIA_A"], float(r["2025"]), float(r["2024"]))

    add_header("EBT", ebt_25, ebt_24)
    add_header("% EBT",
            (ebt_25 / ing_25) if abs(ing_25) > 1e-9 else np.nan,
            (ebt_24 / ing_24) if abs(ing_24) > 1e-9 else np.nan,
            is_pct=True)

    add_header("IMPUESTOS", imp_25, imp_24)
    sub = df_cat[df_cat["CLASIFICACION_A"].astype(str).str.upper().str.strip().eq("IMPUESTOS")].copy()
    if not sub.empty:
        sub = sub.sort_values("CATEGORIA_A")
        for _, r in sub.iterrows():
            add_detail(r["CATEGORIA_A"], float(r["2025"]), float(r["2024"]))

    add_header("Utilidad después de imp.", udi_25, udi_24)
    add_header("%UDI",
            (udi_25 / ing_25) if abs(ing_25) > 1e-9 else np.nan,
            (udi_24 / ing_24) if abs(ing_24) > 1e-9 else np.nan,
            is_pct=True)


    add_header("EBITDA", ebitda_25, ebitda_24)
    df_det = pd.DataFrame(rows)
    df_show2 = df_det.copy()
    mask_pct = df_show2["_is_pct"].fillna(False)
    df_show2.loc[~mask_pct, "2025"] = df_show2.loc[~mask_pct, "2025"].apply(_fmt_money)
    df_show2.loc[~mask_pct, "2024"] = df_show2.loc[~mask_pct, "2024"].apply(_fmt_money)
    df_show2.loc[~mask_pct, "% CAMBIO"] = df_show2.loc[~mask_pct, "% CAMBIO"].apply(_fmt_pct)

    df_show2.loc[mask_pct, "2025"] = df_show2.loc[mask_pct, "2025"].apply(_fmt_pct)
    df_show2.loc[mask_pct, "2024"] = df_show2.loc[mask_pct, "2024"].apply(_fmt_pct)
    df_show2.loc[mask_pct, "% CAMBIO"] = ""

    def _style_detalle(row):
        if row.get("_t", "") == "header":
            return ["font-weight:800; background:#f2f2f2;"] * len(row)
        return [""] * len(row)
    df_show2 = df_show2.rename(columns={"SECCION": str(empresa_sel)})
    st.dataframe(
        df_show2[[str(empresa_sel), "CATEGORIA", "2025", "CATEGORIA2", "2024", "% CAMBIO"]]
            .style.apply(_style_detalle, axis=1),
        use_container_width=True,
        hide_index=True
    )



def tabla_escenarios_edr():
    st.subheader("Escenarios Estado de Resultados")

    col1, col2 = st.columns([1, 1])
    empresa_sel = col1.selectbox("Empresa", EMPRESAS, index=0)

    df_mapeo_local = cargar_mapeo(mapeo_url)
    if df_mapeo_local.empty:
        st.stop()

    req = {"Cuenta", "CLASIFICACION_A", "CATEGORIA_A"}
    if not req.issubset(df_mapeo_local.columns):
        st.error(f"❌ Al mapeo le faltan columnas: {req - set(df_mapeo_local.columns)}")
        st.stop()

    df_map = df_mapeo_local.copy()

    df_map["CLASIFICACION_A"] = (
        df_map["CLASIFICACION_A"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    df_map["CATEGORIA_A"] = (
        df_map["CATEGORIA_A"]
        .astype("string")
        .str.strip()
    )


    df_map = df_map.dropna(subset=["CLASIFICACION_A", "CATEGORIA_A"])
    df_map = df_map[(df_map["CLASIFICACION_A"] != "") & (df_map["CATEGORIA_A"] != "")]


    data_2025 = cargar_balance_multi_hojas(balance_url, [empresa_sel])
    data_2024 = cargar_balance_multi_hojas(balance_ly,  [empresa_sel])

    df_25_raw = data_2025.get(empresa_sel, pd.DataFrame()).copy()
    df_24_raw = data_2024.get(empresa_sel, pd.DataFrame()).copy()

    if df_25_raw.empty:
        st.warning(f"⚠️ No hay datos 2025 para {empresa_sel}.")
        st.stop()
    if df_24_raw.empty:
        st.warning(f"⚠️ No hay datos 2024 para {empresa_sel}.")
        st.stop()

    col_cta_25 = _encontrar_columna(df_25_raw, NUMERO_CUENTA) or _encontrar_columna(df_25_raw, COLUMNAS_CUENTA)
    col_amt_25 = _encontrar_columna(df_25_raw, COLUMNAS_MONTO)
    col_cta_24 = _encontrar_columna(df_24_raw, NUMERO_CUENTA) or _encontrar_columna(df_24_raw, COLUMNAS_CUENTA)
    col_amt_24 = _encontrar_columna(df_24_raw, COLUMNAS_MONTO)

    if not col_cta_25 or not col_amt_25:
        st.error("❌ 2025: columnas inválidas (Cuenta/Saldo).")
        st.stop()
    if not col_cta_24 or not col_amt_24:
        st.error("❌ 2024: columnas inválidas (Cuenta/Saldo).")
        st.stop()

    def prep(df_raw, col_cta, col_amt, nombre_monto):
        df = df_raw.copy()
        df[col_cta] = df[col_cta].apply(limpiar_cuenta)
        df[col_amt] = _to_numeric_money(df[col_amt])
        df = df.dropna(subset=[col_cta])
        df = df.groupby(col_cta, as_index=False)[col_amt].sum()
        df = df.rename(columns={col_cta: "Cuenta", col_amt: nombre_monto})
        return df

    df_25 = prep(df_25_raw, col_cta_25, col_amt_25, "2025")
    df_24 = prep(df_24_raw, col_cta_24, col_amt_24, "2024")
    df_cta = df_25.merge(df_24, on="Cuenta", how="outer").fillna(0.0)

    df_pl = df_cta.merge(
        df_map[["Cuenta", "CLASIFICACION_A", "CATEGORIA_A"]],
        on="Cuenta",
        how="inner"
    )

    if df_pl.empty:
        st.warning("⚠️ No hay cuentas mapeadas a CLASIFICACION_A para esta empresa.")
        st.stop()

    df_tot_base = df_pl.groupby("CLASIFICACION_A", as_index=False)[["2025", "2024"]].sum()

    def tot_base(*nombres):
        if len(nombres) == 1 and isinstance(nombres[0], (list, tuple, set)):
            nombres = tuple(nombres[0])
        claves = [str(x).upper().strip() for x in nombres]
        sub = df_tot_base[df_tot_base["CLASIFICACION_A"].isin(claves)]
        return float(sub["2025"].sum()), float(sub["2024"].sum())

    ing_25_base, ing_24_base = tot_base("INGRESO")
    coss_25_base, coss_24_base = tot_base("COSS")
    gadm_25_base, gadm_24_base = tot_base("G.ADMN")

    st.markdown("### Ajustes de Escenario ")

    a1, a2, a3 = st.columns(3)
    modo = a1.selectbox("Modo de ajuste", ["% sobre el total", "Monto (MXN)"], index=0, key=f"modo_edr_{empresa_sel}")

    if modo == "% sobre el total":
        adj_coss_25 = a2.slider("% COSS 2025", -50.0, 50.0, 0.0, 0.5, key=f"coss_pct_25_{empresa_sel}") / 100.0
        adj_coss_24 = a3.slider("% COSS 2024", -50.0, 50.0, 0.0, 0.5, key=f"coss_pct_24_{empresa_sel}") / 100.0

        b1, b2 = st.columns(2)
        adj_gadm_25 = b1.slider("% G.ADMN 2025", -50.0, 50.0, 0.0, 0.5, key=f"gadm_pct_25_{empresa_sel}") / 100.0
        adj_gadm_24 = b2.slider("% G.ADMN 2024", -50.0, 50.0, 0.0, 0.5, key=f"gadm_pct_24_{empresa_sel}") / 100.0

        coss_25_scn = coss_25_base * (1.0 + adj_coss_25)
        coss_24_scn = coss_24_base * (1.0 + adj_coss_24)

        gadm_25_scn = gadm_25_base * (1.0 + adj_gadm_25)
        gadm_24_scn = gadm_24_base * (1.0 + adj_gadm_24)
    else:
        adj_coss_m_25 = a2.number_input("Δ COSS 2025 (MXN)", value=0.0, step=1000.0, key=f"coss_m_25_{empresa_sel}")
        adj_coss_m_24 = a3.number_input("Δ COSS 2024 (MXN)", value=0.0, step=1000.0, key=f"coss_m_24_{empresa_sel}")

        b1, b2 = st.columns(2)
        adj_gadm_m_25 = b1.number_input("Δ G.ADMN 2025 (MXN)", value=0.0, step=1000.0, key=f"gadm_m_25_{empresa_sel}")
        adj_gadm_m_24 = b2.number_input("Δ G.ADMN 2024 (MXN)", value=0.0, step=1000.0, key=f"gadm_m_24_{empresa_sel}")

        coss_25_scn = coss_25_base + adj_coss_m_25
        coss_24_scn = coss_24_base + adj_coss_m_24

        gadm_25_scn = gadm_25_base + adj_gadm_m_25
        gadm_24_scn = gadm_24_base + adj_gadm_m_24

    factor_coss_25 = (coss_25_scn / coss_25_base) if abs(coss_25_base) > 1e-9 else 1.0
    factor_coss_24 = (coss_24_scn / coss_24_base) if abs(coss_24_base) > 1e-9 else 1.0

    factor_gadm_25 = (gadm_25_scn / gadm_25_base) if abs(gadm_25_base) > 1e-9 else 1.0
    factor_gadm_24 = (gadm_24_scn / gadm_24_base) if abs(gadm_24_base) > 1e-9 else 1.0
    df_pl["CLASIFICACION_A"] = df_pl["CLASIFICACION_A"].astype(str).str.upper().str.strip()

    mask_coss = df_pl["CLASIFICACION_A"].eq("COSS")
    mask_gadm = df_pl["CLASIFICACION_A"].eq("G.ADMN")

    df_pl.loc[mask_coss, "2025"] = df_pl.loc[mask_coss, "2025"] * factor_coss_25
    df_pl.loc[mask_coss, "2024"] = df_pl.loc[mask_coss, "2024"] * factor_coss_24
    df_pl.loc[mask_gadm, "2025"] = df_pl.loc[mask_gadm, "2025"] * factor_gadm_25
    df_pl.loc[mask_gadm, "2024"] = df_pl.loc[mask_gadm, "2024"] * factor_gadm_24
    df_tot = df_pl.groupby("CLASIFICACION_A", as_index=False)[["2025", "2024"]].sum()

    def tot(*nombres):
        if len(nombres) == 1 and isinstance(nombres[0], (list, tuple, set)):
            nombres = tuple(nombres[0])
        claves = [str(x).upper().strip() for x in nombres]
        sub = df_tot[df_tot["CLASIFICACION_A"].isin(claves)]
        return float(sub["2025"].sum()), float(sub["2024"].sum())

    def pct(a, b):
        return (a / b - 1.0) if abs(b) > 1e-9 else None

    ing_25, ing_24 = tot("INGRESO")
    ing_25 *=-1
    ing_24 *=-1
    coss_25, coss_24 = tot("COSS")
    gadm_25, gadm_24 = tot("G.ADMN")

    otros_ing_25, otros_ing_24 = tot("OTROS INGRESOS", "OTROS INGRESO")
    gasto_fin_25, gasto_fin_24 = tot("GASTO FIN", "GASTO FINANCIERO")
    ingreso_fin_25, ingreso_fin_24 = tot("INGRESO FIN", "INGRESO FINANCIERO")
    ingreso_fin_24 *=-1
    ingreso_fin_25 *=-1
    imp_25, imp_24 = tot("IMPUESTOS")
    dep_25, dep_24 = tot("DEPRECIACION")
    amo_25, amo_24 = tot("AMORTIZACION")

    ub_25 = ing_25 - coss_25
    ub_24 = ing_24 - coss_24

    uo_25 = ub_25 - gadm_25
    uo_24 = ub_24 - gadm_24

    ebit_25 = uo_25 + otros_ing_25
    ebit_24 = uo_24 + otros_ing_24

    ebt_25 = ebit_25 - gasto_fin_25 + ingreso_fin_25
    ebt_24 = ebit_24 - gasto_fin_24 + ingreso_fin_24

    udi_25 = ebt_25 - imp_25
    udi_24 = ebt_24 - imp_24

    ebitda_25 = ebit_25 + dep_25 + amo_25
    ebitda_24 = ebit_24 + dep_24 + amo_24

    panel = [
        ("INGRESO", ing_25, ing_24, "money"),
        ("COSS", coss_25, coss_24, "money"),
        ("UTILIDAD BRUTA", ub_25, ub_24, "money_bold"),
        ("% UB", (ub_25/ing_25 if abs(ing_25)>1e-9 else None), (ub_24/ing_24 if abs(ing_24)>1e-9 else None), "pct"),
        ("G.ADMN", gadm_25, gadm_24, "money"),
        ("UTILIDAD OPERATIVA", uo_25, uo_24, "money_bold"),
        ("%UO", (uo_25/ing_25 if abs(ing_25)>1e-9 else None), (uo_24/ing_24 if abs(ing_24)>1e-9 else None), "pct"),
        ("OTROS INGRESOS", otros_ing_25, otros_ing_24, "money"),
        ("EBIT", ebit_25, ebit_24, "money_bold"),
        ("% EBIT", (ebit_25/ing_25 if abs(ing_25)>1e-9 else None), (ebit_24/ing_24 if abs(ing_24)>1e-9 else None), "pct"),
        ("GASTO FIN", gasto_fin_25, gasto_fin_24, "money"),
        ("INGRESO FIN", ingreso_fin_25, ingreso_fin_24, "money"),
        ("EBT", ebt_25, ebt_24, "money_bold"),
        ("% EBT", (ebt_25/ing_25 if abs(ing_25)>1e-9 else None), (ebt_24/ing_24 if abs(ing_24)>1e-9 else None), "pct"),
        ("IMPUESTOS", imp_25, imp_24, "money"),
        ("Utilidad D.Imp.", udi_25, udi_24, "money_bold"),
        ("%UDI", (udi_25/ing_25 if abs(ing_25)>1e-9 else None), (udi_24/ing_24 if abs(ing_24)>1e-9 else None), "pct"),
        ("EBITDA", ebitda_25, ebitda_24, "money_bold"),
    ]

    df_panel = pd.DataFrame(panel, columns=["CONCEPTO", "2025", "2024", "_fmt"])
    df_panel["% CAMBIO"] = df_panel.apply(lambda r: pct(r["2025"], r["2024"]) if r["_fmt"] != "pct" else None, axis=1)

    def fmt_money(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        return f"$ {float(v):,.0f}"

    def fmt_pct(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        return f"{float(v)*100:,.2f}%"

    df_show = df_panel.copy()
    is_pct = df_show["_fmt"].eq("pct")

    df_show.loc[~is_pct, "2025"] = df_show.loc[~is_pct, "2025"].apply(fmt_money)
    df_show.loc[~is_pct, "2024"] = df_show.loc[~is_pct, "2024"].apply(fmt_money)
    df_show.loc[~is_pct, "% CAMBIO"] = df_show.loc[~is_pct, "% CAMBIO"].apply(lambda x: "" if x is None else f"{x*100:,.0f}%")

    df_show.loc[is_pct, "2025"] = df_show.loc[is_pct, "2025"].apply(fmt_pct)
    df_show.loc[is_pct, "2024"] = df_show.loc[is_pct, "2024"].apply(fmt_pct)
    df_show.loc[is_pct, "% CAMBIO"] = ""

    def style_panel(row):
        concepto = str(row.get("CONCEPTO", "")).upper().strip()
        if concepto in ["UTILIDAD BRUTA", "UTILIDAD OPERATIVA", "EBIT", "EBT", "UTILIDAD D.IMP.", "EBITDA"]:
            return ["font-weight:800; background:#f2f2f2;"] * len(row)
        if concepto in ["INGRESO", "COSS", "G.ADMN", "OTROS INGRESOS", "GASTO FIN", "INGRESO FIN", "IMPUESTOS"]:
            return ["font-weight:700;"] * len(row)
        return [""] * len(row)

    st.markdown(f"### {empresa_sel}  \n**Miles MXN**")
    st.dataframe(
        df_show[["CONCEPTO", "2025", "2024", "% CAMBIO"]].style.apply(style_panel, axis=1),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.markdown("### Detalle por Categoría")
    mask_ing = df_pl["CLASIFICACION_A"].astype(str).str.upper().str.strip().eq("INGRESO")
    df_pl.loc[mask_ing, ["2025","2024"]] = df_pl.loc[mask_ing, ["2025","2024"]] * -1
    mask_ingfin = df_pl["CLASIFICACION_A"].astype(str).str.upper().str.strip().isin(["INGRESO FIN","INGRESO FINANCIERO"])
    df_pl.loc[mask_ingfin, ["2025","2024"]] = df_pl.loc[mask_ingfin, ["2025","2024"]] * -1

    df_cat = (
        df_pl.groupby(["CLASIFICACION_A", "CATEGORIA_A"], as_index=False)[["2025", "2024"]]
        .sum()
    )

    def _pct(a, b):
        return (a / b - 1.0) if abs(b) > 1e-9 else np.nan

    def _fmt_money(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        v = float(v)
        if v < 0:
            return f"-$ {abs(v):,.0f}"
        return f"$ {v:,.0f}"

    def _fmt_pct(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        return f"{float(v)*100:,.0f}%"

    rows = []

    def add_header(nombre, v25, v24, is_pct=False):
        rows.append({
            str(empresa_sel): nombre,   
            "CATEGORIA": "",
            "2025": v25,
            "CATEGORIA2": "",
            "2024": v24,
            "% CAMBIO": (None if is_pct else _pct(v25, v24)),
            "_t": "header",
            "_is_pct": bool(is_pct)
        })

    def add_detail(cat, v25, v24):
        rows.append({
            str(empresa_sel): "",
            "CATEGORIA": str(cat),
            "2025": v25,
            "CATEGORIA2": str(cat),
            "2024": v24,
            "% CAMBIO": _pct(v25, v24),
            "_t": "detail",
            "_is_pct": False
        })

    def add_section_with_details(clasif_names, header_name, total25, total24):
        add_header(header_name, total25, total24, is_pct=False)
        sub = df_cat[df_cat["CLASIFICACION_A"].astype(str).str.upper().str.strip().isin(
            [str(x).upper().strip() for x in clasif_names]
        )].copy()
        if not sub.empty:
            sub = sub.sort_values("CATEGORIA_A")
            for _, r in sub.iterrows():
                add_detail(r["CATEGORIA_A"], float(r["2025"]), float(r["2024"]))

    add_section_with_details(["INGRESO"], "INGRESO", ing_25, ing_24)
    add_section_with_details(["COSS"], "COSS", coss_25, coss_24)
    add_header("UTILIDAD BRUTA", ub_25, ub_24)
    add_header("% UB",
            (ub_25/ing_25) if abs(ing_25) > 1e-9 else np.nan,
            (ub_24/ing_24) if abs(ing_24) > 1e-9 else np.nan,
            is_pct=True)

    add_section_with_details(["G.ADMN"], "G.ADMN", gadm_25, gadm_24)
    add_header("UTILIDAD OPERATIVA", uo_25, uo_24)
    add_header("%UO",
            (uo_25/ing_25) if abs(ing_25) > 1e-9 else np.nan,
            (uo_24/ing_24) if abs(ing_24) > 1e-9 else np.nan,
            is_pct=True)

    add_section_with_details(["OTROS INGRESOS", "OTROS INGRESO"], "OTROS INGRESOS", otros_ing_25, otros_ing_24)
    add_header("EBIT", ebit_25, ebit_24)
    add_header("% EBIT",
            (ebit_25/ing_25) if abs(ing_25) > 1e-9 else np.nan,
            (ebit_24/ing_24) if abs(ing_24) > 1e-9 else np.nan,
            is_pct=True)

    add_section_with_details(["GASTO FIN", "GASTO FINANCIERO"], "GASTO FIN", gasto_fin_25, gasto_fin_24)
    add_section_with_details(["INGRESO FIN", "INGRESO FINANCIERO"], "INGRESO FIN", ingreso_fin_25, ingreso_fin_24)
    add_header("EBT", ebt_25, ebt_24)
    add_header("% EBT",
            (ebt_25/ing_25) if abs(ing_25) > 1e-9 else np.nan,
            (ebt_24/ing_24) if abs(ing_24) > 1e-9 else np.nan,
            is_pct=True)

    add_section_with_details(["IMPUESTOS"], "IMPUESTOS", imp_25, imp_24)
    add_header("Utilidad después de imp.", udi_25, udi_24)
    add_header("%UDI",
            (udi_25/ing_25) if abs(ing_25) > 1e-9 else np.nan,
            (udi_24/ing_24) if abs(ing_24) > 1e-9 else np.nan,
            is_pct=True)
    add_header("EBITDA", ebitda_25, ebitda_24)

    df_det = pd.DataFrame(rows)
    df_show2 = df_det.copy()
    mask_pct = df_show2["_is_pct"].fillna(False)
    df_show2.loc[~mask_pct, "2025"] = df_show2.loc[~mask_pct, "2025"].apply(_fmt_money)
    df_show2.loc[~mask_pct, "2024"] = df_show2.loc[~mask_pct, "2024"].apply(_fmt_money)
    df_show2.loc[~mask_pct, "% CAMBIO"] = df_show2.loc[~mask_pct, "% CAMBIO"].apply(_fmt_pct)
    df_show2.loc[mask_pct, "2025"] = df_show2.loc[mask_pct, "2025"].apply(_fmt_pct)
    df_show2.loc[mask_pct, "2024"] = df_show2.loc[mask_pct, "2024"].apply(_fmt_pct)
    df_show2.loc[mask_pct, "% CAMBIO"] = ""

    def _style_detalle(row):
        return ["font-weight:800; background:#f2f2f2;"] * len(row) if row.get("_t") == "header" else [""] * len(row)

    st.dataframe(
        df_show2[[str(empresa_sel), "CATEGORIA", "2025", "CATEGORIA2", "2024", "% CAMBIO"]]
            .style.apply(_style_detalle, axis=1),
        use_container_width=True,
        hide_index=True
    )


def tabla_escenarios_balance():
    col1, col2 = st.columns([1, 1])

    OPCIONES_EMPRESA = ["ACUMULADO"] + EMPRESAS
    empresa_sel = col1.selectbox("Empresa", OPCIONES_EMPRESA, index=0)

    df_mapeo_local = cargar_mapeo(mapeo_url)
    if df_mapeo_local.empty:
        st.stop()

    if empresa_sel == "ACUMULADO":
        empresas_cargar = EMPRESAS[:] 
    else:
        empresas_cargar = [empresa_sel]
    data_empresas = cargar_balance_multi_hojas(balance_url, empresas_cargar)
    data_empresas_ly = cargar_balance_multi_hojas(balance_ly, empresas_cargar)
    if empresa_sel == "ACUMULADO":
        dfs_act = [data_empresas.get(e, pd.DataFrame()).copy() for e in empresas_cargar]
        dfs_ly  = [data_empresas_ly.get(e, pd.DataFrame()).copy() for e in empresas_cargar]
        df_emp = pd.concat([d for d in dfs_act if not d.empty], ignore_index=True) if any([not d.empty for d in dfs_act]) else pd.DataFrame()
        df_emp_ly = pd.concat([d for d in dfs_ly if not d.empty], ignore_index=True) if any([not d.empty for d in dfs_ly]) else pd.DataFrame()
    else:
        df_emp = data_empresas.get(empresa_sel, pd.DataFrame()).copy()
        df_emp_ly = data_empresas_ly.get(empresa_sel, pd.DataFrame()).copy()

    if df_emp.empty:
        st.warning(f"⚠️ No hay datos para {empresa_sel}.")
        st.stop()

    col_cuenta = _encontrar_columna(df_emp, COLUMNAS_CUENTA)
    col_monto = _encontrar_columna(df_emp, COLUMNAS_MONTO)
    col_cuenta_ly = _encontrar_columna(df_emp_ly, COLUMNAS_CUENTA)
    col_monto_ly = _encontrar_columna(df_emp_ly, COLUMNAS_MONTO)

    if not col_cuenta or not col_monto:
        st.error(f"❌ {empresa_sel}: columnas inválidas")
        st.stop()


    data_resultados = []
    for empresa in EMPRESAS:
        df_raw = data_empresas.get(empresa, pd.DataFrame()).copy()
        if df_raw.empty:
            continue

        col_cuenta_raw = _encontrar_columna(df_raw, NUMERO_CUENTA)
        col_monto_raw = _encontrar_columna(df_raw, COLUMNAS_MONTO)

        if not col_cuenta_raw or not col_monto_raw:
            st.warning(f"⚠️ {empresa}: no encontré columnas de Cuenta/Saldo para resultados.")
            continue
        df_raw[col_cuenta_raw] = df_raw[col_cuenta_raw].apply(limpiar_cuenta)
        df_raw[col_monto_raw] = _to_numeric_money(df_raw[col_monto_raw])

        df_raw = df_raw.dropna(subset=[col_cuenta_raw])
        df_cta = df_raw.groupby(col_cuenta_raw, as_index=False)[col_monto_raw].sum()

        ingreso = df_cta.loc[
            (df_cta[col_cuenta_raw] > 400000000) & (df_cta[col_cuenta_raw] < 500000000),
            col_monto_raw
        ].sum()

        gasto = df_cta.loc[
            (df_cta[col_cuenta_raw] > 500000000),
            col_monto_raw
        ].sum()

        utilidad = ingreso + gasto

        data_resultados.append({
            "EMPRESA": empresa,
            "INGRESO": float(ingreso),
            "GASTO": float(gasto),
            "UTILIDAD": float(utilidad),
        })

    df_resultados = pd.DataFrame(data_resultados)

    if empresa_sel == "ACUMULADO" and not df_resultados.empty:
        df_total = pd.DataFrame([{
            "EMPRESA": "TOTAL",
            "INGRESO": float(df_resultados["INGRESO"].sum()),
            "GASTO": float(df_resultados["GASTO"].sum()),
            "UTILIDAD": float(df_resultados["UTILIDAD"].sum()),
        }])
        df_resultados = pd.concat([df_resultados, df_total], ignore_index=True)

    st.markdown("### Estado de Resultados por Empresa")
    st.dataframe(df_resultados, use_container_width=True, hide_index=True)


    df_emp[col_cuenta] = df_emp[col_cuenta].apply(limpiar_cuenta)
    df_emp[col_monto] = _to_numeric_money(df_emp[col_monto])
    df_emp = df_emp.dropna(subset=[col_cuenta])
    df_emp = df_emp.groupby(col_cuenta, as_index=False)[col_monto].sum()

    df_emp_ly[col_cuenta_ly] = df_emp_ly[col_cuenta_ly].apply(limpiar_cuenta)
    df_emp_ly[col_monto_ly] = _to_numeric_money(df_emp_ly[col_monto_ly])
    df_emp_ly = df_emp_ly.dropna(subset=[col_cuenta_ly])
    df_emp_ly = df_emp_ly.groupby(col_cuenta_ly, as_index=False)[col_monto_ly].sum()

    df_merged = df_emp.merge(
        df_mapeo_local[["Cuenta", "CLASIFICACION", "CATEGORIA"]],
        left_on=col_cuenta,
        right_on="Cuenta",
        how="left",
    )

    df_merged_ly = df_emp_ly.merge(
        df_mapeo_local[["Cuenta", "CLASIFICACION", "CATEGORIA"]],
        left_on=col_cuenta_ly,
        right_on="Cuenta",
        how="left",
    )

    df_no_mapeadas = df_merged[df_merged["CLASIFICACION"].isna()].copy()
    df_ok = df_merged[~df_merged["CLASIFICACION"].isna()].copy()
    df_ok_ly = df_merged_ly[~df_merged_ly["CLASIFICACION"].isna()].copy()

    if df_ok.empty:
        st.warning(f"⚠️ {empresa_sel}: sin coincidencias con el mapeo.")
        st.stop()

    ORDEN = ("ACTIVO", "PASIVO", "CAPITAL")

    df_ok["CLASIFICACION"] = df_ok["CLASIFICACION"].astype(str).str.upper().str.strip()
    df_ok["CATEGORIA"] = df_ok["CATEGORIA"].astype(str).str.strip()
    df_ok[col_monto] = pd.to_numeric(df_ok[col_monto], errors="coerce").fillna(0.0)

    df_ok = df_ok[df_ok["CLASIFICACION"].isin(ORDEN)].copy()
    df_ok = df_ok[df_ok["CATEGORIA"].str.upper().ne("MAYOR")].copy()

    df_grp = (
        df_ok.groupby(["CLASIFICACION", "CATEGORIA"], as_index=False)[col_monto]
        .sum()
        .rename(columns={col_monto: "MONTO"})
    )
    df_merged_ly = df_emp_ly.merge(
        df_mapeo_local[["Cuenta", "CLASIFICACION", "CATEGORIA"]],
        left_on=col_cuenta_ly,
        right_on="Cuenta",
        how="left",
    )

    df_ok_ly = df_merged_ly[~df_merged_ly["CLASIFICACION"].isna()].copy()

    df_ok_ly["CLASIFICACION"] = df_ok_ly["CLASIFICACION"].astype(str).str.upper().str.strip()
    df_ok_ly["CATEGORIA"] = df_ok_ly["CATEGORIA"].astype(str).str.strip()
    df_ok_ly[col_monto_ly] = pd.to_numeric(df_ok_ly[col_monto_ly], errors="coerce").fillna(0.0)

    df_ok_ly = df_ok_ly[df_ok_ly["CLASIFICACION"].isin(ORDEN)].copy()
    df_ok_ly = df_ok_ly[df_ok_ly["CATEGORIA"].str.upper().ne("MAYOR")].copy()

    df_grp_ly = (
        df_ok_ly.groupby(["CLASIFICACION", "CATEGORIA"], as_index=False)[col_monto_ly]
        .sum()
        .rename(columns={col_monto_ly: "MONTO_LY"})
    )

    df_base = df_grp.merge(df_grp_ly, on=["CLASIFICACION", "CATEGORIA"], how="outer")
    df_base["MONTO"] = pd.to_numeric(df_base["MONTO"], errors="coerce").fillna(0.0)
    df_base["MONTO_LY"] = pd.to_numeric(df_base["MONTO_LY"], errors="coerce").fillna(0.0)
    df_base["% VARIACION"] = np.where(
        df_base["MONTO_LY"].abs() > 1e-9,
        (df_base["MONTO"] / df_base["MONTO_LY"]) - 1.0,
        np.nan
    )

    rows = []
    totales = {}
    totales_ly = {}

    for clasif in ORDEN:
        sub = df_base[df_base["CLASIFICACION"] == clasif].copy()

        total_act = float(sub["MONTO"].sum()) if not sub.empty else 0.0
        total_ly  = float(sub["MONTO_LY"].sum()) if not sub.empty else 0.0
        totales[clasif] = total_act
        totales_ly[clasif] = total_ly

        rows.append({
            "SECCION": clasif,
            "CUENTA": "",
            "MONTO": total_act,
            "MONTO_LY": total_ly,
            "% VARIACION": (total_act / total_ly - 1.0) if abs(total_ly) > 1e-9 else np.nan
        })
        if not sub.empty:
            sub = sub.sort_values("CATEGORIA")
            for _, r in sub.iterrows():
                rows.append({
                    "SECCION": "",
                    "CUENTA": str(r["CATEGORIA"]),
                    "MONTO": float(r["MONTO"]),
                    "MONTO_LY": float(r["MONTO_LY"]),
                    "% VARIACION": float(r["% VARIACION"]) if pd.notna(r["% VARIACION"]) else np.nan
                })
        st.markdown("### Ajustes de escenario (Balance)")

        c1, c2, c3 = st.columns(3)
        modo_bal = c1.selectbox(
            "Modo de ajuste",
            ["% sobre Proveedores", "Monto (MXN)"],
            index=0,
            key=f"modo_bal_{empresa_sel}"
        )

        CAT_PROV = "PROVEEDORES"

        prov_25_base = float(df_base.loc[
            (df_base["CLASIFICACION"].eq("PASIVO")) & (df_base["CATEGORIA"].astype(str).str.upper().str.strip().eq(CAT_PROV)),
            "MONTO"
        ].sum())

        prov_24_base = float(df_base.loc[
            (df_base["CLASIFICACION"].eq("PASIVO")) & (df_base["CATEGORIA"].astype(str).str.upper().str.strip().eq(CAT_PROV)),
            "MONTO_LY"
        ].sum())

        if modo_bal == "% sobre Proveedores":
            p25 = c2.slider("% Proveedores 2025", -50.0, 50.0, 0.0, 0.5, key=f"prov_pct_25_{empresa_sel}")/100.0
            p24 = c3.slider("% Proveedores 2024", -50.0, 50.0, 0.0, 0.5, key=f"prov_pct_24_{empresa_sel}")/100.0
            prov_25_scn = prov_25_base * (1.0 + p25)
            prov_24_scn = prov_24_base * (1.0 + p24)
        else:
            d25 = c2.number_input("Δ Proveedores 2025 (MXN)", value=0.0, step=1000.0, key=f"prov_m_25_{empresa_sel}")
            d24 = c3.number_input("Δ Proveedores 2024 (MXN)", value=0.0, step=1000.0, key=f"prov_m_24_{empresa_sel}")
            prov_25_scn = prov_25_base + d25
            prov_24_scn = prov_24_base + d24
        mask_prov = (df_base["CLASIFICACION"].eq("PASIVO")) & (
            df_base["CATEGORIA"].astype(str).str.upper().str.strip().eq(CAT_PROV)
        )

        df_base.loc[mask_prov, "MONTO"] = prov_25_scn
        df_base.loc[mask_prov, "MONTO_LY"] = prov_24_scn
        df_base["% VARIACION"] = np.where(
            df_base["MONTO_LY"].abs() > 1e-9,
            (df_base["MONTO"] / df_base["MONTO_LY"]) - 1.0,
            np.nan
        )

        rows.append({"SECCION": "", "CUENTA": "", "MONTO": None, "MONTO_LY": None, "% VARIACION": None})

    if df_resultados.empty:
        utilidad_sel = 0.0
    else:
        if empresa_sel == "ACUMULADO":
            utilidad_sel = float(df_resultados.loc[df_resultados["EMPRESA"] != "TOTAL", "UTILIDAD"].sum())
        else:
            s = df_resultados.loc[df_resultados["EMPRESA"] == empresa_sel, "UTILIDAD"]
            utilidad_sel = float(s.iloc[0]) if not s.empty else 0.0
  
    st.markdown("### Ajuste de Utilidad (impacta CAPITAL)")

    u1, u2 = st.columns(2)
    modo_u = u1.selectbox(
        "Modo utilidad",
        ["Δ Monto (MXN)", "% sobre utilidad"],
        index=0,
        key=f"modo_util_{empresa_sel}"
    )

    util_base = float(utilidad_sel)

    if modo_u == "Δ Monto (MXN)":
        delta_u = u2.number_input("Δ Utilidad (MXN)", value=0.0, step=1000.0, key=f"du_{empresa_sel}")
        utilidad_sel = util_base + delta_u
    else:
        pct_u = u2.slider("% utilidad", -50.0, 50.0, 0.0, 0.5, key=f"pu_{empresa_sel}")/100.0
        utilidad_sel = util_base * (1.0 + pct_u)


    totales["CAPITAL"] = float(totales.get("CAPITAL", 0.0)) + utilidad_sel
    totales_ly["CAPITAL"] = float(totales_ly.get("CAPITAL", 0.0)) + utilidad_sel

    dif = float(totales.get("ACTIVO", 0.0) + (totales.get("PASIVO", 0.0) + totales.get("CAPITAL", 0.0)))
    dif_ly = float(totales_ly.get("ACTIVO", 0.0) + (totales_ly.get("PASIVO", 0.0) + totales_ly.get("CAPITAL", 0.0)))

    rows.append({
        "SECCION": "RESUMEN",
        "CUENTA": "DIFERENCIA",
        "MONTO": dif,
        "MONTO_LY": dif_ly,
        "% VARIACION": (dif / dif_ly - 1.0) if abs(dif_ly) > 1e-9 else np.nan
    })

    df_out_raw = pd.DataFrame(rows)
    def fmt_money(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        return f"${float(x):,.2f}"

    def fmt_pct(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        return f"{x*100:,.1f}%"

    df_out_show = df_out_raw.copy()
    df_out_show["MONTO"] = df_out_show["MONTO"].apply(fmt_money)
    df_out_show["MONTO_LY"] = df_out_show["MONTO_LY"].apply(fmt_money)
    df_out_show["% VARIACION"] = df_out_show["% VARIACION"].apply(fmt_pct)

    def estilo_reporte(row):
        t = row.get("")
        if t == "header":
            return ["font-weight:700; border-top:2px solid #999; border-bottom:1px solid #999;"] * len(row)
        if t == "blank":
            return ["background-color:#fff;"] * len(row)
        return [""] * len(row)

    st.markdown(f"### {empresa_sel}")
    st.dataframe(
        df_out_show[["SECCION", "CUENTA", "MONTO", "MONTO_LY", "% VARIACION"]]
            .style
            .apply(estilo_reporte, axis=1)
            .hide(axis="columns"),
        use_container_width=True,
        hide_index=True
    )

    if abs(dif) < 1:
        st.success("✅ El balance está cuadrado")
    else:
        st.error("❌ El balance no cuadra. Revisa mapeo/cuentas.")

    if not df_no_mapeadas.empty:
        st.markdown("## ⚠️ Cuentas NO mapeadas")
        cols_show = [col_cuenta, col_monto]
        cols_show = [c for c in cols_show if c in df_no_mapeadas.columns]
        df_nm = df_no_mapeadas[cols_show].copy().rename(columns={col_cuenta: "Cuenta", col_monto: "Saldo"})
        st.dataframe(df_nm, use_container_width=True, hide_index=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_ok.to_excel(writer, index=False, sheet_name=f"{empresa_sel[:25]}_detalle")
        df_grp.to_excel(writer, index=False, sheet_name=f"{empresa_sel[:25]}_agrupado")
        if not df_no_mapeadas.empty:
            df_no_mapeadas.to_excel(writer, index=False, sheet_name="No_mapeadas")
    st.markdown(f"### {empresa_sel}")

    nombre_archivo = "Balance_Acumulado_TODAS.xlsx" if empresa_sel == "ACUMULADO" else f"Balance_Acumulado_{empresa_sel}.xlsx"

    st.download_button(
        label=f"💾 Descargar Excel ({empresa_sel})",
        data=output.getvalue(),
        file_name=f"Balance_Acumulado_{empresa_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )


if selected == "BALANCE GENERAL":
    tabla_balance_por_empresa()

elif selected == "BALANCE POR EMPRESA":
    tabla_balance_general_acumulado()

elif selected == "ESTADO DE RESULTADOS":
    tabla_estado_resultados()

elif selected == "ESCENARIOS EDR":
    tabla_escenarios_edr()

elif selected == "ESCENARIOS BALANCE":
    tabla_escenarios_balance()
























































































































































