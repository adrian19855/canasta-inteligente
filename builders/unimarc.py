import json
import re
import urllib.parse
from datetime import date, datetime
from builders.base import crear_solicitud_estandar, generar_id_request

class UnimarcBuilder:
    """
    Builder Oficial para Producción - Unimarc (SMU Chile).
    Extrae el catálogo 100% en vivo desde la API de búsqueda sin catálogos hardcodeados.
    """
    def __init__(self):
        self.cadena = "unimarc"
        self.headers_api = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "es-CL,es;q=0.9",
            "Referer": "https://www.unimarc.cl/"
        }

    def generar_solicitudes(self, terminos: list, sucursal: dict = None) -> list:
        sucursal = sucursal or {"region": "Metropolitana", "comuna": "Santiago", "local": "Online RM"}
        solicitudes = []
        for termino in terminos:
            termino_encoded = urllib.parse.quote_plus(termino)
            url_oficial = f"https://www.unimarc.cl/api/search?type=search&value={termino_encoded}"
            
            req = crear_solicitud_estandar(
                cadena=self.cadena,
                sku_producto=termino,
                nombre_canasta=termino,
                url=url_oficial,
                region=sucursal["region"],
                comuna=sucursal["comuna"],
                headers_custom=self.headers_api
            )
            solicitudes.append(req)
            
        return solicitudes

    def parsear(self, raw_payload: str, termino: str, sucursal: dict = None) -> list:
        sucursal = sucursal or {"region": "Metropolitana", "comuna": "Santiago", "local": "Online RM"}
        productos_capturados = []
        nombres_vistos = set()
        palabra_clave = termino.split()[0].lower()

        def agregar_prod(nombre, sku=None):
            n_limpio = re.sub(r'\s+', ' ', str(nombre)).strip()
            if n_limpio and len(n_limpio) > 4 and n_limpio.lower() not in nombres_vistos:
                nombres_vistos.add(n_limpio.lower())
                sku_str = str(sku) if sku else f"UNI-{len(productos_capturados)+1}"
                productos_capturados.append({"nombre": n_limpio, "sku": sku_str})

        # Parseo 100% REAL en vivo desde el JSON de Unimarc
        if raw_payload:
            try:
                data = json.loads(raw_payload)
                def buscar_en_nodo(obj):
                    if isinstance(obj, dict):
                        nombre = obj.get("productName") or obj.get("name") or obj.get("title")
                        sku = obj.get("productId") or obj.get("sku") or obj.get("id")
                        if nombre and isinstance(nombre, str) and palabra_clave in nombre.lower():
                            agregar_prod(nombre, sku)
                        for valor in obj.values():
                            buscar_en_nodo(valor)
                    elif isinstance(obj, list):
                        for elem in obj:
                            buscar_en_nodo(elem)
                buscar_en_nodo(data)
            except Exception:
                pass

        # Estandarización estricta al formato del Lakehouse
        filas_tabla = []
        for prod in productos_capturados:
            filas_tabla.append({
                "id_request": generar_id_request("unimarc", f"{termino}_{prod['sku']}", sucursal["region"], sucursal["comuna"]),
                "cadena": "unimarc",
                "sku_producto": str(prod["sku"]),
                "nombre_canasta": termino,
                "nombre_detectado": prod["nombre"][:100],
                "nombre_local": sucursal["local"],
                "region": sucursal["region"],
                "comuna": sucursal["comuna"],
                "fecha_carga": date.today().isoformat(),
                "timestamp_proceso": datetime.now().isoformat()
            })
            
        return filas_tabla