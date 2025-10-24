import os
try:
    from dotenv import load_dotenv, find_dotenv
except Exception:
    load_dotenv = None
    find_dotenv = None
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

# Load environment variables from .env (search up the directory tree) if dotenv is available
if load_dotenv and find_dotenv:
    try:
        load_dotenv(find_dotenv())
    except Exception:
        pass

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

# Do not create folders on serverless (read-only) environments like Vercel
# Only create locally when not running on Vercel
if not os.environ.get('VERCEL') and not os.environ.get('READ_ONLY_FS'):
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except Exception:
        pass

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access the admin panel.'

from models import User, News, Event, GalleryImage, Contact, AboutSection, AcademicProgram, SchoolSetting, \
    Teacher, Facility, Syllabus, AdmissionForm, HomeSlider, StoredFile, AdmissionInfo, AchievementsPage, AchievementsItem, \
    AdmissionEligibilityItem, AdmissionDocumentItem, AdmissionImportantDateItem, AdmissionFormField
from forms import LoginForm, NewsForm, EventForm, GalleryUploadForm, ContactForm, AboutSectionForm, AcademicProgramForm, \
    SchoolSettingsForm, UserForm, ProfileForm, TeacherForm, FacilityForm, SyllabusForm, AdmissionApplicationForm, HomeSliderForm, AdmissionResponseForm, AdmissionInfoForm, AchievementsForm, AchievementsItemForm, AdmissionFormFieldForm
from utils import allowed_file, save_file, delete_storage_url

