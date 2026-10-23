import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuración de base de datos para Render o Local
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///punto_venta.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODELOS (BASE DE DATOS ERP) ====================

# --- MENÚ E INVENTARIO ---
class Categoria(db.Model):
    __tablename__ = 'categoria'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    platillos = db.relationship('Platillo', backref='categoria', lazy=True)

class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    unidad = db.Column(db.String(20), default='Unidad')  # Gramos, Mililitros, Unidades, etc.
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

# --- PROVEEDORES Y COMPRAS ---
class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    correo = db.Column(db.String(100), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    compras = db.relationship('Compra', backref='proveedor', lazy=True)

class Compra(db.Model):
    __tablename__ = 'compra'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    numero_factura = db.Column(db.String(50), nullable=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)
    monto_total = db.Column(db.Float, default=0.0)
    detalles = db.relationship('DetalleCompra', backref='compra', cascade="all, delete-orphan")

class DetalleCompra(db.Model):
    __tablename__ = 'detalle_compra'
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compra.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    producto = db.relationship('Producto')

# --- ACTIVOS FIJOS ---
class Activo(db.Model):
    __tablename__ = 'activo'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    valor = db.Column(db.Float, nullable=False)
    fecha_adquisicion = db.Column(db.DateTime, default=datetime.utcnow)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=True)

# --- VENTAS Y COBROS ---
class Venta(db.Model):
    __tablename__ = 'venta'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(20), default='Efectivo')  # Efectivo, Tarjeta, Transferencia
    detalles = db.relationship('DetalleVenta', backref='venta', cascade="all, delete-orphan")

class DetalleVenta(db.Model):
    __tablename__ = 'detalle_venta'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    platillo_id = db.Column(db.Integer, db.ForeignKey('platillo.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    platillo = db.relationship('Platillo')

# --- CONTABILIDAD Y CAJA CHICA ---
class MovimientoCaja(db.Model):
    __tablename__ = 'movimiento_caja'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), nullable=False)  # Apertura, Ingreso, Egreso, Cierre
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)

class Gasto(db.Model):
    __tablename__ = 'gasto'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    concepto = db.Column(db.String(150), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    categoria_gasto = db.Column(db.String(50), default='Operativo')  # Alquiler, Servicios, Planilla, etc.

# ==================== INICIALIZACIÓN SEGURA ====================

def inicializar_base_datos():
    with app.app_context():
        db.create_all()
        
        # 1. Crear Categorías base si no existen
        categorias_base = ["Pizzas", "Entradas", "Bebidas", "Postres"]
        for cat_nombre in categorias_base:
            if not Categoria.query.filter_by(nombre=cat_nombre).first():
                db.session.add(Categoria(nombre=cat_nombre))
        db.session.commit()

        # 2. Crear Insumos Base si no existen
        if not Producto.query.filter_by(nombre="Masa de Pizza").first():
            masa = Producto(nombre="Masa de Pizza", unidad="Gramos", stock=10000.0)
            salsa = Producto(nombre="Salsa de Tomate", unidad="Gramos", stock=5000.0)
            queso = Producto(nombre="Queso Mozzarella", unidad="Gramos", stock=5000.0)
            pepperoni = Producto(nombre="Pepperoni", unidad="Gramos", stock=2000.0)
            pepsi_insumo = Producto(nombre="Pepsi", unidad="Unidades", stock=24.0, precio_venta=1.25, es_directo=True)
            db.session.add_all([masa, salsa, queso, pepperoni, pepsi_insumo])
            db.session.commit()

        # 3. Definir Menú por Nombre de Categoría
        menu = {
            "Pizzas": [
                ("Pepperoni", 8.99, True),
                ("Suprema", 10.99, True),
                ("Hawaiana", 9.99, True),
                ("Loroco", 8.99, True)
            ],
            "Entradas": [
                ("Pan con Ajo", 3.50, False),
                ("Palitroques", 4.00, False),
                ("Papas Fritas", 2.99, False)
            ],
            "Bebidas": [
                ("Pepsi", 1.25, False),
                ("Coca Cola", 1.25, False),
                ("Kolashanpan", 1.25, False)
            ],
            "Postres": [
                ("Pie de Manzana", 2.50, False),
                ("Volcán de Chocolate", 3.00, False)
            ]
        }

        # 4. Insertar Platillos y Vincular Receta
        for nom_cat, lista_platillos in menu.items():
            cat_obj = Categoria.query.filter_by(nombre=nom_cat).first()
            if cat_obj:
                for nombre_p, precio_p, es_comp in lista_platillos:
                    if not Platillo.query.filter_by(nombre=nombre_p).first():
                        nuevo_p = Platillo(
                            nombre=nombre_p,
                            precio=precio_p,
                            categoria=cat_obj,
                            es_compuesto=es_comp
                        )
                        db.session.add(nuevo_p)
                        db.session.commit()

                        # Vincular receta únicamente a Pepperoni
                        if nombre_p == "Pepperoni":
                            masa = Producto.query.filter_by(nombre="Masa de Pizza").first()
                            salsa = Producto.query.filter_by(nombre="Salsa de Tomate").first()
                            queso = Producto.query.filter_by(nombre="Queso Mozzarella").first()
                            pep = Producto.query.filter_by(nombre="Pepperoni").first()
                            if masa and salsa and queso and pep:
                                db.session.add_all([
                                    Receta(platillo=nuevo_p, producto=masa, cantidad_requerida=200),
                                    Receta(platillo=nuevo_p, producto=salsa, cantidad_requerida=80),
                                    Receta(platillo=nuevo_p, producto=queso, cantidad_requerida=150),
                                    Receta(platillo=nuevo_p, producto=pep, cantidad_requerida=50)
                                ])
                                db.session.commit()

# ==================== RUTAS ====================

@app.route('/')
def index():
    try:
        inicializar_base_datos()
    except Exception as e:
        print(f"Error al inicializar DB en la primera petición: {e}")
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
    metodo_pago = data.get('metodo_pago', 'Efectivo')

    if not items:
        return jsonify({"success": False, "message": "El carrito está vacío"}), 400

    try:
        monto_total = 0.0
        nueva_venta = Venta(total=0.0, metodo_pago=metodo_pago)
        db.session.add(nueva_venta)
        db.session.commit()

        for item in items:
            platillo = Platillo.query.get(item['id'])
            cantidad = item['cantidad']

            if platillo:
                subtotal = platillo.precio * cantidad
                monto_total += subtotal

                # Registrar detalle de venta en historial
                detalle = DetalleVenta(
                    venta_id=nueva_venta.id,
                    platillo_id=platillo.id,
                    cantidad=cantidad,
                    precio_unitario=platillo.precio
                )
                db.session.add(detalle)

                # Descontar inventario según receta o directo
                if platillo.es_compuesto:
                    for ingrediente in platillo.receta:
                        producto = ingrediente.producto
                        descuento = ingrediente.cantidad_requerida * cantidad
                        producto.stock -= descuento
                else:
                    producto = Producto.query.filter_by(nombre=platillo.nombre).first()
                    if producto:
                        producto.stock -= cantidad

        nueva_venta.total = monto_total
        db.session.commit()
        return jsonify({"success": True, "message": f"Venta registrada con éxito ({metodo_pago})."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/inventario')
def ver_inventario():
    productos = Producto.query.all()
    return render_template('inventario.html', productos=productos)

if __name__ == '__main__':
    app.run(debug=True)