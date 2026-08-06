import os
import pandas as pd
from core.http_engine import ArmoredHTTPEngine
from core.r2_storage import R2Lakehouse
from builders.santaisabel import SantaIsabelBuilder # <--- IMPORTANTE: Importamos el builder correcto

os.environ["ENV"] = "dev"

print("====================================================================")
print("🛒 --- PRUEBA REAL SANTA ISABEL (SSR SEARCH) --- 🛒")
print("====================================================================\n")

TERMINOS_PRUEBA = ["arroz 1kg", "leche entera 1l"]
LOCAL_PRUEBA = {"local": "Santa Isabel Valdivia", "region": "Los Ríos", "comuna": "Valdivia"}

# Usamos nuestro nuevo Builder oficial
builder = SantaIsabelBuilder() 
solicitudes = builder.generar_solicitudes_canasta(TERMINOS_PRUEBA, LOCAL_PRUEBA)

# 2. Consultamos con el Motor HTTP Blindado
print(f"🌐 [1/3] Consultando {len(solicitudes)} términos en santaisabel.cl...")
engine = ArmoredHTTPEngine()
resultados_raw = engine.ejecutar_bloque(solicitudes)

# 3. Parseamos el HTML SSR
print("🧠 [2/3] Procesando HTML SSR de Santa Isabel...")
todas_las_filas = []
for req in resultados_raw:
    if "raw_payload_json" in req:
        # AQUÍ ESTÁ EL CAMBIO: Usamos 'sku_producto' que es la llave estándar
        filas = builder.parsear_ssr_santaisabel(req["raw_payload_json"], req["sku_producto"], LOCAL_PRUEBA)
        todas_las_filas.extend(filas)
        print(f"   ✅ Término '{req['sku_producto']}': {len(filas)} productos detectados.")

# 4. Guardamos en Cloudflare R2
df_final = pd.DataFrame(todas_las_filas)

if not df_final.empty:
    print("\n📊 TABLA DE PRODUCTOS EXTRAÍDOS DE SANTA ISABEL (Muestra):")
    print(df_final[["nombre_canasta", "nombre_detectado"]].head(6))
    
    print("\n📦 [3/3] Subiendo archivo Parquet a Cloudflare R2...")
    try:
        lake = R2Lakehouse()
        lake.guardar_parquet(df_final, cadena="santaisabel", nombre_archivo="prueba_santaisabel_real")
        print("\n🎉 ¡ÉXITO TOTAL! SANTA ISABEL GUARDADO EN EL LAKEHOUSE EN LA NUBE.")
    except Exception as e:
        print(f"\n⚠️ Error subiendo a R2: {e}")
else:
    print("\n❌ No se detectaron productos en Santa Isabel.")