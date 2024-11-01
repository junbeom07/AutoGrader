from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from models import db, Project, Result
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projects.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)

@app.route('/')
def index():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('index.html', projects=projects)

@app.route('/upload', methods=['POST'])
def upload():
    if 'answer_sheet' not in request.files or 'correct_answers' not in request.files:
        flash('파일이 없습니다')
        return redirect(url_for('index'))
    
    answer_sheet = request.files['answer_sheet']
    correct_answers = request.files['correct_answers']
    project_title = request.form['project_title']
    
    if answer_sheet.filename == '' or correct_answers.filename == '':
        flash('선택된 파일이 없습니다')
        return redirect(url_for('index'))
    
    if answer_sheet and allowed_file(answer_sheet.filename) and \
       correct_answers and allowed_file(correct_answers.filename):
        
        # 파일 저장
        exam_filename = secure_filename(f"{project_title}_exam_{answer_sheet.filename}")
        answer_filename = secure_filename(f"{project_title}_answer_{correct_answers.filename}")
        
        exam_path = os.path.join(app.config['UPLOAD_FOLDER'], exam_filename)
        answer_path = os.path.join(app.config['UPLOAD_FOLDER'], answer_filename)
        
        answer_sheet.save(exam_path)
        correct_answers.save(answer_path)
        
        # 데이터베이스에 저장
        project = Project(
            title=project_title,
            exam_pdf_path=f"uploads/{exam_filename}",
            answer_pdf_path=f"uploads/{answer_filename}"
        )
        db.session.add(project)
        db.session.commit()
        
        return redirect(url_for('view_project', project_id=project.id))

@app.route('/project/<int:project_id>')
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    results = Result.query.filter_by(project_id=project_id).order_by(Result.question_number).all()
    
    correct_count = sum(1 for r in results if r.is_correct)
    total_count = len(results)
    incorrect_count = total_count - correct_count
    total_score = int((correct_count / total_count) * 100) if total_count > 0 else 0
    
    result_data = {
        'total_score': total_score,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count,
        'answers': results
    }
    
    return render_template('project.html', project=project, result=result_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
