
import re
import streamlit as st
from openai import OpenAI


def crear_introduccion(tema):
    """
    Genera una breve introducción conversacional.

    No recibe datos personales, montos ni facturas.
    """

    introducciones = {
        "facturacion": (
            "Con gusto, revisemos tu información "
            "de facturación."
        ),
        "consumo": (
            "Claro, revisemos tus registros "
            "de consumo disponibles."
        ),
        "solicitudes": (
            "Por supuesto, revisemos la "
            "información de tus solicitudes."
        )
    }

    # Respuesta de respaldo si falla la API.
    respaldo = introducciones.get(tema, "")

    if not respaldo:
        return ""

    try:
        cliente = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"],
            timeout=10.0,
            max_retries=1
        )

        respuesta = cliente.responses.create(
            model=st.secrets.get(
                "OPENAI_MODEL", "gpt-6-luna"
            ),
            instructions=(
                "Eres AquaIA, un asistente cordial "
                "de una empresa sanitaria chilena. "
                "Escribe una única frase breve en español "
                "para introducir información del tema indicado. "
                "No incluyas números, montos, fechas, "
                "nombres, diagnósticos, promesas ni "
                "afirmaciones sobre el estado del cliente. "
                "No inventes información de la empresa. "
                "Máximo 20 palabras."
            ),
            input=f"Tema: {tema}",
            max_output_tokens=60,
            store=False
        )

        introduccion = respuesta.output_text.strip()

        # Control básico de longitud y contenido.
        if (
            not introduccion
            or len(introduccion) > 180
            or len(introduccion.split()) > 20
            or re.search(r"\d", introduccion)
        ):
            return respaldo

        return introduccion

    except Exception:
        return respaldo


def construir_respuesta_natural(
    respuesta_verificada,
    tema
):
    """
    Conserva intacto el resultado generado
    por los módulos de Python.
    """

    if not respuesta_verificada:
        return (
            "No tengo información suficiente "
            "para responder esa consulta."
        )

    introduccion = crear_introduccion(tema)

    if not introduccion:
        return respuesta_verificada

    return (
        f"{introduccion}\n\n"
        f"{respuesta_verificada}"
    )