def delete_db_path_if_needed(path_str):
    if not path_str or not isinstance(path_str, str):
        return
    # Delete DB-stored file if using internal /files/<id>
    if path_str.startswith('/files/'):
        try:
            file_id = int(path_str.rsplit('/', 1)[-1])
            sf = StoredFile.query.get(file_id)
            if sf:
                db.session.delete(sf)
                db.session.commit()
        except Exception:
            pass
    # Delete Supabase storage object if URL points to public object
    if '/storage/v1/object/public/' in path_str:
        try:
            delete_storage_url(path_str)
        except Exception:
            pass

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database tables and default data
def init_db():
    with app.app_context():
        db.create_all()

        # Lightweight migrations for admission_info new columns
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            if 'admission_info' in tables:
                cols = [c['name'] for c in inspector.get_columns('admission_info')]
                from sqlalchemy import text as _sql_text
                with db.engine.begin() as conn:
                    if 'intro_text' not in cols:
                        conn.execute(_sql_text("ALTER TABLE admission_info ADD COLUMN intro_text TEXT"))
                    if 'important_dates_text' not in cols:
                        conn.execute(_sql_text("ALTER TABLE admission_info ADD COLUMN important_dates_text TEXT"))
            if 'admission_form_fields' in tables:
                cols2 = [c['name'] for c in inspector.get_columns('admission_form_fields')]
                from sqlalchemy import text as _sql_text2
                with db.engine.begin() as conn2:
                    if 'placeholder' not in cols2:
                        conn2.execute(_sql_text2("ALTER TABLE admission_form_fields ADD COLUMN placeholder VARCHAR(255)"))
            if 'school_settings' in tables:
                cols3 = [c['name'] for c in inspector.get_columns('school_settings')]
                from sqlalchemy import text as _sql_text3
                with db.engine.begin() as conn3:
                    if 'map_embed_html' not in cols3:
                        conn3.execute(_sql_text3("ALTER TABLE school_settings ADD COLUMN map_embed_html TEXT"))
            if 'teachers' in tables:
                cols4 = [c['name'] for c in inspector.get_columns('teachers')]
                from sqlalchemy import text as _sql_text4
                with db.engine.begin() as conn4:
                    if 'experience' not in cols4:
                        conn4.execute(_sql_text4("ALTER TABLE teachers ADD COLUMN experience VARCHAR(100)"))
                    if 'subject' not in cols4:
                        conn4.execute(_sql_text4("ALTER TABLE teachers ADD COLUMN subject VARCHAR(100)"))
            # School settings social links
            if 'school_settings' in tables:
                colsS = [c['name'] for c in inspector.get_columns('school_settings')]
                from sqlalchemy import text as _sql_textS
                with db.engine.begin() as connS:
                    if 'social_facebook_url' not in colsS:
                        connS.execute(_sql_textS("ALTER TABLE school_settings ADD COLUMN social_facebook_url VARCHAR(255)"))
                    if 'social_twitter_url' not in colsS:
                        connS.execute(_sql_textS("ALTER TABLE school_settings ADD COLUMN social_twitter_url VARCHAR(255)"))
                    if 'social_instagram_url' not in colsS:
                        connS.execute(_sql_textS("ALTER TABLE school_settings ADD COLUMN social_instagram_url VARCHAR(255)"))
                    if 'social_linkedin_url' not in colsS:
                        connS.execute(_sql_textS("ALTER TABLE school_settings ADD COLUMN social_linkedin_url VARCHAR(255)"))
            # Gallery migrations: add dimensions and ratio category
            if 'gallery_images' in tables:
                cols5 = [c['name'] for c in inspector.get_columns('gallery_images')]
                from sqlalchemy import text as _sql_text5
                with db.engine.begin() as conn5:
                    if 'width' not in cols5:
                        conn5.execute(_sql_text5("ALTER TABLE gallery_images ADD COLUMN width INTEGER"))
                    if 'height' not in cols5:
                        conn5.execute(_sql_text5("ALTER TABLE gallery_images ADD COLUMN height INTEGER"))
                    if 'ratio_category' not in cols5:
                        conn5.execute(_sql_text5("ALTER TABLE gallery_images ADD COLUMN ratio_category VARCHAR(20)"))
            # Contacts migration: add phone column
            if 'contacts' in tables:
                cols6 = [c['name'] for c in inspector.get_columns('contacts')]
                from sqlalchemy import text as _sql_text6
                with db.engine.begin() as conn6:
                    if 'phone' not in cols6:
                        conn6.execute(_sql_text6("ALTER TABLE contacts ADD COLUMN phone VARCHAR(20)"))
        except Exception:
            # Ignore migration errors so app can still start; admin page may fail until DB is aligned
            pass

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
    # Use DB-backed image paths for sliders instead of local filesystem
    images_list = [s.image_path for s in home_sliders if getattr(s, 'image_path', None)]
    try:
        logging.info(f"Home sliders count: {len(home_sliders)}")
        for i, s in enumerate(home_sliders, start=1):
            logging.info(f"Slider[{i}] id={getattr(s, 'id', None)} path={getattr(s, 'image_path', None)}")
    except Exception:
        pass
    return render_template('index.html', settings=settings, news_items=news_items, events=events,
                           home_sliders=home_sliders, images_list=images_list)

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
    teachers_list = Teacher.query.order_by(Teacher.order, Teacher.id).all()

    # Strict categorization by position_type only
    leadership = [t for t in teachers_list if ((t.position_type or '').strip().lower() == 'leadership')]
    teaching = [t for t in teachers_list if ((t.position_type or '').strip().lower() == 'teaching')]

    return render_template('teachers.html', settings=settings, teachers=teachers_list, leadership=leadership, teaching=teaching)

 

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
    admission_info = AdmissionInfo.query.first()
    eligibility_items = AdmissionEligibilityItem.query.order_by(AdmissionEligibilityItem.order, AdmissionEligibilityItem.id).all()
    document_items = AdmissionDocumentItem.query.order_by(AdmissionDocumentItem.order, AdmissionDocumentItem.id).all()
    date_items = AdmissionImportantDateItem.query.order_by(AdmissionImportantDateItem.order, AdmissionImportantDateItem.id).all()
    form_fields = AdmissionFormField.query.order_by(AdmissionFormField.order, AdmissionFormField.id).all()
    field_map = {f.name: f for f in form_fields}
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

    return render_template('admission.html', settings=settings, form=form, admission_info=admission_info,
                           eligibility_items=eligibility_items, document_items=document_items, date_items=date_items,
                           form_fields=form_fields, field_map=field_map)

@app.route('/events')
def events():
    settings = SchoolSetting.query.first()
    upcoming_events = Event.query.filter(Event.date >= datetime.now()).order_by(Event.date).all()
    past_events = Event.query.filter(Event.date < datetime.now()).order_by(Event.date.desc()).all()
    return render_template('events.html', settings=settings, upcoming_events=upcoming_events, past_events=past_events)

