import os
from io import BytesIO
import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def consultar_parquet_en_r2():
    print("☁️ Conectando a Cloudflare R2 para buscar el archivo Parquet en la nube...")
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

        response = s3.list_objects_v2(Bucket=bucket_name)

        if 'Contents' not in response:
            print("❌ El bucket en R2 está vacío. No hay archivos Parquet cargados.")
            return

        archivos = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.parquet')]

        if not archivos:
            print("⚠️ No se encontraron archivos .parquet en el bucket de R2.")
            return

        # Seleccionamos el último archivo subido según fecha/hora de la ruta
        ultimo_archivo = sorted(archivos)[-1]
        print(f"📥 Descargando archivo Parquet desde la nube: {ultimo_archivo}...")

        obj = s3.get_object(Bucket=bucket_name, Key=ultimo_archivo)
        df = pd.read_parquet(BytesIO(obj['Body'].read()))

        print(f"\n📊 ¡Éxito! Total de registros recuperados desde R2: {len(df)}")

        # Imprimimos las 10 primeras filas incluyendo el PRECIO
        print("\n🔍 Primeras 10 filas del Parquet en la nube (con PRECIO):")
        print(df[["cadena", "nombre_canasta", "nombre_detectado", "precio", "region", "comuna"]].head(10))

        print("\n📦 Resumen de registros por supermercado:")
        print(df["cadena"].value_counts())

        # Verificación automática de precios > 0
        if "precio" in df.columns:
            precios_validos = len(df[df["precio"] > 0])
            print(f"\n💰 VERIFICACIÓN DE PRECIOS: {precios_validos} de {len(df)} productos tienen un precio mayor a $0.")
        else:
            print("\n❌ ALERTA: La columna 'precio' no está en el archivo Parquet.")

    except Exception as e:
        print(f"❌ Error al conectar o leer desde R2: {e}")

if __name__ == "__main__":
    consultar_parquet_en_r2()