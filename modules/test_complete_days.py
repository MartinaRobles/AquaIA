
from modules.daily_consumption import (
    comparar_ultimos_dias_completos
)


if __name__ == "__main__":

    for cliente_id in [1, 3, 8]:

        print(
            f"\n--- CLIENTE {cliente_id} ---"
        )

        resultado = comparar_ultimos_dias_completos(
            cliente_id
        )

        print(resultado)
