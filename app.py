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
CLEAN_FLAG_FILE = "clean_flag.json"
CATEGORIES_FILE = "categories_data.json"  # NUEVO: Para categorías personalizadas
STOCK_FILE = "stock_data.json"

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

# NUEVO: Funciones para categorías personalizadas
def load_categories():
    """Carga las categorías personalizadas desde el archivo JSON"""
    default_categories = {
        'empanadas': {'name': 'Empanadas', 'emoji': '🥟'},
        'corviches':  {'name': 'Corviches',  'emoji': '🐟'},
        'gatos':      {'name': 'Gatos Encerrados', 'emoji': '🎁'},
        'bebidas':    {'name': 'Bebidas',    'emoji': '🥤'}
    }
    if os.path.exists(CATEGORIES_FILE):
        try:
            with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando categorías: {e}")
    return default_categories

def save_categories(categories):
    """Guarda las categorías en el archivo JSON"""
    try:
        with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando categorías: {e}")




def load_stock():
    """Carga el stock de cada producto"""
    if os.path.exists(STOCK_FILE):
        try:
            with open(STOCK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando stock: {e}")
    return {}

def save_stock(stock):
    """Guarda el stock en archivo JSON"""
    try:
        with open(STOCK_FILE, 'w', encoding='utf-8') as f:
            json.dump(stock, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando stock: {e}")


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

def set_clean_flag():
    """Establece la bandera de limpieza para notificar a usuarios"""
    try:
        with open(CLEAN_FLAG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'cleaned': True,
                'timestamp': datetime.now().isoformat(),
                'notified_users': []
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
# Almacenamiento
# =========================
orders = []
order_counter = 1
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
    is_open = load_restaurant_status()
    return jsonify({'is_open': is_open})

@app.route('/api/restaurant-status', methods=['PUT'])
def update_restaurant_status():
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

    # ✅ VALIDAR Y DESCONTAR STOCK
    stock = load_stock()
    items = data['items']
    
    # Verificar que hay suficiente stock
    for item in items:
        product_id = item['name']
        qty_requested = item['quantity']
        available = stock.get(product_id, -1)  # -1 = sin límite
        if available != -1 and available < qty_requested:
            return jsonify({'error': f'Stock insuficiente para {product_id}. Solo quedan {available}.'}), 400

    # Descontar stock
    for item in items:
        product_id = item['name']
        qty_requested = item['quantity']
        if product_id in stock and stock[product_id] != -1:
            stock[product_id] = max(0, stock[product_id] - qty_requested)
    save_stock(stock)

    order = {
        'id': order_counter,
        'user_id': user_id,
        'username': username,
        'items': items,
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

@app.route('/api/orders/clean-all', methods=['DELETE'])
def clean_all_orders():
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    global orders, order_counter
    orders_count = len(orders)
    orders = []
    order_counter = 1
    save_data()
    set_clean_flag()
    print(f"🗑️ LIMPIEZA EJECUTADA: {orders_count} pedidos eliminados")
    return jsonify({
        'success': True,
        'deleted_count': orders_count,
        'message': 'Todos los pedidos han sido eliminados'
    })

@app.route('/api/check-clean-flag', methods=['GET'])
def check_clean():
    if session.get('role') == 'admin':
        return jsonify({'cleaned': False})
    user_id = session.get('user_id', 'unknown')
    cleaned = check_clean_flag_for_user(user_id)
    return jsonify({'cleaned': cleaned})

@app.route('/api/confirm-clean-notification', methods=['POST'])
def confirm_clean_notification():
    if session.get('role') != 'admin':
        user_id = session.get('user_id', 'unknown')
        mark_user_notified(user_id)
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
    product_id = data['name'].lower().replace(' ', '-').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
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
# API CATEGORÍAS (NUEVO)
# =========================
@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Obtener todas las categorías"""
    return jsonify(load_categories())

@app.route('/api/categories', methods=['POST'])
def add_category():
    """Agregar una nueva categoría (solo admin)"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.json
    cat_name = data.get('name', '').strip()
    cat_emoji = data.get('emoji', '🍴').strip()
    
    if not cat_name:
        return jsonify({'error': 'El nombre de la categoría es requerido'}), 400
    
    # Generar ID de categoría (slug)
    cat_id = cat_name.lower().replace(' ', '_').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
    
    categories = load_categories()
    
    if cat_id in categories:
        return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 400
    
    categories[cat_id] = {'name': cat_name, 'emoji': cat_emoji}
    save_categories(categories)
    
    # También inicializar en products_data.json si no existe
    products = load_products()
    if cat_id not in products:
        products[cat_id] = []
        save_products(products)
    
    print(f"✅ Nueva categoría creada: {cat_id} - {cat_name} {cat_emoji}")
    return jsonify({'id': cat_id, 'name': cat_name, 'emoji': cat_emoji}), 201

@app.route('/api/categories/<cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    """Eliminar una categoría (solo admin)"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    # Proteger categorías base
    base_categories = ['empanadas', 'corviches', 'gatos', 'bebidas']
    if cat_id in base_categories:
        return jsonify({'error': 'No puedes eliminar las categorías base'}), 400
    
    categories = load_categories()
    if cat_id not in categories:
        return jsonify({'error': 'Categoría no encontrada'}), 404
    
    del categories[cat_id]
    save_categories(categories)
    
    # Eliminar también los productos de esa categoría
    products = load_products()
    if cat_id in products:
        del products[cat_id]
        save_products(products)
    
    print(f"🗑️ Categoría eliminada: {cat_id}")
    return jsonify({'success': True})



# =========================
# API STOCK
# =========================
@app.route('/api/stock', methods=['GET'])
def get_stock():
    """Obtener el stock actual de todos los productos"""
    return jsonify(load_stock())

@app.route('/api/stock', methods=['PUT'])
def update_stock():
    """Admin actualiza el stock de un producto"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 0)
    stock = load_stock()
    stock[product_id] = int(quantity)
    save_stock(stock)
    return jsonify({'success': True, 'product_id': product_id, 'quantity': quantity})

# =========================
# MAIN
# =========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    serve(app, host='0.0.0.0', port=port)