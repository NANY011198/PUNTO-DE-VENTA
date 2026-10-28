import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_NAME = "charlies_pizza.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            unidad TEXT NOT NULL,
            categoria TEXT NOT NULL,
            cantidad REAL NOT NULL DEFAULT 0,
            ultimo_precio REAL NOT NULL DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            nombre TEXT UNIQUE NOT NULL,
            precio REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_venta TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            metodo TEXT NOT NULL,
            monto REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            factura TEXT NOT NULL,
            proveedor TEXT NOT NULL,
            total REAL NOT NULL
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR IGNORE INTO menu (categoria, nombre, precio) VALUES ('Pizzas', 'Pizza Pepperoni Grande', 8.99)")
        cursor.execute("INSERT OR IGNORE INTO menu (categoria, nombre, precio) VALUES ('Pizzas', 'Pizza Suprema Grande', 10.99)")
        cursor.execute("INSERT OR IGNORE INTO menu (categoria, nombre, precio) VALUES ('Entradas', 'Papas Fritas', 3.50)")
        cursor.execute("INSERT OR IGNORE INTO menu (categoria, nombre, precio) VALUES ('Bebidas', 'Soda 1.25L', 2.00)")

    cursor.execute("SELECT COUNT(*) FROM inventario")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR IGNORE INTO inventario (nombre, unidad, categoria, cantidad, ultimo_precio) VALUES ('Queso Mozzarella', 'Bloque / Kg', 'Lácteos / Quesos', 25, 0.75)")
        cursor.execute("INSERT OR IGNORE INTO inventario (nombre, unidad, categoria, cantidad, ultimo_precio) VALUES ('Harina de Trigo Especial', 'Saco 25kg', 'Harinas / Masas', 10, 18.50)")
        cursor.execute("INSERT OR IGNORE INTO inventario (nombre, unidad, categoria, cantidad, ultimo_precio) VALUES ('Pepperoni Rebanado', 'Caja / Paquete', 'Embutidos / Carnes', 8, 12.00)")

    conn.commit()
    conn.close()

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
        cursor.execute("INSERT INTO ventas (codigo_venta, fecha, hora, metodo, monto) VALUES (?, ?, ?, ?, ?)",
                       (data['id'], data['fecha'], data['hora'], data['metodo'], data['monto']))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    else:
        ventas = cursor.execute("SELECT * FROM ventas").fetchall()
        conn.close()
        return jsonify([dict(v) for v in ventas])

@app.route('/api/gastos', methods=['GET', 'POST'])
def handle_gastos():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute("INSERT INTO gastos (fecha, concepto, monto) VALUES (?, ?, ?)",
                       (data['fecha'], data['concepto'], data['monto']))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    else:
        gastos = cursor.execute("SELECT * FROM gastos").fetchall()
        conn.close()
        return jsonify([dict(g) for g in gastos])

@app.route('/api/compras', methods=['GET', 'POST'])
def handle_compras():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute("INSERT INTO compras (fecha, factura, proveedor, total) VALUES (?, ?, ?, ?)",
                       (data['fecha'], data['factura'], data['proveedor'], data['totalGeneral']))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    else:
        compras = cursor.execute("SELECT * FROM compras").fetchall()
        conn.close()
        return jsonify([dict(c) for c in compras])

if __name__ == '__main__':
    app.run(debug=True)