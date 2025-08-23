"""
文本预处理模块
负责将结构化数据和文档转换为适合向量化的文本格式
"""

import re
import jieba
import markdown
from typing import List, Dict, Any, Tuple
from loguru import logger
from config.settings import Settings


class TextProcessor:
    """文本预处理器"""
    
    def __init__(self):
        self.max_chunk_size = Settings.MAX_CHUNK_SIZE
        self.chunk_overlap = Settings.CHUNK_OVERLAP
        
    def create_chemical_document(self, chemical_record: Dict[str, Any]) -> str:
        """将化学品记录转换为文档文本"""
        try:
            text_parts = []
            
            # 基本信息
            if chemical_record.get('un_number'):
                text_parts.append(f"联合国编号：UN{chemical_record['un_number']}")
            
            if chemical_record.get('chinese_name'):
                text_parts.append(f"中文名称：{chemical_record['chinese_name']}")
            
            if chemical_record.get('english_name'):
                text_parts.append(f"英文名称：{chemical_record['english_name']}")
            
            # 危险性信息
            if chemical_record.get('category'):
                text_parts.append(f"危险类别：{chemical_record['category']}")
            
            if chemical_record.get('secondary_hazard'):
                text_parts.append(f"次要危险性：{chemical_record['secondary_hazard']}")
            
            if chemical_record.get('packaging_group'):
                text_parts.append(f"包装类别：{chemical_record['packaging_group']}")
            
            # 运输信息
            if chemical_record.get('special_provisions'):
                text_parts.append(f"特殊规定：{chemical_record['special_provisions']}")
            
            if chemical_record.get('limited_quantity'):
                text_parts.append(f"有限数量：{chemical_record['limited_quantity']}")
            
            if chemical_record.get('excepted_quantity'):
                text_parts.append(f"例外数量：{chemical_record['excepted_quantity']}")
            
            # 包装信息
            if chemical_record.get('packaging_instruction'):
                text_parts.append(f"包装指南：{chemical_record['packaging_instruction']}")
            
            if chemical_record.get('packaging_special_provision'):
                text_parts.append(f"包装特殊规定：{chemical_record['packaging_special_provision']}")
            
            # 罐柜信息
            if chemical_record.get('portable_tank_instruction'):
                text_parts.append(f"罐柜指南：{chemical_record['portable_tank_instruction']}")
            
            if chemical_record.get('portable_tank_special_provision'):
                text_parts.append(f"罐柜特殊规定：{chemical_record['portable_tank_special_provision']}")
            
            # 过滤空值并连接
            filtered_parts = [part for part in text_parts if part and not part.endswith('：')]
            document_text = " | ".join(filtered_parts)
            
            return document_text
            
        except Exception as e:
            logger.error(f"创建化学品文档失败: {e}")
            return ""
    
    def process_markdown_content(self, markdown_content: str) -> List[Dict[str, Any]]:
        """处理Markdown内容，分块并提取元数据"""
        try:
            # 转换Markdown为纯文本
            html = markdown.markdown(markdown_content)
            # 简单的HTML标签清理
            text = re.sub(r'<[^>]+>', '', html)
            
            # 按章节分割
            sections = self._split_by_sections(text)
            
            documents = []
            for i, section in enumerate(sections):
                if section.strip():
                    # 进一步分块
                    chunks = self._split_text_into_chunks(section)
                    
                    for j, chunk in enumerate(chunks):
                        if len(chunk.strip()) > 50:  # 过滤太短的块
                            documents.append({
                                'content': chunk.strip(),
                                'metadata': {
                                    'source': 'appendix_a',
                                    'section_id': i,
                                    'chunk_id': j,
                                    'doc_type': 'regulation'
                                }
                            })
            
            logger.info(f"处理Markdown内容完成，生成 {len(documents)} 个文档块")
            return documents
            
        except Exception as e:
            logger.error(f"处理Markdown内容失败: {e}")
            return []
    
    def _split_by_sections(self, text: str) -> List[str]:
        """按章节分割文本"""
        # 按照数字编号分割（如 "16 新的或现有的爆炸性物质"）
        sections = re.split(r'\n(?=\d+\s+)', text)
        
        # 也按照标题分割（如 "# 附录A"）
        all_sections = []
        for section in sections:
            subsections = re.split(r'\n(?=#\s+)', section)
            all_sections.extend(subsections)
        
        return [s.strip() for s in all_sections if s.strip()]
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """将文本分割成适当大小的块"""
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        sentences = re.split(r'[。！？；\n]', text)
        
        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果添加这个句子会超过最大长度
            if len(current_chunk) + len(sentence) > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # 保留重叠部分
                    if self.chunk_overlap > 0:
                        overlap_text = current_chunk[-self.chunk_overlap:]
                        current_chunk = overlap_text + sentence
                    else:
                        current_chunk = sentence
                else:
                    # 单个句子就超过最大长度，直接添加
                    chunks.append(sentence)
                    current_chunk = ""
            else:
                current_chunk += sentence + "。"
        
        # 添加最后一个块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符（保留中文、英文、数字和基本标点）
        text = re.sub(r'[^\u4e00-\u9fff\w\s\.\,\;\:\!\?\-\(\)\[\]\/\%\$]', '', text)
        
        return text.strip()
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        try:
            # 使用jieba分词
            words = jieba.cut(text)
            
            # 过滤停用词和短词
            keywords = []
            for word in words:
                word = word.strip()
                if len(word) > 1 and word not in ['的', '是', '在', '有', '和', '或', '等', '及']:
                    keywords.append(word)
            
            return keywords[:10]  # 返回前10个关键词
            
        except Exception as e:
            logger.error(f"提取关键词失败: {e}")
            return []
