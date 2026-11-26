
from modules.billing import obtener_deuda_cliente
from modules.consumption import detectar_consumo_nocturno


def recomendar_siguiente_paso(cliente_id, tema):
    """
    Genera recomendaciones basadas en datos
    consultados desde los módulos de AquaIA.

    No registra solicitudes ni modifica datos.
    """

    if tema == "consumo":

        nocturno = detectar_consumo_nocturno(
            cliente_id
        )

        if nocturno is None:
            return {
                "mensaje": (
                    "Con gusto te ayudo. 💧\n\n"
                    "Todavía no tengo suficientes "
                    "mediciones nocturnas para recomendar "
                    "una acción basada en esos registros.\n\n"
                    "Si has observado una fuga o un "
                    "problema de suministro, podemos "
                    "registrar un reporte de prueba."
                ),
                "opciones": []
            }

        promedio = nocturno["promedio_nocturno"]

        if nocturno["posible_anomalia"]:
            return {
                "mensaje": (
                    "Te recomendaría comenzar revisando "
                    "si existe algún uso continuo de agua "
                    "durante la madrugada. 💧\n\n"
                    f"Tu promedio nocturno registrado "
                    f"es de **{promedio:.1f} L/h**, "
                    "considerado elevado según nuestro "
                    "umbral experimental.\n\n"
                    "Esto no confirma una fuga.\n\n"
                    "**¿Cómo quieres continuar?**\n\n"
                    "1. Revisar mis consumos nocturnos.\n"
                    "2. Registrar una solicitud de revisión."
                ),
                "opciones": [
                    "revisar_nocturno",
                    "registrar_revision"
                ]
            }

        return {
            "mensaje": (
                "Por ahora, tus mediciones nocturnas "
                "no superan nuestro umbral experimental. 💧\n\n"
                "Te recomendaría seguir observando "
                "tus consumos y revisar si hubo cambios "
                "en los horarios de mayor utilización.\n\n"
                "Esto no descarta completamente "
                "una fuga."
            ),
            "opciones": []
        }

    if tema == "facturacion":

        deuda = obtener_deuda_cliente(cliente_id)

        if deuda > 0:
            monto = f"${deuda:,.0f}".replace(",", ".")

            return {
                "mensaje": (
                    "Con gusto te oriento. 💧\n\n"
                    f"Tienes **{monto}** registrados "
                    "en facturas pendientes o vencidas.\n\n"
                    "Te recomiendo revisar sus fechas "
                    "de vencimiento y consultar los "
                    "canales oficiales de pago.\n\n"
                    "¿Quieres que revisemos el detalle "
                    "de tus facturas?"
                ),
                "opciones": []
            }

        return {
            "mensaje": (
                "No encuentro facturas pendientes "
                "ni vencidas en nuestros datos de prueba.\n\n"
                "Si quieres, podemos revisar "
                "tus facturas registradas."
            ),
            "opciones": []
        }

    if tema == "solicitudes":

        return {
            "mensaje": (
                "Con gusto te ayudo a revisar "
                "tus solicitudes. 💧\n\n"
                "Te recomiendo comenzar consultando "
                "su estado registrado.\n\n"
                "Si una solicitud requiere atención "
                "urgente o no se ha resuelto, "
                "será importante utilizar los canales "
                "oficiales de atención de la sanitaria.\n\n"
                "¿Quieres revisar tus solicitudes?"
            ),
            "opciones": []
        }

    return {
        "mensaje": (
            "¡Con gusto! 💧 Puedo orientarte "
            "sobre tus consumos, facturación "
            "o solicitudes.\n\n"
            "¿Sobre cuál de estos temas necesitas "
            "una recomendación?"
        ),
        "opciones": []
    }
