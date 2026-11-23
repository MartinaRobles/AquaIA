
import sqlite3
import random
from pathlib import Path
from datetime import datetime, date, timedelta


# --------------------------------------------------
# 1. CONFIGURACIÓN
# --------------------------------------------------

DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "database"
    / "aquaia.db"
)

random.seed(42)


# --------------------------------------------------
# 2. CLIENTES FICTICIOS
# --------------------------------------------------

CLIENTES = [
    ("Cliente Demo 01", "cliente01@example.com", "+56900000001", "Calle Ficticia 101", "Norte"),
    ("Cliente Demo 02", "cliente02@example.com", "+56900000002", "Calle Ficticia 102", "Norte"),
    ("Cliente Demo 03", "cliente03@example.com", "+56900000003", "Calle Ficticia 103", "Centro"),
    ("Cliente Demo 04", "cliente04@example.com", "+56900000004", "Calle Ficticia 104", "Centro"),
    ("Cliente Demo 05", "cliente05@example.com", "+56900000005", "Calle Ficticia 105", "Sur"),
    ("Cliente Demo 06", "cliente06@example.com", "+56900000006", "Calle Ficticia 106", "Sur"),
    ("Cliente Demo 07", "cliente07@example.com", "+56900000007", "Calle Ficticia 107", "Norte"),
    ("Cliente Demo 08", "cliente08@example.com", "+56900000008", "Calle Ficticia 108", "Centro"),
    ("Cliente Demo 09", "cliente09@example.com", "+56900000009", "Calle Ficticia 109", "Sur"),
    ("Cliente Demo 10", "cliente10@example.com", "+56900000010", "Calle Ficticia 110", "Norte"),
]


# --------------------------------------------------
# 3. FUNCIÓN PARA CALCULAR MESES
# --------------------------------------------------

def obtener_mes(fecha, desplazamiento):
    indice = fecha.year * 12 + fecha.month - 1 + desplazamiento
    anio = indice // 12
    mes = indice % 12 + 1

    return date(anio, mes, 1)


# --------------------------------------------------
# 4. GENERAR CONSUMOS HORARIOS
# --------------------------------------------------

def generar_consumos(cursor, cuenta_id, numero_cliente):

    hora_actual = datetime.now().replace(
        minute=0,
        second=0,
        microsecond=0
    )

    primera_hora = hora_actual - timedelta(hours=167)

    # Los clientes 03 y 08 tendrán un patrón nocturno anormal.
    posible_anomalia = numero_cliente in (3, 8)

    for i in range(168):

        fecha_hora = primera_hora + timedelta(hours=i)
        hora = fecha_hora.hour

        es_noche = hora <= 5 or hora >= 23
        es_hora_punta = (
            6 <= hora <= 9 or
            18 <= hora <= 22
        )

        if posible_anomalia and es_noche:
            # Consumo nocturno elevado y constante.
            litros = random.uniform(18, 27)

        elif es_noche:
            # Consumo nocturno normal.
            litros = random.uniform(1.5, 4.5)

        elif es_hora_punta:
            # Mayor consumo durante la mañana y la tarde.
            litros = random.uniform(15, 28)

        else:
            # Consumo durante el resto del día.
            litros = random.uniform(5, 14)

        cursor.execute(
            """
            INSERT INTO consumos
            (cuenta_id, fecha_hora, litros)
            VALUES (?, ?, ?)
            """,
            (
                cuenta_id,
                fecha_hora.strftime("%Y-%m-%d %H:%M:%S"),
                round(litros)
            )
        )


# --------------------------------------------------
# 5. CREAR TODOS LOS DATOS
# --------------------------------------------------