@app.route('/achievements')
def achievements():
    settings = SchoolSetting.query.first()
    page = AchievementsPage.query.first()
    items = AchievementsItem.query.order_by(AchievementsItem.category, AchievementsItem.order, AchievementsItem.created_at).all()
    return render_template('achievements.html', settings=settings, page=page, items=items)

@app.route('/gallery')
def gallery():
    settings = SchoolSetting.query.first()
    all_images = GalleryImage.query.order_by(GalleryImage.upload_date.desc()).all()

    # Group by ratio_category; compute on the fly if missing
    squares = []
    three_four = []
    portraits = []
    landscapes = []

    for img in all_images:
        cat = getattr(img, 'ratio_category', None)
        w = getattr(img, 'width', None)
        h = getattr(img, 'height', None)
        if not cat and w and h and h != 0:
            ratio = w / float(h)
            def approx(a, b, tol=0.05):
                return abs(a - b) <= tol
            if approx(ratio, 1.0):
                cat = 'square'
            elif approx(ratio, 3/4):
                cat = 'three_four'
            elif ratio < 1.0:
                cat = 'portrait'
            else:
                cat = 'landscape'

        if cat == 'square':
            squares.append(img)
        elif cat == 'three_four':
            three_four.append(img)
        elif cat == 'portrait':
            portraits.append(img)
        else:
            landscapes.append(img)

    return render_template('gallery.html', settings=settings, squares=squares, three_four=three_four, portraits=portraits, landscapes=landscapes)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    settings = SchoolSetting.query.first()
    form = ContactForm()
    contact_info = Contact.query.first()

    if form.validate_on_submit():
        new_contact = Contact(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
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
    # Latest 5 news (most recent first)
    recent_news = News.query.order_by(News.date.desc()).limit(5).all()
    # Upcoming 5 events (today and future)
    today = datetime.now().date()
    upcoming_events = Event.query.filter(Event.date >= today).order_by(Event.date.asc()).limit(5).all()
    # Latest contact message
    latest_contact = Contact.query.order_by(Contact.date.desc()).first()
    # Latest admission form
    latest_admission = AdmissionForm.query.order_by(AdmissionForm.submission_date.desc()).first()
    return render_template('admin/dashboard.html',
                           news_count=news_count,
                           events_count=events_count,
                           gallery_count=gallery_count,
                           contacts_count=contacts_count,
                           recent_news=recent_news,
                           upcoming_events=upcoming_events,
                           latest_contact=latest_contact,
                           latest_admission=latest_admission)

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
                if news.image_path:
                    delete_db_path_if_needed(news.image_path)
                    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], news.image_path)):
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
    if news.image_path:
        delete_db_path_if_needed(news.image_path)
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], news.image_path)):
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
                if event.image_path:
                    delete_db_path_if_needed(event.image_path)
                    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], event.image_path)):
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
    if event.image_path:
        delete_db_path_if_needed(event.image_path)
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], event.image_path)):
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

                # Compute dimensions and ratio category
                width = None
                height = None
                ratio_category = None
                try:
                    from PIL import Image
                    img = Image.open(io.BytesIO(file_data))
                    width, height = img.size
                    if width and height:
                        ratio = width / float(height)
                        def approx(a, b, tol=0.05):
                            return abs(a - b) <= tol
                        if approx(ratio, 1.0):
                            ratio_category = 'square'
                        elif approx(ratio, 3/4):
                            ratio_category = 'three_four'
                        elif ratio < 1.0:
                            ratio_category = 'portrait'
                        else:
                            ratio_category = 'landscape'
                except Exception as _e:
                    ratio_category = None

                # Create a new gallery image entry
                gallery_image = GalleryImage(
                    title=form.title.data or "Uploaded Image",
                    caption=form.caption.data or "",
                    image_data=file_data,
                    image_filename=file.filename,
                    image_mimetype=mimetype,
                    upload_date=datetime.now(),
                    width=width,
                    height=height,
                    ratio_category=ratio_category
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
    if not contact.is_read:
        contact.is_read = True
        db.session.commit()
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
        settings.map_embed_html = form.map_embed_html.data
        # Social links
        settings.social_facebook_url = form.social_facebook_url.data
        settings.social_twitter_url = form.social_twitter_url.data
        settings.social_instagram_url = form.social_instagram_url.data
        settings.social_linkedin_url = form.social_linkedin_url.data

        if form.school_logo.data:
            if allowed_file(form.school_logo.data.filename, app.config['ALLOWED_EXTENSIONS']):
                # Delete old logo if exists and not the default
                if settings.school_logo_path and settings.school_logo_path != 'IMG-20250425-WA0004.jpg':
                    delete_db_path_if_needed(settings.school_logo_path)
                    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], settings.school_logo_path)):
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], settings.school_logo_path))

                settings.school_logo_path = save_file(form.school_logo.data, app.config['UPLOAD_FOLDER'])
            else:
                flash('Invalid file format for logo. Allowed formats: png, jpg, jpeg, gif', 'danger')

        db.session.commit()
        flash('School settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))

    return render_template('admin/settings.html', form=form, settings=settings)

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

# Serve stored files from database (single, module-level route)
@app.route('/files/<int:file_id>')
def serve_db_file(file_id: int):
    sf = StoredFile.query.get_or_404(file_id)
    return send_file(io.BytesIO(sf.data), mimetype=sf.mimetype, download_name=sf.filename)

# Teacher Management
@app.route('/admin/teachers')
@login_required
def admin_teachers():
    teachers_list = Teacher.query.order_by(Teacher.order, Teacher.id).all()
    leadership_keywords = ['principal', 'director', 'chairman', 'vice principal', 'vice-principal', 'head of school', 'headmaster', 'managing director', 'coordinator']
    leadership = []
    teaching = []
    for t in teachers_list:
        ttype = (t.position_type or '').strip().lower()
        tpos = (t.position or '').strip().lower()
        is_leader = (ttype == 'leadership') or any(kw in tpos for kw in leadership_keywords)
        if is_leader:
            leadership.append(t)
        else:
            teaching.append(t)
    return render_template('admin/teachers_manage.html', teachers=teachers_list, leadership=leadership, teaching=teaching)

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
        # Conditional validation: qualification required for teaching staff
        if form.position_type.data == 'teaching' and not (form.qualification.data and form.qualification.data.strip()):
            form.qualification.errors = ['Qualification is required for Teaching Staff']
            return render_template('admin/teacher_form.html', form=form, title=title)
        # Position required for leadership
        if form.position_type.data == 'leadership' and not (form.position.data and form.position.data.strip()):
            form.position.errors = ['Position Title is required for Leadership']
            return render_template('admin/teacher_form.html', form=form, title=title)
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
            qualification=(form.qualification.data or '').strip(),
            experience=(form.experience.data or '').strip(),
            subject=(form.subject.data or '').strip(),
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
        # Conditional validation: qualification required for teaching staff
        if form.position_type.data == 'teaching' and not (form.qualification.data and form.qualification.data.strip()):
            form.qualification.errors = ['Qualification is required for Teaching Staff']
            return render_template('admin/teacher_form.html', form=form, title=title)
        teacher.name = form.name.data
        teacher.position_type = form.position_type.data
        teacher.position = form.position.data
        teacher.qualification = (form.qualification.data or '').strip()
        teacher.experience = (form.experience.data or '').strip()
        teacher.subject = (form.subject.data or '').strip()
        teacher.bio = form.bio.data
        teacher.order = form.order.data

        if form.image.data:
            if allowed_file(form.image.data.filename, app.config['ALLOWED_EXTENSIONS']):
                # Delete old image if exists
                if teacher.image_path:
                    delete_db_path_if_needed(teacher.image_path)
                    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], teacher.image_path)):
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
    if teacher.image_path:
        delete_db_path_if_needed(teacher.image_path)
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], teacher.image_path)):
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
                if facility.image_path:
                    delete_db_path_if_needed(facility.image_path)
                    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], facility.image_path)):
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
    if facility.image_path:
        delete_db_path_if_needed(facility.image_path)
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], facility.image_path)):
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
                if syllabus.file_path:
                    delete_db_path_if_needed(syllabus.file_path)
                    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], syllabus.file_path)):
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
    if syllabus.file_path:
        delete_db_path_if_needed(syllabus.file_path)
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], syllabus.file_path)):
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

