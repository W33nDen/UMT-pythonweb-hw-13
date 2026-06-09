# UMT-pythonweb-hw-13 — Contacts REST API (Фінальне домашнє завдання)

Розширений REST API застосунок на FastAPI для зберігання та управління контактами з підтримкою аутентифікації, авторизації за допомогою JWT-токенів, верифікації email, rate-limiting, CORS, інтеграції з Cloudinary, кешування з Redis, Sphinx-документації та тестування з покриттям >75%.

---

## 🚀 Фінальні можливості (ДЗ №13)

1. **Документація за допомогою Sphinx**:
   - Додано Sphinx-сумісні docstrings (Google format) для всіх основних модулів, функцій та методів класів.
   - Налаштовано тему `sphinx_rtd_theme`.
   - Згенеровано HTML-документацію у папці `docs/_build/html`.

2. **Тестування (Покриття >75%)**:
   - Написано модульні (unit) тести для репозиторію (`app/crud.py`).
   - Написано інтеграційні тести для перевірки всіх маршрутів (`contacts`, `auth`, `users`) за допомогою `pytest`.
   - Використано пакет `pytest-cov` для контролю покриття коду. Досягнуто покриття у **80% - 82%**!

3. **Кешування з Redis**:
   - Налаштовано механізм кешування користувачів за допомогою Redis.
   - Функція `get_current_user` перевіряє наявність користувача в кеші Redis, мінімізуючи запити до бази даних PostgreSQL.
   - Автоматичне скидання (інвалідація) кешу при оновленні профілю користувача (зміна пароля, аватара або верифікація email).

4. **Механізм скидання пароля**:
   - Ендпоінт `POST /auth/request_password_reset` приймає email та надсилає безпечне посилання для скидання пароля на електронну пошту (із виведенням у консоль у режимі розробки).
   - Ендпоінт `POST /auth/reset_password` верифікує токен скидання та встановлює новий пароль.

5. **Керування ролями (User / Admin)**:
   - Впроваджено доступ за ролями: `user` та `admin`.
   - Перший зареєстрований користувач автоматично отримує роль `admin`.
   - Доступ до оновлення аватара (`PATCH /users/avatar`) мають **тільки** адміністратори. Для звичайних користувачів повертається статус `403 Forbidden`.

6. **Пара токенів (Access / Refresh) - Додаткове завдання**:
   - Реалізовано авторизацію за допомогою пари JWT токенів: `access_token` та `refresh_token`.
   - Додано маршрут `POST /auth/refresh_token` для оновлення токенів доступу без повторного вводу пароля.

7. **Docker Compose**:
   - Стек сервісів повністю контейнеризований.
   - Docker Compose запускає PostgreSQL базу даних, кеш Redis та FastAPI веб-додаток разом.

---

## 🛠️ Технологічний стек

*   **Фреймворк**: FastAPI
*   **База даних**: PostgreSQL (SQLAlchemy ORM)
*   **Кешування**: Redis
*   **Аутентифікація**: PyJWT / Python-Jose, Bcrypt (Access & Refresh tokens)
*   **Rate Limiting**: SlowAPI
*   **Хмара (Аватари)**: Cloudinary API
*   **Тестування**: pytest, pytest-cov, pytest-asyncio
*   **Документація**: Sphinx (sphinx_rtd_theme)
*   **Оркестрація**: Docker / Docker Compose

---

## 💻 Швидкий запуск

### Запуск через Docker Compose (Рекомендовано)

Запуск бази даних, Redis та веб-додатка разом:

1.  Створіть файл конфігурації `.env` на основі `.env.example`:
    ```bash
    cp .env.example .env
    ```
2.  Запустіть Docker Compose:
    ```bash
    docker compose up --build
    ```
3.  Застосунок автоматично ініціалізує базу даних, створить таблиці та буде доступний за адресою:
    `http://127.0.0.1:8000`
    - Swagger UI: `http://127.0.0.1:8000/docs`

---

### Локальний запуск (для розробки)

1.  Створіть та активуйте віртуальне оточення:
    ```bash
    python -m venv .venv
    # Для Linux/macOS
    source .venv/bin/activate
    # Для Windows PowerShell
    .\.venv\Scripts\Activate.ps1
    ```
2.  Встановіть залежності:
    ```bash
    pip install -r requirements.txt
    ```
3.  Запустіть локальні сервіси Docker (Postgres & Redis) або переключіть базу на SQLite в `.env`:
    ```env
    DATABASE_URL=sqlite:///./test.db
    REDIS_URL=redis://localhost:6379/0
    ```
4.  Запустіть сервер:
    ```bash
    uvicorn app.main:app --reload
    ```

---

## 🧪 Запуск тестів та перевірка покриття

Запустіть тести та отримайте звіт про покриття коду:
```bash
pytest --cov=app tests/
```

---

## 📚 Генерація документації (Sphinx)

Для повторної збірки HTML документації виконайте команду в корні проекту:
```bash
sphinx-build -b html docs docs/_build/html
```
Згенеровані сторінки будуть знаходитися у директорії: `docs/_build/html/index.html`.

---

## 🗺️ Список основних маршрутів (API Endpoints)

### 🔐 Аутентифікація (`/auth`)
*   `POST /auth/signup` — Реєстрація нового користувача (повертає `201 Created`).
*   `POST /auth/login` — Вхід користувача (повертає `access_token` та `refresh_token`).
*   `POST /auth/token` — Вхід (OAuth2 форма для Swagger).
*   `POST /auth/refresh_token` — Оновлення пари токенів за допомогою `refresh_token`.
*   `GET /auth/verify/{token}` — Підтвердження реєстрації через email.
*   `POST /auth/request_password_reset` — Запит на скидання пароля.
*   `POST /auth/reset_password` — Встановлення нового пароля.

### 👤 Користувачі (`/users`)
*   `GET /users/me` — Профіль користувача (**Rate limited: 10/min, кешується з Redis**).
*   `PATCH /users/avatar` — Оновлення аватара в Cloudinary (**Дозволено тільки для Admin**).

### 📞 Контакти (`/contacts`) — *JWT-авторизовано та розмежовано*
*   `POST /contacts/` — Створення нового контакту.
*   `GET /contacts/` — Пошук та список контактів.
*   `GET /contacts/{contact_id}` — Отримання контакту за ID.
*   `PUT /contacts/{contact_id}` — Оновлення контакту.
*   `DELETE /contacts/{contact_id}` — Видалення контакту.
*   `GET /contacts/birthdays/upcoming` — Список днів народження на найближчі 7 днів.
