
from database.connection import get_connection


def revisar_registros(cliente_id=3):

    conexion = get_connection()

    try:
        consulta = """
            SELECT
                DATE(co.fecha_hora) AS fecha,
                COUNT(*) AS cantidad,
                MIN(co.fecha_hora) AS primera_hora,
                MAX(co.fecha_hora) AS ultima_hora,
                SUM(co.litros) AS total_litros
            FROM consumos AS co
            JOIN cuentas AS cu
                ON co.cuenta_id = cu.id
            WHERE cu.cliente_id = ?
            GROUP BY DATE(co.fecha_hora)
            ORDER BY fecha DESC
        """

        resultados = conexion.execute(
            consulta,
            (cliente_id,)
        ).fetchall()

        print(
            f"\n--- REGISTROS DEL CLIENTE {cliente_id} ---\n"
        )

        for fila in resultados:

            print(f"Fecha: {fila['fecha']}")
            print(f"Registros: {fila['cantidad']} de 24")
            print(f"Primera hora: {fila['primera_hora']}")
            print(f"Última hora: {fila['ultima_hora']}")

            if fila["cantidad"] == 24:
                print("Estado: día completo")
            else:
                print("Estado: día incompleto")

            print("-" * 40)

    finally:
        conexion.close()


if __name__ == "__main__":
    revisar_registros(cliente_id=3)
