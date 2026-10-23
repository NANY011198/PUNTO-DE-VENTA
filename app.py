import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuración de base de datos
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///punto_venta.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODELOS ====================

class Categoria(db.Model):
    __tablename__ = 'categoria'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    platillos = db.relationship('Platillo', backref='categoria', lazy=True)

class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    unidad = db.Column(db.String(20), default='Unidad')
    stock = db.Column(db.Float, default=0.0)
    precio_venta = db.Column(db.Float, nullable=True)
    es_directo = db.Column(db.Boolean, default=False)

class Platillo(db.Model):
    __tablename__ = 'platillo'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    es_compuesto = db.Column(db.Boolean, default=True)
    receta = db.relationship('Receta', backref='platillo', cascade="all, delete-orphan")

class Receta(db.Model):
    __tablename__ = 'receta'
    id = db.Column(db.Integer, primary_key=True)
    platillo_id = db.Column(db.Integer, db.ForeignKey('platillo.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad_requerida = db.Column(db.Float, nullable=False)
    producto = db.relationship('Producto')

# ==================== INICIALIZACIÓN AUTOMÁTICA EN RENDER ====================

def inicializar_base_datos():
    with app.app_context():
        db.create_all()
        if Categoria.query.count() == 0:
            cat_pizzas = Categoria(nombre="Pizzas")
            cat_entradas = Categoria(nombre="Entradas")
            cat_bebidas = Categoria(nombre="Bebidas")
            cat_postres = Categoria(nombre="Postres")
            db.session.add_all([cat_pizzas, cat_entradas, cat_bebidas, cat_postres])
            
            # Insumos base
            masa = Producto(nombre="Masa de Pizza", unidad="Gramos", stock=10000.0)
            salsa = Producto(nombre="Salsa de Tomate", unidad="Gramos", stock=5000.0)
            queso = Producto(nombre="Queso Mozzarella", unidad="Gramos", stock=5000.0)
            pepperoni = Producto(nombre="Pepperoni", unidad="Gramos", stock=2000.0)
            pepsi = Producto(nombre="Pepsi", unidad="Unidades", stock=24.0, precio_venta=1.25, es_directo=True)
            
            db.session.add_all([masa, salsa, queso, pepperoni, pepsi])
            db.session.commit()

            # Platillos base
            p_pepperoni = Platillo(nombre="Pepperoni", precio=8.99, categoria=cat_pizzas, es_compuesto=True)
            b_pepsi = Platillo(nombre="Pepsi", precio=1.25, categoria=cat_bebidas, es_compuesto=False)
            db.session.add_all([p_pepperoni, b_pepsi])
            db.session.commit()

            # Recetas
            r1 = Receta(platillo=p_pepperoni, producto=masa, cantidad_requerida=200)
            r2 = Receta(platillo=p_pepperoni, producto=salsa, cantidad_requerida=80)
            r3 = Receta(platillo=p_pepperoni, producto=queso, cantidad_requerida=150)
            r4 = Receta(platillo=p_pepperoni, producto=pepperoni, cantidad_requerida=50)
            db.session.add_all([r1, r2, r3, r4])
            db.session.commit()

# Ejecutar inicialización al cargar
try:
    inicializar_base_datos()
except Exception as e:
    print(f"Error al inicializar la base de datos: {e}")

# ==================== RUTAS ====================

@app.route('/')
def index():
    categorias = Categoria.query.all()
    return render_template('index.html', categorias=categorias)

@app.route('/api/platillos/<int:categoria_id>')
def obtener_platillos(categoria_id):
    platillos = Platillo.query.filter_by(categoria_id=categoria_id).all()
    resultado = [{"id": p.id, "nombre": p.nombre, "precio": p.precio} for p in platillos]
    return jsonify(resultado)

@app.route('/api/vender', methods=['POST'])
def procesar_venta():
    data = request.get_json()
    items = data.get('items', [])

    if not items:
        return jsonify({"success": False, "message": "El carrito está vacío"}), 400

    try:
        for item in items:
            platillo = Platillo.query.get(item['id'])
            cantidad = item['cantidad']

            if platillo:
                if platillo.es_compuesto:
                    for ingrediente in platillo.receta:
                        producto = ingrediente.producto
                        descuento = ingrediente.cantidad_requerida * cantidad
                        producto.stock -= descuento
                else:
                    producto = Producto.query.filter_by(nombre=platillo.nombre).first()
                    if producto:
                        producto.stock -= cantidad

        db.session.commit()
        return jsonify({"success": True, "message": "Venta realizada e inventario descontado con éxito."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/inventario')
def ver_inventario():
    productos = Producto.query.all()
    return render_template('inventario.html', productos=productos)

if __name__ == '__main__':
    app.run(debug=True)