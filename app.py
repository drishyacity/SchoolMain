import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy with a base class
class Base(DeclarativeBase):
    pass

# Create a db instance
db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///school.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# File upload settings
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access the admin panel.'

from models import User, News, Event, GalleryImage, Contact, AboutSection, AcademicProgram, SchoolSetting
from forms import LoginForm, NewsForm, EventForm, GalleryUploadForm, ContactForm, AboutSectionForm, AcademicProgramForm, SchoolSettingsForm, UserForm, ProfileForm
from utils import allowed_file, save_file

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()
    
    # Create admin user if doesn't exist
    if not User.query.filter_by(username='admin').first():
        from werkzeug.security import generate_password_hash
        admin = User(
            username='admin',
            email='admin@school.edu',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        
        # Add default school settings
        settings = SchoolSetting(
            school_name='Shree Gyan Bharti High School',
            school_address='Bakhari Chowk Sitamarhi, Bihar 843302, India',
            school_phone='+91 1234567890',
            school_email='info@sgbhs.edu',
            school_logo_path='IMG-20250425-WA0004.jpg'  # Logo file from uploaded assets
        )
        db.session.add(settings)
        db.session.commit()

# Frontend routes
@app.route('/')
def index():
    settings = SchoolSetting.query.first()
    news_items = News.query.order_by(News.date.desc()).limit(3).all()
    events = Event.query.filter(Event.date >= datetime.now()).order_by(Event.date).limit(3).all()
    return render_template('index.html', settings=settings, news_items=news_items, events=events)

@app.route('/about')
def about():
    settings = SchoolSetting.query.first()
    about_sections = AboutSection.query.order_by(AboutSection.order).all()
    return render_template('about.html', settings=settings, about_sections=about_sections)

@app.route('/academics')
def academics():
    settings = SchoolSetting.query.first()
    programs = AcademicProgram.query.order_by(AcademicProgram.order).all()
    return render_template('academics.html', settings=settings, programs=programs)

@app.route('/events')
def events():
    settings = SchoolSetting.query.first()
    upcoming_events = Event.query.filter(Event.date >= datetime.now()).order_by(Event.date).all()
    past_events = Event.query.filter(Event.date < datetime.now()).order_by(Event.date.desc()).all()
    return render_template('events.html', settings=settings, upcoming_events=upcoming_events, past_events=past_events)

@app.route('/achievements')
def achievements():
    settings = SchoolSetting.query.first()
    return render_template('achievements.html', settings=settings)

@app.route('/gallery')
def gallery():
    settings = SchoolSetting.query.first()
    images = GalleryImage.query.order_by(GalleryImage.upload_date.desc()).all()
    return render_template('gallery.html', settings=settings, images=images)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    settings = SchoolSetting.query.first()
    form = ContactForm()
    contact_info = Contact.query.first()
    
    if form.validate_on_submit():
        new_contact = Contact(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(new_contact)
        db.session.commit()
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html', settings=settings, form=form, contact_info=contact_info)

@app.route('/news')
def news():
    settings = SchoolSetting.query.first()
    news_items = News.query.order_by(News.date.desc()).all()
    return render_template('news.html', settings=settings, news_items=news_items)

@app.route('/news/<int:news_id>')
def news_detail(news_id):
    settings = SchoolSetting.query.first()
    news_item = News.query.get_or_404(news_id)
    return render_template('news_detail.html', settings=settings, news=news_item)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('admin/login.html', form=form)

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    news_count = News.query.count()
    events_count = Event.query.count()
    gallery_count = GalleryImage.query.count()
    contacts_count = Contact.query.count()
    return render_template('admin/dashboard.html', 
                           news_count=news_count, 
                           events_count=events_count, 
                           gallery_count=gallery_count, 
                           contacts_count=contacts_count)

# News Management
@app.route('/admin/news')
@login_required
def admin_news():
    news_items = News.query.order_by(News.date.desc()).all()
    return render_template('admin/news_manage.html', news_items=news_items)

@app.route('/admin/news/add', methods=['GET', 'POST'])
@login_required
def admin_add_news():
    form = NewsForm()
    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            if allowed_file(form.image.data.filename, app.config['ALLOWED_EXTENSIONS']):
                image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'], 'news')
            else:
                flash('Invalid file format. Allowed formats: png, jpg, jpeg, gif', 'danger')
                return render_template('admin/news_form.html', form=form, title="Add News")
        
        news = News(
            title=form.title.data,
            content=form.content.data,
            date=form.date.data,
            image_path=image_path
        )
        db.session.add(news)
        db.session.commit()
        flash('News added successfully!', 'success')
        return redirect(url_for('admin_news'))
    
    return render_template('admin/news_form.html', form=form, title="Add News")

@app.route('/admin/news/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_news(id):
    news = News.query.get_or_404(id)
    form = NewsForm(obj=news)
    
    if form.validate_on_submit():
        news.title = form.title.data
        news.content = form.content.data
        news.date = form.date.data
        
        if form.image.data:
            if allowed_file(form.image.data.filename, app.config['ALLOWED_EXTENSIONS']):
                # Delete old image if exists and not the default
                if news.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], news.image_path)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], news.image_path))
                
                news.image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'], 'news')
            else:
                flash('Invalid file format. Allowed formats: png, jpg, jpeg, gif', 'danger')
                return render_template('admin/news_form.html', form=form, title="Edit News")
        
        db.session.commit()
        flash('News updated successfully!', 'success')
        return redirect(url_for('admin_news'))
    
    return render_template('admin/news_form.html', form=form, title="Edit News")