# Admission Info Management
@app.route('/admin/admission-info', methods=['GET', 'POST'])
@login_required
def admin_admission_info():
    info = AdmissionInfo.query.first()
    if not info:
        info = AdmissionInfo()
        db.session.add(info)
        db.session.commit()
    form = AdmissionInfoForm(obj=info)
    eligibility_items = AdmissionEligibilityItem.query.order_by(AdmissionEligibilityItem.order, AdmissionEligibilityItem.id).all()
    document_items = AdmissionDocumentItem.query.order_by(AdmissionDocumentItem.order, AdmissionDocumentItem.id).all()
    date_items = AdmissionImportantDateItem.query.order_by(AdmissionImportantDateItem.order, AdmissionImportantDateItem.id).all()
    if form.validate_on_submit():
        info.intro_text = form.intro_text.data
        info.eligibility_text = form.eligibility_text.data
        info.documents_text = form.documents_text.data
        info.important_dates_text = form.important_dates_text.data
        info.form_embed_html = form.form_embed_html.data
        db.session.commit()
        flash('Admission information updated successfully!', 'success')
        return redirect(url_for('admin_admission_info'))
    # form fields for inline manage
    form_fields = AdmissionFormField.query.order_by(AdmissionFormField.order, AdmissionFormField.id).all()
    return render_template('admin/admission_info.html', form=form,
                           eligibility_items=eligibility_items,
                           document_items=document_items,
                           date_items=date_items,
                           form_fields=form_fields)

