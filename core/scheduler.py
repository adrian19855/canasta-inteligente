from itertools import zip_longest
from typing import List, Dict

class RoundRobinScheduler:
    """
    Divide las peticiones en bloques y las intercala entre supermercados
    para evitar ráfagas continuas hacia un mismo dominio (WAF protection).
    """
    def __init__(self, tamano_bloque: int = 50):
        self.tamano_bloque = tamano_bloque

    def _dividir_en_bloques(self, lista: List[dict]) -> List[List[dict]]:
        return [
            lista[i : i + self.tamano_bloque]
            for i in range(0, len(lista), self.tamano_bloque)
        ]

    def crear_cola_intercalada(self, peticiones_por_cadena: Dict[str, List[dict]]) -> List[dict]:
        bloques_por_cadena = []
        for cadena, peticiones in peticiones_por_cadena.items():
            if peticiones:
                bloques = self._dividir_en_bloques(peticiones)
                bloques_por_cadena.append(bloques)
                print(f"🧩 [SCHEDULER] {cadena.upper()}: {len(peticiones)} peticiones -> {len(bloques)} bloque(s) de {self.tamano_bloque}.")

        cola_final = []
        for ronda in zip_longest(*bloques_por_cadena):
            for bloque in ronda:
                if bloque is not None:
                    cola_final.append(bloque)

        print(f"🚀 [SCHEDULER] Cola Round-Robin generada con {len(cola_final)} turnos intercalados.")
        return cola_final