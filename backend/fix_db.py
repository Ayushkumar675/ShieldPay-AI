import os, re
p = r'c:\ShieldPay AI\backend\app'
for r, d, files in os.walk(p):
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(r, f)
            with open(fp, 'r', encoding='utf-8') as file:
                text = file.read()
            # replace db.something. with db["something"].
            text = re.sub(r'db\.([a-zA-Z_]+)\.', r'db["\1"].', text)
            with open(fp, 'w', encoding='utf-8') as file:
                file.write(text)
print("Done fixing motor references!")
