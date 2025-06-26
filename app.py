from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Book, Category, Order, Review, Cart, CartItem, OrderItem
from datetime import datetime
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import re
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose

load_dotenv()

app = Flask(__name__)

app.config.from_pyfile('config.py')

db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршруты аутентификации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'buyer')
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        middle_name = request.form.get('middle_name')

        # Проверка обязательных полей
        if not username or not email or not password:
            flash('Все поля обязательны для заполнения', 'error')
            return redirect(url_for('register'))

        # Проверка уникальности логина
        if User.query.filter_by(username=username).first():
            flash('Логин уже занят', 'error')
            return redirect(url_for('register'))

        # Проверка уникальности email
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'error')
            return redirect(url_for('register'))

        # Проверка ФИО для автора
        if role == 'author':
            if not last_name or not first_name or not middle_name:
                flash('Для авторов обязательны Фамилия, Имя и Отчество', 'error')
                return redirect(url_for('register'))

        # Проверка сложности пароля (должен содержать хотя бы один спецсимвол)
        if not re.search(r'[!@#$%^&*()_+\-=[\]{};:\'\",.<>/?]', password):
            flash('Пароль должен содержать хотя бы один специальный символ (!@#$%^&* и т.д.)', 'error')
            return redirect(url_for('register'))
        # Проверка наличия хотя бы одной заглавной буквы
        if not re.search(r'[A-ZА-Я]', password):
            flash('Пароль должен содержать хотя бы одну заглавную букву', 'error')
            return redirect(url_for('register'))

        # Проверяем, что выбранная роль допустима
        if role not in ['buyer', 'author', 'admin']:
            role = 'buyer'

        # Проверка username
        if not re.match(r'^[\w]{3,30}$', username):
            flash('Логин должен содержать только буквы, цифры и _ и быть длиной от 3 до 30 символов', 'error')
            return redirect(url_for('register'))
        # Проверка email
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash('Некорректный формат email', 'error')
            return redirect(url_for('register'))
        # Проверка ФИО для автора
        if role == 'author':
            fio_fields = [(last_name, 'Фамилия'), (first_name, 'Имя'), (middle_name, 'Отчество')]
            for value, label in fio_fields:
                if not value or not re.match(r'^[A-Za-zА-Яа-яёЁ\-]+$', value):
                    flash(f'{label} может содержать только буквы и дефис', 'error')
                    return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            role=role,
            last_name=last_name if role == 'author' else None,
            first_name=first_name if role == 'author' else None,
            middle_name=middle_name if role == 'author' else None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Вход выполнен успешно!')
            return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы')
    return redirect(url_for('index'))

