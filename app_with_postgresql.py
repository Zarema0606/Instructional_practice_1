from flask import Flask, render_template_string, jsonify, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'premium-furniture-secret-key-2025'

# ==================== НАСТРОЙКИ БАЗЫ ДАННЫХ ====================
DB_CONFIG = {
    'host': 'localhost',
    'database': 'premium_furniture',
    'user': 'postgres',
    'password': 'postgres',
    'port': '5432'
}

def get_db_connection():
    """Создает соединение с базой данных"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return None

def init_database():
    """Инициализация базы данных"""
    try:
        # Подключаемся к postgres для создания БД
        conn = psycopg2.connect(
            host='localhost',
            database='postgres',
            user='postgres',
            password='postgres'
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Создаем базу данных если ее нет
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'premium_furniture'")
        exists = cur.fetchone()
        
        if not exists:
            cur.execute('CREATE DATABASE premium_furniture')
            print("✅ База данных создана")
        
        cur.close()
        conn.close()
        
        # Теперь выполняем SQL-скрипт
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            
            # Читаем SQL-скрипт
            with open('PremiumFurnitureSolutions.sql', 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # Разделяем скрипт на отдельные команды
            commands = sql_script.split(';')
            
            for command in commands:
                command = command.strip()
                if command and not command.startswith('--'):
                    try:
                        cur.execute(command)
                    except Exception as e:
                        print(f"⚠️ Ошибка выполнения команды: {e}")
                        continue
            
            conn.commit()
            cur.close()
            conn.close()
            print("✅ База данных инициализирована")
            
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")

# ==================== ДЕКОРАТОР ДЛЯ РАБОТЫ С БД ====================
def with_db_connection(func):
    """Декоратор для автоматического управления соединением с БД"""
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            kwargs['cursor'] = cursor
            kwargs['connection'] = conn
            
            result = func(*args, **kwargs)
            
            conn.commit()
            return result
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ Ошибка БД в функции {func.__name__}: {e}")
            return jsonify({'error': str(e)}), 500
            
        finally:
            if conn:
                cursor.close()
                conn.close()
    
    wrapper.__name__ = func.__name__
    return wrapper

# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    """Главная страница"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/products', methods=['GET'])
@with_db_connection
def get_products(cursor, connection):
    """Получение списка продукции"""
    query = '''
    SELECT 
        p.product_id as id,
        p.article_number as article,
        p.product_name as name,
        p.minimum_partner_price as min_price,
        p.product_type_id,
        p.material_type_id,
        pt.product_type_name as product_type_name,
        mt.material_type_name as material_name,
        p.created_at
    FROM products p
    JOIN product_types pt ON p.product_type_id = pt.product_type_id
    JOIN material_types mt ON p.material_type_id = mt.material_type_id
    ORDER BY p.product_name
    '''
    cursor.execute(query)
    products = cursor.fetchall()
    
    # Преобразуем Decimal в float для JSON
    for product in products:
        if 'min_price' in product:
            product['min_price'] = float(product['min_price'])
    
    return jsonify(products)

@app.route('/api/product/<int:product_id>', methods=['GET'])
@with_db_connection
def get_product_by_id(product_id, cursor, connection):
    """Получение информации о конкретном продукте"""
    query = '''
    SELECT 
        p.product_id as id,
        p.article_number as article,
        p.product_name as name,
        p.minimum_partner_price as min_price,
        p.product_type_id,
        p.material_type_id,
        pt.product_type_name,
        mt.material_type_name
    FROM products p
    JOIN product_types pt ON p.product_type_id = pt.product_type_id
    JOIN material_types mt ON p.material_type_id = mt.material_type_id
    WHERE p.product_id = %s
    '''
    cursor.execute(query, (product_id,))
    product = cursor.fetchone()
    
    if product:
        if 'min_price' in product:
            product['min_price'] = float(product['min_price'])
        return jsonify(product)
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/api/product-types', methods=['GET'])
@with_db_connection
def get_product_types(cursor, connection):
    """Получение типов продукции"""
    cursor.execute('SELECT product_type_id as id, product_type_name as name, product_type_coefficient as coefficient FROM product_types')
    types = cursor.fetchall()
    
    for t in types:
        if 'coefficient' in t:
            t['coefficient'] = float(t['coefficient'])
    
    return jsonify(types)

@app.route('/api/material-types', methods=['GET'])
@with_db_connection
def get_material_types(cursor, connection):
    """Получение типов материалов"""
    cursor.execute('SELECT material_type_id as id, material_type_name as name, raw_material_loss_percent as waste_percent FROM material_types')
    materials = cursor.fetchall()
    
    for m in materials:
        if 'waste_percent' in m:
            m['waste_percent'] = float(m['waste_percent'])
    
    return jsonify(materials)

