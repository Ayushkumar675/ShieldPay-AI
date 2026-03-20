import asyncio
import sys
from app.models.database import connect_db, close_db, get_db

async def check_user(email):
    print("Connecting to DB...")
    await connect_db()
    db = get_db()
    print(f"Checking for user: {email}")
    user = await db["users"].find_one({"email": email})
    if user:
        print(f"User found: {user['email']}, Role: {user.get('role', 'unknown')}")
    else:
        print("User not found.")
    await close_db()
    
if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_user("coolayush4015@gmail.com"))