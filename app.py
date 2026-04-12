import random

import pandas as pd
from flask import Flask, redirect, render_template_string, request, session, url_for


app = Flask(__name__)
app.secret_key = 'exam_secret_key'

title_to_df = {
    '4月竞赛题库': pd.read_excel('4月竞赛参考题库_标准化.xlsx'),
    '竞赛题库': pd.read_excel('题库_竞赛_标准化.xlsx'),
}

SAMPLE_SIZES = {
    '单选': 30,
    '多选': 30,
    '判断': 20,
}

SCORE_RULES = {
    '单选': 2,
    '多选': 3,
    '判断': 1,
}

EXAM_DURATION_MINUTES = 30

HOME_TEMPLATE = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>选择题库 - 在线考试系统</title>
  <style>
    :root {
      --bg: #f3f6fb;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --accent: #059669;
      --border: #dbe3ef;
    }
    body {
      font-family: "Microsoft YaHei", sans-serif;
      padding: 20px;
      line-height: 1.6;
      background: linear-gradient(180deg, #eef4ff 0%, #f8fbff 100%);
      max-width: 720px;
      margin: 0 auto;
      color: var(--text);
    }
    h2 { text-align: center; margin-bottom: 10px; }
    .subtitle { text-align: center; color: var(--muted); margin-bottom: 22px; }
    form {
      background: var(--panel);
      padding: 24px;
      border-radius: 14px;
      box-shadow: 0 12px 30px rgba(37, 99, 235, 0.08);
      border: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .field-label { font-weight: bold; margin-bottom: 6px; }
    select {
      padding: 12px;
      font-size: 16px;
      border-radius: 10px;
      border: 1px solid var(--border);
      width: 100%;
    }
    .mode-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }
    .mode-card {
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      cursor: pointer;
      background: #f9fbff;
    }
    .mode-card input { margin-right: 8px; }
    .mode-card strong { display: block; margin-bottom: 6px; }
    .mode-card span { color: var(--muted); font-size: 14px; }
    .tips {
      background: #eefbf5;
      border: 1px solid #b7e4d0;
      color: #065f46;
      border-radius: 12px;
      padding: 14px;
      font-size: 14px;
    }
    .submit-btn {
      padding: 13px;
      font-size: 16px;
      background-color: var(--primary);
      color: white;
      border: none;
      border-radius: 10px;
      cursor: pointer;
    }
    .submit-btn:hover { background-color: var(--primary-dark); }
  </style>
</head>
<body>
  <h2>在线考试系统</h2>
  <p class="subtitle">请选择题库与模式后开始作答</p>
  <form method="post">
    <div>
      <div class="field-label">题库</div>
      <select name="exam_title">
        {% for title in titles %}
          <option value="{{ title }}">{{ title }}</option>
        {% endfor %}
      </select>
    </div>

    <div>
      <div class="field-label">模式</div>
      <div class="mode-grid">
        <label class="mode-card">
          <strong><input type="radio" name="exam_mode" value="practice" checked>练习模式</strong>
          <span>80 题，单选 30 / 多选 30 / 判断 20，保持即时反馈。</span>
        </label>
        <label class="mode-card">
          <strong><input type="radio" name="exam_mode" value="exam">考试模式</strong>
          <span>30 分钟限时，80 题，交卷或到时后统一显示得分和答案。</span>
        </label>
      </div>
    </div>

    <div class="tips">
      当前规则：单选每题 2 分，多选每题 3 分（必须全对，漏选不得分），判断每题 1 分。
    </div>

    <input class="submit-btn" type="submit" value="开始考试">
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
    :root {
      --bg: #f3f6fb;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --success: #15803d;
      --danger: #dc2626;
      --warning: #b45309;
      --border: #dbe3ef;
    }
    body {
      font-family: "Microsoft YaHei", sans-serif;
      padding: 15px;
      line-height: 1.6;
      background: linear-gradient(180deg, #eef4ff 0%, #f8fbff 100%);
      max-width: 980px;
      margin: 0 auto;
      color: var(--text);
    }
    .hero {
      position: sticky;
      top: 0;
      z-index: 10;
      background: rgba(243, 246, 251, 0.95);
      backdrop-filter: blur(8px);
      padding: 12px 0 16px;
      margin-bottom: 12px;
    }
    h2 { margin: 0 0 8px; text-align: center; color: var(--primary); }
    .meta {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 10px;
      margin-bottom: 10px;
    }
    .chip {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 6px 12px;
      font-size: 14px;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.06);
    }
    .timer { color: var(--danger); font-weight: bold; }
    .tips {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 14px;
      color: var(--muted);
      font-size: 14px;
    }
    .feedback {
      margin-top: 10px;
      font-weight: bold;
      padding: 8px 10px;
      border-radius: 8px;
      display: none;
    }
    .feedback.correct { display: block; color: var(--success); background: #edfdf2; }
    .feedback.wrong { display: block; color: var(--danger); background: #fff1f2; }
    .question {
      background: var(--panel);
      margin-bottom: 18px;
      border-radius: 14px;
      padding: 16px;
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
      border: 1px solid var(--border);
    }
    .question p { margin-top: 0; }
    label {
      display: block;
      padding: 10px;
      margin: 6px 0;
      background: #fafcff;
      border-radius: 10px;
      cursor: pointer;
      border: 1px solid #e6edf8;
    }
    label:hover { background: #f1f6ff; }
    input[type="radio"], input[type="checkbox"] { transform: scale(1.15); margin-right: 10px; }
    .action-row {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 18px;
    }
    button {
      padding: 12px 18px;
      border: none;
      border-radius: 10px;
      font-size: 16px;
      cursor: pointer;
    }
    .primary-btn { background: var(--accent, #059669); color: white; }
    .secondary-btn { background: var(--primary); color: white; }
    .primary-btn:hover { filter: brightness(0.96); }
    .secondary-btn:hover { background: var(--primary-dark); }
    .result-panel {
      display: none;
      margin: 24px 0 36px;
      background: var(--panel);
      border: 2px solid #bfdbfe;
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 14px 28px rgba(37, 99, 235, 0.08);
    }
    .result-panel.show { display: block; }
    .result-score {
      font-size: 26px;
      color: var(--primary);
      font-weight: bold;
      margin-bottom: 10px;
    }
    .result-summary {
      color: var(--muted);
      margin-bottom: 14px;
    }
    .answer-list {
      display: grid;
      gap: 10px;
    }
    .answer-item {
      background: #f8fbff;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 12px;
    }
    .answer-item strong { color: var(--text); }
    .answer-item .wrong-text { color: var(--danger); }
    .answer-item .right-text { color: var(--success); }
    @media (max-width: 640px) {
      body { padding: 12px; }
      .action-row { flex-direction: column; }
      button { width: 100%; }
    }
  </style>
</head>
<body>
  <div class="hero">
    <h2>{{ mode_name }}：{{ title }}</h2>
    <div class="meta">
      <div class="chip">题量：80 题</div>
      <div class="chip">单选 30</div>
      <div class="chip">多选 30</div>
      <div class="chip">判断 20</div>
      {% if exam_mode == 'exam' %}
        <div class="chip timer">剩余时间：<span id="timer">{{ duration_minutes }}:00</span></div>
      {% endif %}
    </div>
    <div class="tips">
      {% if exam_mode == 'practice' %}
        练习模式会即时反馈答案。当前练习题量已调整为 80 题，不包含问答题。
      {% else %}
        考试模式不即时公布答案。30 分钟内完成作答，单选每题 2 分，多选每题 3 分（必须全对，漏选不得分），判断每题 1 分。主动交卷或时间结束后，页面底部会统一显示得分和答案。
      {% endif %}
    </div>
  </div>

  <form id="exam-form" onsubmit="return false;">
    {% for idx, row in questions.iterrows() %}
      <div class="question" data-qid="q{{ idx }}" data-qtype="{{ row['题型'] }}" data-correct="{{ row['正确答案'] }}" data-score="{{ score_rules[row['题型']] }}">
        <p><b>Q{{ loop.index }}（{{ row['题型'] }}，{{ score_rules[row['题型']] }} 分）:</b> {{ row['题干'] }}</p>

        {% if row['题型'] in ['单选', '多选'] %}
          {% for opt in ['A', 'B', 'C', 'D', 'E', 'F'] %}
            {% if row['选项' + opt] == row['选项' + opt] %}
              <label>
                <input type="{{ 'checkbox' if row['题型'] == '多选' else 'radio' }}"
                       name="q{{ idx }}"
                       value="{{ opt }}"
                       data-qid="q{{ idx }}"
                       onclick="{% if exam_mode == 'practice' and row['题型'] == '单选' %}checkSingleAnswer(this){% endif %}">
                {{ opt }}. {{ row['选项' + opt] }}
              </label>
            {% endif %}
          {% endfor %}
          {% if exam_mode == 'practice' and row['题型'] == '多选' %}
            <button class="primary-btn" type="button" onclick="checkMultiAnswer('q{{ idx }}')">确认本题答案</button>
          {% endif %}
        {% elif row['题型'] == '判断' %}
          <label>
            <input type="radio" name="q{{ idx }}" value="A" onclick="{% if exam_mode == 'practice' %}checkSingleAnswer(this){% endif %}">
            对
          </label>
          <label>
            <input type="radio" name="q{{ idx }}" value="B" onclick="{% if exam_mode == 'practice' %}checkSingleAnswer(this){% endif %}">
            错
          </label>
        {% endif %}
        <div class="feedback"></div>
      </div>
    {% endfor %}

    {% if exam_mode == 'exam' %}
      <div class="action-row">
        <button class="secondary-btn" type="button" onclick="submitExam(false)">提交试卷</button>
      </div>
    {% endif %}
  </form>

  <div id="result-panel" class="result-panel">
    <div class="result-score" id="result-score"></div>
    <div class="result-summary" id="result-summary"></div>
    <div class="answer-list" id="answer-list"></div>
  </div>

<script>
const examMode = {{ exam_mode|tojson }};
const durationMinutes = {{ duration_minutes }};
const totalScore = {{ total_score }};
let examSubmitted = false;
let countdownTimer = null;

function normalizeAnswerText(questionType, answer) {
  if (questionType === '判断') {
    return answer === 'A' ? '对' : answer === 'B' ? '错' : answer;
  }
  return answer;
}

function getSelectedAnswers(qid, questionType) {
  const selectedEls = document.querySelectorAll("input[name='" + qid + "']:checked");
  const selected = Array.from(selectedEls).map(el => el.value);
  if (questionType === '多选') {
    return selected.sort().join('');
  }
  return selected[0] || '';
}

function setFeedback(container, isCorrect, text) {
  const feedback = container.querySelector('.feedback');
  feedback.className = 'feedback ' + (isCorrect ? 'correct' : 'wrong');
  feedback.innerHTML = text;
}

function checkSingleAnswer(el) {
  if (examMode !== 'practice') return;
  const container = el.closest('.question');
  const correct = container.dataset.correct.trim();
  const questionType = container.dataset.qtype;
  const selected = el.value;
  const correctText = normalizeAnswerText(questionType, correct);

  if (selected === correct) {
    setFeedback(container, true, '✔ 回答正确！');
  } else {
    setFeedback(container, false, '❌ 回答错误，正确答案是：<b>' + correctText + '</b>');
  }
}

function checkMultiAnswer(qid) {
  if (examMode !== 'practice') return;
  const container = document.querySelector("[data-qid='" + qid + "']");
  const correct = container.dataset.correct.trim();
  const selected = getSelectedAnswers(qid, '多选');

  if (selected === correct) {
    setFeedback(container, true, '✔ 回答正确！');
  } else {
    setFeedback(container, false, '❌ 回答错误，正确答案是：<b>' + correct + '</b>');
  }
}

function buildResultItem(index, container, userAnswer, earnedScore) {
  const questionType = container.dataset.qtype;
  const correctAnswer = container.dataset.correct.trim();
  const maxScore = Number(container.dataset.score || 0);
  const answerText = userAnswer ? normalizeAnswerText(questionType, userAnswer) : '未作答';
  const correctText = normalizeAnswerText(questionType, correctAnswer);
  const isCorrect = earnedScore === maxScore;

  return `
    <div class="answer-item">
      <strong>Q${index}（${questionType}）</strong><br>
      你的答案：<span class="${isCorrect ? 'right-text' : 'wrong-text'}">${answerText}</span><br>
      正确答案：<span class="right-text">${correctText}</span><br>
      得分：${earnedScore} / ${maxScore}
    </div>
  `;
}

function submitExam(isAutoSubmit) {
  if (examMode !== 'exam' || examSubmitted) return;

  examSubmitted = true;
  if (countdownTimer) {
    clearInterval(countdownTimer);
  }

  const containers = document.querySelectorAll('.question');
  const answerList = [];
  let score = 0;

  containers.forEach((container, index) => {
    const qid = container.dataset.qid;
    const questionType = container.dataset.qtype;
    const correctAnswer = container.dataset.correct.trim();
    const maxScore = Number(container.dataset.score || 0);
    const userAnswer = getSelectedAnswers(qid, questionType);
    const earnedScore = userAnswer === correctAnswer ? maxScore : 0;

    score += earnedScore;
    answerList.push(buildResultItem(index + 1, container, userAnswer, earnedScore));
  });

  const resultPanel = document.getElementById('result-panel');
  document.getElementById('result-score').textContent = '本次得分：' + score + ' / ' + totalScore;
  document.getElementById('result-summary').textContent = isAutoSubmit
    ? '时间已到，系统已自动交卷。以下为本次考试答案与得分。'
    : '你已提交试卷。以下为本次考试答案与得分。';
  document.getElementById('answer-list').innerHTML = answerList.join('');
  resultPanel.classList.add('show');
  resultPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });

  document.querySelectorAll('#exam-form input, #exam-form button').forEach(el => {
    el.disabled = true;
  });
}

function startExamTimer() {
  if (examMode !== 'exam') return;

  let remainingSeconds = durationMinutes * 60;
  const timerEl = document.getElementById('timer');

  function renderTime() {
    const minutes = String(Math.floor(remainingSeconds / 60)).padStart(2, '0');
    const seconds = String(remainingSeconds % 60).padStart(2, '0');
    timerEl.textContent = minutes + ':' + seconds;
  }

  renderTime();
  countdownTimer = setInterval(() => {
    remainingSeconds -= 1;
    if (remainingSeconds <= 0) {
      remainingSeconds = 0;
      renderTime();
      submitExam(true);
      return;
    }
    renderTime();
  }, 1000);
}

startExamTimer();
</script>
</body>
</html>
'''


def build_sampled_questions(df):
    grouped = {qtype: df[df['题型'] == qtype] for qtype in SAMPLE_SIZES}
    sampled = pd.DataFrame()

    for qtype, size in SAMPLE_SIZES.items():
        sample = grouped[qtype].sample(
            n=min(size, len(grouped[qtype])),
            random_state=random.randint(1, 10000),
        )
        sampled = pd.concat([sampled, sample])

    sampled = sampled.sample(frac=1, random_state=random.randint(1, 10000)).reset_index(drop=True)
    return sampled


@app.route('/', methods=['GET', 'POST'])
def choose_exam():
    if request.method == 'POST':
        session['exam_title'] = request.form['exam_title']
        session['exam_mode'] = request.form.get('exam_mode', 'practice')
        return redirect(url_for('exam'))
    return render_template_string(HOME_TEMPLATE, titles=title_to_df.keys())


@app.route('/exam')
def exam():
    exam_title = session.get('exam_title', '默认题库')
    exam_mode = session.get('exam_mode', 'practice')
    df = title_to_df[exam_title]
    questions = build_sampled_questions(df)
    total_score = (
        SAMPLE_SIZES['单选'] * SCORE_RULES['单选']
        + SAMPLE_SIZES['多选'] * SCORE_RULES['多选']
        + SAMPLE_SIZES['判断'] * SCORE_RULES['判断']
    )

    return render_template_string(
        EXAM_TEMPLATE,
        questions=questions,
        title=exam_title,
        exam_mode=exam_mode,
        mode_name='练习模式' if exam_mode == 'practice' else '考试模式',
        duration_minutes=EXAM_DURATION_MINUTES,
        score_rules=SCORE_RULES,
        total_score=total_score,
    )


if __name__ == '__main__':
    app.run(debug=False)