# Защищенные маршруты
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'edit_profile':
            # Логика редактирования профиля
            email = request.form.get('email')
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            
            if email != current_user.email:
                # Проверка формата email
                if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                    flash('Некорректный формат email', 'error')
                    return redirect(url_for('profile'))
                if User.query.filter_by(email=email).first():
                    flash('Этот email уже используется', 'error')
                    return redirect(url_for('profile'))
                current_user.email = email
            
            if current_password and new_password:
                # Проверка сложности нового пароля
                if not re.search(r'[!@#$%^&*()_+\-=[\]{};:\'\",.<>/?]', new_password):
                    flash('Пароль должен содержать хотя бы один специальный символ (!@#$%^&* и т.д.)', 'error')
                    return redirect(url_for('profile'))
                if not re.search(r'[A-ZА-Я]', new_password):
                    flash('Пароль должен содержать хотя бы одну заглавную букву', 'error')
                    return redirect(url_for('profile'))
                if current_user.check_password(current_password):
                    current_user.set_password(new_password)
                else:
                    flash('Неверный текущий пароль', 'error')
                    return redirect(url_for('profile'))
            
            db.session.commit()
            flash('Профиль успешно обновлен', 'success')
            return redirect(url_for('profile'))

        elif form_type == 'upload_book':
            if current_user.role != 'author':
                flash('У вас нет прав для загрузки книг', 'error')
                return redirect(url_for('profile')) # Перенаправляем на профиль, не на index

            title = request.form.get('title')
            description = request.form.get('description')
            price = float(request.form.get('price'))
            file_format = request.form.get('file_format')
            book_file = request.files.get('book_file')
            cover_image = request.files.get('cover_image')

            if not all([title, description, price, file_format, book_file]):
                flash('Все поля должны быть заполнены', 'error')
                return redirect(url_for('profile', _anchor='upload-book')) # Перенаправляем на секцию загрузки

            # Проверка цены
            try:
                if price <= 0:
                    flash('Цена должна быть положительным числом', 'error')
                    return redirect(url_for('profile', _anchor='upload-book'))
            except Exception:
                flash('Некорректная цена', 'error')
                return redirect(url_for('profile', _anchor='upload-book'))
            # Проверка файла книги
            allowed_formats = ['pdf', 'epub']
            file_ext = book_file.filename.rsplit('.', 1)[1].lower() if '.' in book_file.filename else ''
            if file_format.lower() != file_ext or file_ext not in allowed_formats:
                 flash(f'Неверный формат файла. Ожидается {file_format}', 'error')
                 return redirect(url_for('profile', _anchor='upload-book'))
            if book_file.content_length and book_file.content_length > 10*1024*1024:
                flash('Файл книги слишком большой (максимум 10 МБ)', 'error')
                return redirect(url_for('profile', _anchor='upload-book'))
            # Проверка обложки
            if cover_image and cover_image.filename:
                if not re.search(r'\.(jpg|jpeg|png|gif|bmp)$', cover_image.filename.lower()):
                    flash('Обложка должна быть изображением (jpg, jpeg, png, gif, bmp)', 'error')
                    return redirect(url_for('profile', _anchor='upload-book'))
                if cover_image.content_length and cover_image.content_length > 5*1024*1024:
                    flash('Файл обложки слишком большой (максимум 5 МБ)', 'error')
                    return redirect(url_for('profile', _anchor='upload-book'))

            upload_folder_books = os.path.join(app.config['UPLOAD_FOLDER'], 'books')
            os.makedirs(upload_folder_books, exist_ok=True)

            # Разделяем имя файла на имя и расширение
            file_name_without_ext, file_ext = os.path.splitext(book_file.filename)
            
            # Формируем новое имя файла с timestamp и оригинальным расширением
            file_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file_name_without_ext)}{file_ext}"
            file_path = os.path.join(upload_folder_books, file_filename)
            book_file.save(file_path)

            # Получаем выбранную категорию, страну и период
            category_id = request.form.get('category')
            country = request.form.get('country')
            period = request.form.get('period')

            category = Category.query.get(category_id)

            if not category:
                flash('Выбрана неверная категория', 'error')
                # Удаляем сохраненный файл книги, если категория не найдена
                if os.path.exists(file_path):
                    os.remove(file_path)
                return redirect(url_for('profile', _anchor='upload-book'))

            cover_image_path = None
            if cover_image and cover_image.filename:
                 upload_folder_covers = os.path.join(app.config['UPLOAD_FOLDER'], 'covers')
                 os.makedirs(upload_folder_covers, exist_ok=True)
                 cover_image_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(cover_image.filename)}"
                 cover_image_path = os.path.join(upload_folder_covers, cover_image_filename)
                 cover_image.save(cover_image_path)
                 # Сохраняем относительный путь для статики
                 cover_image_relpath = f"uploads/covers/{cover_image_filename}".replace('\\', '/')
            else:
                 cover_image_relpath = None

            new_book = Book(
                title=title,
                description=description,
                price=price,
                file_format=file_format,
                author_id=current_user.id,
                country=country,
                period=period,
                cover_image=cover_image_relpath, 
                file_path=file_path 
            )

            db.session.add(new_book)
            new_book.categories.append(category)
            db.session.commit()

            flash('Книга успешно загружена!', 'success')
            return redirect(url_for('profile', _anchor='my-books')) # Перенаправляем на секцию мои книги

    # GET запрос или POST с неверным form_type
    categories = Category.query.all()
    users = []
    all_orders = []
    if current_user.role == 'admin':
        users = User.query.all()
        all_orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('profile.html', categories=categories, users=users, all_orders=all_orders)

