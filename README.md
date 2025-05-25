// FOR REVIEW
// IP ADDRESS: 158.160.28.122
// DOMAIN: https://foodgram-warqone.zapto.org/
// ADMIN EMAIL: warqone@gmail.com
// ADMIN PASSWORD: JlOv3bJ-5z
// ADMIN USERNAME: Admin
# **Foodgram - Как инстаграм, но только для рецептов!**
___  
[![Main Foodgram workflow](https://github.com/warqone/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/warqone/foodgram/actions/workflows/main.yml)  

---

## **Возможности проекта**  
**Foodgram** - это удобная платформа для обмена рецептами! Здесь вы можете:  
- **Выкладывать свои любимые рецепты** и делиться ими с друзьями.  
- **Добавлять чужие рецепты в избранное**, чтобы всегда иметь под рукой.  
- **Подписываться на других авторов** и следить за их кулинарными шедеврами.  
- **Составлять список покупок** на основе избранных рецептов.  
- **API для интеграции** с другими сервисами и приложениями.  

---

## **Стек используемых технологий**  
Проект создан на современных и надёжных технологиях:  

- [Python](https://www.python.org/) - язык программирования для разработки веб-приложений.  
- [Django](https://www.djangoproject.com/) - мощный фреймворк для создания веб-приложений.  
- [Django Rest Framework](https://www.django-rest-framework.org/) - удобное создание API на базе Django.  
- [PostgreSQL](https://www.postgresql.org/) - надёжная реляционная база данных.  
- [React](https://react.dev/) - библиотека для создания интерактивных интерфейсов.  
- [Docker](https://www.docker.com/) - контейнеризация и упрощение развёртывания.  
- [Yandex Cloud](https://cloud.yandex.ru/) - облачная платформа для размещения проекта.  

---

## **Как развернуть проект (локально)**  
### **1. Клонируйте репозиторий и перейдите в него:**  
```bash
git clone git@github.com:warqone/foodgram.git
cd foodgram
```

### 2. Создайте файл настроек (.env) и заполните его:
```code
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=<your_domain> localhost 127.0.0.1
MEDIA_ROOT=/app/media
DEBUG=False #  (опционально)
SQLITE=False #  (опционально)
```
### 3. Запустите проект через Docker Compose:
```bash
docker compose -f docker-compose.production.yml up -d --build
```
### 4. Выполните миграции и сбор статических файлов:
```bash
docker compose -f docker-compose.production.yml exec backend python manage.py migrate
docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
docker compose -f docker-compose.production.yml exec backend cp -r /app/backend_static/. /backend_static/static/
```
### 5. Готово!
#### Теперь вы можете зайти на сайт по [адресу](http://127.0.0.1:9000)
____
### Как работать с проектом (основные команды)
##### Запуск контейнеров:
```bash
docker compose up -d
```
##### Обновление зависимостей:
```bash
docker compose exec backend pip install -r requirements.txt
```
____
### Развёртывание на сервере
#### 1. Подготовьте сервер:
 - Установите Docker и Docker Compose.
 - Настройте доменное имя и SSL (например, через Certbot).

#### 2. Деплой через GitHub Actions:
 - При каждом пуше на ветку main происходит автоматический деплой.
 - Для работы CI/CD необходимо настроить секреты в репозитории:
```
DOCKER_USERNAME
DOCKER_PASSWORD
SSH_KEY
SSH_PASSPHRASE
HOST
USER
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
SECRET_KEY
ALLOWED_HOSTS
DEBUG
```
____
#### Пример использования API:
#### Получение списка рецептов:
```bash
curl http://127.0.0.1:8000/api/recipes/
```
#### Получение всех рецептов:
```bash
curl -X GET http://127.0.0.1:8000/api/recipes/ 
```
____
# Автор - [warqone](https://github.com/warqone)