def crear_datos():

    if not DB_PATH.exists():
        print("No se encontró la base de datos.")
        return

    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON")
    cursor = conexion.cursor()

    try:

        # Evitamos insertar los datos dos veces.
        cantidad_clientes = cursor.execute(
            "SELECT COUNT(*) FROM clientes"
        ).fetchone()[0]

        if cantidad_clientes > 0:
            print(
                "La base de datos ya contiene clientes. "
                "No se insertaron nuevos datos."
            )
            return

        fecha_actual = date.today()
        fecha_hora_actual = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        ids_clientes = []

        # CREAR CLIENTES Y SUS CUENTAS
        for numero, cliente in enumerate(CLIENTES, start=1):

            nombre, correo, telefono, direccion, sector = cliente

            cursor.execute(
                """
                INSERT INTO clientes
                (nombre, correo, telefono, direccion, sector, estado)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    nombre,
                    correo,
                    telefono,
                    direccion,
                    sector,
                    "activo"
                )
            )

            cliente_id = cursor.lastrowid
            ids_clientes.append(cliente_id)

            numero_cuenta = f"AQA-{numero:04d}"

            cursor.execute(
                """
                INSERT INTO cuentas
                (cliente_id, numero_cuenta, estado)
                VALUES (?, ?, ?)
                """,
                (cliente_id, numero_cuenta, "activa")
            )

            cuenta_id = cursor.lastrowid

            # CREAR DOS FACTURAS POR CUENTA
            for desplazamiento in (-1, 0):

                mes = obtener_mes(fecha_actual, desplazamiento)
                mes_vencimiento = obtener_mes(
                    fecha_actual,
                    desplazamiento + 1
                )

                periodo = mes.strftime("%Y-%m")
                vencimiento = mes_vencimiento.replace(day=15)

                monto = random.randint(18000, 65000)

                if desplazamiento == -1:
                    estado = (
                        "pagada" if numero % 3 != 0
                        else "vencida"
                    )
                else:
                    estado = "pendiente"

                cursor.execute(
                    """
                    INSERT INTO facturas
                    (cuenta_id, periodo, monto, vencimiento, estado)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        cuenta_id,
                        periodo,
                        monto,
                        vencimiento.isoformat(),
                        estado
                    )
                )

            # CREAR 168 REGISTROS HORARIOS
            generar_consumos(cursor, cuenta_id, numero)

        # CREAR SOLICITUDES FICTICIAS

        solicitudes = [
            (
                ids_clientes[2],
                "baja_presion",
                "El cliente informa presión de agua menor a la habitual.",
                "Sector Centro, ubicación ficticia.",
                "+56900000003",
                "recibida",
                "media"
            ),
            (
                None,
                "fuga_via_publica",
                "Se observa agua saliendo continuamente desde la vía pública.",
                "Sector Norte, esquina ficticia.",
                None,
                "recibida",
                "alta"
            ),
            (
                ids_clientes[7],
                "consulta_facturacion",
                "El cliente solicita revisar su última factura.",
                "Calle Ficticia 108, Sector Centro",
                "+56900000008",
                "recibida",
                "baja"
            )
        ]

        for solicitud in solicitudes:

            cursor.execute(
                """
                INSERT INTO solicitudes
                (
                    cliente_id,
                    tipo,
                    descripcion,
                    ubicacion,
                    contacto,
                    fecha_creacion,
                    estado,
                    prioridad
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    solicitud[0],
                    solicitud[1],
                    solicitud[2],
                    solicitud[3],
                    solicitud[4],
                    fecha_hora_actual,
                    solicitud[5],
                    solicitud[6]
                )
            )

        conexion.commit()

        print("¡Datos simulados creados correctamente!")

        print("Clientes:", cursor.execute(
            "SELECT COUNT(*) FROM clientes"
        ).fetchone()[0])

        print("Cuentas:", cursor.execute(
            "SELECT COUNT(*) FROM cuentas"
        ).fetchone()[0])

        print("Facturas:", cursor.execute(
            "SELECT COUNT(*) FROM facturas"
        ).fetchone()[0])

        print("Registros horarios:", cursor.execute(
            "SELECT COUNT(*) FROM consumos"
        ).fetchone()[0])

        print("Solicitudes:", cursor.execute(
            "SELECT COUNT(*) FROM solicitudes"
        ).fetchone()[0])

    except sqlite3.Error as error:
        conexion.rollback()
        print("Error al crear los datos:", error)

    finally:
        conexion.close()


# --------------------------------------------------
# 6. EJECUTAR EL PROGRAMA
# --------------------------------------------------

if __name__ == "__main__":
    crear_datos()
