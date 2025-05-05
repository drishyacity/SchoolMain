from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, Time, ForeignKey

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
    image_path = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.now)
    
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
    position = Column(String(100), nullable=False)
    qualification = Column(String(200), nullable=False)
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
    
    def __repr__(self):
        return f'<SchoolSetting {self.school_name}>'
