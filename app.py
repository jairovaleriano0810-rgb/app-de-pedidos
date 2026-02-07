from flask import Flask, render_template, request, jsonify, session, redirect
from datetime import datetime
import os
import json
from waitress import serve

app = Flask(__name__)
app.secret_key = "clave-super-secreta-123"

ADMIN_CODE = "EMPANADAS2026"
DATA_FILE = "orders_data.json"
PRODUCTS_FILE = "products_data.json"
STATUS_FILE = "restaurant_status.json"
CLEAN_FLAG_FILE = "clean_flag.json"  # NUEVO: Para notificar a usuarios

# =========================
# Funciones de persistencia
# =========================

def load_data():
    """Carga los pedidos desde el archivo JSON"""
    global orders, order_counter
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                orders = data.get('orders', [])
                order_counter = data.get('order_counter', 1)
        except Exception as e:
            print(f"Error cargando datos: {e}")
            orders = []
            order_counter = 1
    else:
        orders = []
        order_counter = 1

def save_data():
    """Guarda los pedidos en el archivo JSON"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'orders': orders,
                'order_counter': order_counter
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando datos: {e}")

def load_products():
    """Carga los productos desde el archivo JSON"""
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando productos: {e}")
    
    # Productos por defecto
    return {
        'empanadas': [
            {'id': 'empanada-pollo', 'name': 'Empanada de Pollo', 'price': 1.00, 'description': 'Empanadas jugosas rellenas de pollo sazonado'},
            {'id': 'empanada-queso', 'name': 'Empanada de Queso', 'price': 1.00, 'description': 'Deliciosas empanadas rellenas de queso fresco'}
        ],
        'corviches': [
            {'id': 'corviche', 'name': 'Corviche Clásico', 'price': 1.00, 'description': 'Delicia costeña de verde y pescado'}
        ],
        'gatos': [
            {'id': 'gato-encerrado', 'name': 'Gato Encerrado Tradicional', 'price': 1.00, 'description': 'Tradicional bocadito ecuatoriano'}
        ],
        'bebidas': [
            {'id': 'coca-cola', 'name': 'Coca Cola', 'price': 0.50, 'description': 'Refrescante bebida'},
            {'id': 'fanta', 'name': 'Fanta', 'price': 0.50, 'description': 'Sabor naranja burbujeante'},
            {'id': 'sprite', 'name': 'Sprite', 'price': 0.50, 'description': 'Lima-limón refrescante'}
        ]
    }

def save_products(products):
    """Guarda los productos en el archivo JSON"""
    try:
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando productos: {e}")

def load_restaurant_status():
    """Carga el estado del restaurante (abierto/cerrado)"""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('is_open', True)
        except Exception as e:
            print(f"Error cargando estado: {e}")
            return True
    return True

def save_restaurant_status(is_open):
    """Guarda el estado del restaurante"""
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'is_open': is_open}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando estado: {e}")

# NUEVO: Funciones para bandera de limpieza
def set_clean_flag():
    """Establece la bandera de limpieza para notificar a usuarios"""
    try:
        with open(CLEAN_FLAG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'cleaned': True,
                'timestamp': datetime.now().isoformat(),
                'notified_users': []  # Lista de usuarios que ya vieron la notificación
            }, f, ensure_ascii=False, indent=2)
        print(f"✅ Bandera de limpieza establecida")
    except Exception as e:
        print(f"Error estableciendo bandera: {e}")

def check_clean_flag_for_user(user_id):
    """Verifica si hay una bandera de limpieza activa para un usuario específico"""
    if os.path.exists(CLEAN_FLAG_FILE):
        try:
            with open(CLEAN_FLAG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Si la bandera está activa Y el usuario no ha sido notificado
                if data.get('cleaned', False):
                    notified_users = data.get('notified_users', [])
                    return user_id not in notified_users
                    
        except Exception as e:
            print(f"Error verificando bandera: {e}")
            return False
    return False

def mark_user_notified(user_id):
    """Marca que un usuario específico ya vio la notificación"""
    if os.path.exists(CLEAN_FLAG_FILE):
        try:
            with open(CLEAN_FLAG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'notified_users' not in data:
                data['notified_users'] = []
            
            if user_id not in data['notified_users']:
                data['notified_users'].append(user_id)
            
            with open(CLEAN_FLAG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"✅ Usuario {user_id} marcado como notificado")
        except Exception as e:
            print(f"Error marcando usuario: {e}")

def clear_clean_flag():
    """Limpia la bandera después de que todos los usuarios la hayan visto"""
    try:
        if os.path.exists(CLEAN_FLAG_FILE):
            os.remove(CLEAN_FLAG_FILE)
            print(f"✅ Bandera de limpieza eliminada")
    except Exception as e:
        print(f"Error limpiando bandera: {e}")

# =========================
# Almacenamiento (se carga desde archivo)
# =========================
orders = []
order_counter = 1

# Cargar datos al iniciar
load_data()

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')

        if role == 'admin':
            code = request.form.get('code')
            if code == ADMIN_CODE:
                session['role'] = 'admin'
                session['user_id'] = 'admin'
                session['username'] = 'Administrador'
                return redirect('/')
            else:
                return render_template('login.html', error="Código incorrecto")
        else:
            name = request.form.get('name', '').strip()
            lastname = request.form.get('lastname', '').strip()

            if not name or not lastname:
                return render_template('login.html', error="Por favor completa todos los campos")

            user_id = f"{name.lower()}_{lastname.lower()}"

            session['role'] = 'user'
            session['username'] = f"{name.capitalize()} {lastname.capitalize()}"
            session['user_id'] = user_id

            return redirect('/')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# =========================
# APP PRINCIPAL
# =========================

@app.route('/')
def index():
    if 'role' not in session:
        return redirect('/login')
    return render_template('index.html', role=session['role'])


# =========================
# API ESTADO DEL RESTAURANTE
# =========================

@app.route('/api/restaurant-status', methods=['GET'])
def get_restaurant_status():
    """Obtener el estado del restaurante"""
    is_open = load_restaurant_status()
    return jsonify({'is_open': is_open})


@app.route('/api/restaurant-status', methods=['PUT'])
def update_restaurant_status():
    """Actualizar el estado del restaurante (solo admin)"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.json
    is_open = data.get('is_open', True)
    save_restaurant_status(is_open)
    
    return jsonify({'is_open': is_open})


