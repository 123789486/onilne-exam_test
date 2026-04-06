import re

txt_path = r"d:\桌面文件夹\onilne-exam\onilne-exam_test\temp_bank.txt"

def inspect():
    with open(txt_path, 'r', encoding='gb18030', errors='ignore') as f:
        text = f.read()
    
    # Standardize
    text = text.replace('【多选】', '【多选题】')
    
    # Find positions of 多选题
    matches = list(re.finditer(r'【多选题】', text))
    print(f"Total 多选题 markers found: {len(matches)}")
    
    if len(matches) > 0:
        print("\n--- Inspecting first Multi-Choice Question (index 0) ---")
        start = matches[0].start()
        # Find next block or end of text
        next_m = re.search(r'【', text[start+10:])
        end = (start + 10 + next_m.start()) if next_m else len(text)
        print(text[start:end])
        
        print("\n--- Inspecting row around 1345 (which is middle of list) ---")
        # Let's say we find the 200th multi-choice (approx offset)
        idx = min(len(matches)-1, 200)
        start = matches[idx].start()
        next_m = re.search(r'【', text[start+10:])
        end = (start + 10 + next_m.start()) if next_m else len(text)
        print(text[start:end])

if __name__ == "__main__":
    inspect()
