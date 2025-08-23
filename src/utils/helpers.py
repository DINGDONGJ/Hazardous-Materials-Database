"""
工具函数模块
包含项目中常用的辅助函数
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from loguru import logger
import re


def ensure_dir(directory: str) -> None:
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")


def load_json(file_path: str) -> Dict[str, Any]:
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件失败: {file_path}, 错误: {e}")
        return {}


def save_json(data: Dict[str, Any], file_path: str) -> bool:
    """保存数据到JSON文件"""
    try:
        ensure_dir(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"保存JSON文件: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败: {file_path}, 错误: {e}")
        return False


def clean_text(text: str) -> str:
    """清理文本，去除多余的空白字符"""
    if not text or text == "-":
        return None
    
    # 去除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    return text if text else None


def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """将长文本分割成较小的块"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # 如果不是最后一块，尝试在句号处分割
        if end < len(text):
            # 寻找最近的句号
            last_period = text.rfind('.', start, end)
            if last_period > start:
                end = last_period + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # 设置下一块的起始位置，考虑重叠
        start = max(start + 1, end - overlap)
    
    return chunks


def validate_un_number(un_number: Any) -> Optional[int]:
    """验证并转换UN编号"""
    if un_number is None or un_number == "-":
        return None
    
    try:
        return int(un_number)
    except (ValueError, TypeError):
        logger.warning(f"无效的UN编号: {un_number}")
        return None


def format_query_result(mysql_result: Dict[str, Any], vector_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """格式化查询结果，用于LLM输入"""
    formatted_result = {
        "structured_data": mysql_result,
        "semantic_context": vector_results,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    return formatted_result


def calculate_similarity_score(query_vector: List[float], doc_vector: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    import numpy as np
    
    query_vec = np.array(query_vector)
    doc_vec = np.array(doc_vector)
    
    # 计算余弦相似度
    dot_product = np.dot(query_vec, doc_vec)
    norm_query = np.linalg.norm(query_vec)
    norm_doc = np.linalg.norm(doc_vec)
    
    if norm_query == 0 or norm_doc == 0:
        return 0.0
    
    return dot_product / (norm_query * norm_doc)
