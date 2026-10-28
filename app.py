import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Enlace de conexión a Supabase PostgreSQL
DATABASE_URL = "postgresql://postgres:ERIKa%2301020304DANy%2301@db.robhchusikbljnowrqmr.supabase.co:5432/postgres"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

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
                precio NUMERIC NOT NULL,
                receta TEXT DEFAULT ''
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

        conn.commit()
        cursor.close()
        conn.close()
        print("Base de datos de Supabase verificada/inicializada correctamente.")
    except Exception as e:
        print("Error al inicializar la base de datos:", e)

init_db()

@app.route('/')
def index():
    return render_template('index.html')

# --- API INVENTARIO ---
@app.route('/api/inventario', methods=['GET', 'POST', 'DELETE'])
def handle_inventario():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute('''
            INSERT INTO inventario (nombre, unidad, categoria, cantidad, ultimo_precio)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (nombre) DO UPDATE 
            SET unidad = EXCLUDED.unidad,
                categoria = EXCLUDED.categoria,
                cantidad = EXCLUDED.cantidad,
                ultimo_precio = EXCLUDED.ultimo_precio;
        ''', (data['nombre'], data['unidad'], data['categoria'], data['cantidad'], data.get('ultimo_precio', 0)))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "ok"})
    elif request.method == 'DELETE':
        nombre = request.args.get('nombre')
        cursor.execute("DELETE FROM inventario WHERE nombre = %s;", (nombre,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "deleted"})
    else:
        cursor.execute("SELECT * FROM inventario ORDER BY id ASC;")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(items)

# --- API MENU ---
@app.route('/api/menu', methods=['GET', 'POST', 'DELETE'])
def handle_menu():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        receta_str = str(data.get('receta', ''))
        cursor.execute('''
            INSERT INTO menu (categoria, nombre, precio, receta)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (nombre) DO UPDATE 
            SET categoria = EXCLUDED.categoria,
                precio = EXCLUDED.precio,
                receta = EXCLUDED.receta;
        ''', (data['categoria'], data['nombre'], data['precio'], receta_str))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "ok"})
    elif request.method == 'DELETE':
        nombre = request.args.get('nombre')
        cursor.execute("DELETE FROM menu WHERE nombre = %s;", (nombre,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "deleted"})
    else:
        cursor.execute("SELECT * FROM menu ORDER BY id ASC;")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(items)

# --- API VENTAS & DESCUENTO DE STOCK ---
@app.route('/api/ventas', methods=['GET', 'POST'])
def handle_ventas():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        # 1. Registrar Venta
        cursor.execute("INSERT INTO ventas (codigo_venta, fecha, hora, metodo, monto) VALUES (%s, %s, %s, %s, %s)",
                       (data['id'], data['fecha'], data['hora'], data['metodo'], data['monto']))
        
        # 2. Descontar Stock si se envian los items vendidos
        items = data.get('items', [])
        for item in items:
            # Obtener la receta del platillo
            cursor.execute("SELECT receta FROM menu WHERE nombre = %s;", (item['nombre'],))
            row = cursor.fetchone()
            if row and row['receta']:
                # Ejemplo de formato receta en texto: "Queso Mozzarella (1), Harina (1)"
                partes = row['receta'].split(',')
                for p in partes:
                    if '(' in p and ')' in p:
                        insumo_nom = p.split('(')[0].strip()
                        cant_str = p.split('(')[1].replace(')', '').strip()
                        try:
                            cant_insumo = float(cant_str.split()[0]) * float(item['cantidad'])
                            cursor.execute("UPDATE inventario SET cantidad = GREATEST(0, cantidad - %s) WHERE nombre = %s;", (cant_insumo, insumo_nom))
                        except Exception:
                            pass

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "ok"})
    else:
        cursor.execute("SELECT * FROM ventas ORDER BY id DESC;")
        ventas = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(ventas)

# --- API GASTOS ---
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
        cursor.execute("SELECT * FROM gastos ORDER BY id DESC;")
        gastos = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(gastos)

# --- API COMPRAS ---
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
        cursor.execute("SELECT * FROM compras ORDER BY id DESC;")
        compras = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(compras)

if __name__ == '__main__':
    app.run(debug=True)