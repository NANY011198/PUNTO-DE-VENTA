from app import app, db, Categoria, Producto, Platillo, Receta

def poblar_base_de_datos():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # 1. Crear Categorías
        cat_pizzas = Categoria(nombre="Pizzas")
        cat_entradas = Categoria(nombre="Entradas")
        cat_bebidas = Categoria(nombre="Bebidas")
        cat_postres = Categoria(nombre="Postres")

        db.session.add_all([cat_pizzas, cat_entradas, cat_bebidas, cat_postres])
        db.session.commit()

        # 2. Crear Insumos / Materia Prima
        masa = Producto(nombre="Masa de Pizza", unidad="Gramos", stock=10000.0, es_directo=False)
        salsa = Producto(nombre="Salsa de Tomate", unidad="Gramos", stock=5000.0, es_directo=False)
        queso = Producto(nombre="Queso Mozzarella", unidad="Gramos", stock=5000.0, es_directo=False)
        pepperoni = Producto(nombre="Pepperoni", unidad="Gramos", stock=2000.0, es_directo=False)
        jamon = Producto(nombre="Jamón", unidad="Gramos", stock=2000.0, es_directo=False)
        pina = Producto(nombre="Piña", unidad="Gramos", stock=2000.0, es_directo=False)
        loroco = Producto(nombre="Loroco", unidad="Gramos", stock=1500.0, es_directo=False)

        pan = Producto(nombre="Pan de Ajo", unidad="Unidades", stock=50.0, es_directo=False)
        mantequilla = Producto(nombre="Mantequilla con Ajo", unidad="Gramos", stock=1000.0, es_directo=False)
        alitas = Producto(nombre="Alitas de Pollo", unidad="Unidades", stock=100.0, es_directo=False)
        salsa_bbq = Producto(nombre="Salsa BBQ", unidad="ML", stock=2000.0, es_directo=False)
        papas = Producto(nombre="Papas pre-fritas", unidad="Gramos", stock=5000.0, es_directo=False)

        # 3. Crear Productos de Venta Directa
        pepsi = Producto(nombre="Pepsi", unidad="Unidades", stock=24.0, precio_venta=1.25, es_directo=True)
        cocacola = Producto(nombre="Coca Cola", unidad="Unidades", stock=24.0, precio_venta=1.25, es_directo=True)
        flan = Producto(nombre="Flan", unidad="Unidades", stock=15.0, precio_venta=2.00, es_directo=True)
        gelatina = Producto(nombre="Gelatina", unidad="Unidades", stock=20.0, precio_venta=1.00, es_directo=True)
        tres_leches = Producto(nombre="Tres Leches", unidad="Unidades", stock=10.0, precio_venta=2.50, es_directo=True)

        insumos = [
            masa, salsa, queso, pepperoni, jamon, pina, loroco,
            pan, mantequilla, alitas, salsa_bbq, papas,
            pepsi, cocacola, flan, gelatina, tres_leches
        ]
        db.session.add_all(insumos)
        db.session.commit()

        # 4. Crear Platillos
        p_pepperoni = Platillo(nombre="Pepperoni", precio=8.99, categoria=cat_pizzas, es_compuesto=True)
        p_suprema = Platillo(nombre="Suprema", precio=10.99, categoria=cat_pizzas, es_compuesto=True)
        p_hawaiana = Platillo(nombre="Hawaiana", precio=9.99, categoria=cat_pizzas, es_compuesto=True)
        p_loroco = Platillo(nombre="Loroco", precio=8.99, categoria=cat_pizzas, es_compuesto=True)

        e_pan_ajo = Platillo(nombre="Pan con Ajo", precio=3.50, categoria=cat_entradas, es_compuesto=True)
        e_alitas = Platillo(nombre="Alitas", precio=5.99, categoria=cat_entradas, es_compuesto=True)
        e_papas = Platillo(nombre="Papas", precio=2.99, categoria=cat_entradas, es_compuesto=True)

        b_pepsi = Platillo(nombre="Pepsi", precio=1.25, categoria=cat_bebidas, es_compuesto=False)
        b_cocacola = Platillo(nombre="Coca Cola", precio=1.25, categoria=cat_bebidas, es_compuesto=False)

        po_flan = Platillo(nombre="Flan", precio=2.00, categoria=cat_postres, es_compuesto=False)
        po_gelatina = Platillo(nombre="Gelatina", precio=1.00, categoria=cat_postres, es_compuesto=False)
        po_tres_leches = Platillo(nombre="Tres Leches", precio=2.50, categoria=cat_postres, es_compuesto=False)

        platillos = [
            p_pepperoni, p_suprema, p_hawaiana, p_loroco,
            e_pan_ajo, e_alitas, e_papas,
            b_pepsi, b_cocacola,
            po_flan, po_gelatina, po_tres_leches
        ]
        db.session.add_all(platillos)
        db.session.commit()

        # 5. Crear Recetas
        recetas = [
            Receta(platillo=p_pepperoni, producto=masa, cantidad_requerida=200),
            Receta(platillo=p_pepperoni, producto=salsa, cantidad_requerida=80),
            Receta(platillo=p_pepperoni, producto=queso, cantidad_requerida=150),
            Receta(platillo=p_pepperoni, producto=pepperoni, cantidad_requerida=50),

            Receta(platillo=p_suprema, producto=masa, cantidad_requerida=200),
            Receta(platillo=p_suprema, producto=salsa, cantidad_requerida=80),
            Receta(platillo=p_suprema, producto=queso, cantidad_requerida=150),
            Receta(platillo=p_suprema, producto=pepperoni, cantidad_requerida=30),
            Receta(platillo=p_suprema, producto=jamon, cantidad_requerida=30),
            Receta(platillo=p_suprema, producto=loroco, cantidad_requerida=30),

            Receta(platillo=p_hawaiana, producto=masa, cantidad_requerida=200),
            Receta(platillo=p_hawaiana, producto=salsa, cantidad_requerida=80),
            Receta(platillo=p_hawaiana, producto=queso, cantidad_requerida=150),
            Receta(platillo=p_hawaiana, producto=jamon, cantidad_requerida=60),
            Receta(platillo=p_hawaiana, producto=pina, cantidad_requerida=40),

            Receta(platillo=p_loroco, producto=masa, cantidad_requerida=200),
            Receta(platillo=p_loroco, producto=salsa, cantidad_requerida=80),
            Receta(platillo=p_loroco, producto=queso, cantidad_requerida=150),
            Receta(platillo=p_loroco, producto=loroco, cantidad_requerida=50),

            Receta(platillo=e_pan_ajo, producto=pan, cantidad_requerida=1),
            Receta(platillo=e_pan_ajo, producto=mantequilla, cantidad_requerida=30),

            Receta(platillo=e_alitas, producto=alitas, cantidad_requerida=6),
            Receta(platillo=e_alitas, producto=salsa_bbq, cantidad_requerida=50),

            Receta(platillo=e_papas, producto=papas, cantidad_requerida=200),
        ]

        db.session.add_all(recetas)
        db.session.commit()
        print("¡Base de datos cargada exitosamente!")

if __name__ == '__main__':
    poblar_base_de_datos()