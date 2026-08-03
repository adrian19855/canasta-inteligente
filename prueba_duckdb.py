import duckdb
import pandas as pd

# 1. Conectar a una base de datos DuckDB local (se crea un archivo llamado 'canasta.duckdb')
con = duckdb.connect('canasta.duckdb')

# 2. Crear una tabla de prueba con datos simulados de la Canasta Básica por Comuna
con.execute("""
    CREATE OR REPLACE TABLE precios_canasta (
        producto VARCHAR,
        comuna VARCHAR,
        precio INT,
        fuente VARCHAR
    );
""")

# 3. Insertar datos de ejemplo
datos_ejemplo = [
    ('Pan Amasado (1kg)', 'Santiago', 2100, 'Supermercado A'),
    ('Pan Amasado (1kg)', 'Santiago', 1800, 'Feria Libre'),
    ('Pan Amasado (1kg)', 'Maipú', 1650, 'Feria Libre'),
    ('Pan Amasado (1kg)', 'Las Condes', 2400, 'Supermercado A'),
    ('Leche Entera (1L)', 'Santiago', 1050, 'Supermercado B'),
    ('Leche Entera (1L)', 'Maipú', 990, 'Feria Libre'),
    ('Leche Entera (1L)', 'Las Condes', 1150, 'Supermercado B')
]

con.executemany("INSERT INTO precios_canasta VALUES (?, ?, ?, ?)", datos_ejemplo)

print("--- DATOS CARGADOS EXITOSAMENTE EN DUCKDB ---")

# 4. Ejecutar una consulta analítica: Encontrar el precio promedio por producto y el precio mínimo por comuna
print("\nConsulta 1: Precio promedio de la canasta por producto:")
resultado_promedio = con.execute("""
    SELECT producto, ROUND(AVG(precio), 1) as precio_promedio, MIN(precio) as precio_minimo
    FROM precios_canasta
    GROUP BY producto;
""").fetchdf()

print(resultado_promedio)

# Cerramos la conexión
con.close()
