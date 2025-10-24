from datetime import datetime
from database import db
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, Time, ForeignKey

class StoredFile(db.Model):
    __tablename__ = 'stored_files'

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    mimetype = Column(String(100), nullable=False)
    data = Column(db.LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f'<StoredFile {self.id}:{self.filename}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f'<User {self.username}>'

class News(db.Model):
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    date = Column(Date, nullable=False, default=datetime.now().date())
    image_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f'<News {self.title}>'

class Event(db.Model):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=True)
    location = Column(String(200), nullable=False)
    image_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Event {self.title}>'

class GalleryImage(db.Model):
    __tablename__ = 'gallery_images'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=True)
    caption = Column(String(255), nullable=True)
    image_data = Column(db.LargeBinary, nullable=False)  # Store the actual image data
    image_filename = Column(String(255), nullable=False)  # Store the original filename
    image_mimetype = Column(String(50), nullable=False)   # Store the MIME type
    upload_date = Column(DateTime, default=datetime.now)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    ratio_category = Column(String(20), nullable=True)  # 'square', 'three_four', 'portrait', 'landscape'

    def __repr__(self):
        return f'<GalleryImage {self.id}>'

class Contact(db.Model):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False)
    subject = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    date = Column(DateTime, default=datetime.now)
    is_read = Column(Boolean, default=False)

    def __repr__(self):
        return f'<Contact {self.name}>'

class AboutSection(db.Model):
    __tablename__ = 'about_sections'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    order = Column(Integer, default=0)

    def __repr__(self):
        return f'<AboutSection {self.title}>'

class AcademicProgram(db.Model):
    __tablename__ = 'academic_programs'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    order = Column(Integer, default=0)

    def __repr__(self):
        return f'<AcademicProgram {self.title}>'

class Teacher(db.Model):
    __tablename__ = 'teachers'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    position_type = Column(String(50), default='teaching')  # 'leadership' or 'teaching'
    position = Column(String(100), nullable=False)
    qualification = Column(String(200), nullable=True)
    experience = Column(String(100), nullable=True)
    subject = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    image_path = Column(String(255))
    order = Column(Integer, default=0)

    def __repr__(self):
        return f'<Teacher {self.name}>'

class Facility(db.Model):
    __tablename__ = 'facilities'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    image_path = Column(String(255))
    order = Column(Integer, default=0)

    def __repr__(self):
        return f'<Facility {self.title}>'

class Syllabus(db.Model):
    __tablename__ = 'syllabus'

    id = Column(Integer, primary_key=True)
    class_name = Column(String(50), nullable=False)
    subject = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    file_path = Column(String(255), nullable=True)
    order = Column(Integer, default=0)

    def __repr__(self):
        return f'<Syllabus {self.class_name}-{self.subject}>'

class AdmissionInfo(db.Model):
    __tablename__ = 'admission_info'

    id = Column(Integer, primary_key=True)
    intro_text = Column(Text, nullable=True)
    eligibility_text = Column(Text, nullable=True)
    documents_text = Column(Text, nullable=True)
    important_dates_text = Column(Text, nullable=True)
    form_embed_html = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f'<AdmissionInfo {self.id}>'

class AdmissionForm(db.Model):
    __tablename__ = 'admission_forms'

    id = Column(Integer, primary_key=True)
    student_name = Column(String(100), nullable=False)
    parent_name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    class_applying = Column(String(50), nullable=False)
    previous_school = Column(String(200), nullable=True)
    date_of_birth = Column(Date, nullable=False)
    submission_date = Column(DateTime, default=datetime.now)
    status = Column(String(50), default='Pending') # Pending, Approved, Rejected
    comments = Column(Text, nullable=True)

    def __repr__(self):
        return f'<AdmissionForm {self.student_name}>'

class HomeSlider(db.Model):
    __tablename__ = 'home_sliders'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=True)
    image_path = Column(String(255), nullable=False)
    order = Column(Integer, default=0)
    active = Column(Boolean, default=True)

    def __repr__(self):
        return f'<HomeSlider {self.id}>'

class SchoolSetting(db.Model):
    __tablename__ = 'school_settings'

    id = Column(Integer, primary_key=True)
    school_name = Column(String(200), nullable=False)
    school_address = Column(String(255), nullable=False)
    school_phone = Column(String(20), nullable=False)
    school_email = Column(String(120), nullable=False)
    school_logo_path = Column(String(255), default='IMG-20250425-WA0004.jpg')
    map_embed_html = Column(Text, nullable=True)

    def __repr__(self):
        return f'<SchoolSetting {self.school_name}>'

class AchievementsPage(db.Model):
    __tablename__ = 'achievements_page'

    id = Column(Integer, primary_key=True)
    content_html = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f'<AchievementsPage {self.id}>'

class AchievementsItem(db.Model):
    __tablename__ = 'achievements_items'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # e.g., 'Academic', 'Sports', 'Co-curricular'
    icon_class = Column(String(100), nullable=True)  # e.g., 'fas fa-trophy'
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f'<AchievementsItem {self.title}>'

class AdmissionEligibilityItem(db.Model):
    __tablename__ = 'admission_eligibility_items'

    id = Column(Integer, primary_key=True)
    label = Column(String(100), nullable=False)
    detail = Column(String(255), nullable=False)
    order = Column(Integer, default=0)

    def __repr__(self):
        return f'<AdmissionEligibilityItem {self.label}>'

class AdmissionDocumentItem(db.Model):
    __tablename__ = 'admission_document_items'

    id = Column(Integer, primary_key=True)
    label = Column(String(100), nullable=False)
    detail = Column(String(255), nullable=False)
    order = Column(Integer, default=0)

    def __repr__(self):
        return f'<AdmissionDocumentItem {self.label}>'

class AdmissionImportantDateItem(db.Model):
    __tablename__ = 'admission_important_date_items'

    id = Column(Integer, primary_key=True)
    label = Column(String(100), nullable=False)
    detail = Column(String(255), nullable=False)
    order = Column(Integer, default=0)

    def __repr__(self):
        return f'<AdmissionImportantDateItem {self.label}>'

class AdmissionFormField(db.Model):
    __tablename__ = 'admission_form_fields'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # internal field name
    label = Column(String(150), nullable=False)
    field_type = Column(String(30), nullable=False)  # text, email, tel, textarea, date, select
    required = Column(Boolean, default=False)
    options = Column(Text, nullable=True)  # comma-separated for select
    order = Column(Integer, default=0)
    placeholder = Column(String(255), nullable=True)

    def __repr__(self):
        return f'<AdmissionFormField {self.name}:{self.field_type}>'
