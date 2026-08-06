import duckdb
import requests
import json
import re
import html
import time
from datetime import datetime, date

# 1. CANASTA BÁSICA OFICIAL + PRODUCTOS ESENCIALES (Ampliables)
TERMINOS_CANASTA = [
    # Pan, Cereales y Masas
    "arroz 1kg", "pan marraqueta", "pan hallulla", "fideos espagueti", "galletas dulces",
    "galletas de soda", "harina sin polvos 1kg", "avena 500g", "prepizza",
    # Carnes y Embutidos
    "carne molida vacuno", "asiento vacuno", "chuleta de cerdo", "costillar cerdo",
    "pulpa de cerdo", "pechuga de pollo", "pollo entero", "trutro de pollo",
    "salchichas vienesas", "longaniza", "jamon acaramelado", "pate",
    # Pescados y Mariscos
    "merluza congelada", "jurel en conserva", "choritos en conserva", "surtido mariscos",
    # Lácteos, Huevos y Grasas
    "leche entera 1l", "leche en polvo", "yogurt natural", "queso gouda", "quesillo",
    "queso crema", "huevos docena", "mantequilla 250g", "margarina", "aceite vegetal 1l",
    # Frutas, Verduras y Legumbres
    "platanos", "manzanas", "limones", "palta hass", "tomates", "lechuga",
    "zapallo", "zanahorias", "cebolla", "choclo congelado", "papas 1kg",
    "porotos secos", "lentejas 1kg", "mani salado",
    # Azúcares, Condimentos y Bebidas
    "azucar 1kg", "salsa de tomate", "sal de mesa", "mayonesa",
    "cafe instantaneo", "te ceylan", "agua mineral 1.5l", "bebida cola 2l", "jugo nectar 1.5l"
]

