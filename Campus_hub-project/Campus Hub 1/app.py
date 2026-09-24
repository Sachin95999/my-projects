from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from models import db, User, LostFoundItem, Complaint, Notice, MessMenu, Notification
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_campus_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def seed_default_data():
    """Seed notices and mess menu if empty."""
    if Notice.query.count() == 0:
        notices = [
            Notice(title='End Semester Examinations', body='End semester examinations will commence from May 5th. Hall tickets can be collected from the academic section.', category='Academic', is_pinned=True),
            Notice(title='Hostel Curfew Reminder', body='All students must return to the hostel by 10:30 PM on weekdays and 11:30 PM on weekends. Violations will be reported to the warden.', category='Hostel', is_pinned=True),
            Notice(title='Annual Cultural Fest – Vibrance 2026', body='Registrations for Vibrance 2026 are now open! Visit the student affairs office or register online at vibrance.campus.edu before April 20th.', category='Events', is_pinned=False),
            Notice(title='Library Timing Update', body='The central library will now be open until midnight (12:00 AM) from Monday to Friday during the exam season.', category='Academic', is_pinned=False),
            Notice(title='Water Supply Interruption', body='Due to maintenance work, water supply to Block C and D will be interrupted on April 12th from 8 AM to 2 PM. Water tankers will be arranged.', category='Hostel', is_pinned=False),
            Notice(title='Sports Day – April 18th', body='Annual Sports Day is scheduled for April 18th. Students interested in participating must register at the sports office by April 14th.', category='Events', is_pinned=False),
        ]
        for n in notices:
            db.session.add(n)

    if MessMenu.query.count() == 0:
        menu_data = {
            'Monday':    {'Breakfast': 'Idli, Sambar, Coconut Chutney, Tea/Coffee', 'Lunch': 'Rice, Dal Fry, Aloo Gobi, Salad, Papad', 'Dinner': 'Chapati, Paneer Butter Masala, Dal Tadka, Rice, Curd'},
            'Tuesday':   {'Breakfast': 'Poha, Boiled Eggs, Bread & Butter, Tea', 'Lunch': 'Rice, Rajma, Jeera Aloo, Raita, Roti', 'Dinner': 'Chapati, Chana Masala, Mixed Veg, Rice, Pickle'},
            'Wednesday': {'Breakfast': 'Upma, Vada, Sambar, Tea/Coffee', 'Lunch': 'Rice, Dal Makhani, Bhindi Fry, Papad, Salad', 'Dinner': 'Chapati, Egg Curry/Paneer Curry, Dal, Rice, Curd'},
            'Thursday':  {'Breakfast': 'Puri Bhaji, Banana, Tea', 'Lunch': 'Rice, Sambar, Rasam, Papad, Potato Roast', 'Dinner': 'Chapati, Chicken Curry (Non-veg)/Kofta Curry, Rice, Dal'},
            'Friday':    {'Breakfast': 'Dosa, Sambar, Chutney, Tea/Coffee', 'Lunch': 'Fried Rice, Gobi Manchurian, Dal, Salad, Roti', 'Dinner': 'Chapati, Shahi Paneer, Mix Dal, Rice, Sweet (Halwa)'},
            'Saturday':  {'Breakfast': 'Bread Toast, Omelette/Jam, Cornflakes, Milk', 'Lunch': 'Rice, Dal, Aloo Paratha, Raita, Pickle', 'Dinner': 'Chapati, Mutton/Soya Curry, Veg Pulao, Dal, Ice Cream'},
            'Sunday':    {'Breakfast': 'Chole Bhature, Lassi/Juice, Fruits', 'Lunch': 'Biryani (Veg/Non-veg), Raita, Shami Kebab/Paneer Tikka, Salad', 'Dinner': 'Chapati, Dal Fry, Aloo Sabzi, Rice, Gulab Jamun'},
        }
        for day, meals in menu_data.items():
            for meal, items in meals.items():
                db.session.add(MessMenu(day=day, meal=meal, items=items))

    db.session.commit()

with app.app_context():
    db.create_all()
    seed_default_data()

# ─── Helpers ──────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Access denied. Administrator privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def push_notification(user_id, message, icon='🔔'):
    notif = Notification(user_id=user_id, message=message, icon=icon)
    db.session.add(notif)
    db.session.commit()

