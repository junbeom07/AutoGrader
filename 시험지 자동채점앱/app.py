from flask import Flask, render_template, request, redirect, flash, url_for, jsonify
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
import os
from flask_sqlalchemy import SQLAlchemy
from models import db, Project, Result

# 허용할 파일 확장자 정의
ALLOWED_EXTENSIONS = {'pdf'}

# 폴더 경로 설정
UPLOAD_FOLDER = 'static/uploads'
PDF_FOLDER = os.path.join(UPLOAD_FOLDER, 'pdfs')
IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
POPPLER_PATH = r"C:\poppler-24.08.0\Library\bin"  # poppler 실제 설치 경로로 수정

app = Flask(__name__, static_folder='static')
app.secret_key = 'your-secret-key-here'  # 실제 운영환경에서는 더 복잡한 키를 사용하세요

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 최대 16MB 파일 제한
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grading.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# 정답 데이터 (실제 구현시에는 DB나 별도 파일에서 관리)
CORRECT_ANSWERS = {
    1: '3',
    2: '2',
    3: '5',
    4: '1',
    5: '4',
    6: '2',
    7: '3',
    8: '5',
    9: '1',
    10: '4',
    11: '2',
    12: '3',
    13: '5',
    14: '1',
    15: '4',
    16: '2',
    17: '3',
    18: '5',
    19: '1',
    20: '4',
    21: '2',
    22: '3',
    23: '5',
    24: '1',
    25: '4',
    26: '2',
    27: '3',
    28: '5',
    29: '1',
    30: '4',
    31: '2',
    32: '3',
    33: '5',
    34: '1',
    35: '4',
    36: '2',
    37: '3',
    38: '5',
    39: '1',
    40: '4',
    41: '2',
    42: '3',
    43: '5',
    44: '1',
    45: '4',
}

# 테스트용 제출 답안 상수로 정의
DETECTED_ANSWERS = {
    1: '3',
    2: '2',
    3: '2',
    4: '3',
    5: '4',
    6: '2',
    7: '3',
    8: '4',
    9: '1',
    10: '4',
    11: '5',
    12: '3',
    13: '5',
    14: '1',
    15: '4',
    16: '4',
    17: '4',
    18: '4',
    19: '1',
    20: '4',
    21: '2',
    22: '3',
    23: '5',
    24: '1',
    25: '4',
    26: '2',
    27: '3',
    28: '3',
    29: '1',
    30: '4',
    31: '2',
    32: '3',
    33: '5',
    34: '1',
    35: '4',
    36: '2',
    37: '3',
    38: '5',
    39: '1',
    40: '4',
    41: '2',
    42: '3',
    43: '5',
    44: '1',
    45: '4',
}



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 필요한 폴더들 생성
def create_folders():
    for folder in [PDF_FOLDER, IMAGE_FOLDER]:
        os.makedirs(folder, exist_ok=True)

# 새로운 헬퍼 함수 추가
def process_pdf_file(file, project_id):
    filename = secure_filename(file.filename)
    pdf_path = os.path.join(PDF_FOLDER, filename)
    file.save(pdf_path)
    
    # PDF를 이미지로 변환
    images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
    
    # 이미지 저장
    image_paths = []
    for i, image in enumerate(images):
        image_filename = f'page_{i+1}.jpg'
        image_path = os.path.join(IMAGE_FOLDER, f"{filename.rsplit('.', 1)[0]}_{image_filename}")
        image.save(image_path, 'JPEG')
        relative_path = f"{filename.rsplit('.', 1)[0]}_{image_filename}"
        image_paths.append(relative_path)
    
    # YOLO 모델로 체크된 답 감지 (나중에 구현)
    # detected_answers = detect_answers(image_path)
    
    # 임시 테스트용 데이터
    detected_answers = DETECTED_ANSWERS
    
    # 채점 결과 계산
    results = grade_answers(detected_answers)
    
    # 결과를 데이터베이스에 저장
    result = Result(
        project_id=project_id,
        pdf_filename=filename,
        score=results['score'],
        correct_count=results['correct_count'],
        total_questions=results['total_questions'],
        detected_answers=detected_answers
    )
    db.session.add(result)
    db.session.commit()
    
    return image_paths, results, detected_answers

@app.route('/')
def home():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('index.html', projects=projects)

