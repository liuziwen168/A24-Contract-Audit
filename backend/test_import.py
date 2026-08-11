from dotenv import load_dotenv
load_dotenv()
from app.core.config import settings
print("数据库连接字符串：", settings.database_url)