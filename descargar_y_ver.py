import os
import boto3
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

r2_endpoint = os.getenv("R2_ENDPOINT_URL") or os.getenv("R2_ENDPOINT")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket_name = os.getenv("R2_BUCKET_NAME", "canasta-inteligente-lake")

if r2_endpoint and not r2_endpoint.startswith("https://"):
    r2_endpoint = f"https://{r2_endpoint}"

s3 = boto3.client(
    's3',
    endpoint_url=r2_endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name='auto'
)

def ver_datos_desde_r2():
    print(f"☁️ Conectando a R2 para listar archivos en '{bucket_name}'...")
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' not in response:
            print("❌ El bucket en R2 está vacío.")
            return

        # Buscamos los archivos parquet almacenados
        archivos = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.parquet')]
        
        if not archivos:
            print("⚠️ No se encontraron archivos .parquet en R2.")
            return

        # Seleccionamos el último archivo subido
        ultimo_archivo = sorted(archivos)[-1]
        print(f"📥 Descargando archivo desde R2: {ultimo_archivo}")

        obj = s3.get_object(Bucket=bucket_name, Key=ultimo_archivo)
        df = pd.read_parquet(BytesIO(obj['Body'].read()))

        print(f"\n📊 ¡Éxito! Total de registros recuperados desde la nube: {len(df)}")
        print("\n🔍 Muestra de los primeros productos detectados:")
        print(df[["cadena", "nombre_canasta", "nombre_detectado", "region", "comuna"]].head(10))
        
        print("\n📦 Resumen de registros por supermercado:")
        print(df["cadena"].value_counts())
        
        # Guardar copia local en CSV para revisión manual fácil
        output_csv = "ultimo_consolidado.csv"
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(f"\n💾 Copia local guardada exitosamente en '{output_csv}' (puedes abrirlo y revisarlo como Excel).")

    except Exception as e:
        print(f"❌ Error al conectar o descargar desde R2: {e}")

if __name__ == "__main__":
    ver_datos_desde_r2()