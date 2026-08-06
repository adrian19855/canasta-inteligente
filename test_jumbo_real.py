import os
import re
import json
import html
import pandas as pd
from datetime import date, datetime
from core.http_engine import ArmoredHTTPEngine
from core.r2_storage import R2Lakehouse
from builders.base import generar_id_request

# 1. Configuración de ambiente
os.environ["ENV"] = "dev"

print("====================================================================")
print("🛒 --- PRUEBA REAL JUMBO (HTML SSR JSON-LD SEARCH) --- 🛒")
print("====================================================================\n")

# 2. Muestra de prueba de tu lista oficial de la Canasta Básica
TERMINOS_PRUEBA = ["arroz 1kg", "leche entera 1l"]
LOCAL_PRUEBA = {"local": "Jumbo Costanera Center", "region": "Metropolitana", "comuna": "Providencia"}

def parsear_ssr_jumbo(html_content, termino, tienda):
    """
    Tu lógica ganadora: Extrae los productos desde los scripts JSON-LD o regex en el HTML SSR de Jumbo.
    """
    productos_capturados = []
    
    # 1. Búsqueda estructurada (JSON-LD)
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

    # 2. Respaldo textual SSR (tu regex de seguridad)
    if not productos_capturados:
        palabra_clave = termino.split()[0]
        nombres = re.findall(rf'({palabra_clave}\s+[^<>"\'={{}}\[\]\\/]{{8,70}})', html_content, re.IGNORECASE)
        nombres_unicos = []
        for n in nombres:
            n_limpio = re.sub(r'\s+', ' ', n).strip()
            if len(n_limpio) > 12 and n_limpio not in nombres_unicos and "Jumbo" not in n_limpio:
                nombres_unicos.append(n_limpio)
        
        for i, nombre in enumerate(nombres_unicos[:15]):
            productos_capturados.append({
                "posicion": i + 1,
                "nombre_producto": nombre,
                "fuente": "Jumbo HTML SSR Respaldo",
                "termino_busqueda": termino
            })

    # 3. Empaquetar todo en el formato tabular estándar para nuestro Data Lake
    filas_tabla = []
    for idx, item in enumerate(productos_capturados, 1):
        nombre_prod = str(item.get("name", item.get("nombre_producto", f"Producto {idx}")))
        sku_prod = str(item.get("sku", item.get("posicion", idx)))
        
        filas_tabla.append({
            "id_request": generar_id_request("jumbo", f"{termino}_{sku_prod}", LOCAL_PRUEBA["region"], LOCAL_PRUEBA["comuna"]),
            "cadena": "jumbo",
            "sku_producto": sku_prod,
            "nombre_canasta": termino,
            "nombre_detectado": nombre_prod[:100],  # Limitar longitud
            "nombre_local": LOCAL_PRUEBA["local"],
            "region": LOCAL_PRUEBA["region"],
            "comuna": LOCAL_PRUEBA["comuna"],
            "fecha_carga": date.today().isoformat(),
            "timestamp_proceso": datetime.now().isoformat()
        })
        
    return filas_tabla

# 3. Armar solicitudes con la URL pública de búsqueda
solicitudes = []
for termino in TERMINOS_PRUEBA:
    solicitudes.append({
        "cadena": "jumbo",
        "sku_producto": termino,
        "url": f"https://www.jumbo.cl/busqueda?ft={termino}",
        "termino": termino,
        "headers_custom": {
            "Referer": "https://www.jumbo.cl/"
        }
    })

# 4. Ejecutar con nuestro Motor HTTP Blindado
print(f"🌐 [1/3] Consultando {len(solicitudes)} términos en www.jumbo.cl con Motor HTTP Blindado...")
engine = ArmoredHTTPEngine()
resultados_raw = engine.ejecutar_bloque(solicitudes)

# 5. Parsear el HTML usando tu lógica SSR
print("🧠 [2/3] Procesando HTML y extrayendo productos desde etiquetas JSON-LD...")
todas_las_filas = []
for req in resultados_raw:
    if "raw_payload_json" in req:
        filas = parsear_ssr_jumbo(req["raw_payload_json"], req["termino"], LOCAL_PRUEBA)
        todas_las_filas.extend(filas)
        print(f"   ✅ Término '{req['termino']}': {len(filas)} productos detectados en el HTML.")

# 6. Guardar en Cloudflare R2
df_final = pd.DataFrame(todas_las_filas)

if not df_final.empty:
    print("\n📊 TABLA DE PRODUCTOS EXTRAÍDOS (Muestra):")
    print(df_final[["nombre_canasta", "nombre_detectado", "nombre_local"]].head(6))
    
    print("\n📦 [3/3] Subiendo archivo Parquet a Cloudflare R2...")
    try:
        lake = R2Lakehouse()
        lake.guardar_parquet(df_final, cadena="jumbo", nombre_archivo="prueba_ssr_real")
        print("\n🎉 ¡ÉXITO TOTAL! TU LÓGICA SSR FUE INTEGRADA AL LAKEHOUSE EN LA NUBE.")
    except Exception as e:
        print(f"\n⚠️ Error subiendo a R2: {e}")
        print("💡 Verifica que tus secretos de R2 estén en la terminal (export R2_ACCESS_KEY_ID=...).")
else:
    print("\n❌ No se extrajeron productos. Revisa la conexión.")