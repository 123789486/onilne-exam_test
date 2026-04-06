import os
import re
import pandas as pd

# Path configuration
txt_path = r"d:\桌面文件夹\onilne-exam\onilne-exam_test\temp_bank.txt"
output_path = r"d:\桌面文件夹\onilne-exam\onilne-exam_test\题库_竞赛_标准化.xlsx"

def clean_text(text):
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Standardize full-width characters commonly used in Chinese Word docs
    text = text.replace('．', '.').replace('、', '.').replace('：', ':')
    return text

def parse_questions(text):
    print("Parsing questions with REVISED robust logic...")
    
    # Standardize markers
    text = text.replace('【单选】', '【单选题】')
    text = text.replace('【多选】', '【多选题】')
    
    # Define split markers for questions
    # 1. 【题型】 labels
    # 2. Numbered questions like 1. or 2. if they appear at start of line
    # 3. '---' if it seems to separate questions
    
    # Strategy: First, split into huge blocks by the main labels
    # Then refine each block if it contains multiple questions (based on multiple answer labels)
    
    initial_blocks = re.split(r'(?=【(?:单选题|多选题|判断题)】)', text)
    
    all_questions = []
    
    for block in initial_blocks:
        block = block.strip()
        if not block:
            continue
            
        # Detect Type
        type_match = re.match(r'【(单选题|多选题|判断题)】', block)
        current_type_raw = type_match.group(1) if type_match else "单选题" # Fallback to single
        current_type = {'单选题': '单选', '多选题': '多选', '判断题': '判断'}.get(current_type_raw, current_type_raw)
        
        # This block might contain multiple questions if the labels were missing
        # We look for all answer markers: 【正确答案】:X or ---X or ---答案:X
        # Also handle metadata like 1ABC where 1 is the value
        
        # Split block into individual questions by looking for answer markers
        # A question ends after its answer.
        
        # Regex for answer markers:
        # Match 【正确答案】... OR --- followed by some letters at the end of a block/line
        ans_pattern = r'(?:【正确答案】[:： ]*|---[:： ]*)([A-Fa-f对错√×.0-9\s]+)'
        
        # We'll split the block into question-answer pairs
        # Finding all indices of answer markers
        ans_matches = list(re.finditer(ans_pattern, block))
        
        last_pos = 0
        for match in ans_matches:
            # The question content is from last_pos to match.start()
            q_content = block[last_pos:match.start()].strip()
            # If the first question had a type marker, remove it from the content
            if last_pos == 0 and type_match:
                q_content = q_content[len(type_match.group(0)):].strip()
            
            # Extract Answer from match
            raw_ans = match.group(1).strip()
            # Clean answer: keep only letters A-F or specific Chinese markers
            answer = ""
            if current_type == '判断':
                if any(x in raw_ans for x in ['对', '正确', '√', 'A']): answer = 'A'
                elif any(x in raw_ans for x in ['错', '错误', '×', 'B']): answer = 'B'
                else: answer = 'A' # fallback
            else:
                # Keep only A-F letters, ignoring numbers and punctuation
                answer = "".join(re.findall(r'[A-Fa-f]', raw_ans)).upper()
                if current_type == '多选':
                    answer = "".join(sorted(list(set(answer))))
                else:
                    answer = answer[:1]
            
            # Process Stem and Options
            stem = q_content
            options = {'A': None, 'B': None, 'C': None, 'D': None, 'E': None, 'F': None}
            
            if current_type != '判断':
                # Find options like A. B. C.
                opt_pattern = r'(?:\s|^)([A-F])[.\s]\s*'
                parts = re.split(opt_pattern, q_content)
                if len(parts) > 1:
                    stem = parts[0].strip()
                    for i in range(1, len(parts), 2):
                        opt_key = parts[i].upper()
                        if i + 1 < len(parts):
                            opt_val = parts[i+1].strip()
                            if opt_key in options:
                                options[opt_key] = opt_val
            else:
                options['A'] = '正确'
                options['B'] = '错误'

            # Basic stem cleaning (remove question numbers if they exist like 1. 2.)
            stem = re.sub(r'^\d+[.\s]+', '', stem)
            # Remove lingering '---' or labels at the end of stem
            stem = re.sub(r'---.*$', '', stem).strip()

            if stem and answer:
                all_questions.append({
                    '题型': current_type,
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
            
            last_pos = match.end()

    return all_questions

def main():
    if not os.path.exists(txt_path):
        print(f"Error: {txt_path} not found. Please recreate it from Word doc.")
        return
        
    try:
        with open(txt_path, 'r', encoding='gb18030', errors='ignore') as f:
            raw_text = f.read()
            
        clean_raw = clean_text(raw_text)
        data = parse_questions(clean_raw)
        
        if not data:
            print("No questions successfully parsed.")
            return
            
        df = pd.DataFrame(data)
        
        # Deduplication based on stem and type
        prev_count = len(df)
        df = df.drop_duplicates(subset=['题型', '题干'])
        if len(df) < prev_count:
            print(f"Removed {prev_count - len(df)} duplicate questions.")

        def excel_safe(val):
            if isinstance(val, str):
                return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', val)
            return val
        df = df.map(excel_safe)
        
        df.to_excel(output_path, index=False)
        print(f"\nREVISED Parsing Success!")
        print(f"Total entries: {len(df)}")
        print(df['题型'].value_counts())
        
        # Verify the range the user mentioned (roughly)
        print("\nChecking range 1345-1350 for sanity:")
        print(df.iloc[1344:1350][['题型', '题干', '正确答案']].to_string())
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
