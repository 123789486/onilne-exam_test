import os
import re
import pandas as pd

# Path configuration
txt_path = r"d:\桌面文件夹\onilne-exam\onilne-exam_test\temp_bank.txt"
output_path = r"d:\桌面文件夹\onilne-exam\onilne-exam_test\题库_竞赛_标准化.xlsx"

def clean_text(text):
    # Word text usually uses GB18030 or similar. If we read it correctly it's fine.
    # Standard cleanup for safe Excel saving
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text

def parse_questions(text):
    print("Parsing questions from text file...")
    # Standardize markers
    text = text.replace('【单选】', '【单选题】')
    text = text.replace('【多选】', '【多选题】')
    
    # Split by blocks starting with 【类型】
    blocks = re.split(r'(?=【(?:单选题|多选题|判断题)】)', text)
    
    questions = []
    
    for block in blocks:
        block = block.strip()
        if not block or '正确答案' not in block:
            continue
            
        # Extract Type
        type_match = re.match(r'【(单选题|多选题|判断题)】', block)
        if not type_match:
            continue
        
        q_type_raw = type_match.group(1)
        q_type = {
            '单选题': '单选',
            '多选题': '多选',
            '判断题': '判断'
        }.get(q_type_raw, q_type_raw)
        
        # Extract Answer
        ans_find = re.search(r'【正确答案】[：: ]*([A-Za-z对错√×\s,]+)', block)
        if not ans_find:
            continue
        
        raw_ans = ans_find.group(1).strip()
        
        # Get content between type and answer
        content = block[len(type_match.group(0)):ans_find.start()].strip()
        
        stem = ""
        options = {'A': None, 'B': None, 'C': None, 'D': None, 'E': None, 'F': None}
        
        if q_type == '判断':
            stem = content
            options['A'] = '正确'
            options['B'] = '错误'
            if any(x in raw_ans for x in ['对', '正确', '√', 'A']):
                answer = 'A'
            elif any(x in raw_ans for x in ['错', '错误', '×', 'B']):
                answer = 'B'
            else:
                answer = raw_ans
        else:
            # Single/Multi Choice
            # Split using a pattern that avoids decimal numbers
            # We look for A. or A、 or B. or B、
            pattern = re.compile(r'\s*([A-F])[.、]\s*')
            parts = pattern.split(content)
            
            if len(parts) > 1:
                stem = parts[0].strip()
                # parts[1] is 'A', parts[2] is text A, parts[3] is 'B', etc.
                for i in range(1, len(parts), 2):
                    opt_key = parts[i].upper()
                    if i + 1 < len(parts):
                        opt_val = parts[i+1].strip()
                        if opt_key in options:
                            options[opt_key] = opt_val
            else:
                stem = content

            # Multi answer cleanup
            if q_type == '多选':
                answer = "".join(sorted([c for c in raw_ans.upper() if c in 'ABCDEF']))
            else:
                answer = "".join([c for c in raw_ans.upper() if c in 'ABCDEF'])[:1]

        questions.append({
            '题型': q_type,
            '题干': stem.replace('\r', ' ').replace('\n', ' '),
            '选项A': options['A'],
            '选项B': options['B'],
            '选项C': options['C'],
            '选项D': options['D'],
            '选项E': options['E'], 
            '选项F': options['F'],
            '正确答案': answer,
            '分值': 1
        })
        
    return questions

def main():
    if not os.path.exists(txt_path):
        print(f"Error: {txt_path} not found.")
        return
        
    try:
        # docx text files are often encoded in ANSI or UTF-16
        with open(txt_path, 'r', encoding='gb18030', errors='ignore') as f:
            raw_text = f.read()
            
        clean_raw = clean_text(raw_text)
        data = parse_questions(clean_raw)
        
        if not data:
            print("No questions successfully parsed.")
            return
            
        df = pd.DataFrame(data)
        def excel_safe(val):
            if isinstance(val, str):
                return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', val)
            return val
        df = df.applymap(excel_safe)
        
        df.to_excel(output_path, index=False)
        print(f"\nParsing Success!")
        print(f"Total entries: {len(df)}")
        print(df['题型'].value_counts())
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
