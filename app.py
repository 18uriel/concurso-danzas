# app.py - Versión pura para PostgreSQL (sin flask_mysqldb)
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import pandas as pd
from io import BytesIO
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-development')

# Configuración de la base de datos desde variables de entorno
DB_HOST = os.environ.get('MYSQL_HOST', 'localhost')
DB_PORT = os.environ.get('MYSQL_PORT', '5432')
DB_USER = os.environ.get('MYSQL_USER', 'postgres')
DB_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
DB_NAME = os.environ.get('MYSQL_DB', 'concurso_danzas')

def get_db_connection():
    """Conecta a la base de datos PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursor_factory=RealDictCursor,
            connect_timeout=10
        )
        return conn
    except Exception as e:
        print(f"Error de conexión a la base de datos: {e}")
        return None

# ==================== LOGIN ====================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn is None:
            flash('Error de conexión a la base de datos', 'danger')
            return render_template('login.html')
            
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['username'] = username
            flash('Login exitoso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

# ==================== DASHBOARD ====================
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('login'))
        
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) as total FROM participantes")
    total_participantes = cur.fetchone()['total']
    
    cur.execute("SELECT categoria, COUNT(*) as total FROM participantes GROUP BY categoria")
    participantes_por_categoria = cur.fetchall()
    
    cur.execute("SELECT COUNT(*) as total FROM calificaciones")
    total_calificaciones = cur.fetchone()['total']
    
    cur.execute("SELECT COALESCE(AVG(puntaje_total), 0) as promedio FROM calificaciones")
    promedio_general = cur.fetchone()['promedio']
    
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', 
                         total_participantes=total_participantes,
                         participantes_por_categoria=participantes_por_categoria,
                         total_calificaciones=total_calificaciones,
                         promedio_general=round(promedio_general, 2))

# ==================== PARTICIPANTES ====================
@app.route('/participantes')
def participantes():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('login'))
        
    cur = conn.cursor()
    cur.execute("SELECT * FROM participantes ORDER BY id DESC")
    participantes = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('participantes.html', participantes=participantes)

@app.route('/participante/agregar', methods=['POST'])
def agregar_participante():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    nombre_institucion = request.form['nombre_institucion']
    nombre_danza = request.form['nombre_danza']
    categoria = request.form['categoria']
    
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('participantes'))
        
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO participantes (nombre_institucion, nombre_danza, categoria) 
        VALUES (%s, %s, %s)
    """, (nombre_institucion, nombre_danza, categoria))
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Participante registrado exitosamente', 'success')
    return redirect(url_for('participantes'))

@app.route('/participante/editar/<int:id>', methods=['POST'])
def editar_participante(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    nombre_institucion = request.form['nombre_institucion']
    nombre_danza = request.form['nombre_danza']
    categoria = request.form['categoria']
    
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('participantes'))
        
    cur = conn.cursor()
    cur.execute("""
        UPDATE participantes 
        SET nombre_institucion = %s, nombre_danza = %s, categoria = %s 
        WHERE id = %s
    """, (nombre_institucion, nombre_danza, categoria, id))
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Participante actualizado exitosamente', 'success')
    return redirect(url_for('participantes'))

