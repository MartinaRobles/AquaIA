
from database.connection import get_connection
from datetime import datetime


# ----------------------------------------
# 1. OBTENER CONSUMOS DE UN CLIENTE
# ----------------------------------------

def obtener_consumos_cliente(cliente_id):

    conexion = get_connection()

    try:
        consulta = """
            SELECT
                co.fecha_hora,
                co.litros,
                cu.numero_cuenta
            FROM consumos AS co
            JOIN cuentas AS cu
                ON co.cuenta_id = cu.id
            WHERE cu.cliente_id = ?
            ORDER BY co.fecha_hora
        """

        resultados = conexion.execute(
            consulta,
            (cliente_id,)
        ).fetchall()

        return [dict(fila) for fila in resultados]

    finally:
        conexion.close()


# ----------------------------------------
# 2. ANALIZAR CONSUMO
# ----------------------------------------

def analizar_consumo(cliente_id):

    consumos = obtener_consumos_cliente(cliente_id)

    if not consumos:
        return None

    total_litros = sum(
        consumo["litros"]
        for consumo in consumos
    )

    promedio_horario = total_litros / len(consumos)

    mayor_consumo = max(
        consumos,
        key=lambda consumo: consumo["litros"]
    )

    return {
        "cliente_id": cliente_id,
        "total_litros": round(total_litros, 2),
        "promedio_horario": round(promedio_horario, 2),
        "hora_mayor_consumo": mayor_consumo["fecha_hora"],
        "litros_maximos": mayor_consumo["litros"],
        "registros": len(consumos)
    }


# ----------------------------------------
# 3. ANALIZAR CONSUMO NOCTURNO
# ----------------------------------------

def detectar_consumo_nocturno(cliente_id):

    consumos = obtener_consumos_cliente(cliente_id)

    if not consumos:
        return None

    registros_nocturnos = []

    for consumo in consumos:

        fecha = datetime.strptime(
            consumo["fecha_hora"],
            "%Y-%m-%d %H:%M:%S"
        )

        # Analizaremos de 00:00 a 05:59.
        if 0 <= fecha.hour < 6:
            registros_nocturnos.append(consumo)

    if not registros_nocturnos:
        return None

    promedio_nocturno = sum(
        registro["litros"]
        for registro in registros_nocturnos
    ) / len(registros_nocturnos)

    # Umbral experimental para los datos simulados.
    umbral = 15

    posible_anomalia = promedio_nocturno > umbral

    return {
        "cliente_id": cliente_id,
        "promedio_nocturno": round(promedio_nocturno, 2),
        "posible_anomalia": posible_anomalia,
        "registros_analizados": len(registros_nocturnos)
    }


# ----------------------------------------
# 4. EJECUTAR PRUEBAS
# ----------------------------------------

if __name__ == "__main__":

    for cliente_id in [1, 3, 8]:

        print(
            f"\n--- ANÁLISIS DEL CLIENTE {cliente_id} ---"
        )

        analisis = analizar_consumo(cliente_id)

        nocturno = detectar_consumo_nocturno(cliente_id)

        if analisis:

            print(
                f"Consumo total: "
                f"{analisis['total_litros']} litros"
            )

            print(
                f"Promedio horario: "
                f"{analisis['promedio_horario']} litros"
            )

            print(
                f"Mayor consumo: "
                f"{analisis['litros_maximos']} litros"
            )

            print(
                f"Fecha y hora: "
                f"{analisis['hora_mayor_consumo']}"
            )

        if nocturno:

            print(
                f"Promedio nocturno: "
                f"{nocturno['promedio_nocturno']} litros"
            )

            if nocturno["posible_anomalia"]:
                print(
                    "ALERTA: posible consumo nocturno anormal."
                )
            else:
                print(
                    "Consumo nocturno dentro del rango "
                    "esperado para esta simulación."
                )
