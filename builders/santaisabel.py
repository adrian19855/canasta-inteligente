import re
import json
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
class SantaIsabelBuilder:
    """
    Builder Estandarizado para Santa Isabel (Cencosud Chile).
    """
    def __init__(self):
        self.cadena = "santaisabel"
        self.headers_cencosud = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9",
            "Referer": "https://www.santaisabel.cl/"
        }

    def generar_solicitudes(self, terminos: list, sucursal: dict = None) -> list:
        sucursal = sucursal or {"region": "Metropolitana", "comuna": "Santiago", "local": "Online RM"}
        solicitudes = []
        for termino in terminos:
            termino_url = termino.replace(" ", "-")
            url_oficial = f"https://www.santaisabel.cl/busqueda?ft={termino_url}"
            
            req = crear_solicitud_estandar(
                cadena=self.cadena,
                sku_producto=termino,
                nombre_canasta=termino,
                url=url_oficial,
                region=sucursal["region"],
                comuna=sucursal["comuna"],
                headers_custom=self.headers_cencosud
            )
            solicitudes.append(req)
            
        return solicitudes

    def parsear(self, raw_payload: str, termino: str, sucursal: dict = None) -> list:
        sucursal = sucursal or {"region": "Metropolitana", "comuna": "Santiago", "local": "Online RM"}
        html_content = html.unescape(raw_payload)
        productos_capturados = []
        
        # 1. Búsqueda estructurada JSON-LD
        scripts_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html_content, re.DOTALL | re.IGNORECASE)
        
        for bloque in scripts_ld:
            try:
                data = json.loads(bloque.strip())
                if isinstance(data, dict):
                    if data.get("@type") == "ItemList" and "itemListElement" in data:
                        for item in data["itemListElement"]:
                            productos_capturados.append(item)
                    elif data.get("@type") == "Product":
                        productos_capturados.append(data)
            except Exception:
                pass

        # 2. Respaldo textual SSR
        if not productos_capturados:
            palabra_clave = termino.split()[0]
            nombres = re.findall(rf'({palabra_clave}\s+[^<>"\'={{}}\[\]\\/]{{8,70}})', html_content, re.IGNORECASE)
            nombres_unicos = []
            for n in nombres:
                n_limpio = re.sub(r'\s+', ' ', n).strip()
                if len(n_limpio) > 12 and n_limpio not in nombres_unicos and "Santa Isabel" not in n_limpio:
                    nombres_unicos.append(n_limpio)
            
            for i, nombre in enumerate(nombres_unicos[:15], 1):
                productos_capturados.append({
                    "posicion": i,
                    "nombre_producto": nombre,
                    "fuente": "Santa Isabel HTML SSR",
                    "termino_busqueda": termino
                })

        # 3. Estandarización al Contrato del Lakehouse
        filas_tabla = []
        for idx, item in enumerate(productos_capturados, 1):
            nombre_prod = str(item.get("name", item.get("nombre_producto", f"Producto {idx}")))
            sku_prod = str(item.get("sku", item.get("posicion", idx)))
            
            filas_tabla.append({
                "id_request": generar_id_request("santaisabel", f"{termino}_{sku_prod}", sucursal["region"], sucursal["comuna"]),
                "cadena": "santaisabel",
                "sku_producto": sku_prod,
                "nombre_canasta": termino,
                "nombre_detectado": nombre_prod[:100],
                "precio": extraer_precio_definitivo(item),
                "nombre_local": sucursal["local"],
                "region": sucursal["region"],
                "comuna": sucursal["comuna"],
                "fecha_carga": date.today().isoformat(),
                "timestamp_proceso": datetime.now().isoformat()
            })
            
        return filas_tabla