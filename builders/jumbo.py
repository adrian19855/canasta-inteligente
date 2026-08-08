import json
import re
import html
from datetime import date, datetime
from builders.base import crear_solicitud_estandar, generar_id_request

def extraer_precio_definitivo(item):
    """
    1. Busca en las rutas de VTEX Moderno (Intelligent Search / priceRange) y VTEX Clásico.
    2. Si cambia la API, escasea recursivamente el JSON hasta encontrar un precio chileno real (>= 100 CLP).
    """
    # --- INTENTO 1: Rutas modernas de VTEX Intelligent Search ---
    try:
        price_range = item.get("priceRange", {})
        for sub_key in ["sellingPrice", "listPrice"]:
            p_obj = price_range.get(sub_key, {})
            for k in ["lowPrice", "highPrice", "price"]:
                val = p_obj.get(k)
                if val and isinstance(val, (int, float)) and val >= 100:
                    return int(val)

        # --- INTENTO 2: Rutas clásicas VTEX (items -> sellers -> commertialOffer) ---
        items = item.get("items", []) if isinstance(item.get("items"), list) else []
        for sub in items:
            for seller in sub.get("sellers", []):
                oferta = seller.get("commertialOffer") or seller.get("commercialOffer") or {}
                for key in ["Price", "spotPrice", "PriceWithoutDiscount", "ListPrice"]:
                    val = oferta.get(key)
                    if val and isinstance(val, (int, float)) and val >= 100:
                        return int(val)

        # --- INTENTO 3: Búsqueda directa en raíz ---
        for key in ["Price", "bestPrice", "precio", "price", "sellingPrice", "lowPrice"]:
            val = item.get(key)
            if val and isinstance(val, (int, float)) and val >= 100:
                return int(val)
    except Exception:
        pass

    # --- INTENTO 4 (INFALIBLE): Escáner recursivo por todo el diccionario ---
    precios_encontrados = []
    def _escanear(nodo):
        if isinstance(nodo, dict):
            for k, v in nodo.items():
                key_lower = k.lower()
                # Si la llave dice "price" o "precio" y no es un rango ni fecha
                if any(p in key_lower for p in ["price", "precio"]) and not any(ignore in key_lower for ignore in ["range", "valid", "date", "unit", "multiplier"]):
                    if isinstance(v, (int, float)) and v >= 100:
                        precios_encontrados.append(int(v))
                elif isinstance(v, (dict, list)):
                    _escanear(v)
        elif isinstance(nodo, list):
            for elem in nodo:
                _escanear(elem)

    _escanear(item)
    return precios_encontrados[0] if precios_encontrados else 0

class JumboBuilder:
    def __init__(self):
        self.cadena = "jumbo"
        self.headers_jumbo = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9",
            "Referer": "https://www.jumbo.cl/"
        }

    def generar_solicitudes(self, terminos: list, sucursal: dict = None) -> list:
        solicitudes = []
        for termino in terminos:
            termino_url = termino.replace(" ", "%20")
            # Usamos la URL pública de búsqueda de Jumbo
            url_oficial = f"https://www.jumbo.cl/busqueda?ft={termino_url}"
            
            req = crear_solicitud_estandar(
                cadena=self.cadena,
                sku_producto=termino,
                nombre_canasta=termino,
                url=url_oficial,
                region=sucursal["region"],
                comuna=sucursal["comuna"],
                headers_custom=self.headers_jumbo
            )
            solicitudes.append(req)
        return solicitudes

    def parsear(self, raw_payload: str, termino: str, sucursal: dict = None) -> list:
        sucursal = sucursal or {"region": "Metropolitana", "comuna": "Santiago", "local": "Online RM"}
        html_content = html.unescape(raw_payload)
        productos = []

        # 1. Extracción desde JSON-LD (Lo que vimos en tu código fuente)
        scripts_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html_content, re.DOTALL | re.IGNORECASE)
        for bloque in scripts_ld:
            try:
                data = json.loads(bloque.strip())
                # Jumbo pone la lista de productos en ItemList -> itemListElement
                if isinstance(data, dict) and "itemListElement" in data:
                    for item in data["itemListElement"]:
                        # item['item'] contiene la info del producto
                        if "item" in item:
                            productos.append(item["item"])
            except Exception:
                pass

        # 2. Estandarización al contrato
        filas = []
        for idx, item in enumerate(productos, 1):
            nombre = str(item.get("name", f"Producto Jumbo {idx}"))
            sku = str(item.get("sku", idx))
            
            filas.append({
                "id_request": generar_id_request("jumbo", f"{termino}_{sku}", sucursal["region"], sucursal["comuna"]),
                "cadena": "jumbo",
                "sku_producto": sku,
                "nombre_canasta": termino,
                "nombre_detectado": nombre[:100],
                "precio": extraer_precio_definitivo(item),
                "nombre_local": sucursal["local"],
                "region": sucursal["region"],
                "comuna": sucursal["comuna"],
                "fecha_carga": date.today().isoformat(),
                "timestamp_proceso": datetime.now().isoformat()
            })
        return filas