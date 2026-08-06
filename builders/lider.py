import re
import json
import html
from datetime import date, datetime
from builders.base import crear_solicitud_estandar, generar_id_request

class LiderBuilder:
    """
    Builder para Lider (Walmart Chile) usando la URL SSR de super.lider.cl
    """
    def __init__(self):
        self.cadena = "lider"
        self.headers_lider = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9",
            "Referer": "https://super.lider.cl/"
        }

    def generar_solicitudes_canasta(self, terminos: list, sucursal: dict) -> list:
        solicitudes = []
        for termino in terminos:
            termino_url = termino.replace(" ", "+")
            # TU URL EXACTA DE BÚSQUEDA EN LIDER
            url_oficial = f"https://super.lider.cl/search?q={termino_url}&facet=fulfillment_method%3APickup"
            
            req = crear_solicitud_estandar(
                cadena=self.cadena,
                sku_producto=termino,
                nombre_canasta=termino,
                url=url_oficial,
                region=sucursal["region"],
                comuna=sucursal["comuna"],
                headers_custom=self.headers_lider
            )
            solicitudes.append(req)
            
        return solicitudes

    def parsear_ssr_lider(self, html_content: str, termino: str, sucursal: dict) -> list:
        """
        Extrae productos desde el HTML de super.lider.cl (Next.js __NEXT_DATA__, JSON-LD o Regex).
        """
        html_content = html.unescape(html_content)
        productos_capturados = []
        
        # 1. Buscar en el estado SSR de Next.js (__NEXT_DATA__)
        next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_content, re.DOTALL)
        if next_data_match:
            try:
                data = json.loads(next_data_match.group(1))
                # Búsqueda recursiva de diccionarios que parezcan productos en el JSON de Next.js
                def buscar_productos(obj):
                    if isinstance(obj, dict):
                        if ("displayName" in obj or "productName" in obj) and ("sku" in obj or "ID" in obj or "productId" in obj):
                            nombre = obj.get("displayName", obj.get("productName"))
                            sku = str(obj.get("sku", obj.get("ID", obj.get("productId"))))
                            if nombre and len(str(nombre)) > 4:
                                productos_capturados.append({"nombre": nombre, "sku": sku})
                        for v in obj.values():
                            buscar_productos(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            buscar_productos(item)
                buscar_productos(data)
            except Exception:
                pass

        # 2. Respaldo Textual/Regex en el HTML si no capturó por Next.js
        if not productos_capturados:
            palabra_clave = termino.split()[0]
            nombres = re.findall(rf'({palabra_clave}\s+[^<>"\'={{}}\[\]\\/]{{8,70}})', html_content, re.IGNORECASE)
            nombres_unicos = []
            for n in nombres:
                n_limpio = re.sub(r'\s+', ' ', n).strip()
                if len(n_limpio) > 12 and n_limpio not in nombres_unicos and "Lider" not in n_limpio:
                    nombres_unicos.append(n_limpio)
            
            for idx, nombre in enumerate(nombres_unicos[:20], 1):
                productos_capturados.append({
                    "nombre": nombre,
                    "sku": f"LID-SSR-{idx}"
                })

        # 3. Estandarizamos al formato del Lakehouse
        filas_tabla = []
        for prod in productos_capturados:
            filas_tabla.append({
                "id_request": generar_id_request("lider", f"{termino}_{prod['sku']}", sucursal["region"], sucursal["comuna"]),
                "cadena": "lider",
                "sku_producto": prod["sku"],
                "nombre_canasta": termino,
                "nombre_detectado": prod["nombre"][:100],
                "nombre_local": sucursal["local"],
                "region": sucursal["region"],
                "comuna": sucursal["comuna"],
                "fecha_carga": date.today().isoformat(),
                "timestamp_proceso": datetime.now().isoformat()
            })
            
        return filas_tabla