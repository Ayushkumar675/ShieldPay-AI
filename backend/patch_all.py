import os, re

p = r'c:\ShieldPay AI\backend\app'

def process_file(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        text = f.read()

    original = text
    
    # Fix Motor db.collection. to db["collection"].
    # Exclude db.close() or get_db() types, match only standard collection names used
    collections = ["users", "policies", "claims", "disruptions", "fraud_alerts", "payouts", "payments", "platform_metrics"]
    for col in collections:
        text = re.sub(rf'\bdb\.{col}\.', f'db["{col}"].', text)
        
    # Standardize Payment to Payout
    text = re.sub(r'\bPayment\b', 'Payout', text)
    # Also standardize db["payments"].insert_one to db["payouts"].insert_one just in case
    text = text.replace('db["payments"]', 'db["payouts"]')
    text = text.replace('db.payments.', 'db["payouts"].')
    
    # Phase 3: Platform metric increments for total_premiums (in policies.py)
    if "policies.py" in fp and "total_premiums" not in text:
        text = text.replace(
            'await db["payouts"].insert_one(payment.model_dump())',
            'await db["payouts"].insert_one(payment.model_dump())\n\n    # Update platform metrics\n    await db["platform_metrics"].update_one({}, {"$inc": {"total_premiums": policy.premium_amount, "reserve_balance": policy.premium_amount}}, upsert=True)'
        )
    
    # Phase 3: Platform metric increments for total_payouts (in claims.py)
    if "claims.py" in fp and "total_payouts" not in text:
        text = text.replace(
            'await db["payouts"].insert_one(payment.model_dump())',
            'await db["payouts"].insert_one(payment.model_dump())\n        await db["platform_metrics"].update_one({}, {"$inc": {"total_payouts": payout, "reserve_balance": -payout}}, upsert=True)'
        )
        text = text.replace(
            'amount=payout_amount,',
            'amount=payout_amount,'
        )
        # Fix the payout variable name for auto_approved
        text = text.replace('total_payouts": payout,', 'total_payouts": payment.amount,')
        text = text.replace('reserve_balance": -payout}', 'reserve_balance": -payment.amount}')

    if original != text:
        print(f"Updated {fp}")
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(text)

for r, d, files in os.walk(p):
    for f in files:
        if f.endswith('.py'):
            process_file(os.path.join(r, f))

print("Patching complete.")
