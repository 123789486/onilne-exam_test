import random
import time
import uuid
import os

import pandas as pd
from flask import Flask, jsonify, redirect, render_template_string, request, session, url_for
from flask_session import Session


app = Flask(__name__)
app.secret_key = 'exam_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_sessions')
app.config['SESSION_PERMANENT'] = False
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
Session(app)

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
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
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
          <span>30 分钟限时，80 题，刷新后题目、倒计时和答案都会保持。</span>
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
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --success: #15803d;
      --danger: #dc2626;
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
      background: rgba(243, 246, 251, 0.96);
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
    .result-banner {
      display: none;
      margin: 18px 0 20px;
      background: var(--panel);
      border: 2px solid #bfdbfe;
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 14px 28px rgba(37, 99, 235, 0.08);
    }
    .result-banner.show { display: block; }
    .result-score {
      font-size: 26px;
      color: var(--primary);
      font-weight: bold;
      margin-bottom: 10px;
    }
    .result-summary { color: var(--muted); }
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
    .primary-btn { background: #059669; color: white; }
    .secondary-btn { background: var(--primary); color: white; }
    .primary-btn:hover { filter: brightness(0.96); }
    .secondary-btn:hover { background: var(--primary-dark); }
    .right-text { color: var(--success); }
    .wrong-text { color: var(--danger); }
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
        <div class="chip timer">剩余时间：<span id="timer">{{ initial_timer_text }}</span></div>
      {% endif %}
    </div>
    <div class="tips">
      {% if exam_mode == 'practice' %}
        练习模式会即时反馈答案。当前练习题量已调整为 80 题，不包含问答题。
      {% else %}
        考试模式由服务端锁定题目快照、开始时间与答题状态。刷新页面不会重抽题，也不会重置倒计时；交卷后会在每道题原位置显示答案与得分。
      {% endif %}
    </div>
    <div id="result-banner" class="result-banner{% if submitted_result %} show{% endif %}">
      <div class="result-score" id="result-score">{% if submitted_result %}本次得分：{{ submitted_result['score'] }} / {{ total_score }}{% endif %}</div>
      <div class="result-summary" id="result-summary">{% if submitted_result %}{{ submitted_result['summary'] }}{% endif %}</div>
    </div>
  </div>

  <form id="exam-form" onsubmit="return false;">
    {% for row in questions %}
      {% set saved_answer = saved_answers.get(row['qid'], '') %}
      {% set detail = submitted_details.get(row['qid']) %}
      <div class="question" data-qid="{{ row['qid'] }}" data-qtype="{{ row['题型'] }}" data-correct="{{ row['正确答案'] }}" data-score="{{ score_rules[row['题型']] }}">
        <p><b>Q{{ loop.index }}（{{ row['题型'] }}，{{ score_rules[row['题型']] }} 分）:</b> {{ row['题干'] }}</p>

        {% if row['题型'] in ['单选', '多选'] %}
          {% for opt in ['A', 'B', 'C', 'D', 'E', 'F'] %}
            {% if row['选项' + opt] == row['选项' + opt] %}
              <label>
                <input type="{{ 'checkbox' if row['题型'] == '多选' else 'radio' }}"
                       name="{{ row['qid'] }}"
                       value="{{ opt }}"
                       {% if (row['题型'] == '多选' and opt in saved_answer) or (row['题型'] != '多选' and saved_answer == opt) %}checked{% endif %}
                       {% if submitted_result %}disabled{% endif %}
                       onchange="{% if exam_mode == 'practice' and row['题型'] == '单选' %}checkSingleAnswer(this){% elif exam_mode == 'exam' %}saveExamAnswer('{{ row['qid'] }}', '{{ row['题型'] }}'){% endif %}">
                {{ opt }}. {{ row['选项' + opt] }}
              </label>
            {% endif %}
          {% endfor %}
          {% if exam_mode == 'practice' and row['题型'] == '多选' %}
            <button class="primary-btn" type="button" onclick="checkMultiAnswer('{{ row['qid'] }}')">确认本题答案</button>
          {% endif %}
        {% elif row['题型'] == '判断' %}
          <label>
            <input type="radio" name="{{ row['qid'] }}" value="A"
                   {% if saved_answer == 'A' %}checked{% endif %}
                   {% if submitted_result %}disabled{% endif %}
                   onchange="{% if exam_mode == 'practice' %}checkSingleAnswer(this){% elif exam_mode == 'exam' %}saveExamAnswer('{{ row['qid'] }}', '判断'){% endif %}">
            对
          </label>
          <label>
            <input type="radio" name="{{ row['qid'] }}" value="B"
                   {% if saved_answer == 'B' %}checked{% endif %}
                   {% if submitted_result %}disabled{% endif %}
                   onchange="{% if exam_mode == 'practice' %}checkSingleAnswer(this){% elif exam_mode == 'exam' %}saveExamAnswer('{{ row['qid'] }}', '判断'){% endif %}">
            错
          </label>
        {% endif %}

        <div class="feedback{% if detail %} {{ 'correct' if detail['earned_score'] == detail['max_score'] else 'wrong' }}{% endif %}">
          {% if detail %}
            你的答案：<b class="{{ 'right-text' if detail['earned_score'] == detail['max_score'] else 'wrong-text' }}">{{ detail['display_user_answer'] }}</b><br>
            正确答案：<b>{{ detail['display_correct_answer'] }}</b><br>
            得分：{{ detail['earned_score'] }} / {{ detail['max_score'] }}
          {% endif %}
        </div>
      </div>
    {% endfor %}

    {% if exam_mode == 'exam' %}
      <div class="action-row">
        <button id="submit-btn" class="secondary-btn" type="button" onclick="submitExam(false)" {% if submitted_result %}disabled{% endif %}>提交试卷</button>
      </div>
    {% endif %}
  </form>

<script>
const examMode = {{ exam_mode|tojson }};
const remainingSecondsOnLoad = {{ remaining_seconds }};
const totalScore = {{ total_score }};
const submittedResult = {{ submitted_result|tojson }};
let examSubmitted = {{ 'true' if submitted_result else 'false' }};
let countdownTimer = null;

function normalizeAnswerText(questionType, answer) {
  if (questionType === '判断') {
    return answer === 'A' ? '对' : answer === 'B' ? '错' : (answer || '未作答');
  }
  return answer || '未作答';
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

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return response.json();
}

async function saveExamAnswer(qid, questionType) {
  if (examMode !== 'exam' || examSubmitted) return;
  const answer = getSelectedAnswers(qid, questionType);
  const data = await postJson('/exam/save_answer', { qid, answer });

  if (data.status === 'submitted') {
    applyExamResult(data.result);
  }
}

function buildExamFeedback(container, detail) {
  const isCorrect = detail.earned_score === detail.max_score;
  const answerClass = isCorrect ? 'right-text' : 'wrong-text';
  return {
    feedbackClass: isCorrect ? 'correct' : 'wrong',
    html: '你的答案：<b class="' + answerClass + '">' + detail.display_user_answer + '</b><br>'
      + '正确答案：<b>' + detail.display_correct_answer + '</b><br>'
      + '得分：' + detail.earned_score + ' / ' + detail.max_score,
  };
}

function applyExamResult(result) {
  examSubmitted = true;
  if (countdownTimer) {
    clearInterval(countdownTimer);
  }

  const resultBanner = document.getElementById('result-banner');
  document.getElementById('result-score').textContent = '本次得分：' + result.score + ' / ' + totalScore;
  document.getElementById('result-summary').textContent = result.summary;
  resultBanner.classList.add('show');

  Object.entries(result.details).forEach(([qid, detail]) => {
    const container = document.querySelector("[data-qid='" + qid + "']");
    if (!container) return;
    const feedbackData = buildExamFeedback(container, detail);
    const feedback = container.querySelector('.feedback');
    feedback.className = 'feedback ' + feedbackData.feedbackClass;
    feedback.innerHTML = feedbackData.html;
  });

  document.querySelectorAll('#exam-form input, #exam-form button').forEach(el => {
    el.disabled = true;
  });
}

async function submitExam(isAutoSubmit) {
  if (examMode !== 'exam' || examSubmitted) return;
  const data = await postJson('/exam/submit', { auto_submit: isAutoSubmit });
  applyExamResult(data);
  document.getElementById('result-banner').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function startExamTimer() {
  if (examMode !== 'exam' || examSubmitted) return;

  let remainingSeconds = remainingSecondsOnLoad;
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

if (submittedResult) {
  applyExamResult(submittedResult);
} else {
  startExamTimer();
}
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


def build_question_records(df):
    records = []
    for index, row in build_sampled_questions(df).iterrows():
        record = {
            'qid': f'q{index}',
            '题型': row['题型'],
            '题干': row['题干'],
            '选项A': None if pd.isna(row.get('选项A')) else row.get('选项A'),
            '选项B': None if pd.isna(row.get('选项B')) else row.get('选项B'),
            '选项C': None if pd.isna(row.get('选项C')) else row.get('选项C'),
            '选项D': None if pd.isna(row.get('选项D')) else row.get('选项D'),
            '选项E': None if pd.isna(row.get('选项E')) else row.get('选项E'),
            '选项F': None if pd.isna(row.get('选项F')) else row.get('选项F'),
            '正确答案': row['正确答案'],
        }
        records.append(record)
    return records


def build_exam_state(exam_title):
    return {
        'exam_id': uuid.uuid4().hex,
        'exam_title': exam_title,
        'questions': build_question_records(title_to_df[exam_title]),
        'start_ts': int(time.time()),
        'answers': {},
        'submitted': False,
        'result': None,
    }


def get_active_exam():
    return session.get('active_exam')


def clear_active_exam():
    session.pop('active_exam', None)


def get_remaining_seconds(exam_state):
    elapsed = int(time.time()) - int(exam_state['start_ts'])
    return max(0, EXAM_DURATION_MINUTES * 60 - elapsed)


def display_answer(question_type, answer):
    if not answer:
        return '未作答'
    if question_type == '判断':
        return '对' if answer == 'A' else '错' if answer == 'B' else answer
    return answer


def compute_exam_result(exam_state, is_auto_submit=False):
    if exam_state.get('submitted') and exam_state.get('result'):
        return exam_state['result']

    details = {}
    score = 0

    for question in exam_state['questions']:
        qid = question['qid']
        question_type = question['题型']
        max_score = SCORE_RULES[question_type]
        correct_answer = question['正确答案']
        user_answer = exam_state['answers'].get(qid, '')
        earned_score = max_score if user_answer == correct_answer else 0

        score += earned_score
        details[qid] = {
            'question_type': question_type,
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'display_user_answer': display_answer(question_type, user_answer),
            'display_correct_answer': display_answer(question_type, correct_answer),
            'earned_score': earned_score,
            'max_score': max_score,
        }

    result = {
        'score': score,
        'summary': '时间已到，系统已自动交卷。以下为本次考试答案与得分。'
        if is_auto_submit else
        '你已提交试卷。以下为本次考试答案与得分。',
        'details': details,
        'auto_submitted': is_auto_submit,
    }

    exam_state['submitted'] = True
    exam_state['result'] = result
    session['active_exam'] = exam_state
    session.modified = True
    return result


def ensure_exam_state(exam_title):
    exam_state = get_active_exam()
    if exam_state and exam_state.get('exam_title') == exam_title:
        if not exam_state.get('submitted') and get_remaining_seconds(exam_state) == 0:
            compute_exam_result(exam_state, is_auto_submit=True)
            exam_state = get_active_exam()
        return exam_state

    exam_state = build_exam_state(exam_title)
    session['active_exam'] = exam_state
    session.modified = True
    return exam_state


def parse_exam_mode():
    return session.get('exam_mode', 'practice')


def total_score():
    return (
        SAMPLE_SIZES['单选'] * SCORE_RULES['单选']
        + SAMPLE_SIZES['多选'] * SCORE_RULES['多选']
        + SAMPLE_SIZES['判断'] * SCORE_RULES['判断']
    )


@app.route('/', methods=['GET', 'POST'])
def choose_exam():
    if request.method == 'POST':
        exam_title = request.form['exam_title']
        exam_mode = request.form.get('exam_mode', 'practice')
        session['exam_title'] = exam_title
        session['exam_mode'] = exam_mode

        if exam_mode == 'exam':
            session['active_exam'] = build_exam_state(exam_title)
            session.modified = True
        else:
            clear_active_exam()

        return redirect(url_for('exam'))

    return render_template_string(HOME_TEMPLATE, titles=title_to_df.keys())


@app.route('/exam')
def exam():
    exam_title = session.get('exam_title')
    if exam_title not in title_to_df:
        exam_title = next(iter(title_to_df))
        session['exam_title'] = exam_title
    exam_mode = parse_exam_mode()

    if exam_mode == 'exam':
        exam_state = ensure_exam_state(exam_title)
        submitted_result = exam_state.get('result') if exam_state.get('submitted') else None
        submitted_details = submitted_result['details'] if submitted_result else {}
        remaining_seconds = 0 if submitted_result else get_remaining_seconds(exam_state)
        questions = exam_state['questions']
        saved_answers = exam_state.get('answers', {})
    else:
        questions = build_question_records(title_to_df[exam_title])
        submitted_result = None
        submitted_details = {}
        remaining_seconds = 0
        saved_answers = {}

    initial_timer_text = (
        f"{remaining_seconds // 60:02d}:{remaining_seconds % 60:02d}"
        if exam_mode == 'exam' else ''
    )

    return render_template_string(
        EXAM_TEMPLATE,
        questions=questions,
        title=exam_title,
        exam_mode=exam_mode,
        mode_name='练习模式' if exam_mode == 'practice' else '考试模式',
        initial_timer_text=initial_timer_text,
        remaining_seconds=remaining_seconds,
        score_rules=SCORE_RULES,
        total_score=total_score(),
        saved_answers=saved_answers,
        submitted_result=submitted_result,
        submitted_details=submitted_details,
    )


@app.route('/exam/save_answer', methods=['POST'])
def save_answer():
    exam_state = get_active_exam()
    if not exam_state:
        return jsonify({'status': 'missing'})

    if exam_state.get('submitted'):
        return jsonify({'status': 'submitted', 'result': exam_state['result']})

    if get_remaining_seconds(exam_state) == 0:
        result = compute_exam_result(exam_state, is_auto_submit=True)
        return jsonify({'status': 'submitted', 'result': result})

    payload = request.get_json(silent=True) or {}
    qid = payload.get('qid')
    answer = payload.get('answer', '')

    if qid:
        exam_state['answers'][qid] = answer
        session['active_exam'] = exam_state
        session.modified = True

    return jsonify({'status': 'ok'})


@app.route('/exam/submit', methods=['POST'])
def submit_exam():
    exam_state = get_active_exam()
    if not exam_state:
        return jsonify({'score': 0, 'summary': '未找到有效考试。', 'details': {}, 'auto_submitted': False})

    payload = request.get_json(silent=True) or {}
    is_auto_submit = bool(payload.get('auto_submit'))
    result = compute_exam_result(exam_state, is_auto_submit=is_auto_submit)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=False)
