from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import random
import string
import os
import json

# ==================== CONFIGURACIÓN ====================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu-clave-secreta-super-segura-123'

# CONFIGURACIÓN MYSQL
MYSQL_USER = 'root'
MYSQL_PASSWORD = '080808'
MYSQL_HOST = 'localhost'
MYSQL_PORT = '3306'
MYSQL_DATABASE = 'recursos_aprendizaje'

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CONFIGURACIÓN EMAIL (Gmail) 
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tucorreo@gmail.com'  
app.config['MAIL_PASSWORD'] = 'tu_contraseña_app'   
app.config['MAIL_DEFAULT_SENDER'] = 'tucorreo@gmail.com'

# CONFIGURACIÓN DE UPLOADS
UPLOAD_FOLDER = 'static/uploads/avisos'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Crear carpeta si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
mail = Mail(app)

# ==================== MODELOS ====================

class Alumno(db.Model):
    __tablename__ = 'alumnos'
    
    NumeroControl = db.Column(db.String(20), primary_key=True)
    Curp = db.Column(db.String(18), unique=True, nullable=False)
    Nombre = db.Column(db.String(100), nullable=False)
    Paterno = db.Column(db.String(100), nullable=False)
    Materno = db.Column(db.String(100), nullable=False)
    Turno = db.Column(db.String(20), nullable=False)
    Grupo = db.Column(db.String(10), nullable=False)
    Semestre = db.Column(db.Integer, nullable=False)
    CorreoInstitucional = db.Column(db.String(120), unique=True)
    FechaRegistro = db.Column(db.DateTime, default=datetime.utcnow)
    Activo = db.Column(db.Boolean, default=True)

class Empleado(db.Model):
    __tablename__ = 'empleados'
    
    NumeroEmpleado = db.Column(db.String(20), primary_key=True)
    Nombre = db.Column(db.String(100), nullable=False)
    Paterno = db.Column(db.String(100), nullable=False)
    Materno = db.Column(db.String(100), nullable=False)
    Usuario = db.Column(db.String(50), unique=True, nullable=False)
    Rol = db.Column(db.String(20), nullable=False)
    Materias = db.Column(db.Text, nullable=True)
    GrupoAsignado = db.Column(db.Integer, nullable=True)
    FechaRegistro = db.Column(db.DateTime, default=datetime.utcnow)
    Activo = db.Column(db.Boolean, default=True)

class IntentoLogin(db.Model):
    __tablename__ = 'intentos_login'
    
    id = db.Column(db.Integer, primary_key=True)
    identificador = db.Column(db.String(120), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False)
    intentos_fallidos = db.Column(db.Integer, default=0)
    bloqueado_hasta = db.Column(db.DateTime, nullable=True)
    ultimo_intento = db.Column(db.DateTime, default=datetime.utcnow)

class CodigoVerificacion(db.Model):
    __tablename__ = 'codigos_verificacion'
    
    id = db.Column(db.Integer, primary_key=True)
    correo = db.Column(db.String(120), nullable=False)
    codigo = db.Column(db.String(6), nullable=False)
    expira = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, default=False)
    creado = db.Column(db.DateTime, default=datetime.utcnow)

class Aviso(db.Model):
    __tablename__ = 'avisos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_profesor = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    archivos = db.Column(db.Text, nullable=True)  # JSON con nombres de archivos
    fecha_publicacion = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)

# ==================== FUNCIONES DE SEGURIDAD ====================

def generar_codigo():
    return ''.join(random.choices(string.digits, k=6))

