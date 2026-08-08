import os
from datetime import date, datetime
from io import BytesIO
import boto3
import pandas as pd
from dotenv import load_dotenv
from core.http_engine import ArmoredHTTPEngine
from builders.jumbo import JumboBuilder
from builders.santaisabel import SantaIsabelBuilder

load_dotenv()
os.environ["ENV"] = "prod"

# Canasta Básica completa para el seguimiento diario
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

SUCURSAL = {
    "region": "Metropolitana",
    "comuna": "Santiago",
    "local": "Online RM"
}

def ejecutar_carga_diaria():
    print(f"🚀 [PROD] INICIANDO CARGA DIARIA: {datetime.now().isoformat()}")
    
    # Por ahora Cencosud; pronto sumamos LiderBuilder() y UnimarcBuilder() aquí
    builders = [JumboBuilder(), SantaIsabelBuilder()]
    engine = ArmoredHTTPEngine()
    todas_las_filas = []

    for builder in builders:
        print(f"\n📦 Procesando cadena: {builder.cadena.upper()}...")
        solicitudes = builder.generar_solicitudes(TERMINOS_CANASTA, SUCURSAL)
        resultados = engine.ejecutar_bloque(solicitudes)
        
        for req in resultados:
            raw_payload = req.get("raw_payload_json", "")
            filas = builder.parsear(raw_payload, req["sku_producto"], SUCURSAL)
            print(f"   -> {len(filas)} productos extraídos para '{req['sku_producto']}'")
            todas_las_filas.extend(filas)

    if todas_las_filas:
        df = pd.DataFrame(todas_las_filas)
        print(f"\n📊 Total consolidado: {len(df)} registros listos para el Data Lake.")
        
        fecha_hoy = date.today().isoformat()
        
        # Guardar respaldo local solo si estamos en un entorno con sistema de archivos temporal
        archivo_local = "ultimo_consolidado.csv"
        df.to_csv(archivo_local, index=False, encoding="utf-8-sig")

        # Subida obligatoria a Cloudflare R2
        print("☁️ Subiendo archivo Parquet a Cloudflare R2...")
        try:
            r2_endpoint = os.getenv("R2_ENDPOINT_URL") or os.getenv("R2_ENDPOINT")
            if r2_endpoint and not r2_endpoint.startswith("https://"):
                r2_endpoint = f"https://{r2_endpoint}"

            s3 = boto3.client(
                's3',
                endpoint_url=r2_endpoint,
                aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
                region_name='auto'
            )
            bucket_name = os.getenv("R2_BUCKET_NAME", "canasta-inteligente-lake")

            parquet_buffer = BytesIO()
            df.to_parquet(parquet_buffer, index=False)
            parquet_buffer.seek(0)

            object_key = f"bronze/consolidado/fecha_carga={fecha_hoy}/canasta_basica.parquet"
            
            s3.upload_fileobj(parquet_buffer, bucket_name, object_key)
            print(f"✅ ¡ÉXITO PRODUCTIVO! Archivo subido a R2 en: {object_key}")
            
            precios_validos = len(df[df["precio"] > 0])
            print(f"💰 Control de calidad: {precios_validos}/{len(df)} productos con precio > $0.")
            
        except Exception as e:
            print(f"❌ Error crítico al subir a R2: {e}")
            raise e
    else:
        print("❌ ALERTA: No se obtuvieron datos hoy.")

if __name__ == "__main__":
    ejecutar_carga_diaria()