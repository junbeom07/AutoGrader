from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    results = db.relationship('Result', backref='project', lazy=True)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    pdf_filename = db.Column(db.String(255))
    score = db.Column(db.Float)
    correct_count = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    detected_answers = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 