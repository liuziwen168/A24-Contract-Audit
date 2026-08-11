from __future__ import annotations
import asyncio
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.entities import User

# 临时硬编码一个有效的bcrypt哈希，密码=123456
HASH_PWD = "$2b$12$R9h/cIPz0kmDAtw85UAVKunMjR8bWM1fHnT4gNy4u0XVmkrAfm3N2"

async def create_admin():
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
    async with AsyncSessionLocal() as db:
        res = await db.execute(User.__table__.select().where(User.username == "admin"))
        exist_user = res.scalar_one_or_none()
        if exist_user:
            print("admin已存在")
            return
        new_user = User(
            username="admin",
            password=HASH_PWD,
            full_name="超级管理员",
            role="admin",
            is_active=True
        )
        db.add(new_user)
        await db.commit()
        print("✅admin创建成功，密码123456")

if __name__ == "__main__":
    asyncio.run(create_admin())