"""
FAISS向量数据库处理模块
负责向量数据库的创建、数据导入和查询功能
"""

import os
import json
import pickle
import uuid
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
import jieba
from loguru import logger
from tqdm import tqdm

from config.settings import Settings
from src.data_processing.text_processor import TextProcessor


class SimpleTfidfVectorizer:
    """简化的TF-IDF向量化器"""

    def __init__(self, max_features=5000):
        # 配置jieba
        jieba.setLogLevel(jieba.logging.INFO)

        # 创建TF-IDF向量化器
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            tokenizer=self._chinese_tokenizer,
            lowercase=False,
            stop_words=None
        )
        self.is_fitted = False

    def _chinese_tokenizer(self, text):
        """中文分词器"""
        # 使用jieba进行中文分词
        words = list(jieba.cut(text))
        # 过滤短词和停用词
        filtered_words = [word.strip() for word in words
                         if len(word.strip()) > 1 and word.strip() not in ['的', '是', '在', '有', '和', '或', '等', '及']]
        return filtered_words

    def fit_transform(self, documents):
        """训练并转换文档"""
        logger.info(f"正在训练TF-IDF模型，文档数量: {len(documents)}")
        vectors = self.vectorizer.fit_transform(documents)
        self.is_fitted = True
        logger.info(f"TF-IDF训练完成，特征维度: {vectors.shape[1]}")
        return vectors.toarray().astype('float32')

    def transform(self, documents):
        """转换文档"""
        if not self.is_fitted:
            raise ValueError("向量化器尚未训练")
        vectors = self.vectorizer.transform(documents)
        return vectors.toarray().astype('float32')


