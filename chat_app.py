
import streamlit as st
from modules.chatbot import procesar_mensaje_ia

from modules.customers import listar_clientes
from modules.session_manager import (
    inicializar_sesion,
    iniciar_sesion,
    cerrar_sesion,
    cliente_autenticado
)


st.set_page_config(
    page_title="AquaIA - Chat",
    page_icon="💧",
    layout="centered"
)

inicializar_sesion()

st.title("💧 AquaIA")
st.caption("Asistente personalizado - Prototipo con datos ficticios")


# ----------------------------------------
# INICIO DE SESIÓN DE DEMOSTRACIÓN
# ----------------------------------------

if not cliente_autenticado():

    st.subheader("Iniciar sesión de prueba")

    clientes = listar_clientes()

    if not clientes:
        st.error("No existen clientes de prueba.")
        st.stop()

    opciones = {
        cliente["id"]: cliente
        for cliente in clientes
    }

    cliente_id = st.selectbox(
        "Selecciona un cliente ficticio",
        options=list(opciones.keys()),
        format_func=lambda id: opciones[id]["nombre"]
    )

    st.warning(
        "Este acceso es solamente para desarrollo local. "
        "Todavía no está integrado con el OTP."
    )

    if st.button("Iniciar sesión", type="primary"):

        iniciar_sesion(opciones[cliente_id])
        st.rerun()

    st.stop()


# ----------------------------------------
# SESIÓN ACTIVA
# ----------------------------------------

st.sidebar.success(
    f"Sesión: {st.session_state.nombre_cliente}"
)

if st.sidebar.button("Cerrar sesión"):

    cerrar_sesion()
    st.rerun()


st.subheader(
    f"Hola, {st.session_state.nombre_cliente}"
)

st.write("Puedes comenzar a conversar conmigo.")


# ----------------------------------------
# HISTORIAL DE CONVERSACIÓN
# ----------------------------------------

for mensaje in st.session_state.mensajes:

    with st.chat_message(mensaje["role"]):
        st.write(mensaje["content"])


# ----------------------------------------
# ENTRADA DEL CLIENTE
# ----------------------------------------

pregunta = st.chat_input(
    "Escribe tu pregunta..."
)

if pregunta:

    # Guardar mensaje del cliente
    st.session_state.mensajes.append(
        {
            "role": "user",
            "content": pregunta
        }
    )

    with st.chat_message("user"):
        st.write(pregunta)

    # Consultar los módulos de AquaIA
    try:
        respuesta = procesar_mensaje_ia(
            texto=pregunta,
            cliente_id=st.session_state.cliente_id,
            estado=st.session_state.solicitud_pendiente,
            contexto=st.session_state.contexto_ia
    )

    except Exception:
        respuesta = (
            "No pude procesar tu consulta con IA "
            "en este momento. Inténtalo nuevamente."
    )

    st.session_state.mensajes.append(
        {
            "role": "assistant",
            "content": respuesta
        }
    )

    with st.chat_message("assistant"):
        st.write(respuesta)