# 2. LISTA TOTAL Y EXHAUSTIVA DE LOCALES JUMBO EN CHILE
LOCALES_JUMBO = [
    # Región de Arica y Parinacota y Región de Tarapacá
    {"local": "Jumbo Arica", "region": "Arica y Parinacota", "comuna": "Arica"},
    {"local": "Jumbo Iquique", "region": "Tarapacá", "comuna": "Iquique"},
    # Región de Antofagasta y Región de Atacama
    {"local": "Jumbo Antofagasta Pedro de Valdivia", "region": "Antofagasta", "comuna": "Antofagasta"},
    {"local": "Jumbo Antofagasta Angamos", "region": "Antofagasta", "comuna": "Antofagasta"},
    {"local": "Jumbo Antofagasta Punto de Encuentro", "region": "Antofagasta", "comuna": "Antofagasta"},
    {"local": "Jumbo Calama", "region": "Antofagasta", "comuna": "Calama"},
    {"local": "Jumbo Copiapó", "region": "Atacama", "comuna": "Copiapó"},
    # Región de Coquimbo
    {"local": "Jumbo La Serena (El Milagro / Ulriksen)", "region": "Coquimbo", "comuna": "La Serena"},
    {"local": "Jumbo Portal La Serena", "region": "Coquimbo", "comuna": "La Serena"},
    # Región de Valparaíso
    {"local": "Jumbo Portal Valparaíso", "region": "Valparaíso", "comuna": "Valparaíso"},
    {"local": "Jumbo Viña del Mar 1 Norte", "region": "Valparaíso", "comuna": "Viña del Mar"},
    {"local": "Jumbo Viña del Mar Arlegui", "region": "Valparaíso", "comuna": "Viña del Mar"},
    {"local": "Jumbo Reñaca", "region": "Valparaíso", "comuna": "Viña del Mar"},
    {"local": "Jumbo Concón", "region": "Valparaíso", "comuna": "Concón"},
    {"local": "Jumbo El Belloto", "region": "Valparaíso", "comuna": "Quilpué"},
    {"local": "Jumbo Los Andes", "region": "Valparaíso", "comuna": "Los Andes"},
    {"local": "Jumbo San Felipe", "region": "Valparaíso", "comuna": "San Felipe"},
    # Región Metropolitana (Santiago)
    {"local": "Jumbo El Llano", "region": "Metropolitana", "comuna": "San Miguel"},
    {"local": "Jumbo Santiago Centro", "region": "Metropolitana", "comuna": "Santiago"},
    {"local": "Jumbo Costanera Center", "region": "Metropolitana", "comuna": "Providencia"},
    {"local": "Jumbo Alto Las Condes", "region": "Metropolitana", "comuna": "Las Condes"},
    {"local": "Jumbo Bilbao", "region": "Metropolitana", "comuna": "Las Condes"},
    {"local": "Jumbo Latadía", "region": "Metropolitana", "comuna": "Las Condes"},
    {"local": "Jumbo El Alba", "region": "Metropolitana", "comuna": "Las Condes"},
    {"local": "Jumbo Los Trapenses", "region": "Metropolitana", "comuna": "Lo Barnechea"},
    {"local": "Jumbo Pie Andino", "region": "Metropolitana", "comuna": "Lo Barnechea"},
    {"local": "Jumbo Lo Castillo", "region": "Metropolitana", "comuna": "Vitacura"},
    {"local": "Jumbo Portal La Reina", "region": "Metropolitana", "comuna": "La Reina"},
    {"local": "Jumbo Portal Ñuñoa", "region": "Metropolitana", "comuna": "Ñuñoa"},
    {"local": "Jumbo Peñalolén", "region": "Metropolitana", "comuna": "Peñalolén"},
    {"local": "Jumbo Florida Center", "region": "Metropolitana", "comuna": "La Florida"},
    {"local": "Jumbo Independencia", "region": "Metropolitana", "comuna": "Independencia"},
    {"local": "Jumbo Arauco Maipú", "region": "Metropolitana", "comuna": "Maipú"},
    {"local": "Jumbo Pajaritos", "region": "Metropolitana", "comuna": "Maipú"},
    {"local": "Jumbo Concha y Toro", "region": "Metropolitana", "comuna": "Puente Alto"},
    {"local": "Jumbo Plaza Puente", "region": "Metropolitana", "comuna": "Puente Alto"},
    {"local": "Jumbo San Bernardo (Mallplaza Sur)", "region": "Metropolitana", "comuna": "San Bernardo"},
    {"local": "Jumbo Chamisero", "region": "Metropolitana", "comuna": "Colina"},
    {"local": "Jumbo Puertas de Chicureo", "region": "Metropolitana", "comuna": "Colina"},
    # Región de O'Higgins y Región del Maule
    {"local": "Jumbo Rancagua Membrillar", "region": "O'Higgins", "comuna": "Rancagua"},
    {"local": "Jumbo Rancagua Centro", "region": "O'Higgins", "comuna": "Rancagua"},
    {"local": "Jumbo Santa Cruz", "region": "O'Higgins", "comuna": "Santa Cruz"},
    {"local": "Jumbo Curicó", "region": "Maule", "comuna": "Curicó"},
    {"local": "Jumbo Talca Centro", "region": "Maule", "comuna": "Talca"},
    {"local": "Jumbo Talca Las Rastras", "region": "Maule", "comuna": "Talca"},
    # Región de Ñuble y Región del Biobío
    {"local": "Jumbo Chillán Vicente Méndez", "region": "Ñuble", "comuna": "Chillán"},
    {"local": "Jumbo Chillán Centro", "region": "Ñuble", "comuna": "Chillán"},
    {"local": "Jumbo Concepción Barros Arana", "region": "Biobío", "comuna": "Concepción"},
    {"local": "Jumbo Concepción Pedro de Valdivia", "region": "Biobío", "comuna": "Concepción"},
    {"local": "Jumbo Hualpén (Costanera Norte)", "region": "Biobío", "comuna": "Hualpén"},
    {"local": "Jumbo Los Ángeles", "region": "Biobío", "comuna": "Los Ángeles"},
    # Región de La Araucanía y Región de Los Ríos
    {"local": "Jumbo Temuco Av. Alemania", "region": "La Araucanía", "comuna": "Temuco"},
    {"local": "Jumbo Temuco Los Pablos", "region": "La Araucanía", "comuna": "Temuco"},
    {"local": "Jumbo Valdivia", "region": "Los Ríos", "comuna": "Valdivia"},
    # Región de Los Lagos
    {"local": "Jumbo Osorno", "region": "Los Lagos", "comuna": "Osorno"},
    {"local": "Jumbo Puerto Varas (Doña Ema)", "region": "Los Lagos", "comuna": "Puerto Varas"},
    {"local": "Jumbo Puerto Montt Ejército", "region": "Los Lagos", "comuna": "Puerto Montt"},
    {"local": "Jumbo Puerto Montt Bosquemar", "region": "Los Lagos", "comuna": "Puerto Montt"}
]

def inicializar_tabla_bronze(con):
    """Crea la tabla Bronze en DuckDB si no existe."""
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

