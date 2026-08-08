import os
import pandas as pd
from core.http_engine import ArmoredHTTPEngine
from core.r2_storage import R2Lakehouse
from builders.unimarc import UnimarcBuilder

print("🚀 PROBANDO PIPELINE DE UNIMARC (MODO RESILIENTE)...")

os.environ["ENV"] = "dev"

TERMINOS_PRUEBA = ["arroz 1kg", "leche entera 1l"]
LOCAL_PRUEBA = {
    "local": "Unimarc Valdivia Centro",
    "region": "Los Ríos",
    "comuna": "Valdivia",
}

builder = UnimarcBuilder()
solicitudes = builder.generar_solicitudes_canasta(TERMINOS_PRUEBA, LOCAL_PRUEBA)

print(f"🌐 [1/3] Consultando {len(solicitudes)} términos para Unimarc...")
engine = ArmoredHTTPEngine()
resultados_raw = engine.ejecutar_bloque(solicitudes)

# Mapeo por SKU para asociar respuestas en vivo o pasar texto vacío si hubo bloqueo 500
payloads_por_sku = {
    req["sku_producto"]: req.get("raw_payload_json", "")
    for req in (resultados_raw or [])
}

print("🧠 [2/3] Procesando catálogo y estandarizando datos...")
todas_las_filas = []

for req in solicitudes:
    sku = req["sku_producto"]
    raw_json = payloads_por_sku.get(sku, "")
    filas = builder.parsear_ssr_unimarc(raw_json, sku, LOCAL_PRUEBA)
    todas_las_filas.extend(filas)
    print(
        f"   ✅ Término '{sku}': {len(filas)} productos listos para el"
        " Lakehouse."
    )

df_final = pd.DataFrame(todas_las_filas)

if not df_final.empty:
    print("\n📊 TABLA DE PRODUCTOS EXTRAÍDOS DE UNIMARC:")
    print(
        df_final[["nombre_canasta", "nombre_detectado", "sku_producto"]].head(8)
    )

    print("\n📦 [3/3] Subiendo archivo Parquet a Cloudflare R2...")
    try:
        lake = R2Lakehouse()
        lake.guardar_parquet(
            df_final,
            cadena="unimarc",
            nombre_archivo="prueba_unimarc_real",
        )
        print(
            "\n🎉 ¡GOLAZO! UNIMARC DERROTADO Y GUARDADO CON ÉXITO EN EL"
            " LAKEHOUSE."
        )
    except Exception as e:
        print(f"\n⚠️ Error subiendo a R2: {e}")
else:
    print("\n❌ Error inesperado: No se generaron filas.")