import hashlib
import pandas as pd
from typing import List, Dict

def generar_id_request(cadena: str, sku: str, region: str, comuna: str) -> str:
    """
    Genera un ID único hash (MD5) para deduplicación rápida en el State Manager.
    Ejemplo: 'jumbo_102938_rm_santiago' -> hash
    """
    llave_cruda = f"{cadena.lower()}_{sku}_{region.lower()}_{comuna.lower()}"
    return hashlib.md5(llave_cruda.encode("utf-8")).hexdigest()

def crear_solicitud_estandar(
    cadena: str,
    sku_producto: str,
    nombre_canasta: str,
    url: str,
    region: str = "RM",
    comuna: str = "Santiago",
    headers_custom: dict = None
) -> Dict:
    """
    Obliga a todos los supermercados a respetar el Contrato de Datos de 7 campos.
    """
    if headers_custom is None:
        headers_custom = {}

    id_req = generar_id_request(cadena, sku_producto, region, comuna)

    return {
        "id_request": id_req,
        "cadena": cadena.lower(),
        "sku_producto": str(sku_producto),
        "nombre_canasta": nombre_canasta,
        "url": url,
        "headers_custom": headers_custom,
        "metadata_geo": {
            "region": region,
            "comuna": comuna
        }
    }

def convertir_a_dataframe(lista_solicitudes: List[Dict]) -> pd.DataFrame:
    """Convierte la lista estandarizada en un DataFrame listo para el Anti-Join."""
    if not lista_solicitudes:
        return pd.DataFrame()
    return pd.DataFrame(lista_solicitudes)