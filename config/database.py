"""
数据库配置文件
包含MySQL和向量数据库的连接配置
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class DatabaseConfig:
    """数据库配置类"""
    
    # MySQL配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'hazardous_chemicals')
    
    # MySQL连接字符串
    MYSQL_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

    @classmethod
    def get_mysql_url(cls):
        """获取MySQL连接URL"""
        return cls.MYSQL_URL
