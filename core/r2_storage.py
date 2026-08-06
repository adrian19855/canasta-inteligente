import os
from datetime import date
import duckdb
import pandas as pd
from dotenv import load_dotenv

# 1. Cargar variables del archivo .env obligatoriamente
load_dotenv()

class R2Lakehouse:
    """
    Conector al Data Lake en Cloudflare R2 utilizando DuckDB y la API S3.
    Operaciones 100% en memoria hacia formato Parquet.
    """
    def __init__(self):
        self.ambiente = os.getenv("ENV", "dev")
        self.bucket = "canasta-inteligente-lake"
        self.con = self._iniciar_conexion()

    def _iniciar_conexion(self):
        con = duckdb.connect()
        con.execute("INSTALL httpfs; LOAD httpfs;")
        
        access_key = os.getenv("R2_ACCESS_KEY_ID", "")
        secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "")
        
        # Limpiamos el endpoint por si trae https:// o barras al final
        endpoint = os.getenv("R2_ENDPOINT", "")
        endpoint_limpio = endpoint.replace("https://", "").replace("http://", "").rstrip("/")

        con.execute(f"""
            CREATE SECRET IF NOT EXISTS r2_secret (
                TYPE S3,
                KEY_ID '{access_key}',
                SECRET '{secret_key}',
                ENDPOINT '{endpoint_limpio}',
                REGION 'auto',
                URL_STYLE 'path'
            );
        """)
        return con

    def obtener_ruta_bronze(self, cadena: str, fecha_carga: str = None) -> str:
        if not fecha_carga:
            fecha_carga = date.today().isoformat()
        return f"s3://{self.bucket}/{self.ambiente}/bronze/cadena={cadena.lower()}/fecha_carga={fecha_carga}"

    def guardar_parquet(self, df: pd.DataFrame, cadena: str, nombre_archivo: str):
        if df.empty:
            print(f"⚠️ [{cadena.upper()}] DataFrame vacío, se omite el guardado.")
            return

        ruta_base = self.obtener_ruta_bronze(cadena)
        ruta_completa = f"{ruta_base}/{nombre_archivo}.parquet"
        
        print(f"📦 [R2 WRITE -> {self.ambiente.upper()}] Subiendo {len(df)} filas a: {ruta_completa}")
        self.con.execute(f"COPY df TO '{ruta_completa}' (FORMAT PARQUET, COMPRESSION 'SNAPPY');")
        print("✅ ¡Archivo Parquet guardado con éxito en Cloudflare R2!")

    def consultar_sql(self, sql_query: str) -> pd.DataFrame:
        return self.con.sql(sql_query).df()