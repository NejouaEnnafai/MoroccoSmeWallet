from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os
from translations import translations
from database import db
from models import User, Expense, Revenue
import requests
from werkzeug.utils import secure_filename

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
    # Récupérer les dépenses récentes
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5)
    
    # Calculer le total des dépenses pour la période en cours (ce mois-ci)
    current_month = datetime.now().month
    current_year = datetime.now().year
    total_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        db.extract('month', Expense.date) == current_month,
        db.extract('year', Expense.date) == current_year
    ).scalar() or 0

    # Calculer la croissance des dépenses (comparaison avec le mois précédent)
    last_month = (current_month - 1) if current_month > 1 else 12
    last_month_year = current_year if current_month > 1 else current_year - 1
    
    last_month_total = db.session.query(db.func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        db.extract('month', Expense.date) == last_month,
        db.extract('year', Expense.date) == last_month_year
    ).scalar() or 0
    
    expense_growth = ((total_expenses - last_month_total) / last_month_total * 100) if last_month_total > 0 else 0

    # Nombre total de transactions ce mois
    total_transactions = Expense.query.filter(
        Expense.user_id == current_user.id,
        db.extract('month', Expense.date) == current_month,
        db.extract('year', Expense.date) == current_year
    ).count()

    # Top catégories
    categories = db.session.query(
        Expense.category,
        db.func.sum(Expense.amount).label('total_amount')
    ).filter(
        Expense.user_id == current_user.id,
        db.extract('month', Expense.date) == current_month,
        db.extract('year', Expense.date) == current_year
    ).group_by(Expense.category).all()
    
    # Calculer les pourcentages pour chaque catégorie
    top_categories = []
    if categories:
        total_amount = sum(cat.total_amount for cat in categories)
        top_categories = [
            {
                'name': cat.category,
                'amount': cat.total_amount,
                'percentage': round((cat.total_amount / total_amount) * 100 if total_amount > 0 else 0, 1)
            }
            for cat in categories
        ]

    # Factures à venir (simulées pour l'exemple)
    upcoming_bills = [
        {
            'title': get_text('office_rent'),
            'amount': 5000,
            'days_left': 5,
            'recurring': True
        },
        {
            'title': get_text('utilities'),
            'amount': 1200,
            'days_left': 12,
            'recurring': True
        }
    ]

    return render_template('dashboard.html',
        user=current_user,
        expenses=expenses,
        total_expenses=total_expenses,
        expense_growth=expense_growth,
        total_transactions=total_transactions,
        top_categories=top_categories,
        upcoming_bills=upcoming_bills
    )

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        recipient = request.form.get('recipient')
        description = request.form.get('description')

        if amount <= current_user.balance:
            # transaction = Transaction(
            #     user_id=current_user.id,
            #     amount=amount,
            #     transaction_type='transfer',
            #     description=description,
            #     recipient=recipient,
            #     status='completed'
            # )
            # current_user.balance -= amount
            # db.session.add(transaction)
            # db.session.commit()
            flash('Transfer successful!', 'success')
        else:
            flash('Insufficient funds!', 'error')
        
        return redirect(url_for('dashboard'))
    
    return render_template('transfer.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(get_text('login_success'), 'success')
            return redirect(url_for('dashboard'))
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

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    try:
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        category = request.form.get('category')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        
        new_expense = Expense(
            amount=amount,
            description=description,
            category=category,
            date=date,
            user_id=current_user.id
        )
        
        # Gérer le reçu s'il est fourni
        if 'receipt' in request.files:
            receipt = request.files['receipt']
            if receipt and receipt.filename:
                # Créer le dossier uploads s'il n'existe pas
                if not os.path.exists('uploads'):
                    os.makedirs('uploads')
                
                # Sauvegarder le fichier
                filename = secure_filename(f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{receipt.filename}")
                receipt.save(os.path.join('uploads', filename))
                new_expense.receipt_path = filename
        
        db.session.add(new_expense)
        db.session.commit()
        
        return jsonify({'success': True, 'message': get_text('expense_added_success')})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/get_expenses')
@login_required
def get_expenses():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return jsonify([expense.to_dict() for expense in expenses])

@app.route('/delete_expense/<int:id>', methods=['DELETE'])
@login_required
def delete_expense(id):
    try:
        expense = Expense.query.get_or_404(id)
        if expense.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
        # Supprimer le reçu s'il existe
        if expense.receipt_path:
            receipt_path = os.path.join('uploads', expense.receipt_path)
            if os.path.exists(receipt_path):
                os.remove(receipt_path)
        
        db.session.delete(expense)
        db.session.commit()
        
        return jsonify({'success': True, 'message': get_text('expense_deleted_success')})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    try:
        # Récupérer les dépenses de l'utilisateur pour le contexte
        user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
        total_expenses = sum(expense.amount for expense in user_expenses)
        
        # Préparer le résumé des dépenses
        if user_expenses:
            # S'il y a des dépenses, obtenir la catégorie principale
            categories = {}
            for expense in user_expenses:
                categories[expense.category] = categories.get(expense.category, 0) + expense.amount
            top_category = max(categories.items(), key=lambda x: x[1])
            expense_summary = f"Total: {total_expenses}MAD. Catégorie principale: {top_category[0]}: {top_category[1]}MAD"
        else:
            # S'il n'y a pas de dépenses
            expense_summary = "Aucune dépense enregistrée pour le moment"
        
        # Message système détaillé mais concis
        system_message = f"""Assistant Morocco SME Wallet. {expense_summary}.
Rôle: Guider les PME marocaines dans la gestion de leurs dépenses via l'application.
Fonctionnalités: Suivi des dépenses, catégorisation, analyse des tendances, rapports PDF.
Catégories disponibles: Matériel, Marketing, Services, Salaires, Transport, Autres.
Répondre en français avec des conseils pratiques liés aux fonctionnalités de l'application."""
        
        response = requests.post('http://localhost:11434/api/generate', 
            json={
                "model": "llama3.2:1b",
                "prompt": user_message,
                "stream": False,
                "system": system_message,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150,
                    "top_k": 20,
                    "top_p": 0.9,
                    "num_ctx": 128,
                    "repeat_penalty": 1.1
                }
            })
        
        if response.status_code == 200:
            response_data = response.json()
            print("Ollama response:", response_data)
            
            if 'response' in response_data:
                return jsonify({'response': response_data['response']})
            else:
                print("Unexpected response format:", response_data)
                return jsonify({'response': "Format de réponse inattendu de l'assistant."}), 500
        else:
            print(f"Error status code: {response.status_code}")
            print("Error response:", response.text)
            return jsonify({'response': "Désolé, je ne peux pas répondre pour le moment."}), 500
            
    except Exception as e:
        print(f"Error calling Ollama: {str(e)}")
        return jsonify({'response': "Une erreur s'est produite lors de la communication avec le chatbot."}), 500

@app.route('/add_revenue', methods=['POST'])
@login_required
def add_revenue():
    try:
        data = request.get_json()
        new_revenue = Revenue(
            amount=float(data['amount']),
            description=data['description'],
            category=data['category'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            user_id=current_user.id
        )
        db.session.add(new_revenue)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Revenu ajouté avec succès'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/get_revenues')
@login_required
def get_revenues():
    revenues = Revenue.query.filter_by(user_id=current_user.id).order_by(Revenue.date.desc()).all()
    return jsonify([revenue.to_dict() for revenue in revenues])

@app.route('/api/transactions')
@login_required
def get_transactions():
    # transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).all()
    # return jsonify([{
    #     'id': t.id,
    #     'amount': t.amount,
    #     'type': t.transaction_type,
    #     'description': t.description,
    #     'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
    #     'status': t.status
    # } for t in transactions])
    return jsonify([])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
