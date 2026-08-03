import duckdb
import pandas as pd
import requests

def obtener_indicadores():
    print("Conectando con la API de indicadores económicos...")
    
    # Usaremos una API pública y gratuita de indicadores financieros de Chile
    url = "https://mindicador.cl/api"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        
        # Extraemos valores clave para el análisis de la canasta
        uf = data.get('uf', {}).get('valor')
        dolar = data.get('dolar', {}).get('valor')
        ipc = data.get('ipc', {}).get('valor')
        
        print(f"Valores obtenidos -> UF: {uf}, Dólar: {dolar}, IPC: {ipc}")
        
        # Creamos un DataFrame con los datos
        df = pd.DataFrame([{
            'fecha': pd.Timestamp.now(),
            'uf': uf,
            'dolar': dolar,
            'ipc': ipc
        }])
        
        # Conectamos a DuckDB (creará o actualizará el archivo canasta.duckdb)
        con = duckdb.connect('canasta.duckdb')
        
        # Creamos la tabla si no existe y guardamos los datos
        con.execute("""
            CREATE TABLE IF NOT EXISTS indicadores_historicos (
                fecha TIMESTAMP,
                uf DOUBLE,
                dolar DOUBLE,
                ipc DOUBLE
            )
        """)
        
        con.execute("INSERT INTO indicadores_historicos SELECT * FROM df")
        print("¡Datos guardados exitosamente en DuckDB!")
        
        # Consultamos la tabla para verificar
        resultado = con.execute("SELECT * FROM indicadores_historicos").fetchdf()
        print("\nHistorial actual en la base de datos:")
        print(resultado)
        
        con.close()
    else:
        print("Error al conectar con la API de indicadores.")

if __name__ == "__main__":
    obtener_indicadores()