@app.route('/profile/book/add', methods=['POST'])
@login_required
def add_book():
    if current_user.role != 'author':
        flash('У вас нет прав для добавления книг', 'error')
        return redirect(url_for('profile'))

    title = request.form.get('title')
    description = request.form.get('description')
    price = float(request.form.get('price'))
    cover = request.files.get('cover')
    book_file = request.files.get('book_file')

    if not all([title, description, price, cover, book_file]):
        flash('Все поля должны быть заполнены', 'error')
        return redirect(url_for('profile'))

    # Сохраняем файлы
    cover_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', f"{datetime.now().timestamp()}_{secure_filename(cover.filename)}")
    os.makedirs(os.path.dirname(cover_path), exist_ok=True)
    cover.save(cover_path)
    # Сохраняем относительный путь для статики
    cover_relpath = f"uploads/covers/{os.path.basename(cover_path)}".replace('\\', '/')

    # Разделяем имя файла книги на имя и расширение
    book_file_name_without_ext, book_file_ext = os.path.splitext(book_file.filename)
    # Формируем новое имя файла книги с timestamp, безопасным именем и оригинальным расширением
    book_filename_new = f"{datetime.now().timestamp()}_{secure_filename(book_file_name_without_ext)}{book_file_ext}"
    book_path = os.path.join(app.config['UPLOAD_FOLDER'], 'books', book_filename_new)

    os.makedirs(os.path.dirname(book_path), exist_ok=True)

    book_file.save(book_path)

    book = Book(
        title=title,
        description=description,
        price=price,
        cover_image=f"uploads/covers/{os.path.basename(cover_path)}".replace('\\', '/'),
        file_path=book_path,
        author_id=current_user.id
    )
    db.session.add(book)
    db.session.commit()

    flash('Книга успешно добавлена', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/book/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if current_user.role != 'author' or book.author_id != current_user.id:
        flash('У вас нет прав для редактирования этой книги', 'error')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        book.title = request.form.get('title')
        book.description = request.form.get('description')
        try:
            price = float(request.form.get('price'))
            if price <= 0:
                flash('Цена должна быть положительным числом', 'error')
                return redirect(url_for('edit_book', book_id=book.id))
            book.price = price
        except Exception:
            flash('Некорректная цена', 'error')
            return redirect(url_for('edit_book', book_id=book.id))

        cover = request.files.get('cover')
        if cover and cover.filename:
            if not re.search(r'\.(jpg|jpeg|png|gif|bmp)$', cover.filename.lower()):
                flash('Обложка должна быть изображением (jpg, jpeg, png, gif, bmp)', 'error')
                return redirect(url_for('edit_book', book_id=book.id))
            if cover.content_length and cover.content_length > 5*1024*1024:
                flash('Файл обложки слишком большой (максимум 5 МБ)', 'error')
                return redirect(url_for('edit_book', book_id=book.id))
            cover_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', f"{datetime.now().timestamp()}_{cover.filename}")
            os.makedirs(os.path.dirname(cover_path), exist_ok=True)
            cover.save(cover_path)
            # Сохраняем относительный путь для статики
            book.cover_image = f"uploads/covers/{os.path.basename(cover_path)}".replace('\\', '/')

        book_file = request.files.get('book_file')
        if book_file and book_file.filename:
            allowed_formats = ['pdf', 'epub']
            book_file_name_without_ext, book_file_ext = os.path.splitext(book_file.filename)
            if book_file_ext[1:].lower() not in allowed_formats:
                flash('Файл книги должен быть в формате PDF или EPUB', 'error')
                return redirect(url_for('edit_book', book_id=book.id))
            if book_file.content_length and book_file.content_length > 10*1024*1024:
                flash('Файл книги слишком большой (максимум 10 МБ)', 'error')
                return redirect(url_for('edit_book', book_id=book.id))
            # Формируем новое имя файла книги с timestamp, безопасным именем и оригинальным расширением
            book_filename_new = f"{datetime.now().timestamp()}_{secure_filename(book_file_name_without_ext)}{book_file_ext}"
            book_path = os.path.join(app.config['UPLOAD_FOLDER'], 'books', book_filename_new)
            os.makedirs(os.path.dirname(book_path), exist_ok=True)
            book_file.save(book_path)
            book.file_path = book_path

        db.session.commit()
        flash('Книга успешно обновлена', 'success')
        return redirect(url_for('profile'))

    return render_template('edit_book.html', book=book)

@app.route('/profile/book/<int:book_id>/delete')
@login_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if current_user.role != 'author' or book.author_id != current_user.id:
        flash('У вас нет прав для удаления этой книги', 'error')
        return redirect(url_for('profile'))

    # Удаляем файлы
    if book.cover_image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], book.cover_image)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], book.cover_image))
    if os.path.exists(book.file_path):
        os.remove(book.file_path)

    db.session.delete(book)
    db.session.commit()

    flash('Книга успешно удалена', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/user/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        flash('У вас нет прав для редактирования пользователей', 'error')
        return redirect(url_for('profile'))

    user = User.query.get_or_404(user_id)
    role = request.form.get('role')
    # Дополнительные поля для валидации
    email = request.form.get('email')
    username = request.form.get('username')
    last_name = request.form.get('last_name')
    first_name = request.form.get('first_name')
    middle_name = request.form.get('middle_name')
    # Валидация email
    if email and email != user.email:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash('Некорректный формат email', 'error')
            return redirect(url_for('profile'))
        if User.query.filter_by(email=email).first():
            flash('Этот email уже используется', 'error')
            return redirect(url_for('profile'))
        user.email = email
    # Валидация username
    if username and username != user.username:
        if not re.match(r'^[\w]{3,30}$', username):
            flash('Логин должен содержать только буквы, цифры и _ и быть длиной от 3 до 30 символов', 'error')
            return redirect(url_for('profile'))
        if User.query.filter_by(username=username).first():
            flash('Логин уже занят', 'error')
            return redirect(url_for('profile'))
        user.username = username
    # Валидация ФИО для автора
    if role == 'author':
        fio_fields = [(last_name, 'Фамилия'), (first_name, 'Имя'), (middle_name, 'Отчество')]
        for value, label in fio_fields:
            if not value or not re.match(r'^[A-Za-zА-Яа-яёЁ\-]+$', value):
                flash(f'{label} может содержать только буквы и дефис', 'error')
                return redirect(url_for('profile'))
        user.last_name = last_name
        user.first_name = first_name
        user.middle_name = middle_name
    if role in ['buyer', 'author', 'admin']:
        user.role = role
        db.session.commit()
        flash('Пользователь успешно обновлен', 'success')
    else:
        flash('Неверная роль пользователя', 'error')
    return redirect(url_for('profile'))

@app.route('/profile/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.role != 'admin':
        flash('У вас нет прав для удаления пользователей', 'error')
        return redirect(url_for('profile'))
    if user.id == current_user.id:
        flash('Вы не можете удалить свой аккаунт', 'error')
        return redirect(url_for('profile'))
    # Удаляем все книги пользователя, если он автор
    if user.role == 'author':
        for book in user.books:
            # Удаляем файлы книги и обложки
            if book.cover_image and os.path.exists(book.cover_image):
                try:
                    os.remove(book.cover_image)
                except Exception:
                    pass
            if book.file_path and os.path.exists(book.file_path):
                try:
                    os.remove(book.file_path)
                except Exception:
                    pass
            db.session.delete(book)
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь успешно удален', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/user/<int:user_id>')
@login_required
def user_details(user_id):
    if current_user.role != 'admin':
        flash('У вас нет прав для просмотра информации о пользователях', 'error')
        return redirect(url_for('profile'))
    user = User.query.get_or_404(user_id)
    return render_template('user_details.html', user=user)

@app.route('/')
def index():
    popular_books = Book.query.join(User).filter(User.role == 'author').order_by(Book.created_at.desc()).limit(10).all()
    return render_template('index.html', popular_books=popular_books)

@app.route('/catalog')
def catalog():
    # Получаем параметры фильтрации
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    sort = request.args.get('sort', 'newest')
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    page = request.args.get('page', 1, type=int)
    
    # Базовый запрос
    query = Book.query
    
    # Применяем фильтры
    if search:
        query = query.filter(
            db.or_(
                Book.title.ilike(f'%{search}%'),
                Book.description.ilike(f'%{search}%')
            )
        )
    
    if category_id:
        query = query.filter(Book.categories.any(Category.id == category_id))
    
    if price_min is not None:
        query = query.filter(Book.price >= price_min)
    
    if price_max is not None:
        query = query.filter(Book.price <= price_max)
    
    # Применяем сортировку
    if sort == 'newest':
        query = query.order_by(Book.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Book.created_at.asc())
    elif sort == 'price_asc':
        query = query.order_by(Book.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Book.price.desc())
    elif sort == 'rating':
        # Сортировка по среднему рейтингу
        query = query.outerjoin(Review).group_by(Book.id).order_by(
            db.func.avg(Review.rating).desc()
        )
    
    # Получаем все категории для фильтра
    categories = Category.query.all()
    
    # Пагинация
    books = query.paginate(page=page, per_page=12)
    
    return render_template('catalog.html',
                         books=books,
                         categories=categories,
                         search=search,
                         category_id=category_id,
                         sort=sort,
                         price_min=price_min,
                         price_max=price_max)

@app.route('/authors')
def authors():
    # Get filter parameters from request
    genres = request.args.getlist('genre')
    countries = request.args.getlist('country')
    periods = request.args.getlist('period')
    sort_by = request.args.get('sort', 'popularity')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    # Получаем всех пользователей с ролью 'author'
    authors_query = User.query.filter_by(role='author')
    authors_list = authors_query.all()

    # Фильтрация по книгам автора
    if genres or countries or periods:
        filtered_authors = []
        for author in authors_list:
            books = author.books
            match = False
            for book in books:
                genre_match = not genres or any(cat.name.lower() in genres for cat in book.categories)
                country_match = not countries or (book.country and book.country.lower() in countries)
                period_match = not periods or (book.period and book.period.lower() in periods)
                if genre_match and country_match and period_match:
                    match = True
                    break
            if match:
                filtered_authors.append(author)
        authors_list = filtered_authors

    return render_template('authors.html',
                         authors=authors_list, # Передаем список авторов
                         genres=genres,
                         countries=countries,
                         periods=periods,
                         sort_by=sort_by,
                         page=page,
                         per_page=per_page)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/book/<int:book_id>/review', methods=['POST'])
@login_required
def add_review(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Проверяем, не оставил ли пользователь уже отзыв
    existing_review = Review.query.filter_by(book_id=book_id, user_id=current_user.id).first()
    if existing_review:
        flash('Вы уже оставили отзыв на эту книгу', 'error')
        return redirect(url_for('book', book_id=book_id))
    
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment')
    
    if not rating or rating < 1 or rating > 5:
        flash('Пожалуйста, выберите оценку от 1 до 5', 'error')
        return redirect(url_for('book', book_id=book_id))
    
    review = Review(
        book_id=book_id,
        user_id=current_user.id,
        rating=rating,
        comment=comment
    )
    
    db.session.add(review)
    db.session.commit()
    
    flash('Спасибо за ваш отзыв!', 'success')
    return redirect(url_for('book', book_id=book_id))

@app.route('/book/<int:book_id>/review/<int:review_id>/delete')
@login_required
def delete_review(book_id, review_id):
    review = Review.query.get_or_404(review_id)
    
    # Проверяем, является ли пользователь автором отзыва или администратором
    if review.user_id != current_user.id and current_user.role != 'admin':
        flash('У вас нет прав для удаления этого отзыва', 'error')
        return redirect(url_for('book', book_id=book_id))
    
    db.session.delete(review)
    db.session.commit()
    
    flash('Отзыв успешно удален', 'success')
    return redirect(url_for('book', book_id=book_id))

@app.route('/order/<int:order_id>')
@login_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Проверяем, имеет ли пользователь доступ к этому заказу
    if current_user.role != 'admin' and order.buyer_id != current_user.id:
        flash('У вас нет доступа к этому заказу', 'error')
        return redirect(url_for('profile'))
    
    return render_template('order.html', order=order)

@app.route('/order/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    if current_user.role != 'admin':
        flash('У вас нет прав для изменения статуса заказа', 'error')
        return redirect(url_for('profile'))
    
    order = Order.query.get_or_404(order_id)
    status = request.form.get('status')
    
    if status not in ['completed', 'cancelled']:
        flash('Неверный статус заказа', 'error')
        return redirect(url_for('order_details', order_id=order_id))
    
    order.status = status
    db.session.commit()
    
    flash('Статус заказа обновлен', 'success')
    return redirect(url_for('order_details', order_id=order_id))

@app.route('/cart')
@login_required
def cart():
    cart = current_user.cart
    return render_template('cart.html', cart=cart)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('index'))
        
    books = Book.query.join(User).filter(
        db.or_(
            Book.title.ilike(f'%{query}%'),
            Book.description.ilike(f'%{query}%'),
            User.email.ilike(f'%{query}%')
        )
    ).all()
    
    return render_template('search_results.html', books=books, query=query)

# Маршрут для отображения деталей книги
@app.route('/book/<int:book_id>')
def book(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book.html', book=book)

# Маршрут для добавления книги в корзину
@app.route('/add_to_cart/<int:book_id>', methods=['POST'])
@login_required
def add_to_cart(book_id):
    book = Book.query.get_or_404(book_id)

    # Получаем или создаем корзину для текущего пользователя
    cart = current_user.cart
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)

    # Проверяем, есть ли книга уже в корзине
    cart_item = CartItem.query.filter_by(cart_id=cart.id, book_id=book_id).first()

    if cart_item:
        flash('Книга уже в корзине!', 'info')
        response_message = 'Книга уже в корзине!'
        response_status = 'info'
    else:
        # Если книги нет, создаем новый элемент корзины
        cart_item = CartItem(
            cart_id=cart.id,
            book_id=book.id,
            price=book.price # Сохраняем цену на момент добавления в корзину
        )
        db.session.add(cart_item)
        flash('Книга добавлена в корзину!', 'success')
        response_message = 'Книга добавлена в корзину!'
        response_status = 'success'

    db.session.commit()
    
    return jsonify({'message': response_message, 'status': response_status}), 200

# Маршрут для удаления книги из корзины
@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)

    # Проверяем, принадлежит ли элемент корзины текущему пользователю
    if cart_item.cart.user_id != current_user.id:
        flash('У вас нет прав для удаления этого элемента из корзины', 'error')
        return redirect(url_for('cart'))

    db.session.delete(cart_item)
    db.session.commit()

    flash('Книга удалена из корзины!', 'success')
    return redirect(url_for('cart'))

# Маршрут для оформления заказа
@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = current_user.cart

    if not cart or not cart.items:
        flash('Ваша корзина пуста.', 'error')
        return redirect(url_for('cart'))

    # Создаем новый заказ
    new_order = Order(
        buyer_id=current_user.id,
        status='pending'  # Или 'completed' сразу, если оплата не требуется
    )
    db.session.add(new_order)
    db.session.flush() # Получаем ID заказа до коммита

    # Переносим элементы из корзины в заказ
    for item in cart.items:
        order_item = OrderItem(
            order_id=new_order.id,
            book_id=item.book_id,
            price=item.price
        )
        db.session.add(order_item)

    # Очищаем корзину (удаляем все CartItem, корзина будет удалена cascade'ом)
    for item in cart.items:
        db.session.delete(item)
    db.session.delete(cart)

    db.session.commit()

    flash('Заказ успешно оформлен!', 'success')
    return redirect(url_for('profile', _anchor='my-orders')) # Перенаправляем на мои покупки

@app.route('/download_book/<int:book_id>')
@login_required
def download_book(book_id):
    book = Book.query.get_or_404(book_id)
    # Проверка: пользователь купил книгу или он админ
    is_buyer = any(
        order_item.book_id == book_id
        for order in current_user.orders
        for order_item in order.items
        if order.status == 'completed'
    )
    if not (is_buyer or current_user.role == 'admin'):
        flash('У вас нет доступа к скачиванию этой книги', 'error')
        return redirect(url_for('book', book_id=book_id))
    
    # Путь к файлу
    if not book.file_path:
        flash('Файл книги не найден', 'error')
        return redirect(url_for('book', book_id=book_id))
    
    # Получаем абсолютный путь к файлу
    file_path = os.path.join(app.root_path, book.file_path)
    
    if not os.path.exists(file_path):
        flash('Файл книги не найден на сервере', 'error')
        return redirect(url_for('book', book_id=book_id))
    
    # Определяем расширение файла для mimetype и имени скачиваемого файла
    file_extension = os.path.splitext(book.file_path)[1].lower()
    mimetype = 'application/pdf' if file_extension == '.pdf' else 'application/epub+zip'
    download_name = f"{os.path.basename(book.file_path)}"

    return send_file(file_path, as_attachment=True, mimetype=mimetype, download_name=download_name)

@app.route('/read_book/<int:book_id>')
@login_required
def read_book(book_id):
    book = Book.query.get_or_404(book_id)
    # Проверка: пользователь купил книгу или он админ
    is_buyer = any(
        order_item.book_id == book_id
        for order in current_user.orders
        for order_item in order.items
        if order.status == 'completed'
    )
    if not (is_buyer or current_user.role == 'admin'):
        flash('У вас нет доступа к чтению этой книги', 'error')
        return redirect(url_for('book', book_id=book_id))
    # Определяем путь к файлу
    if hasattr(book, 'file_path') and book.file_path:
        file_path = book.file_path
    elif hasattr(book, 'file') and book.file:
        file_path = book.file
    else:
        flash('Файл книги не найден', 'error')
        return redirect(url_for('book', book_id=book_id))
    # Определяем формат
    ext = file_path.rsplit('.', 1)[-1].lower()
    if ext == 'pdf':
        return render_template('read_pdf.html', book=book, file_path=file_path)
    else:
        flash('Онлайн-чтение поддерживается только для PDF', 'error')
        return redirect(url_for('book', book_id=book_id))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Доступ только для администратора', 'error')
        return redirect(url_for('profile'))
    users = User.query.all()
    books = Book.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin.html', users=users, books=books, orders=orders)

class AdminOnlyView(ModelView):
    def is_accessible(self):
        from flask_login import current_user
        return current_user.is_authenticated and current_user.role == 'admin'
    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for, flash
        flash('Доступ только для администратора', 'error')
        return redirect(url_for('login'))

class UserAdminView(AdminOnlyView):
    column_list = ('id', 'email', 'username', 'role', 'created_at')
    column_searchable_list = ('email', 'username')
    column_filters = ('role',)
    form_excluded_columns = ('password_hash', 'books', 'orders', 'reviews', 'cart')
    can_view_details = True
    can_export = True
    column_details_list = ('id', 'email', 'username', 'role', 'created_at', 'books', 'orders')
    def delete_model(self, model):
        from flask_login import current_user
        if model.id == current_user.id:
            from flask import flash
            flash('Нельзя удалить самого себя!', 'error')
            return False
        return super().delete_model(model)

class BookAdminView(AdminOnlyView):
    column_list = ('id', 'title', 'author', 'price', 'file_format', 'status', 'created_at')
    column_searchable_list = ('title',)
    column_filters = ('status', 'file_format')
    can_view_details = True
    can_export = True

class OrderAdminView(AdminOnlyView):
    column_list = ('id', 'buyer', 'status', 'created_at')
    column_filters = ('status',)
    can_view_details = True
    can_export = True

class CategoryAdminView(AdminOnlyView):
    column_list = ('id', 'name')
    column_searchable_list = ('name',)
    can_view_details = True
    can_export = True

admin = Admin(app, name='Админ-панель', template_mode='bootstrap4')
admin.add_view(UserAdminView(User, db.session, name='Пользователи'))
admin.add_view(BookAdminView(Book, db.session, name='Книги'))
admin.add_view(OrderAdminView(Order, db.session, name='Заказы'))
admin.add_view(CategoryAdminView(Category, db.session, name='Категории'))

if __name__ == '__main__':
    app.run(debug=True) 