@app.route('/api/workshops', methods=['GET'])
@with_db_connection
def get_workshops(cursor, connection):
    """Получение списка цехов"""
    cursor.execute('SELECT workshop_id as id, workshop_name as name, staff_count as people_count, workshop_type FROM workshops')
    workshops = cursor.fetchall()
    
    # Для совместимости с фронтендом добавляем фиктивное production_time
    for w in workshops:
        w['production_time'] = 8  # Стандартное значение
    
    return jsonify(workshops)

@app.route('/api/product-workshops/<int:product_id>', methods=['GET'])
@with_db_connection
def get_product_workshops(product_id, cursor, connection):
    """Получение цехов для конкретного продукта"""
    query = '''
    SELECT 
        pw.workshop_id,
        w.workshop_name,
        w.staff_count,
        pw.manufacturing_time_hours as production_time
    FROM product_workshops pw
    JOIN workshops w ON pw.workshop_id = w.workshop_id
    WHERE pw.product_id = %s
    ORDER BY pw.manufacturing_time_hours DESC
    '''
    cursor.execute(query, (product_id,))
    workshops = cursor.fetchall()
    
    for w in workshops:
        if 'production_time' in w:
            w['production_time'] = float(w['production_time'])
    
    return jsonify(workshops)

@app.route('/api/calculate-raw-materials', methods=['POST'])
@with_db_connection
def api_calculate_raw_materials(cursor, connection):
    """Расчет необходимого сырья"""
    data = request.json
    
    try:
        product_type_id = int(data.get('product_type_id', 0))
        material_type_id = int(data.get('material_type_id', 0))
        quantity = int(data.get('quantity', 0))
        param1 = float(data.get('param1', 0))
        param2 = float(data.get('param2', 0))
    except (ValueError, TypeError):
        return jsonify({"result": -1})
    
    # Проверяем существование типов в БД
    cursor.execute('SELECT 1 FROM product_types WHERE product_type_id = %s', (product_type_id,))
    if not cursor.fetchone():
        return jsonify({"result": -1})
    
    cursor.execute('SELECT 1 FROM material_types WHERE material_type_id = %s', (material_type_id,))
    if not cursor.fetchone():
        return jsonify({"result": -1})
    
    if quantity <= 0 or param1 <= 0 or param2 <= 0:
        return jsonify({"result": -1})
    
    # Получаем коэффициент типа продукции и процент потерь
    cursor.execute('SELECT product_type_coefficient FROM product_types WHERE product_type_id = %s', (product_type_id,))
    product_coeff_result = cursor.fetchone()
    
    cursor.execute('SELECT raw_material_loss_percent FROM material_types WHERE material_type_id = %s', (material_type_id,))
    material_loss_result = cursor.fetchone()
    
    if not product_coeff_result or not material_loss_result:
        return jsonify({"result": -1})
    
    product_coefficient = float(product_coeff_result['product_type_coefficient'])
    loss_percent = float(material_loss_result['raw_material_loss_percent'])
    
    # Расчет
    raw_material_per_unit = param1 * param2 * product_coefficient
    total_raw_material = raw_material_per_unit * quantity
    waste_multiplier = 1 + (loss_percent / 100)
    final_raw_material = int(total_raw_material * waste_multiplier + 0.5)
    
    return jsonify({"result": final_raw_material})

@app.route('/api/calculate-production-time/<int:product_id>', methods=['GET'])
@with_db_connection
def calculate_production_time(product_id, cursor, connection):
    """Расчет времени производства для продукта"""
    query = '''
    SELECT 
        SUM(pw.manufacturing_time_hours) as total_time,
        COUNT(*) as workshops_count,
        STRING_AGG(w.workshop_name, ', ') as workshops_list
    FROM product_workshops pw
    JOIN workshops w ON pw.workshop_id = w.workshop_id
    WHERE pw.product_id = %s
    '''
    cursor.execute(query, (product_id,))
    result = cursor.fetchone()
    
    if result and result['total_time']:
        return jsonify({
            'total_time': float(result['total_time']),
            'workshops_count': result['workshops_count'],
            'workshops_list': result['workshops_list']
        })
    else:
        return jsonify({'total_time': 0, 'workshops_count': 0, 'workshops_list': ''})

# ==================== CRUD ОПЕРАЦИИ ДЛЯ ПРОДУКЦИИ ====================