@app.route('/project/create', methods=['POST'])
def create_project():
    project_name = request.form.get('project_name')
    if 'file' not in request.files:
        flash('PDF 파일을 선택해주세요')
        return redirect('/')
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        flash('유효한 PDF 파일을 선택해주세요')
        return redirect('/')
    
    if project_name and file:
        create_folders()
        # 프로젝트 생성
        project = Project(name=project_name)
        db.session.add(project)
        db.session.commit()
        
        try:
            process_pdf_file(file, project.id)
            return redirect(url_for('view_project', project_id=project.id))
        except Exception as e:
            db.session.delete(project)
            db.session.commit()
            flash(f"PDF 처리 중 오류 발생: {str(e)}")
            return redirect('/')
    
    return redirect('/')

@app.route('/project/<int:project_id>')
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    result = Result.query.filter_by(project_id=project_id).first()
    
    # 테스트용 제출 답안
    detected_answers = DETECTED_ANSWERS
    
    # 채점 결과 계산
    total_questions = len(CORRECT_ANSWERS)
    correct_count = 0
    details = []
    
    # 각 문항별로 채점
    for question_num in sorted(CORRECT_ANSWERS.keys()):
        student_answer = detected_answers.get(question_num, '미체크')
        correct_answer = CORRECT_ANSWERS[question_num]
        is_correct = student_answer == correct_answer
        
        if is_correct:
            correct_count += 1
            
        details.append({
            'question_num': question_num,
            'student_answer': student_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })
    
    # 점수 계산
    score = round((correct_count / total_questions) * 100, 2)
    
    results = {
        'score': score,
        'correct_count': correct_count,
        'total_questions': total_questions,
        'details': details
    }

    # PDF에서 변환된 이미지 경로 가져오기
    image_paths = []
    if result and result.pdf_filename:
        pdf_name = os.path.splitext(result.pdf_filename)[0]
        image_dir = os.path.join(app.static_folder, 'uploads/images')
        for file in os.listdir(image_dir):
            if file.startswith(pdf_name):
                image_paths.append(file)
    
    return render_template('result.html',
                         project=project,
                         results=results,
                         image_paths=sorted(image_paths))  # 이미지 순서대로 정렬

@app.route('/project/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    try:
        # 먼저 해당 프로젝트의 모든 결과를 삭제
        db.session.query(Result).filter_by(project_id=project_id).delete()
        
        # 그 다음 프로젝트 삭제
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        
        flash('프로젝트가 성공적으로 삭제되었습니다.')
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()
        flash('프로젝트 삭제 중 오류가 발생했습니다.')
        return redirect(url_for('home'))

@app.route('/project/<int:project_id>/upload', methods=['POST'])
def upload_file(project_id):
    project = Project.query.get_or_404(project_id)
    
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return redirect(request.url)
    
    if file:
        create_folders()
        try:
            image_paths, results, detected_answers = process_pdf_file(file, project_id)
            return render_template('result.html',
                                project=project,
                                image_paths=image_paths,
                                results=results,
                                detected_answers=detected_answers,
                                correct_answers=CORRECT_ANSWERS)
        except Exception as e:
            return f"PDF 변환 중 오류 발생: {str(e)}"

@app.route('/project/<int:project_id>/update', methods=['POST'])
def update_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        new_name = request.form.get('project_name')
        original_name = project.name
        
        if new_name:
            project.name = new_name
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'original_name': original_name})
            
    except Exception as e:
        return jsonify({'success': False, 'original_name': original_name})

def grade_answers(detected_answers):
    """
    채점 함수
    detected_answers: 학생이 제출한 답안 딕셔너리 {문항번호: 답안}
    returns: 채점 결과 딕셔너리
    """
    total_questions = len(CORRECT_ANSWERS)
    correct_count = 0
    details = []

    # 각 문항별로 채점
    for question_num in sorted(CORRECT_ANSWERS.keys()):
        student_answer = detected_answers.get(question_num, '미체크')
        correct_answer = CORRECT_ANSWERS[question_num]
        is_correct = student_answer == correct_answer

        if is_correct:
            correct_count += 1

        details.append({
            'question_num': question_num,
            'student_answer': student_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })

    # 점수 계산 (100점 만점)
    score = round((correct_count / total_questions) * 100, 2)

    return {
        'score': score,
        'correct_count': correct_count,
        'total_questions': total_questions,
        'details': details
    }

# 서버 시작 시 폴더 생성
create_folders()

# 데이터베이스 생성
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)