import os
import pandas as pd
from core.http_engine import ArmoredHTTPEngine
from core.r2_storage import R2Lakehouse
from builders.unimarc import UnimarcBuilder

os.environ["ENV"] = "dev"

print("--- PRUEBA DEBUG UNIMARC ---")

TERMINOS_PRUEBA = ["arroz 1kg"]
LOCAL_PRUEBA = {"local": "Unimarc Valdivia Centro", "region": "Los Ríos", "comuna": "Valdivia"}

builder = UnimarcBuilder()
solicitudes = builder.generar_solicitudes_canasta(TERMINOS_PRUEBA, LOCAL_PRUEBA)

# AQUÍ ESTÁ EL TRUCO: Imprimimos la URL antes de llamar al motor
for req in solicitudes:
    print(f"\n🔗 URL PARA PROBAR EN TU NAVEGADOR (INCOGNITO):")
    print(req['url'])

print("\n🌐 [1/3] Consultando con Motor HTTP Blindado...")
engine = ArmoredHTTPEngine()
resultados_raw = engine.ejecutar_bloque(solicitudes)

# 3. Parseamos el HTML SSR
print("🧠 [2/3] Procesando HTML SSR de Unimarc...")
todas_las_filas = []
for req in resultados_raw:
    if "raw_payload_json" in req:
        filas = builder.parsear_ssr_unimarc(req["raw_payload_json"], req["sku_producto"], LOCAL_PRUEBA)
        todas_las_filas.extend(filas)
        print(f"   ✅ Término '{req['sku_producto']}': {len(filas)} productos detectados en Unimarc.")

# 4. Guardamos en Cloudflare R2
df_final = pd.DataFrame(todas_las_filas)

if not df_final.empty:
    print("\n📊 TABLA DE PRODUCTOS EXTRAÍDOS DE UNIMARC (Muestra):")
    print(df_final[["nombre_canasta", "nombre_detectado", "sku_producto"]].head(6))
    
    print("\n📦 [3/3] Subiendo archivo Parquet a Cloudflare R2...")
    try:
        lake = R2Lakehouse()
        lake.guardar_parquet(df_final, cadena="unimarc", nombre_archivo="prueba_unimarc_real")
        print("\n🎉 ¡ÉXITO TOTAL! UNIMARC GUARDADO EN EL LAKEHOUSE EN LA NUBE.")
    except Exception as e:
        print(f"\n⚠️ Error subiendo a R2: {e}")
else:
    print("\n❌ No se detectaron productos en el HTML de Unimarc.")