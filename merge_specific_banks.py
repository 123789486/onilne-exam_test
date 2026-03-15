import pandas as pd
import os

base_path = r"d:\桌面文件夹\onilne-exam\onilne-exam_test"
target_files = [
    "题库1_标准化.xlsx",
    "题库2_标准化.xlsx",
    "题库4_标准化.xlsx",
    "题库5_标准化.xlsx",
    "题库6_标准化.xlsx",
    "题库7_标准化.xlsx",
    "题库13_标准化.xlsx"
]

def merge_banks():
    print("Starting merge process...")
    dfs = []
    total_rows = 0
    
    for file_name in target_files:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            print(f"Loading: {file_name}")
            df = pd.read_excel(file_path)
            dfs.append(df)
            total_rows += len(df)
            print(f"  Rows: {len(df)}")
        else:
            print(f"Warning: {file_name} not found!")
    
    if not dfs:
        print("No dataframes to merge.")
        return

    combined_df = pd.concat(dfs, ignore_index=True)
    output_name = "合并题库_标准化.xlsx"
    output_path = os.path.join(base_path, output_name)
    
    combined_df.to_excel(output_path, index=False)
    print(f"\nSuccessfully merged {len(dfs)} files.")
    print(f"Total rows in combined bank: {len(combined_df)} (Original sum: {total_rows})")
    print(f"Saved to: {output_name}")

if __name__ == "__main__":
    merge_banks()
