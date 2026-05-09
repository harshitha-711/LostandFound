from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portal.db'
app.config['SECRET_KEY'] = 'your_secret_key_here' # Needed for session and flash messages
db = SQLAlchemy(app)

# --- MODELS ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    items = db.relationship('Item', backref='author', lazy=True) # Links items to user

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Lost') 
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Foreign key to User

with app.app_context():
    db.create_all()

# --- AUTHENTICATION MIDDLEWARE ---

@app.before_request
def require_login():
    # Force login for all pages except login and register
    allowed_routes = ['login', 'register', 'static']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))

# --- ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Domain restriction
        if not email.endswith('@bmsce.ac.in'):
            flash('Access restricted: Please use a valid @bmsce.ac.in email address.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    search_query = request.args.get('search')
    if search_query:
        items = Item.query.filter(Item.title.contains(search_query)).order_by(Item.date_posted.desc()).all()
    else:
        items = Item.query.order_by(Item.date_posted.desc()).all()
    return render_template('index.html', items=items)

@app.route('/report', methods=['POST', 'GET'])
def report():
     request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        description = request.form['description']
        location = request.form['location']
        status = request.form['status']

        new_item = Item(
            title=title, category=category, description=description, 
            location=location, status=status, user_id=session['user_id']
        )
        db.session.add(new_item)
        db.session.commit()

        # MATCHING LOGIC: Look for the opposite status in the same category
       # ENHANCED MATCHING LOGIC
        opposite_status = 'Found' if status == 'Lost' else 'Lost'
        
        # This looks for items in the same category where the title 
        # is either a subset or a superset of the reported item
        matches = Item.query.filter(
            Item.status == opposite_status,
            Item.category == category,
            db.or_(
                Item.title.ilike(f"%{title}%"),
                db.literal(title).ilike(db.concat("%", Item.title, "%"))
            )
        ).all()

        if matches:
            flash(f"Matching {opposite_status} item detected! Please contact the other user.", "warning")
        else:
            flash("Item reported successfully!", "success")

        return redirect('/')
    return render_template('report.html')

if __name__ == "__main__":
    app.run(debug=True)