def enviar_codigo_email(correo, codigo):
    try:
        msg = Message('Código de Verificación - Recursos de Aprendizaje', recipients=[correo])
        msg.body = f"""
Hola,

Tu código de verificación es: {codigo}

Este código expirará en 10 minutos.

Si no solicitaste este código, ignora este mensaje.

Saludos,
Plataforma de Recursos de Aprendizaje
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f"❌ Error al enviar email: {e}")
        return False

def verificar_bloqueo(identificador, tipo):
    intento = IntentoLogin.query.filter_by(identificador=identificador, tipo_usuario=tipo).first()
    
    if not intento:
        return False, 0, None
    
    if intento.bloqueado_hasta:
        if datetime.utcnow() < intento.bloqueado_hasta:
            tiempo_restante = intento.bloqueado_hasta - datetime.utcnow()
            return True, intento.intentos_fallidos, tiempo_restante
        else:
            db.session.delete(intento)
            db.session.commit()
            return False, 0, None
    
    return False, intento.intentos_fallidos, None

def registrar_intento_fallido(identificador, tipo):
    intento = IntentoLogin.query.filter_by(identificador=identificador, tipo_usuario=tipo).first()
    
    if not intento:
        intento = IntentoLogin(identificador=identificador, tipo_usuario=tipo, intentos_fallidos=1)
        db.session.add(intento)
    else:
        intento.intentos_fallidos += 1
        intento.ultimo_intento = datetime.utcnow()
        
        if intento.intentos_fallidos == 7:
            intento.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=5)
        elif intento.intentos_fallidos >= 9:
            intento.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=5)
    
    db.session.commit()
    return intento.intentos_fallidos

def limpiar_intentos(identificador, tipo):
    intento = IntentoLogin.query.filter_by(identificador=identificador, tipo_usuario=tipo).first()
    if intento:
        db.session.delete(intento)
        db.session.commit()

def limpiar_bloqueos_expirados():
    try:
        ahora = datetime.utcnow()
        registros_eliminados = IntentoLogin.query.filter(IntentoLogin.bloqueado_hasta < ahora).delete()
        db.session.commit()
        if registros_eliminados > 0:
            print(f"🧹 Limpiados {registros_eliminados} bloqueos expirados")
    except Exception as e:
        print(f"⚠️ Error al limpiar bloqueos: {e}")
        db.session.rollback()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== INICIALIZACIÓN ====================

with app.app_context():
    try:
        db.create_all()
        limpiar_bloqueos_expirados()
        print("✅ Conexión a MySQL exitosa")
        print(f"✅ Base de datos: {MYSQL_DATABASE}")
        
        total_alumnos = Alumno.query.count()
        total_empleados = Empleado.query.count()
        total_avisos = Aviso.query.count()
        print(f"📊 Total alumnos: {total_alumnos}")
        print(f"📊 Total empleados: {total_empleados}")
        print(f"📢 Total avisos: {total_avisos}")
    except Exception as e:
        print(f"❌ Error al conectar con MySQL: {e}")

# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('Login.html')

@app.route('/inicio')
def inicio():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    if session.get('user_type') == 'alumno':
        return render_template('inicio.html')
    elif session.get('user_type') == 'empleado':
        return redirect(url_for('inicio_docente'))
    
    return render_template('inicio.html')

@app.route('/inicio-docente')
def inicio_docente():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    if session.get('user_type') != 'empleado':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('inicio'))
    
    return render_template('inicio_docente.html')

# ==================== API ESTADO BLOQUEO ====================

@app.route('/api/verificar-bloqueo', methods=['POST'])
def api_verificar_bloqueo():
    data = request.get_json()
    identificador = data.get('identificador')
    tipo = data.get('tipo')
    
    bloqueado, intentos, tiempo_restante = verificar_bloqueo(identificador, tipo)
    
    if bloqueado:
        segundos = int(tiempo_restante.total_seconds())
        return jsonify({'bloqueado': True, 'intentos': intentos, 'segundos_restantes': segundos})
    
    return jsonify({'bloqueado': False, 'intentos': intentos})

# ==================== AUTENTICACIÓN CON SEGURIDAD ====================

@app.route('/login/alumno', methods=['POST'])
def login_alumno():
    correo = request.form.get('email')
    numero_control = request.form.get('numerocontrol')
    
    bloqueado, intentos, tiempo_restante = verificar_bloqueo(correo, 'alumno')
    
    if bloqueado:
        minutos = int(tiempo_restante.total_seconds() / 60)
        segundos = int(tiempo_restante.total_seconds() % 60)
        flash(f'⏱️ Cuenta bloqueada. Intenta en {minutos}m {segundos}s', 'error')
        return redirect(url_for('login'))
    
    if intentos >= 9:
        session['verificacion_correo'] = correo
        session['verificacion_tipo'] = 'alumno'
        flash('🔒 Límite de intentos alcanzado. Debes verificar tu identidad por email.', 'warning')
        return redirect(url_for('verificacion_email'))
    
    try:
        alumno = Alumno.query.filter_by(CorreoInstitucional=correo, NumeroControl=numero_control, Activo=True).first()
        
        if alumno:
            limpiar_intentos(correo, 'alumno')
            session['user_id'] = alumno.NumeroControl
            session['user_type'] = 'alumno'
            session['user_name'] = f"{alumno.Nombre} {alumno.Paterno}"
            session['grupo'] = alumno.Grupo
            session['semestre'] = alumno.Semestre
            flash('¡Bienvenido!', 'success')
            return redirect(url_for('inicio'))
        else:
            intentos_actuales = registrar_intento_fallido(correo, 'alumno')
            
            if intentos_actuales == 7:
                flash('⚠️ 7 intentos fallidos. Cuenta bloqueada por 5 minutos. Te quedan 2 intentos más.', 'error')
            elif intentos_actuales == 8:
                flash('⚠️ Credenciales incorrectas. Te queda 1 intento antes de verificación por email.', 'error')
            elif intentos_actuales >= 9:
                flash('🚫 Último intento fallido. Debes verificar tu identidad por email.', 'error')
            else:
                intentos_restantes = 7 - intentos_actuales
                flash(f'❌ Credenciales incorrectas. Te quedan {intentos_restantes} intentos.', 'error')
            
            return redirect(url_for('login'))
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/login/empleado', methods=['POST'])
def login_empleado():
    usuario = request.form.get('usuario')
    numero_empleado = request.form.get('numeroempleado')
    
    bloqueado, intentos, tiempo_restante = verificar_bloqueo(usuario, 'empleado')
    
    if bloqueado:
        minutos = int(tiempo_restante.total_seconds() / 60)
        segundos = int(tiempo_restante.total_seconds() % 60)
        flash(f'⏱️ Cuenta bloqueada. Intenta en {minutos}m {segundos}s', 'error')
        return redirect(url_for('login'))
    
    if intentos >= 9:
        session['verificacion_correo'] = usuario
        session['verificacion_tipo'] = 'empleado'
        flash('🔒 Límite de intentos alcanzado. Debes verificar tu identidad por email.', 'warning')
        return redirect(url_for('verificacion_email'))
    
    try:
        empleado = Empleado.query.filter_by(Usuario=usuario, NumeroEmpleado=numero_empleado, Activo=True).first()
        
        if empleado:
            limpiar_intentos(usuario, 'empleado')
            session['user_id'] = empleado.NumeroEmpleado
            session['user_type'] = 'empleado'
            session['user_name'] = f"{empleado.Nombre} {empleado.Paterno}"
            session['rol_empleado'] = empleado.Rol
            flash('¡Bienvenido!', 'success')
            return redirect(url_for('inicio_docente'))
        else:
            intentos_actuales = registrar_intento_fallido(usuario, 'empleado')
            
            if intentos_actuales == 7:
                flash('⚠️ 7 intentos fallidos. Cuenta bloqueada por 5 minutos. Te quedan 2 intentos más.', 'error')
            elif intentos_actuales == 8:
                flash('⚠️ Credenciales incorrectas. Te queda 1 intento antes de verificación por email.', 'error')
            elif intentos_actuales >= 9:
                flash('🚫 Último intento fallido. Debes verificar tu identidad por email.', 'error')
            else:
                intentos_restantes = 7 - intentos_actuales
                flash(f'❌ Credenciales incorrectas. Te quedan {intentos_restantes} intentos.', 'error')
            
            return redirect(url_for('login'))
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('login'))

# ==================== VERIFICACIÓN POR EMAIL ====================

@app.route('/verificacion-email')
def verificacion_email():
    if 'verificacion_correo' not in session:
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    return render_template('verificacion_email.html')

@app.route('/enviar-codigo', methods=['POST'])
def enviar_codigo():
    if 'verificacion_correo' not in session:
        return jsonify({'success': False, 'message': 'Sesión inválida'})
    
    identificador = session['verificacion_correo']
    tipo = session['verificacion_tipo']
    
    email_destino = None
    if tipo == 'alumno':
        alumno = Alumno.query.filter_by(CorreoInstitucional=identificador).first()
        if alumno:
            email_destino = alumno.CorreoInstitucional
    else:
        email_destino = f"{identificador}@institucion.edu.mx"
    
    if not email_destino:
        return jsonify({'success': False, 'message': 'No se encontró el correo'})
    
    codigo = generar_codigo()
    expira = datetime.utcnow() + timedelta(minutes=10)
    
    nuevo_codigo = CodigoVerificacion(correo=identificador, codigo=codigo, expira=expira)
    db.session.add(nuevo_codigo)
    db.session.commit()
    
    if enviar_codigo_email(email_destino, codigo):
        return jsonify({'success': True, 'message': f'Código enviado a {email_destino}'})
    else:
        return jsonify({'success': False, 'message': 'Error al enviar el email.'})

@app.route('/verificar-codigo', methods=['POST'])
def verificar_codigo():
    if 'verificacion_correo' not in session:
        return jsonify({'success': False, 'message': 'Sesión inválida'})
    
    codigo_ingresado = request.form.get('codigo')
    identificador = session['verificacion_correo']
    tipo = session['verificacion_tipo']
    
    codigo_db = CodigoVerificacion.query.filter_by(correo=identificador, codigo=codigo_ingresado, usado=False).first()
    
    if not codigo_db:
        return jsonify({'success': False, 'message': 'Código incorrecto'})
    
    if datetime.utcnow() > codigo_db.expira:
        return jsonify({'success': False, 'message': 'Código expirado. Solicita uno nuevo.'})
    
    codigo_db.usado = True
    db.session.commit()
    
    limpiar_intentos(identificador, tipo)
    
    session.pop('verificacion_correo', None)
    session.pop('verificacion_tipo', None)
    
    flash('✅ Verificación exitosa. Puedes iniciar sesión nuevamente.', 'success')
    return jsonify({'success': True, 'redirect': url_for('login')})

# ==================== REGISTRO ====================

@app.route('/registro/alumno', methods=['GET', 'POST'])
def registro_alumno():
    if request.method == 'POST':
        try:
            nuevo_alumno = Alumno(
                NumeroControl=request.form.get('control'),
                Curp=request.form.get('curp'),
                Nombre=request.form.get('nombre'),
                Paterno=request.form.get('apellidoP'),
                Materno=request.form.get('apellidoM'),
                Turno=request.form.get('turno', 'Matutino'),
                Grupo=request.form.get('grupo'),
                Semestre=int(request.form.get('semestre', 1)),
                CorreoInstitucional=request.form.get('correo')
            )
            
            db.session.add(nuevo_alumno)
            db.session.commit()
            flash('¡Registro exitoso! Ya puedes iniciar sesión', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}', 'error')
    
    return render_template('Registro_Alumnos.html')

@app.route('/registro/empleado', methods=['GET', 'POST'])
def registro_empleado():
    if request.method == 'POST':
        try:
            numero_empleado = request.form.get('control')
            rol = request.form.get('rol')
            
            materias = None
            grupo_asignado = None
            
            if rol == 'docente':
                materias_list = request.form.getlist('materias[]')
                materias_list = [m.strip() for m in materias_list if m.strip()]
                materias = ', '.join(materias_list) if materias_list else None
            elif rol == 'orientador':
                grupo_asignado = request.form.get('grupo')
                if grupo_asignado:
                    grupo_asignado = int(grupo_asignado)
            
            nuevo_empleado = Empleado(
                NumeroEmpleado=numero_empleado,
                Nombre=request.form.get('nombre'),
                Paterno=request.form.get('apellidoP'),
                Materno=request.form.get('apellidoM'),
                Usuario=request.form.get('usuario'),
                Rol=rol,
                Materias=materias,
                GrupoAsignado=grupo_asignado
            )
            
            db.session.add(nuevo_empleado)
            db.session.commit()
            flash('¡Registro exitoso! Ya puedes iniciar sesión', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}', 'error')
    
    return render_template('Registro_Trabajadores.html')

# ==================== SISTEMA DE AVISOS ====================

@app.route('/agregar-aviso-form')
def agregar_aviso_form():
    if 'user_id' not in session or session.get('user_type') != 'empleado':
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('login'))
    return render_template('agregar_aviso.html')

@app.route('/agregar-aviso', methods=['POST'])
def agregar_aviso():
    if 'user_id' not in session or session.get('user_type') != 'empleado':
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 403
    
    try:
        nombre_profesor = session.get('user_name')
        descripcion = request.form.get('descripcion')
        
        if not descripcion:
            return jsonify({'success': False, 'message': 'La descripción es obligatoria'}), 400
        
        # Procesar archivos
        archivos_guardados = []
        if 'archivos[]' in request.files:
            files = request.files.getlist('archivos[]')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    archivos_guardados.append(filename)
        
        # Guardar en base de datos
        nuevo_aviso = Aviso(
            nombre_profesor=nombre_profesor,
            descripcion=descripcion,
            archivos=json.dumps(archivos_guardados) if archivos_guardados else None
        )
        
        db.session.add(nuevo_aviso)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Aviso publicado exitosamente'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/ver-avisos')
def ver_avisos():
    if 'user_id' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    # Obtener todos los avisos activos ordenados por fecha
    avisos = Aviso.query.filter_by(activo=True).order_by(Aviso.fecha_publicacion.desc()).all()
    
    # Procesar archivos JSON a lista
    for aviso in avisos:
        if aviso.archivos:
            aviso.archivos_list = json.loads(aviso.archivos)
        else:
            aviso.archivos_list = []
    
    return render_template('ver_avisos.html', avisos=avisos)

# ==================== GRUPOS ====================

@app.route('/grupos')
def grupos():
    return render_template('Desicion_Alumnos.html')

@app.route('/grupo/101')
def grupo_101():
    return render_template('101.html')

@app.route('/grupo/102')
def grupo_102():
    return render_template('102.html')

@app.route('/grupo/103')
def grupo_103():
    return render_template('103.html')

@app.route('/grupo/104')
def grupo_104():
    return render_template('104.html')

@app.route('/grupo/301')
def grupo_301():
    return render_template('301.html')

@app.route('/grupo/302')
def grupo_302():
    return render_template('302.html')

@app.route('/grupo/303')
def grupo_303():
    return render_template('303.html')

@app.route('/grupo/304')
def grupo_304():
    return render_template('304.html')

@app.route('/grupo/501')
def grupo_501():
    return render_template('501.html')

@app.route('/grupo/502')
def grupo_502():
    return render_template('502.html')

@app.route('/grupo/503')
def grupo_503():
    return render_template('503.html')

@app.route('/grupo/504')
def grupo_504():
    return render_template('504.html')

# ==================== PERSONAL ====================

@app.route('/docentes')
def docentes():
    return render_template('Docentes.html')

@app.route('/directivos')
def directivos():
    return render_template('Directivos.html')

@app.route('/directivo/amalia')
def directivo_amalia():
    return render_template('Directiva-amalia.html')

@app.route('/directivo/karla')
def directivo_karla():
    return render_template('Directiva-karla.html')

@app.route('/directivo/violeta')
def directivo_violeta():
    return render_template('Directiva-violeta.html')

@app.route('/orientadores')
def orientadores():
    return render_template('Orientadores.html')

@app.route('/orientador/guadalupe')
def orientador_guadalupe():
    return render_template('orientador-guadalupe.html')

@app.route('/orientador/mayra')
def orientador_mayra():
    return render_template('orientador-mayra.html')

@app.route('/orientador/rubi')
def orientador_rubi():
    return render_template('orientador-rubi.html')

# ==================== OTRAS SECCIONES ====================

@app.route('/avisos')
def avisos():
    return render_template('ver_avisos.html')

@app.route('/materias')
def materias():
    return render_template('Materias.html')

@app.route('/ayuda')
def ayuda():
    return render_template('Ayuda.html')

# ==================== API BÚSQUEDA ====================

@app.route('/api/buscar-empleados')
def buscar_empleados():
    termino = request.args.get('q', '').lower()
    if not termino:
        return jsonify({'empleados': []})
    
    empleados_encontrados = Empleado.query.filter(
        db.or_(
            Empleado.Nombre.ilike(f'%{termino}%'),
            Empleado.Paterno.ilike(f'%{termino}%'),
            Empleado.Materno.ilike(f'%{termino}%'),
            Empleado.NumeroEmpleado.ilike(f'%{termino}%'),
            Empleado.Usuario.ilike(f'%{termino}%'),
            Empleado.Rol.ilike(f'%{termino}%'),
            Empleado.Materias.ilike(f'%{termino}%')
        ),
        Empleado.Activo == True
    ).all()
    
    resultados = []
    for emp in empleados_encontrados:
        resultado = {
            'nombre': f"{emp.Nombre} {emp.Paterno} {emp.Materno}",
            'numeroEmpleado': emp.NumeroEmpleado,
            'rol': emp.Rol,
            'usuario': emp.Usuario
        }
        if emp.Rol == 'docente' and emp.Materias:
            resultado['materias'] = emp.Materias
        elif emp.Rol == 'orientador' and emp.GrupoAsignado:
            resultado['grupo'] = emp.GrupoAsignado
        resultados.append(resultado)
    
    return jsonify({'empleados': resultados})

@app.route('/api/buscar-alumnos')
def buscar_alumnos():
    termino = request.args.get('q', '').lower()
    if not termino:
        return jsonify({'alumnos': []})
    
    alumnos_encontrados = Alumno.query.filter(
        db.or_(
            Alumno.Nombre.ilike(f'%{termino}%'),
            Alumno.Paterno.ilike(f'%{termino}%'),
            Alumno.Materno.ilike(f'%{termino}%'),
            Alumno.NumeroControl.ilike(f'%{termino}%'),
            Alumno.Grupo.ilike(f'%{termino}%')
        ),
        Alumno.Activo == True
    ).all()
    
    resultados = []
    for alumno in alumnos_encontrados:
        resultados.append({
            'nombre': f"{alumno.Nombre} {alumno.Paterno} {alumno.Materno}",
            'matricula': alumno.NumeroControl,
            'grupo': alumno.Grupo,
            'semestre': alumno.Semestre
        })
    
    return jsonify({'alumnos': resultados})

# ==================== UTILIDADES ====================

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('login'))

@app.errorhandler(404)
def no_encontrado(error):
    return "<h1>404 - Página no encontrada</h1>", 404

if __name__ == '__main__':
    print("🚀 Servidor Flask iniciado con SISTEMA DE AVISOS")
    print("📍 http://127.0.0.1:5000")
    print("📍 http://localhost:5000")
    print("🔐 Seguridad: 7 intentos + bloqueo 5 min + verificación email")
    print("👥 Roles: Docente, Orientador, Directivo")
    print("✅ Inicio Docentes: /inicio-docente")
    print("✅ Inicio Alumnos: /inicio")
    print("📢 Agregar Avisos (Docentes): /agregar-aviso-form")
    print("📬 Ver Avisos (Alumnos): /ver-avisos")
    app.run(debug=True, host='127.0.0.1', port=5000)