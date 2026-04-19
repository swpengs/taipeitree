import csv
import math
import json
import os
import shutil
import urllib.request
import filecmp
from datetime import datetime

# 配置資訊
DATA_URL = "https://tppkl.blob.core.windows.net/blobfs/TaipeiTree.csv"
INPUT_CSV = "uploads/TaipeiTree.csv"
OUTPUT_JS = "data/tree-data.js"

# TWD97 (TM2) to WGS84 (Lat/Lon) conversion constants
A = 6378137.0
B = 6356752.314140356
LONG0 = 121.0 * math.pi / 180
K0 = 0.9999
DX = 250000

def twd97_to_wgs84(x, y):
    """將 TWD97 (TM2) 座標轉換為 WGS84 經緯度"""
    e = math.sqrt(1 - (B**2) / (A**2))
    e2 = e**2 / (1 - e**2)
    m = y / K0
    mu = m / (A * (1 - e**2/4 - 3*e**4/64 - 5*e**6/256))
    e1 = (1 - math.sqrt(1 - e**2)) / (1 + math.sqrt(1 - e**2))
    j1 = (3*e1/2 - 27*e1**3/32)
    j2 = (21*e1**2/16 - 55*e1**4/32)
    j3 = (151*e1**3/96)
    j4 = (1097*e1**4/512)
    phi1 = mu + j1*math.sin(2*mu) + j2*math.sin(4*mu) + j3*math.sin(6*mu) + j4*math.sin(8*mu)
    c1 = e2 * math.cos(phi1)**2
    t1 = math.tan(phi1)**2
    n1 = A / math.sqrt(1 - e**2 * math.sin(phi1)**2)
    r1 = A * (1 - e**2) / (1 - e**2 * math.sin(phi1)**2)**1.5
    d = (x - DX) / (n1 * K0)
    phi = phi1 - (n1 * math.tan(phi1) / r1) * (d**2/2 - (5 + 3*t1 + 10*c1 - 4*c1**2 - 9*e2)*d**4/24 + (61 + 90*t1 + 298*c1 + 45*t1**2 - 252*e2 - 3*c1**2)*d**6/720)
    lon = LONG0 + (d - (1 + 2*t1 + c1)*d**3/6 + (5 - 2*c1 + 28*t1 - 3*c1**2 + 8*e2 + 24*t1**2)*d**5/120) / math.cos(phi1)
    return math.degrees(phi), math.degrees(lon)

def download_and_backup():
    """下載最新資料並備份舊有 CSV"""
    os.makedirs("uploads", exist_ok=True)
    
    backup_path = None
    if os.path.exists(INPUT_CSV):
        # 產生備份檔名: TaipeiTree_YYYY-MM-DD_HH_mm_ss.csv
        timestamp = datetime.now().strftime("_%Y-%m-%d_%H_%M_%S")
        backup_path = INPUT_CSV.replace(".csv", f"{timestamp}.csv")
        print(f"正在備份舊資料至: {backup_path}")
        shutil.copy2(INPUT_CSV, backup_path)
    
    print(f"正在從資料源下載最新資料: {DATA_URL}")
    try:
        urllib.request.urlretrieve(DATA_URL, INPUT_CSV)
        print("下載完成。")
        
        # 比對新下載的檔案與備份檔
        if backup_path and os.path.exists(backup_path):
            if filecmp.cmp(INPUT_CSV, backup_path, shallow=False):
                print("資料內容與舊版完全相同，移除重複的備份檔。")
                os.remove(backup_path)
            else:
                print("偵測到資料更新，保留備份檔。")
                
        return True
    except Exception as e:
        print(f"下載失敗: {e}")
        return False

def convert():
    """將 CSV 轉換為壓縮後的 JS 格式"""
    if not os.path.exists(INPUT_CSV):
        print(f"錯誤: 找不到輸入檔案 {INPUT_CSV}")
        return

    species, dists, regions, remarks = [], [], [], []
    species_map, dist_map, region_map, remark_map = {}, {}, {}, {}
    
    def get_idx(val, list_obj, map_obj):
        val = val.strip()
        if val not in map_obj:
            map_obj[val] = len(list_obj)
            list_obj.append(val)
        return map_obj[val]

    rows_data = []
    print(f"正在解析 {INPUT_CSV}...")
    
    with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # 座標轉換
                lat, lon = twd97_to_wgs84(float(row['TWD97X']), float(row['TWD97Y']))
                
                # 建立索引
                s_idx = get_idx(row['TreeType'], species, species_map)
                d_idx = get_idx(row['Dist'], dists, dist_map)
                r_idx = get_idx(row['Region'], regions, region_map)
                rm_idx = get_idx(row['RegionRemark'], remarks, remark_map)
                
                # 數值處理：採用與 JS Math.round 一致的四捨五入
                f_dia = float(row['Diameter'])
                dia = int(f_dia + 0.5) if f_dia >= 0 else int(f_dia - 0.5)
                
                f_height = float(row['TreeHeight'])
                height = int(f_height * 10 + 0.5) / 10.0 if f_height >= 0 else int(f_height * 10 - 0.5) / 10.0
                
                # 使用 Tab 分隔欄位，符合原始 JS 格式邏輯
                row_str = f"{lat:.6f}\t{lon:.6f}\t{s_idx}\t{d_idx}\t{r_idx}\t{rm_idx}\t{dia}\t{height}\t{row['TreeID']}\t{row['SurveyDate']}"
                rows_data.append(row_str)
            except Exception as e:
                # 忽略解析失敗的筆數
                pass

    print(f"正在產生 {OUTPUT_JS}...")
    os.makedirs(os.path.dirname(OUTPUT_JS), exist_ok=True)
    with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
        f.write(f"window.TREE_SPECIES = {json.dumps(species, ensure_ascii=False)};\n")
        f.write(f"window.TREE_DISTS = {json.dumps(dists, ensure_ascii=False)};\n")
        f.write(f"window.TREE_REGIONS = {json.dumps(regions, ensure_ascii=False)};\n")
        f.write(f"window.TREE_REMARKS = {json.dumps(remarks, ensure_ascii=False)};\n")
        f.write(f'window.TREE_ROWS_RAW = "{"\\n".join(rows_data)}";\n')
        f.write("window.TREE_ROWS = null; // parsed lazily\n")

    print(f"更新完成！共處理 {len(rows_data)} 筆樹木資料。")

if __name__ == "__main__":
    if download_and_backup():
        convert()
