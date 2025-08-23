"""
系统设置配置文件
包含应用程序的各种设置参数
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """系统设置类"""
    
    # 应用程序设置
    APP_NAME = "危险化学品混合数据库系统"
    VERSION = "1.0.0"
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # 日志设置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/app.log')
    
    # 查询设置
    DEFAULT_SEARCH_LIMIT = int(os.getenv('DEFAULT_SEARCH_LIMIT', 10))

    # 向量数据库配置
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', './data/vector_db')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')
    VECTOR_COLLECTION_NAME = os.getenv('VECTOR_COLLECTION_NAME', 'hazardous_chemicals')

    # 文本处理配置
    MAX_CHUNK_SIZE = int(os.getenv('MAX_CHUNK_SIZE', 500))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 50))

    # 检索配置
    RETRIEVAL_TOP_K = int(os.getenv('RETRIEVAL_TOP_K', 50))  # 增加默认返回数量
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.1))
    
    # 数据处理设置
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 100))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    
    @classmethod
    def get_log_config(cls):
        """获取日志配置"""
        return {
            'level': cls.LOG_LEVEL,
            'file': cls.LOG_FILE,
            'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}'
        }

    @classmethod
    def get_vector_db_config(cls):
        """获取向量数据库配置"""
        return {
            'path': cls.VECTOR_DB_PATH,
            'embedding_model': cls.EMBEDDING_MODEL,
            'collection_name': cls.VECTOR_COLLECTION_NAME,
            'max_chunk_size': cls.MAX_CHUNK_SIZE,
            'chunk_overlap': cls.CHUNK_OVERLAP,
            'retrieval_top_k': cls.RETRIEVAL_TOP_K,
            'similarity_threshold': cls.SIMILARITY_THRESHOLD
        }
