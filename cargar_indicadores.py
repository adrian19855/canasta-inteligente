import duckdb
import pandas as pd
import requests
from datetime import date

def obtener_indicadores():
    print("Conectando con la API de indicadores económicos...")
    
    url = "https://mindicador.cl/api"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        uf = data.get('uf', {}).get('valor')
        dolar = data.get('dolar', {}).get('valor')
        ipc = data.get('ipc', {}).get('valor')
        
        # Obtenemos la fecha actual sin hora (solo DATE)
        hoy = date.today()
        
        print(f"Fecha: {hoy} -> UF: {uf}, Dólar: {dolar}, IPC: {ipc}")
        
        # Conectamos a DuckDB
        con = duckdb.connect('canasta.duckdb')
        
        # Creamos la tabla usando DATE en lugar de TIMESTAMP
        con.execute("""
            CREATE TABLE IF NOT EXISTS indicadores_historicos (
                fecha DATE,
                uf DOUBLE,
                dolar DOUBLE,
                ipc DOUBLE
            )
        """)
        
        # Verificamos si ya existe un registro para el día de hoy
        existe = con.execute("SELECT COUNT(*) FROM indicadores_historicos WHERE fecha = ?", [hoy]).fetchone()[0]
        
        if existe > 0:
            print(f"Ya existe un registro para la fecha {hoy}. Actualizando...")
            con.execute("""
                UPDATE indicadores_historicos 
                SET uf = ?, dolar = ?, ipc = ? 
                WHERE fecha = ?
            """, [uf, dolar, ipc, hoy])
        else:
            print(f"No existe registro para {hoy}. Insertando nuevo...")
            con.execute("""
                INSERT INTO indicadores_historicos (fecha, uf, dolar, ipc) 
                VALUES (?, ?, ?, ?)
            """, [hoy, uf, dolar, ipc])
            
        print("¡Operación completada con éxito en DuckDB!")
        
        # Mostramos el historial completo ordenado por fecha
        resultado = con.execute("SELECT * FROM indicadores_historicos ORDER BY fecha DESC").fetchdf()
        print("\nHistorial actual en la base de datos:")
        print(resultado)
        
        con.close()
    else:
        print("Error al conectar con la API de indicadores.")

if __name__ == "__main__":
    obtener_indicadores()