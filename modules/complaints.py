
from database.connection import get_connection
from datetime import datetime


TIPOS_VALIDOS = {
    "baja_presion",
    "corte_suministro",
    "fuga_via_publica",
    "problema_facturacion",
    "reclamo",
    "sugerencia"
}


def registrar_solicitud(
    tipo,
    descripcion,
    ubicacion,
    cliente_id=None,
    contacto=None
):
    """
    Registra una solicitud de prueba en SQLite.
    No envía información a una empresa real.
    """

    if tipo not in TIPOS_VALIDOS:
        raise ValueError(
            "El tipo de solicitud no es válido."
        )

    if not descripcion or not descripcion.strip():
        raise ValueError(
            "Debes ingresar una descripción."
        )

    if not ubicacion or not ubicacion.strip():
        raise ValueError(
            "Debes ingresar una ubicación."
        )

    # Prioridad de demostración.
    prioridad = (
        "alta"
        if tipo in {"fuga_via_publica", "corte_suministro"}
        else "media"
    )

    fecha_actual = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conexion = get_connection()

    try:
        cursor = conexion.execute(
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
                cliente_id,
                tipo,
                descripcion.strip(),
                ubicacion.strip(),
                contacto,
                fecha_actual,
                "recibida",
                prioridad
            )
        )

        conexion.commit()

        return {
            "solicitud_id": cursor.lastrowid,
            "estado": "recibida",
            "prioridad": prioridad,
            "mensaje": (
                "Solicitud registrada en el "
                "prototipo de AquaIA."
            )
        }

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


def consultar_solicitud(solicitud_id):

    conexion = get_connection()

    try:
        resultado = conexion.execute(
            """
            SELECT
                id,
                tipo,
                descripcion,
                ubicacion,
                fecha_creacion,
                estado,
                prioridad
            FROM solicitudes
            WHERE id = ?
            """,
            (solicitud_id,)
        ).fetchone()

        return dict(resultado) if resultado else None

    finally:
        conexion.close()


if __name__ == "__main__":

    resultado = registrar_solicitud(
        tipo="fuga_via_publica",
        descripcion=(
            "Se observa una posible fuga de agua "
            "en la vía pública."
        ),
        ubicacion="Calle Ficticia 150, Sector Norte"
    )

    print("\n--- NUEVA SOLICITUD ---")
    print("ID:", resultado["solicitud_id"])
    print("Estado:", resultado["estado"])
    print("Prioridad:", resultado["prioridad"])
    print("Mensaje:", resultado["mensaje"])

    solicitud = consultar_solicitud(
        resultado["solicitud_id"]
    )

    print("\n--- CONSULTA DE SOLICITUD ---")
    print(solicitud)
