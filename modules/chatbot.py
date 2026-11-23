
from modules.ai_router import interpretar_pregunta
import unicodedata
from modules.natural_responses import construir_respuesta_natural

from database.connection import get_connection
from modules.billing import (
    obtener_facturas_cliente,
    obtener_deuda_cliente
)
from modules.consumption import (
    analizar_consumo,
    detectar_consumo_nocturno
)
from modules.complaints import registrar_solicitud


def normalizar(texto):
    texto = texto.lower().strip()
    return "".join(
        caracter for caracter in unicodedata.normalize(
            "NFD", texto
        )
        if unicodedata.category(caracter) != "Mn"
    )


def pesos(monto):
    return "$" + f"{monto:,.0f}".replace(",", ".")


# ----------------------------------------
# FACTURACIÓN
# ----------------------------------------

def responder_facturacion(cliente_id):

    facturas = obtener_facturas_cliente(cliente_id)
    deuda = obtener_deuda_cliente(cliente_id)

    if not facturas:
        return "No encontré facturas para tu cuenta."

    respuesta = (
        f"Tu saldo pendiente registrado es de "
        f"{pesos(deuda)}.\n\n"
        "Estas son tus facturas:\n\n"
    )

    for factura in facturas:
        respuesta += (
            f"- Período {factura['periodo']}: "
            f"{pesos(factura['monto'])}, "
            f"estado: {factura['estado']}, "
            f"vencimiento: {factura['vencimiento']}.\n"
        )

    return respuesta


# ----------------------------------------
# CONSUMOS
# ----------------------------------------

def responder_consumo(cliente_id):

    datos = analizar_consumo(cliente_id)
    nocturno = detectar_consumo_nocturno(cliente_id)

    if not datos:
        return "No encontré registros de consumo."

    respuesta = (
        "Según los registros disponibles:\n\n"
        f"- Consumo total: {datos['total_litros']} litros.\n"
        f"- Promedio por hora: "
        f"{datos['promedio_horario']} litros.\n"
        f"- Mayor consumo horario: "
        f"{datos['litros_maximos']} litros.\n"
        f"- Momento del máximo: "
        f"{datos['hora_mayor_consumo']}.\n"
        f"- Horas registradas: {datos['registros']}.\n"
    )

    if nocturno:
        respuesta += (
            f"\nPromedio nocturno: "
            f"{nocturno['promedio_nocturno']} L/h.\n"
        )

        if nocturno["posible_anomalia"]:
            respuesta += (
                "\n⚠️ Se detectó consumo nocturno elevado. "
                "Podría corresponder a un consumo inusual "
                "o una posible fuga, pero no confirma "
                "que exista una fuga."
            )
        else:
            respuesta += (
                "\nNo se detectó consumo nocturno elevado "
                "según el umbral experimental."
            )

    return respuesta


# ----------------------------------------
# SOLICITUDES DEL CLIENTE
# ----------------------------------------

def responder_solicitudes(cliente_id):

    conexion = get_connection()

    try:
        resultados = conexion.execute(
            """
            SELECT id, tipo, estado, fecha_creacion
            FROM solicitudes
            WHERE cliente_id = ?
            ORDER BY fecha_creacion DESC, id DESC
            LIMIT 10
            """,
            (cliente_id,)
        ).fetchall()

        if not resultados:
            return "No encontré solicitudes asociadas a tu cuenta."

        respuesta = "Tus solicitudes registradas son:\n\n"

        for fila in resultados:
            respuesta += (
                f"- Solicitud #{fila['id']}: "
                f"{fila['tipo']}, "
                f"estado: {fila['estado']}, "
                f"fecha: {fila['fecha_creacion']}.\n"
            )

        return respuesta

    finally:
        conexion.close()


# ----------------------------------------
# REGISTRO CONVERSACIONAL DE SOLICITUD
# ----------------------------------------

def gestionar_solicitud(texto, estado):

    etapa = estado["etapa"]
    respuesta = normalizar(texto)

    if etapa == "descripcion":

        estado["descripcion"] = texto.strip()
        estado["etapa"] = "ubicacion"

        return (
            "Gracias. ¿Dónde ocurre el problema? "
            "Indícame la ubicación."
        )

    if etapa == "ubicacion":

        estado["ubicacion"] = texto.strip()
        estado["etapa"] = "confirmacion"

        return (
            "Voy a registrar la siguiente solicitud "
            "en el prototipo:\n\n"
            f"Tipo: {estado['tipo']}\n\n"
            f"Descripción: {estado['descripcion']}\n\n"
            f"Ubicación: {estado['ubicacion']}\n\n"
            "¿Confirmas el registro? Responde 'sí' o 'no'."
        )

    if etapa == "confirmacion":

        if respuesta in ("si", "confirmar"):

            resultado = registrar_solicitud(
                tipo=estado["tipo"],
                descripcion=estado["descripcion"],
                ubicacion=estado["ubicacion"],
                cliente_id=estado["cliente_id"]
            )

            estado.clear()

            return (
                "Tu solicitud fue registrada "
                "correctamente en el prototipo.\n\n"
                f"Número: #{resultado['solicitud_id']}\n\n"
                f"Estado: {resultado['estado']}\n\n"
                f"Prioridad: {resultado['prioridad']}\n\n"
                "Este registro es una simulación; "
                "no se ha enviado a una empresa real."
            )

        if respuesta in ("no", "cancelar"):

            estado.clear()
            return "Se canceló el registro de la solicitud."

        return "Por favor, responde 'sí' o 'no'."

    estado.clear()
    return "No pude continuar el registro. Inténtalo nuevamente."


