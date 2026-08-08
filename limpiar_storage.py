import os
import boto3
from dotenv import load_dotenv

load_dotenv()

# Buscamos indistintamente R2_ENDPOINT_URL o R2_ENDPOINT para evitar problemas de nombres
r2_endpoint = os.getenv("R2_ENDPOINT_URL") or os.getenv("R2_ENDPOINT")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket_name = os.getenv("R2_BUCKET_NAME", "canasta-inteligente-lake")

print(f"🔍 [DEBUG] Endpoint leído: {r2_endpoint}")
print(f"🔍 [DEBUG] Access Key leída: {'Configurada' if access_key else 'VACÍA O NO ENCONTRADA'}")
print(f"🔍 [DEBUG] Bucket: {bucket_name}")

if not r2_endpoint:
    raise ValueError("❌ Error crítico: No se encontró R2_ENDPOINT ni R2_ENDPOINT_URL en el archivo .env")

if not r2_endpoint.startswith("https://"):
    r2_endpoint = f"https://{r2_endpoint}"

s3 = boto3.client(
    's3',
    endpoint_url=r2_endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name='auto'
)

def limpiar_bucket_r2():
    print(f"\n🧹 Conectando al bucket R2: {bucket_name}...")
    try:
        paginator = s3.get_paginator('list_objects_v2')
        total_eliminados = 0
        
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                
                for i in range(0, len(objects_to_delete), 1000):
                    chunk = objects_to_delete[i:i+1000]
                    s3.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': chunk}
                    )
                    total_eliminados += len(chunk)
                    print(f"🗑️ Eliminados {total_eliminados} archivos...")
                    
        print("✅ ¡Storage de R2 completamente limpio!")
    except Exception as e:
        print(f"❌ Error al limpiar el storage: {e}")

if __name__ == "__main__":
    limpiar_bucket_r2()