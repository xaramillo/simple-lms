import os
import json
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import markdown
from werkzeug.security import generate_password_hash, check_password_hash

# Configuración inicial
app = Flask(__name__)
app.config["SECRET_KEY"] = "tu_clave_secreta_muy_segura_aqui"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lms.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["COURSES_DIR"] = "courses"
app.config["REGISTRATION_OPEN"] = True  # Permitir auto-registro

# Inicialización de extensiones
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Modelo de Usuario
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Clase Curso (sin cambios)
class Course:
    def __init__(self, course_path):
        self.path = course_path
        self.load_metadata()
        self.load_content()
    
    # ... (mismos métodos que antes)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def load_courses():
    # ... (misma implementación que antes)

# Crear la aplicación
def create_app():
    # ... (configuración previa)
    
    # Rutas de autenticación
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
            
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password) and user.is_active:
                login_user(user)
                return redirect(url_for("index"))
                
            flash("Usuario o contraseña inválidos")
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if not app.config["REGISTRATION_OPEN"]:
            return redirect(url_for("index"))
            
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            
            if User.query.filter_by(username=username).first():
                flash("El nombre de usuario ya existe")
                return redirect(url_for("register"))

            new_user = User(username=username)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash("Registro exitoso. Por favor inicia sesión.")
            return redirect(url_for("login"))

        return render_template("register.html")

    # Rutas existentes actualizadas con protección
    @app.route("/")
    def index():
        return render_template("index.html", courses=app.courses)

    @app.route("/course/<slug>")
    @login_required
    def course_detail(slug):
        course = next((c for c in app.courses if c.slug == slug), None)
        if not course:
            return "Curso no encontrado", 404
        return render_template("course.html", course=course)

    return app

if __name__ == "__main__":
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
    
    app = create_app()
    app.courses = load_courses(app.config["COURSES_DIR"])
    app.run(debug=True)