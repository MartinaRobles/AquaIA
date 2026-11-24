
import calendar
from datetime import date, timedelta

from database.connection import get_connection


def mes_anterior(inicio_mes):
    """Devuelve el primer día del mes anterior."""
    return (inicio_mes - timedelta(days=1)).replace(day=1)


def fin_mes(inicio_mes):
    """Devuelve el primer día del mes siguiente."""
    anio = inicio_mes.year
    mes = inicio_mes.month

    if mes == 12:
        return date(anio + 1, 1, 1)

    return date(anio, mes + 1, 1)


def formato_litros(valor):
    return f"{valor:,.1f}".replace(
        ",", "X"
    ).replace(".", ",").replace("X", ".")


def obtener_ultima_fecha(cliente_id):
    conexion = get_connection()

    try:
        fila = conexion.execute(
            """
            SELECT MAX(co.fecha_hora) AS ultima
            FROM consumos AS co
            JOIN cuentas AS cu
                ON co.cuenta_id = cu.id
            WHERE cu.cliente_id = ?
            """,
            (cliente_id,)
        ).fetchone()

        if fila["ultima"] is None:
            return None

        return date.fromisoformat(
            fila["ultima"][:10]
        )

    finally:
        conexion.close()


def consultar_periodo(cliente_id, inicio, fin):
    """
    Calcula el consumo de un período.

    fin es exclusivo.
    Valida 24 horas por día y por cuenta.
    """

    conexion = get_connection()

    try:
        cuentas = conexion.execute(
            """
            SELECT id
            FROM cuentas
            WHERE cliente_id = ?
            """,
            (cliente_id,)
        ).fetchall()

        ids_cuentas = {fila["id"] for fila in cuentas}

        if not ids_cuentas:
            return None

        filas = conexion.execute(
            """
            SELECT
                co.cuenta_id,
                DATE(co.fecha_hora) AS fecha,
                COUNT(*) AS cantidad,
                COUNT(DISTINCT SUBSTR(
                    co.fecha_hora, 12, 2
                )) AS horas,
                SUM(co.litros) AS total
            FROM consumos AS co
            JOIN cuentas AS cu
                ON co.cuenta_id = cu.id
            WHERE cu.cliente_id = ?
              AND co.fecha_hora >= ?
              AND co.fecha_hora < ?
            GROUP BY co.cuenta_id, DATE(co.fecha_hora)
            """,
            (
                cliente_id,
                inicio.isoformat() + " 00:00:00",
                fin.isoformat() + " 00:00:00"
            )
        ).fetchall()

        registros = {
            (fila["cuenta_id"], fila["fecha"]): fila
            for fila in filas
        }

        total = 0.0
        dia = inicio

        while dia < fin:

            for cuenta_id in ids_cuentas:
                fila = registros.get(
                    (cuenta_id, dia.isoformat())
                )

                if (
                    fila is None
                    or fila["cantidad"] != 24
                    or fila["horas"] != 24
                ):
                    return None

                total += float(fila["total"])

            dia += timedelta(days=1)

        return round(total, 2)

    finally:
        conexion.close()


def obtener_periodos(cliente_id, tipo):
    """
    Busca los dos períodos calendario completos
    más recientes disponibles.

    Excluye la semana o mes que contiene la
    última medición, pues podría estar incompleto.
    """

    ultima = obtener_ultima_fecha(cliente_id)

    if ultima is None:
        return []

    if tipo == "semana":
        inicio = ultima - timedelta(
            days=ultima.weekday()
        )

    elif tipo == "mes":
        inicio = ultima.replace(day=1)

    else:
        raise ValueError("Tipo de período no válido.")

    encontrados = []

    # Máximo 12 períodos anteriores.
    for _ in range(12):

        if tipo == "semana":
            fin = inicio
            inicio = fin - timedelta(days=7)
        else:
            fin = inicio
            inicio = mes_anterior(fin)

        total = consultar_periodo(
            cliente_id, inicio, fin
        )

        if total is not None:
            encontrados.append({
                "inicio": inicio,
                "fin": fin,
                "litros": total
            })

        if len(encontrados) == 2:
            break

    return encontrados


def responder_comparacion_historica(cliente_id, tipo):

    periodos = obtener_periodos(cliente_id, tipo)

    if len(periodos) < 2:
        return (
            f"No tengo dos períodos completos de "
            f"consumo por {tipo} para compararlos. "
            "Prefiero indicártelo antes que darte "
            "una cifra que podría ser incorrecta."
        )

    reciente, anterior = periodos

    actual = reciente["litros"]
    previo = anterior["litros"]
    diferencia = actual - previo

    etiqueta = (
        "semanas" if tipo == "semana"
        else "meses"
    )

    def rango(p):
        ultimo_dia = p["fin"] - timedelta(days=1)
        return (
            f"{p['inicio'].strftime('%d/%m/%Y')} "
            f"al {ultimo_dia.strftime('%d/%m/%Y')}"
        )

    respuesta = (
        f"¡Claro! 💧 Comparé tus dos {etiqueta} "
        "completos más recientes disponibles.\n\n"
        f"- Período más reciente ({rango(reciente)}): "
        f"**{formato_litros(actual)} litros**.\n"
        f"- Período anterior ({rango(anterior)}): "
        f"**{formato_litros(previo)} litros**.\n"
    )

    if diferencia > 0:
        cambio = "aumentó"
    elif diferencia < 0:
        cambio = "disminuyó"
    else:
        cambio = "se mantuvo igual"

    respuesta += (
        f"\nTu consumo {cambio}. "
        f"La diferencia es de "
        f"{formato_litros(abs(diferencia))} litros."
    )

    if previo > 0:
        porcentaje = abs(diferencia / previo * 100)
        respuesta += (
            f" Esto corresponde a un "
            f"{formato_litros(porcentaje)}%."
        )
    elif actual > 0:
        respuesta += (
            " No se puede calcular un porcentaje "
            "porque el período anterior registró "
            "cero litros."
        )

    if anterior["fin"] != reciente["inicio"]:
        respuesta += (
            "\n\nNota: los períodos seleccionados "
            "no son consecutivos porque no hay "
            "mediciones completas en los intermedios."
        )

    respuesta += (
        "\n\nEstos resultados muestran una variación, "
        "pero no permiten determinar su causa."
    )

    if tipo == "mes":
        respuesta += (
            " Además, los meses pueden tener "
            "diferentes cantidades de días."
        )

    respuesta += (
        "\n\n¿Quieres que revisemos tus horarios "
        "de mayor consumo?"
    )

    return respuesta


if __name__ == "__main__":

    for cliente_id in [1, 3, 8]:
        print(f"\n--- CLIENTE {cliente_id} ---")

        print("\nSEMANAL")
        print(
            responder_comparacion_historica(
                cliente_id, "semana"
            )
        )

        print("\nMENSUAL")
        print(
            responder_comparacion_historica(
                cliente_id, "mes"
            )
        )
