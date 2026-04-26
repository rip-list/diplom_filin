# webapp/app.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from database.db import get_session
from database.models import Question
from nlp.search import search_engine
from config import ADMIN_PASSWORD
import pypdf

app = Flask(__name__)
app.secret_key = os.urandom(24)  #Рандомный секрет для сессий 
# Декоратор защиты
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# === Главная страница (список вопросов) ===
@app.route('/')
@login_required
def index():
    session_db = get_session()
    questions = session_db.query(Question).order_by(Question.category, Question.id).all()
    session_db.close()
    return render_template('index.html', questions=questions)

# === Аутентификация ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неверный пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

# === Добавление одного вопроса (старый функционал) ===
@app.route('/add', methods=['POST'])
@login_required
def add_question():
    text = request.form['text']
    answer = request.form['answer']
    category = request.form['category']
    session_db = get_session()
    q = Question(text=text, answer=answer, category=category)
    session_db.add(q)
    session_db.commit()
    session_db.close()
    search_engine.rebuild_index()
    return redirect(url_for('index'))

# === Удаление вопроса ===
@app.route('/delete/<int:question_id>')
@login_required
def delete_question(question_id):
    session_db = get_session()
    q = session_db.query(Question).get(question_id)
    if q:
        session_db.delete(q)
        session_db.commit()
        search_engine.rebuild_index()
    session_db.close()
    return redirect(url_for('index'))

# === Загрузка PDF ===
@app.route('/upload_pdf', methods=['GET', 'POST'])
@login_required
def upload_pdf():
    if request.method == 'POST':
        file = request.files.get('pdf_file')
        if not file or not file.filename.endswith('.pdf'):
            return render_template('upload_pdf.html', error='Выберите корректный PDF-файл')
        try:
            reader = pypdf.PdfReader(file)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        except Exception as e:
            return render_template('upload_pdf.html', error=f'Ошибка чтения PDF: {str(e)}')
        # Передаём текст в шаблон для предпросмотра и редактирования
        return render_template('process_pdf.html', raw_text=full_text)
    return render_template('upload_pdf.html')

# === Обработка отредактированного текста из PDF ===
@app.route('/process_pdf', methods=['POST'])
@login_required
def process_pdf():
    raw_text = request.form.get('edited_text', '')
    # Разбиваем на блоки по двойному переводу строки (пустая строка – разделитель)
    blocks = raw_text.strip().split('\n\n')
    pairs = []
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) >= 2:
            question = lines[0]
            answer = '\n'.join(lines[1:])
            pairs.append((question, answer, 'general'))  # по умолчанию категория general
        # Если одна строка – игнорируем
    # Добавляем в базу
    added = 0
    session_db = get_session()
    for q_text, ans, cat in pairs:
        # Проверяем дубликат
        if not session_db.query(Question).filter(Question.text == q_text).first():
            session_db.add(Question(text=q_text, answer=ans, category=cat))
            added += 1
    session_db.commit()
    session_db.close()
    search_engine.rebuild_index()
    return render_template('upload_result.html', added=added, total=len(pairs))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)