# Combined add for Eligibility & Documents
@app.route('/admin/admission/eligdoc/add', methods=['POST'])
@login_required
def admin_add_elig_or_doc_item():
    item_type = request.form.get('item_type')
    label = request.form.get('label')
    detail = request.form.get('detail')
    order = request.form.get('order') or 0
    try:
        order = int(order)
    except Exception:
        order = 0
    if not label or not detail:
        flash('Please provide label and detail.', 'danger')
        return redirect(url_for('admin_admission_info'))
    if item_type == 'document':
        db.session.add(AdmissionDocumentItem(label=label, detail=detail, order=order))
    else:
        db.session.add(AdmissionEligibilityItem(label=label, detail=detail, order=order))
    db.session.commit()
    flash('Item added.', 'success')
    return redirect(url_for('admin_admission_info'))

# Admission Items: Eligibility
@app.route('/admin/admission/eligibility/add', methods=['POST'])
@login_required
def admin_add_eligibility_item():
    label = request.form.get('label')
    detail = request.form.get('detail')
    order = request.form.get('order') or 0
    try:
        order = int(order)
    except Exception:
        order = 0
    if label and detail:
        db.session.add(AdmissionEligibilityItem(label=label, detail=detail, order=order))
        db.session.commit()
        flash('Eligibility item added.', 'success')
    else:
        flash('Please provide label and detail.', 'danger')
    return redirect(url_for('admin_admission_info'))

@app.route('/admin/admission/eligibility/delete/<int:item_id>', methods=['POST'])
@login_required
def admin_delete_eligibility_item(item_id):
    item = AdmissionEligibilityItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Eligibility item deleted.', 'success')
    return redirect(url_for('admin_admission_info'))

