import os

p = r'c:\ShieldPay AI\backend\app'
for r, d, files in os.walk(p):
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(r, f)
            with open(fp, 'r', encoding='utf-8') as file:
                text = file.read()
            
            # The previous script replaced db.users. with db[\'users\'].
            # This is literally written as "db[\\'users\\']." in the file.
            text = text.replace(r"db[\'", "db['")
            text = text.replace(r"\'].", "'].")
            
            with open(fp, 'w', encoding='utf-8') as file:
                file.write(text)
print("Sanitized brackets.")
