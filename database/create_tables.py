
import sqlite3
from pathlib import Path

# Ubicación de la base de datos
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "aquaia.db"

def create_database():
    """
    Creates the AquaIA SQLite database and all required tables if they do not exist.
    This function establishes a connection to the database file, enables foreign key support,
    and creates tables for clients, accounts, invoices, consumption records, requests,
    company knowledge, and request history.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    # 1. Clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        correo TEXT,
        telefono TEXT,
        direccion TEXT,
        sector TEXT,
        estado TEXT DEFAULT 'activo'
    )
    """)

    # 2. Cuentas de suministro
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        numero_cuenta TEXT UNIQUE NOT NULL,
        estado TEXT DEFAULT 'activa',
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    )
    """)

    # 3. Facturas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cuenta_id INTEGER NOT NULL,
        periodo TEXT NOT NULL,
        monto REAL NOT NULL,
        vencimiento DATE,
        estado TEXT NOT NULL,
        FOREIGN KEY (cuenta_id) REFERENCES cuentas(id)
    )
    """)

    # 4. Consumos horarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consumos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cuenta_id INTEGER NOT NULL,
        fecha_hora DATETIME NOT NULL,
        litros REAL NOT NULL,
        FOREIGN KEY (cuenta_id) REFERENCES cuentas(id),
        UNIQUE (cuenta_id, fecha_hora)
    )
    """)

    # 5. Quejas, reclamos y reportes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solicitudes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        tipo TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        ubicacion TEXT,
        contacto TEXT,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        estado TEXT DEFAULT 'pendiente',
        prioridad TEXT DEFAULT 'normal',
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    )
    """)

    # 6. Información institucional
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conocimiento_empresa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        categoria TEXT,
        contenido TEXT NOT NULL,
        fuente TEXT,
        fecha_publicacion DATE,
        fecha_actualizacion DATE,
        verificado INTEGER DEFAULT 0
    )
    """)

    # 7. Historial de solicitudes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historial_solicitudes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        solicitud_id INTEGER NOT NULL,
        estado_anterior TEXT,
        estado_nuevo TEXT NOT NULL,
        observacion TEXT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (solicitud_id) REFERENCES solicitudes(id)
    )
    """)

    connection.commit()
    connection.close()

    print("Base de datos AquaIA creada correctamente.")

if __name__ == "__main__":
    create_database()
