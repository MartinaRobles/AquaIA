
import sqlite3
from pathlib import Path


# Ubicación de nuestra base de datos
DB_PATH = Path(__file__).resolve().parent / "aquaia.db"


def get_connection():
    """
    Crea y devuelve una conexión con la base de datos AquaIA.
    """

    conexion = sqlite3.connect(DB_PATH)

    # Permite acceder a las columnas por su nombre.
    conexion.row_factory = sqlite3.Row

    # Activa la comprobación de relaciones entre tablas.
    conexion.execute("PRAGMA foreign_keys = ON")

    return conexion
