import os
import sqlite3
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configurazione delle chiavi di sicurezza da ambiente
SECRET_KEY = os.environ.get("key")
FERNET_KEY = os.environ.get("bi-key")

# Blocco dell'applicazione in avvio se mancano le chiavi critiche
if not SECRET_KEY or not FERNET_KEY:
    raise ValueError("ERRORE CRITICO DI SICUREZZA: Manca 'key' o 'bi-key' nel file .env!")

app.secret_key = SECRET_KEY
fernet = Fernet(FERNET_KEY.encode())

# --- INTESTAZIONI DI SICUREZZA (HTTP Security Headers) ---
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# --- FUNZIONI DI SUPPORTO ---
def encrypt_data(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    return fernet.decrypt(encrypted_data.encode()).decode()

def hash_email(email: str) -> str:
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- ROTTE ---

@app.route('/')
def home():
    return redirect(url_for('first_page'))

@app.route('/policy')
def policy():
    return render_template("policy.html")

@app.route('/First_page')
def first_page():
    return render_template('First_page.html')

@app.route('/Index', methods=['GET'])
def Index():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user_name = session.get('user_name', '')

    conn = get_db_connection()
    snippets = conn.execute(
        "SELECT * FROM snippets WHERE user_id = ?", 
        (user_id,)
    ).fetchall()
    conn.close()

    return render_template('index.html', decryped_name=user_name, snippets=snippets)

@app.route('/create_page')
def page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("create.html")

@app.route("/support")
def support():
    return render_template("support.html")

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        return redirect(url_for('page'))

    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    titolo = request.form.get("titolo")
    linguaggio = request.form.get("linguaggio")
    codice = request.form.get("codice")

    if not linguaggio or not codice or not titolo:
        flash("Tutti i campi sono obbligatori!")
        return redirect(url_for('page'))

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO snippets (titolo, linguaggio, codice, user_id) VALUES (?, ?, ?, ?)",
        (titolo, linguaggio, codice, user_id)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('Index'))

@app.route('/elimina/<int:snippet_id>', methods=['POST'])
def elimina_snippet(snippet_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute("DELETE FROM snippets WHERE id = ? AND user_id = ?", (snippet_id, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for('Index'))

@app.route('/account')
def account():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for('login'))
        
    user_name = session.get('user_name')
    
    conn = get_db_connection()
    # Recuperiamo email_hash poiché la colonna 'email' non esiste più nel DB
    user = conn.execute("SELECT email_hash,password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if not user:
        session.clear()
        return redirect(url_for('login'))

    return render_template(
        "account.html", 
        name=user_name, 
        id=user_id, 
        email_hash=user['email_hash'],
        password_hash=user['password_hash'],
    )
@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        flash("Devi aver effettuato l'accesso per compiere questa azione.")
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    conn.execute('DELETE FROM snippets WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    session.clear()
    return redirect(url_for('first_page'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not name or not email or not password:
            flash("Compilare tutti i campi del modulo.")
            return redirect(url_for('register'))

        if password != confirm_password:
            flash("Le password non coincidono.")
            return redirect(url_for('register'))

        email_h = hash_email(email)

        conn = get_db_connection()
        user = conn.execute('SELECT id FROM users WHERE email_hash = ?', (email_h,)).fetchone()

        if user:
            conn.close()
            flash("Questa email è già registrata.")
            return redirect(url_for('register'))

        encrypted_name = encrypt_data(name)
        hashed_password = generate_password_hash(password)

        conn.execute(
            'INSERT INTO users (name, email_hash, password_hash) VALUES (?, ?, ?)',
            (encrypted_name, email_h, hashed_password)
        )
        conn.commit()
        conn.close()

        flash("Registrazione avvenuta con successo! Ora puoi accedere.")
        return redirect(url_for('login'))

    return render_template('Register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash("Inserire email e password.")
            return redirect(url_for('login'))

        email_h = hash_email(email)

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email_hash = ?', (email_h,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            decrypted_name = decrypt_data(user['name'])
            
            # PULIZIA SICUREZZA: Si salvano solo i dati necessari alla sessione
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = decrypted_name
            
            return redirect(url_for('Index'))
        else:
            flash("Credenziali non valide. Riprova.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('first_page'))

if __name__ == '__main__':
    # Disabilitare debug=True prima del rilascio in produzione
    app.run(debug=True)