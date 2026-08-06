import os
from core.http_engine import ArmoredHTTPEngine
from core.r2_storage import R2Lakehouse
from builders.base import crear_solicitud_estandar, convertir_a_dataframe

# 1. Configuramos el ambiente en DEV
os.environ["ENV"] = "dev"

print("🔥 --- INICIANDO PRUEBA DE HUMO (SMOKE TEST) --- 🔥")

# 2. Reemplaza esta URL y SKU por UNO REAL que tengas en tu archivo 'scraping_jumbo_bronze.py'
# (Aquí te pongo la estructura de Cencosud por defecto para probar)
SKU_REAL = "102938"  # <-- PON AQUÍ UN SKU REAL DE TU SCRIPT ANTIGUO
URL_REAL = f"https://sm-api.cencosud.com/catalog/api/v1/products/{SKU_REAL}"

solicitud_prueba = crear_solicitud_estandar(
    cadena="jumbo",
    sku_producto=SKU_REAL,
    nombre_canasta="Producto de Prueba Humo",
    url=URL_REAL,
    region="RM",
    comuna="Santiago",
    headers_custom={
        "Accept": "application/json",
        "apikey": "WlDftCF3wWMb85z7f0aG0gYc61QGqfN8"  # Reemplaza si en tu script antiguo usabas otra
    }
)

# 3. Probamos el Motor HTTP (que haga el GET con sesión y headers reales)
print(f"🌐 [1/3] Enviando petición al Motor HTTP para SKU: {SKU_REAL}...")
engine = ArmoredHTTPEngine()
resultados = engine.ejecutar_bloque([solicitud_prueba])

if not list(resultados):
    print("❌ [FALLO] La API no devolvió datos o bloqueó la petición. ¡Revisemos la URL del script antiguo!")
else:
    print("✅ [2/3] ¡ÉXITO! Recibimos respuesta JSON de la API.")
    
    # 4. Probamos subir ese único resultado a Cloudflare R2
    df_resultado = convertir_a_dataframe(resultados)
    print("📦 [3/3] Probando subida del DataFrame a Cloudflare R2...")
    
    try:
        lake = R2Lakehouse()
        lake.guardar_parquet(df_resultado, cadena="test_humo", nombre_archivo="smoke_test_001")
        print("🎉 ¡PRUEBA DE HUMO SUPERADA Al 100%! Motor HTTP y Data Lake R2 operativos.")
    except Exception as e:
        print(f"❌ Error al conectar o subir a R2: {e}")
        print("💡 Recuerda tener cargados tus secretos de R2 en la terminal si estás en sesión nueva.")