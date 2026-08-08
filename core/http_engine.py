import time
from curl_cffi import requests

class ArmoredHTTPEngine:
    """
    Motor HTTP Estandarizado con suplantación de huella TLS (JA4/JA3).
    """
    def __init__(self):
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "es-CL,es;q=0.9",
            "Accept": "application/json, text/plain, */*"
        }

    def ejecutar_bloque(self, solicitudes: list) -> list:
        resultados = []
        for req in solicitudes:
            url = req.get("url")
            headers = req.get("headers_custom", self.default_headers)
            
            exito = False
            for _ in range(2):
                try:
                    res = requests.get(
                        url, 
                        headers=headers, 
                        impersonate="chrome", 
                        timeout=15
                    )
                    if res.status_code == 200:
                        req["raw_payload_json"] = res.text
                        resultados.append(req)
                        exito = True
                        break
                except Exception as e:
                    time.sleep(1)
            
            if not exito:
                req["raw_payload_json"] = ""
                resultados.append(req)
                
            time.sleep(0.5)
        return resultados