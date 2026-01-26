#!/usr/bin/env python3
"""
Скрипт для импорта данных из Excel файлов в базу данных Premium Furniture Solutions
"""

import os
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor
import sys
from decimal import Decimal

# ==================== НАСТРОЙКИ БАЗЫ ДАННЫХ ====================
DB_CONFIG = {
    'host': 'localhost',
    'database': 'premium_furniture',
    'user': 'postgres',
    'password': 'postgres',
    'port': '5432'
}

# ==================== ПУТИ К ФАЙЛАМ ====================
EXCEL_FILES = {
    'material_types': 'Material_type_import.xlsx',
    'product_types': 'Product_type_import.xlsx',
    'workshops': 'Workshops_import.xlsx',
    'products': 'Products_import.xlsx',
    'product_workshops': 'Product_workshops_import.xlsx'
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

def check_excel_files():
    """Проверяет наличие всех Excel файлов"""
    print("🔍 Проверка наличия файлов Excel...")
    
    missing_files = []
    for file_type, filename in EXCEL_FILES.items():
        if not os.path.exists(filename):
            missing_files.append(filename)
            print(f"   ❌ {filename} - не найден")
        else:
            print(f"   ✅ {filename} - найден")
    
    if missing_files:
        print(f"\n❌ Отсутствуют файлы: {', '.join(missing_files)}")
        print("📌 Убедитесь, что все файлы находятся в той же папке, что и скрипт")
        return False
    
    print("✅ Все файлы найдены")
    return True

def clear_existing_data(cursor):
    """Очищает существующие данные в таблицах"""
    print("\n🧹 Очистка существующих данных...")
    
    # Отключаем foreign key constraints для безопасного удаления
    cursor.execute("SET session_replication_role = 'replica';")
    
    tables = [
        'product_workshops',
        'products', 
        'product_types',
        'material_types',
        'workshops'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table} CASCADE;")
            print(f"   ✅ {table} - очищена")
        except Exception as e:
            print(f"   ⚠️  {table} - ошибка: {e}")
    
    # Включаем constraints обратно
    cursor.execute("SET session_replication_role = 'origin';")

def import_material_types(cursor):
    """Импорт типов материалов"""
    print("\n📦 Импорт типов материалов...")
    
    try:
        df = pd.read_excel(
            EXCEL_FILES['material_types'],
            sheet_name='Material_type_import'
        )
        
        print(f"   📄 Прочитано записей: {len(df)}")
        
        for index, row in df.iterrows():
            material_name = row['Тип материала']
            loss_percent = Decimal(str(row['Процент потерь сырья']))
            
            # В Excel проценты указаны как 0.008 (0.8%), преобразуем в проценты
            loss_percent_percent = loss_percent * 100  # 0.008 → 0.8
            
            cursor.execute(
                """
                INSERT INTO material_types 
                (material_type_name, raw_material_loss_percent)
                VALUES (%s, %s)
                RETURNING material_type_id
                """,
                (material_name, loss_percent_percent)
            )
            
            material_id = cursor.fetchone()[0]
            print(f"   ✅ {material_name} (ID: {material_id}) - импортирован")
            
        print(f"✅ Импортировано типов материалов: {len(df)}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта типов материалов: {e}")
        return False

def import_product_types(cursor):
    """Импорт типов продукции"""
    print("\n📦 Импорт типов продукции...")
    
    try:
        df = pd.read_excel(
            EXCEL_FILES['product_types'],
            sheet_name='Product_type_import'
        )
        
        print(f"   📄 Прочитано записей: {len(df)}")
        
        for index, row in df.iterrows():
            product_type_name = row['Тип продукции']
            coefficient = Decimal(str(row['Коэффициент типа продукции']))
            
            cursor.execute(
                """
                INSERT INTO product_types 
                (product_type_name, product_type_coefficient)
                VALUES (%s, %s)
                RETURNING product_type_id
                """,
                (product_type_name, coefficient)
            )
            
            product_type_id = cursor.fetchone()[0]
            print(f"   ✅ {product_type_name} (ID: {product_type_id}, коэффициент: {coefficient}) - импортирован")
            
        print(f"✅ Импортировано типов продукции: {len(df)}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта типов продукции: {e}")
        return False

def import_workshops(cursor):
    """Импорт цехов"""
    print("\n🏭 Импорт цехов...")
    
    try:
        df = pd.read_excel(
            EXCEL_FILES['workshops'],
            sheet_name='Workshops_import'
        )
        
        print(f"   📄 Прочитано записей: {len(df)}")
        
        for index, row in df.iterrows():
            workshop_name = row['Название цеха']
            workshop_type = row['Тип цеха']
            staff_count = int(row['Количество человек для производства'])
            
            cursor.execute(
                """
                INSERT INTO workshops 
                (workshop_name, workshop_type, staff_count)
                VALUES (%s, %s, %s)
                RETURNING workshop_id
                """,
                (workshop_name, workshop_type, staff_count)
            )
            
            workshop_id = cursor.fetchone()[0]
            print(f"   ✅ {workshop_name} (ID: {workshop_id}, сотрудников: {staff_count}) - импортирован")
            
        print(f"✅ Импортировано цехов: {len(df)}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта цехов: {e}")
        return False

def import_products(cursor):
    """Импорт продукции"""
    print("\n📦 Импорт продукции...")
    
    try:
        df = pd.read_excel(
            EXCEL_FILES['products'],
            sheet_name='Products_import'
        )
        
        print(f"   📄 Прочитано записей: {len(df)}")
        
        imported_count = 0
        
        for index, row in df.iterrows():
            product_type_name = row['Тип продукции']
            product_name = row['Наименование продукции']
            article_number = int(row['Артикул'])
            min_price = Decimal(str(row['Минимальная стоимость для партнера']))
            material_name = row['Основной материал']
            
            # Получаем ID типа продукции
            cursor.execute(
                "SELECT product_type_id FROM product_types WHERE product_type_name = %s",
                (product_type_name,)
            )
            product_type_result = cursor.fetchone()
            
            if not product_type_result:
                print(f"   ⚠️  Пропущен {product_name}: тип продукции '{product_type_name}' не найден")
                continue
            
            product_type_id = product_type_result[0]
            
            # Получаем ID материала
            cursor.execute(
                "SELECT material_type_id FROM material_types WHERE material_type_name = %s",
                (material_name,)
            )
            material_result = cursor.fetchone()
            
            if not material_result:
                print(f"   ⚠️  Пропущен {product_name}: материал '{material_name}' не найден")
                continue
            
            material_type_id = material_result[0]
            
            # Вставляем продукт
            cursor.execute(
                """
                INSERT INTO products 
                (product_type_id, product_name, article_number, minimum_partner_price, material_type_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING product_id
                """,
                (product_type_id, product_name, article_number, min_price, material_type_id)
            )
            
            product_id = cursor.fetchone()[0]
            imported_count += 1
            print(f"   ✅ {product_name} (ID: {product_id}, артикул: {article_number}) - импортирован")
            
        print(f"✅ Импортировано продуктов: {imported_count}/{len(df)}")
        return imported_count > 0
        
    except Exception as e:
        print(f"❌ Ошибка импорта продукции: {e}")
        return False

def import_product_workshops(cursor):
    """Импорт связей продукции с цехами"""
    print("\n🔗 Импорт связей продукции с цехами...")
    
    try:
        df = pd.read_excel(
            EXCEL_FILES['product_workshops'],
            sheet_name='Product_workshops_import'
        )
        
        print(f"   📄 Прочитано записей: {len(df)}")
        
        imported_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            product_name = row['Наименование продукции']
            workshop_name = row['Название цеха']
            manufacturing_time = Decimal(str(row['Время изготовления, ч']))
            
            # Получаем ID продукта
            cursor.execute(
                "SELECT product_id FROM products WHERE product_name = %s",
                (product_name,)
            )
            product_result = cursor.fetchone()
            
            if not product_result:
                print(f"   ⚠️  Пропущена связь: продукт '{product_name}' не найден")
                skipped_count += 1
                continue
            
            product_id = product_result[0]
            
            # Получаем ID цеха
            cursor.execute(
                "SELECT workshop_id FROM workshops WHERE workshop_name = %s",
                (workshop_name,)
            )
            workshop_result = cursor.fetchone()
            
            if not workshop_result:
                print(f"   ⚠️  Пропущена связь: цех '{workshop_name}' не найден")
                skipped_count += 1
                continue
            
            workshop_id = workshop_result[0]
            
            # Проверяем, существует ли уже такая связь
            cursor.execute(
                """
                SELECT 1 FROM product_workshops 
                WHERE product_id = %s AND workshop_id = %s
                """,
                (product_id, workshop_id)
            )
            
            if cursor.fetchone():
                # Обновляем существующую запись
                cursor.execute(
                    """
                    UPDATE product_workshops 
                    SET manufacturing_time_hours = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE product_id = %s AND workshop_id = %s
                    """,
                    (manufacturing_time, product_id, workshop_id)
                )
                action = "обновлена"
            else:
                # Вставляем новую запись
                cursor.execute(
                    """
                    INSERT INTO product_workshops 
                    (product_id, workshop_id, manufacturing_time_hours)
                    VALUES (%s, %s, %s)
                    """,
                    (product_id, workshop_id, manufacturing_time)
                )
                action = "добавлена"
            
            imported_count += 1
            
            if imported_count % 20 == 0:  # Выводим прогресс каждые 20 записей
                print(f"   📊 Обработано: {imported_count} связей")
        
        print(f"✅ Импортировано связей: {imported_count}")
        if skipped_count > 0:
            print(f"⚠️  Пропущено связей: {skipped_count} (продукты/цехи не найдены)")
        
        return imported_count > 0
        
    except Exception as e:
        print(f"❌ Ошибка импорта связей: {e}")
        return False

def verify_import(cursor):
    """Проверка результатов импорта"""
    print("\n🔍 Проверка результатов импорта...")
    
    queries = {
        'Типы материалов': "SELECT COUNT(*) FROM material_types",
        'Типы продукции': "SELECT COUNT(*) FROM product_types",
        'Цехи': "SELECT COUNT(*) FROM workshops",
        'Продукция': "SELECT COUNT(*) FROM products",
        'Связи продукции с цехами': "SELECT COUNT(*) FROM product_workshops"
    }
    
    total_records = 0
    
    for entity, query in queries.items():
        cursor.execute(query)
        count = cursor.fetchone()[0]
        total_records += count
        print(f"   📊 {entity}: {count} записей")
    
    # Выводим статистику по цехам
    cursor.execute("""
        SELECT 
            w.workshop_name,
            COUNT(pw.product_workshop_id) as product_count,
            SUM(pw.manufacturing_time_hours) as total_hours
        FROM workshops w
        LEFT JOIN product_workshops pw ON w.workshop_id = pw.workshop_id
        GROUP BY w.workshop_id, w.workshop_name
        ORDER BY product_count DESC
    """)
    
    print("\n🏭 Статистика по цехам:")
    workshops_stats = cursor.fetchall()
    for stat in workshops_stats:
        print(f"   📌 {stat[0]}: {stat[1]} продуктов, {float(stat[2] or 0):.1f} часов")
    
    # Выводим статистику по типам продукции
    cursor.execute("""
        SELECT 
            pt.product_type_name,
            COUNT(p.product_id) as product_count,
            AVG(p.minimum_partner_price) as avg_price
        FROM product_types pt
        LEFT JOIN products p ON pt.product_type_id = p.product_type_id
        GROUP BY pt.product_type_id, pt.product_type_name
        ORDER BY product_count DESC
    """)
    
    print("\n📦 Статистика по типам продукции:")
    product_stats = cursor.fetchall()
    for stat in product_stats:
        print(f"   📌 {stat[0]}: {stat[1]} продуктов, средняя цена: {float(stat[2] or 0):.2f}₽")
    
    return total_records

def create_excel_import_function(cursor):
    """Создает функцию для повторного импорта данных"""
    print("\n⚙️  Создание функции для импорта из Excel...")
    
    sql_function = """
    CREATE OR REPLACE FUNCTION import_from_excel()
    RETURNS TEXT AS $$
    DECLARE
        result_text TEXT := '';
        rec_count INTEGER;
    BEGIN
        -- Очистка данных
        DELETE FROM product_workshops;
        DELETE FROM products;
        DELETE FROM product_types;
        DELETE FROM material_types;
        DELETE FROM workshops;
        
        -- Импорт типов материалов (пример - нужно адаптировать под ваши данные)
        -- В реальной реализации здесь был бы COPY или внешние таблицы
        INSERT INTO material_types (material_type_name, raw_material_loss_percent) VALUES
        ('Мебельный щит из массива дерева', 0.80),
        ('Ламинированное ДСП', 0.70),
        ('Фанера', 0.55),
        ('МДФ', 0.30);
        
        GET DIAGNOSTICS rec_count = ROW_COUNT;
        result_text := result_text || 'Материалы: ' || rec_count || ' записей; ';
        
        -- Импорт типов продукции
        INSERT INTO product_types (product_type_name, product_type_coefficient) VALUES
        ('Гостиные', 3.5),
        ('Прихожие', 5.6),
        ('Мягкая мебель', 3.0),
        ('Кровати', 4.7),
        ('Шкафы', 1.5),
        ('Комоды', 2.3);
        
        GET DIAGNOSTICS rec_count = ROW_COUNT;
        result_text := result_text || 'Типы продукции: ' || rec_count || ' записей; ';
        
        -- Импорт цехов
        INSERT INTO workshops (workshop_name, workshop_type, staff_count) VALUES
        ('Проектный', 'Проектирование', 4),
        ('Расчетный', 'Проектирование', 5),
        ('Раскроя', 'Обработка', 5),
        ('Обработки', 'Обработка', 6),
        ('Сушильный', 'Сушка', 3),
        ('Покраски', 'Обработка', 5),
        ('Столярный', 'Обработка', 7),
        ('Изготовления изделий из искусственного камня и композитных материалов', 'Обработка', 3),
        ('Изготовления мягкой мебели', 'Обработка', 5),
        ('Монтажа стеклянных, зеркальных вставок и других изделий', 'Сборка', 2),
        ('Сборки', 'Сборка', 6),
        ('Упаковки', 'Сборка', 4);
        
        GET DIAGNOSTICS rec_count = ROW_COUNT;
        result_text := result_text || 'Цехи: ' || rec_count || ' записей; ';
        
        RETURN result_text;
    END;
    $$ LANGUAGE plpgsql;
    """
    
    try:
        cursor.execute(sql_function)
        print("✅ Функция import_from_excel() создана")
        return True
    except Exception as e:
        print(f"⚠️  Ошибка создания функции: {e}")
        return False

def main():
    """Основная функция импорта"""
    print("=" * 70)
    print("📥 ИМПОРТ ДАННЫХ ИЗ EXCEL В БАЗУ ДАННЫХ")
    print("=" * 70)
    
    # Проверяем наличие файлов
    if not check_excel_files():
        sys.exit(1)
    
    # Подключаемся к базе данных
    conn = get_db_connection()
    if not conn:
        print("❌ Не удалось подключиться к базе данных")
        sys.exit(1)
    
    try:
        cursor = conn.cursor()
        
        # Очищаем существующие данные
        clear_existing_data(cursor)
        conn.commit()
        
        # Импортируем данные по порядку зависимостей
        success = True
        
        # 1. Типы материалов
        if not import_material_types(cursor):
            success = False
        conn.commit()
        
        # 2. Типы продукции
        if success and not import_product_types(cursor):
            success = False
        conn.commit()
        
        # 3. Цехи
        if success and not import_workshops(cursor):
            success = False
        conn.commit()
        
        # 4. Продукция (зависит от типов материалов и продукции)
        if success and not import_products(cursor):
            success = False
        conn.commit()
        
        # 5. Связи продукции с цехами (зависит от продукции и цехов)
        if success and not import_product_workshops(cursor):
            success = False
        conn.commit()
        
        # Проверяем результаты
        if success:
            total_records = verify_import(cursor)
            
            print("\n" + "=" * 70)
            print("🎉 ИМПОРТ УСПЕШНО ЗАВЕРШЕН!")
            print("=" * 70)
            print(f"📊 Всего импортировано записей: {total_records}")
            print("\n📁 Импортированные данные:")
            print("   ✅ Material_type_import.xlsx → material_types")
            print("   ✅ Product_type_import.xlsx → product_types")
            print("   ✅ Workshops_import.xlsx → workshops")
            print("   ✅ Products_import.xlsx → products")
            print("   ✅ Product_workshops_import.xlsx → product_workshops")
            print("\n💡 Данные готовы к использованию в приложении!")
            
            # Создаем функцию для быстрого импорта
            create_excel_import_function(cursor)
            conn.commit()
            
        else:
            print("\n❌ Импорт завершен с ошибками")
            conn.rollback()
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        conn.rollback()
        success = False
        
    finally:
        cursor.close()
        conn.close()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)