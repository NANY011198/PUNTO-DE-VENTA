import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Conexión a la base de datos PostgreSQL en Render
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM categorias ORDER BY id;")
        categorias = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('index.html', categorias=categorias)
    except Exception as e:
        return render_template('index.html', categorias=[], error=str(e))

@app.route('/api/platillos/<int:categoria_id>')
def get_platillos(categoria_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM productos WHERE categoria_id = %s;", (categoria_id,))
        platillos = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(platillos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vender', methods=['POST'])
def vender():
    try:
        data = request.get_json()
        items = data.get('items', [])
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Registrar venta en la BD
        total_venta = sum(item['precio'] * item['cantidad'] for item in items)
        cur.execute("INSERT INTO ventas (total) VALUES (%s) RETURNING id;", (total_venta,))
        venta_id = cur.fetchone()['id']
        
        for item in items:
            cur.execute(
                "INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario) VALUES (%s, %s, %s, %s);",
                (venta_id, item['id'], item['cantidad'], item['precio'])
            )
            
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "message": "¡Venta registrada con éxito!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# RUTAS DE LOS MÓDULOS ERP
@app.route('/caja')
def caja():
    return render_template('caja.html')

@app.route('/inventario')
def inventario():
    return render_template('inventario.html')

@app.route('/menu')
def menu_recetas():
    return render_template('menu.html')

@app.route('/compras')
def compras():
    return render_template('compras.html')

@app.route('/reportes')
def reportes():
    return render_template('reportes.html')

if __name__ == '__main__':
    app.run(debug=True)