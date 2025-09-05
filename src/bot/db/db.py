import sqlite3
import os


class Database:

    def __init__(self, db_name="database.db"):
        db_path = os.path.join(os.path.dirname(__file__), db_name)
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _create_tables(self):
        with self.connection:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    status TEXT DEFAULT 'active' 
                )
            """)

            #status:
            # active - обычный статус пользователя
            # waiting_for_art - ожидание ботом артикула товара для добавления

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    size TEXT NOT NULL,
                    current_price INTEGER,
                    last_check_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(article, size)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_products (
                    user_id INTEGER,
                    product_id INTEGER,
                    notifications_enabled BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    PRIMARY KEY (user_id, product_id)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    previous_price INTEGER NOT NULL,
                    current_price INTEGER NOT NULL,
                    change_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            """)

    def add_user(self, user_id: int):
        with self.connection:
            self.cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))

    def get_products_list(self, user_id: int) -> list[tuple]:
        with self.connection:
            self.cursor.execute("""
                SELECT p.id, p.name, p.size
                FROM products p
                JOIN user_products up ON p.id = up.product_id
                WHERE up.user_id = ?
            """, (user_id,))
            return self.cursor.fetchall()

    def get_user_status(self, user_id: int):
        with self.connection:
            self.cursor.execute("SELECT status FROM users WHERE user_id = ?", (user_id,))
            return self.cursor.fetchone()[0]

    def get_product_info(self, product_id: int) -> str | None:
        with self.connection:
            self.cursor.execute(
                "SELECT name, article ,size, current_price, last_check_time FROM products WHERE id = ?",
                (product_id,)
            )
            result = self.cursor.fetchone()
            if result:
                name, article, size, price, last_check = result
                price_rub = f"{price} ₽" if price is not None else 'N/A'
                size_str = f"Размер: {size}\n" if size != "-1" else ""
                return f"Название: {name}\n{size_str}Текущая цена: {price_rub}\nПоследняя проверка: {last_check}\nСсылка: https://www.wildberries.ru/catalog/{article}/detail.aspx"
        return None

    def add_product(self, user_id: int, article: int, name: str, price: int, size: str):
        """
        Добавляет товар (артикул+размер) в БД и связывает его с пользователем.
        Если товар существует, его имя и цена обновляются.
        """
        with self.connection:
            # Вставить или обновить продукт.
            self.cursor.execute(
                """INSERT INTO products (article, size, name, current_price) VALUES (?, ?, ?, ?)
                   ON CONFLICT(article, size) DO UPDATE SET
                   name=excluded.name, 
                   current_price=excluded.current_price, 
                   last_check_time=CURRENT_TIMESTAMP""",
                (article, size, name, price)
            )
            # Получить id продукта
            self.cursor.execute("SELECT id FROM products WHERE article = ? AND size = ?", (article, size))
            product_id = self.cursor.fetchone()[0]

            # Связать с пользователем
            self.cursor.execute(
                "INSERT OR IGNORE INTO user_products (user_id, product_id) VALUES (?, ?)",
                (user_id, product_id)
            )

    def update_product_price(self, product_id: int, new_price: int) -> tuple[int, int] | None:
        """
        Обновляет цену товара и записывает изменение в историю.
        Возвращает (старая_цена, новая_цена) если цена изменилась, иначе None.
        """
        with self.connection:
            self.cursor.execute("SELECT current_price FROM products WHERE id = ?", (product_id,))
            result = self.cursor.fetchone()

            if result is None:
                return None
            old_price = result[0]
            self.cursor.execute("UPDATE products SET last_check_time = CURRENT_TIMESTAMP WHERE id = ?", (product_id,))
            if old_price is not None and old_price != new_price:
                self.cursor.execute("INSERT INTO price_history (product_id, previous_price, current_price) VALUES (?, ?, ?)", (product_id, old_price, new_price))
                self.cursor.execute("UPDATE products SET current_price = ? WHERE id = ?", (new_price, product_id))
                return old_price, new_price
        return None

    def set_user_status(self, user_id: int, status: str):
        try:
            with self.connection:
                self.cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
            return True
        except sqlite3.Error:
            return False

    def get_all_products_for_monitoring(self) -> list[tuple]:
        """Получает все продукты для мониторинга."""
        with self.connection:
            self.cursor.execute("SELECT id, article, size, name FROM products")
            return self.cursor.fetchall()

    def get_users_for_product(self, product_id: int) -> list[int]:
        """Получает ID пользователей, отслеживающих товар."""
        with self.connection:
            self.cursor.execute(
                "SELECT user_id FROM user_products WHERE product_id = ? AND notifications_enabled = 1",
                (product_id,)
            )
            return [row[0] for row in self.cursor.fetchall()]

    def delete_user_product(self, user_id: int, product_id: int):
        """Удаляет связь пользователя с товаром."""
        with self.connection:
            self.cursor.execute(
                "DELETE FROM user_products WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            )

    def get_notification_status(self, user_id: int, product_id: int) -> bool | None:
        """Получает статус уведомлений для товара пользователя."""
        with self.connection:
            self.cursor.execute(
                "SELECT notifications_enabled FROM user_products WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            )
            result = self.cursor.fetchone()
            return bool(result[0]) if result else None

    def toggle_notifications(self, user_id: int, product_id: int) -> bool | None:
        """Переключает статус уведомлений для товара пользователя."""
        current_status = self.get_notification_status(user_id, product_id)
        if current_status is None:
            return None
        new_status = not current_status
        with self.connection:
            self.cursor.execute(
                "UPDATE user_products SET notifications_enabled = ? WHERE user_id = ? AND product_id = ?",
                (new_status, user_id, product_id)
            )
        return new_status

    def close(self):
        if self.connection:
            self.connection.close()


db = Database()