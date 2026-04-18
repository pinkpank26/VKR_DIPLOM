Вот более **красивый и “гитхабный” README** с аккуратной структурой.

---

# 📧 Email Mailing System

Клиент-серверное приложение для автоматизации массовых email-рассылок бизнес-информации.

Проект разработан в рамках выпускной квалификационной работы и демонстрирует подход к реализации системы массовой рассылки с использованием **FastAPI**, **PostgreSQL**, **tkinter** и **SMTP**.

---

## 🚀 Возможности

* регистрация и авторизация пользователей
* импорт контактов из **CSV** и **Excel**
* создание шаблонов писем
* создание кампаний рассылки
* подготовка сообщений к отправке
* отправка писем через **SMTP**
* получение отчетов по кампаниям
* учет отписок получателей
* работа через **GUI** и **Swagger API**

---

## 🛠 Технологии

* **Python**
* **FastAPI**
* **SQLAlchemy**
* **PostgreSQL**
* **tkinter**
* **SMTP**
* **requests**
* **pgAdmin4**
* **Visual Studio Code**

---

## 📁 Структура проекта

```text id="r6fowm"
app/
  main.py
  config.py
  database.py
  models.py
  schemas.py
  security.py
  smtp_client.py
  tasks.py

client_gui.py
create_tables.sql
requirements.txt
.env
```

---

## ⚙️ Установка

### 1. Клонирование репозитория

```bash id="hmsa73"
git clone <repo_url>
cd <project_folder>
```

### 2. Создание виртуального окружения

```bash id="mngy0j"
python -m venv .venv
```

### 3. Активация виртуального окружения

**Windows PowerShell**

```bash id="1nqvgo"
.venv\Scripts\Activate.ps1
```

**Windows CMD**

```bash id="txrrlr"
.venv\Scripts\activate
```

**Linux / macOS**

```bash id="m8g5gd"
source .venv/bin/activate
```

### 4. Установка зависимостей

```bash id="nwlzyc"
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔐 Настройка `.env`

Создайте файл **`.env`** в корне проекта.

### Шаблон `.env`

```env id="37wzhf"
APP_SECRET_KEY=
APP_JWT_ISSUER=mailer_app
APP_JWT_EXPIRE_MIN=120

DB_URL=
DB_SCHEMA=mailing

SMTP_HOST=smtp.mail.ru
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_NAME=S8 Airlines
SMTP_FROM_EMAIL=

RATE_LIMIT_PER_MINUTE=30
MAX_RETRY=3
```

### Что нужно заполнить

| Переменная        | Описание                        |
| ----------------- | ------------------------------- |
| `APP_SECRET_KEY`  | секретный ключ для JWT          |
| `DB_URL`          | строка подключения к PostgreSQL |
| `SMTP_USERNAME`   | логин почтового ящика           |
| `SMTP_PASSWORD`   | SMTP-пароль / пароль приложения |
| `SMTP_FROM_EMAIL` | адрес отправителя               |

### Пример заполнения

```env id="3dynv5"
APP_SECRET_KEY=my_super_secret_key_123
APP_JWT_ISSUER=mailer_app
APP_JWT_EXPIRE_MIN=120

DB_URL=postgresql+psycopg://postgres:12345@127.0.0.1:5432/mailer_db
DB_SCHEMA=mailing

SMTP_HOST=smtp.mail.ru
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_USERNAME=example@mail.ru
SMTP_PASSWORD=your_smtp_password
SMTP_FROM_NAME=S8 Airlines
SMTP_FROM_EMAIL=example@mail.ru

