-- Удаление существующих таблиц (если нужна переустановка)
DROP TABLE IF EXISTS product_workshops CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS product_types CASCADE;
DROP TABLE IF EXISTS material_types CASCADE;
DROP TABLE IF EXISTS workshops CASCADE;

-- ============================================================================
-- ТАБЛИЦА: material_types (Типы материалов)
-- Описание: Справочник материалов, используемых при производстве
-- ============================================================================
CREATE TABLE material_types (
    material_type_id SERIAL PRIMARY KEY,
    material_type_name VARCHAR(255) NOT NULL UNIQUE,
    raw_material_loss_percent DECIMAL(5, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ТАБЛИЦА: product_types (Типы продукции)
-- Описание: Классификация мебельных изделий и их коэффициенты
-- ============================================================================
CREATE TABLE product_types (
    product_type_id SERIAL PRIMARY KEY,
    product_type_name VARCHAR(255) NOT NULL UNIQUE,
    product_type_coefficient DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ТАБЛИЦА: workshops (Цехи производства)
-- Описание: Информация о производственных цехах предприятия
-- ============================================================================
CREATE TABLE workshops (
    workshop_id SERIAL PRIMARY KEY,
    workshop_name VARCHAR(255) NOT NULL UNIQUE,
    workshop_type VARCHAR(100) NOT NULL,
    staff_count INT NOT NULL CHECK (staff_count > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ТАБЛИЦА: products (Продукция)
-- Описание: Каталог мебельных изделий компании
-- Связи: FK на product_types, FK на material_types
-- ============================================================================
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_type_id INT NOT NULL,
    product_name VARCHAR(500) NOT NULL UNIQUE,
    article_number BIGINT NOT NULL UNIQUE,
    minimum_partner_price DECIMAL(12, 2) NOT NULL CHECK (minimum_partner_price > 0),
    material_type_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Внешние ключи
    CONSTRAINT fk_products_product_type 
        FOREIGN KEY (product_type_id) 
        REFERENCES product_types(product_type_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_products_material_type 
        FOREIGN KEY (material_type_id) 
        REFERENCES material_types(material_type_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
);

-- ============================================================================
-- ТАБЛИЦА: product_workshops (Связь продукции с цехами)
-- Описание: Маршрут изготовления каждого изделия в цехах
-- Связи: FK на products, FK на workshops
-- ============================================================================
CREATE TABLE product_workshops (
    product_workshop_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    workshop_id INT NOT NULL,
    manufacturing_time_hours DECIMAL(8, 2) NOT NULL CHECK (manufacturing_time_hours > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Уникальная комбинация продукта и цеха (одно изделие - один маршрут в цехе)
    CONSTRAINT uk_product_workshop 
        UNIQUE (product_id, workshop_id),
    
    -- Внешние ключи
    CONSTRAINT fk_product_workshops_product 
        FOREIGN KEY (product_id) 
        REFERENCES products(product_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    CONSTRAINT fk_product_workshops_workshop 
        FOREIGN KEY (workshop_id) 
        REFERENCES workshops(workshop_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
);

-- ============================================================================
-- ИНДЕКСЫ для оптимизации запросов
-- ============================================================================
CREATE INDEX idx_products_product_type_id ON products(product_type_id);
CREATE INDEX idx_products_material_type_id ON products(material_type_id);
CREATE INDEX idx_products_article_number ON products(article_number);
CREATE INDEX idx_product_workshops_product_id ON product_workshops(product_id);
CREATE INDEX idx_product_workshops_workshop_id ON product_workshops(workshop_id);

-- ============================================================================
-- КОММЕНТАРИИ К ТАБЛИЦАМ И ПОЛЯМ
-- ============================================================================
COMMENT ON TABLE material_types IS 'Справочник материалов для производства мебели';
COMMENT ON COLUMN material_types.material_type_name IS 'Название материала (дерево, ДСП, МДФ и т.д.)';
COMMENT ON COLUMN material_types.raw_material_loss_percent IS 'Процент потерь сырья при обработке';

COMMENT ON TABLE product_types IS 'Классификация мебельной продукции';
COMMENT ON COLUMN product_types.product_type_name IS 'Наименование типа (Гостиные, Кровати, Шкафы)';
COMMENT ON COLUMN product_types.product_type_coefficient IS 'Коэффициент сложности изготовления';

COMMENT ON TABLE workshops IS 'Информация о производственных цехах';
COMMENT ON COLUMN workshops.workshop_name IS 'Название цеха (Проектный, Столярный и т.д.)';
COMMENT ON COLUMN workshops.workshop_type IS 'Тип цеха (Проектирование, Обработка, Сборка, Сушка)';
COMMENT ON COLUMN workshops.staff_count IS 'Количество работников в цехе';

COMMENT ON TABLE products IS 'Каталог мебельной продукции';
COMMENT ON COLUMN products.product_name IS 'Полное наименование изделия';
COMMENT ON COLUMN products.article_number IS 'Артикул для идентификации в каталоге';
COMMENT ON COLUMN products.minimum_partner_price IS 'Минимальная цена для партнеров';

COMMENT ON TABLE product_workshops IS 'Маршрут производства (какие цехи участвуют в изготовлении продукции)';
COMMENT ON COLUMN product_workshops.manufacturing_time_hours IS 'Время изготовления в цехе (в часах)';

-- ============================================================================
-- ИМПОРТ ДАННЫХ
-- ============================================================================

-- 1. Импорт типов материалов
INSERT INTO material_types (material_type_name, raw_material_loss_percent) VALUES
('Мебельный щит из массива дерева', 0.80),
('Ламинированное ДСП', 0.70),
('Фанера', 0.55),
('МДФ', 0.30);

-- 2. Импорт типов продукции
INSERT INTO product_types (product_type_name, product_type_coefficient) VALUES
('Гостиные', 3.5),
('Прихожие', 5.6),
('Мягкая мебель', 3.0),
('Кровати', 4.7),
('Шкафы', 1.5),
('Комоды', 2.3);

-- 3. Импорт цехов
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

-- 4. Импорт продукции
INSERT INTO products (product_type_id, product_name, article_number, minimum_partner_price, material_type_id) VALUES
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Гостиные'), 'Комплект мебели для гостиной Ольха горная', 1549922, 160507.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Мебельный щит из массива дерева')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Гостиные'), 'Стенка для гостиной Вишня темная', 1018556, 216907.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Мебельный щит из массива дерева')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Прихожие'), 'Прихожая Венге Винтаж', 3028272, 24970.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Ламинированное ДСП')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Прихожие'), 'Тумба с вешалкой Дуб натуральный', 3029272, 18206.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Ламинированное ДСП')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Прихожие'), 'Прихожая-комплект Дуб темный', 3028248, 177509.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Мебельный щит из массива дерева')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Мягкая мебель'), 'Диван-кровать угловой Книжка', 7118827, 85900.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Мебельный щит из массива дерева')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Мягкая мебель'), 'Диван модульный Телескоп', 7137981, 75900.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Мебельный щит из массива дерева')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Мягкая мебель'), 'Диван-кровать Соло', 7029787, 120345.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Мебельный щит из массива дерева')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Мягкая мебель'), 'Детский диван Выкатной', 7758953, 25990.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Фанера')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Кровати'), 'Кровать с подъемным механизмом с матрасом 1600х2000 Венге', 6026662, 69500.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Мебельный щит из массива дерева')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Кровати'), 'Кровать с матрасом 90х2000 Венге', 6159043, 55600.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Ламинированное ДСП')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Кровати'), 'Кровать универсальная Дуб натуральный', 6588376, 37900.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Ламинированное ДСП')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Кровати'), 'Кровать с ящиками Ясень белый', 6758375, 46750.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Фанера')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Шкафы'), 'Шкаф-купе 3-х дверный Сосна белая', 2759324, 131560.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Ламинированное ДСП')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Шкафы'), 'Стеллаж Бук натуральный', 2118827, 38700.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Мебельный щит из массива дерева')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Шкафы'), 'Шкаф 4 дверный с ящиками Ясень серый', 2559898, 160151.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Фанера')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Шкафы'), 'Шкаф-пенал Береза белый', 2259474, 40500.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Фанера')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Комоды'), 'Комод 6 ящиков Вишня светлая', 4115947, 61235.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Мебельный щит из массива дерева')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Комоды'), 'Комод 4 ящика Вишня светлая', 4033136, 41200.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'Мебельный щит из массива дерева')),
((SELECT product_type_id FROM product_types WHERE product_type_name = 'Комоды'), 'Тумба под ТВ', 4028048, 12350.00, (SELECT material_type_id FROM material_types WHERE material_type_name = 'МДФ'));

