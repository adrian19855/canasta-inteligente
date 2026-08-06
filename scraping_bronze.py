import duckdb
import requests
import json
import re
import html
from datetime import datetime, date

def inicializar_tabla_bronze(con):
    """Crea la tabla Bronze en DuckDB con soporte nativo de JSON."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS bronze_precios_supermercados (
            fecha_carga DATE,
            timestamp_proceso TIMESTAMP,
            cadena VARCHAR,
            nombre_local VARCHAR,
            region VARCHAR,
            comuna VARCHAR,
            termino_busqueda VARCHAR,
            raw_json JSON
        );
    """)
    print("✅ Tabla 'bronze_precios_supermercados' verificada/creada.")

def guardar_en_bronze(con, cadena, nombre_local, region, comuna, termino, data_json):
    """Inserta el JSON real y los metadatos en la capa Bronze de DuckDB."""
    fecha_hoy = date.today()
    ahora = datetime.now()
    
    json_str = json.dumps(data_json, ensure_ascii=False)
    
    con.execute("""
        INSERT INTO bronze_precios_supermercados (
            fecha_carga, timestamp_proceso, cadena, nombre_local, 
            region, comuna, termino_busqueda, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (fecha_hoy, ahora, cadena, nombre_local, region, comuna, termino, json_str))
    
    print(f"📦 [BRONZE] ¡DATOS REALES GUARDADOS EN DUCKDB!: {cadena} ({comuna}) - Término: '{termino}'")

def extraer_jumbo_ssr_real(con):
    """
    Descarga la URL real de búsqueda de Jumbo (200 OK) y extrae los productos
    directamente desde el HTML renderizado (Server-Side Rendering / Modo Lectura).
    """
    termino = "arroz"
    url_oficial = f"https://www.jumbo.cl/busqueda?ft={termino}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.9"
    }
    
    print(f"🌐 Descargando HTML oficial de Jumbo: {url_oficial} ...")
    try:
        response = requests.get(url_oficial, headers=headers, timeout=20)
        print(f"📡 Código de respuesta HTTP: {response.status_code}")
        
        if response.status_code == 200:
            html_content = html.unescape(response.text)
            
            # 1. Buscar estructurado SEO (Schema.org / JSON-LD) que Google Shopping exige
            scripts_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html_content, re.DOTALL | re.IGNORECASE)
            productos_encontrados = []
            
            for bloque in scripts_ld:
                try:
                    data = json.loads(bloque.strip())
                    if isinstance(data, dict):
                        if data.get("@type") == "ItemList" and "itemListElement" in data:
                            for item in data["itemListElement"]:
                                productos_encontrados.append(item)
                        elif data.get("@type") == "Product":
                            productos_encontrados.append(data)
                except:
                    pass
            
            # 2. Extracción directa desde el HTML (SSR / Modo Lectura)
            if not productos_encontrados:
                print("🔍 Analizando el texto del HTML (Modo Lectura SSR)...")
                # Capturamos los nombres exactos de los productos en el HTML (ej: "Arroz Grado 2 Tucapel...")
                nombres = re.findall(r'(Arroz\s+[^<>"\'={}\[\]\\/]{10,75})', html_content, re.IGNORECASE)
                
                nombres_unicos = []
                for n in nombres:
                    n_limpio = re.sub(r'\s+', ' ', n).strip()
                    if len(n_limpio) > 14 and n_limpio not in nombres_unicos and "Jumbo" not in n_limpio:
                        nombres_unicos.append(n_limpio)
                
                for i, nombre in enumerate(nombres_unicos[:25]):
                    productos_encontrados.append({
                        "posicion": i + 1,
                        "nombre_producto": nombre,
                        "fuente": "Jumbo HTML SSR",
                        "termino_busqueda": termino
                    })
            
            if len(productos_encontrados) > 0:
                print(f"🔥 ¡ÉXITO TOTAL! Se capturaron {len(productos_encontrados)} productos reales de Jumbo.")
                print("🛒 Muestra de productos encontrados en tu HTML:")
                for p in productos_encontrados[:6]:
                    nombre_print = p.get("nombre_producto") or p.get("name") or str(p)
                    print(f"   • {nombre_print}")
                
                payload_final = {
                    "status": 200,
                    "url": url_oficial,
                    "metodo_captura": "React SSR HTML",
                    "total_productos": len(productos_encontrados),
                    "productos": productos_encontrados
                }
                
                guardar_en_bronze(
                    con=con,
                    cadena="Jumbo",
                    nombre_local="Jumbo Online Chile",
                    region="Metropolitana",
                    comuna="Providencia",
                    termino=termino,
                    data_json=payload_final
                )
            else:
                print("⚠️ La página cargó OK, pero no se encontraron coincidencias de texto.")
        else:
            print(f"⚠️ El servidor respondió con estado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error al conectar con Jumbo: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando proceso de ingesta Bronze con DATOS REALES DE JUMBO (SSR)...")
    conn = duckdb.connect("canasta.duckdb")
    
    inicializar_tabla_bronze(conn)
    extraer_jumbo_ssr_real(conn)
    
    total = conn.execute("SELECT COUNT(*) FROM bronze_precios_supermercados").fetchone()[0]
    print(f"\n📊 Total de registros en Bronze: {total}")
    
    conn.close()