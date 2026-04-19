import csv
import math
import json
import os

# TWD97 (TM2) to WGS84 (Lat/Lon) conversion constants
# Ellipsoid: GRS80
A = 6378137.0
B = 6356752.314140356
LONG0 = 121.0 * math.pi / 180
K0 = 0.9999
DX = 250000

def twd97_to_wgs84(x, y):
    """
    Converts TWD97 (TM2) coordinates to WGS84 (Latitude, Longitude).
    """
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

def convert():
    input_csv = 'uploads/TaipeiTree.csv'
    output_js = 'data/tree-data.js'
    
    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} not found.")
        return

    species = []
    dists = []
    regions = []
    remarks = []
    
    species_map = {}
    dist_map = {}
    region_map = {}
    remark_map = {}
    
    def get_idx(val, list_obj, map_obj):
        val = val.strip()
        if val not in map_obj:
            map_obj[val] = len(list_obj)
            list_obj.append(val)
        return map_obj[val]

    rows_data = []
    
    print(f"Reading {input_csv}...")
    with open(input_csv, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Coordinate conversion
                x = float(row['TWD97X'])
                y = float(row['TWD97Y'])
                lat, lon = twd97_to_wgs84(x, y)
                
                # Index mapping
                s_idx = get_idx(row['TreeType'], species, species_map)
                d_idx = get_idx(row['Dist'], dists, dist_map)
                r_idx = get_idx(row['Region'], regions, region_map)
                rm_idx = get_idx(row['RegionRemark'], remarks, remark_map)
                
                # Format diameter and height
                # Diameter is integer in JS (Uint8Array)
                try:
                    # JavaScript Math.round style: always round half up
                    f_dia = float(row['Diameter'])
                    dia = int(f_dia + 0.5) if f_dia >= 0 else int(f_dia - 0.5)
                except:
                    dia = 0
                
                # Height is float
                try:
                    f_height = float(row['TreeHeight'])
                    # Round to 1 decimal place, half up
                    height = int(f_height * 10 + 0.5) / 10.0 if f_height >= 0 else int(f_height * 10 - 0.5) / 10.0
                except:
                    height = 0.0
                
                # Build row string: lat\tlon\ts_idx\td_idx\tr_idx\trm_idx\tdia\theight\tid\tdate
                row_str = f"{lat:.6f}\t{lon:.6f}\t{s_idx}\t{d_idx}\t{r_idx}\t{rm_idx}\t{dia}\t{height}\t{row['TreeID']}\t{row['SurveyDate']}"
                rows_data.append(row_str)
            except Exception as e:
                print(f"Skipping row {row.get('TreeID')}: {e}")

    print(f"Generating {output_js}...")
    os.makedirs(os.path.dirname(output_js), exist_ok=True)
    with open(output_js, 'w', encoding='utf-8') as f:
        f.write(f"window.TREE_SPECIES = {json.dumps(species, ensure_ascii=False)};\n")
        f.write(f"window.TREE_DISTS = {json.dumps(dists, ensure_ascii=False)};\n")
        f.write(f"window.TREE_REGIONS = {json.dumps(regions, ensure_ascii=False)};\n")
        f.write(f"window.TREE_REMARKS = {json.dumps(remarks, ensure_ascii=False)};\n")
        
        # Write rows raw data joined by newline
        all_rows = "\\n".join(rows_data)
        f.write(f'window.TREE_ROWS_RAW = "{all_rows}";\n')
        f.write("window.TREE_ROWS = null; // parsed lazily\n")

    print(f"Successfully converted {len(rows_data)} trees.")

if __name__ == "__main__":
    convert()