class VectorHandler:
    """FAISS向量数据库处理器"""

    def __init__(self):
        self.config = Settings.get_vector_db_config()
        self.text_processor = TextProcessor()

        # 确保向量数据库目录存在
        os.makedirs(self.config['path'], exist_ok=True)

        # 文件路径
        self.index_path = os.path.join(self.config['path'], 'faiss_index.index')
        self.metadata_path = os.path.join(self.config['path'], 'metadata.json')
        self.documents_path = os.path.join(self.config['path'], 'documents.pkl')
        self.vectorizer_path = os.path.join(self.config['path'], 'vectorizer.pkl')

        # 初始化向量化器
        self.vectorizer = SimpleTfidfVectorizer()

        # 初始化FAISS索引
        self.index = None
        self.documents = []
        self.metadata = []
        self._load_or_create_index()
        
    def _load_or_create_index(self):
        """加载或创建FAISS索引"""
        try:
            if (os.path.exists(self.index_path) and
                os.path.exists(self.metadata_path) and
                os.path.exists(self.documents_path) and
                os.path.exists(self.vectorizer_path)):

                # 加载现有索引
                self.index = faiss.read_index(self.index_path)

                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)

                with open(self.documents_path, 'rb') as f:
                    self.documents = pickle.load(f)

                with open(self.vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)

                logger.info(f"加载现有索引，包含 {len(self.metadata)} 个文档")
            else:
                # 创建新索引（将在第一次添加数据时初始化）
                self.index = None
                self.metadata = []
                self.documents = []

                logger.info("准备创建新的FAISS索引")

        except Exception as e:
            logger.error(f"初始化FAISS索引失败: {e}")
            raise
    
    def import_mysql_data(self, mysql_handler) -> bool:
        """从MySQL导入化学品数据"""
        try:
            logger.info("开始从MySQL导入化学品数据...")

            # 获取所有化学品数据
            chemicals = mysql_handler.get_all_chemicals()
            if not chemicals:
                logger.warning("没有找到化学品数据")
                return False

            logger.info(f"找到 {len(chemicals)} 条化学品记录")

            # 准备批量数据
            documents = []
            metadatas = []

            for chemical in tqdm(chemicals, desc="处理化学品数据"):
                # 创建文档文本
                doc_text = self.text_processor.create_chemical_document(chemical)
                if not doc_text:
                    continue

                documents.append(doc_text)

                # 创建元数据
                metadata = {
                    'source': 'mysql',
                    'doc_type': 'chemical',
                    'un_number': str(chemical.get('un_number', '')),
                    'chinese_name': chemical.get('chinese_name', ''),
                    'category': chemical.get('category', ''),
                    'packaging_group': chemical.get('packaging_group', ''),
                    'id': f"chemical_{chemical.get('un_number', uuid.uuid4().hex)}"
                }
                metadatas.append(metadata)

            # 批量向量化和添加
            if documents:
                self._add_documents_batch(documents, metadatas)

            logger.info(f"MySQL数据导入完成，共导入 {len(documents)} 条记录")
            return True

        except Exception as e:
            logger.error(f"导入MySQL数据失败: {e}")
            return False

    def _add_documents_batch(self, documents: List[str], metadatas: List[Dict]):
        """批量添加文档到向量数据库"""
        try:
            # 如果是第一次添加文档，需要训练向量化器并创建索引
            if self.index is None:
                logger.info("首次添加文档，训练向量化器...")
                vectors = self.vectorizer.fit_transform(documents)

                # 创建FAISS索引
                dimension = vectors.shape[1]
                self.index = faiss.IndexFlatIP(dimension)
                logger.info(f"创建FAISS索引，维度: {dimension}")
            else:
                # 使用已训练的向量化器
                logger.info("向量化文档...")
                vectors = self.vectorizer.transform(documents)

            # 标准化向量（用于余弦相似度）
            faiss.normalize_L2(vectors)

            # 添加到索引
            self.index.add(vectors)

            # 保存文档和元数据
            self.documents.extend(documents)
            self.metadata.extend(metadatas)

            # 保存到磁盘
            self._save_index()

            logger.info(f"成功添加 {len(documents)} 个文档到向量数据库")

        except Exception as e:
            logger.error(f"批量添加文档失败: {e}")
            raise

    def _save_index(self):
        """保存索引到磁盘"""
        try:
            # 保存FAISS索引
            faiss.write_index(self.index, self.index_path)

            # 保存元数据
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)

            # 保存文档
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.documents, f)

            # 保存向量化器
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)

        except Exception as e:
            logger.error(f"保存索引失败: {e}")
            raise
    
    def import_markdown_data(self, markdown_file_path: str) -> bool:
        """导入Markdown文档数据"""
        try:
            logger.info(f"开始导入Markdown文档: {markdown_file_path}")

            # 读取Markdown文件
            with open(markdown_file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # 处理Markdown内容
            documents_data = self.text_processor.process_markdown_content(markdown_content)

            if not documents_data:
                logger.warning("没有从Markdown文件中提取到有效内容")
                return False

            logger.info(f"从Markdown文件提取到 {len(documents_data)} 个文档块")

            # 准备批量数据
            documents = []
            metadatas = []

            for doc_data in documents_data:
                documents.append(doc_data['content'])

                # 添加ID到元数据
                metadata = doc_data['metadata'].copy()
                metadata['id'] = f"appendix_{metadata['section_id']}_{metadata['chunk_id']}"
                metadatas.append(metadata)

            # 批量添加到向量数据库
            if documents:
                self._add_documents_batch(documents, metadatas)

            logger.info(f"Markdown数据导入完成，共导入 {len(documents)} 个文档块")
            return True

        except Exception as e:
            logger.error(f"导入Markdown数据失败: {e}")
            return False
    
    def semantic_search(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """语义搜索"""
        try:
            if top_k is None:
                top_k = self.config['retrieval_top_k']

            if self.index is None or self.index.ntotal == 0:
                logger.warning("向量数据库为空，无法进行搜索")
                return []

            if not self.vectorizer.is_fitted:
                logger.warning("向量化器未训练，无法进行搜索")
                return []

            # 向量化查询
            query_vector = self.vectorizer.transform([query])
            faiss.normalize_L2(query_vector)

            # 搜索
            scores, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))

            # 格式化结果
            formatted_results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx >= 0 and idx < len(self.documents) and score > 0.1:  # 有效索引和最低分数阈值
                    result = {
                        'content': self.documents[idx],
                        'metadata': self.metadata[idx],
                        'score': float(score),  # FAISS返回的是相似度分数
                        'distance': 1.0 - float(score),  # 转换为距离
                        'id': self.metadata[idx].get('id', f'doc_{idx}')
                    }

                    # 只返回相似度超过阈值的结果
                    if score >= 0.1:  # 使用较低的阈值以确保能找到相关法规
                        formatted_results.append(result)

            logger.info(f"语义搜索完成，查询: '{query}'，返回 {len(formatted_results)} 个结果")
            return formatted_results

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            total_docs = len(self.documents)

            # 统计不同类型的文档
            doc_types = {}
            sources = {}

            for metadata in self.metadata:
                doc_type = metadata.get('doc_type', 'unknown')
                source = metadata.get('source', 'unknown')

                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                sources[source] = sources.get(source, 0) + 1

            return {
                'total_documents': total_docs,
                'collection_name': self.config['collection_name'],
                'embedding_model': self.config['embedding_model'],
                'doc_types': doc_types,
                'sources': sources,
                'index_size': self.index.ntotal if self.index else 0
            }

        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            return {}

    def reset_collection(self) -> bool:
        """重置集合（清空所有数据）"""
        try:
            logger.warning("正在重置向量数据库...")

            # 删除现有文件
            for file_path in [self.index_path, self.metadata_path, self.documents_path]:
                if os.path.exists(file_path):
                    os.remove(file_path)

            # 重新初始化
            self._load_or_create_index()

            logger.info("向量数据库重置完成")
            return True
        except Exception as e:
            logger.error(f"重置向量数据库失败: {e}")
            return False
