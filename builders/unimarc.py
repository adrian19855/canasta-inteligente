import re
import json
import html
from datetime import date, datetime
from builders.base import crear_solicitud_estandar, generar_id_request

class UnimarcBuilder:
    """
    Builder para Unimarc (SMU Chile) con cabeceras anti-WAF reforzadas.
    """
    def __init__(self):
        self.cadena = "unimarc"
        # Cabeceras estilo navegador real para engañar al WAF
        self.headers_unimarc = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.unimarc.cl/",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }

    def generar_solicitudes_canasta(self, terminos: list, sucursal: dict) -> list:
        solicitudes = []
        for termino in terminos:
            termino_url = termino.replace(" ", "-")
            url_oficial = f"https://www.unimarc.cl/search?q={termino_url}"
            
            req = crear_solicitud_estandar(
                cadena=self.cadena,
                sku_producto=termino,
                nombre_canasta=termino,
                url=url_oficial,
                region=sucursal["region"],
                comuna=sucursal["comuna"],
                headers_custom=self.headers_unimarc
            )
            solicitudes.append(req)
            
        return solicitudes

    def parsear_ssr_unimarc(self, html_content: str, termino: str, sucursal: dict) -> list:
        html_content = html.unescape(html_content)
        productos_capturados = []
        
        # 1. Next.js __NEXT_DATA__
        next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_content, re.DOTALL)
        if next_data_match:
            try:
                data = json.loads(next_data_match.group(1))
                def buscar_productos(obj):
                    if isinstance(obj, dict):
                        if ("name" in obj or "title" in obj) and ("sku" in obj or "id" in obj or "productId" in obj):
                            nombre = obj.get("name", obj.get("title"))
                            sku = str(obj.get("sku", obj.get("id", obj.get("productId"))))
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

        # 2. Respaldo Regex
        if not productos_capturados:
            palabra_clave = termino.split()[0]
            nombres = re.findall(rf'({palabra_clave}\s+[^<>"\'={{}}\[\]\\/]{{8,70}})', html_content, re.IGNORECASE)
            nombres_unicos = []
            for n in nombres:
                n_limpio = re.sub(r'\s+', ' ', n).strip()
                if len(n_limpio) > 12 and n_limpio not in nombres_unicos and "Unimarc" not in n_limpio:
                    nombres_unicos.append(n_limpio)
            
            for idx, nombre in enumerate(nombres_unicos[:20], 1):
                productos_capturados.append({
                    "nombre": nombre,
                    "sku": f"UNI-SSR-{idx}"
                })

        filas_tabla = []
        for prod in productos_capturados:
            filas_tabla.append({
                "id_request": generar_id_request("unimarc", f"{termino}_{prod['sku']}", sucursal["region"], sucursal["comuna"]),
                "cadena": "unimarc",
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