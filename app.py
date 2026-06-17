from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import random
from functools import wraps
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear la aplicación Flask
app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads/documentos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración de la base de datos
database_path = os.path.join(os.path.dirname(__file__), 'database', 'nobiru.db')
os.makedirs(os.path.dirname(database_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu_clave_secreta_super_segura_123')

# Inicializar la base de datos
db = SQLAlchemy(app)

# ============================================
# MODELOS DE BASE DE DATOS
# ============================================

class Usuario(db.Model):
    """Tabla de usuarios"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nombre_usuario = db.Column(db.String(80), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(120))
    fecha_registro = db.Column(db.DateTime, default=datetime.now)
    puntos = db.Column(db.Integer, default=0)
    insignia = db.Column(db.String(20), default='bronce')
    nivel = db.Column(db.Integer, default=1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nombre_usuario': self.nombre_usuario,
            'nombre_completo': self.nombre_completo,
            'puntos': self.puntos,
            'insignia': self.insignia,
            'nivel': self.nivel
        }


class Cuestionario(db.Model):
    """Tabla de cuestionarios"""
    __tablename__ = 'cuestionarios'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    categorias = db.Column(db.String(50))
    

class Pregunta(db.Model):
    """Tabla de preguntas (para cuestionarios)"""
    __tablename__ = 'preguntas'
    
    id = db.Column(db.Integer, primary_key=True)
    cuestionario_id = db.Column(db.Integer, db.ForeignKey('cuestionarios.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    opcion_a = db.Column(db.String(200))
    opcion_b = db.Column(db.String(200))
    opcion_c = db.Column(db.String(200))
    opcion_d = db.Column(db.String(200))
    respuesta_correcta = db.Column(db.String(1))  # A, B, C o D


class PostComunidad(db.Model):
    """Tabla de posts en comunidad"""
    __tablename__ = 'posts_comunidad'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    tipo = db.Column(db.String(20))  # 'pregunta', 'consejo', etc.


class Reel(db.Model):
    """Tabla de reels educativos"""
    __tablename__ = 'reels'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    categoria = db.Column(db.String(50))  # Matemáticas, Historia, Ciencias, etc.
    url_video = db.Column(db.String(500))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)


class Biblioteca(db.Model):
    """Tabla de archivos en biblioteca"""
    __tablename__ = 'biblioteca'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    autor = db.Column(db.String(120))
    tipo = db.Column(db.String(50))  # PDF, Libro, Diapositivas, Documento
    url_archivo = db.Column(db.String(500))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)


class Favorito(db.Model):
    """Tabla de favoritos del usuario"""
    __tablename__ = 'favoritos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(20))  # 'cuestionario', 'reel', 'pdf'
    item_id = db.Column(db.Integer)
    fecha_agregado = db.Column(db.DateTime, default=datetime.now)


# ============================================
# DATOS INICIALES
# ============================================

FRASES_DIARIAS = [
    "El esfuerzo de hoy es el éxito de mañana.",
    "Cada pregunta resuelta te acerca a tu meta.",
    "Aprender es avanzar.",
    "La constancia supera al talento.",
    "Nunca subestimes una hora de estudio.",
    "Tu futuro comienza con lo que haces hoy.",
    "La disciplina vence a la motivación."
]

PREGUNTAS_DEMO = [
    {
        "texto": "¿Cuál es la capital de Francia?",
        "opcion_a": "Londres",
        "opcion_b": "París",
        "opcion_c": "Berlín",
        "opcion_d": "Madrid",
        "respuesta_correcta": "B"
    },
    {
        "texto": "¿Cuánto es 5 + 3?",
        "opcion_a": "7",
        "opcion_b": "8",
        "opcion_c": "9",
        "opcion_d": "10",
        "respuesta_correcta": "B"
    },
    {
        "texto": "¿En qué año terminó la Segunda Guerra Mundial?",
        "opcion_a": "1943",
        "opcion_b": "1944",
        "opcion_c": "1945",
        "opcion_d": "1946",
        "respuesta_correcta": "C"
    },
    {
        "texto": "¿Cuál es el planeta más grande del sistema solar?",
        "opcion_a": "Saturno",
        "opcion_b": "Neptuno",
        "opcion_c": "Júpiter",
        "opcion_d": "Urano",
        "respuesta_correcta": "C"
    },
    {
        "texto": "¿Quién escribió 'Don Quijote'?",
        "opcion_a": "Lope de Vega",
        "opcion_b": "Miguel de Cervantes",
        "opcion_c": "Garcilaso de la Vega",
        "opcion_d": "Fernando de Rojas",
        "respuesta_correcta": "B"
    },
    {
        "texto": "¿Cuál es la raíz cuadrada de 144?",
        "opcion_a": "10",
        "opcion_b": "11",
        "opcion_c": "12",
        "opcion_d": "13",
        "respuesta_correcta": "C"
    },
    {
        "texto": "¿En qué continente se encuentra Egipto?",
        "opcion_a": "Asia",
        "opcion_b": "Europa",
        "opcion_c": "África",
        "opcion_d": "América",
        "respuesta_correcta": "C"
    },
    {
        "texto": "¿Cuál es la fórmula química del agua?",
        "opcion_a": "CO2",
        "opcion_b": "H2O",
        "opcion_c": "O2",
        "opcion_d": "NH3",
        "respuesta_correcta": "B"
    },
    {
        "texto": "¿Cuántos lados tiene un hexágono?",
        "opcion_a": "4",
        "opcion_b": "5",
        "opcion_c": "6",
        "opcion_d": "7",
        "respuesta_correcta": "C"
    },
    {
        "texto": "¿En qué año se declaró la independencia de Estados Unidos?",
        "opcion_a": "1775",
        "opcion_b": "1776",
        "opcion_c": "1777",
        "opcion_d": "1778",
        "respuesta_correcta": "B"
    }
]

# ============================================
# DECORADOR PARA REQUERIR LOGIN
# ============================================

def login_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# RUTAS PRINCIPALES
# ============================================

@app.route('/')
def index():
    """Página de inicio (sin login)"""
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    
    # Obtener frase diaria
    hoy = datetime.now().date()
    indice = (hoy - datetime(2024, 1, 1).date()).days % len(FRASES_DIARIAS)
    frase = FRASES_DIARIAS[indice]
    
    return render_template('index.html', frase=frase)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de usuarios"""
    if request.method == 'POST':
        data = request.get_json(force=True)
        email = data.get('email')
        nombre_usuario = data.get('nombre_usuario')
        nombre_completo = data.get('nombre_completo', '')
        
        # Validar que no exista el usuario
        if Usuario.query.filter_by(email=email).first():
            return jsonify({'error': 'El email ya está registrado'}), 400
        
        if Usuario.query.filter_by(nombre_usuario=nombre_usuario).first():
            return jsonify({'error': 'El nombre de usuario ya existe'}), 400
        
        # Crear usuario
        nuevo_usuario = Usuario(
            email=email,
            nombre_usuario=nombre_usuario,
            nombre_completo=nombre_completo
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        # Iniciar sesión
        session['usuario_id'] = nuevo_usuario.id
        session['nombre_usuario'] = nuevo_usuario.nombre_usuario
        
        return jsonify({'success': True, 'redirect': url_for('dashboard')}), 201
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión"""
    if request.method == 'POST':
        data = request.get_json(force=True)
        nombre_usuario = data.get('nombre_usuario')
        email = data.get('email')
        
        # Buscar usuario
        usuario = Usuario.query.filter(
            (Usuario.nombre_usuario == nombre_usuario) | (Usuario.email == email)
        ).first()
        
        if usuario:
            # Iniciar sesión
            session['usuario_id'] = usuario.id
            session['nombre_usuario'] = usuario.nombre_usuario
            return jsonify({'success': True, 'redirect': url_for('dashboard')}), 200
        
        return jsonify({'error': 'Usuario o email no encontrado'}), 401
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_requerido
def dashboard():
    """Panel principal del usuario"""
    usuario = Usuario.query.get(session['usuario_id'])
    
    # Obtener frase diaria
    hoy = datetime.now().date()
    indice = (hoy - datetime(2024, 1, 1).date()).days % len(FRASES_DIARIAS)
    frase = FRASES_DIARIAS[indice]
    
    return render_template('dashboard.html', usuario=usuario, frase=frase)


@app.route('/cuestionarios')
@login_requerido
def cuestionarios():
    """Página de cuestionarios"""
    todos_cuestionarios = Cuestionario.query.all()
    return render_template('cuestionarios.html', cuestionarios=todos_cuestionarios)


@app.route('/comunidad')
@login_requerido
def comunidad():
    """Página de comunidad"""
    posts = PostComunidad.query.all()
    return render_template('comunidad.html', posts=posts)


@app.route('/reels')
@login_requerido
def reels():
    """Página de reels educativos"""
    reels_datos = Reel.query.all()
    return render_template('reels.html', reels=reels_datos)


@app.route('/biblioteca')
@login_requerido
def biblioteca():
    """Página de biblioteca"""
    archivos = Biblioteca.query.all()
    return render_template('biblioteca.html', archivos=archivos)


@app.route('/favoritos')
@login_requerido
def favoritos():
    """Página de favoritos"""
    usuario = Usuario.query.get(session['usuario_id'])
    favoritos_usuario = Favorito.query.filter_by(usuario_id=usuario.id).all()
    return render_template('favoritos.html', favoritos=favoritos_usuario)

@app.route('/descargar/<nombre_archivo>')
@login_requerido
def descargar_archivo(nombre_archivo):

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        nombre_archivo,
        as_attachment=True
    )


@app.route('/api/usuario')
@app.route('/api/publicar-post', methods=['POST'])
@login_requerido
def publicar_post():

    data = request.get_json(force=True)

    nuevo_post = PostComunidad(
        usuario_id=session['usuario_id'],
        titulo=data.get('titulo'),
        contenido=data.get('contenido'),
        tipo=data.get('tipo')
    )

    db.session.add(nuevo_post)
    db.session.commit()

    return jsonify({
        'success': True
    })

@app.route('/api/subir-archivo', methods=['POST'])
@login_requerido
def subir_archivo():

    if 'archivo' not in request.files:
        return jsonify({'error': 'No se recibió ningún archivo'}), 400

    archivo = request.files['archivo']

    if archivo.filename == '':
        return jsonify({'error': 'Archivo vacío'}), 400

    nombre_seguro = secure_filename(archivo.filename)

    ruta = os.path.join(app.config['UPLOAD_FOLDER'], nombre_seguro)
    archivo.save(ruta)

    nuevo_archivo = Biblioteca(
        titulo=request.form.get('titulo'),
        descripcion=request.form.get('descripcion'),
        autor=session['nombre_usuario'],
        tipo='PDF',
        url_archivo=nombre_seguro,
        usuario_id=session['usuario_id']
    )

    db.session.add(nuevo_archivo)
    db.session.commit()

    return jsonify({'success': True})

@app.route('/api/agregar-favorito', methods=['POST'])
@login_requerido
def agregar_favorito():

    data = request.get_json(force=True)

    existe = Favorito.query.filter_by(
        usuario_id=session['usuario_id'],
        tipo=data.get('tipo'),
        item_id=data.get('item_id')
    ).first()

    if existe:
        return jsonify({
            'success': False,
            'error': 'Ya está en favoritos'
        })

    nuevo_favorito = Favorito(
        usuario_id=session['usuario_id'],
        tipo=data.get('tipo'),
        item_id=data.get('item_id')
    )

    db.session.add(nuevo_favorito)
    db.session.commit()

    return jsonify({
        'success': True
    })

# ============================================
# CREAR BASE DE DATOS Y DATOS INICIALES
# ============================================

def crear_base_datos():
    """Crear la base de datos y datos iniciales"""
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        
        # Verificar si ya existe el cuestionario de demostración
        quiz_demo = Cuestionario.query.filter_by(titulo='Quiz de Demostración').first()
        
        if not quiz_demo:
            # Crear usuario admin si no existe
            admin = Usuario.query.filter_by(nombre_usuario='admin').first()
            if not admin:
                admin = Usuario(
                    email='admin@nobiru.com',
                    nombre_usuario='admin',
                    nombre_completo='Administrador Nobiru',
                    puntos=1000,
                    insignia='obsidiana',
                    nivel=10
                )
                db.session.add(admin)
                db.session.commit()
            
            # Crear cuestionario de demostración
            quiz_demo = Cuestionario(
                titulo='Quiz de Demostración',
                descripcion='Un cuestionario de ejemplo con 10 preguntas variadas',
                autor_id=admin.id,
                categorias='Variado'
            )
            db.session.add(quiz_demo)
            db.session.commit()
            
            # Agregar preguntas de demostración
            for pregunta_data in PREGUNTAS_DEMO:
                pregunta = Pregunta(
                    cuestionario_id=quiz_demo.id,
                    texto=pregunta_data['texto'],
                    opcion_a=pregunta_data['opcion_a'],
                    opcion_b=pregunta_data['opcion_b'],
                    opcion_c=pregunta_data['opcion_c'],
                    opcion_d=pregunta_data['opcion_d'],
                    respuesta_correcta=pregunta_data['respuesta_correcta']
                )
                db.session.add(pregunta)
            
            db.session.commit()
            print("✅ Base de datos creada con éxito")


# ============================================
# MANEJO DE ERRORES
# ============================================

@app.errorhandler(404)
def pagina_no_encontrada(error):
    """Manejar error 404"""
    return render_template('error.html', mensaje='Página no encontrada'), 404


@app.errorhandler(500)
def error_interno(error):
    """Manejar error 500"""
    return render_template('error.html', mensaje='Error interno del servidor'), 500


# Crear base de datos siempre (también en Render)
crear_base_datos()

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV', 'production') == 'development'
    port = int(os.getenv('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
