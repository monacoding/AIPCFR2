import os
import pandas as pd
import bcrypt
from flask import Flask, request, render_template, send_file, jsonify, session, redirect, url_for, redirect, flash
from ai_model import generate_response
from db_manager import init_db, save_to_db, update_db, bulk_update_data,create_user,check_user
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return render_template('login.html')  # 로그인 안 한 경우 로그인 창
    return render_template('index.html')      # 로그인한 경우 index.html 진입

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "파일이 없습니다.", 400
    file = request.files['file']
    if file.filename == '':
        return "파일이 선택되지 않았습니다.", 400
    if file and file.filename.endswith('.xlsx'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        df = pd.read_excel(filepath)
        inquiries = df.to_dict('records')

        responses = []
        session['uploaded_data'] = []
        for idx, inquiry in enumerate(inquiries, start=1):
            item_no = inquiry.get('Item No.', 'N/A')
            status = inquiry.get('Status', 'N/A')
            count = inquiry.get('Count', 0.0)
            buyer_comments = inquiry.get("Buyer's Comments", "문의 내용 없음")
            company = inquiry.get('Company', 'N/A')
            name = inquiry.get('Name', 'N/A')
            status_for_sort = inquiry.get('Status(for sort)', 'N/A')

            builder_reply = generate_response(buyer_comments, company, name, item_no)

            response_item = {
                'id': idx,
                'item_no': item_no,
                'status': status,
                'count': count,
                'inquiry': buyer_comments,
                'company': company,
                'name': name,
                'response': builder_reply,
                'status_for_sort': status_for_sort
            }

            session['uploaded_data'].append(response_item)
            responses.append(response_item)

        return render_template('result.html', data=responses, filename=file.filename)
    return "Excel 파일만 업로드 가능합니다.", 400

@app.route('/update', methods=['POST'])
def update_data():
    data = request.get_json()
    save_to_db(data['item_no'], data['status'], None, data['inquiry'],
               data['company'], data['name'], data['response'], '학습')
    return jsonify({'status': 'success', 'message': '수정 완료'})

@app.route('/bulk_update', methods=['POST'])
def bulk_update():
    bulk_data = request.get_json()
    try:
        bulk_update_data(bulk_data)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/download_pcf/<filename>')
def download_pcf(filename):
    data = session.get('uploaded_data', [])
    df = pd.DataFrame(data)
    pcf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pcf_output.xlsx')
    df.to_excel(pcf_path, index=False)
    return send_file(pcf_path, as_attachment=True, download_name='pcf_output.xlsx')


# app.py 내부에 추가할 코드

# 회원가입 라우트
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            create_user(username, hashed)
            flash('회원가입 완료. 로그인해주세요.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('이미 존재하는 사용자입니다.', 'danger')
    return render_template('register.html')

# 로그인 라우트
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = check_user(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('로그인 성공!', 'success')
            return redirect(url_for('index'))  # ✅ 여기서 dashboard → index 로 변경
        flash('아이디 또는 비밀번호가 틀립니다.', 'danger')
    return render_template('login.html')

# 로그아웃
@app.route('/logout')
def logout():
    session.clear()
    flash('로그아웃 되었습니다.', 'info')
    return redirect(url_for('login'))

# 예시 대시보드 (로그인 필요)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return f"<h2>안녕하세요, {session['username']}님!</h2><p><a href='/logout'>로그아웃</a></p>"



app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    port = int(os.getenv("PORT", 5019))
    app.run(debug=True, host='0.0.0.0', port=port)