@app.route('/admin/news/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_news(id):
    news = News.query.get_or_404(id)
    
    # Delete image file if exists
    if news.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], news.image_path)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], news.image_path))
    
    db.session.delete(news)
    db.session.commit()
    flash('News deleted successfully!', 'success')
    return redirect(url_for('admin_news'))

# Events Management
@app.route('/admin/events')
@login_required
def admin_events():
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template('admin/events_manage.html', events=events)

@app.route('/admin/events/add', methods=['GET', 'POST'])
@login_required
def admin_add_event():
    form = EventForm()
    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            if allowed_file(form.image.data.filename, app.config['ALLOWED_EXTENSIONS']):
                image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'], 'events')
            else:
                flash('Invalid file format. Allowed formats: png, jpg, jpeg, gif', 'danger')
                return render_template('admin/event_form.html', form=form, title="Add Event")
        
        event = Event(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            time=form.time.data,
            location=form.location.data,
            image_path=image_path
        )
        db.session.add(event)
        db.session.commit()
        flash('Event added successfully!', 'success')
        return redirect(url_for('admin_events'))
    
    return render_template('admin/event_form.html', form=form, title="Add Event")

@app.route('/admin/events/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_event(id):
    event = Event.query.get_or_404(id)
    form = EventForm(obj=event)
    
    if form.validate_on_submit():
        event.title = form.title.data
        event.description = form.description.data
        event.date = form.date.data
        event.time = form.time.data
        event.location = form.location.data
        
        if form.image.data:
            if allowed_file(form.image.data.filename, app.config['ALLOWED_EXTENSIONS']):
                # Delete old image if exists
                if event.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], event.image_path)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], event.image_path))
                
                event.image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'], 'events')
            else:
                flash('Invalid file format. Allowed formats: png, jpg, jpeg, gif', 'danger')
                return render_template('admin/event_form.html', form=form, title="Edit Event")
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin_events'))
    
    return render_template('admin/event_form.html', form=form, title="Edit Event")

@app.route('/admin/events/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_event(id):
    event = Event.query.get_or_404(id)
    
    # Delete image file if exists
    if event.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], event.image_path)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], event.image_path))
    
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin_events'))

# Gallery Management
@app.route('/admin/gallery')
@login_required
def admin_gallery():
    images = GalleryImage.query.order_by(GalleryImage.upload_date.desc()).all()
    return render_template('admin/gallery_manage.html', images=images)

@app.route('/admin/gallery/upload', methods=['GET', 'POST'])
@login_required
def admin_upload_gallery():
    form = GalleryUploadForm()
    if form.validate_on_submit():
        files = request.files.getlist('images')
        
        for file in files:
            if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
                image_path = save_file(file, app.config['UPLOAD_FOLDER'], 'gallery')
                
                gallery_image = GalleryImage(
                    title=form.title.data,
                    caption=form.caption.data,
                    image_path=image_path,
                    upload_date=datetime.now()
                )
                db.session.add(gallery_image)
            else:
                flash(f'Invalid file format for {file.filename}. Allowed formats: png, jpg, jpeg, gif', 'danger')
        
        db.session.commit()
        flash('Images uploaded successfully!', 'success')
        return redirect(url_for('admin_gallery'))
    
    return render_template('admin/gallery_upload.html', form=form)

@app.route('/admin/gallery/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_gallery(id):
    image = GalleryImage.query.get_or_404(id)
    
    # Delete image file if exists
    if image.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], image.image_path)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.image_path))
    
    db.session.delete(image)
    db.session.commit()
    flash('Image deleted successfully!', 'success')
    return redirect(url_for('admin_gallery'))

# About Section Management
@app.route('/admin/about')
@login_required
def admin_about():
    sections = AboutSection.query.order_by(AboutSection.order).all()
    return render_template('admin/about_manage.html', sections=sections)

@app.route('/admin/about/add', methods=['GET', 'POST'])
@login_required
def admin_add_about():
    form = AboutSectionForm()
    if form.validate_on_submit():
        section = AboutSection(
            title=form.title.data,
            content=form.content.data,
            order=form.order.data
        )
        db.session.add(section)
        db.session.commit()
        flash('About section added successfully!', 'success')
        return redirect(url_for('admin_about'))
    
    return render_template('admin/about_form.html', form=form, title="Add About Section")

