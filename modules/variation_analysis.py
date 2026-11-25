
from database.connection import get_connection
from modules.historical_comparison import (
    obtener_periodos,
    formato_litros
)


def analizar_variacion(cliente_id, tipo="semana"):
    """
    Compara dos períodos completos y analiza
    en qué horarios cambió el consumo.

    Solo utiliza datos de SQLite.
    """

    if tipo not in ("semana", "mes"):
        raise ValueError("Período no válido.")

    periodos = obtener_periodos(cliente_id, tipo)

    if len(periodos) < 2:
        return {
            "disponible": False,
            "mensaje": (
                "Todavía no tengo dos períodos "
                "completos para analizar la variación."
            )
        }

    reciente, anterior = periodos

    conexion = get_connection()

    try:
        def obtener_perfil(periodo):

            filas = conexion.execute(
                """
                SELECT
                    CAST(SUBSTR(
                        co.fecha_hora, 12, 2
                    ) AS INTEGER) AS hora,
                    SUM(co.litros) AS litros
                FROM consumos AS co
                JOIN cuentas AS cu
                    ON co.cuenta_id = cu.id
                WHERE cu.cliente_id = ?
                  AND co.fecha_hora >= ?
                  AND co.fecha_hora < ?
                GROUP BY hora
                ORDER BY hora
                """,
                (
                    cliente_id,
                    periodo["inicio"].isoformat()
                    + " 00:00:00",
                    periodo["fin"].isoformat()
                    + " 00:00:00"
                )
            ).fetchall()

            return {
                fila["hora"]: float(fila["litros"])
                for fila in filas
            }

        perfil_actual = obtener_perfil(reciente)
        perfil_anterior = obtener_perfil(anterior)

    finally:
        conexion.close()

    # La validación de períodos completos
    # ya fue realizada en obtener_periodos().

    dias_actual = (
        reciente["fin"] - reciente["inicio"]
    ).days

    dias_anterior = (
        anterior["fin"] - anterior["inicio"]
    ).days

    # Normalizamos por día para comparar
    # meses con diferente duración.
    diferencias = {}

    for hora in range(24):
        promedio_actual = (
            perfil_actual.get(hora, 0)
            / dias_actual
        )

        promedio_anterior = (
            perfil_anterior.get(hora, 0)
            / dias_anterior
        )

        diferencias[hora] = (
            promedio_actual - promedio_anterior
        )

    hora_mayor_aumento = max(
        diferencias,
        key=diferencias.get
    )

    cambio_hora = diferencias[hora_mayor_aumento]

    # Horario nocturno experimental:
    # desde las 00:00 hasta las 05:59.
    horas_nocturnas = range(0, 6)

    nocturno_actual = sum(
        perfil_actual.get(h, 0)
        for h in horas_nocturnas
    ) / dias_actual

    nocturno_anterior = sum(
        perfil_anterior.get(h, 0)
        for h in horas_nocturnas
    ) / dias_anterior

    total_actual = reciente["litros"]
    total_anterior = anterior["litros"]

    promedio_diario_actual = (
        total_actual / dias_actual
    )

    promedio_diario_anterior = (
        total_anterior / dias_anterior
    )

    diferencia_diaria = (
        promedio_diario_actual
        - promedio_diario_anterior
    )

    porcentaje = None

    if promedio_diario_anterior > 0:
        porcentaje = (
            diferencia_diaria
            / promedio_diario_anterior
        ) * 100

    return {
        "disponible": True,
        "tipo": tipo,
        "actual": reciente,
        "anterior": anterior,
        "promedio_actual": promedio_diario_actual,
        "promedio_anterior": promedio_diario_anterior,
        "diferencia_diaria": diferencia_diaria,
        "porcentaje": porcentaje,
        "hora_mayor_aumento": hora_mayor_aumento,
        "cambio_hora": cambio_hora,
        "nocturno_actual": nocturno_actual,
        "nocturno_anterior": nocturno_anterior
    }


def responder_variacion(cliente_id, tipo="semana"):

    datos = analizar_variacion(cliente_id, tipo)

    if not datos["disponible"]:
        return datos["mensaje"]

    actual = datos["actual"]
    anterior = datos["anterior"]

    def rango(periodo):
        from datetime import timedelta

        ultimo = periodo["fin"] - timedelta(days=1)

        return (
            f"{periodo['inicio']:%d/%m/%Y} "
            f"al {ultimo:%d/%m/%Y}"
        )

    respuesta = (
        "¡Claro! 💧 Revisemos qué muestran "
        "tus mediciones.\n\n"
        f"**Período reciente:** {rango(actual)}\n"
        f"**Período de referencia:** "
        f"{rango(anterior)}\n\n"
        f"- Promedio diario reciente: "
        f"{formato_litros(datos['promedio_actual'])} L.\n"
        f"- Promedio diario anterior: "
        f"{formato_litros(datos['promedio_anterior'])} L.\n"
    )

    diferencia = datos["diferencia_diaria"]

    if diferencia > 0:
        respuesta += (
            "\nTu consumo promedio diario aumentó "
            f"{formato_litros(diferencia)} litros."
        )
    elif diferencia < 0:
        respuesta += (
            "\nTu consumo promedio diario disminuyó "
            f"{formato_litros(abs(diferencia))} litros."
        )
    else:
        respuesta += (
            "\nTu consumo promedio diario "
            "se mantuvo igual."
        )

    if datos["porcentaje"] is not None:
        respuesta += (
            f" La variación fue de "
            f"{datos['porcentaje']:+.1f}%."
        )

    if datos["cambio_hora"] > 0:
        respuesta += (
            "\n\n**Horario destacado:** el mayor "
            "aumento del promedio por franja horaria "
            "se registró entre las "
            f"{datos['hora_mayor_aumento']:02d}:00 "
            "y la hora siguiente."
        )

    if (
        datos["nocturno_actual"]
        > datos["nocturno_anterior"]
    ):
        respuesta += (
            "\n\nTambién se observó un aumento "
            "del consumo nocturno promedio."
        )

    if anterior["fin"] != actual["inicio"]:
        respuesta += (
            "\n\nLos períodos comparados no son "
            "consecutivos, porque se seleccionaron "
            "los últimos con mediciones completas."
        )

    respuesta += (
        "\n\nEstos resultados ayudan a identificar "
        "cuándo cambió el consumo, pero no demuestran "
        "la causa del cambio. Factores como un mayor "
        "uso de agua o una posible fuga requieren "
        "información adicional.\n\n"
    )

    return respuesta


if __name__ == "__main__":

    for cliente_id in [1, 3, 8]:

        print(f"\n--- CLIENTE {cliente_id} ---")

        print(responder_variacion(
            cliente_id,
            "semana"
        ))