def guardar_en_bronze(con, cadena, nombre_local, region, comuna, termino, data_json):
    """Inserta el JSON en la capa Bronze de DuckDB."""
    fecha_hoy = date.today()
    ahora = datetime.now()
    json_str = json.dumps(data_json, ensure_ascii=False)
    
    con.execute("""
        INSERT INTO bronze_precios_supermercados (
            fecha_carga, timestamp_proceso, cadena, nombre_local, 
            region, comuna, termino_busqueda, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (fecha_hoy, ahora, cadena, nombre_local, region, comuna, termino, json_str))

def extraer_jumbo_ssr(con, termino, tienda):
    """Extrae datos desde el HTML SSR de Jumbo para un producto y sucursal."""
    url_oficial = f"https://www.jumbo.cl/busqueda?ft={termino}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.9",
        "Referer": "https://www.jumbo.cl/"
    }
    
    try:
        response = requests.get(url_oficial, headers=headers, timeout=20)
        
        if response.status_code == 200:
            html_content = html.unescape(response.text)
            
            # 1. Búsqueda estructurada (JSON-LD)
            scripts_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html_content, re.DOTALL | re.IGNORECASE)
            productos = []
            
            for bloque in scripts_ld:
                try:
                    data = json.loads(bloque.strip())
                    if isinstance(data, dict):
                        if data.get("@type") == "ItemList" and "itemListElement" in data:
                            for item in data["itemListElement"]:
                                productos.append(item)
                        elif data.get("@type") == "Product":
                            productos.append(data)
                except:
                    pass
            
            # 2. Respaldo textual SSR
            if not productos:
                palabra_clave = termino.split()[0]
                nombres = re.findall(rf'({palabra_clave}\s+[^<>"\'={{}}\[\]\\/]{{8,70}})', html_content, re.IGNORECASE)
                nombres_unicos = []
                for n in nombres:
                    n_limpio = re.sub(r'\s+', ' ', n).strip()
                    if len(n_limpio) > 12 and n_limpio not in nombres_unicos and "Jumbo" not in n_limpio:
                        nombres_unicos.append(n_limpio)
                
                for i, nombre in enumerate(nombres_unicos[:25]):
                    productos.append({
                        "posicion": i + 1,
                        "nombre_producto": nombre,
                        "fuente": "Jumbo HTML SSR",
                        "termino_busqueda": termino
                    })
            
            if len(productos) > 0:
                payload_final = {
                    "status": 200,
                    "url": url_oficial,
                    "tienda": tienda["local"],
                    "metodo_captura": "React SSR HTML",
                    "total_productos": len(productos),
                    "productos": productos
                }
                
                guardar_en_bronze(
                    con=con,
                    cadena="Jumbo",
                    nombre_local=tienda["local"],
                    region=tienda["region"],
                    comuna=tienda["comuna"],
                    termino=termino,
                    data_json=payload_final
                )
                print(f"   ✅ [{tienda['comuna']}] '{termino}': {len(productos)} productos capturados.")
            else:
                print(f"   ⚠️ [{tienda['comuna']}] '{termino}': Sin resultados directos en el HTML.")
        else:
            print(f"   ❌ [{tienda['comuna']}] '{termino}': Error HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error conectando: {e}")

def ejecutar_pipeline_nacional():
    print("🚀 [PIPELINE JUMBO NACIONAL] Iniciando captura masiva de la Canasta Básica...")
    conn = duckdb.connect("canasta.duckdb")
    inicializar_tabla_bronze(conn)
    
    total_tiendas = len(LOCALES_JUMBO)
    total_terminos = len(TERMINOS_CANASTA)
    total_iteraciones = total_tiendas * total_terminos
    contador = 0
    
    for t_idx, tienda in enumerate(LOCALES_JUMBO, 1):
        print(f"\n🏬 [{t_idx}/{total_tiendas}] REGIÓN: {tienda['region'].upper()} -> {tienda['local']} ({tienda['comuna']})")
        
        for termino in TERMINOS_CANASTA:
            contador += 1
            print(f"   -> ({contador}/{total_iteraciones}) Consultando: '{termino}'...")
            extraer_jumbo_ssr(conn, termino, tienda)
            
            # Pausa de 2 segundos para Scraping Defensivo (cuidar IP y evitar bloqueos WAF)
            time.sleep(2)
            
    total_registros = conn.execute("SELECT COUNT(*) FROM bronze_precios_supermercados WHERE cadena = 'Jumbo'").fetchone()[0]
    print(f"\n🎉 ¡Carga Nacional de Jumbo terminada con éxito! Total en Bronze: {total_registros} registros.")
    conn.close()

if __name__ == "__main__":
    ejecutar_pipeline_nacional()