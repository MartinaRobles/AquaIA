
import hashlib
import random
import sqlite3

from datetime import date, datetime, timedelta
from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "database"
    / "aquaia.db"
)

DIAS_HISTORICOS = 90


def generar_litros(cuenta_id, fecha, hora, anomalia):
    """
    Crea consumos reproducibles para una
    cuenta, fecha y hora específicas.
    """

    clave = f"aquaia-demo-{cuenta_id}-{fecha}-{hora}"

    semilla = int.from_bytes(
        hashlib.sha256(clave.encode()).digest()[:8],
        "big"
    )

    generador = random.Random(semilla)

    if anomalia and (hora <= 5 or hora == 23):
        litros = generador.uniform(18, 27)

    elif hora <= 5 or hora == 23:
        litros = generador.uniform(1.5, 4.5)

    elif 6 <= hora <= 9 or 18 <= hora <= 22:
        litros = generador.uniform(15, 28)

    else:
        litros = generador.uniform(5, 14)

    return round(litros)


def generar_historial():

    if not DB_PATH.exists():
        print("No se encontró la base de datos AquaIA.")
        return

    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON")

    try:
        cuentas = conexion.execute(
            """
            SELECT c.id, c.cliente_id,
                   MIN(co.fecha_hora) AS primer_registro
            FROM cuentas AS c
            LEFT JOIN consumos AS co
                ON co.cuenta_id = c.id
            GROUP BY c.id, c.cliente_id
            """
        ).fetchall()

        insertados = 0
        omitidas = 0

        for cuenta_id, cliente_id, primer_registro in cuentas:

            if primer_registro is None:
                print(
                    f"Cuenta {cuenta_id}: "
                    "sin registros iniciales; omitida."
                )
                continue

            # Generamos únicamente fechas ANTERIORES
            # al primer día que ya existe.
            primera_fecha = date.fromisoformat(
                primer_registro[:10]
            )

            inicio = primera_fecha - timedelta(
                days=DIAS_HISTORICOS
            )

            # Clientes Demo 03 y 08 tendrán
            # patrones nocturnos de prueba.
            anomalia = cliente_id in (3, 8)

            for dia in range(DIAS_HISTORICOS):

                fecha = inicio + timedelta(days=dia)

                for hora in range(24):

                    fecha_hora = datetime.combine(
                        fecha,
                        datetime.min.time()
                    ) + timedelta(hours=hora)

                    litros = generar_litros(
                        cuenta_id,
                        fecha.isoformat(),
                        hora,
                        anomalia
                    )

                    cursor = conexion.execute(
                        """
                        INSERT OR IGNORE INTO consumos
                        (cuenta_id, fecha_hora, litros)
                        VALUES (?, ?, ?)
                        """,
                        (
                            cuenta_id,
                            fecha_hora.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            litros
                        )
                    )

                    if cursor.rowcount == 1:
                        insertados += 1
                    else:
                        omitidas += 1

        conexion.commit()

        total = conexion.execute(
            "SELECT COUNT(*) FROM consumos"
        ).fetchone()[0]

        print("\n--- HISTORIAL AQUAIA ---")
        print("Nuevos registros:", insertados)
        print("Registros ya existentes:", omitidas)
        print("Total de registros:", total)
        print("Historial generado correctamente.")

    except sqlite3.Error as error:
        conexion.rollback()
        print("Error en la base de datos:", error)

    finally:
        conexion.close()


if __name__ == "__main__":
    generar_historial()
