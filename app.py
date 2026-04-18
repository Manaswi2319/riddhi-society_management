from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'riddhi-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///society.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='member')
    user_type = db.Column(db.String(20), default='resident')
    flat_no = db.Column(db.String(10))
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    address = db.Column(db.String(200))
    joining_date = db.Column(db.DateTime, default=datetime.utcnow)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flat_no = db.Column(db.String(10), unique=True, nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    family_members = db.Column(db.Integer, default=1)
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))
    parking_slot = db.Column(db.String(10))

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flat_no = db.Column(db.String(10), nullable=False)
    complaint_type = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flat_no = db.Column(db.String(10), nullable=False)
    month = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(80))
    
    section = db.relationship('Section', backref=db.backref('contents', lazy=True))

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(50), unique=True, nullable=False)
    flat_no = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_mode = db.Column(db.String(50))
    receipt_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(80))

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(80))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database and admin user
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin',
            user_type='staff',
            flat_no='A-001',
            full_name='Administrator',
            email='admin@riddhi.com'
        )
        db.session.add(admin)
        db.session.commit()
        
        # Add default sections
        default_sections = ['Roles', 'Payment Mode', 'Building Type', 'Expense Type', 'Notice Board', 'Rules & Regulations']
        for section in default_sections:
            if not Section.query.filter_by(section_name=section).first():
                db.session.add(Section(section_name=section))
        db.session.commit()
        print('✅ Admin and default sections created!')

# ========== LOGIN/LOGOUT ==========
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

# ========== DASHBOARD ==========
@app.route('/dashboard')
@login_required
def dashboard():
    total_members = Member.query.count()
    total_complaints = Complaint.query.count()
    pending_complaints = Complaint.query.filter_by(status='Pending').count()
    total_bills = Bill.query.count()
    total_amount_due = db.session.query(db.func.sum(Bill.total_amount)).filter_by(paid=False).scalar() or 0
    total_sections = Section.query.count()
    total_contents = Content.query.count()
    total_receipts = Receipt.query.count()
    total_expenses = Expense.query.count()
    total_users = User.query.count()
    
    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()
    recent_bills = Bill.query.order_by(Bill.due_date.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         name=current_user.full_name,
                         total_members=total_members,
                         total_complaints=total_complaints,
                         pending_complaints=pending_complaints,
                         total_bills=total_bills,
                         total_amount_due=total_amount_due,
                         total_sections=total_sections,
                         total_contents=total_contents,
                         total_receipts=total_receipts,
                         total_expenses=total_expenses,
                         total_users=total_users,
                         recent_complaints=recent_complaints,
                         recent_bills=recent_bills)

# ========== SECTION CRUD ==========
@app.route('/admin/sections')
@login_required
def admin_sections():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    sections = Section.query.order_by(Section.id).all()
    return render_template('admin_sections.html', sections=sections)

@app.route('/admin/add_section', methods=['POST'])
@login_required
def add_section():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    section_name = request.form.get('section_name')
    if section_name:
        existing = Section.query.filter_by(section_name=section_name).first()
        if existing:
            flash('Section already exists!', 'danger')
        else:
            section = Section(section_name=section_name)
            db.session.add(section)
            db.session.commit()
            flash('Section added successfully!', 'success')
    return redirect(url_for('admin_sections'))