# ----------------------------------------
# PROCESAMIENTO PRINCIPAL
# ----------------------------------------

def procesar_mensaje(texto, cliente_id, estado):

    pregunta = normalizar(texto)

    if not pregunta:
        return "Escribe una pregunta para continuar."

    if pregunta == "cancelar":
        if estado:
            estado.clear()
            return "Operación cancelada."
        return "No hay ninguna operación pendiente."

    # Continuar una solicitud ya iniciada.
    if estado:
        return gestionar_solicitud(texto, estado)

    # Registro de reportes.
    if (
        "reportar" in pregunta
        or "registrar reclamo" in pregunta
        or "hacer un reclamo" in pregunta
        or "crear solicitud" in pregunta
    ):

        if "fuga" in pregunta:
            tipo = "fuga_via_publica"
        elif "presion" in pregunta:
            tipo = "baja_presion"
        elif "corte" in pregunta:
            tipo = "corte_suministro"
        elif "factura" in pregunta:
            tipo = "problema_facturacion"
        else:
            tipo = "reclamo"

        estado.update({
            "cliente_id": cliente_id,
            "tipo": tipo,
            "etapa": "descripcion"
        })

        return (
            "Puedo registrar tu solicitud. "
            "Primero, describe brevemente qué ocurrió. "
            "Puedes escribir 'cancelar' para detenerte."
        )

    # Consultar solicitudes existentes.
    if any(p in pregunta for p in [
        "mis reclamos",
        "mis solicitudes",
        "estado de mi reclamo",
        "estado de mi solicitud"
    ]):
        return responder_solicitudes(cliente_id)

    # Consultar facturas.
    if any(p in pregunta for p in [
        "debo", "deuda", "factura",
        "boleta", "pagar", "vencimiento"
    ]):
        return responder_facturacion(cliente_id)

    # Consultar consumos.
    if any(p in pregunta for p in [
        "consumo", "consumi", "litros",
        "medidor", "anomalia",
        "fuga en mi casa"
    ]):
        return responder_consumo(cliente_id)

    if pregunta in ("hola", "buenas", "buenos dias"):
        return (
            "¡Hola! Puedo ayudarte con tus facturas, "
            "consumos de agua y solicitudes."
        )

    return (
        "Todavía no sé interpretar esa pregunta. "
        "Puedes probar con:\n\n"
        "- ¿Cuánto debo?\n"
        "- ¿Cómo estuvo mi consumo?\n"
        "- ¿Cuáles son mis solicitudes?\n"
        "- Quiero reportar una fuga.\n\n"
        "Más adelante incorporaré inteligencia "
        "artificial para comprender otras preguntas."
    )


def procesar_mensaje_ia(
    texto,
    cliente_id,
    estado,
    contexto
):
    """
    Interpreta la pregunta mediante IA y utiliza
    los módulos existentes para responder.
    """

    pregunta = normalizar(texto)

    # Si estamos registrando una solicitud,
    # mantenemos el proceso controlado por Python.
    if estado or pregunta == "cancelar":
        return procesar_mensaje(
            texto, cliente_id, estado
        )

    # La IA identifica la intención.
    categoria = interpretar_pregunta(
        pregunta,
        contexto.get("ultimo_tema")
    )

    # Esta pista permite continuar una conversación
    # cuando el cliente hace una pregunta breve.
    if (
        categoria == "otro"
        and pregunta in (
            "y el anterior",
            "y el mes anterior",
            "y antes",
            "y el detalle"
        )
    ):
        categoria = contexto.get(
            "ultimo_tema", "otro"
        )

    if categoria == "facturacion":
        contexto["ultimo_tema"] = "facturacion"
        return construir_respuesta_natural(
            responder_facturacion(cliente_id),
            "facturacion"
        )

    if categoria == "consumo":
        contexto["ultimo_tema"] = "consumo"

        # Evitamos responder sobre períodos que
        # todavía no permite consultar el módulo.
        if any(frase in pregunta for frase in [
            "mes anterior",
            "semana anterior",
            "ano anterior"
        ]):
            return (
                "Todavía no puedo filtrar ese período. "
                "Por ahora puedo analizar los registros "
                "horarios disponibles en la base de datos."
            )

        return construir_respuesta_natural(
            responder_consumo(cliente_id),
            "consumo"
        )

    if categoria == "solicitudes":
        contexto["ultimo_tema"] = "solicitudes"
        return construir_respuesta_natural(
            responder_solicitudes(cliente_id),
            "solicitudes"
        )

    if categoria == "registrar_solicitud":
        contexto["ultimo_tema"] = "solicitudes"

        # Conservamos el procedimiento del paso 10:
        # pedir datos y solicitar confirmación.
        return procesar_mensaje(
            "quiero reportar",
            cliente_id,
            estado
        )

    if categoria == "saludo":
        return (
            "¡Hola! Puedo ayudarte con tus facturas, "
            "consumos, reclamos y reportes. "
            "¿Qué necesitas consultar?"
        )

    return (
        "Todavía no tengo información suficiente "
        "para responder esa consulta. "
        "Puedo ayudarte con facturación, consumo "
        "de agua y solicitudes."
    )

