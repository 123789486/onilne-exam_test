import pandas as pd
import os

base_path = r"d:\桌面文件夹\onilne-exam\onilne-exam_test"
file_name = "13.账户营运业务题库（2026年修订）总行上传.xls"

mapping_qtype = {
    '单选题': '单选',
    '多选题': '多选',
    '判断题': '判断',
    '问答题': '简答'
}

def standardize():
    file_path = os.path.join(base_path, file_name)
    print(f"Processing: {file_name}")
    
    try:
        df_orig = pd.read_excel(file_path, engine='xlrd')
    except Exception as e:
        print(f"Error reading {file_name}: {e}")
        return

    standard_data = []
    
    for _, row in df_orig.iterrows():
        qtype_orig = str(row.get('试题类型', '')).strip()
        qtype = mapping_qtype.get(qtype_orig, qtype_orig)
        
        qcontent = str(row.get('试题内容', '')).strip()
        
        # Options - Note the lowercase keys from the source Excel
        optA = row.get('选项a')
        optB = row.get('选项b')
        optC = row.get('选项c')
        optD = row.get('选项d')
        optE = row.get('选项e')
        optF = row.get('选项f')
        
        answer = str(row.get('答案', '')).strip()
        
        if qtype == '判断':
            optA = '正确'
            optB = '错误'
            optC = None
            optD = None
            # Standardize answer for judgement
            if '正' in answer or '对' in answer or 'A' in answer:
                answer = 'A'
            elif '误' in answer or '错' in answer or 'B' in answer:
                answer = 'B'
        
        if qtype == '多选':
            answer = "".join(sorted([c for c in answer if c.upper() in 'ABCDEF']))

        standard_data.append({
            '题型': qtype,
            '题干': qcontent,
            '选项A': optA,
            '选项B': optB,
            '选项C': optC,
            '选项D': optD,
            '选项E': optE,
            '选项F': optF,
            '正确答案': answer,
            '分值': 1
        })
    
    df_std = pd.DataFrame(standard_data)
    output_name = "题库13_标准化.xlsx"
    output_path = os.path.join(base_path, output_name)
    df_std.to_excel(output_path, index=False)
    print(f"Saved to: {output_name}")

if __name__ == '__main__':
    standardize()