def time_ago(dt):
    now = datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        m = int(seconds // 60)
        return f'{m} minute{"s" if m > 1 else ""} ago'
    elif seconds < 86400:
        h = int(seconds // 3600)
        return f'{h} hour{"s" if h > 1 else ""} ago'
    elif seconds < 604800:
        d = int(seconds // 86400)
        return f'{d} day{"s" if d > 1 else ""} ago'
    else:
        return dt.strftime('%d %b %Y')

app.jinja_env.filters['time_ago'] = time_ago

@app.context_processor
def inject_globals():
    user = None
    unread_count = 0
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        unread_count = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    return dict(current_user=user, unread_notif_count=unread_count, current_endpoint=request.endpoint)

# ─── Auth ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        roll_no = request.form.get('roll_no')
        phone = request.form.get('phone')
        password = request.form.get('password')
        hostel_name = request.form.get('hostel_name')
        room_no = request.form.get('room_no')
        admin_code = request.form.get('admin_code', '').strip()
        
        is_admin = False
        if admin_code == 'ADMIN@789':  # This is the secret code
            is_admin = True
            
        if User.query.filter_by(roll_no=roll_no).first():
            flash('Roll number already registered. Please log in.', 'error')
            return redirect(url_for('signup'))
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, roll_no=roll_no, phone=phone, password=hashed_pw,
                        hostel_name=hostel_name, room_no=room_no, is_admin=is_admin)
        db.session.add(new_user)
        db.session.commit()
        
        msg = 'Account created successfully!'
        if is_admin:
            msg = 'Admin account created successfully! 🔑'
        flash(msg, 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        password = request.form.get('password')
        user = User.query.filter_by(roll_no=roll_no).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash(f'Welcome back, {user.name}! 👋', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid roll number or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    uid = session['user_id']
    stats = {
        'active_complaints': Complaint.query.filter(
            Complaint.user_id == uid,
            Complaint.status.in_(['Pending', 'In Progress', 'Reopened'])
        ).count(),
        'resolved_complaints': Complaint.query.filter(
            Complaint.user_id == uid,
            Complaint.status.in_(['Resolved', 'Auto-Resolved'])
        ).count(),
        'items_reported': LostFoundItem.query.filter_by(user_id=uid).count(),
        'items_claimed': LostFoundItem.query.filter_by(user_id=uid, status='Claimed').count(),
    }
    pinned_notices = Notice.query.filter_by(is_pinned=True).order_by(Notice.posted_at.desc()).limit(3).all()
    return render_template('dashboard.html', stats=stats, pinned_notices=pinned_notices)

# ─── Profile ──────────────────────────────────────────────────────────────────

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    user = User.query.get(session['user_id'])
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    if not name or not phone:
        flash('Name and phone number cannot be empty.', 'error')
        return redirect(url_for('profile'))

    user.name = name
    user.phone = phone
    user.hostel_name = request.form.get('hostel_name', user.hostel_name)
    user.room_no = request.form.get('room_no', user.room_no)
    new_pw = request.form.get('new_password', '').strip()
    if new_pw:
        current_pw = request.form.get('current_password', '')
        if check_password_hash(user.password, current_pw):
            user.password = generate_password_hash(new_pw, method='pbkdf2:sha256')
        else:
            flash('Current password is incorrect. Profile updated without password change.', 'warning')
            db.session.commit()
            return redirect(url_for('profile'))
    db.session.commit()
    flash('Profile updated successfully! ✅', 'success')
    return redirect(url_for('profile'))

# ─── Notifications ────────────────────────────────────────────────────────────

@app.route('/notifications')
@login_required
def notifications():
    uid = session['user_id']
    notifs = Notification.query.filter_by(user_id=uid).order_by(Notification.created_at.desc()).limit(30).all()
    # Mark all as read
    Notification.query.filter_by(user_id=uid, is_read=False).update({'is_read': True})
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)

@app.route('/notifications/mark_read', methods=['POST'])
@login_required
def mark_notifications_read():
    Notification.query.filter_by(user_id=session['user_id'], is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'status': 'ok'})

# ─── Notice Board ─────────────────────────────────────────────────────────────

@app.route('/notices')
@login_required
def notices():
    category = request.args.get('category', 'All')
    if category != 'All':
        all_notices = Notice.query.filter_by(category=category).order_by(Notice.is_pinned.desc(), Notice.posted_at.desc()).all()
    else:
        all_notices = Notice.query.order_by(Notice.is_pinned.desc(), Notice.posted_at.desc()).all()
    return render_template('notices.html', notices=all_notices, active_category=category)

# ─── Mess Menu ────────────────────────────────────────────────────────────────

@app.route('/sw.js')
def service_worker():
    """Serve service worker from root scope so it controls all pages."""
    return send_from_directory(app.static_folder, 'sw.js', mimetype='application/javascript')

@app.route('/mess_menu')
@login_required
def mess_menu():
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    meals_order = ['Breakfast', 'Lunch', 'Dinner']
    menus = MessMenu.query.all()
    menu_dict = {}
    for entry in menus:
        if entry.day not in menu_dict:
            menu_dict[entry.day] = {}
        menu_dict[entry.day][entry.meal] = entry.items
    today = datetime.now().strftime('%A')
    selected_day = request.args.get('day', today)
    if selected_day not in days_order:
        selected_day = today
    return render_template('mess_menu.html', menu_dict=menu_dict, days_order=days_order,
                           meals_order=meals_order, today=today, selected_day=selected_day)

# ─── Lost & Found ─────────────────────────────────────────────────────────────

@app.route('/lost_found', methods=['GET'])
@login_required
def lost_found():
    filter_type = request.args.get('type')
    category_filter = request.args.get('category')
    query_str = request.args.get('q', '').strip()

    q = LostFoundItem.query
    if filter_type in ['lost', 'found']:
        q = q.filter_by(item_type=filter_type)
    if category_filter:
        q = q.filter_by(category=category_filter)
    if query_str:
        q = q.filter(
            db.or_(
                LostFoundItem.title.ilike(f'%{query_str}%'),
                LostFoundItem.description.ilike(f'%{query_str}%')
            )
        )
    items = q.order_by(LostFoundItem.date_reported.desc()).all()

    # Leaderboard: top helpers (users who found & item got claimed)
    from sqlalchemy import func
    leaderboard = db.session.query(
        User.name,
        func.count(LostFoundItem.id).label('count')
    ).join(LostFoundItem, LostFoundItem.user_id == User.id)\
     .filter(LostFoundItem.item_type == 'found', LostFoundItem.status == 'Claimed')\
     .group_by(User.id)\
     .order_by(func.count(LostFoundItem.id).desc())\
     .limit(5).all()

    categories = ['Electronics', 'Documents/ID', 'Keys', 'Clothing', 'Stationery', 'Other']
    return render_template('lost_found.html', items=items, filter_type=filter_type,
                           category_filter=category_filter, query_str=query_str,
                           leaderboard=leaderboard, categories=categories)

@app.route('/report_item', methods=['POST'])
@login_required
def report_item():
    item_type = request.form.get('item_type')
    title = request.form.get('title')
    category = request.form.get('category')
    description = request.form.get('description')
    new_item = LostFoundItem(title=title, description=description, category=category,
                             item_type=item_type, user_id=session['user_id'])
    db.session.add(new_item)
    db.session.commit()
    flash(f'{"Lost" if item_type == "lost" else "Found"} item reported successfully. 📌', 'success')
    return redirect(url_for('lost_found'))

@app.route('/claim_item/<int:item_id>', methods=['POST'])
@login_required
def claim_item(item_id):
    item = LostFoundItem.query.get_or_404(item_id)
    item.status = 'Claimed'
    db.session.commit()
    # Notify the reporter
    if item.user_id != session['user_id']:
        push_notification(item.user_id, f'Your "{item.title}" report has been marked as resolved/claimed!', '✅')
    flash('Item marked as resolved/claimed. ✅', 'success')
    return redirect(url_for('lost_found'))

# ─── Complaints ───────────────────────────────────────────────────────────────

WORKERS = {
    'Plumbing':      ('Rajesh Kumar (Plumber, ID: P-101)', 'Tomorrow at 10:00 AM'),
    'Electrical':    ('Suresh Verma (Electrician, ID: E-102)', 'Today at 4:30 PM'),
    'Carpentry':     ('Mahesh Singh (Carpenter, ID: C-103)', 'Tomorrow at 2:00 PM'),
    'Network/Wi-Fi': ('Amit Sharma (IT Support, ID: N-201)', 'Today at 6:00 PM'),
    'Cleaning':      ('Sunita Devi (Housekeeping, ID: H-301)', 'Tomorrow at 8:00 AM'),
    'Other':         ('Vijay Kumar (Maintenance, ID: M-401)', 'Tomorrow at 11:00 AM'),
}

@app.route('/complaints', methods=['GET'])
@login_required
def complaints():
    uid = session['user_id']
    user_complaints = Complaint.query.filter_by(user_id=uid).order_by(Complaint.date_lodged.desc()).all()

    for c in user_complaints:
        # Auto-resolve check
        if c.status == 'In Progress' and c.expected_resolution_time and datetime.utcnow() >= c.expected_resolution_time:
            c.status = 'Auto-Resolved'
            db.session.commit()
            push_notification(uid, f'Your {c.category} complaint has been auto-resolved. Was it fixed?', '⏰')

        # Assign worker to new complaints
        if c.status == 'Pending' and not c.assigned_worker:
            assigned_info = WORKERS.get(c.category, ('Vijay Kumar (Maintenance)', 'Tomorrow at 4:00 PM'))
            c.assigned_worker = assigned_info[0]
            c.visit_time = assigned_info[1]
            c.expected_resolution_time = datetime.utcnow() + timedelta(minutes=1)
            c.status = 'In Progress'
            db.session.commit()
            push_notification(uid, f'Worker assigned for your {c.category} complaint. Visit: {c.visit_time}', '👷')

        # Handle re-opened auto-assignment
        if c.status == 'Reopened' and c.expected_resolution_time and datetime.utcnow() >= c.expected_resolution_time:
            c.status = 'Auto-Resolved'
            db.session.commit()
            push_notification(uid, f'Your re-opened {c.category} complaint has been auto-resolved again.', '⏰')

    return render_template('complaints.html', complaints=user_complaints)

@app.route('/lodge_complaint', methods=['POST'])
@login_required
def lodge_complaint():
    category = request.form.get('category')
    description = request.form.get('description')
    user = User.query.get(session['user_id'])
    if not user.hostel_name or not user.room_no:
        flash('Please update your hostel details in your profile first.', 'error')
        return redirect(url_for('complaints'))
    full_description = f"Room: {user.room_no}, Hostel: {user.hostel_name}. Issue: {description}"
    priority_map = {
        'Electrical': 'High', 'Plumbing': 'High',
        'Network/Wi-Fi': 'Medium', 'Carpentry': 'Medium',
        'Cleaning': 'Low', 'Other': 'Low'
    }
    new_complaint = Complaint(category=category, description=full_description,
                              priority=priority_map.get(category, 'Low'),
                              user_id=session['user_id'])
    db.session.add(new_complaint)
    db.session.commit()
    flash('Complaint lodged successfully. We\'ll assign a worker shortly. 🔧', 'success')
    return redirect(url_for('complaints'))

@app.route('/resolve_complaint/<int:complaint_id>', methods=['POST'])
@login_required
def resolve_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    if complaint.user_id == session['user_id']:
        complaint.status = 'Resolved'
        db.session.commit()
        flash('Complaint marked as resolved. Thank you for your feedback! ✅', 'success')
    return redirect(url_for('complaints'))

@app.route('/reopen_complaint/<int:complaint_id>', methods=['POST'])
@login_required
def reopen_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    if complaint.user_id == session['user_id']:
        complaint.status = 'Reopened'
        complaint.expected_resolution_time = datetime.utcnow() + timedelta(minutes=1)
        db.session.commit()
        push_notification(session['user_id'], f'Your {complaint.category} complaint has been re-opened for attention.', '🔄')
        flash('Complaint re-opened. We\'ll look into it again. 🔄', 'warning')
    return redirect(url_for('complaints'))

# ─── Admin Panel ──────────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'open_complaints': Complaint.query.filter(Complaint.status != 'Resolved').count(),
        'total_notices': Notice.query.count(),
        'active_items': LostFoundItem.query.filter_by(status='Active').count()
    }
    # Recent complaints for the mini-table
    recent_complaints = Complaint.query.order_by(Complaint.date_lodged.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, recent_complaints=recent_complaints)

@app.route('/admin/notices', methods=['GET', 'POST'])
@admin_required
def admin_notices():
    if request.method == 'POST':
        title = request.form.get('title')
        body = request.form.get('body')
        category = request.form.get('category')
        is_pinned = 'is_pinned' in request.form
        
        new_notice = Notice(title=title, body=body, category=category, is_pinned=is_pinned)
        db.session.add(new_notice)
        db.session.commit()
        flash('Notice published successfully! 📢', 'success')
        return redirect(url_for('admin_notices'))
    
    all_notices = Notice.query.order_by(Notice.posted_at.desc()).all()
    return render_template('admin/notices.html', notices=all_notices)

@app.route('/admin/delete_notice/<int:notice_id>')
@admin_required
def delete_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    db.session.delete(notice)
    db.session.commit()
    flash('Notice deleted.', 'info')
    return redirect(url_for('admin_notices'))

@app.route('/admin/mess_menu', methods=['GET', 'POST'])
@admin_required
def admin_mess_menu():
    if request.method == 'POST':
        day = request.form.get('day')
        meal = request.form.get('meal')
        items = request.form.get('items')
        
        menu_entry = MessMenu.query.filter_by(day=day, meal=meal).first()
        if menu_entry:
            menu_entry.items = items
            db.session.commit()
            flash(f'Menu updated for {day} {meal}!', 'success')
        else:
            flash('Meal entry not found.', 'error')
        return redirect(url_for('admin_mess_menu'))
    
    menus = MessMenu.query.all()
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    meals_order = ['Breakfast', 'Lunch', 'Dinner']
    return render_template('admin/mess_menu.html', menus=menus, days_order=days_order, meals_order=meals_order)

@app.route('/admin/update_complaint/<int:complaint_id>', methods=['POST'])
@admin_required
def admin_update_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    status = request.form.get('status')
    worker = request.form.get('worker')
    
    complaint.status = status
    if worker:
        complaint.assigned_worker = worker
    
    db.session.commit()
    push_notification(complaint.user_id, f'Admin updated your {complaint.category} complaint status to: {status}', '🛠️')
    flash('Complaint updated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
