from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    results = db.relationship('Result', backref='project', lazy=True)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    student_answer = db.Column(db.String(10))
    correct_answer = db.Column(db.String(10))
    is_correct = db.Column(db.Boolean, default=False)
