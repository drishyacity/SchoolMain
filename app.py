import os
import io
import json
import logging
from datetime import datetime, timedelta
from PIL import Image
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import uuid
import database
from database import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize database
database.init_app(app)

# File upload settings
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access the admin panel.'

from models import User, News, Event, GalleryImage, Contact, AboutSection, AcademicProgram, SchoolSetting, \
    Teacher, Facility, Syllabus, AdmissionForm, HomeSlider
from forms import LoginForm, NewsForm, EventForm, GalleryUploadForm, ContactForm, AboutSectionForm, AcademicProgramForm, \
    SchoolSettingsForm, UserForm, ProfileForm, TeacherForm, FacilityForm, SyllabusForm, AdmissionApplicationForm, HomeSliderForm, AdmissionResponseForm
from utils import allowed_file, save_file

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database tables and default data
def init_db():
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
    home_sliders = HomeSlider.query.filter_by(active=True).order_by(HomeSlider.order).all()
    # Getting a list of available slider images in the static folder
    image_paths = []
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        if file.startswith('IMG-') and file.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            image_paths.append(file)
    return render_template('index.html', settings=settings, news_items=news_items, events=events,
                           home_sliders=home_sliders, images_list=image_paths)

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

@app.route('/teachers')
def teachers():
    settings = SchoolSetting.query.first()
    teachers_list = Teacher.query.order_by(Teacher.order).all()

    # Debug: Print teacher image paths
    for teacher in teachers_list:
        print(f"Teacher: {teacher.name}, Image Path: {teacher.image_path}")
        if teacher.image_path:
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], teacher.image_path)
            print(f"Full path: {full_path}, Exists: {os.path.exists(full_path)}")
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                print(f"File size: {file_size} bytes")
            else:
                print("❌ File does not exist!")

    return render_template('teachers.html', settings=settings, teachers=teachers_list)

@app.route('/debug/images')
def debug_images():
    """Debug route to check all teacher images"""
    teachers_list = Teacher.query.all()
    debug_info = []

    for teacher in teachers_list:
        info = {
            'name': teacher.name,
            'image_path': teacher.image_path,
            'exists': False,
            'size': 0,
            'full_path': ''
        }

        if teacher.image_path:
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], teacher.image_path)
            info['full_path'] = full_path
            info['exists'] = os.path.exists(full_path)
            if info['exists']:
                info['size'] = os.path.getsize(full_path)

        debug_info.append(info)

    return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"