@app.route('/admin/edit_section/<int:id>', methods=['POST'])
@login_required
def edit_section(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    section = Section.query.get_or_404(id)
    new_name = request.form.get('section_name')
    if new_name:
        section.section_name = new_name
        db.session.commit()
        flash('Section updated successfully!', 'success')
    return redirect(url_for('admin_sections'))

@app.route('/admin/delete_section/<int:id>')
@login_required
def delete_section(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    section = Section.query.get_or_404(id)
    db.session.delete(section)
    db.session.commit()
    flash('Section deleted successfully!', 'success')
    return redirect(url_for('admin_sections'))

# ========== CONTENT CRUD ==========
@app.route('/admin/contents')
@login_required
def admin_contents():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    contents = Content.query.order_by(Content.created_at.desc()).all()
    sections = Section.query.all()
    return render_template('admin_contents.html', contents=contents, sections=sections)

@app.route('/admin/add_content', methods=['POST'])
@login_required
def add_content():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    content = Content(
        section_id=request.form['section_id'],
        title=request.form['title'],
        content=request.form['content'],
        created_by=current_user.username
    )
    db.session.add(content)
    db.session.commit()
    flash('Content added successfully!', 'success')
    return redirect(url_for('admin_contents'))

@app.route('/admin/edit_content/<int:id>', methods=['POST'])
@login_required
def edit_content(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    content = Content.query.get_or_404(id)
    content.section_id = request.form['section_id']
    content.title = request.form['title']
    content.content = request.form['content']
    db.session.commit()
    flash('Content updated successfully!', 'success')
    return redirect(url_for('admin_contents'))

@app.route('/admin/delete_content/<int:id>')
@login_required
def delete_content(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    content = Content.query.get_or_404(id)
    db.session.delete(content)
    db.session.commit()
    flash('Content deleted successfully!', 'success')
    return redirect(url_for('admin_contents'))

# ========== USER CRUD ==========
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            password=generate_password_hash(request.form['password']),
            role=request.form['role'],
            user_type=request.form['user_type'],
            full_name=request.form['full_name'],
            email=request.form['email'],
            phone=request.form['phone'],
            flat_no=request.form.get('flat_no', '')
        )
        db.session.add(user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('add_user.html')

@app.route('/admin/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.full_name = request.form['full_name']
        user.email = request.form['email']
        user.phone = request.form['phone']
        user.role = request.form['role']
        user.user_type = request.form['user_type']
        user.flat_no = request.form.get('flat_no', '')
        if request.form.get('password'):
            user.password = generate_password_hash(request.form['password'])
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('edit_user.html', user=user)

@app.route('/admin/delete_user/<int:id>')
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(id)
    if user.username == 'admin':
        flash('Cannot delete main admin!', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/residents')
@login_required
def admin_residents():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    residents = User.query.filter_by(user_type='resident').all()
    return render_template('admin_residents.html', residents=residents)

@app.route('/admin/staff')
@login_required
def admin_staff():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    staff = User.query.filter_by(user_type='staff').all()
    return render_template('admin_staff.html', staff=staff)

@app.route('/admin/tenants')
@login_required
def admin_tenants():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    tenants = User.query.filter_by(user_type='tenant').all()
    return render_template('admin_tenants.html', tenants=tenants)

# ========== RECEIPT CRUD ==========
@app.route('/admin/receipts')
@login_required
def admin_receipts():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    receipts = Receipt.query.order_by(Receipt.receipt_date.desc()).all()
    return render_template('admin_receipts.html', receipts=receipts)

@app.route('/admin/add_receipt', methods=['GET', 'POST'])
@login_required
def add_receipt():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        receipt = Receipt(
            receipt_no=request.form['receipt_no'],
            flat_no=request.form['flat_no'],
            amount=float(request.form['amount']),
            payment_mode=request.form['payment_mode'],
            created_by=current_user.username
        )
        db.session.add(receipt)
        db.session.commit()
        flash('Receipt generated successfully!', 'success')
        return redirect(url_for('admin_receipts'))
    
    members = Member.query.all()
    return render_template('add_receipt.html', members=members)

@app.route('/admin/delete_receipt/<int:id>')
@login_required
def delete_receipt(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    receipt = Receipt.query.get_or_404(id)
    db.session.delete(receipt)
    db.session.commit()
    flash('Receipt deleted successfully!', 'success')
    return redirect(url_for('admin_receipts'))

# ========== EXPENSE CRUD ==========
@app.route('/admin/expenses')
@login_required
def admin_expenses():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    expenses = Expense.query.order_by(Expense.expense_date.desc()).all()
    return render_template('admin_expenses.html', expenses=expenses)

@app.route('/admin/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        expense = Expense(
            expense_type=request.form['expense_type'],
            description=request.form['description'],
            amount=float(request.form['amount']),
            created_by=current_user.username
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('admin_expenses'))
    
    return render_template('add_expense.html')

@app.route('/admin/edit_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    expense = Expense.query.get_or_404(id)
    if request.method == 'POST':
        expense.expense_type = request.form['expense_type']
        expense.description = request.form['description']
        expense.amount = float(request.form['amount'])
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('admin_expenses'))
    
    return render_template('edit_expense.html', expense=expense)

@app.route('/admin/delete_expense/<int:id>')
@login_required
def delete_expense(id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))
    
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('admin_expenses'))

# ========== MEMBER CRUD ==========
@app.route('/members')
@login_required
def members():
    all_members = Member.query.all()
    return render_template('members.html', members=all_members)

@app.route('/add_member', methods=['GET', 'POST'])
@login_required
def add_member():
    if request.method == 'POST':
        member = Member(
            flat_no=request.form['flat_no'],
            owner_name=request.form['owner_name'],
            family_members=request.form['family_members'],
            phone=request.form['phone'],
            email=request.form['email'],
            parking_slot=request.form['parking_slot']
        )
        db.session.add(member)
        db.session.commit()
        flash('Member added successfully!', 'success')
        return redirect(url_for('members'))
    return render_template('add_member.html')

@app.route('/edit_member/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_member(id):
    member = Member.query.get_or_404(id)
    if request.method == 'POST':
        member.owner_name = request.form['owner_name']
        member.family_members = request.form['family_members']
        member.phone = request.form['phone']
        member.email = request.form['email']
        member.parking_slot = request.form['parking_slot']
        db.session.commit()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('members'))
    return render_template('edit_member.html', member=member)

@app.route('/delete_member/<int:id>')
@login_required
def delete_member(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    flash('Member deleted successfully!', 'success')
    return redirect(url_for('members'))

# ========== COMPLAINT CRUD ==========
@app.route('/complaints')
@login_required
def complaints():
    all_complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template('complaints.html', complaints=all_complaints)

@app.route('/add_complaint', methods=['GET', 'POST'])
@login_required
def add_complaint():
    if request.method == 'POST':
        complaint = Complaint(
            flat_no=request.form['flat_no'],
            complaint_type=request.form['complaint_type'],
            description=request.form['description']
        )
        db.session.add(complaint)
        db.session.commit()
        flash('Complaint registered successfully!', 'success')
        return redirect(url_for('complaints'))
    members = Member.query.all()
    return render_template('add_complaint.html', members=members)

@app.route('/edit_complaint/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    if request.method == 'POST':
        complaint.complaint_type = request.form['complaint_type']
        complaint.description = request.form['description']
        complaint.status = request.form['status']
        db.session.commit()
        flash('Complaint updated successfully!', 'success')
        return redirect(url_for('complaints'))
    return render_template('edit_complaint.html', complaint=complaint)

@app.route('/delete_complaint/<int:id>')
@login_required
def delete_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    db.session.delete(complaint)
    db.session.commit()
    flash('Complaint deleted successfully!', 'success')
    return redirect(url_for('complaints'))

@app.route('/resolve_complaint/<int:id>')
@login_required
def resolve_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    complaint.status = 'Resolved'
    db.session.commit()
    flash('Complaint marked as resolved!', 'success')
    return redirect(url_for('complaints'))

# ========== BILL CRUD ==========
@app.route('/bills')
@login_required
def bills():
    all_bills = Bill.query.order_by(Bill.due_date.desc()).all()
    return render_template('bills.html', bills=all_bills)

@app.route('/add_bill', methods=['GET', 'POST'])
@login_required
def add_bill():
    if request.method == 'POST':
        total = float(request.form['amount'])
        bill = Bill(
            flat_no=request.form['flat_no'],
            month=request.form['month'],
            year=int(request.form['year']),
            amount=total,
            total_amount=total,
            due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        )
        db.session.add(bill)
        db.session.commit()
        flash('Bill generated successfully!', 'success')
        return redirect(url_for('bills'))
    members = Member.query.all()
    return render_template('add_bill.html', members=members)

@app.route('/edit_bill/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_bill(id):
    bill = Bill.query.get_or_404(id)
    if request.method == 'POST':
        bill.amount = float(request.form['amount'])
        bill.total_amount = float(request.form['amount'])
        bill.month = request.form['month']
        bill.year = int(request.form['year'])
        bill.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        db.session.commit()
        flash('Bill updated successfully!', 'success')
        return redirect(url_for('bills'))
    return render_template('edit_bill.html', bill=bill)

@app.route('/delete_bill/<int:id>')
@login_required
def delete_bill(id):
    bill = Bill.query.get_or_404(id)
    db.session.delete(bill)
    db.session.commit()
    flash('Bill deleted successfully!', 'success')
    return redirect(url_for('bills'))

@app.route('/pay_bill/<int:id>')
@login_required
def pay_bill(id):
    bill = Bill.query.get_or_404(id)
    bill.paid = True
    db.session.commit()
    flash('Payment recorded successfully!', 'success')
    return redirect(url_for('bills'))

if __name__ == '__main__':
    print('🚀 Riddhi Society Management System Starting...')
    print('🌐 Server: http://127.0.0.1:5000')
    print('📝 Login: admin / admin123')
    print('='*50)
    app.run(debug=True, port=5000)