@app.route('/admin/about/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_about(id):
    section = AboutSection.query.get_or_404(id)
    form = AboutSectionForm(obj=section)
    
    if form.validate_on_submit():
        section.title = form.title.data
        section.content = form.content.data
        section.order = form.order.data
        
        db.session.commit()
        flash('About section updated successfully!', 'success')
        return redirect(url_for('admin_about'))
    
    return render_template('admin/about_form.html', form=form, title="Edit About Section")

@app.route('/admin/about/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_about(id):
    section = AboutSection.query.get_or_404(id)
    db.session.delete(section)
    db.session.commit()
    flash('About section deleted successfully!', 'success')
    return redirect(url_for('admin_about'))

# Academic Programs Management
@app.route('/admin/academics')
@login_required
def admin_academics():
    programs = AcademicProgram.query.order_by(AcademicProgram.order).all()
    return render_template('admin/academics_manage.html', programs=programs)

@app.route('/admin/academics/add', methods=['GET', 'POST'])
@login_required
def admin_add_academic():
    form = AcademicProgramForm()
    if form.validate_on_submit():
        program = AcademicProgram(
            title=form.title.data,
            description=form.description.data,
            order=form.order.data
        )
        db.session.add(program)
        db.session.commit()
        flash('Academic program added successfully!', 'success')
        return redirect(url_for('admin_academics'))
    
    return render_template('admin/academic_form.html', form=form, title="Add Academic Program")

@app.route('/admin/academics/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_academic(id):
    program = AcademicProgram.query.get_or_404(id)
    form = AcademicProgramForm(obj=program)
    
    if form.validate_on_submit():
        program.title = form.title.data
        program.description = form.description.data
        program.order = form.order.data
        
        db.session.commit()
        flash('Academic program updated successfully!', 'success')
        return redirect(url_for('admin_academics'))
    
    return render_template('admin/academic_form.html', form=form, title="Edit Academic Program")

@app.route('/admin/academics/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_academic(id):
    program = AcademicProgram.query.get_or_404(id)
    db.session.delete(program)
    db.session.commit()
    flash('Academic program deleted successfully!', 'success')
    return redirect(url_for('admin_academics'))

# Contacts Management
@app.route('/admin/contacts')
@login_required
def admin_contacts():
    contacts = Contact.query.order_by(Contact.date.desc()).all()
    return render_template('admin/contacts_manage.html', contacts=contacts)

@app.route('/admin/contacts/view/<int:id>')
@login_required
def admin_view_contact(id):
    contact = Contact.query.get_or_404(id)
    return render_template('admin/contact_view.html', contact=contact)

@app.route('/admin/contacts/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact message deleted successfully!', 'success')
    return redirect(url_for('admin_contacts'))

# School Settings
@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    settings = SchoolSetting.query.first()
    form = SchoolSettingsForm(obj=settings)
    
    if form.validate_on_submit():
        settings.school_name = form.school_name.data
        settings.school_address = form.school_address.data
        settings.school_phone = form.school_phone.data
        settings.school_email = form.school_email.data
        
        if form.school_logo.data:
            if allowed_file(form.school_logo.data.filename, app.config['ALLOWED_EXTENSIONS']):
                # Delete old logo if exists and not the default
                if settings.school_logo_path and settings.school_logo_path != 'IMG-20250425-WA0004.jpg' and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], settings.school_logo_path)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], settings.school_logo_path))
                
                settings.school_logo_path = save_file(form.school_logo.data, app.config['UPLOAD_FOLDER'], 'logo')
            else:
                flash('Invalid file format for logo. Allowed formats: png, jpg, jpeg, gif', 'danger')
        
        db.session.commit()
        flash('School settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin/settings.html', form=form)

# User Management
@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    users = User.query.all()
    return render_template('admin/users_manage.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    form = UserForm()
    if form.validate_on_submit():
        from werkzeug.security import generate_password_hash
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            is_admin=form.is_admin.data
        )
        db.session.add(user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/user_form.html', form=form, title="Add User")

@app.route('/admin/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    
    # Don't require password on edit
    form.password.validators = []
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        
        if form.password.data:
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash(form.password.data)
        
        user.is_admin = form.is_admin.data
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    # Don't show password field value
    form.password.data = ''
    
    return render_template('admin/user_form.html', form=form, title="Edit User")

@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_user(id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    user = User.query.get_or_404(id)
    
    # Prevent deleting your own account
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_users'))

# User Profile
@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        if form.new_password.data:
            from werkzeug.security import generate_password_hash, check_password_hash
            
            if not check_password_hash(current_user.password_hash, form.current_password.data):
                flash('Current password is incorrect', 'danger')
                return render_template('admin/profile.html', form=form)
            
            current_user.password_hash = generate_password_hash(form.new_password.data)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('admin_profile'))
    
    return render_template('admin/profile.html', form=form)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
