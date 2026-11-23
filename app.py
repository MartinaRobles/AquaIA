
import streamlit as st
import pandas as pd

from modules.customers import listar_clientes
from modules.billing import (
    obtener_facturas_cliente,
    obtener_deuda_cliente
)
from modules.consumption import (
    obtener_consumos_cliente,
    analizar_consumo,
    detectar_consumo_nocturno
)


# -------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# -------------------------------------------

st.set_page_config(
    page_title="AquaIA",
    page_icon="💧",
    layout="wide"
)

st.title("💧 AquaIA")
st.subheader("Asistente de atención al cliente")

st.info(
    "Prototipo de demostración. "
    "Todos los datos son ficticios."
)


# -------------------------------------------
# SELECCIÓN DE CLIENTE
# -------------------------------------------

clientes = listar_clientes()

if not clientes:
    st.warning("No hay clientes registrados.")
    st.stop()

opciones_clientes = {
    cliente["id"]: cliente["nombre"]
    for cliente in clientes
}

st.sidebar.header("Panel de pruebas")

cliente_id = st.sidebar.selectbox(
    "Selecciona un cliente ficticio",
    options=list(opciones_clientes.keys()),
    format_func=lambda id: opciones_clientes[id]
)

# Solo para demostración local.
# En producción se utilizará autenticación OTP.

cliente = next(
    c for c in clientes
    if c["id"] == cliente_id
)

st.header(f"Bienvenido, {cliente['nombre']}")

st.write(f"**Sector:** {cliente['sector']}")
st.write(f"**Estado:** {cliente['estado']}")


# -------------------------------------------
# FACTURACIÓN
# -------------------------------------------

st.divider()
st.header("💳 Facturación")

facturas = obtener_facturas_cliente(cliente_id)
deuda = obtener_deuda_cliente(cliente_id)

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Facturas registradas",
        len(facturas)
    )

with col2:
    st.metric(
        "Total pendiente de pago",
        f"${deuda:,.0f}".replace(",", ".")
    )

if facturas:
    df_facturas = pd.DataFrame(facturas)

    st.dataframe(
        df_facturas,
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("No se encontraron facturas.")


# -------------------------------------------
# CONSUMO HORARIO
# -------------------------------------------

st.divider()
st.header("🚰 Consumo de agua")

analisis = analizar_consumo(cliente_id)
consumos = obtener_consumos_cliente(cliente_id)

if analisis:

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Consumo total registrado",
            f"{analisis['total_litros']:,.0f} L"
        )

    with col2:
        st.metric(
            "Promedio por hora",
            f"{analisis['promedio_horario']:.1f} L"
        )

    with col3:
        st.metric(
            "Mayor consumo horario",
            f"{analisis['litros_maximos']:.0f} L"
        )

    # PREPARAR DATOS PARA EL GRÁFICO

    df_consumos = pd.DataFrame(consumos)

    df_consumos["fecha_hora"] = pd.to_datetime(
        df_consumos["fecha_hora"]
    )

    df_consumos = df_consumos.set_index("fecha_hora")

    st.subheader("Evolución del consumo horario")

    st.line_chart(df_consumos["litros"])

    # CALCULAR CONSUMO POR DÍA

    st.subheader("Consumo diario")

    consumo_diario = df_consumos["litros"].resample(
        "D"
    ).sum()

    st.bar_chart(consumo_diario)

else:
    st.warning("No hay registros de consumo.")


# -------------------------------------------
# DETECCIÓN DE ANOMALÍAS
# -------------------------------------------

st.divider()
st.header("🔎 Análisis de consumo nocturno")

resultado_nocturno = detectar_consumo_nocturno(
    cliente_id
)

if resultado_nocturno:

    st.write(
        "**Promedio nocturno:**",
        resultado_nocturno["promedio_nocturno"],
        "litros por hora"
    )

    if resultado_nocturno["posible_anomalia"]:

        st.warning(
            "Se detectó un consumo nocturno elevado "
            "en los datos simulados. "
            "Este patrón podría indicar un consumo "
            "inusual o una posible fuga. "
            "No constituye un diagnóstico."
        )

    else:

        st.success(
            "No se detectó un consumo nocturno "
            "elevado según el umbral experimental."
        )

else:
    st.info(
        "No existen suficientes registros nocturnos."
    )


# -------------------------------------------
# PIE DE PÁGINA
# -------------------------------------------

st.divider()

st.caption(
    "AquaIA - Prototipo experimental. "
    "Sin conexión a sistemas reales."
)
