
import random
import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_session import Session
import os

app = Flask(__name__)
app.secret_key = 'exam_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_sessions')
Session(app)

title_to_df = {
    '默认题库': pd.read_excel("题库.xlsx"),
    '题库2': pd.read_excel("2.xlsx"),
    '题库4': pd.read_excel("4.xlsx"),
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
  <title>选择题库 - 在线考试系统</title>
</head>
<body>
  <h2>请选择题库开始考试</h2>
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
  <title>在线考试系统</title>
  <style>
    .feedback { margin-top: 5px; font-weight: bold; }
    .question { margin-bottom: 20px; border-bottom: 1px dashed #ccc; padding-bottom: 10px; }
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
          </label><br>
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
      <textarea name="q{{ idx }}" rows="3" cols="60"></textarea>
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
  if (selected === correct) {
    feedback.innerHTML = '<span style="color:green">✔ 回答正确！</span>';
  } else {
    feedback.innerHTML = '<span style="color:red">❌ 回答错误，正确答案是：<b>' + correct + '</b></span>';
  }
}

function checkMultiAnswer(qid, correctStr) {
  const correct = new Set(correctStr.trim().split(''));
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
