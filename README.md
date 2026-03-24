# NeoSync — трекер подписок

Приложение для отслеживания платных подписок. Есть веб-версия и мобильное приложение на Flutter.

## Стек

- **Бэкенд:** Python, Flask, SQLAlchemy, SQLite
- **Веб-фронтенд:** HTML/CSS/JS (Jinja2 шаблоны)
- **Мобильное приложение:** Flutter (Web, Android, iOS)
- **Авторизация:** JWT токены для мобилки, Flask-Login для веба, OAuth (Google, Yandex)
- **Email:** SMTP Gmail для отправки кодов подтверждения при регистрации

## Структура

```
├── app.py              # Flask приложение, все роуты
├── models.py           # Модели БД
├── config.py           # Конфиг (читает из .env)
├── email_import.py     # Импорт подписок из почты через IMAP
├── requirements.txt    # Python зависимости
├── templates/          # HTML шаблоны веб-версии
├── static/             # CSS/JS для веба
└── rpza_sredi_navoza/  # Flutter мобильное приложение
    └── lib/
        ├── screens/    # Экраны
        ├── providers/  # State management
        ├── api/        # HTTP клиент
        └── models/     # Dart модели
```

## Запуск бэкенда

1. Установи зависимости:
```bash
pip install -r requirements.txt
```

2. Создай файл `.env` в корне (скопируй из `.env.example`) и заполни своими данными

3. Запусти Flask:
```bash
python app.py
```

Сервер поднимется на `http://localhost:5000`

## Запуск Flutter (веб)

```bash
cd rpza_sredi_navoza
flutter pub get
flutter run -d chrome
```

## Регистрация и код подтверждения

При регистрации на почту отправляется 6-значный код подтверждения.

**Если письмо не пришло** — смотри в терминал Flask. Там будет строка:
```
[REGISTER] === FALLBACK === Код для email@example.com: 123456 ===
```
Введи этот код вручную на экране подтверждения.

Это происходит если не настроены переменные `EMAIL_USER` / `EMAIL_PASSWORD` в `.env`.

## Импорт подписок из почты

Приложение подключается к почте через IMAP и ищет письма о подписках.

Для Яндекс почты нужно:
1. Включить IMAP в настройках почты (Все настройки → Почтовые программы)
2. Создать пароль приложения на id.yandex.ru → Безопасность → Пароли приложений

**Если сканирование не работает** — смотри терминал Flask, там будет точная ошибка подключения.

## Мобильное API

Все мобильные роуты начинаются с `/mobile/`:
- `POST /mobile/auth/register` — регистрация (отправляет код на почту)
- `POST /mobile/auth/verify-email` — подтверждение кода
- `POST /mobile/auth/login` — вход
- `GET /mobile/subscriptions` — список подписок
- `POST /mobile/email/scan` — сканирование почты
