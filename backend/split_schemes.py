import os
import re

data_dir = os.path.join(os.path.dirname(__file__), "data")

def split_all():
    for filename in os.listdir(data_dir):
        if not filename.endswith(".txt"):
            continue
            
        filepath = os.path.join(data_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(filepath, "r", encoding="latin-1") as f:
                content = f.read()
            
        # Split by "# Scheme Name:" case-insensitive
        schemes = re.split(r'(?i)(?=# SCHEME NAME:)', content)
        
        count = 0
        for scheme_text in schemes:
            scheme_text = scheme_text.strip()
            if not scheme_text or not scheme_text.lower().startswith('# scheme name:'):
                continue
                
            match = re.search(r'(?i)# SCHEME NAME:\s*(.+)', scheme_text)
            if match:
                name = match.group(1).strip()
                # Sanitize filename (e.g., "PM-JAY" -> "pm_jay")
                safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name).strip('_')
                safe_name = re.sub(r'_+', '_', safe_name).lower()
                
                new_filepath = os.path.join(data_dir, f"{safe_name}.txt")
                with open(new_filepath, "w", encoding="utf-8") as new_f:
                    new_f.write(scheme_text)
                count += 1
                
        if count > 0:
            os.remove(filepath)
            print(f"Split {filename} into {count} individual files and removed the original.")

if __name__ == "__main__":
    split_all()
