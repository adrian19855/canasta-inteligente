import re
import json
import html
from datetime import date, datetime
from builders.base import crear_solicitud_estandar, generar_id_request

class SantaIsabelBuilder:
    """
    Builder para Santa Isabel (Cencosud Chile).
    Reutiliza la lógica SSR de búsqueda web pública de Cencosud.
    """
    def __init__(self):
        self.cadena = "santaisabel"
        self.headers_cencosud = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9",
            "Referer": "https://www.santaisabel.cl/"
        }

    def generar_solicitudes_canasta(self, terminos: list, sucursal: dict) -> list:
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

    def parsear_ssr_santaisabel(self, html_content: str, termino: str, sucursal: dict) -> list:
        """
        Extrae productos desde los scripts JSON-LD o respaldo SSR de Santa Isabel.
        """
        html_content = html.unescape(html_content)
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

        # 3. Estandarizamos al Contrato de Datos del Lakehouse
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
                "nombre_local": sucursal["local"],
                "region": sucursal["region"],
                "comuna": sucursal["comuna"],
                "fecha_carga": date.today().isoformat(),
                "timestamp_proceso": datetime.now().isoformat()
            })
            
        return filas_tabla