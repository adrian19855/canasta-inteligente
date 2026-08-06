from datetime import date
import pandas as pd

class StateManager:
    """
    Filtro de idempotencia. Evita raspar productos ya descargados en el día
    mediante una resta de conjuntos (Anti-Join).
    """
    def __init__(self, lakehouse):
        self.lake = lakehouse

    def obtener_delta_pendientes(self, df_matriz_ideal: pd.DataFrame, cadena: str, fecha_carga: str = None) -> pd.DataFrame:
        if df_matriz_ideal.empty:
            return df_matriz_ideal

        if not fecha_carga:
            fecha_carga = date.today().isoformat()

        print(f"🔍 [STATE MANAGER - {cadena.upper()}] Verificando historial del día ({fecha_carga})...")

        try:
            query = f"""
                SELECT DISTINCT id_request 
                FROM read_parquet('s3://canasta-inteligente-lake/{self.lake.ambiente}/bronze/cadena={cadena.lower()}/fecha_carga={fecha_carga}/*.parquet', hive_partitioning=1)
            """
            df_descargados = self.lake.consultar_sql(query)
            print(f"📦 [STATE MANAGER] Se encontraron {len(df_descargados)} registros ya guardados hoy.")

        except Exception:
            print("🆕 [STATE MANAGER] Primera carga del día para esta cadena. Cero registros previos.")
            return df_matriz_ideal

        if df_descargados.empty:
            return df_matriz_ideal

        # Resta (Anti-Join) usando id_request
        df_delta = df_matriz_ideal.merge(
            df_descargados,
            on="id_request",
            how="left",
            indicator=True
        )
        df_delta = df_delta[df_delta["_merge"] == "left_only"].drop(columns=["_merge"])

        ahorro = len(df_matriz_ideal) - len(df_delta)
        print(f"⚡ [DELTA] Total: {len(df_matriz_ideal)} | Omitidos: {ahorro} | Pendientes por raspar: {len(df_delta)}")
        return df_delta