"""
app.py - Panel de control del proyecto de optimización de la luz.

Se despliega en Streamlit Community Cloud (gratis), conectado a este mismo
repositorio de GitHub. Lee resultado_comparacion.json, que se regenera
automáticamente cada día mediante GitHub Actions.
"""
import json
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="Optimizador de la luz", page_icon="⚡", layout="centered")

st.title("⚡ Optimizador de tarifa eléctrica")


@st.cache_data(ttl=3600)
def cargar_informe():
    try:
        with open("resultado_comparacion.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


informe = cargar_informe()

if informe is None:
    st.warning(
        "Todavía no hay ningún informe generado. Esto es normal si acabas de "
        "montar el proyecto: en cuanto se ejecute la primera vez la automatización "
        "diaria de GitHub Actions, aparecerán aquí los datos."
    )
    st.stop()

generado = datetime.fromisoformat(informe["generado_utc"])
st.caption(f"Última actualización: {generado.strftime('%d/%m/%Y %H:%M')} UTC · "
           f"basado en {informe['dias_de_consumo_usados']} días de consumo real")

# --- Recomendación principal ---
mejor = informe.get("mejor_tarifa")
if mejor:
    st.header("💡 Mejor tarifa para ti ahora mismo")
    col1, col2 = st.columns(2)
    col1.metric("Tarifa recomendada", mejor["nombre"])
    col2.metric("Coste mensual estimado", f"{mejor['total_mensual_estimado_eur']} €")
    if mejor.get("url"):
        st.markdown(f"[Ver esta tarifa]({mejor['url']})")
    if mejor.get("indexada_pvpc"):
        st.info("Esta tarifa está indexada al precio PVPC (variable cada hora).")
else:
    st.warning(
        "Aún no hay suficientes datos de consumo acumulados para calcular una "
        "recomendación fiable. Necesitas al menos varios días de histórico."
    )

# --- Potencia contratada ---
st.header("🔌 Potencia contratada")
pot = informe.get("sugerencia_potencia", {})
actual = informe.get("potencia_contratada_actual_kw")

if "error" in pot:
    st.write(f"Potencia actual: **{actual} kW**. {pot['error']}")
else:
    sugerida = pot["potencia_sugerida_kw"]
    maximo = pot["maximo_demandado_kw"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Contratada", f"{actual} kW")
    c2.metric("Máximo demandado (12m)", f"{maximo} kW")
    c3.metric("Sugerida", f"{sugerida} kW")

    if sugerida < actual:
        st.success(
            f"Podrías bajar de {actual} kW a {sugerida} kW y ahorrar en el "
            f"término de potencia, manteniendo margen de seguridad."
        )
    elif sugerida > actual:
        st.warning(
            f"Tu consumo se acerca al límite de tu potencia contratada "
            f"(máximo demandado {maximo} kW sobre {actual} kW contratados). "
            f"Vigila los picos para evitar cortes."
        )
    else:
        st.success("Tu potencia contratada ya es la óptima. 👍")

# --- Ranking completo de tarifas ---
st.header("📊 Ranking completo de tarifas")
ranking = informe.get("ranking_tarifas", [])
if ranking:
    filas = [
        {
            "Tarifa": r["nombre"],
            "€/mes estimado": r["total_mensual_estimado_eur"],
            "Energía (€)": r["coste_energia_eur"],
            "Potencia (€)": r["coste_potencia_eur"],
            "Indexada PVPC": "Sí" if r["indexada_pvpc"] else "No",
        }
        for r in ranking
    ]
    st.dataframe(filas, use_container_width=True, hide_index=True)
else:
    st.write("Sin datos todavía.")

st.divider()
st.caption(
    "Datos de consumo: Datadis (datos oficiales de tu distribuidora). "
    "Precio PVPC: REData (Red Eléctrica de España). "
    "Tarifas de mercado: simuladorfacturaluz.es. "
    "Cálculos sin impuestos (IVA/IEE), válidos para comparar entre tarifas."
)
