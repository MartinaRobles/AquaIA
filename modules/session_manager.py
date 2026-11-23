
import streamlit as st


def inicializar_sesion():
    """
    Inicializa los datos de la sesión actual.
    """

    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if "cliente_id" not in st.session_state:
        st.session_state.cliente_id = None

    if "nombre_cliente" not in st.session_state:
        st.session_state.nombre_cliente = None

    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    if "solicitud_pendiente" not in st.session_state:
        st.session_state.solicitud_pendiente = {}

    if "contexto_ia" not in st.session_state:
        st.session_state.contexto_ia = {
            "ultimo_tema": None
    }


def iniciar_sesion(cliente):
    """
    Inicia una sesión de demostración
    con un cliente ficticio.
    """

    st.session_state.autenticado = True
    st.session_state.cliente_id = cliente["id"]
    st.session_state.nombre_cliente = cliente["nombre"]
    st.session_state.solicitud_pendiente = {}
    st.session_state.contexto_ia = {
        "ultimo_tema": None
}

    st.session_state.mensajes = [
        {
            "role": "assistant",
            "content": (
                f"¡Hola, {cliente['nombre']}! "
                "Soy AquaIA, tu asistente virtual. "
                "¿En qué puedo ayudarte?"
            )
        }
    ]


def cerrar_sesion():
    """
    Elimina los datos de la sesión actual.
    """

    for clave in [
        "autenticado",
        "cliente_id",
        "nombre_cliente",
        "mensajes"
        "solicitud_pendiente"
        "contexto_ia"
    ]:
        st.session_state.pop(clave, None)


def cliente_autenticado():
    """
    Indica si la sesión actual está activa.
    """

    return st.session_state.get(
        "autenticado", False
    )
