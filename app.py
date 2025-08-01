import random
import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for, session
from datetime import datetime
from flask_session import Session



app = Flask(__name__)
app.secret_key = 'exam_secret_key'

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
# Load all available question sets
title_to_df = {
    '默认题库': pd.read_excel("题库.xlsx"),
    # "1.对公业务题库（2025年修订）总行上传": pd.read_excel("题库1.xlsx"),

    # 可扩展其他题库如 '高级题库': pd.read_excel("高级题库.xlsx")
}

sample_sizes = {
    '单选': 30,
    '多选': 20,
    '判断': 10,
    '简答': 4
}

TEMPLATE = '''
<!doctype html>
<title>在线考试系统</title>
<h2>考试：{{ title }}</h2>
<form method="post">
  {% for idx, row in questions.iterrows() %}
    <p><b>Q{{ loop.index }} ({{ row['题型'] }}):</b> {{ row['题干'] }}</p>
    {% if row['题型'] in ['单选', '多选'] %}
      {% for opt in ['A', 'B', 'C', 'D', 'E', 'F'] %}
        {% if row['选项' + opt] == row['选项' + opt] %}
          <label>
            <input type="{{ 'checkbox' if row['题型']=='多选' else 'radio' }}" name="q{{ idx }}" value="{{ opt }}">
            {{ opt }}. {{ row['选项' + opt] }}
          </label><br>
        {% endif %}
      {% endfor %}
    {% elif row['题型'] == '判断' %}
      <label><input type="radio" name="q{{ idx }}" value="对"> 对</label>
      <label><input type="radio" name="q{{ idx }}" value="错"> 错</label>
    {% elif row['题型'] == '简答' %}
      <textarea name="q{{ idx }}" rows="3" cols="60"></textarea>
    {% endif %}
    {% if submitted and row['题型'] != '简答' %}
      <p style="color:{{ 'green' if row['是否正确'] else 'red' }}">
        {% if row['是否正确'] %}✔ 回答正确{% else %}❌ 回答错误{% endif %}。
        正确答案是：<b>{{ row['正确答案'] }}</b>
      </p>
    {% endif %}
    <br>
  {% endfor %}
  <input type="submit" value="提交试卷">
</form>
'''

RESULT_TEMPLATE = '''
<!doctype html>
<title>成绩报告</title>
<h2>考试结果：</h2>
<p><b>得分：{{ score }} / {{ total }}</b></p>
<p><b>完成时间：</b> {{ timestamp }}</p>
<p><a href="/">返回考试首页</a></p>
'''

@app.route('/', methods=['GET', 'POST'])
def choose_exam():
    if request.method == 'POST':
        session['exam_title'] = request.form['exam_title']
        return redirect(url_for('exam'))
    return '''
    <h2>请选择题库开始考试</h2>
    <form method="post">
        <select name="exam_title">
        %s
        </select>
        <input type="submit" value="开始考试">
    </form>
    ''' % '\n'.join(f'<option value="{title}">{title}</option>' for title in title_to_df)

@app.route('/exam', methods=['GET', 'POST'])
def exam():
    exam_title = session.get('exam_title', '默认题库')
    df = title_to_df[exam_title]
    grouped = {k: df[df['题型'] == k] for k in ['单选', '多选', '判断', '简答']}

    if request.method == 'POST':
        if 'questions' not in session:
            return "<h3>会话已失效，请从<a href='/'>首页</a>重新开始考试。</h3>"

        questions = session['questions']
        for q in questions:
            qid = f"q{q['index']}"
            user_ans = request.form.getlist(qid)
            correct = str(q['正确答案']).strip()

            q['用户答案'] = user_ans
            q['是否正确'] = False

            if q['题型'] in ['单选', '判断']:
                if user_ans and user_ans[0].strip() == correct:
                    q['是否正确'] = True
            elif q['题型'] == '多选':
                correct_set = set(correct)
                if set(map(str.strip, user_ans)) == correct_set:
                    q['是否正确'] = True

        return render_template_string(TEMPLATE, questions=pd.DataFrame(questions), title=exam_title, submitted=True)

    # GET 请求，生成试题
    sampled = pd.DataFrame()
    for qtype, size in sample_sizes.items():
        sample = grouped[qtype].sample(n=min(size, len(grouped[qtype])), random_state=random.randint(1, 10000))
        sampled = pd.concat([sampled, sample])

    sampled.reset_index(inplace=True)
    session['questions'] = sampled.to_dict(orient='records')
    return render_template_string(TEMPLATE, questions=sampled, title=exam_title)

if __name__ == '__main__':
    app.run(debug=False)
