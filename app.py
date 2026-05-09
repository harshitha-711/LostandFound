from flask import Flask,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portal.db'
db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Lost') # Lost or Found
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    search_query = request.args.get('search')
    if search_query:
        # Filters titles that contain the search string (case-insensitive)
        items = Item.query.filter(Item.title.contains(search_query)).order_by(Item.date_posted.desc()).all()
    else:
        items = Item.query.order_by(Item.date_posted.desc()).all()
    return render_template('index.html', items=items)
    
@app.route('/report', methods=['POST', 'GET'])
def report():
    if request.method == 'POST':
        new_item = Item(
            title=request.form['title'],
            category=request.form['category'],
            description=request.form['description'],
            location=request.form['location'],
            status=request.form['status']
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect('/')
    return render_template('report.html')

if __name__ == "__main__":
    app.run(debug=True)