
from database.connection import get_connection


def obtener_facturas_cliente(cliente_id):
    """
    Recupera las facturas asociadas a un cliente.
    """

    conexion = get_connection()

    try:
        consulta = """
            SELECT
                f.id,
                f.periodo,
                f.monto,
                f.vencimiento,
                f.estado,
                c.numero_cuenta
            FROM facturas AS f
            JOIN cuentas AS c
                ON f.cuenta_id = c.id
            WHERE c.cliente_id = ?
            ORDER BY f.periodo DESC
        """

        resultados = conexion.execute(
            consulta,
            (cliente_id,)
        ).fetchall()

        return [dict(fila) for fila in resultados]

    finally:
        conexion.close()


def obtener_deuda_cliente(cliente_id):
    """
    Calcula el total de facturas impagas.
    """

    conexion = get_connection()

    try:
        consulta = """
            SELECT COALESCE(SUM(f.monto), 0)
            FROM facturas AS f
            JOIN cuentas AS c
                ON f.cuenta_id = c.id
            WHERE c.cliente_id = ?
              AND f.estado IN ('pendiente', 'vencida')
        """

        resultado = conexion.execute(
            consulta,
            (cliente_id,)
        ).fetchone()

        return resultado[0]

    finally:
        conexion.close()


if __name__ == "__main__":

    # Cliente ficticio utilizado para la prueba.
    cliente_id = 3

    facturas = obtener_facturas_cliente(cliente_id)
    deuda = obtener_deuda_cliente(cliente_id)

    print(f"\n--- FACTURAS DEL CLIENTE {cliente_id} ---\n")

    if not facturas:
        print("No se encontraron facturas.")

    else:
        for factura in facturas:
            print(
                f"Periodo: {factura['periodo']} | "
                f"Monto: ${factura['monto']:,} | "
                f"Vencimiento: {factura['vencimiento']} | "
                f"Estado: {factura['estado']}"
            )

    print(f"\nTotal de facturas impagas: ${deuda:,}")
