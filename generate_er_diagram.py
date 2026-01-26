#!/usr/bin/env python3
"""
Генерация ER-диаграммы из SQL-скрипта
"""

import os
import sys
from sqlalchemy import MetaData, create_engine
from sqlalchemy_schemadisplay import create_schema_graph

def generate_er_diagram():
    """
    Создает ER-диаграмму в формате PDF из SQL-скрипта
    """
    print("📊 Генерация ER-диаграммы из SQL-скрипта...")
    
    try:
        # Создаем временную базу данных PostgreSQL
        temp_db_name = "temp_furniture_db"
        
        # Параметры подключения к временной БД
        connection_string = "postgresql://postgres:postgres@localhost:5432/postgres"
        
        # Создаем подключение
        engine = create_engine(connection_string)
        
        # Считываем SQL-скрипт
        with open('PremiumFurnitureSolutions.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Выполняем скрипт (кроме DROP TABLE для теста)
        # Заменим DROP TABLE на комментарии для теста
        sql_for_execution = sql_script.replace(
            'DROP TABLE IF EXISTS',
            '-- DROP TABLE IF EXISTS'
        )
        
        with engine.connect() as conn:
            # Создаем схему
            conn.execute("DROP SCHEMA IF EXISTS furniture CASCADE;")
            conn.execute("CREATE SCHEMA furniture;")
            
            # Выполняем SQL (только CREATE TABLE)
            create_table_section = []
            in_create_table = False
            current_table = []
            
            for line in sql_script.split('\n'):
                line_stripped = line.strip()
                if line_stripped.startswith('CREATE TABLE'):
                    in_create_table = True
                    current_table = [line]
                elif in_create_table:
                    current_table.append(line)
                    if line_stripped.endswith(');'):
                        create_table_sql = '\n'.join(current_table)
                        create_table_section.append(create_table_sql)
                        in_create_table = False
            
            # Выполняем только CREATE TABLE
            for create_sql in create_table_section:
                try:
                    # Заменяем имена таблиц для работы в схеме
                    create_sql = create_sql.replace('CREATE TABLE ', 'CREATE TABLE furniture.')
                    conn.execute(create_sql)
                except Exception as e:
                    print(f"⚠️ Ошибка выполнения: {e}")
                    continue
        
        # Создаем график схемы
        print("🔄 Создание диаграммы...")
        
        graph = create_schema_graph(
            metadata=MetaData(bind=engine, schema='furniture'),
            show_datatypes=True,
            show_indexes=True,
            rankdir='TB',
            concentrate=False
        )
        
        # Сохраняем в PDF
        output_file = 'ER_Diagram_Furniture.pdf'
        graph.write_pdf(output_file)
        
        print(f"✅ ER-диаграмма сохранена как: {output_file}")
        print(f"📄 Размер файла: {os.path.getsize(output_file) / 1024:.2f} KB")
        
        # Альтернативно можно сохранить как PNG
        graph.write_png('ER_Diagram_Furniture.png')
        print(f"🖼️  Также сохранено как PNG: ER_Diagram_Furniture.png")
        
        # Создаем текстовое описание ER-диаграммы
        create_text_er_diagram()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def create_text_er_diagram():
    """
    Создает текстовое описание ER-диаграммы
    """
    print("\n📋 Текстовое описание ER-диаграммы:\n")
    
    er_description = """
================================================================================
                            ER-ДИАГРАММА БАЗЫ ДАННЫХ
                           Premium Furniture Solutions
================================================================================

📊 СУЩНОСТИ И СВЯЗИ:

1. material_types (Типы материалов)
   ├── PK: material_type_id (SERIAL)
   ├── material_type_name (VARCHAR(255)) UNIQUE
   ├── raw_material_loss_percent (DECIMAL(5,2))
   └── created_at, updated_at (TIMESTAMP)

2. product_types (Типы продукции)
   ├── PK: product_type_id (SERIAL)
   ├── product_type_name (VARCHAR(255)) UNIQUE
   ├── product_type_coefficient (DECIMAL(10,2))
   └── created_at, updated_at (TIMESTAMP)

3. workshops (Цехи производства)
   ├── PK: workshop_id (SERIAL)
   ├── workshop_name (VARCHAR(255)) UNIQUE
   ├── workshop_type (VARCHAR(100))
   ├── staff_count (INT) > 0
   └── created_at, updated_at (TIMESTAMP)

4. products (Продукция)
   ├── PK: product_id (SERIAL)
   ├── FK: product_type_id → product_types(product_type_id)
   ├── product_name (VARCHAR(500)) UNIQUE
   ├── article_number (BIGINT) UNIQUE
   ├── minimum_partner_price (DECIMAL(12,2)) > 0
   ├── FK: material_type_id → material_types(material_type_id)
   └── created_at, updated_at (TIMESTAMP)

5. product_workshops (Связь продукции с цехами)
   ├── PK: product_workshop_id (SERIAL)
   ├── FK: product_id → products(product_id) ON DELETE CASCADE
   ├── FK: workshop_id → workshops(workshop_id)
   ├── manufacturing_time_hours (DECIMAL(8,2)) > 0
   └── UNIQUE: (product_id, workshop_id)

================================================================================
                          СХЕМА СВЯЗЕЙ (CARDINALITY)
================================================================================

1. material_types (1) ────< (0..N) products
   Один тип материала может использоваться в нескольких продуктах

2. product_types (1) ────< (0..N) products
   Один тип продукции может быть у нескольких продуктов

3. products (1) ────< (0..N) product_workshops
   Один продукт может проходить через несколько цехов

4. workshops (1) ────< (0..N) product_workshops
   Один цех может использоваться для нескольких продуктов

================================================================================
                          ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ
================================================================================

1. idx_products_product_type_id (products.product_type_id)
2. idx_products_material_type_id (products.material_type_id)
3. idx_products_article_number (products.article_number)
4. idx_product_workshops_product_id (product_workshops.product_id)
5. idx_product_workshops_workshop_id (product_workshops.workshop_id)

================================================================================
                           ОБРАБОТКА ЦЕЛОСТНОСТИ
================================================================================

1. ON DELETE RESTRICT:
   - products → product_types
   - products → material_types
   - product_workshops → workshops

2. ON DELETE CASCADE:
   - product_workshops → products

3. ON UPDATE CASCADE:
   - Все внешние ключи

================================================================================
"""
    
    # Сохраняем текстовое описание
    with open('ER_Diagram_Description.txt', 'w', encoding='utf-8') as f:
        f.write(er_description)
    
    print(er_description)
    print("📝 Текстовое описание сохранено как: ER_Diagram_Description.txt")

if __name__ == "__main__":
    # Проверяем наличие SQL-файла
    if not os.path.exists('PremiumFurnitureSolutions.sql'):
        print("❌ Файл PremiumFurnitureSolutions.sql не найден!")
        sys.exit(1)
    
    # Генерируем ER-диаграмму
    success = generate_er_diagram()
    
    if success:
        print("\n" + "="*60)
        print("✅ ER-диаграмма успешно создана!")
        print("="*60)
        print("📄 Основные файлы:")
        print("   - ER_Diagram_Furniture.pdf (PDF версия)")
        print("   - ER_Diagram_Furniture.png (PNG версия)")
        print("   - ER_Diagram_Description.txt (Текстовое описание)")
        print("="*60)
    else:
        print("\n❌ Не удалось создать ER-диаграмму")