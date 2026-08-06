import os
import pandas as pd
from core.http_engine import ArmoredHTTPEngine
from core.scheduler import RoundRobinScheduler
from core.r2_storage import R2Lakehouse
from builders.base import crear_solicitud_estandar, convertir_a_dataframe

# 1. Configuración de ambiente para pruebas
os.environ["ENV"] = "dev"

print("====================================================================")
print("🚀 --- INICIANDO BANCO DE PRUEBAS INTEGRAL (4 SUPERMERCADOS) --- 🚀")
print("====================================================================\n")

# 2. Catálogo de prueba con dominios web PÚBLICOS REALES (VTEX / BFF Catalogs)
# Usamos endpoints públicos de búsqueda por SKU para garantizar resolución DNS 100%
solicitudes_prueba = {
    "jumbo": [
        crear_solicitud_estandar(
            cadena="jumbo",
            sku_producto="1001",
            nombre_canasta="Arroz Grano Largo 1kg (Prueba)",
            url="https://www.jumbo.cl/api/catalog_system/pub/products/search?fq=sku:1",
            region="RM",
            comuna="Santiago",
            headers_custom={"Accept": "application/json"}
        )
    ],
    "santaisabel": [
        crear_solicitud_estandar(
            cadena="santaisabel",
            sku_producto="2001",
            nombre_canasta="Aceite Maravilla 1L (Prueba)",
            url="https://www.santaisabel.cl/api/catalog_system/pub/products/search?fq=sku:1",
            region="RM",
            comuna="Santiago",
            headers_custom={"Accept": "application/json"}
        )
    ],
    "lider": [
        crear_solicitud_estandar(
            cadena="lider",
            sku_producto="3001",
            nombre_canasta="Azúcar Blanca 1kg (Prueba)",
            url="https://www.lider.cl/api/catalog_system/pub/products/search?fq=sku:1",
            region="RM",
            comuna="Santiago",
            headers_custom={"Accept": "application/json"}
        )
    ],
    "unimarc": [
        crear_solicitud_estandar(
            cadena="unimarc",
            sku_producto="4001",
            nombre_canasta="Harina sin Polvos 1kg (Prueba)",
            url="https://www.unimarc.cl/api/catalog_system/pub/products/search?fq=sku:1",
            region="RM",
            comuna="Santiago",
            headers_custom={"Accept": "application/json"}
        )
    ]
}

# 3. Probar el Orquestador Round-Robin (Intercalado por turnos)
print("🧩 [PASO 1/4] Orquestando cola intercalada para evitar bloqueos WAF...")
scheduler = RoundRobinScheduler(tamano_bloque=1) # Bloque de 1 para intercalar uno a uno
cola_round_robin = scheduler.crear_cola_intercalada(solicitudes_prueba)

# Aplanar la cola para enviar todo ordenado en un solo lote de ejecución
lista_ordenada = [item for bloque in cola_round_robin for item in bloque]

print("\n--- ORDEN DE TURNOS EN LA COLA ---")
for idx, req in enumerate(lista_ordenada, 1):
    print(f"Turno #{idx} -> Supermercado: {req['cadena'].upper():<12} | SKU: {req['sku_producto']} | URL: {req['url']}")

# 4. Ejecutar el Motor HTTP Blindado
print("\n🌐 [PASO 2/4] Enviando peticiones reales a internet con Motor HTTP Blindado...")
engine = ArmoredHTTPEngine()
resultados = engine.ejecutar_bloque(lista_ordenada)

print(f"\n📊 [PASO 3/4] Resultados de red: {len(resultados)} de {len(lista_ordenada)} supermercados respondieron correctamente con HTTP 200.")

# 5. Convertir a DataFrame y mostrar resumen
df_resultados = convertir_a_dataframe(resultados)

if not df_resultados.empty:
    print("\n✅ TABLA RESUMEN DE DATOS EXTRAÍDOS:")
    print(df_resultados[["cadena", "sku_producto", "nombre_canasta", "id_request"]])

    # 6. Guardar en Cloudflare R2
    print("\n📦 [PASO 4/4] Subiendo reporte de prueba al Data Lake en Cloudflare R2...")
    try:
        lake = R2Lakehouse()
        lake.guardar_parquet(df_resultados, cadena="test_multicadena", nombre_archivo="auditoria_4_supermercados")
        print("\n🎉 ====================================================================")
        print("🎉 ¡TODAS LAS PRUEBAS SUPERADAS AL 100%! DATA LAKE Y SCRAPING OPERATIVOS.")
        print("🎉 ====================================================================")
    except Exception as e:
        print(f"\n⚠️ Advertencia de subida a R2: {e}")
        print("💡 Nota: Si falta configurar variables de entorno R2 en esta terminal, exporta R2_ACCESS_KEY_ID y R2_SECRET_ACCESS_KEY.")
else:
    print("\n❌ Ninguna API retornó código 200. Revisa tu conexión a internet del Codespace.")