@app.route('/admin/admission/eligibility/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_eligibility_item(item_id):
    item = AdmissionEligibilityItem.query.get_or_404(item_id)
    if request.method == 'POST':
        new_type = request.form.get('item_type') or 'eligibility'
        label = request.form.get('label') or item.label
        detail = request.form.get('detail') or item.detail
        try:
            new_order = int(request.form.get('order') or item.order or 0)
        except Exception:
            new_order = item.order or 0
        if new_type == 'document':
            # move to documents table
            moved = AdmissionDocumentItem(label=label, detail=detail, order=new_order)
            db.session.add(moved)
            db.session.delete(item)
        else:
            item.label = label
            item.detail = detail
            item.order = new_order
        db.session.commit()
        flash('Item updated.', 'success')
        return redirect(url_for('admin_admission_info'))
    return render_template('admin/admission_item_form.html', title='Edit Eligibility Item', item=item, current_type='eligibility')

# Admission Items: Documents
@app.route('/admin/admission/documents/add', methods=['POST'])
@login_required
def admin_add_document_item():
    label = request.form.get('label')
    detail = request.form.get('detail')
    order = request.form.get('order') or 0
    try:
        order = int(order)
    except Exception:
        order = 0
    if label and detail:
        db.session.add(AdmissionDocumentItem(label=label, detail=detail, order=order))
        db.session.commit()
        flash('Document item added.', 'success')
    else:
        flash('Please provide label and detail.', 'danger')
    return redirect(url_for('admin_admission_info'))

@app.route('/admin/admission/documents/delete/<int:item_id>', methods=['POST'])
@login_required
def admin_delete_document_item(item_id):
    item = AdmissionDocumentItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Document item deleted.', 'success')
    return redirect(url_for('admin_admission_info'))

@app.route('/admin/admission/documents/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_document_item(item_id):
    item = AdmissionDocumentItem.query.get_or_404(item_id)
    if request.method == 'POST':
        new_type = request.form.get('item_type') or 'document'
        label = request.form.get('label') or item.label
        detail = request.form.get('detail') or item.detail
        try:
            new_order = int(request.form.get('order') or item.order or 0)
        except Exception:
            new_order = item.order or 0
        if new_type == 'eligibility':
            moved = AdmissionEligibilityItem(label=label, detail=detail, order=new_order)
            db.session.add(moved)
            db.session.delete(item)
        else:
            item.label = label
            item.detail = detail
            item.order = new_order
        db.session.commit()
        flash('Item updated.', 'success')
        return redirect(url_for('admin_admission_info'))
    return render_template('admin/admission_item_form.html', title='Edit Document Item', item=item, current_type='document')

# Admission Items: Important Dates
@app.route('/admin/admission/dates/add', methods=['POST'])
@login_required
def admin_add_date_item():
    label = request.form.get('label')
    detail = request.form.get('detail')
    order = request.form.get('order') or 0
    try:
        order = int(order)
    except Exception:
        order = 0
    if label and detail:
        db.session.add(AdmissionImportantDateItem(label=label, detail=detail, order=order))
        db.session.commit()
        flash('Important date added.', 'success')
    else:
        flash('Please provide label and detail.', 'danger')
    return redirect(url_for('admin_admission_info'))

@app.route('/admin/admission/dates/delete/<int:item_id>', methods=['POST'])
@login_required
def admin_delete_date_item(item_id):
    item = AdmissionImportantDateItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Important date deleted.', 'success')
    return redirect(url_for('admin_admission_info'))

@app.route('/admin/admission/dates/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_date_item(item_id):
    item = AdmissionImportantDateItem.query.get_or_404(item_id)
    if request.method == 'POST':
        item.label = request.form.get('label') or item.label
        item.detail = request.form.get('detail') or item.detail
        try:
            item.order = int(request.form.get('order') or item.order or 0)
        except Exception:
            pass
        db.session.commit()
        flash('Important date updated.', 'success')
        return redirect(url_for('admin_admission_info'))
    return render_template('admin/admission_item_form.html', title='Edit Important Date', item=item)

# Admission Form Fields Management
@app.route('/admin/admission/form-fields')
@login_required
def admin_form_fields():
    fields = AdmissionFormField.query.order_by(AdmissionFormField.order, AdmissionFormField.id).all()
    return render_template('admin/form_fields_manage.html', fields=fields)

@app.route('/admin/admission/form-fields/add', methods=['GET', 'POST'])
@login_required
def admin_add_form_field():
    form = AdmissionFormFieldForm()
    if form.validate_on_submit():
        field = AdmissionFormField(
            name=form.name.data.strip(),
            label=form.label.data.strip(),
            field_type=form.field_type.data,
            required=(form.required.data == 'yes'),
            placeholder=form.placeholder.data,
            options=form.options.data,
            order=form.order.data or 0
        )
        db.session.add(field)
        db.session.commit()
        flash('Form field added.', 'success')
        return redirect(url_for('admin_admission_info'))
    return render_template('admin/form_field_form.html', form=form, title='Add Form Field')

@app.route('/admin/admission/form-fields/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_form_field(id):
    field = AdmissionFormField.query.get_or_404(id)
    form = AdmissionFormFieldForm(obj=field)
    if form.validate_on_submit():
        field.name = form.name.data.strip()
        field.label = form.label.data.strip()
        field.field_type = form.field_type.data
        field.required = (form.required.data == 'yes')
        field.placeholder = form.placeholder.data
        field.options = form.options.data
        field.order = form.order.data or 0
        db.session.commit()
        flash('Form field updated.', 'success')
        return redirect(url_for('admin_form_fields'))
    # prefill select for required
    form.required.data = 'yes' if field.required else 'no'
    return render_template('admin/form_field_form.html', form=form, title='Edit Form Field')

@app.route('/admin/admission/form-fields/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_form_field(id):
    field = AdmissionFormField.query.get_or_404(id)
    db.session.delete(field)
    db.session.commit()
    flash('Form field deleted.', 'success')
    return redirect(url_for('admin_form_fields'))

# Quick add endpoint for inline form fields on admission info page
@app.route('/admin/admission/form-fields/quick-add', methods=['POST'])
@login_required
def admin_quick_add_form_field():
    name = (request.form.get('name') or '').strip()
    label = (request.form.get('label') or '').strip()
    field_type = request.form.get('field_type') or 'text'
    required = request.form.get('required') == 'yes'
    options = request.form.get('options')
    placeholder = request.form.get('placeholder')
    try:
        order = int(request.form.get('order') or 0)
    except Exception:
        order = 0
    if not name or not label:
        flash('Name and Label are required.', 'danger')
        return redirect(url_for('admin_admission_info'))
    db.session.add(AdmissionFormField(name=name, label=label, field_type=field_type, required=required, options=options, order=order, placeholder=placeholder))
    db.session.commit()
    flash('Form field added.', 'success')
    return redirect(url_for('admin_admission_info'))

# Achievements Page Management
@app.route('/admin/achievements/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_achievements():
    page = AchievementsPage.query.first()
    if not page:
        page = AchievementsPage()
        db.session.add(page)
        db.session.commit()
    form = AchievementsForm(obj=page)
    if form.validate_on_submit():
        page.content_html = form.content_html.data
        db.session.commit()
        flash('Achievements page updated successfully!', 'success')
        return redirect(url_for('admin_edit_achievements'))
    return render_template('admin/achievements_form.html', form=form)

# Achievements Items Management
@app.route('/admin/achievements')
@login_required
def admin_achievements():
    items = AchievementsItem.query.order_by(AchievementsItem.category, AchievementsItem.order, AchievementsItem.created_at).all()
    return render_template('admin/achievements_manage.html', items=items)

@app.route('/admin/achievements/add', methods=['GET', 'POST'])
@login_required
def admin_add_achievement():
    form = AchievementsItemForm()
    if form.validate_on_submit():
        item = AchievementsItem(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            icon_class=form.icon_class.data,
            order=form.order.data or 0
        )
        db.session.add(item)
        db.session.commit()
        flash('Achievement item added successfully!', 'success')
        return redirect(url_for('admin_achievements'))
    return render_template('admin/achievements_item_form.html', form=form, title='Add Achievement')

@app.route('/admin/achievements/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_achievement(id):
    item = AchievementsItem.query.get_or_404(id)
    form = AchievementsItemForm(obj=item)
    if form.validate_on_submit():
        item.title = form.title.data
        item.description = form.description.data
        item.category = form.category.data
        item.icon_class = form.icon_class.data
        item.order = form.order.data or 0
        db.session.commit()
        flash('Achievement item updated successfully!', 'success')
        return redirect(url_for('admin_achievements'))
    return render_template('admin/achievements_item_form.html', form=form, title='Edit Achievement')

@app.route('/admin/achievements/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_achievement(id):
    item = AchievementsItem.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Achievement item deleted successfully!', 'success')
    return redirect(url_for('admin_achievements'))

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

        # Determine next display order if not provided or 0
        next_order = form.order.data
        if not next_order or next_order == 0:
            last = HomeSlider.query.order_by(HomeSlider.order.desc()).first()
            next_order = (last.order + 1) if last and last.order else 1

        slider = HomeSlider(
            title=form.title.data,
            image_path=image_path,
            order=next_order,
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
                if slider.image_path:
                    delete_db_path_if_needed(slider.image_path)
                    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], slider.image_path)):
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
    if slider.image_path:
        delete_db_path_if_needed(slider.image_path)
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], slider.image_path)):
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
