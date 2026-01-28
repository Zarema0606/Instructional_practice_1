from flask import Flask, render_template_string, jsonify, request
import json

app = Flask(__name__)

# ==================== ДАННЫЕ ====================
PRODUCT_TYPES = [
    {"id": 1, "name": "Софа", "coefficient": 1.2},
    {"id": 2, "name": "Пуфик", "coefficient": 0.8},
    {"id": 3, "name": "Стол", "coefficient": 0.9},
    {"id": 4, "name": "Табурет", "coefficient": 0.6},
]

MATERIAL_TYPES = [
    {"id": 1, "name": "Дуб натуральный", "waste_percent": 5},
    {"id": 2, "name": "Экокожа премиум", "waste_percent": 3},
    {"id": 3, "name": "Акриловое стекло", "waste_percent": 8},
    {"id": 4, "name": "Ясень мореный", "waste_percent": 2},
]

WORKSHOPS = [
    {"id": 1, "name": " Деревообрабатывающий участок", "people_count": 15, "production_time": 8},
    {"id": 2, "name": "Отдел мягкой мебели", "people_count": 12, "production_time": 6},
    {"id": 3, "name": "Сборочный комплекс", "people_count": 10, "production_time": 4},
    {"id": 4, "name": " Отдел ОТК", "people_count": 5, "production_time": 2},
]

PRODUCT_WORKSHOPS = [
    {"product_id": 1, "workshop_id": 1},
    {"product_id": 1, "workshop_id": 2},
    {"product_id": 1, "workshop_id": 3},
    {"product_id": 2, "workshop_id": 2},
    {"product_id": 2, "workshop_id": 3},
    {"product_id": 3, "workshop_id": 1},
    {"product_id": 3, "workshop_id": 3},
    {"product_id": 4, "workshop_id": 2},
    {"product_id": 4, "workshop_id": 3},
]

INITIAL_PRODUCTS = [
    {"id": 1, "article": "SOFA-PRO", "name": "Софа Executive", "product_type_id": 1, "material": "Дуб натуральный", "min_price": 25000, "param1": 2.5, "param2": 1.8},
    {"id": 2, "article": "OTTO-001", "name": "Оттоманка Elite", "product_type_id": 2, "material": "Экокожа премиум", "min_price": 12000, "param1": 1.2, "param2": 1.0},
    {"id": 3, "article": "DESK-PRO", "name": "Рабочий стол Minimal", "product_type_id": 3, "material": "Акриловое стекло", "min_price": 8500, "param1": 1.5, "param2": 0.8},
    {"id": 4, "article": "BAR-001", "name": "Барный стул Manhattan", "product_type_id": 4, "material": "Ясень мореный", "min_price": 5000, "param1": 0.5, "param2": 0.5},
]

products = INITIAL_PRODUCTS.copy()


# ==================== МЕТОДЫ ====================

def calculate_raw_materials(product_type_id: int, material_type_id: int, quantity: int, param1: float, param2: float) -> int:
    """
    CORE METHOD: Расчет необходимого количества сырья с учетом потерь
    Формула: (param1 × param2 × коэффициент_типа × количество) × (1 + процент_потерь)
    
    Параметры:
        product_type_id - ID типа продукции
        material_type_id - ID типа материала
        quantity - количество единиц
        param1, param2 - параметры размера
        
    Возвращает: целое число килограммов или -1 при ошибке
    """
    product_type = next((pt for pt in PRODUCT_TYPES if pt["id"] == product_type_id), None)
    if not product_type:
        return -1

    material_type = next((mt for mt in MATERIAL_TYPES if mt["id"] == material_type_id), None)
    if not material_type:
        return -1

    if quantity <= 0 or param1 <= 0 or param2 <= 0:
        return -1

    raw_material_per_unit = param1 * param2 * product_type["coefficient"]
    total_raw_material = raw_material_per_unit * quantity
    waste_multiplier = 1 + (material_type["waste_percent"] / 100)
    final_raw_material = int(total_raw_material * waste_multiplier + 0.5)

    return final_raw_material


# ==================== API ENDPOINTS ====================

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/api/product-types', methods=['GET'])
def get_product_types():
    return jsonify(PRODUCT_TYPES)

@app.route('/api/material-types', methods=['GET'])
def get_material_types():
    return jsonify(MATERIAL_TYPES)

@app.route('/api/workshops', methods=['GET'])
def get_workshops():
    return jsonify(WORKSHOPS)

@app.route('/api/product-workshops', methods=['GET'])
def get_product_workshops():
    return jsonify(PRODUCT_WORKSHOPS)

@app.route('/api/calculate-raw-materials', methods=['POST'])
def api_calculate_raw_materials():
    data = request.json
    result = calculate_raw_materials(
        data.get('product_type_id'),
        data.get('material_type_id'),
        data.get('quantity'),
        data.get('param1'),
        data.get('param2')
    )
    return jsonify({"result": result})