@app.route('/api/products', methods=['POST'])
@with_db_connection
def add_product(cursor, connection):
    """Добавление нового продукта"""
    data = request.json
    
    try:
        article = data.get('article')
        name = data.get('name')
        product_type_id = int(data.get('product_type_id'))
        material_type_id = int(data.get('material_type_id'))
        min_price = Decimal(str(data.get('min_price', 0)))
        
        if min_price <= 0:
            return jsonify({'error': 'Цена должна быть положительной'}), 400
        
        # Проверяем уникальность артикула
        cursor.execute('SELECT 1 FROM products WHERE article_number = %s', (article,))
        if cursor.fetchone():
            return jsonify({'error': 'Продукт с таким артикулом уже существует'}), 400
        
        # Проверяем существование типов
        cursor.execute('SELECT 1 FROM product_types WHERE product_type_id = %s', (product_type_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Указанный тип продукции не существует'}), 400
        
        cursor.execute('SELECT 1 FROM material_types WHERE material_type_id = %s', (material_type_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Указанный тип материала не существует'}), 400
        
        # Добавляем продукт
        query = '''
        INSERT INTO products 
        (article_number, product_name, product_type_id, material_type_id, minimum_partner_price)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING product_id
        '''
        
        cursor.execute(query, (article, name, product_type_id, material_type_id, min_price))
        new_id = cursor.fetchone()['product_id']
        
        return jsonify({
            'success': True,
            'message': 'Продукт успешно добавлен',
            'product_id': new_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@with_db_connection
def update_product(product_id, cursor, connection):
    """Обновление существующего продукта"""
    data = request.json
    
    try:
        # Проверяем существование продукта
        cursor.execute('SELECT 1 FROM products WHERE product_id = %s', (product_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Продукт не найден'}), 404
        
        article = data.get('article')
        name = data.get('name')
        product_type_id = int(data.get('product_type_id'))
        material_type_id = int(data.get('material_type_id'))
        min_price = Decimal(str(data.get('min_price', 0)))
        
        if min_price <= 0:
            return jsonify({'error': 'Цена должна быть положительной'}), 400
        
        # Проверяем уникальность артикула (исключая текущий продукт)
        cursor.execute('SELECT 1 FROM products WHERE article_number = %s AND product_id != %s', 
                      (article, product_id))
        if cursor.fetchone():
            return jsonify({'error': 'Продукт с таким артикулом уже существует'}), 400
        
        # Проверяем существование типов
        cursor.execute('SELECT 1 FROM product_types WHERE product_type_id = %s', (product_type_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Указанный тип продукции не существует'}), 400
        
        cursor.execute('SELECT 1 FROM material_types WHERE material_type_id = %s', (material_type_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Указанный тип материала не существует'}), 400
        
        # Обновляем продукт
        query = '''
        UPDATE products 
        SET article_number = %s,
            product_name = %s,
            product_type_id = %s,
            material_type_id = %s,
            minimum_partner_price = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE product_id = %s
        '''
        
        cursor.execute(query, (article, name, product_type_id, material_type_id, min_price, product_id))
        
        return jsonify({
            'success': True,
            'message': 'Продукт успешно обновлен'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@with_db_connection
def delete_product(product_id, cursor, connection):
    """Удаление продукта"""
    try:
        # Проверяем существование продукта
        cursor.execute('SELECT 1 FROM products WHERE product_id = %s', (product_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Продукт не найден'}), 404
        
        # Удаляем продукт (CASCADE удалит связанные записи в product_workshops)
        cursor.execute('DELETE FROM products WHERE product_id = %s', (product_id,))
        
        return jsonify({
            'success': True,
            'message': 'Продукт успешно удален'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== HTML ШАБЛОН С ФОРМОЙ ДОБАВЛЕНИЯ/РЕДАКТИРОВАНИЯ ====================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium Furniture Solutions</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: Candara, 'Segoe UI', sans-serif;
            background-color: #FFFFFF;
            color: #333;
            line-height: 1.6;
        }

        header {
            background-color: #FFFFFF;
            border-bottom: 2px solid #D2DFFF;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        header img {
            height: 50px;
            width: auto;
        }

        header h1 {
            color: #355CBD;
            font-size: 24px;
            margin: 0;
        }

        .container {
            display: flex;
            height: calc(100vh - 70px - 60px);
        }

        aside {
            width: 250px;
            background-color: #D2DFFF;
            padding: 20px;
            border-right: 1px solid #355CBD;
            overflow-y: auto;
        }

        aside nav ul {
            list-style: none;
        }

        aside nav li {
            margin: 10px 0;
        }

        aside nav button {
            width: 100%;
            padding: 12px 15px;
            border: none;
            background-color: transparent;
            color: #333;
            text-align: left;
            cursor: pointer;
            border-radius: 5px;
            transition: all 0.3s ease;
            font-family: Candara, sans-serif;
            font-size: 14px;
        }

        aside nav button:hover {
            background-color: #355CBD;
            color: white;
            font-weight: bold;
        }

        aside nav button.active {
            background-color: #355CBD;
            color: white;
            font-weight: bold;
        }

        main {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
            background-color: #FFFFFF;
        }

        h2 {
            color: #355CBD;
            margin-bottom: 25px;
            font-size: 28px;
        }

        h3 {
            color: #355CBD;
            margin-bottom: 15px;
            font-size: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background-color: #FFFFFF;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 5px;
            overflow: hidden;
        }

        table thead {
            background-color: #355CBD;
            color: white;
        }

        table th {
            padding: 15px;
            text-align: left;
            font-weight: bold;
        }

        table td {
            padding: 12px 15px;
            border-bottom: 1px solid #D2DFFF;
        }

        table tbody tr:hover {
            background-color: #F0F4FF;
        }

        table tbody tr:nth-child(even) {
            background-color: #FAFBFF;
        }

        button.btn-primary {
            padding: 10px 20px;
            background-color: #355CBD;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-family: Candara, sans-serif;
            font-size: 14px;
            margin-bottom: 20px;
            transition: background-color 0.3s;
        }

        button.btn-primary:hover {
            background-color: #1e3a6a;
        }

        button.btn-secondary {
            padding: 10px 20px;
            background-color: #6c757d;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-family: Candara, sans-serif;
            font-size: 14px;
            margin-bottom: 20px;
            transition: background-color 0.3s;
        }

        button.btn-secondary:hover {
            background-color: #545b62;
        }

        button.btn-success {
            padding: 10px 20px;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-family: Candara, sans-serif;
            font-size: 14px;
            transition: background-color 0.3s;
        }

        button.btn-success:hover {
            background-color: #218838;
        }

        button.btn-danger {
            padding: 6px 12px;
            background-color: #dc2626;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
            transition: background-color 0.3s;
        }

        button.btn-danger:hover {
            background-color: #b91c1c;
        }

        button.btn-warning {
            padding: 6px 12px;
            background-color: #f59e0b;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
            transition: background-color 0.3s;
        }

        button.btn-warning:hover {
            background-color: #d97706;
        }

        .form-container {
            background-color: #F9FAFB;
            padding: 30px;
            border-radius: 8px;
            border: 1px solid #D2DFFF;
            max-width: 700px;
            margin: 20px 0;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }

        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #D2DFFF;
            border-radius: 5px;
            font-family: Candara, sans-serif;
            font-size: 14px;
            background-color: white;
        }

        input:focus, select:focus {
            outline: none;
            border-color: #355CBD;
            box-shadow: 0 0 5px rgba(53, 92, 189, 0.3);
        }

        .form-row {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }

        .form-row .form-group {
            flex: 1;
        }

        .alert {
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            display: none;
        }

        .alert.show {
            display: block;
        }

        .alert-success {
            background-color: #d1fae5;
            color: #065f46;
            border: 1px solid #6ee7b7;
        }

        .alert-error {
            background-color: #fee2e2;
            color: #991b1b;
            border: 1px solid #fca5a5;
        }

        .alert-info {
            background-color: #dbeafe;
            color: #1e40af;
            border: 1px solid #93c5fd;
        }

        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: linear-gradient(135deg, #355CBD, #1e40af);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        .stat-card h3 {
            margin: 0 0 10px 0;
            font-size: 16px;
            opacity: 0.9;
            color: white;
        }

        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
        }

        .page {
            display: none;
        }

        .page.active {
            display: block;
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
        }

        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 8px;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            position: relative;
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 1px solid #D2DFFF;
            padding-bottom: 15px;
        }

        .modal-title {
            color: #355CBD;
            font-size: 22px;
            margin: 0;
        }

        .modal-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
        }

        .modal-close:hover {
            color: #355CBD;
        }

        .modal-footer {
            margin-top: 30px;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            border-top: 1px solid #D2DFFF;
            padding-top: 20px;
        }

        .action-buttons {
            display: flex;
            gap: 5px;
        }

        footer {
            background-color: #D2DFFF;
            border-top: 1px solid #355CBD;
            padding: 15px 20px;
            text-align: center;
            color: #333;
            font-size: 13px;
        }

        .required::after {
            content: " *";
            color: #dc2626;
        }

        .error-message {
            color: #dc2626;
            font-size: 12px;
            margin-top: 5px;
            display: none;
        }

        input.error, select.error {
            border-color: #dc2626;
        }
    </style>
</head>
<body>
    <header>
        <img src="https://agi-prod-file-upload-public-main-use1.s3.amazonaws.com/fb69424b-f1f8-4242-8eb1-c9d897e3566e" alt="Logo">
        <h1>Premium Furniture Solutions</h1>
    </header>

    <div class="container">
        <aside>
            <nav>
                <ul>
                    <li><button class="nav-btn active" data-page="products">📦 Продукция</button></li>
                    <li><button class="nav-btn" data-page="workshops">🏭 Цеха</button></li>
                    <li><button class="nav-btn" data-page="calculator">🧮 Сырье</button></li>
                    <li><button class="nav-btn" data-page="production-time">⏱️ Время</button></li>
                </ul>
            </nav>
        </aside>

        <main>
            <!-- Продукция -->
            <div id="page-products" class="page active">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2>Список продукции</h2>
                    <button class="btn-success" onclick="openAddProductModal()">+ Добавить продукт</button>
                </div>
                <div id="alert-container-products"></div>
                <table>
                    <thead>
                        <tr>
                            <th>Артикул</th>
                            <th>Наименование</th>
                            <th>Тип</th>
                            <th>Материал</th>
                            <th>Мин. цена (₽)</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody id="products-tbody"></tbody>
                </table>
            </div>

            <!-- Цеха -->
            <div id="page-workshops" class="page">
                <h2>Цеха производства</h2>
                <div id="workshops-stats" class="stats-container"></div>
                <table>
                    <thead>
                        <tr>
                            <th>Название цеха</th>
                            <th>Тип цеха</th>
                            <th>Количество сотрудников</th>
                        </tr>
                    </thead>
                    <tbody id="workshops-tbody"></tbody>
                </table>
            </div>

            <!-- Калькулятор сырья -->
            <div id="page-calculator" class="page">
                <h2>Калькулятор сырья</h2>
                <div id="alert-container-calc"></div>
                <div class="form-container">
                    <h3>Расчет необходимого сырья</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="required">Тип продукции</label>
                            <select id="calc-product-type">
                                <option value="">-- Выберите --</option>
                            </select>
                            <div class="error-message" id="error-product-type">Выберите тип продукции</div>
                        </div>
                        <div class="form-group">
                            <label class="required">Тип материала</label>
                            <select id="calc-material-type">
                                <option value="">-- Выберите --</option>
                            </select>
                            <div class="error-message" id="error-material-type">Выберите тип материала</div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="required">Количество (шт)</label>
                            <input type="number" id="calc-quantity" min="1" value="1" step="1">
                            <div class="error-message" id="error-quantity">Введите количество больше 0</div>
                        </div>
                        <div class="form-group">
                            <label class="required">Параметр 1 (м)</label>
                            <input type="number" id="calc-param1" step="0.1" min="0.1" value="1.0">
                            <div class="error-message" id="error-param1">Введите положительное число</div>
                        </div>
                        <div class="form-group">
                            <label class="required">Параметр 2 (м)</label>
                            <input type="number" id="calc-param2" step="0.1" min="0.1" value="1.0">
                            <div class="error-message" id="error-param2">Введите положительное число</div>
                        </div>
                    </div>
                    <button class="btn-primary" onclick="calculateRawMaterials()">Рассчитать сырье</button>
                </div>
                <div id="calc-result" class="form-container" style="display: none; background-color: #f0f9ff;">
                    <h3>📊 Результат расчета</h3>
                    <div id="result-details"></div>
                </div>
            </div>

            <!-- Время производства -->
            <div id="page-production-time" class="page">
                <h2>Калькулятор времени производства</h2>
                <div id="alert-container-time"></div>
                <div class="form-container">
                    <h3>Расчет времени изготовления</h3>
                    <div class="form-group">
                        <label>Выберите продукт</label>
                        <select id="prod-time-product">
                            <option value="">-- Выберите --</option>
                        </select>
                    </div>
                    <button class="btn-primary" onclick="calculateProductionTime()">Рассчитать время</button>
                </div>
                <div id="time-result" class="form-container" style="display: none; background-color: #f0fff4;">
                    <h3>⏱️ Время производства</h3>
                    <div id="time-details"></div>
                </div>
            </div>
        </main>
    </div>

    <!-- Модальное окно добавления/редактирования продукта -->
    <div id="productModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title" id="modal-title">Добавление нового продукта</h3>
                <button class="modal-close" onclick="closeProductModal()">&times;</button>
            </div>
            <form id="productForm" onsubmit="saveProduct(event)">
                <input type="hidden" id="edit-product-id" value="">
                
                <div class="form-group">
                    <label class="required">Артикул</label>
                    <input type="text" id="product-article" required>
                    <div class="error-message" id="error-article">Введите артикул</div>
                </div>
                
                <div class="form-group">
                    <label class="required">Наименование</label>
                    <input type="text" id="product-name" required>
                    <div class="error-message" id="error-name">Введите наименование</div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label class="required">Тип продукции</label>
                        <select id="product-type" required>
                            <option value="">-- Выберите --</option>
                        </select>
                        <div class="error-message" id="error-product-type-form">Выберите тип продукции</div>
                    </div>
                    <div class="form-group">
                        <label class="required">Тип материала</label>
                        <select id="product-material" required>
                            <option value="">-- Выберите --</option>
                        </select>
                        <div class="error-message" id="error-material-form">Выберите тип материала</div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="required">Минимальная цена для партнера (₽)</label>
                    <input type="number" id="product-price" min="0.01" step="0.01" required>
                    <div class="error-message" id="error-price">Введите положительную цену</div>
                </div>
                
                <div class="modal-footer">
                    <button type="button" class="btn-secondary" onclick="closeProductModal()">Отмена</button>
                    <button type="submit" class="btn-primary" id="modal-save-btn">Сохранить</button>
                </div>
            </form>
        </div>
    </div>

    <footer>
        © 2006–2025 Premium Furniture Solutions.
    </footer>

    <script>
        let products = [];
        let productTypes = [];
        let materialTypes = [];
        let workshops = [];

        // Загрузка данных
        async function loadData() {
            try {
                // Загружаем все данные параллельно
                const [productsRes, typesRes, materialsRes, workshopsRes] = await Promise.all([
                    fetch('/api/products').then(r => r.json()),
                    fetch('/api/product-types').then(r => r.json()),
                    fetch('/api/material-types').then(r => r.json()),
                    fetch('/api/workshops').then(r => r.json())
                ]);

                products = productsRes;
                productTypes = typesRes;
                materialTypes = materialsRes;
                workshops = workshopsRes;

                renderProducts();
                renderWorkshops();
                loadProductTypesForCalculator();
                loadMaterialTypes();
                loadProductsForProductionTime();
                loadProductTypesForForm();
                loadMaterialTypesForForm();
                
                showAlert('✅ Данные загружены успешно', 'success', 'alert-container-products');
            } catch (error) {
                showAlert('❌ Ошибка загрузки данных: ' + error.message, 'error', 'alert-container-products');
            }
        }

        // Навигация
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                const page = e.target.dataset.page;
                document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
                document.getElementById(`page-${page}`).classList.add('active');
            });
        });

        // Рендер продуктов
        function renderProducts() {
            const tbody = document.getElementById('products-tbody');
            tbody.innerHTML = products.map(product => `
                <tr>
                    <td><strong>${product.article}</strong></td>
                    <td>${product.name}</td>
                    <td>${product.product_type_name || 'N/A'}</td>
                    <td>${product.material_name || 'N/A'}</td>
                    <td>₽${product.min_price ? product.min_price.toFixed(2) : '0.00'}</td>
                    <td class="action-buttons">
                        <button class="btn-warning" onclick="openEditProductModal(${product.id})">✏️</button>
                        <button class="btn-danger" onclick="deleteProduct(${product.id})">🗑️</button>
                    </td>
                </tr>
            `).join('');
        }

        // Удаление продукта
        async function deleteProduct(productId) {
            if (!confirm('Вы уверены, что хотите удалить этот продукт?')) {
                return;
            }

            try {
                const response = await fetch(`/api/products/${productId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    products = products.filter(p => p.id !== productId);
                    renderProducts();
                    loadProductsForProductionTime();
                    showAlert(result.message, 'success', 'alert-container-products');
                } else {
                    showAlert('❌ ' + (result.error || 'Ошибка удаления'), 'error', 'alert-container-products');
                }
            } catch (error) {
                showAlert('❌ Ошибка: ' + error.message, 'error', 'alert-container-products');
            }
        }

        // Открытие модального окна для добавления
        function openAddProductModal() {
            document.getElementById('modal-title').textContent = 'Добавление нового продукта';
            document.getElementById('edit-product-id').value = '';
            document.getElementById('product-article').value = '';
            document.getElementById('product-name').value = '';
            document.getElementById('product-price').value = '';
            document.getElementById('product-type').value = '';
            document.getElementById('product-material').value = '';
            
            clearFormErrors();
            document.getElementById('productModal').style.display = 'block';
        }

        // Открытие модального окна для редактирования
        async function openEditProductModal(productId) {
            try {
                const response = await fetch(`/api/product/${productId}`);
                const product = await response.json();
                
                if (response.ok) {
                    document.getElementById('modal-title').textContent = 'Редактирование продукта';
                    document.getElementById('edit-product-id').value = product.id;
                    document.getElementById('product-article').value = product.article;
                    document.getElementById('product-name').value = product.name;
                    document.getElementById('product-price').value = product.min_price || '';
                    document.getElementById('product-type').value = product.product_type_id || '';
                    document.getElementById('product-material').value = product.material_type_id || '';
                    
                    clearFormErrors();
                    document.getElementById('productModal').style.display = 'block';
                } else {
                    showAlert('❌ Ошибка загрузки продукта', 'error', 'alert-container-products');
                }
            } catch (error) {
                showAlert('❌ Ошибка: ' + error.message, 'error', 'alert-container-products');
            }
        }

        // Закрытие модального окна
        function closeProductModal() {
            document.getElementById('productModal').style.display = 'none';
            clearFormErrors();
        }

        // Очистка ошибок формы
        function clearFormErrors() {
            document.querySelectorAll('.error-message').forEach(el => {
                el.style.display = 'none';
            });
            document.querySelectorAll('input.error, select.error').forEach(el => {
                el.classList.remove('error');
            });
        }

        // Загрузка типов продукции для формы
        function loadProductTypesForForm() {
            const select = document.getElementById('product-type');
            select.innerHTML = '<option value="">-- Выберите --</option>' + 
                productTypes.map(pt => `<option value="${pt.id}">${pt.name}</option>`).join('');
        }

        // Загрузка типов материалов для формы
        function loadMaterialTypesForForm() {
            const select = document.getElementById('product-material');
            select.innerHTML = '<option value="">-- Выберите --</option>' + 
                materialTypes.map(mt => `<option value="${mt.id}">${mt.name}</option>`).join('');
        }

        // Сохранение продукта
        async function saveProduct(event) {
            event.preventDefault();
            
            const productId = document.getElementById('edit-product-id').value;
            const article = document.getElementById('product-article').value.trim();
            const name = document.getElementById('product-name').value.trim();
            const productTypeId = document.getElementById('product-type').value;
            const materialTypeId = document.getElementById('product-material').value;
            const price = parseFloat(document.getElementById('product-price').value);
            
            // Валидация
            let isValid = true;
            clearFormErrors();
            
            if (!article) {
                document.getElementById('error-article').style.display = 'block';
                document.getElementById('product-article').classList.add('error');
                isValid = false;
            }
            
            if (!name) {
                document.getElementById('error-name').style.display = 'block';
                document.getElementById('product-name').classList.add('error');
                isValid = false;
            }
            
            if (!productTypeId) {
                document.getElementById('error-product-type-form').style.display = 'block';
                document.getElementById('product-type').classList.add('error');
                isValid = false;
            }
            
            if (!materialTypeId) {
                document.getElementById('error-material-form').style.display = 'block';
                document.getElementById('product-material').classList.add('error');
                isValid = false;
            }
            
            if (!price || price <= 0) {
                document.getElementById('error-price').style.display = 'block';
                document.getElementById('product-price').classList.add('error');
                isValid = false;
            }
            
            if (!isValid) {
                return;
            }
            
            const productData = {
                article: article,
                name: name,
                product_type_id: parseInt(productTypeId),
                material_type_id: parseInt(materialTypeId),
                min_price: price
            };
            
            try {
                const url = productId ? `/api/products/${productId}` : '/api/products';
                const method = productId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(productData)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    closeProductModal();
                    await loadData(); // Перезагружаем все данные
                    showAlert(result.message, 'success', 'alert-container-products');
                } else {
                    showAlert('❌ ' + (result.error || 'Ошибка сохранения'), 'error', 'alert-container-products');
                }
            } catch (error) {
                showAlert('❌ Ошибка: ' + error.message, 'error', 'alert-container-products');
            }
        }

        // Рендер цехов
        function renderWorkshops() {
            const tbody = document.getElementById('workshops-tbody');
            const statsContainer = document.getElementById('workshops-stats');

            tbody.innerHTML = workshops.map(w => `
                <tr>
                    <td><strong>${w.name}</strong></td>
                    <td>${w.workshop_type || 'N/A'}</td>
                    <td style="text-align: center;">${w.people_count} чел.</td>
                </tr>
            `).join('');

            const totalPeople = workshops.reduce((sum, w) => sum + w.people_count, 0);
            const totalWorkshops = workshops.length;

            statsContainer.innerHTML = `
                <div class="stat-card">
                    <h3>Всего цехов</h3>
                    <div class="value">${totalWorkshops}</div>
                </div>
                <div class="stat-card">
                    <h3>Всего сотрудников</h3>
                    <div class="value">${totalPeople}</div>
                </div>
                <div class="stat-card">
                    <h3>Среднее количество</h3>
                    <div class="value">${Math.round(totalPeople / totalWorkshops)}</div>
                </div>
            `;
        }

        // Загрузка типов продукции для калькулятора
        function loadProductTypesForCalculator() {
            const select = document.getElementById('calc-product-type');
            select.innerHTML = '<option value="">-- Выберите --</option>' + 
                productTypes.map(pt => `<option value="${pt.id}">${pt.name}</option>`).join('');
        }

        // Загрузка типов материалов
        function loadMaterialTypes() {
            const select = document.getElementById('calc-material-type');
            select.innerHTML = '<option value="">-- Выберите --</option>' + 
                materialTypes.map(mt => `<option value="${mt.id}">${mt.name}</option>`).join('');
        }

        // Загрузка продуктов для времени производства
        function loadProductsForProductionTime() {
            const select = document.getElementById('prod-time-product');
            select.innerHTML = '<option value="">-- Выберите --</option>' + 
                products.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
        }

        // Расчет сырья
        async function calculateRawMaterials() {
            const productTypeId = parseInt(document.getElementById('calc-product-type').value);
            const materialTypeId = parseInt(document.getElementById('calc-material-type').value);
            const quantity = parseInt(document.getElementById('calc-quantity').value);
            const param1 = parseFloat(document.getElementById('calc-param1').value);
            const param2 = parseFloat(document.getElementById('calc-param2').value);

            // Валидация
            let isValid = true;
            
            if (!productTypeId) {
                document.getElementById('error-product-type').style.display = 'block';
                document.getElementById('calc-product-type').classList.add('error');
                isValid = false;
            }
            
            if (!materialTypeId) {
                document.getElementById('error-material-type').style.display = 'block';
                document.getElementById('calc-material-type').classList.add('error');
                isValid = false;
            }
            
            if (!quantity || quantity <= 0) {
                document.getElementById('error-quantity').style.display = 'block';
                document.getElementById('calc-quantity').classList.add('error');
                isValid = false;
            }
            
            if (!param1 || param1 <= 0) {
                document.getElementById('error-param1').style.display = 'block';
                document.getElementById('calc-param1').classList.add('error');
                isValid = false;
            }
            
            if (!param2 || param2 <= 0) {
                document.getElementById('error-param2').style.display = 'block';
                document.getElementById('calc-param2').classList.add('error');
                isValid = false;
            }
            
            if (!isValid) {
                return;
            }

            try {
                const response = await fetch('/api/calculate-raw-materials', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        product_type_id: productTypeId, 
                        material_type_id: materialTypeId, 
                        quantity, 
                        param1, 
                        param2 
                    })
                });

                const data = await response.json();
                if (data.result === -1) {
                    showAlert('❌ Ошибка расчета. Проверьте введенные данные', 'error', 'alert-container-calc');
                    return;
                }

                const productType = productTypes.find(pt => pt.id === productTypeId);
                const materialType = materialTypes.find(mt => mt.id === materialTypeId);

                document.getElementById('result-details').innerHTML = `
                    <p><strong>Тип продукции:</strong> ${productType.name}</p>
                    <p><strong>Тип материала:</strong> ${materialType.name}</p>
                    <p><strong>Количество:</strong> ${quantity} шт</p>
                    <p><strong>Параметры:</strong> ${param1}м × ${param2}м</p>
                    <p><strong>Коэффициент типа:</strong> ${productType.coefficient}</p>
                    <p><strong>Потери материала:</strong> ${materialType.waste_percent}%</p>
                    <hr style="margin: 15px 0; border: none; border-top: 1px solid #D2DFFF;">
                    <p style="font-size: 20px; font-weight: bold; color: #355CBD;">📦 Необходимо сырья: ${data.result} кг</p>
                `;
                document.getElementById('calc-result').style.display = 'block';
                showAlert(`✅ Расчет выполнен: требуется ${data.result} кг сырья`, 'success', 'alert-container-calc');
                
            } catch (error) {
                showAlert('❌ Ошибка: ' + error.message, 'error', 'alert-container-calc');
            }
        }

        // Расчет времени производства
        async function calculateProductionTime() {
            const productId = parseInt(document.getElementById('prod-time-product').value);
            if (!productId) {
                showAlert('❌ Выберите продукт', 'error', 'alert-container-time');
                return;
            }

            try {
                const response = await fetch(`/api/calculate-production-time/${productId}`);
                const data = await response.json();
                
                if (response.ok) {
                    const product = products.find(p => p.id === productId);
                    
                    // Получаем детали по цехам
                    const workshopsResponse = await fetch(`/api/product-workshops/${productId}`);
                    const workshopsData = await workshopsResponse.json();
                    
                    let workshopsDetails = '';
                    if (workshopsData && workshopsData.length > 0) {
                        workshopsDetails = workshopsData.map(w => 
                            `<p style="margin-left: 20px;">• ${w.workshop_name}: ${w.production_time} ч</p>`
                        ).join('');
                    }
                    
                    document.getElementById('time-details').innerHTML = `
                        <p><strong>Продукт:</strong> ${product.name}</p>
                        <p style="margin-bottom: 15px; color: #355CBD;">Участвующие цеха (${data.workshops_count}):</p>
                        ${workshopsDetails}
                        <hr style="margin: 20px 0; border: none; border-top: 1px solid #D2DFFF;">
                        <p style="font-size: 22px; color: #1e40af; font-weight: bold;">⏱️ Итого время производства: ${data.total_time.toFixed(1)} часов</p>
                    `;
                    document.getElementById('time-result').style.display = 'block';
                    showAlert(`✅ Время производства: ${data.total_time.toFixed(1)} часов`, 'success', 'alert-container-time');
                } else {
                    showAlert('❌ Ошибка расчета времени', 'error', 'alert-container-time');
                }
            } catch (error) {
                showAlert('❌ Ошибка: ' + error.message, 'error', 'alert-container-time');
            }
        }

        // Показ уведомлений
        function showAlert(message, type, containerId) {
            const container = document.getElementById(containerId);
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} show`;
            alert.textContent = message;
            container.innerHTML = '';
            container.appendChild(alert);

            setTimeout(() => {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 300);
            }, 4000);
        }

        // Закрытие модального окна при клике вне его
        window.onclick = function(event) {
            const modal = document.getElementById('productModal');
            if (event.target === modal) {
                closeProductModal();
            }
        }

        // Инициализация при загрузке страницы
        document.addEventListener('DOMContentLoaded', loadData);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Premium Furniture Solutions - PostgreSQL Edition")
    print("="*60)
    
    # Инициализация базы данных
    print("🔄 Инициализация базы данных...")
    init_database()
    
    print("✅ База данных готова")
    print("🌐 Приложение запущено на http://localhost:5000")
    print("📌 Откройте браузер и перейдите по адресу выше")
    print("💡 Нажмите Ctrl+C для остановки")
    print("="*60 + "\n")
    
    # Запуск приложения
    app.run(debug=True, use_reloader=False)