# =========================
# API PEDIDOS
# =========================

@app.route('/api/orders', methods=['GET'])
def get_orders():
    if session.get('role') == 'admin':
        return jsonify(orders)
    else:
        user_id = session.get('user_id')
        user_orders = [o for o in orders if o['user_id'] == user_id]
        return jsonify(user_orders)



@app.route('/api/orders', methods=['POST'])
def create_order():
    global order_counter

    data = request.json
    user_id = session.get('user_id', 'desconocido')
    username = session.get('username')
    
    if not username:
        if user_id == 'admin':
            username = 'Administrador'
        elif '_' in user_id:
            parts = user_id.split('_')
            username = f"{parts[0].capitalize()} {parts[1].capitalize()}"
        else:
            username = 'Usuario Desconocido'

    order = {
        'id': order_counter,
        'user_id': user_id,
        'username': username,
        'items': data['items'],
        'status': 'pending',
        'timestamp': datetime.now().isoformat()
    }

    orders.insert(0, order)
    order_counter += 1
    save_data()

    return jsonify(order), 201


@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403

    data = request.json

    for order in orders:
        if order['id'] == order_id:
            order['status'] = data['status']
            save_data()
            return jsonify(order)

    return jsonify({'error': 'Pedido no encontrado'}), 404


@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403

    global orders
    orders = [order for order in orders if order['id'] != order_id]
    save_data()
    
    return jsonify({'success': True})


# NUEVO: Limpiar todos los pedidos
@app.route('/api/orders/clean-all', methods=['DELETE'])
def clean_all_orders():
    """Eliminar todos los pedidos (solo admin)"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    global orders
    orders_count = len(orders)
    orders = []
    save_data()
    
    # Establecer bandera para notificar a usuarios
    set_clean_flag()
    
    print(f"🗑️ LIMPIEZA EJECUTADA: {orders_count} pedidos eliminados")
    print(f"🔔 Bandera de notificación establecida para usuarios")
    
    return jsonify({
        'success': True,
        'deleted_count': orders_count,
        'message': 'Todos los pedidos han sido eliminados'
    })


# NUEVO: Verificar bandera de limpieza
@app.route('/api/check-clean-flag', methods=['GET'])
def check_clean():
    """Verificar si hay una bandera de limpieza activa"""
    if session.get('role') == 'admin':
        return jsonify({'cleaned': False})
    
    user_id = session.get('user_id', 'unknown')
    cleaned = check_clean_flag_for_user(user_id)
    
    if cleaned:
        print(f"🔔 Usuario {user_id} detectó bandera de limpieza")
    
    return jsonify({'cleaned': cleaned})


# NUEVO: Confirmar lectura de notificación de limpieza
@app.route('/api/confirm-clean-notification', methods=['POST'])
def confirm_clean_notification():
    """Confirmar que el usuario vio la notificación"""
    if session.get('role') != 'admin':
        user_id = session.get('user_id', 'unknown')
        mark_user_notified(user_id)
        print(f"📋 Usuario {user_id} confirmó notificación de limpieza")
    return jsonify({'success': True})


# =========================
# API PRODUCTOS
# =========================

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(load_products())


@app.route('/api/products', methods=['POST'])
def add_product():
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.json
    products = load_products()
    
    product_id = data['name'].lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    
    new_product = {
        'id': product_id,
        'name': data['name'],
        'price': float(data['price']),
        'description': data.get('description', '')
    }
    
    category = data['category']
    if category not in products:
        products[category] = []
    
    products[category].append(new_product)
    save_products(products)
    
    return jsonify(new_product), 201


@app.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    products = load_products()
    
    for category in products:
        products[category] = [p for p in products[category] if p['id'] != product_id]
    
    save_products(products)
    
    return jsonify({'success': True})


# =========================
# MAIN
# =========================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    serve(app, host='0.0.0.0', port=port)