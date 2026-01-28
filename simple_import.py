#!/usr/bin/env python3
"""
Упрощенный скрипт импорта данных с автоматическим созданием БД
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Создает базу данных если она не существует"""
    try:
        # Подключаемся к серверу PostgreSQL
        conn = psycopg2.connect(
            host='localhost',
            database='postgres',
            user='postgres',
            password='postgres',
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Проверяем существование базы данных
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'premium_furniture'")
        exists = cursor.fetchone()
        
        if not exists:
            print("📦 Создание базы данных 'premium_furniture'...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier('premium_furniture')
            ))
            print("✅ База данных создана")
        else:
            print("✅ База данных уже существует")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании БД: {e}")
        print("\n🔧 Проверьте:")
        print("1. Запущен ли PostgreSQL")
        print("2. Правильность логина/пароля")
        print("3. Разрешения пользователя")
        return False

def test_connection():
    """Тестирует подключение к базе данных"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='premium_furniture',
            user='postgres',
            password='postgres',
            port='5432'
        )
        print("✅ Подключение к БД успешно")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def execute_sql_file():
    """Выполняет SQL скрипт для создания таблиц"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='premium_furniture',
            user='postgres',
            password='postgres',
            port='5432'
        )
        cursor = conn.cursor()
        
        # Читаем SQL файл
        with open('PremiumFurnitureSolutions.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("📦 Создание таблиц...")
        
        # Выполняем скрипт по частям
        commands = sql_script.split(';')
        for command in commands:
            command = command.strip()
            if command and not command.startswith('--'):
                try:
                    cursor.execute(command)
                except Exception as e:
                    print(f"⚠️  Пропущена команда: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Таблицы созданы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

def main():
    """Основная функция"""
    print("="*60)
    print("🛠  НАСТРОЙКА БАЗЫ ДАННЫХ ДЛЯ PREMIUM FURNITURE")
    print("="*60)
    
    # Шаг 1: Создание базы данных
    print("\n1. Проверка и создание базы данных...")
    if not create_database():
        return False
    
    # Шаг 2: Тестирование подключения
    print("\n2. Тестирование подключения...")
    if not test_connection():
        return False
    
    # Шаг 3: Создание таблиц
    print("\n3. Создание структуры таблиц...")
    if not execute_sql_file():
        return False
    
    print("\n" + "="*60)
    print("✅ НАСТРОЙКА УСПЕШНО ЗАВЕРШЕНА!")
    print("="*60)
    print("\nТеперь вы можете:")
    print("1. Запустить Flask приложение: python app_with_postgresql.py")
    print("2. Импортировать данные из Excel: python import_excel_data.py")
    print("3. Использовать веб-интерфейс: http://localhost:5000")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)