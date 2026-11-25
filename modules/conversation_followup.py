
import re
import unicodedata

from modules.consumption import (
    detectar_consumo_nocturno
)


def normalizar_respuesta(texto):
    texto = texto.lower().strip()

    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

    texto = re.sub(r"[^\w\s]", " ", texto)

    return " ".join(texto.split())


def interpretar_confirmacion(texto):
    """
    Reconoce respuestas breves y explícitas.

    No interpreta cualquier mensaje como
    una confirmación.
    """

    respuesta = normalizar_respuesta(texto)

    afirmativas = {
        "si",
        "si por favor",
        "claro",
        "dale",
        "de acuerdo",
        "por supuesto",
        "si me gustaria",
        "si hagamoslo",
        "hagamoslo"
    }

    negativas = {
        "no",
        "no gracias",
        "prefiero que no",
        "ahora no",
        "mejor no"
    }

    if respuesta in afirmativas:
        return True

    if respuesta in negativas:
        return False

    return None


OPCIONES_VALIDAS = {
    "revisar_nocturno",
    "registrar_revision"
}


def mostrar_opciones(opciones):
    """Presenta las acciones disponibles."""

    nombres = {
        "revisar_nocturno": "Revisar consumos nocturnos",
        "registrar_revision": "Registrar una solicitud de revisión"
    }

    lineas = [
        f"{i}. {nombres[opcion]}"
        for i, opcion in enumerate(opciones, start=1)
    ]

    return (
        "¡Con gusto! 💧 ¿Cuál de estas opciones prefieres?\n\n"
        + "\n".join(lineas)
        + "\n\nPuedes responder con el número "
        "o con el nombre de la opción."
    )


def identificar_opcion(texto, opciones):
    """
    Identifica una elección explícita.
    No interpreta un simple 'sí' cuando
    existen varias alternativas.
    """

    respuesta = normalizar_respuesta(texto)

    if respuesta in ("1", "opcion 1", "la primera"):
        return opciones[0]

    if (
        len(opciones) > 1
        and respuesta in ("2", "opcion 2", "la segunda")
    ):
        return opciones[1]

    if any(p in respuesta for p in [
        "nocturno", "madrugada", "revisar consumo"
    ]):
        if "revisar_nocturno" in opciones:
            return "revisar_nocturno"

    if any(p in respuesta for p in [
        "registrar", "solicitud", "reclamo", "reporte"
    ]):
        if "registrar_revision" in opciones:
            return "registrar_revision"

    return None


def procesar_seguimiento(
    texto,
    cliente_id,
    contexto,
    estado_solicitud
):
    """Continúa una oferta anterior de AquaIA."""

    oferta = contexto.get("oferta_pendiente")

    if not oferta:
        return None

    # Compatibilidad con los pasos anteriores.
    opciones = (
        [oferta] if isinstance(oferta, str)
        else list(oferta)
    )

    if (
        not opciones
        or any(op not in OPCIONES_VALIDAS for op in opciones)
    ):
        contexto["oferta_pendiente"] = None
        return None

    respuesta = normalizar_respuesta(texto)

    if respuesta in ("cancelar", "salir"):
        contexto["oferta_pendiente"] = None
        return "De acuerdo, cancelamos esa opción."

    confirmacion = interpretar_confirmacion(texto)

    if confirmacion is False:
        contexto["oferta_pendiente"] = None
        return (
            "¡Está bien! Si necesitas algo más, "
            "con gusto te ayudaré. 💧"
        )

    eleccion = identificar_opcion(texto, opciones)

    # Si hay una sola oferta, un sí es suficiente.
    if eleccion is None and confirmacion is True:
        if len(opciones) == 1:
            eleccion = opciones[0]
        else:
            # No adivinamos entre varias opciones.
            return mostrar_opciones(opciones)

    if eleccion is None:
        # Para preguntas nuevas, dejamos que el
        # chatbot continúe su clasificación normal.
        if confirmacion is None:
            contexto["oferta_pendiente"] = None
            return None

        return mostrar_opciones(opciones)

    # La oferta se consume una sola vez.
    contexto["oferta_pendiente"] = None

    if eleccion == "revisar_nocturno":

        resultado = detectar_consumo_nocturno(
            cliente_id
        )

        if resultado is None:
            return (
                "No tengo suficientes mediciones "
                "nocturnas para realizar esa revisión."
            )

        promedio = resultado["promedio_nocturno"]

        if resultado["posible_anomalia"]:
            mensaje = (
                "¡Claro! 💧 Revisé tus registros "
                "de consumo nocturno.\n\n"
                f"El promedio fue de {promedio:.1f} L/h. "
                "Encontré un valor elevado según "
                "nuestro umbral experimental.\n\n"
                "Esto no confirma una fuga, pero "
                "podemos revisar posibles usos "
                "continuos de agua."
            )
        else:
            mensaje = (
                "¡Claro! 💧 Revisé tus registros "
                "de consumo nocturno.\n\n"
                f"El promedio fue de {promedio:.1f} L/h. "
                "No encontré un consumo elevado "
                "según nuestro criterio experimental. "
                "Esto no descarta completamente "
                "la existencia de una fuga."
            )

        contexto["ultimo_tema"] = "consumo"
        contexto["oferta_pendiente"] = [
            "registrar_revision"
        ]

        return (
            mensaje
            + "\n\n¿Te gustaría registrar una "
            "solicitud de revisión?"
        )

    if eleccion == "registrar_revision":

        estado_solicitud.update({
            "cliente_id": cliente_id,
            "tipo": "reclamo",
            "etapa": "descripcion"
        })

        return (
            "¡Por supuesto! 💧 Te ayudaré a registrar "
            "una solicitud de revisión en nuestro "
            "prototipo.\n\n"
            "Cuéntame brevemente qué problema "
            "has observado.\n\n"
            "Puedes escribir 'cancelar' "
            "en cualquier momento."
        )

    return None
