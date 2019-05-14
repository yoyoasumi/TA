import os
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np


UPLOAD_FOLDER = 'grade'
ALLOWED_EXTENSIONS = set(['csv'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def measurement(gt_path, my_path, tp):
    score = 0
    gt = pd.read_csv(gt_path, dtype=str)
    try:
        my = pd.read_csv(my_path, dtype=str, error_bad_lines=False)
    except UnicodeDecodeError:
        my = pd.read_csv(my_path, dtype=str, encoding='gbk', error_bad_lines=False)
    columns = list(gt.columns)
    gt_count = gt.count()
    my_count = my.count()
    
    if columns[1] == '增发对象':
        pk = [ columns[0], columns[1] ]
        if tp == '5':
            gt['增发金额'] = pd.to_numeric(gt['增发金额'], downcast='integer', errors='coerce').dropna().apply(np.int64).astype(str)
            my['增发金额'] = pd.to_numeric(my['增发金额'], downcast='integer', errors='coerce').dropna().apply(np.int64).astype(str)
    elif columns[1] == '甲方':
        pk = [ columns[0], columns[1], columns[2] ]
        if tp == '5':
            gt['合同金额上限'] = pd.to_numeric(gt['合同金额上限'], downcast='integer', errors='coerce').dropna().apply(np.int64).astype(str)
            my['合同金额上限'] = pd.to_numeric(my['合同金额上限'], downcast='integer', errors='coerce').dropna().apply(np.int64).astype(str)
            gt['合同金额下限'] = pd.to_numeric(gt['合同金额下限'], downcast='integer', errors='coerce').dropna().apply(np.int64).astype(str)
            my['合同金额下限'] = pd.to_numeric(my['合同金额下限'], downcast='integer', errors='coerce').dropna().apply(np.int64).astype(str)
    elif columns[1] == '股东全称':
        pk = [ columns[0], columns[1], columns[3] ]
        my['变动截止日期'] = pd.to_datetime(my['变动截止日期'], errors='coerce').astype(str)
    
    match = pd.merge(gt, my, on=pk, suffixes=('_gt', '_my'))
    
    for col in columns:
        print('\t', col, end='')
        gt_col = gt[col]
        my_col = my[col]
        pos = gt_count[col]
        act = my_count[col]
        if col in pk:
            cor = match[col].count()
        else:
            cor = len(match.loc[ match[col+'_gt'] == match[col+'_my'] ])
        print('\t', 'POS =', pos, 'ACT =', act, 'COR =', cor, end='')
        recall = cor / pos
        precision = cor / act
        if recall == 0 or precision == 0:
            f1 = 0
        else:
            f1 = (2 * recall * precision) / (recall + precision)
        print('\t', 'F1 =', f1)
        score = score + f1
        
    return score / len(columns)



@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST' and (request.form['type'] == '3' or request.form['type'] == '5'):
        # check if the post request has the file part
        if 'file1' not in request.files and 'file2' not in request.files and 'file3' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file1 = request.files['file1']
        file2 = request.files['file2']
        file3 = request.files['file3']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file1.filename == '' and file2.filename == '' and file3.filename == '':
            flash('No selected file')
            return redirect(request.url)

        team = request.form['team']
        team_path = os.path.join(app.config['UPLOAD_FOLDER'], 'xxx', team)
        if not os.path.exists(team_path):
            os.mkdir(team_path)
        
        if file1 and allowed_file(file1.filename) and file2 and allowed_file(file2.filename) and file3 and allowed_file(file3.filename):

            dingzeng_filename = 'dingzeng_test.csv'
            hetong_filename = 'hetong_test.csv'
            zengjianchi_filename = 'zengjianchi_test.csv'

            gt_dingzeng_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test_result_csv', dingzeng_filename)
            gt_hetong_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test_result_csv', hetong_filename)
            gt_zengjianchi_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test_result_csv', zengjianchi_filename)

            my_dingzeng_path = os.path.join(app.config['UPLOAD_FOLDER'], 'xxx', team, dingzeng_filename)
            my_hetong_path = os.path.join(app.config['UPLOAD_FOLDER'], 'xxx', team, hetong_filename)
            my_zengjianchi_path = os.path.join(app.config['UPLOAD_FOLDER'], 'xxx', team, zengjianchi_filename)

            file1.save(my_dingzeng_path)
            file2.save(my_hetong_path)
            file3.save(my_zengjianchi_path)

            tp = request.form['type']

            print('*小组', team)
            dingzeng_score = measurement(gt_dingzeng_path, my_dingzeng_path, tp)
            print('*定向增发 F1 =', dingzeng_score)
            hetong_score = measurement(gt_hetong_path, my_hetong_path, tp)
            print('*重大合同 F1 =', hetong_score)
            zengjianchi_score = measurement(gt_zengjianchi_path, my_zengjianchi_path, tp)
            print('*股东增减持 F1 =', zengjianchi_score)
            avg_score = (dingzeng_score + hetong_score + zengjianchi_score) / 3
            print('*平均', avg_score)
            
            sheet = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'grade.csv'))
            row = {'team': team, 
                'dingzeng': dingzeng_score,
                'hetong': hetong_score,
                'zengjianchi': zengjianchi_score,
                'avg': avg_score}
            sheet = sheet.append(row, ignore_index=True)
            sheet.to_csv('grade.csv', index=False)


            return render_template('display.html', team=team, 
              dingzeng_score=dingzeng_score, hetong_score=hetong_score, zengjianchi_score=zengjianchi_score, avg_score=avg_score)
    return '''
    <!doctype html>
    <title>Upload Your Results</title>
    <h1>Upload Your Results</h1>
    <form method=post enctype=multipart/form-data>
      <p>小组：<input name="team"></p>
      <p>定向增发：<input type=file name=file1></p>
      <p>重大合同：<input type=file name=file2></p>
      <p>股东增减持：<input type=file name=file3></p>
      <p>类别：<input name="type"></p>
      <p><input type=submit value=Upload></p>
    </form>
    '''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
