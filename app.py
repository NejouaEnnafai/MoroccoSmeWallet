from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from translations import translations
from database import db
from models import User, Expense

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///morocco_wallet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_text(key):
    lang = session.get('language', 'ar')
    return translations[lang].get(key, '')

app.jinja_env.globals.update(get_text=get_text)

@app.before_request
def before_request():
    # Set default language if not set
    if 'language' not in session:
        session['language'] = 'ar'  # Default to Arabic

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(5)
    return render_template('dashboard.html', user=current_user, transactions=transactions)

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        recipient = request.form.get('recipient')
        description = request.form.get('description')

        if amount <= current_user.balance:
            transaction = Transaction(
                user_id=current_user.id,
                amount=amount,
                transaction_type='transfer',
                description=description,
                recipient=recipient,
                status='completed'
            )
            current_user.balance -= amount
            db.session.add(transaction)
            db.session.commit()
            flash('Transfer successful!', 'success')
        else:
            flash('Insufficient funds!', 'error')
        
        return redirect(url_for('dashboard'))
    
    return render_template('transfer.html')

@app.route('/api/transactions')
@login_required
def get_transactions():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).all()
    return jsonify([{
        'id': t.id,
        'amount': t.amount,
        'type': t.transaction_type,
        'description': t.description,
        'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'status': t.status
    } for t in transactions])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(get_text('login_success'), 'success')
            return redirect(url_for('index'))
        else:
            flash(get_text('login_error'), 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        business_name = request.form.get('business_name')
        email = request.form.get('email')
        password = request.form.get('password')
        business_type = request.form.get('business_type')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        if User.query.filter_by(email=email).first():
            flash(get_text('email_exists'), 'error')
            return redirect(url_for('register'))
        
        user = User(
            business_name=business_name,
            email=email,
            password_hash=generate_password_hash(password),
            business_type=business_type,
            phone=phone,
            address=address
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash(get_text('register_success'), 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('index'))

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['ar', 'fr']:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/expenses')
@login_required
def expenses():
    return render_template('expenses.html')

@app.route('/api/expenses', methods=['GET'])
@login_required
def get_expenses():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return jsonify([expense.to_dict() for expense in expenses])

@app.route('/api/expenses', methods=['POST'])
@login_required
def add_expense():
    data = request.json
    expense = Expense(
        description=data['description'],
        amount=float(data['amount']),
        category=data['category'],
        date=datetime.strptime(data['date'], '%Y-%m-%d'),
        notes=data.get('notes'),
        user_id=current_user.id
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify(expense.to_dict()), 201

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
@login_required
def update_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    expense.description = data.get('description', expense.description)
    expense.amount = float(data.get('amount', expense.amount))
    expense.category = data.get('category', expense.category)
    expense.date = datetime.strptime(data.get('date', expense.date.strftime('%Y-%m-%d')), '%Y-%m-%d')
    expense.notes = data.get('notes', expense.notes)
    
    db.session.commit()
    return jsonify(expense.to_dict())

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(expense)
    db.session.commit()
    return '', 204

@app.route('/api/expenses/upload', methods=['POST'])
@login_required
def upload_receipt():
    if 'receipt' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['receipt']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # TODO: Implement AI receipt processing here
        
        return jsonify({
            'filepath': filepath,
            'message': 'Receipt uploaded successfully'
        })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
