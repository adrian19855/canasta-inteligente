import time
import requests

class ArmoredHTTPEngine:
    """
    Motor HTTP Blindado con rotación de User-Agents, manejo de sesiones y reintentos defensivos.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "es-CL,es;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        })

    def ejecutar_bloque(self, solicitudes: list) -> list:
        resultados = []
        
        # 1. Visita inicial a la home para obtener cookies de sesión legítimas (vital para Unimarc)
        try:
            self.session.get("https://www.unimarc.cl/", timeout=15)
        except Exception:
            pass

        for req in solicitudes:
            url = req.get("url")
            headers = req.get("headers_custom", {})
            
            exito = False
            intentos = 3
            
            for intento in range(intentos):
                try:
                    # Usamos la sesión para heredar las cookies de la home
                    response = self.session.get(url, headers=headers, timeout=20)
                    
                    if response.status_code == 200:
                        req["raw_payload_json"] = response.text
                        resultados.append(req)
                        exito = True
                        break
                    elif response.status_code == 403:
                        print(f"⚠️ [WAF ALERT] HTTP 403 en {req.get('cadena')}. Enfriando motores por 15s...")
                        time.sleep(15)
                    else:
                        print(f"⚠️ HTTP {response.status_code} para URL: {url}")
                        break
                except Exception as e:
                    print(f"❌ Error de red en {url}: {e}")
                    time.sleep(5)
            
            time.sleep(2)  # Pausa defensiva entre peticiones
            
        return resultados