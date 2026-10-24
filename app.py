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

class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    correo = db.Column(db.String(100), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)

class Compra(db.Model):
    __tablename__ = 'compra'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    numero_factura = db.Column(db.String(50), nullable=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)
    monto_total = db.Column(db.Float, default=0.0)
    proveedor = db.relationship('Proveedor')
    detalles = db.relationship('DetalleCompra', backref='compra', cascade="all, delete-orphan")

class DetalleCompra(db.Model):
    __tablename__ = 'detalle_compra'
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compra.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    producto = db.relationship('Producto')

class Venta(db.Model):
    __tablename__ = 'venta'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(20), default='Efectivo')
    detalles = db.relationship('DetalleVenta', backref='venta', cascade="all, delete-orphan")

class DetalleVenta(db.Model):
    __tablename__ = 'detalle_venta'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    platillo_id = db.Column(db.Integer, db.ForeignKey('platillo.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)

# ==================== RUTAS VISTAS Y POS ====================

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

                detalle = DetalleVenta(
                    venta_id=nueva_venta.id,
                    platillo_id=platillo.id,
                    cantidad=cantidad,
                    precio_unitario=platillo.precio
                )
                db.session.add(detalle)

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

# ==================== MÓDULO MENÚ Y RECETAS ====================

@app.route('/menu')
def gestionar_menu():
    platillos = Platillo.query.all()
    categorias = Categoria.query.all()
    insumos = Producto.query.all()
    return render_template('menu.html', platillos=platillos, categorias=categorias, insumos=insumos)

@app.route('/api/platillo/obtener/<int:platillo_id>')
def obtener_platillo_detalle(platillo_id):
    platillo = Platillo.query.get_or_404(platillo_id)
    ingredientes = [
        {
            "producto_id": r.producto_id,
            "nombre": r.producto.nombre,
            "cantidad": r.cantidad_requerida,
            "unidad": r.producto.unidad
        } for r in platillo.receta
    ]
    return jsonify({
        "id": platillo.id,
        "nombre": platillo.nombre,
        "precio": platillo.precio,
        "categoria_id": platillo.categoria_id,
        "ingredientes": ingredientes
    })

@app.route('/api/platillo/guardar', methods=['POST'])
def guardar_platillo_full():
    try:
        data = request.get_json()
        platillo_id = data.get('id')
        nombre = data.get('nombre')
        precio = float(data.get('precio', 0))
        categoria_id = int(data.get('categoria_id'))
        ingredientes = data.get('ingredientes', [])

        if platillo_id:
            platillo = Platillo.query.get(platillo_id)
            platillo.nombre = nombre
            platillo.precio = precio
            platillo.categoria_id = categoria_id
            platillo.es_compuesto = len(ingredientes) > 0
            
            Receta.query.filter_by(platillo_id=platillo.id).delete()
        else:
            platillo = Platillo(
                nombre=nombre,
                precio=precio,
                categoria_id=categoria_id,
                es_compuesto=len(ingredientes) > 0
            )
            db.session.add(platillo)
        
        db.session.commit()

        for ing in ingredientes:
            receta_item = Receta(
                platillo_id=platillo.id,
                producto_id=int(ing['producto_id']),
                cantidad_requerida=float(ing['cantidad'])
            )
            db.session.add(receta_item)

        db.session.commit()
        return jsonify({"success": True, "message": "Platillo y receta guardados correctamente."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/platillo/eliminar/<int:platillo_id>', methods=['DELETE'])
def eliminar_platillo(platillo_id):
    try:
        platillo = Platillo.query.get_or_404(platillo_id)
        db.session.delete(platillo)
        db.session.commit()
        return jsonify({"success": True, "message": "Platillo y su receta eliminados correctamente."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== MÓDULO PROVEEDORES Y COMPRAS ====================

@app.route('/compras')
def gestionar_compras():
    proveedores = Proveedor.query.all()
    insumos = Producto.query.all()
    historial_compras = Compra.query.order_by(Compra.fecha.desc()).all()
    return render_template('compras.html', proveedores=proveedores, insumos=insumos, compras=historial_compras)

@app.route('/api/proveedor/crear', methods=['POST'])
def crear_proveedor():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        contacto = data.get('contacto')
        telefono = data.get('telefono')
        
        if not nombre:
            return jsonify({"success": False, "message": "El nombre es obligatorio"}), 400
            
        nuevo_prov = Proveedor(nombre=nombre, contacto=contacto, telefono=telefono)
        db.session.add(nuevo_prov)
        db.session.commit()
        return jsonify({"success": True, "message": "Proveedor registrado correctamente."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/compra/registrar', methods=['POST'])
def registrar_compra():
    try:
        data = request.get_json()
        proveedor_id = int(data.get('proveedor_id'))
        numero_factura = data.get('numero_factura')
        items = data.get('items', [])  # {producto_id, cantidad, precio_unitario}

        if not items:
            return jsonify({"success": False, "message": "Debe agregar al menos un insumo a la compra."}), 400

        monto_total = 0.0
        nueva_compra = Compra(
            proveedor_id=proveedor_id,
            numero_factura=numero_factura,
            monto_total=0.0
        )
        db.session.add(nueva_compra)
        db.session.commit()

        for item in items:
            producto = Producto.query.get(item['producto_id'])
            cantidad = float(item['cantidad'])
            precio = float(item['precio_unitario'])
            subtotal = cantidad * precio
            monto_total += subtotal

            detalle = DetalleCompra(
                compra_id=nueva_compra.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio
            )
            db.session.add(detalle)

            # AUMENTAR STOCK EN INVENTARIO AUTOMÁTICAMENTE
            producto.stock += cantidad

        nueva_compra.monto_total = monto_total
        db.session.commit()
        return jsonify({"success": True, "message": "Compra registrada e inventario actualizado."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)