@app.route('/participante/eliminar/<int:id>')
def eliminar_participante(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('participantes'))
        
    cur = conn.cursor()
    cur.execute("DELETE FROM participantes WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Participante eliminado exitosamente', 'success')
    return redirect(url_for('participantes'))

# ==================== CALIFICACIONES ====================
@app.route('/calificaciones')
def calificaciones():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('login'))
        
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*, c.id as calificacion_id, c.jurado1, c.jurado2, c.jurado3, c.puntaje_total 
        FROM participantes p
        LEFT JOIN calificaciones c ON p.id = c.participante_id
        ORDER BY p.categoria, p.nombre_institucion
    """)
    participantes = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('calificaciones.html', participantes=participantes)

@app.route('/calificacion/guardar/<int:participante_id>', methods=['POST'])
def guardar_calificacion(participante_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    jurado1 = float(request.form['jurado1'])
    jurado2 = float(request.form['jurado2'])
    jurado3 = float(request.form['jurado3'])
    
    # ✅ NO calcular puntaje_total, PostgreSQL lo hará automáticamente
    
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('calificaciones'))
        
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM calificaciones WHERE participante_id = %s", (participante_id,))
    existe = cur.fetchone()
    
    if existe:
        # ✅ SIN puntaje_total en UPDATE
        cur.execute("""
            UPDATE calificaciones 
            SET jurado1 = %s, jurado2 = %s, jurado3 = %s
            WHERE participante_id = %s
        """, (jurado1, jurado2, jurado3, participante_id))
    else:
        # ✅ SIN puntaje_total en INSERT
        cur.execute("""
            INSERT INTO calificaciones (participante_id, jurado1, jurado2, jurado3) 
            VALUES (%s, %s, %s, %s)
        """, (participante_id, jurado1, jurado2, jurado3))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Calificación guardada exitosamente', 'success')
    return redirect(url_for('calificaciones'))

# ==================== RESULTADOS ADMIN ====================
@app.route('/resultados')
def resultados():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('login'))
        
    cur = conn.cursor()
    
    resultados = {}
    for categoria in ['A', 'B']:
        cur.execute("""
            SELECT 
                p.id,
                p.nombre_institucion,
                p.nombre_danza,
                c.jurado1,
                c.jurado2,
                c.jurado3,
                c.puntaje_total,
                ROW_NUMBER() OVER (ORDER BY c.puntaje_total DESC) as posicion
            FROM participantes p
            INNER JOIN calificaciones c ON p.id = c.participante_id
            WHERE p.categoria = %s
            ORDER BY c.puntaje_total DESC
        """, (categoria,))
        resultados[categoria] = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('resultados.html', resultados=resultados)

# ==================== RESULTADOS PUBLICOS ====================
@app.route('/resultados/publicos')
def resultados_publicos():
    conn = get_db_connection()
    if conn is None:
        return "Error de conexión a la base de datos", 500
        
    cur = conn.cursor()
    
    resultados = {}
    for categoria in ['A', 'B']:
        cur.execute("""
            SELECT 
                p.id,
                p.nombre_institucion,
                p.nombre_danza,
                c.jurado1,
                c.jurado2,
                c.jurado3,
                c.puntaje_total,
                ROW_NUMBER() OVER (ORDER BY c.puntaje_total DESC) as posicion
            FROM participantes p
            INNER JOIN calificaciones c ON p.id = c.participante_id
            WHERE p.categoria = %s
            ORDER BY c.puntaje_total DESC
        """, (categoria,))
        resultados[categoria] = cur.fetchall()
    
    cur.close()
    conn.close()
    
    now = datetime.now()
    
    fondo_url = '/static/images/fondo_bicentenario.jpg'
    logo_izquierda = '/static/images/logo_municipalidad.png'
    logo_derecha = '/static/images/logo_bicentenario.png'
    
    return render_template('resultados_publicos.html', 
                         resultados=resultados, 
                         now=now,
                         fondo_url=fondo_url,
                         logo_izquierda=logo_izquierda,
                         logo_derecha=logo_derecha)

# ==================== REPORTE ====================
@app.route('/reporte')
def reporte():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('login'))
        
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            p.categoria,
            p.nombre_institucion,
            p.nombre_danza,
            c.jurado1,
            c.jurado2,
            c.jurado3,
            c.puntaje_total,
            ROW_NUMBER() OVER (PARTITION BY p.categoria ORDER BY c.puntaje_total DESC) as posicion
        FROM participantes p
        INNER JOIN calificaciones c ON p.id = c.participante_id
        ORDER BY p.categoria, c.puntaje_total DESC
    """)
    reporte_data = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('reporte.html', reporte=reporte_data)

# ==================== EXPORTAR EXCEL ====================
@app.route('/exportar/excel')
def exportar_excel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn is None:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('dashboard'))
        
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            p.categoria as "Categoría",
            p.nombre_institucion as "Institución",
            p.nombre_danza as "Danza",
            c.jurado1 as "Jurado 1",
            c.jurado2 as "Jurado 2",
            c.jurado3 as "Jurado 3",
            c.puntaje_total as "Promedio",
            ROW_NUMBER() OVER (PARTITION BY p.categoria ORDER BY c.puntaje_total DESC) as "Posición"
        FROM participantes p
        INNER JOIN calificaciones c ON p.id = c.participante_id
        ORDER BY p.categoria, c.puntaje_total DESC
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resultados', index=False)
        
        worksheet = writer.sheets['Resultados']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'resultados_concurso_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

# ==================== LOGOUT ====================
@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)