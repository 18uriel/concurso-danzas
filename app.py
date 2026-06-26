# app.py - Versión con PyMySQL
import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_mysqldb import MySQL
from config import Config
import pandas as pd
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)

# ==================== LOGIN ====================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        
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
    
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT COUNT(*) as total FROM participantes")
    total_participantes = cur.fetchone()['total']
    
    cur.execute("SELECT categoria, COUNT(*) as total FROM participantes GROUP BY categoria")
    participantes_por_categoria = cur.fetchall()
    
    cur.execute("SELECT COUNT(*) as total FROM calificaciones")
    total_calificaciones = cur.fetchone()['total']
    
    cur.execute("SELECT AVG(puntaje_total) as promedio FROM calificaciones")
    promedio_general = cur.fetchone()['promedio'] or 0
    
    cur.close()
    
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
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM participantes ORDER BY id DESC")
    participantes = cur.fetchall()
    cur.close()
    
    return render_template('participantes.html', participantes=participantes)

@app.route('/participante/agregar', methods=['POST'])
def agregar_participante():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    nombre_institucion = request.form['nombre_institucion']
    nombre_danza = request.form['nombre_danza']
    categoria = request.form['categoria']
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO participantes (nombre_institucion, nombre_danza, categoria) 
        VALUES (%s, %s, %s)
    """, (nombre_institucion, nombre_danza, categoria))
    mysql.connection.commit()
    cur.close()
    
    flash('Participante registrado exitosamente', 'success')
    return redirect(url_for('participantes'))

@app.route('/participante/editar/<int:id>', methods=['POST'])
def editar_participante(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    nombre_institucion = request.form['nombre_institucion']
    nombre_danza = request.form['nombre_danza']
    categoria = request.form['categoria']
    
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE participantes 
        SET nombre_institucion = %s, nombre_danza = %s, categoria = %s 
        WHERE id = %s
    """, (nombre_institucion, nombre_danza, categoria, id))
    mysql.connection.commit()
    cur.close()
    
    flash('Participante actualizado exitosamente', 'success')
    return redirect(url_for('participantes'))

@app.route('/participante/eliminar/<int:id>')
def eliminar_participante(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM participantes WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    
    flash('Participante eliminado exitosamente', 'success')
    return redirect(url_for('participantes'))

# ==================== CALIFICACIONES ====================
@app.route('/calificaciones')
def calificaciones():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT p.*, c.id as calificacion_id, c.jurado1, c.jurado2, c.jurado3, c.puntaje_total 
        FROM participantes p
        LEFT JOIN calificaciones c ON p.id = c.participante_id
        ORDER BY p.categoria, p.nombre_institucion
    """)
    participantes = cur.fetchall()
    cur.close()
    
    return render_template('calificaciones.html', participantes=participantes)

@app.route('/calificacion/guardar/<int:participante_id>', methods=['POST'])
def guardar_calificacion(participante_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    jurado1 = float(request.form['jurado1'])
    jurado2 = float(request.form['jurado2'])
    jurado3 = float(request.form['jurado3'])
    
    # Calcular el promedio
    puntaje_total = (jurado1 + jurado2 + jurado3) / 3
    
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT id FROM calificaciones WHERE participante_id = %s", (participante_id,))
    existe = cur.fetchone()
    
    if existe:
        cur.execute("""
            UPDATE calificaciones 
            SET jurado1 = %s, jurado2 = %s, jurado3 = %s, puntaje_total = %s
            WHERE participante_id = %s
        """, (jurado1, jurado2, jurado3, puntaje_total, participante_id))
    else:
        cur.execute("""
            INSERT INTO calificaciones (participante_id, jurado1, jurado2, jurado3, puntaje_total) 
            VALUES (%s, %s, %s, %s, %s)
        """, (participante_id, jurado1, jurado2, jurado3, puntaje_total))
    
    mysql.connection.commit()
    cur.close()
    
    flash('Calificación guardada exitosamente', 'success')
    return redirect(url_for('calificaciones'))

# ==================== RESULTADOS ADMIN ====================
@app.route('/resultados')
def resultados():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    
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
                RANK() OVER (ORDER BY c.puntaje_total DESC) as posicion
            FROM participantes p
            INNER JOIN calificaciones c ON p.id = c.participante_id
            WHERE p.categoria = %s
            ORDER BY c.puntaje_total DESC
        """, (categoria,))
        resultados[categoria] = cur.fetchall()
    
    cur.close()
    return render_template('resultados.html', resultados=resultados)

# ==================== RESULTADOS PUBLICOS ====================
@app.route('/resultados/publicos')
def resultados_publicos():
    cur = mysql.connection.cursor()
    
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
                RANK() OVER (ORDER BY c.puntaje_total DESC) as posicion
            FROM participantes p
            INNER JOIN calificaciones c ON p.id = c.participante_id
            WHERE p.categoria = %s
            ORDER BY c.puntaje_total DESC
        """, (categoria,))
        resultados[categoria] = cur.fetchall()
    
    cur.close()
    
    now = datetime.now()
    
    # ==========================================
    # 🖼️ CONFIGURACIÓN DE IMÁGENES
    # ==========================================
    
    # === FONDO DE PANTALLA ===
    # Opción 1: Imagen local (coloca tu imagen en static/images/)
    fondo_url = '/static/images/fondo_bicentenario.jpg'
    
    # Opción 2: URL externa (descomenta y usa esta)
    # fondo_url = 'https://ejemplo.com/mi-fondo.jpg'
    
    # Opción 3: Sin fondo (solo color)
    # fondo_url = ''
    
    # === LOGO IZQUIERDA ===
    # Opción 1: Imagen local
    logo_izquierda = '/static/images/logo_municipalidad.png'
    
    # Opción 2: URL externa
    # logo_izquierda = 'https://ejemplo.com/logo-izquierda.png'
    
    # Opción 3: Sin logo
    # logo_izquierda = ''
    
    # === LOGO DERECHA ===
    # Opción 1: Imagen local
    logo_derecha = '/static/images/logo_bicentenario.png'
    
    # Opción 2: URL externa
    # logo_derecha = 'https://ejemplo.com/logo-derecha.png'
    
    # Opción 3: Sin logo
    # logo_derecha = ''
    
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
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            p.categoria,
            p.nombre_institucion,
            p.nombre_danza,
            c.jurado1,
            c.jurado2,
            c.jurado3,
            c.puntaje_total,
            RANK() OVER (PARTITION BY p.categoria ORDER BY c.puntaje_total DESC) as posicion
        FROM participantes p
        INNER JOIN calificaciones c ON p.id = c.participante_id
        ORDER BY p.categoria, c.puntaje_total DESC
    """)
    reporte_data = cur.fetchall()
    cur.close()
    
    return render_template('reporte.html', reporte=reporte_data)

# ==================== EXPORTAR EXCEL ====================
@app.route('/exportar/excel')
def exportar_excel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            p.categoria as 'Categoría',
            p.nombre_institucion as 'Institución',
            p.nombre_danza as 'Danza',
            c.jurado1 as 'Jurado 1',
            c.jurado2 as 'Jurado 2',
            c.jurado3 as 'Jurado 3',
            c.puntaje_total as 'Promedio',
            RANK() OVER (PARTITION BY p.categoria ORDER BY c.puntaje_total DESC) as 'Posición'
        FROM participantes p
        INNER JOIN calificaciones c ON p.id = c.participante_id
        ORDER BY p.categoria, c.puntaje_total DESC
    """)
    data = cur.fetchall()
    cur.close()
    
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
    app.run(debug=True)