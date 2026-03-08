
import random
import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask import Flask, render_template_string, request, redirect, url_for, session
# from flask_session import Session
import os

app = Flask(__name__)
app.secret_key = 'exam_secret_key'
# app.config['SESSION_TYPE'] = 'filesystem'
# app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_sessions')
# Session(app)

title_to_df = {
    '题库1': pd.read_excel("题库1_标准化.xlsx"),
    '题库2': pd.read_excel("题库2_标准化.xlsx"),
    '题库3': pd.read_excel("题库3_标准化.xlsx"),
    '题库4': pd.read_excel("题库4_标准化.xlsx"),
    '题库5': pd.read_excel("题库5_标准化.xlsx"),
    '题库6': pd.read_excel("题库6_标准化.xlsx"),
    '题库7': pd.read_excel("题库7_标准化.xlsx"),
    '题库8': pd.read_excel("题库8_标准化.xlsx"),
    '合并题库': pd.read_excel("合并题库_标准化.xlsx"),
}

sample_sizes = {
    '单选': 30,
    '多选': 20,
    '判断': 10,
    '简答': 4
}

HOME_TEMPLATE = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>选择题库 - 在线考试系统</title>
  <style>
    body { font-family: sans-serif; padding: 20px; line-height: 1.6; background-color: #f4f7f6; max-width: 600px; margin: 0 auto; }
    h2 { color: #333; text-align: center; }
    form { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; flex-direction: column; gap: 15px; }
    select { padding: 12px; font-size: 16px; border-radius: 5px; border: 1px solid #ddd; }
    input[type="submit"] { padding: 12px; font-size: 16px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
    input[type="submit"]:hover { background-color: #0056b3; }
  </style>
</head>
<body>
  <h2>在线考试系统</h2>
  <p style="text-align:center;">请选择题库开始考试</p>
  <form method="post">
    <select name="exam_title">
      {% for title in titles %}
        <option value="{{ title }}">{{ title }}</option>
      {% endfor %}
    </select>
    <input type="submit" value="开始考试">
  </form>
</body>
</html>
'''

EXAM_TEMPLATE = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>在线考试系统</title>
  <style>
    body { font-family: sans-serif; padding: 15px; line-height: 1.6; background-color: #f4f7f6; max-width: 800px; margin: 0 auto; color: #333; }
    h2 { text-align: center; color: #007bff; }
    .feedback { margin-top: 10px; font-weight: bold; padding: 5px; border-radius: 4px; }
    .question { background: white; margin-bottom: 20px; border-radius: 8px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    label { display: block; padding: 10px; margin: 5px 0; background: #fafafa; border-radius: 5px; cursor: pointer; border: 1px solid #eee; }
    label:hover { background: #f0f0f0; }
    input[type="radio"], input[type="checkbox"] { transform: scale(1.2); margin-right: 10px; }
    button { display: block; width: 100%; padding: 12px; margin-top: 10px; background: #28a745; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
    textarea { width: 100%; border: 1px solid #ddd; border-radius: 5px; padding: 10px; box-sizing: border-box; }
  </style>
</head>
<body>
<h2>考试：{{ title }}</h2>
<form onsubmit="return false;">
  {% for idx, row in questions.iterrows() %}
    <div class="question">
    <p><b>Q{{ loop.index }} ({{ row['题型'] }}):</b> {{ row['题干'] }}</p>

    {% if row['题型'] in ['单选', '多选'] %}
      {% for opt in ['A','B','C','D','E','F'] %}
        {% if row['选项' + opt] == row['选项' + opt] %}
          <label>
            <input type="{{ 'checkbox' if row['题型'] == '多选' else 'radio' }}"
                   name="q{{ idx }}"
                   value="{{ opt }}"
                   data-qid="q{{ idx }}"
                   data-correct="{{ row['正确答案'] }}"
                   onclick="{% if row['题型']=='单选' %}checkSingleAnswer(this){% endif %}">
            {{ opt }}. {{ row['选项' + opt] }}
          </label>
        {% endif %}
      {% endfor %}
      {% if row['题型'] == '多选' %}
        <button type="button" onclick="checkMultiAnswer('q{{ idx }}', '{{ row['正确答案'] }}')">确认本题答案</button>
      {% endif %}
    {% elif row['题型'] == '判断' %}
      <label><input type="radio" name="q{{ idx }}" value="对"
                    data-correct="{{ row['正确答案'] }}"
                    onclick="checkSingleAnswer(this)"> 对</label>
      <label><input type="radio" name="q{{ idx }}" value="错"
                    data-correct="{{ row['正确答案'] }}"
                    onclick="checkSingleAnswer(this)"> 错</label>
    {% elif row['题型'] == '简答' %}
      <textarea name="q{{ idx }}" rows="3" placeholder="在此输入答案..."></textarea>
    {% endif %}
    <div class="feedback"></div>
    </div>
  {% endfor %}
</form>

<script>
function checkSingleAnswer(el) {
  const selected = el.value;
  const correct = el.dataset.correct.trim();
  const container = el.closest('.question');
  const feedback = container.querySelector('.feedback');
  let mapped = selected;
  if (selected === '对') mapped = 'A';
  else if (selected === '错') mapped = 'B';

  if (mapped === correct) {
    feedback.innerHTML = '<span style="color:green">✔ 回答正确！</span>';
  } else {
    let correctText = (correct === 'A') ? '对' : (correct === 'B') ? '错' : correct;
    feedback.innerHTML = '<span style="color:red">❌ 回答错误，正确答案是：<b>' + correctText + '</b></span>';
  }
}

function checkMultiAnswer(qid, correctStr) {
  const correct = new Set(correctStr.replace(/[^A-F]/g, '').split(''));
  const selectedEls = document.querySelectorAll("input[name='" + qid + "']:checked");
  const selected = new Set(Array.from(selectedEls).map(el => el.value));
  const container = selectedEls.length > 0 ? selectedEls[0].closest('.question') : document.querySelector("[name='" + qid + "']").closest('.question');
  const feedback = container.querySelector('.feedback');

  if (setsEqual(correct, selected)) {
    feedback.innerHTML = '<span style="color:green">✔ 回答正确！</span>';
  } else {
    feedback.innerHTML = '<span style="color:red">❌ 回答错误，正确答案是：<b>' + Array.from(correct).join('') + '</b></span>';
  }
}

function setsEqual(a, b) {
  if (a.size !== b.size) return false;
  for (let val of a) if (!b.has(val)) return false;
  return true;
}
</script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def choose_exam():
    if request.method == 'POST':
        session['exam_title'] = request.form['exam_title']
        return redirect(url_for('exam'))
    return render_template_string(HOME_TEMPLATE, titles=title_to_df.keys())

@app.route('/exam')
def exam():
    exam_title = session.get('exam_title', '默认题库')
    df = title_to_df[exam_title]
    grouped = {k: df[df['题型'] == k] for k in ['单选', '多选', '判断', '简答']}
    sampled = pd.DataFrame()
    for qtype, size in sample_sizes.items():
        sample = grouped[qtype].sample(n=min(size, len(grouped[qtype])), random_state=random.randint(1, 10000))
        sampled = pd.concat([sampled, sample])
    sampled.reset_index(inplace=True)
    return render_template_string(EXAM_TEMPLATE, questions=sampled, title=exam_title)

if __name__ == '__main__':
    app.run(debug=False)
