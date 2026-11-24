
from datetime import datetime, timedelta

from modules.consumption import obtener_consumos_cliente


def comparar_consumos(cliente_id):
    """
    Compara dos períodos consecutivos de 72 horas.

    Utiliza únicamente las mediciones disponibles
    para el cliente indicado.
    """

    registros = obtener_consumos_cliente(cliente_id)

    if not registros:
        return {
            "disponible": False,
            "mensaje": "No hay registros de consumo."
        }

    # Convertimos fechas y litros.
    datos = []

    for registro in registros:
        fecha = datetime.strptime(
            registro["fecha_hora"],
            "%Y-%m-%d %H:%M:%S"
        )

        datos.append({
            "fecha": fecha,
            "litros": float(registro["litros"])
        })

    datos.sort(key=lambda x: x["fecha"])

    # Para comparar dos períodos necesitamos
    # 144 mediciones horarias consecutivas.
    recientes = datos[-144:]

    if len(recientes) < 144:
        return {
            "disponible": False,
            "mensaje": (
                "No hay suficientes mediciones para "
                "comparar dos períodos de 72 horas."
            )
        }

    # Comprobamos que no falten horas intermedias.
    for i in range(1, len(recientes)):
        diferencia = (
            recientes[i]["fecha"]
            - recientes[i - 1]["fecha"]
        )

        if diferencia != timedelta(hours=1):
            return {
                "disponible": False,
                "mensaje": (
                    "Hay horas sin mediciones o registros "
                    "duplicados. No puedo hacer una "
                    "comparación completa y confiable."
                )
            }

    periodo_anterior = recientes[:72]
    periodo_actual = recientes[72:]

    consumo_anterior = sum(
        r["litros"] for r in periodo_anterior
    )

    consumo_actual = sum(
        r["litros"] for r in periodo_actual
    )

    diferencia = consumo_actual - consumo_anterior

    if consumo_anterior > 0:
        porcentaje = (
            diferencia / consumo_anterior
        ) * 100
    else:
        porcentaje = None

    if diferencia > 0:
        tendencia = "aumento"
    elif diferencia < 0:
        tendencia = "disminucion"
    else:
        tendencia = "sin_cambio"

    return {
        "disponible": True,
        "consumo_actual": round(consumo_actual, 2),
        "consumo_anterior": round(consumo_anterior, 2),
        "diferencia_litros": round(diferencia, 2),
        "porcentaje": (
            round(porcentaje, 2)
            if porcentaje is not None
            else None
        ),
        "tendencia": tendencia,
        "actual_inicio": periodo_actual[0]["fecha"],
        "actual_fin": periodo_actual[-1]["fecha"],
        "anterior_inicio": periodo_anterior[0]["fecha"],
        "anterior_fin": periodo_anterior[-1]["fecha"]
    }


def responder_comparacion(cliente_id):
    """
    Construye una respuesta verificable con
    los resultados de la comparación.
    """

    datos = comparar_consumos(cliente_id)

    if not datos["disponible"]:
        return datos["mensaje"]

    def formato_litros(valor):
        return f"{valor:,.1f}".replace(
            ",", "X"
        ).replace(
            ".", ","
        ).replace(
            "X", "."
        )

    actual = formato_litros(datos["consumo_actual"])
    anterior = formato_litros(datos["consumo_anterior"])
    diferencia = formato_litros(
        abs(datos["diferencia_litros"])
    )

    respuesta = (
        "Comparación de tus registros horarios:\n\n"
        f"- Últimas 72 horas registradas: {actual} L.\n"
        f"- 72 horas anteriores: {anterior} L.\n"
    )

    if datos["tendencia"] == "sin_cambio":
        respuesta += (
            "\nTu consumo fue igual en ambos períodos."
        )
    else:
        movimiento = (
            "aumentó"
            if datos["tendencia"] == "aumento"
            else "disminuyó"
        )

        respuesta += (
            f"\nTu consumo {movimiento} "
            f"en {diferencia} litros."
        )

        if datos["porcentaje"] is not None:
            porcentaje = formato_litros(
                abs(datos["porcentaje"])
            )

            respuesta += (
                f" Esto equivale al {porcentaje}% "
                "respecto del período anterior."
            )
        else:
            respuesta += (
                " No es posible calcular el porcentaje "
                "porque el período anterior tuvo "
                "un consumo de cero litros."
            )

    respuesta += (
        "\n\nLa comparación utiliza únicamente "
        "mediciones disponibles y no determina "
        "por sí sola la causa de una variación."
    )

    return respuesta


if __name__ == "__main__":
    for cliente_id in [1, 3, 8]:
        print(f"\n--- CLIENTE {cliente_id} ---")
        print(responder_comparacion(cliente_id))
