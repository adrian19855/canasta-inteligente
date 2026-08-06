from builders.base import crear_solicitud_estandar, convertir_a_dataframe
import pandas as pd

class JumboBuilder:
    def __init__(self):
        self.cadena = "jumbo"
        # Cabeceras que Cencosud suele pedir para responder en JSON
        self.headers_cencosud = {
            "Accept": "application/json",
            "apikey": "WlDftCF3wWMb85z7f0aG0gYc61QGqfN8" # Key pública estándar web
        }

    def generar_matriz(self, productos_canasta: list, sucursales: list) -> pd.DataFrame:
        """
        Recibe:
          - productos_canasta: listado de dicts [{'sku': '123', 'nombre': 'Arroz...'}]
          - sucursales: listado de dicts [{'region': 'RM', 'comuna': 'Santiago'}]
        """
        solicitudes = []

        for prod in productos_canasta:
            for suc in sucursales:
                sku = prod["sku"]
                # URL estándar de búsqueda por SKU en API de Cencosud
                url_api = f"https://sm-api.cencosud.com/catalog/api/v1/products/{sku}"

                req = crear_solicitud_estandar(
                    cadena=self.cadena,
                    sku_producto=sku,
                    nombre_canasta=prod["nombre"],
                    url=url_api,
                    region=suc["region"],
                    comuna=suc["comuna"],
                    headers_custom=self.headers_cencosud
                )
                solicitudes.append(req)

        df_matriz = convertir_a_dataframe(solicitudes)
        print(f"🏗️ [BUILDER - JUMBO] Matriz generada con {len(df_matriz)} solicitudes.")
        return df_matriz