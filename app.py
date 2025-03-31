import os
import pandas as pd
from flask import Flask, request, render_template, send_file, jsonify, session, redirect, url_for
from ai_model import generate_response
from db_manager import init_db, save_to_db, update_db, bulk_update_data

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

init_db()

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    port = int(os.getenv("PORT", 5019))
    app.run(debug=True, host='0.0.0.0', port=port)