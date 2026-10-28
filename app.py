import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Configuración de conexión a Supabase PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL', "postgresql://postgres:ERIKa%2301020304DANy%2301@db.robhchusikbljnowrqmr.supabase.co:5432/postgres")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Crear tablas si no existen
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventario (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                unidad VARCHAR(100) NOT NULL,
                categoria VARCHAR(100) NOT NULL,
                cantidad NUMERIC DEFAULT 0,
                ultimo_precio NUMERIC DEFAULT 0
            );
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu (
                id SERIAL PRIMARY KEY,
                categoria VARCHAR(100) NOT NULL,
                nombre VARCHAR(255) NOT NULL,
                precio NUMERIC NOT NULL,
                receta TEXT
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                codigo_venta VARCHAR(100),
                fecha DATE NOT NULL,
                hora VARCHAR(50),
                metodo VARCHAR(50),
                monto NUMERIC NOT NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gastos (
                id SERIAL PRIMARY KEY,
                fecha DATE NOT NULL,
                concepto VARCHAR(255) NOT NULL,
                monto NUMERIC NOT NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras (
                id SERIAL PRIMARY KEY,
                fecha DATE NOT NULL,
                factura VARCHAR(100) NOT NULL,
                proveedor VARCHAR(255) NOT NULL,
                total NUMERIC NOT NULL
            );
        ''')

        conn.commit()
        cursor.close()
        conn.close()
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print("Error inicializando base de datos:", e)

init_db()

@app.route('/')
def index():
    return render_template('index.html')

# --- ROUTE INVENTARIO ---
@app.route('/api/inventario', methods=['GET', 'POST', 'DELETE'])
def handle_inventario():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            data = request.json
            nombre = data['nombre'].strip()
            unidad = data['unidad']
            categoria = data['categoria']
            cantidad = float(data.get('cantidad', 0))
            precio = float(data.get('ultimo_precio', 0))

            # Verificar si existe previamente
            cursor.execute("SELECT id FROM inventario WHERE LOWER(nombre) = LOWER(%s);", (nombre,))
            item = cursor.fetchone()

            if item:
                cursor.execute('''
                    UPDATE inventario 
                    SET unidad = %s, categoria = %s, cantidad = %s, ultimo_precio = %s 
                    WHERE id = %s;
                ''', (unidad, categoria, cantidad, precio, item['id']))
            else:
                cursor.execute('''
                    INSERT INTO inventario (nombre, unidad, categoria, cantidad, ultimo_precio)
                    VALUES (%s, %s, %s, %s, %s);
                ''', (nombre, unidad, categoria, cantidad, precio))

            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            print("Error en POST inventario:", e)
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            nombre = request.args.get('nombre')
            cursor.execute("DELETE FROM inventario WHERE nombre = %s;", (nombre,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"status": "deleted"}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": str(e)}), 500

    else:
        cursor.execute("SELECT * FROM inventario ORDER BY id ASC;")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(items)

# --- ROUTE MENU ---
@app.route('/api/menu', methods=['GET', 'POST', 'DELETE'])
def handle_menu():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            data = request.json
            categoria = data['categoria']
            nombre = data['nombre'].strip()
            precio = float(data['precio'])
            receta = data.get('receta', '')

            cursor.execute("SELECT id FROM menu WHERE LOWER(nombre) = LOWER(%s);", (nombre,))
            item = cursor.fetchone()

            if item:
                cursor.execute('''
                    UPDATE menu 
                    SET categoria = %s, precio = %s, receta = %s 
                    WHERE id = %s;
                ''', (categoria, precio, receta, item['id']))
            else:
                cursor.execute('''
                    INSERT INTO menu (categoria, nombre, precio, receta)
                    VALUES (%s, %s, %s, %s);
                ''', (categoria, nombre, precio, receta))

            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            nombre = request.args.get('nombre')
            cursor.execute("DELETE FROM menu WHERE nombre = %s;", (nombre,))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"status": "deleted"}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": str(e)}), 500

    else:
        cursor.execute("SELECT * FROM menu ORDER BY id ASC;")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(items)

# --- ROUTE VENTAS ---
@app.route('/api/ventas', methods=['GET', 'POST'])
def handle_ventas():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            data = request.json
            codigo = data.get('id', '')
            fecha = data.get('fecha')
            hora = data.get('hora', '')
            metodo = data.get('metodo', 'EFECTIVO')
            monto = float(data.get('monto', 0))

            cursor.execute('''
                INSERT INTO ventas (codigo_venta, fecha, hora, metodo, monto)
                VALUES (%s, %s, %s, %s, %s);
            ''', (codigo, fecha, hora, metodo, monto))

            # Descuento de stock según la receta
            items = data.get('items', [])
            for item in items:
                nombre_prod = item.get('nombre')
                cant_vendida = float(item.get('cantidad', 1))
                
                cursor.execute("SELECT receta FROM menu WHERE nombre = %s;", (nombre_prod,))
                menu_item = cursor.fetchone()
                if menu_item and menu_item['receta']:
                    ingredientes = menu_item['receta'].split(',')
                    for ing in ingredientes:
                        if '(' in ing and ')' in ing:
                            partes = ing.strip().split('(')
                            nom_insumo = partes[0].strip()
                            cant_req = float(partes[1].replace(')', '').strip())
                            total_descontar = cant_req * cant_vendida

                            cursor.execute('''
                                UPDATE inventario 
                                SET cantidad = GREATEST(0, cantidad - %s) 
                                WHERE LOWER(nombre) = LOWER(%s);
                            ''', (total_descontar, nom_insumo))

            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": str(e)}), 500

    else:
        cursor.execute("SELECT * FROM ventas ORDER BY id DESC;")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(items)

# --- ROUTE GASTOS ---
@app.route('/api/gastos', methods=['GET', 'POST'])
def handle_gastos():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            data = request.json
            fecha = data.get('fecha')
            concepto = data.get('concepto')
            monto = float(data.get('monto', 0))

            cursor.execute('''
                INSERT INTO gastos (fecha, concepto, monto)
                VALUES (%s, %s, %s);
            ''', (fecha, concepto, monto))

            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        cursor.execute("SELECT * FROM gastos ORDER BY id DESC;")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(items)

# --- ROUTE COMPRAS ---
@app.route('/api/compras', methods=['GET', 'POST'])
def handle_compras():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            data = request.json
            fecha = data.get('fecha')
            factura = data.get('factura')
            proveedor = data.get('proveedor')
            total = float(data.get('totalGeneral', 0))

            cursor.execute('''
                INSERT INTO compras (fecha, factura, proveedor, total)
                VALUES (%s, %s, %s, %s);
            ''', (fecha, factura, proveedor, total))

            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        cursor.execute("SELECT * FROM compras ORDER BY id DESC;")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(items)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)