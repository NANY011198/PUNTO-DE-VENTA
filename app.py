import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Enlace de conexión a Supabase PostgreSQL
DATABASE_URL = "postgresql://postgres:ERIKa%2301020304DANy%2301@db.robhchusikbljnowrqmr.supabase.co:5432/postgres"

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventario (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) UNIQUE NOT NULL,
                unidad VARCHAR(100) NOT NULL,
                categoria VARCHAR(100) NOT NULL,
                cantidad NUMERIC NOT NULL DEFAULT 0,
                ultimo_precio NUMERIC NOT NULL DEFAULT 0
            );
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu (
                id SERIAL PRIMARY KEY,
                categoria VARCHAR(100) NOT NULL,
                nombre VARCHAR(255) UNIQUE NOT NULL,
                precio NUMERIC NOT NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                codigo_venta VARCHAR(100) NOT NULL,
                fecha VARCHAR(50) NOT NULL,
                hora VARCHAR(50) NOT NULL,
                metodo VARCHAR(50) NOT NULL,
                monto NUMERIC NOT NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gastos (
                id SERIAL PRIMARY KEY,
                fecha VARCHAR(50) NOT NULL,
                concepto VARCHAR(255) NOT NULL,
                monto NUMERIC NOT NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras (
                id SERIAL PRIMARY KEY,
                fecha VARCHAR(50) NOT NULL,
                factura VARCHAR(100) NOT NULL,
                proveedor VARCHAR(255) NOT NULL,
                total NUMERIC NOT NULL
            );
        ''')

        # Insertar menú base inicial si está vacío
        cursor.execute("SELECT COUNT(*) FROM menu;")
        if cursor.fetchone()['count'] == 0:
            cursor.execute("INSERT INTO menu (categoria, nombre, precio) VALUES ('Pizzas', 'Pizza Pepperoni Grande', 8.99) ON CONFLICT DO NOTHING;")
            cursor.execute("INSERT INTO menu (categoria, nombre, precio) VALUES ('Pizzas', 'Pizza Suprema Grande', 10.99) ON CONFLICT DO NOTHING;")
            cursor.execute("INSERT INTO menu (categoria, nombre, precio) VALUES ('Entradas', 'Papas Fritas', 3.50) ON CONFLICT DO NOTHING;")
            cursor.execute("INSERT INTO menu (categoria, nombre, precio) VALUES ('Bebidas', 'Soda 1.25L', 2.00) ON CONFLICT DO NOTHING;")

        # Insertar inventario base inicial si está vacío
        cursor.execute("SELECT COUNT(*) FROM inventario;")
        if cursor.fetchone()['count'] == 0:
            cursor.execute("INSERT INTO inventario (nombre, unidad, categoria, cantidad, ultimo_precio) VALUES ('Queso Mozzarella', 'Bloque / Kg', 'Lácteos / Quesos', 25, 0.75) ON CONFLICT DO NOTHING;")
            cursor.execute("INSERT INTO inventario (nombre, unidad, categoria, cantidad, ultimo_precio) VALUES ('Harina de Trigo Especial', 'Saco 25kg', 'Harinas / Masas', 10, 18.50) ON CONFLICT DO NOTHING;")
            cursor.execute("INSERT INTO inventario (nombre, unidad, categoria, cantidad, ultimo_precio) VALUES ('Pepperoni Rebanado', 'Caja / Paquete', 'Embutidos / Carnes', 8, 12.00) ON CONFLICT DO NOTHING;")

        conn.commit()
        cursor.close()
        conn.close()
        print("Base de datos de Supabase inicializada correctamente.")
    except Exception as e:
        print("Error al inicializar la base de datos:", e)

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ventas', methods=['GET', 'POST'])
def handle_ventas():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute("INSERT INTO ventas (codigo_venta, fecha, hora, metodo, monto) VALUES (%s, %s, %s, %s, %s)",
                       (data['id'], data['fecha'], data['hora'], data['metodo'], data['monto']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "ok"})
    else:
        cursor.execute("SELECT * FROM ventas;")
        ventas = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(ventas)

@app.route('/api/gastos', methods=['GET', 'POST'])
def handle_gastos():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute("INSERT INTO gastos (fecha, concepto, monto) VALUES (%s, %s, %s)",
                       (data['fecha'], data['concepto'], data['monto']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "ok"})
    else:
        cursor.execute("SELECT * FROM gastos;")
        gastos = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(gastos)

@app.route('/api/compras', methods=['GET', 'POST'])
def handle_compras():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute("INSERT INTO compras (fecha, factura, proveedor, total) VALUES (%s, %s, %s, %s)",
                       (data['fecha'], data['factura'], data['proveedor'], data['totalGeneral']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "ok"})
    else:
        cursor.execute("SELECT * FROM compras;")
        compras = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(compras)

if __name__ == '__main__':
    app.run(debug=True)