RATE_LIMIT_PER_MINUTE=30
MAX_RETRY=3
```

### ⚠️ Важно

* не публикуйте реальный `.env` в репозитории
* не храните пароли и секретные ключи в GitHub
* используйте пароль приложения для почтового сервиса

---

## 🗄 Настройка базы данных

1. Создайте базу данных PostgreSQL, например:

```text id="nezw1w"
mailer_db
```

2. Выполните SQL-скрипт:

```text id="tsh1yw"
create_tables.sql
```

После этого будет создана схема `mailing` и все необходимые таблицы.

---

## ▶️ Запуск проекта

### Запуск сервера

```bash id="3fo4su"
python -m uvicorn app.main:app --reload
```

Сервер будет доступен по адресу:

```text id="v2o5pt"
http://127.0.0.1:8000
```

### Swagger API

```text id="gqudcm"
http://127.0.0.1:8000/docs
```

### Запуск GUI-клиента

```bash id="ghx67g"
python client_gui.py
```

---

## 🧭 Как пользоваться

1. Запустите сервер
2. Запустите GUI-клиент
3. Нажмите **«Проверить API»**
4. Зарегистрируйтесь или войдите в систему
5. Импортируйте контакты из **CSV** или **Excel**
6. Создайте шаблон письма
7. Создайте кампанию
8. Подготовьте кампанию к отправке
9. Запустите рассылку
10. Получите отчет по кампании

---

## 📥 Формат входных файлов

### CSV

```csv id="o6j2wg"
email,full_name,external_client_id,consent
andykovalev26@gmail.com,Андрей Ковалев,REAL-001,TRUE
user2@example.com,Иван Петров,REAL-002,TRUE
```

### Excel

Файл `.xlsx` должен содержать колонки:

* `email`
* `full_name`
* `external_client_id`
* `consent`

Колонка `email` обязательна.

---

## ✉️ Пример шаблона письма

**Название шаблона**

```text id="qkyx2k"
Летняя акция S8 2026
```

**Тема письма**

```text id="k0v41p"
Специальное предложение для {name} от S8 Airlines
```

**Текст письма**

```text id="dtdbwt"
Здравствуйте, {name}!

Компания S8 Airlines рада сообщить о специальном предложении на авиаперелеты.

Для наших клиентов доступны выгодные тарифы и скидки на популярные направления. Предложение действует ограниченное время.

Подробности можно уточнить на официальном сайте компании.

С уважением,
S8 Airlines
```

---

## 📡 Основные маршруты API

### Авторизация

* `POST /auth/register`
* `POST /auth/login`

### Контакты

* `POST /contacts/import_csv`
* `POST /contacts/import_excel`

### Шаблоны

* `POST /templates`
* `GET /templates`

### Кампании

* `POST /campaigns`
* `GET /campaigns`
* `POST /campaigns/{id}/prepare`
* `POST /campaigns/{id}/send`
* `GET /campaigns/{id}/report`
* `GET /campaigns/{id}/report/html`

### Отписка

* `GET /unsubscribe/{contact_id}`

---

## 🧪 Типовой сценарий тестирования

```text id="cgtswl"
1. Заполнить .env
2. Создать базу данных
3. Выполнить create_tables.sql
4. Запустить сервер
5. Запустить GUI
6. Проверить API
7. Зарегистрироваться
8. Импортировать контакты
9. Создать шаблон
10. Создать кампанию
11. Подготовить кампанию
12. Отправить кампанию
13. Проверить отчет
```

---

## ❗ Возможные проблемы

### Сервер не запускается

Проверьте:

* заполнен ли `.env`
* корректен ли `DB_URL`
* существует ли база данных
* выполнен ли `create_tables.sql`

### Письма не отправляются

Проверьте:

* `SMTP_USERNAME`
* `SMTP_PASSWORD`
* `SMTP_FROM_EMAIL`
* настройки SMTP-сервера

### Письма не приходят

Проверьте:

* папку **Спам**
* корректность email в таблице `contacts`
* статус записей в таблице `messages`

---

## 📌 Назначение проекта

Проект создан как исследовательский прототип системы массовой email-рассылки и демонстрирует автоматизацию следующих процессов:

* управление контактной базой
* хранение шаблонов писем
* управление кампаниями
* массовая SMTP-отправка
* фиксация результатов рассылки
* получение отчетной информации

---


