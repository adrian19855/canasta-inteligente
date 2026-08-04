import duckdb
import requests
from datetime import datetime

def cargar_uf_mensual():
    print("Conectando con la API para la serie de UF...")
    url = "https://mindicador.cl/api/uf"
    response = requests.get(url, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        serie = data.get('serie', [])
        
        if not serie:
            print("No se encontraron registros de UF.")
            return

        con = duckdb.connect('canasta.duckdb')
        
        # Tabla unificada
        con.execute("""
            CREATE TABLE IF NOT EXISTS indicadores_historicos (
                fecha DATE PRIMARY KEY,
                uf DOUBLE,
                dolar DOUBLE,
                ipc DOUBLE
            )
        """)
        
        print(f"Procesando e insertando {len(serie)} registros de UF...")
        
        for item in serie:
            fecha_str = item['fecha'][:10] # Formato YYYY-MM-DD
            valor_uf = item['valor']
            
            # Insertamos la UF; si la fecha ya existe, actualizamos solo la columna uf
            con.execute("""
                INSERT INTO indicadores_historicos (fecha, uf) 
                VALUES (?, ?)
                ON CONFLICT (fecha) DO UPDATE SET uf = EXCLUDED.uf
            """, [fecha_str, valor_uf])
            
        print("¡Proceso mensual de UF completado con éxito!")
        
        resultado = con.execute("SELECT * FROM indicadores_historicos ORDER BY fecha DESC LIMIT 5").fetchdf()
        print("\nVista previa de la tabla unificada:")
        print(resultado)
        
        con.close()
    else:
        print("Error al conectar con la API de UF.")

if __name__ == "__main__":
    cargar_uf_mensual()