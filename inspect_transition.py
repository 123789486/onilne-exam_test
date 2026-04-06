import re

def inspect():
    with open('temp_bank.txt', 'r', encoding='gb18030', errors='ignore') as f:
        text = f.read()
    
    # Standardize
    text = text.replace('【多选】', '【多选题】')
    
    m = list(re.finditer(r'【多选题】', text))
    print(f"Total Multi-Choice found: {len(m)}")
    
    # Sample specifically around the range where it might have broken
    # Row 1345 starts around the beginning of multi-choice (which starts at 1400 total)
    # Actually, the user says 1345 to 2265.
    # Total Single: 1400. So 1345 is near the end of Single-Choice!
    # Let's check Single Choice end and Multi Choice start.
    
    ms = list(re.finditer(r'【单选题】', text))
    print(f"Total Single-Choice found: {len(ms)}")
    
    print("\n--- Last few Single-Choice Questions ---")
    for i in range(len(ms)-5, len(ms)):
        start = ms[i].start()
        end = text.find('【', start + 10)
        print(text[start:end or start+500])
        print("---")
        
    print("\n\n--- First few Multi-Choice Questions ---")
    for i in range(min(5, len(m))):
        start = m[i].start()
        end = text.find('【', start + 10)
        print(text[start:end or start+500])
        print("---")

if __name__ == "__main__":
    inspect()
