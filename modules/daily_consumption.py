
from datetime import date, datetime, timedelta
from database.connection import get_connection


def obtener_consumo_dia(cliente_id, fecha):
    """
    Consulta el consumo de un cliente
    en una fecha específica.

    Exige 24 registros horarios para
    considerar el día completo.
    """

    if isinstance(fecha, str):
        fecha = date.fromisoformat(fecha)

    inicio = datetime.combine(
        fecha, datetime.min.time()
    )

    fin = inicio + timedelta(days=1)

    conexion = get_connection()

    try:
        resultado = conexion.execute(
            """
            SELECT
                COUNT(*) AS registros,
                COALESCE(SUM(co.litros), 0) AS total
            FROM consumos AS co
            JOIN cuentas AS cu
                ON co.cuenta_id = cu.id
            WHERE cu.cliente_id = ?
              AND co.fecha_hora >= ?
              AND co.fecha_hora < ?
            """,
            (
                cliente_id,
                inicio.strftime("%Y-%m-%d %H:%M:%S"),
                fin.strftime("%Y-%m-%d %H:%M:%S")
            )
        ).fetchone()

        cantidad = resultado["registros"]
        total = float(resultado["total"])

        return {
            "fecha": fecha.isoformat(),
            "litros": round(total, 2),
            "registros": cantidad,
            "completo": cantidad == 24
        }

    finally:
        conexion.close()


def responder_dia(cliente_id, fecha):

    datos = obtener_consumo_dia(cliente_id, fecha)

    if datos["registros"] == 0:
        return (
            f"No tengo mediciones del "
            f"{datos['fecha']} para tu cuenta."
        )

    if not datos["completo"]:
        return (
            f"Para el {datos['fecha']} tengo "
            f"{datos['registros']} registros horarios. "
            "No puedo confirmar el consumo completo "
            "de ese día."
        )

    return (
        f"El {datos['fecha']} registraste "
        f"{datos['litros']:.1f} litros de agua "
        "según las mediciones disponibles."
    )


def comparar_dias(cliente_id, fecha_actual, fecha_anterior):
    """
    Compara dos días completos y calcula
    la variación porcentual.
    """

    actual = obtener_consumo_dia(
        cliente_id, fecha_actual
    )

    anterior = obtener_consumo_dia(
        cliente_id, fecha_anterior
    )

    if not actual["completo"] or not anterior["completo"]:
        return (
            "No puedo comparar ambos días porque "
            "faltan mediciones horarias completas "
            "en al menos uno de los períodos."
        )

    diferencia = actual["litros"] - anterior["litros"]

    if anterior["litros"] == 0:
        if actual["litros"] == 0:
            return (
                "Ambos días registraron cero litros "
                "de consumo."
            )

        return (
            f"El consumo pasó de cero a "
            f"{actual['litros']:.1f} litros. "
            "No es posible calcular un porcentaje "
            "de aumento con una base de cero."
        )

    porcentaje = (
        diferencia / anterior["litros"]
    ) * 100

    if diferencia > 0:
        tendencia = "aumentó"
    elif diferencia < 0:
        tendencia = "disminuyó"
    else:
        tendencia = "se mantuvo igual"

    return (
        f"Comparación del {actual['fecha']} "
        f"con el {anterior['fecha']}:\n\n"
        f"- Consumo más reciente: "
        f"{actual['litros']:.1f} L.\n"
        f"- Consumo anterior: "
        f"{anterior['litros']:.1f} L.\n"
        f"- Diferencia: {diferencia:+.1f} L.\n"
        f"- Variación: {porcentaje:+.1f}%.\n\n"
        f"Tu consumo {tendencia}. "
        "Esta comparación no determina "
        "por sí sola la causa de la variación."
    )


if __name__ == "__main__":

    ayer = date.today() - timedelta(days=1)
    anteayer = date.today() - timedelta(days=2)

    for cliente_id in [1, 3, 8]:

        print(f"\n--- CLIENTE {cliente_id} ---")

        print(responder_dia(cliente_id, ayer))

        print(
            comparar_dias(
                cliente_id,
                ayer,
                anteayer
            )
        )


def comparar_ultimos_dias_completos(cliente_id):
    """
    Busca los últimos dos días completos
    con registros horarios del cliente.
    """

    conexion = get_connection()

    try:
        filas = conexion.execute(
            """
            SELECT
                DATE(co.fecha_hora) AS fecha,
                COUNT(*) AS cantidad,
                COUNT(DISTINCT strftime(
                    '%H', co.fecha_hora
                )) AS horas_distintas
            FROM consumos AS co
            JOIN cuentas AS cu
                ON co.cuenta_id = cu.id
            WHERE cu.cliente_id = ?
            GROUP BY DATE(co.fecha_hora)
            HAVING COUNT(*) = 24
               AND COUNT(DISTINCT strftime(
                   '%H', co.fecha_hora
               )) = 24
            ORDER BY fecha DESC
            LIMIT 2
            """,
            (cliente_id,)
        ).fetchall()

    finally:
        conexion.close()

    if len(filas) < 2:
        return (
            "No tengo dos días completos de "
            "mediciones para realizar la comparación."
        )

    fecha_reciente = date.fromisoformat(
        filas[0]["fecha"]
    )

    fecha_anterior = date.fromisoformat(
        filas[1]["fecha"]
    )

    resultado = comparar_dias(
        cliente_id,
        fecha_reciente,
        fecha_anterior
    )

    # Aclaramos si los días no son consecutivos.
    if (
        fecha_reciente - fecha_anterior
        != timedelta(days=1)
    ):
        resultado += (
            "\n\nNota: estos son los dos días "
            "completos más recientes disponibles. "
            "No son días consecutivos."
        )

    return resultado
