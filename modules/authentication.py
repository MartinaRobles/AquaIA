
import secrets
import hmac
from datetime import datetime, timedelta, timezone


# Configuración para el prototipo
DURACION_MINUTOS = 5
MAX_INTENTOS = 3


def crear_desafio(cliente_id):
    """
    Genera un código temporal para un cliente ficticio.
    No envía SMS ni correos electrónicos.
    """

    codigo = f"{secrets.randbelow(1000000):06d}"

    desafio = {
        "cliente_id": cliente_id,
        "codigo": codigo,
        "expira": datetime.now(timezone.utc)
                  + timedelta(minutes=DURACION_MINUTOS),
        "intentos_restantes": MAX_INTENTOS,
        "utilizado": False
    }

    return desafio


def verificar_codigo(desafio, cliente_id, codigo_ingresado):
    """
    Verifica que el código corresponda al cliente,
    no haya expirado y no se haya utilizado.
    """

    if desafio["utilizado"]:
        return False

    if desafio["intentos_restantes"] <= 0:
        return False

    if datetime.now(timezone.utc) > desafio["expira"]:
        return False

    if desafio["cliente_id"] != cliente_id:
        return False

    valido = hmac.compare_digest(
        desafio["codigo"],
        str(codigo_ingresado)
    )

    if valido:
        desafio["utilizado"] = True
        return True

    desafio["intentos_restantes"] -= 1

    return False


# -------------------------------------------
# PRUEBA LOCAL
# -------------------------------------------

if __name__ == "__main__":

    cliente_id = 3

    desafio = crear_desafio(cliente_id)

    print("\n--- AUTENTICACIÓN AQUAIA ---")
    print("Cliente ficticio:", cliente_id)

    # Solo para desarrollo local.
    print("Código de prueba:", desafio["codigo"])

    codigo_usuario = input(
        "\nIngresa el código de verificación: "
    ).strip()

    resultado = verificar_codigo(
        desafio,
        cliente_id,
        codigo_usuario
    )

    if resultado:
        print("\nVerificación correcta.")
        print("Cliente autenticado en esta prueba.")
    else:
        print("\nCódigo incorrecto o expirado.")