-- 5. Импорт маршрутов (связей между продукцией и цехами)
INSERT INTO product_workshops (product_id, workshop_id, manufacturing_time_hours) VALUES
((SELECT product_id FROM products WHERE article_number = 6026662), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Изготовления изделий из искусственного камня и композитных материалов'), 2.0),
((SELECT product_id FROM products WHERE article_number = 4028048), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Изготовления изделий из искусственного камня и композитных материалов'), 2.7),
((SELECT product_id FROM products WHERE article_number = 7118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Изготовления мягкой мебели'), 4.2),
((SELECT product_id FROM products WHERE article_number = 7137981), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Изготовления мягкой мебели'), 4.5),
((SELECT product_id FROM products WHERE article_number = 7029787), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Изготовления мягкой мебели'), 4.7),
((SELECT product_id FROM products WHERE article_number = 7758953), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Изготовления мягкой мебели'), 4.0),
((SELECT product_id FROM products WHERE article_number = 6159043), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Изготовления мягкой мебели'), 5.5),
((SELECT product_id FROM products WHERE article_number = 1018556), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Монтажа стеклянных, зеркальных вставок и других изделий'), 0.3),
((SELECT product_id FROM products WHERE article_number = 3028272), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Монтажа стеклянных, зеркальных вставок и других изделий'), 0.5),
((SELECT product_id FROM products WHERE article_number = 3028248), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Монтажа стеклянных, зеркальных вставок и других изделий'), 0.3),
((SELECT product_id FROM products WHERE article_number = 6026662), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Монтажа стеклянных, зеркальных вставок и других изделий'), 0.5),
((SELECT product_id FROM products WHERE article_number = 2759324), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Монтажа стеклянных, зеркальных вставок и других изделий'), 0.5),
((SELECT product_id FROM products WHERE article_number = 4028048), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Монтажа стеклянных, зеркальных вставок и других изделий'), 1.0),
((SELECT product_id FROM products WHERE article_number = 1549922), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 1018556), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.3),
((SELECT product_id FROM products WHERE article_number = 3028272), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 3029272), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 3028248), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7137981), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7029787), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7758953), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.3),
((SELECT product_id FROM products WHERE article_number = 6026662), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.6),
((SELECT product_id FROM products WHERE article_number = 6159043), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 1.0),
((SELECT product_id FROM products WHERE article_number = 6588376), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.8),
((SELECT product_id FROM products WHERE article_number = 6758375), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 2.0),
((SELECT product_id FROM products WHERE article_number = 2759324), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 2118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.3),
((SELECT product_id FROM products WHERE article_number = 2559898), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 1.5),
((SELECT product_id FROM products WHERE article_number = 2259474), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 1.0),
((SELECT product_id FROM products WHERE article_number = 4115947), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 4033136), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.4),
((SELECT product_id FROM products WHERE article_number = 4028048), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Обработки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 1549922), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 0.3),
((SELECT product_id FROM products WHERE article_number = 1018556), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 0.4),
((SELECT product_id FROM products WHERE article_number = 3028248), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7137981), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 1.0),
((SELECT product_id FROM products WHERE article_number = 7029787), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7758953), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 0.5),
((SELECT product_id FROM products WHERE article_number = 6026662), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 0.4),
((SELECT product_id FROM products WHERE article_number = 6758375), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 1.5),
((SELECT product_id FROM products WHERE article_number = 2118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 1.0),
((SELECT product_id FROM products WHERE article_number = 2259474), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 2.5),
((SELECT product_id FROM products WHERE article_number = 4115947), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 1.0),
((SELECT product_id FROM products WHERE article_number = 4033136), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 0.4),
((SELECT product_id FROM products WHERE article_number = 4028048), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Покраски'), 0.5),
((SELECT product_id FROM products WHERE article_number = 1549922), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Проектный'), 1.0),
((SELECT product_id FROM products WHERE article_number = 1018556), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Проектный'), 1.0),
((SELECT product_id FROM products WHERE article_number = 3028248), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Проектный'), 1.5),
((SELECT product_id FROM products WHERE article_number = 7029787), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Проектный'), 0.5),
((SELECT product_id FROM products WHERE article_number = 2759324), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Проектный'), 2.0),
((SELECT product_id FROM products WHERE article_number = 2118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Проектный'), 1.0),
((SELECT product_id FROM products WHERE article_number = 4028048), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Проектный'), 1.0),
((SELECT product_id FROM products WHERE article_number = 1549922), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 1018556), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 3028272), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 3029272), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 3028248), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 7118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 7137981), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 7029787), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7758953), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 0.7),
((SELECT product_id FROM products WHERE article_number = 6026662), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 6159043), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 6588376), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.1),
((SELECT product_id FROM products WHERE article_number = 6758375), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 2.0),
((SELECT product_id FROM products WHERE article_number = 2759324), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 2118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 2559898), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 2259474), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 4115947), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 4033136), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 1.0),
((SELECT product_id FROM products WHERE article_number = 4028048), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Раскроя'), 0.6),
((SELECT product_id FROM products WHERE article_number = 1549922), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Расчетный'), 0.4),
((SELECT product_id FROM products WHERE article_number = 1018556), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Расчетный'), 1.0),
((SELECT product_id FROM products WHERE article_number = 3028248), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Расчетный'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7029787), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Расчетный'), 0.5),
((SELECT product_id FROM products WHERE article_number = 2759324), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Расчетный'), 1.0),
((SELECT product_id FROM products WHERE article_number = 2118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Расчетный'), 0.7),
((SELECT product_id FROM products WHERE article_number = 4028048), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Расчетный'), 0.4),
((SELECT product_id FROM products WHERE article_number = 1018556), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 1.0),
((SELECT product_id FROM products WHERE article_number = 3028272), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 1.0),
((SELECT product_id FROM products WHERE article_number = 3028248), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7137981), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 0.3),
((SELECT product_id FROM products WHERE article_number = 6588376), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 0.8),
((SELECT product_id FROM products WHERE article_number = 6758375), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 0.3),
((SELECT product_id FROM products WHERE article_number = 2759324), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 1.5),
((SELECT product_id FROM products WHERE article_number = 2118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 0.3),
((SELECT product_id FROM products WHERE article_number = 2559898), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 2.0),
((SELECT product_id FROM products WHERE article_number = 4115947), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 0.3),
((SELECT product_id FROM products WHERE article_number = 4028048), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сборки'), 1.0),
((SELECT product_id FROM products WHERE article_number = 1549922), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Столярный'), 1.5),
((SELECT product_id FROM products WHERE article_number = 1018556), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Столярный'), 1.0),
((SELECT product_id FROM products WHERE article_number = 3028248), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Столярный'), 1.0),
((SELECT product_id FROM products WHERE article_number = 7137981), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Столярный'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7029787), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Столярный'), 0.5),
((SELECT product_id FROM products WHERE article_number = 7758953), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Столярный'), 1.0),
((SELECT product_id FROM products WHERE article_number = 2118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Столярный'), 0.5),
((SELECT product_id FROM products WHERE article_number = 2559898), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Столярный'), 1.0),
((SELECT product_id FROM products WHERE article_number = 2259474), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Столярный'), 3.0),
((SELECT product_id FROM products WHERE article_number = 4115947), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Столярный'), 2.0),
((SELECT product_id FROM products WHERE article_number = 4033136), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Столярный'), 2.0),
((SELECT product_id FROM products WHERE article_number = 1549922), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сушильный'), 2.0),
((SELECT product_id FROM products WHERE article_number = 1018556), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сушильный'), 2.0),
((SELECT product_id FROM products WHERE article_number = 3028248), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сушильный'), 2.0),
((SELECT product_id FROM products WHERE article_number = 7118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сушильный'), 2.0),
((SELECT product_id FROM products WHERE article_number = 7137981), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сушильный'), 2.0),
((SELECT product_id FROM products WHERE article_number = 2118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сушильный'), 2.0),
((SELECT product_id FROM products WHERE article_number = 4115947), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сушильный'), 2.0),
((SELECT product_id FROM products WHERE article_number = 4033136), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Сушильный'), 2.0),
((SELECT product_id FROM products WHERE article_number = 1549922), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.3),
((SELECT product_id FROM products WHERE article_number = 3029272), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 3028248), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.2),
((SELECT product_id FROM products WHERE article_number = 7118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.3),
((SELECT product_id FROM products WHERE article_number = 7137981), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.2),
((SELECT product_id FROM products WHERE article_number = 7029787), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.3),
((SELECT product_id FROM products WHERE article_number = 7758953), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 6026662), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 6159043), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 6588376), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.3),
((SELECT product_id FROM products WHERE article_number = 6758375), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.2),
((SELECT product_id FROM products WHERE article_number = 2759324), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 2118827), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.2),
((SELECT product_id FROM products WHERE article_number = 2559898), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 2259474), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.5),
((SELECT product_id FROM products WHERE article_number = 4115947), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.2),
((SELECT product_id FROM products WHERE article_number = 4033136), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.2),
((SELECT product_id FROM products WHERE article_number = 4028048), (SELECT workshop_id FROM workshops WHERE workshop_name = 'Упаковки'), 0.3);

-- ============================================================================
-- ПРОВЕРКА ИМПОРТА ДАННЫХ
-- ============================================================================
SELECT 'Material Types' as entity_type, COUNT(*) as count FROM material_types
UNION ALL
SELECT 'Product Types', COUNT(*) FROM product_types
UNION ALL
SELECT 'Workshops', COUNT(*) FROM workshops
UNION ALL
SELECT 'Products', COUNT(*) FROM products
UNION ALL
SELECT 'Product Workshops', COUNT(*) FROM product_workshops;



