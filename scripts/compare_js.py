import re
import json
import math
import sys

def parse_tree_js(filepath):
    """解析 tree-data.js 並將資料提取為 Python 物件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"無法讀取檔案 {filepath}: {e}")
        return None

    data = {}
    # 提取對照表 (Arrays)
    for var_name in ['TREE_SPECIES', 'TREE_DISTS', 'TREE_REGIONS', 'TREE_REMARKS']:
        pattern = rf'window\.{var_name}\s*=\s*(\[.*?\]);'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            data[var_name] = json.loads(match.group(1))
        else:
            data[var_name] = []

    # 提取原始資料字串 (String)
    row_pattern = r'window\.TREE_ROWS_RAW\s*=\s*"(.*?)";'
    match = re.search(row_pattern, content, re.DOTALL)
    if match:
        raw_str = match.group(1)
        # 處理 JS 字串中的轉義符號
        # 1. 將字面上的 \t 轉義序列替換為真正的 Tab (如果是 B 檔案則已經是 Tab)
        raw_str = raw_str.replace('\\t', '\t')
        # 2. 根據 \n 轉義序列進行切割
        data['ROWS'] = raw_str.split('\\n')
    else:
        data['ROWS'] = []
    
    return data

def compare_js_files(file_a, file_b):
    print(f"正在比對:\n  A: {file_a}\n  B: {file_b}\n")
    
    data_a = parse_tree_js(file_a)
    data_b = parse_tree_js(file_b)
    
    if not data_a or not data_b:
        return

    is_equal = True

    # 1. 比對對照表內容
    for table in ['TREE_SPECIES', 'TREE_DISTS', 'TREE_REGIONS', 'TREE_REMARKS']:
        list_a = data_a[table]
        list_b = data_b[table]
        if list_a == list_b:
            print(f"✅ {table}: 完全一致 (長度: {len(list_a)})")
        else:
            is_equal = False
            print(f"❌ {table}: 不一致!")
            print(f"   A 長度: {len(list_a)}, B 長度: {len(list_b)}")
            # 顯示前幾個差異
            diffs = [(i, a, b) for i, (a, b) in enumerate(zip(list_a, list_b)) if a != b]
            if diffs:
                print(f"   前幾個差異點: {diffs[:3]}")

    # 2. 比對樹木資料筆數
    rows_a = data_a['ROWS']
    rows_b = data_b['ROWS']
    
    if len(rows_a) != len(rows_b):
        is_equal = False
        print(f"❌ 資料筆數不一致! A: {len(rows_a)}, B: {len(rows_b)}")
    else:
        print(f"✅ 資料筆數一致: {len(rows_a)} 筆")

    # 3. 逐筆詳細比對 (抽樣或全比)
    print("正在逐筆比對欄位資料...")
    diff_count = 0
    max_diff_to_show = 5
    
    # 定義欄位索引
    # [lat, lon, s, d, r, rm, dia, h, id, date]
    for i in range(min(len(rows_a), len(rows_b))):
        cols_a = rows_a[i].split('\t')
        cols_b = rows_b[i].split('\t')
        
        if len(cols_a) != len(cols_b):
            diff_count += 1
            if diff_count <= max_diff_to_show:
                print(f"   筆數 {i} 欄位數量不一致 (ID: {cols_a[8] if len(cols_a)>8 else 'N/A'})")
            continue

        # 欄位解析比對
        try:
            # 經緯度與高度比對 (容許極小誤差)
            lat_a, lat_b = float(cols_a[0]), float(cols_b[0])
            lon_a, lon_b = float(cols_a[1]), float(cols_b[1])
            h_a, h_b = float(cols_a[7]), float(cols_b[7])
            
            # 索引與 ID/日期 (必須精確相等)
            # s, d, r, rm, dia, id, date
            cat_match = cols_a[2:7] == cols_b[2:7] and cols_a[8:] == cols_b[8:]
            
            coord_match = math.isclose(lat_a, lat_b, rel_tol=1e-7) and \
                          math.isclose(lon_a, lon_b, rel_tol=1e-7)
            
            height_match = math.isclose(h_a, h_b, abs_tol=0.1)

            if not (cat_match and coord_match and height_match):
                diff_count += 1
                if diff_count <= max_diff_to_show:
                    print(f"   第 {i} 筆發現差異 (ID: {cols_a[8]}):")
                    print(f"     A: {cols_a}")
                    print(f"     B: {cols_b}")
        except Exception as e:
            diff_count += 1
            if diff_count <= max_diff_to_show:
                print(f"   解析第 {i} 筆時發生錯誤: {e}")

    if diff_count == 0:
        print("✅ 欄位詳細資料: 全部等效一致")
    else:
        is_equal = False
        print(f"❌ 共發現 {diff_count} 筆資料存在差異")

    if is_equal:
        print("\n總結: 兩個 JS 檔案在功能與資料上【完全等效】。")
    else:
        print("\n總結: 檔案之間存在實質差異。")

if __name__ == "__main__":
    file_bak = 'data/tree-data.js.bak'
    file_new = 'data/tree-data.js'
    compare_js_files(file_bak, file_new)
