import os
import pandas as pd
from core.http_engine import ArmoredHTTPEngine
from builders.lider import LiderBuilder

print("🔍 [DEBUG] INICIANDO PRUEBA AISLADA PARA LIDER...")

os.environ["ENV"] = "dev"

TERMINOS_PRUEBA = ["arroz 1kg"]
LOCAL_PRUEBA = {
    "local": "Lider Online RM",
    "region": "Metropolitana",
    "comuna": "Santiago",
}

builder = LiderBuilder()

# Usamos el nombre de método estandarizado correcto: 'generar_solicitudes'
solicitudes = builder.generar_solicitudes(TERMINOS_PRUEBA, LOCAL_PRUEBA)

print(f"🌐 Consultando URL de Lider: {solicitudes[0]['url']}")
engine = ArmoredHTTPEngine()
resultados_raw = engine.ejecutar_bloque(solicitudes)

for req in resultados_raw:
    raw_html = req.get("raw_payload_json", "")
    print(f"\n📄 [DEBUG] Tamaño del HTML descargado: {len(raw_html)} caracteres.")
    
    if len(raw_html) < 500:
        print("⚠️ ALERTA: El HTML recibido es muy pequeño. Es probable que Lider haya bloqueado la IP o devuelto error.")
        print(f"Contenido recibido: {raw_html[:300]}")
    else:
        print("✅ HTML descargado correctamente. Probando parseo...")

    filas = builder.parsear(raw_html, req["sku_producto"], LOCAL_PRUEBA)
    print(f"📊 Productos extraídos por Lider: {len(filas)}")
    
    if filas:
        df_test = pd.DataFrame(filas)
        print("\nMuestra de productos detectados:")
        print(df_test[["nombre_canasta", "nombre_detectado", "sku_producto"]].head(10))
    else:
        print("❌ El parser devolvió 0 productos reales (cayó en el fallback).")