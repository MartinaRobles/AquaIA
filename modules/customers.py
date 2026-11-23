
from database.connection import get_connection


def listar_clientes():
    """
    Recupera todos los clientes registrados.
    """

    conexion = get_connection()

    try:
        consulta = """
            SELECT
                id,
                nombre,
                correo,
                telefono,
                direccion,
                sector,
                estado
            FROM clientes
            ORDER BY nombre
        """

        resultados = conexion.execute(consulta).fetchall()

        # Convertimos los resultados en una lista de diccionarios.
        return [dict(fila) for fila in resultados]

    finally:
        conexion.close()


def obtener_cliente_por_id(cliente_id):
    """
    Busca un cliente utilizando su identificador.
    """

    conexion = get_connection()

    try:
        consulta = """
            SELECT *
            FROM clientes
            WHERE id = ?
        """

        resultado = conexion.execute(
            consulta,
            (cliente_id,)
        ).fetchone()

        if resultado is None:
            return None

        return dict(resultado)

    finally:
        conexion.close()


# Permite probar este módulo directamente.
if __name__ == "__main__":

    clientes = listar_clientes()

    print("\n--- CLIENTES REGISTRADOS EN AQUAIA ---\n")

    if not clientes:
        print("No hay clientes registrados.")

    else:
        for cliente in clientes:
            print(
                f"ID: {cliente['id']} | "
                f"Nombre: {cliente['nombre']} | "
                f"Sector: {cliente['sector']}"
            )

    print(f"\nTotal de clientes: {len(clientes)}")
