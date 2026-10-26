import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_NAME = "charlies_pizza.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla de Inventario
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
    
    # Tabla de Menú / Platillos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            nombre TEXT UNIQUE NOT NULL,
            precio REAL NOT NULL
        )
    ''')

    # Tabla de Recetas (Ingredientes por Platillo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_id INTEGER NOT NULL,
            insumo_nombre TEXT NOT NULL,
            unidad TEXT NOT NULL,
            cantidad REAL NOT NULL,
            FOREIGN KEY(menu_id) REFERENCES menu(id) ON DELETE CASCADE
        )
    ''')

    # Tabla de Ventas
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

    # Tabla de Gastos de Caja Chica
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL
        )
    ''')

    # Tabla de Compras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            factura TEXT NOT NULL,
            proveedor TEXT NOT NULL,
            total REAL NOT NULL
        )
    ''')

    # Tabla de Proveedores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            telefono TEXT NOT NULL,
            categoria TEXT
        )
    ''')

    # Insertar datos base por defecto si la base está vacía
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

if __name__ == '__main__':
    app.run(debug=True)