@app.route('/api/delete-product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    global products
    products = [p for p in products if p["id"] != product_id]
    return jsonify({"success": True})


# ==================== HTML СТРАНИЦА ====================

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
        }

        button.btn-primary:hover {
            background-color: #1e3a6a;
        }

        button.btn-danger {
            padding: 6px 12px;
            background-color: #dc2626;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
        }

        button.btn-danger:hover {
            background-color: #b91c1c;
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

        footer {
            background-color: #D2DFFF;
            border-top: 1px solid #355CBD;
            padding: 15px 20px;
            text-align: center;
            color: #333;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <header>
        <img src="https://agi-prod-file-upload-public-main-use1.s3.amazonaws.com/fb69424b-f1f8-4242-8eb1-c9d897e3566e" alt="Logo" style="height: 50px;">
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
                <h2>Список продукции</h2>
                <div id="alert-container"></div>
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
                            <th>Количество сотрудников</th>
                            <th>Время производства (ч)</th>
                        </tr>
                    </thead>
                    <tbody id="workshops-tbody"></tbody>
                </table>
            </div>

            <!-- Калькулятор сырья -->
            <div id="page-calculator" class="page">
                <h2>Калькулятор сырья</h2>
                <div id="alert-container-calc"></div>
                <div class="form-container" style="max-width: 700px;">
                    <h3 style="color: #355CBD; margin-bottom: 20px;">Расчет необходимого сырья</h3>
                    <div class="form-group">
                        <label>Тип продукции</label>
                        <select id="calc-product-type"></select>
                    </div>
                    <div class="form-group">
                        <label>Тип материала</label>
                        <select id="calc-material-type"></select>
                    </div>
                    <div class="form-group">
                        <label>Количество (шт)</label>
                        <input type="number" id="calc-quantity" min="1" value="1">
                    </div>
                    <div class="form-group">
                        <label>Параметр 1 (м)</label>
                        <input type="number" id="calc-param1" step="0.1" min="0.1" value="1.0">
                    </div>
                    <div class="form-group">
                        <label>Параметр 2 (м)</label>
                        <input type="number" id="calc-param2" step="0.1" min="0.1" value="1.0">
                    </div>
                    <button class="btn-primary" onclick="calculateRawMaterials()">Рассчитать сырье</button>
                </div>
                <div id="calc-result" class="form-container" style="display: none; background-color: #f0f9ff; max-width: 700px;">
                    <h3 style="color: #355CBD; margin-bottom: 15px;">📊 Результат расчета</h3>
                    <div id="result-details"></div>
                </div>
            </div>

            <!-- Время производства -->
            <div id="page-production-time" class="page">
                <h2>Калькулятор времени производства</h2>
                <div id="alert-container-time"></div>
                <div class="form-container" style="max-width: 600px;">
                    <h3 style="color: #355CBD; margin-bottom: 20px;">Расчет времени изготовления</h3>
                    <div class="form-group">
                        <label>Выберите продукт</label>
                        <select id="prod-time-product"></select>
                    </div>
                    <button class="btn-primary" onclick="calculateProductionTime()">Рассчитать время</button>
                </div>
                <div id="time-result" class="form-container" style="display: none; background-color: #f0fff4; max-width: 600px;">
                    <h3 style="color: #355CBD; margin-bottom: 15px;">⏱️ Время производства</h3>
                    <div id="time-details"></div>
                </div>
            </div>
        </main>
    </div>

    <footer>
        © 2025 Premium Furniture Solutions.
    </footer>

    <script>
        let products = [];
        let productTypes = [];
        let materialTypes = [];
        let workshops = [];
        let productWorkshops = [];

        // Загрузка данных
        async function loadData() {
            products = await fetch('/api/products').then(r => r.json());
            productTypes = await fetch('/api/product-types').then(r => r.json());
            materialTypes = await fetch('/api/material-types').then(r => r.json());
            workshops = await fetch('/api/workshops').then(r => r.json());
            productWorkshops = await fetch('/api/product-workshops').then(r => r.json());

            renderProducts();
            renderWorkshops();
            loadProductTypesForCalculator();
            loadMaterialTypes();
            loadProductsForProductionTime();
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
            tbody.innerHTML = products.map(product => {
                const productType = productTypes.find(pt => pt.id === product.product_type_id);
                return `
                    <tr>
                        <td><strong>${product.article}</strong></td>
                        <td>${product.name}</td>
                        <td>${productType ? productType.name : 'N/A'}</td>
                        <td>${product.material}</td>
                        <td>₽${product.min_price.toFixed(2)}</td>
                        <td>
                            <button class="btn-danger" onclick="deleteProduct(${product.id})">🗑️ Удалить</button>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        // Удаление продукта
        async function deleteProduct(productId) {
            if (confirm('Вы уверены?')) {
                await fetch(`/api/delete-product/${productId}`, { method: 'DELETE' });
                products = products.filter(p => p.id !== productId);
                renderProducts();
            }
        }

        // Рендер цехов
        function renderWorkshops() {
            const tbody = document.getElementById('workshops-tbody');
            const statsContainer = document.getElementById('workshops-stats');

            tbody.innerHTML = workshops.map(w => `
                <tr>
                    <td><strong>${w.name}</strong></td>
                    <td style="text-align: center;">${w.people_count} чел.</td>
                    <td style="text-align: center;">${w.production_time} ч</td>
                </tr>
            `).join('');

            const totalPeople = workshops.reduce((sum, w) => sum + w.people_count, 0);
            const totalTime = workshops.reduce((sum, w) => sum + w.production_time, 0);
            const avgTime = totalTime / workshops.length;

            statsContainer.innerHTML = `
                <div class="stat-card">
                    <h3>Всего цехов</h3>
                    <div class="value">${workshops.length}</div>
                </div>
                <div class="stat-card">
                    <h3>Всего сотрудников</h3>
                    <div class="value">${totalPeople}</div>
                </div>
                <div class="stat-card">
                    <h3>Среднее время</h3>
                    <div class="value">${avgTime.toFixed(1)} ч</div>
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

            if (!productTypeId || !materialTypeId || !quantity || !param1 || !param2) {
                showAlert('Заполните все поля', 'error', 'alert-container-calc');
                return;
            }

            const response = await fetch('/api/calculate-raw-materials', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_type_id: productTypeId, material_type_id: materialTypeId, quantity, param1, param2 })
            });

            const data = await response.json();
            if (data.result === -1) {
                showAlert('Ошибка расчета', 'error', 'alert-container-calc');
                return;
            }

            const productType = productTypes.find(pt => pt.id === productTypeId);
            const materialType = materialTypes.find(mt => mt.id === materialTypeId);

            document.getElementById('result-details').innerHTML = `
                <p><strong>Тип продукции:</strong> ${productType.name}</p>
                <p><strong>Тип материала:</strong> ${materialType.name}</p>
                <p><strong>Количество:</strong> ${quantity} шт</p>
                <p><strong>Параметры:</strong> ${param1}м × ${param2}м</p>
                <hr style="margin: 15px 0; border: none; border-top: 1px solid #D2DFFF;">
                <p style="font-size: 20px; font-weight: bold; color: #355CBD;">📦 Необходимо сырья: ${data.result} кг</p>
            `;
            document.getElementById('calc-result').style.display = 'block';
            showAlert(`Расчет выполнен: требуется ${data.result} кг сырья`, 'success', 'alert-container-calc');
        }

        // Расчет времени производства
        function calculateProductionTime() {
            const productId = parseInt(document.getElementById('prod-time-product').value);
            if (!productId) {
                showAlert('Выберите продукт', 'error', 'alert-container-time');
                return;
            }

            const product = products.find(p => p.id === productId);
            const relatedWorkshops = productWorkshops
                .filter(pw => pw.product_id === productId)
                .map(pw => workshops.find(w => w.id === pw.workshop_id));

            if (relatedWorkshops.length === 0) {
                showAlert('Для этого продукта нет цехов', 'error', 'alert-container-time');
                return;
            }

            const totalTime = relatedWorkshops.reduce((sum, w) => sum + w.production_time, 0);

            document.getElementById('time-details').innerHTML = `
                <p><strong>${product.name}</strong></p>
                <p style="margin-bottom: 20px; color: #355CBD;">Участвующие цеха:</p>
                ${relatedWorkshops.map(w => `<p style="margin-left: 20px;">• ${w.name}: ${w.production_time}ч</p>`).join('')}
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #D2DFFF;">
                <p style="font-size: 22px; color: #1e40af; font-weight: bold;">⏱️ Итого: ${totalTime} часов</p>
            `;
            document.getElementById('time-result').style.display = 'block';
            showAlert(`Время производства: ${totalTime} часов`, 'success', 'alert-container-time');
        }

        // Показ уведомлений
        function showAlert(message, type, containerId) {
            const container = document.getElementById(containerId);
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} show`;
            alert.textContent = (type === 'success' ? '✓ ' : '✗ ') + message;
            container.innerHTML = '';
            container.appendChild(alert);

            setTimeout(() => {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 300);
            }, 4000);
        }

        // Инициализация
        loadData();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Premium Furnitur eSolutions - Flask Edition")
    print("="*60)
    print("✅ Приложение запущено на http://localhost:5000")
    print("📌 Откройте браузер и перейдите по адресу выше")
    print("💡 Нажмите Ctrl+C для остановки")
    print("="*60 + "\n")
    
    import webbrowser
    webbrowser.open('http://localhost:5000')
    
    app.run(debug=True, use_reloader=False)
