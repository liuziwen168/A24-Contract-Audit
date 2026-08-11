from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine
from app.core.config import settings
from app.models.entities import Base

engine = create_engine(settings.database_url)
# 自动根据ORM模型生成所有数据表
Base.metadata.create_all(bind=engine)
print("✅ 数据表创建完成！")