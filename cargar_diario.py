import duckdb
import requests
from datetime import date

def cargar_indicadores_diarios():
    print("Conectando con la API para indicadores diarios...")
    url = "https://mindicador.cl/api"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        dolar = data.get('dolar', {}).get('valor')
        ipc = data.get('ipc', {}).get('valor')
        hoy = date.today()
        
        print(f"Fecha: {hoy} -> Dólar: {dolar}, IPC: {ipc}")
        
        con = duckdb.connect('canasta.duckdb')
        
        # Aseguramos que la tabla exista
        con.execute("""
            CREATE TABLE IF NOT EXISTS indicadores_historicos (
                fecha DATE PRIMARY KEY,
                uf DOUBLE,
                dolar DOUBLE,
                ipc DOUBLE
            )
        """)
        
        # Verificamos si ya existe el registro de hoy
        existe = con.execute("SELECT COUNT(*) FROM indicadores_historicos WHERE fecha = ?", [hoy]).fetchone()[0]
        
        if existe > 0:
            print(f"Actualizando Dólar e IPC para el registro existente de hoy ({hoy})...")
            con.execute("""
                UPDATE indicadores_historicos 
                SET dolar = ?, ipc = ? 
                WHERE fecha = ?
            """, [dolar, ipc, hoy])
        else:
            print(f"Insertando nueva fila para hoy ({hoy}) con Dólar e IPC...")
            con.execute("""
                INSERT INTO indicadores_historicos (fecha, dolar, ipc) 
                VALUES (?, ?, ?)
            """, [hoy, dolar, ipc])
            
        print("¡Proceso diario completado con éxito!")
        
        resultado = con.execute("SELECT * FROM indicadores_historicos ORDER BY fecha DESC LIMIT 5").fetchdf()
        print("\nVista previa de la tabla unificada:")
        print(resultado)
        
        con.close()
    else:
        print("Error al conectar con la API general.")

if __name__ == "__main__":
    cargar_indicadores_diarios()