@app.route('/test/image/<filename>')
def test_image(filename):
    """Test route to directly serve an image"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return f"File not found: {file_path}", 404
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/test/upload', methods=['GET', 'POST'])
def test_upload():
    """Simple test upload route"""
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded', 400

        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400

        try:
            from utils import save_file
            filename = save_file(file, app.config['UPLOAD_FOLDER'])
            return f'File uploaded successfully: {filename}<br><a href="/test/image/{filename}">View Image</a>'
        except Exception as e:
            return f'Upload failed: {str(e)}', 500

    return '''
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept="image/*" required>
        <button type="submit">Upload Test Image</button>
    </form>
    '''

@app.route('/facilities')
def facilities():
    settings = SchoolSetting.query.first()
    facilities_list = Facility.query.order_by(Facility.order).all()
    return render_template('facilities.html', settings=settings, facilities=facilities_list)

@app.route('/syllabus')
def syllabus():
    settings = SchoolSetting.query.first()
    syllabus_list = Syllabus.query.order_by(Syllabus.class_name, Syllabus.subject).all()
    return render_template('syllabus.html', settings=settings, syllabus_list=syllabus_list)

@app.route('/admission', methods=['GET', 'POST'])
def admission():
    settings = SchoolSetting.query.first()
    form = AdmissionApplicationForm()

    if form.validate_on_submit():
        admission_application = AdmissionForm(
            student_name=form.student_name.data,
            parent_name=form.parent_name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            class_applying=form.class_applying.data,
            previous_school=form.previous_school.data,
            date_of_birth=form.date_of_birth.data,
            submission_date=datetime.now(),
            status='Pending'
        )
        db.session.add(admission_application)
        db.session.commit()
        flash('Your admission application has been submitted successfully!', 'success')
        return redirect(url_for('admission'))

    return render_template('admission.html', settings=settings, form=form)

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
@app.route('/gallery/page/<int:page>')
def gallery(page=1):
    settings = SchoolSetting.query.first()
    per_page = 12  # Number of images per page
    images = GalleryImage.query.order_by(GalleryImage.upload_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
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
                # Save the file directly to the uploads folder
                image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'])
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

                news.image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'])
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
                # Save the file directly to the uploads folder
                image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'])
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

                event.image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'])
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
@app.route('/admin/gallery/page/<int:page>')
@login_required
def admin_gallery(page=1):
    per_page = 16  # Number of images per page
    images = GalleryImage.query.order_by(GalleryImage.upload_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/gallery_manage.html', images=images)

@app.route('/admin/gallery/upload', methods=['GET', 'POST'])
@login_required
def admin_upload_gallery():
    form = GalleryUploadForm()

    if request.method == 'POST':
        try:
            # Get the files from the form
            files = request.files.getlist('images')

            if not files or not files[0].filename:
                flash('No files selected for upload.', 'danger')
                return render_template('admin/gallery_upload.html', form=form)

            # Process each file
            for file in files:
                if not file.filename:
                    continue

                # Read the file data
                file_data = file.read()

                if len(file_data) == 0:
                    flash(f'Error: File {file.filename} is empty!', 'danger')
                    continue

                # Get the MIME type
                mimetype = file.content_type or 'image/jpeg'

                # Create a new gallery image entry
                gallery_image = GalleryImage(
                    title=form.title.data or "Uploaded Image",
                    caption=form.caption.data or "",
                    image_data=file_data,
                    image_filename=file.filename,
                    image_mimetype=mimetype,
                    upload_date=datetime.now()
                )

                # Add to database
                db.session.add(gallery_image)

            # Commit all changes to the database
            db.session.commit()
            flash('Images uploaded successfully!', 'success')
            return redirect(url_for('admin_gallery'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading images: {str(e)}', 'danger')
            print(f"Error uploading images: {str(e)}")
            return render_template('admin/gallery_upload.html', form=form)

    return render_template('admin/gallery_upload.html', form=form)

@app.route('/admin/gallery/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_gallery(id):
    image = GalleryImage.query.get_or_404(id)

    # No need to delete files since images are stored in the database
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

                settings.school_logo_path = save_file(form.school_logo.data, app.config['UPLOAD_FOLDER'])
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

# Teacher Management
@app.route('/admin/teachers')
@login_required
def admin_teachers():
    teachers_list = Teacher.query.order_by(Teacher.order).all()
    return render_template('admin/teachers_manage.html', teachers=teachers_list)

@app.route('/admin/teachers/add', methods=['GET', 'POST'])
@login_required
def admin_add_teacher():
    form = TeacherForm()

    # Set default position type based on query parameter
    position_type = request.args.get('type', 'teaching')
    if position_type == 'leadership':
        form.position_type.data = 'leadership'
        title = "Add Principal/Director"
    else:
        form.position_type.data = 'teaching'
        title = "Add Teacher"

    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            if allowed_file(form.image.data.filename, app.config['ALLOWED_EXTENSIONS']):
                # Get position type for proper cropping
                position_type = form.position_type.data

                # Get crop data from form if available
                crop_data_json = request.form.get('crop_data')
                if crop_data_json:
                    # Use the crop data from the form
                    crop_data = crop_data_json
                else:
                    # Fallback to basic position type data
                    crop_data = json.dumps({"positionType": position_type})

                image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'], crop_data)
            else:
                flash('Invalid file format. Allowed formats: png, jpg, jpeg, gif', 'danger')
                return render_template('admin/teacher_form.html', form=form, title=title)

        teacher = Teacher(
            name=form.name.data,
            position_type=form.position_type.data,
            position=form.position.data,
            qualification=form.qualification.data,
            bio=form.bio.data,
            image_path=image_path,
            order=form.order.data
        )
        db.session.add(teacher)
        db.session.commit()

        if form.position_type.data == 'leadership':
            flash('Leadership staff added successfully!', 'success')
            return redirect(url_for('admin_teachers') + '#leadership')
        else:
            flash('Teacher added successfully!', 'success')
            return redirect(url_for('admin_teachers') + '#teachers')

    return render_template('admin/teacher_form.html', form=form, title=title)

@app.route('/admin/teachers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    form = TeacherForm(obj=teacher)

    # Set title based on position type
    if teacher.position_type == 'leadership' or teacher.position in ['Principal', 'Director', 'Chairman', 'Vice Principal', 'Head of School']:
        title = f"Edit {teacher.position}"
    else:
        title = "Edit Teacher"

    if form.validate_on_submit():
        teacher.name = form.name.data
        teacher.position_type = form.position_type.data
        teacher.position = form.position.data
        teacher.qualification = form.qualification.data
        teacher.bio = form.bio.data
        teacher.order = form.order.data

        if form.image.data:
            if allowed_file(form.image.data.filename, app.config['ALLOWED_EXTENSIONS']):
                # Delete old image if exists
                if teacher.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], teacher.image_path)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], teacher.image_path))

                # Get position type for proper cropping
                position_type = form.position_type.data

                # Get crop data from form if available
                crop_data_json = request.form.get('crop_data')
                if crop_data_json:
                    # Use the crop data from the form
                    crop_data = crop_data_json
                else:
                    # Fallback to basic position type data
                    crop_data = json.dumps({"positionType": position_type})

                teacher.image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'], crop_data)
            else:
                flash('Invalid file format. Allowed formats: png, jpg, jpeg, gif', 'danger')
                return render_template('admin/teacher_form.html', form=form, title=title)

        db.session.commit()

        if form.position_type.data == 'leadership':
            flash('Leadership staff updated successfully!', 'success')
            return redirect(url_for('admin_teachers') + '#leadership')
        else:
            flash('Teacher updated successfully!', 'success')
            return redirect(url_for('admin_teachers') + '#teachers')

    return render_template('admin/teacher_form.html', form=form, title=title)

@app.route('/admin/teachers/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_teacher(id):
    teacher = Teacher.query.get_or_404(id)

    # Check if it's a leadership position
    is_leadership = teacher.position_type == 'leadership' or teacher.position in ['Principal', 'Director', 'Chairman', 'Vice Principal', 'Head of School']

    # Delete image file if exists
    if teacher.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], teacher.image_path)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], teacher.image_path))

    db.session.delete(teacher)
    db.session.commit()

    if is_leadership:
        flash('Leadership staff deleted successfully!', 'success')
        return redirect(url_for('admin_teachers') + '#leadership')
    else:
        flash('Teacher deleted successfully!', 'success')
        return redirect(url_for('admin_teachers') + '#teachers')

# Facilities Management
@app.route('/admin/facilities')
@login_required
def admin_facilities():
    facilities_list = Facility.query.order_by(Facility.order).all()
    return render_template('admin/facilities_manage.html', facilities=facilities_list)

@app.route('/admin/facilities/add', methods=['GET', 'POST'])
@login_required
def admin_add_facility():
    form = FacilityForm()
    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            if allowed_file(form.image.data.filename, app.config['ALLOWED_EXTENSIONS']):
                image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'])
            else:
                flash('Invalid file format. Allowed formats: png, jpg, jpeg, gif', 'danger')
                return render_template('admin/facility_form.html', form=form, title="Add Facility")

        facility = Facility(
            title=form.title.data,
            description=form.description.data,
            image_path=image_path,
            order=form.order.data
        )
        db.session.add(facility)
        db.session.commit()
        flash('Facility added successfully!', 'success')
        return redirect(url_for('admin_facilities'))

    return render_template('admin/facility_form.html', form=form, title="Add Facility")

@app.route('/admin/facilities/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_facility(id):
    facility = Facility.query.get_or_404(id)
    form = FacilityForm(obj=facility)

    if form.validate_on_submit():
        facility.title = form.title.data
        facility.description = form.description.data
        facility.order = form.order.data

        if form.image.data:
            if allowed_file(form.image.data.filename, app.config['ALLOWED_EXTENSIONS']):
                # Delete old image if exists
                if facility.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], facility.image_path)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], facility.image_path))

                facility.image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'])
            else:
                flash('Invalid file format. Allowed formats: png, jpg, jpeg, gif', 'danger')
                return render_template('admin/facility_form.html', form=form, title="Edit Facility")

        db.session.commit()
        flash('Facility updated successfully!', 'success')
        return redirect(url_for('admin_facilities'))

    return render_template('admin/facility_form.html', form=form, title="Edit Facility")

@app.route('/admin/facilities/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_facility(id):
    facility = Facility.query.get_or_404(id)

    # Delete image file if exists
    if facility.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], facility.image_path)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], facility.image_path))

    db.session.delete(facility)
    db.session.commit()
    flash('Facility deleted successfully!', 'success')
    return redirect(url_for('admin_facilities'))

# Syllabus Management
@app.route('/admin/syllabus')
@login_required
def admin_syllabus():
    syllabus_list = Syllabus.query.order_by(Syllabus.class_name, Syllabus.subject).all()
    return render_template('admin/syllabus_manage.html', syllabus_list=syllabus_list)

@app.route('/admin/syllabus/add', methods=['GET', 'POST'])
@login_required
def admin_add_syllabus():
    form = SyllabusForm()
    if form.validate_on_submit():
        file_path = None
        if form.file.data:
            if allowed_file(form.file.data.filename, ['pdf']):
                file_path = save_file(form.file.data, app.config['UPLOAD_FOLDER'])
            else:
                flash('Invalid file format. Only PDF files allowed.', 'danger')
                return render_template('admin/syllabus_form.html', form=form, title="Add Syllabus")

        syllabus = Syllabus(
            class_name=form.class_name.data,
            subject=form.subject.data,
            description=form.description.data,
            file_path=file_path,
            order=form.order.data
        )
        db.session.add(syllabus)
        db.session.commit()
        flash('Syllabus added successfully!', 'success')
        return redirect(url_for('admin_syllabus'))

    return render_template('admin/syllabus_form.html', form=form, title="Add Syllabus")

@app.route('/admin/syllabus/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_syllabus(id):
    syllabus = Syllabus.query.get_or_404(id)
    form = SyllabusForm(obj=syllabus)

    if form.validate_on_submit():
        syllabus.class_name = form.class_name.data
        syllabus.subject = form.subject.data
        syllabus.description = form.description.data
        syllabus.order = form.order.data

        if form.file.data:
            if allowed_file(form.file.data.filename, ['pdf']):
                # Delete old file if exists
                if syllabus.file_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], syllabus.file_path)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], syllabus.file_path))

                syllabus.file_path = save_file(form.file.data, app.config['UPLOAD_FOLDER'])
            else:
                flash('Invalid file format. Only PDF files allowed.', 'danger')
                return render_template('admin/syllabus_form.html', form=form, title="Edit Syllabus")

        db.session.commit()
        flash('Syllabus updated successfully!', 'success')
        return redirect(url_for('admin_syllabus'))

    return render_template('admin/syllabus_form.html', form=form, title="Edit Syllabus")

@app.route('/admin/syllabus/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_syllabus(id):
    syllabus = Syllabus.query.get_or_404(id)

    # Delete file if exists
    if syllabus.file_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], syllabus.file_path)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], syllabus.file_path))

    db.session.delete(syllabus)
    db.session.commit()
    flash('Syllabus deleted successfully!', 'success')
    return redirect(url_for('admin_syllabus'))

# Admission Applications Management
@app.route('/admin/admission-applications')
@login_required
def admin_admission_applications():
    applications = AdmissionForm.query.order_by(AdmissionForm.submission_date.desc()).all()
    return render_template('admin/admission_applications.html', applications=applications)

@app.route('/admin/admission-applications/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_view_application(id):
    application = AdmissionForm.query.get_or_404(id)
    form = AdmissionResponseForm(obj=application)

    if form.validate_on_submit():
        application.status = form.status.data
        application.comments = form.comments.data
        db.session.commit()
        flash('Application status updated successfully!', 'success')
        return redirect(url_for('admin_admission_applications'))

    return render_template('admin/admission_application_detail.html', application=application, form=form)

# Home Slider Management
@app.route('/admin/home-slider')
@login_required
def admin_home_slider():
    sliders = HomeSlider.query.order_by(HomeSlider.order).all()
    return render_template('admin/home_slider_manage.html', sliders=sliders)

@app.route('/admin/home-slider/add', methods=['GET', 'POST'])
@login_required
def admin_add_home_slider():
    form = HomeSliderForm()
    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            if allowed_file(form.image.data.filename, app.config['ALLOWED_EXTENSIONS']):
                image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'])
            else:
                flash('Invalid file format. Allowed formats: png, jpg, jpeg, gif', 'danger')
                return render_template('admin/home_slider_form.html', form=form, title="Add Slider Image")
        else:
            flash('Please select an image to upload', 'danger')
            return render_template('admin/home_slider_form.html', form=form, title="Add Slider Image")

        slider = HomeSlider(
            title=form.title.data,
            image_path=image_path,
            order=form.order.data,
            active=form.active.data
        )
        db.session.add(slider)
        db.session.commit()
        flash('Slider image added successfully!', 'success')
        return redirect(url_for('admin_home_slider'))

    return render_template('admin/home_slider_form.html', form=form, title="Add Slider Image")

@app.route('/admin/home-slider/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_home_slider(id):
    slider = HomeSlider.query.get_or_404(id)
    form = HomeSliderForm(obj=slider)

    if form.validate_on_submit():
        slider.title = form.title.data
        slider.order = form.order.data
        slider.active = form.active.data

        if form.image.data:
            if allowed_file(form.image.data.filename, app.config['ALLOWED_EXTENSIONS']):
                # Delete old image if exists
                if slider.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], slider.image_path)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], slider.image_path))

                slider.image_path = save_file(form.image.data, app.config['UPLOAD_FOLDER'])
            else:
                flash('Invalid file format. Allowed formats: png, jpg, jpeg, gif', 'danger')
                return render_template('admin/home_slider_form.html', form=form, title="Edit Slider Image")

        db.session.commit()
        flash('Slider image updated successfully!', 'success')
        return redirect(url_for('admin_home_slider'))

    return render_template('admin/home_slider_form.html', form=form, title="Edit Slider Image")

@app.route('/admin/home-slider/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_home_slider(id):
    slider = HomeSlider.query.get_or_404(id)

    # Delete image file if exists
    if slider.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], slider.image_path)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], slider.image_path))

    db.session.delete(slider)
    db.session.commit()
    flash('Slider image deleted successfully!', 'success')
    return redirect(url_for('admin_home_slider'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Route to serve images directly from the database with caching
@app.route('/gallery/image/<int:image_id>')
def get_gallery_image(image_id):
    image = GalleryImage.query.get_or_404(image_id)

    # Create a response with the image data
    response = send_file(
        io.BytesIO(image.image_data),
        mimetype=image.image_mimetype,
        as_attachment=False,
        download_name=image.image_filename
    )

    # Add cache headers (cache for 1 day = 86400 seconds)
    response.headers['Cache-Control'] = 'public, max-age=86400'
    response.headers['Expires'] = (datetime.now() + timedelta(days=1)).strftime('%a, %d %b %Y %H:%M:%S GMT')

    return response

# Test route to check database contents
@app.route('/test/gallery')
def test_gallery():
    images = GalleryImage.query.all()
    result = "<h1>Gallery Images in Database</h1>"
    result += f"<p>Total images: {len(images)}</p>"
    result += "<ul>"
    for img in images:
        result += f"<li>ID: {img.id}, Title: {img.title}, Filename: {img.image_filename}, Size: {len(img.image_data) if img.image_data else 0} bytes</li>"
    result += "</ul>"

    # Add image previews
    result += "<h2>Image Previews</h2>"
    for img in images:
        result += f'<div style="margin-bottom: 20px;"><h3>{img.title}</h3>'
        result += f'<img src="/gallery/image/{img.id}" alt="{img.title}" style="max-width: 300px;"><br>'
        result += f'<small>Filename: {img.image_filename}, Size: {len(img.image_data) if img.image_data else 0} bytes</small></div>'

    return result

# Route to check database tables
@app.route('/test/db')
def test_db():
    result = "<h1>Database Tables</h1>"

    # Get all table names
    tables = db.engine.table_names()

    result += "<h2>Tables in Database</h2>"
    result += "<ul>"
    for table in tables:
        result += f"<li>{table}</li>"
    result += "</ul>"

    # Check if gallery_images table exists
    if 'gallery_images' in tables:
        result += "<h2>Gallery Images Table Structure</h2>"

        # Get table structure
        inspector = db.inspect(db.engine)
        columns = inspector.get_columns('gallery_images')

        result += "<table border='1'><tr><th>Column</th><th>Type</th></tr>"
        for column in columns:
            result += f"<tr><td>{column['name']}</td><td>{column['type']}</td></tr>"
        result += "</table>"
    else:
        result += "<p>gallery_images table does not exist!</p>"

    return result

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
