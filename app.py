from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de Producto
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

# Modelo de Venta
class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    producto_nombre = db.Column(db.String(100), nullable=False, default="Producto")
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    total = db.Column(db.Float, nullable=False)
    forma_pago = db.Column(db.String(50), nullable=False)

@app.route('/')
def inicio():
    lista_productos = Producto.query.all()
    return render_template('productos.html', productos=lista_productos)

@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    nombre = request.form.get('nombre')
    precio = float(request.form.get('precio'))
    stock = int(request.form.get('stock'))

    nuevo_producto = Producto(nombre=nombre, precio=precio, stock=stock)
    db.session.add(nuevo_producto)
    db.session.commit()

    return redirect(url_for('inicio'))

@app.route('/pos')
def pos():
    productos = Producto.query.all()
    ventas = Venta.query.order_by(Venta.id.desc()).all()
    return render_template('ventas.html', productos=productos, ventas=ventas)

@app.route('/registrar_venta', methods=['POST'])
def registrar_venta():
    producto_id = int(request.form.get('producto_id'))
    cantidad = int(request.form.get('cantidad'))
    forma_pago = request.form.get('forma_pago')

    producto = db.session.get(Producto, producto_id)

    if producto and producto.stock >= cantidad:
        total = producto.precio * cantidad
        producto.stock -= cantidad

        nueva_venta = Venta(
            producto_nombre=producto.nombre,
            cantidad=cantidad,
            total=total,
            forma_pago=forma_pago
        )
        db.session.add(nueva_venta)
        db.session.commit()

    return redirect(url_for('pos'))

@app.route('/reporte')
def reporte():
    hoy = date.today()
    ventas_hoy = Venta.query.filter(db.func.date(Venta.fecha) == hoy).all()

    total_dia = sum(v.total for v in ventas_hoy)
    total_transacciones = len(ventas_hoy)

    desglose = {
        'Efectivo': sum(v.total for v in ventas_hoy if v.forma_pago == 'Efectivo'),
        'Tarjeta': sum(v.total for v in ventas_hoy if v.forma_pago == 'Tarjeta'),
        'Transferencia': sum(v.total for v in ventas_hoy if v.forma_pago == 'Transferencia')
    }

    return render_template('reportes.html', total_dia=total_dia, total_transacciones=total_transacciones, desglose=desglose)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)