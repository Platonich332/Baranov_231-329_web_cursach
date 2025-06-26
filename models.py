from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column('user_id', db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    last_name = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='buyer')
    created_at = db.Column('registration_date', db.DateTime, default=datetime.utcnow)
    
    # Отношения
    books = db.relationship('Book', backref='author', lazy=True, foreign_keys='Book.author_id')
    orders = db.relationship('Order', backref='buyer', lazy=True, foreign_keys='Order.buyer_id')
    reviews = db.relationship('Review', backref='user', lazy=True, foreign_keys='Review.user_id')
    cart = db.relationship('Cart', backref='user', uselist=False, lazy='joined', foreign_keys='Cart.user_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column('book_id', db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    file_format = db.Column(db.String(10))
    file_path = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column('upload_date', db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pending')
    country = db.Column(db.String(100))
    period = db.Column(db.String(100))
    cover_image = db.Column(db.String(255))
    
    # Отношения
    categories = db.relationship('Category', secondary='book_categories', backref='books')
    reviews = db.relationship('Review', backref='book', lazy=True, foreign_keys='Review.book_id')
    order_items = db.relationship('OrderItem', backref='book', lazy=True, foreign_keys='OrderItem.book_id')
    cart_items = db.relationship('CartItem', lazy=True, foreign_keys='CartItem.book_id')

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column('category_id', db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column('order_id', db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column('purchase_date', db.DateTime, default=datetime.utcnow)
    
    # Отношения
    items = db.relationship('OrderItem', backref='order', lazy=True, foreign_keys='OrderItem.order_id')

    @property
    def total_amount(self):
        return sum(item.price for item in self.items)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column('review_id', db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column('review_date', db.DateTime, default=datetime.utcnow)

class Cart(db.Model):
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения
    items = db.relationship('CartItem', backref='cart', lazy='joined', cascade='all, delete-orphan', foreign_keys='CartItem.cart_id')
    
    @property
    def total_amount(self):
        return sum(item.price for item in self.items)

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    book = db.relationship('Book', lazy='joined')

# Таблица связи многие-ко-многим для книг и категорий
book_categories = db.Table('book_categories',
    db.Column('book_id', db.Integer, db.ForeignKey('books.book_id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.category_id'), primary_key=True)
) 