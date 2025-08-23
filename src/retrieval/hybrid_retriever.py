"""
混合检索系统
结合结构化查询和语义搜索，提供多种检索策略
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from src.database.mysql_handler import MySQLHandler
from src.vector_db.chroma_handler import VectorHandler
from config.settings import Settings


class HybridRetriever:
    """混合检索器"""

    def __init__(self):
        self.mysql_handler = MySQLHandler()
        self.vector_handler = VectorHandler()
        self.config = Settings.get_vector_db_config()
        
    def retrieve(self, query: str, strategy: str = "auto", top_k: int = 5, verbose: bool = False) -> Dict[str, Any]:
        """
        主检索接口

        Args:
            query: 查询文本
            strategy: 检索策略 ("exact", "semantic", "hybrid", "auto")
            top_k: 返回结果数量
            verbose: 是否显示详细查询流程

        Returns:
            包含化学品数据和相关法规的结构化结果
        """
        try:
            if verbose:
                print(f"\n🔍 查询流程:")
                print(f"1. 用户输入：如\"{query}\"的危险性及解释。")

            logger.info(f"开始检索，查询: '{query}'，策略: {strategy}")

            # 获取基础搜索结果
            if strategy == "exact":
                basic_results = self._exact_search(query, top_k, verbose)
            elif strategy == "semantic":
                basic_results = self._semantic_search(query, top_k, verbose)
            elif strategy == "hybrid":
                basic_results = self._hybrid_search(query, top_k, verbose)
            else:  # auto
                basic_results = self._auto_search(query, top_k, verbose)

            # 构建结构化结果
            structured_result = self._build_structured_result(basic_results, query, verbose)

            # 如果没有找到结果，尝试备用搜索
            if not structured_result.get('chemical_data') and not structured_result.get('regulations'):
                if verbose:
                    print(f"6. 备用搜索：未找到直接结果，尝试提取化学品名称进行搜索")
                fallback_result = self._fallback_search(query, top_k, verbose)
                if fallback_result.get('chemical_data') or fallback_result.get('regulations'):
                    return fallback_result

            return structured_result

        except Exception as e:
            logger.error(f"检索失败: {e}")
            return {"chemical_data": [], "regulations": [], "query": query}
    
    def _auto_search(self, query: str, top_k: int, verbose: bool = False) -> List[Dict[str, Any]]:
        """自动选择检索策略"""
        try:
            # 检测查询类型
            query_type = self._detect_query_type(query)

            if query_type == "un_number":
                # UN编号查询，使用精确搜索
                if verbose:
                    print(f"2. 查询类型检测：识别为UN编号查询")
                return self._exact_search(query, top_k, verbose)
            elif query_type == "name_search":
                # 名称搜索，使用混合搜索
                if verbose:
                    print(f"2. 查询类型检测：识别为化学品名称查询")
                return self._hybrid_search(query, top_k, verbose)
            else:
                # 自然语言查询，优先使用语义搜索
                if verbose:
                    print(f"2. 查询类型检测：识别为自然语言查询")
                semantic_results = self._semantic_search(query, top_k, verbose)

                # 如果语义搜索结果不够，补充精确搜索
                if len(semantic_results) < top_k:
                    if verbose:
                        print(f"5. 结果补充：语义搜索结果不足，补充精确搜索")
                    exact_results = self._exact_search(query, top_k - len(semantic_results), False)
                    # 合并结果，去重
                    combined_results = self._merge_results(semantic_results, exact_results)
                    return combined_results[:top_k]

                return semantic_results

        except Exception as e:
            logger.error(f"自动搜索失败: {e}")
            return []
    
    def _detect_query_type(self, query: str) -> str:
        """检测查询类型"""
        # UN编号模式
        if re.search(r'\bUN\s*\d+\b|\b\d{4}\b', query, re.IGNORECASE):
            return "un_number"
        
        # 化学品名称搜索模式
        chemical_keywords = ['化学品', '物质', '液体', '固体', '气体', '电池', '酸', '碱', '醇', '醚']
        if any(keyword in query for keyword in chemical_keywords):
            return "name_search"
        
        # 默认为自然语言查询
        return "natural_language"

    def _expand_search_terms(self, query: str) -> List[str]:
        """扩展搜索词，处理同义词和相关词汇"""
        expanded_terms = []

        # 电池相关的扩展
        if "锂电池" in query:
            expanded_terms.extend(["锂离子电池", "锂金属电池", "锂合金电池"])
        elif "电池" in query and "锂" in query:
            expanded_terms.extend(["锂离子电池", "锂金属电池"])
        elif "电池" in query:
            expanded_terms.extend(["锂离子电池", "锂金属电池", "电池"])

        # 化学品类别相关的扩展
        if "易燃" in query:
            expanded_terms.extend(["易燃液体", "易燃固体", "易燃气体"])
        elif "腐蚀" in query:
            expanded_terms.extend(["腐蚀性物质", "腐蚀性液体"])
        elif "有毒" in query:
            expanded_terms.extend(["有毒物质", "毒性物质"])

        # 去重并返回
        return list(set(expanded_terms))
    
    def _exact_search(self, query: str, top_k: int, verbose: bool = False) -> List[Dict[str, Any]]:
        """精确搜索（基于MySQL）"""
        try:
            results = []

            # 提取UN编号
            un_numbers = re.findall(r'\bUN\s*(\d+)\b|\b(\d{4})\b', query, re.IGNORECASE)

            if un_numbers:
                total_found = 0
                for match in un_numbers:
                    un_num = int(match[0] or match[1])
                    chemicals = self.mysql_handler.query_by_un_number(un_num)
                    total_found += len(chemicals)

                if verbose:
                    un_num = int(un_numbers[0][0] or un_numbers[0][1])
                    print(f"3. MySQL查询：执行 SELECT * FROM hazardous_chemicals_catalog WHERE un_number = {un_num}，返回 {total_found} 条结构化数据。")

                for match in un_numbers:
                    un_num = int(match[0] or match[1])
                    chemicals = self.mysql_handler.query_by_un_number(un_num)
                    for chemical in chemicals:
                        results.append({
                            'content': self._format_chemical_content(chemical),
                            'metadata': {
                                'source': 'mysql',
                                'doc_type': 'chemical',
                                'un_number': str(chemical['un_number']),
                                'search_type': 'exact_un'
                            },
                            'score': 1.0,
                            'chemical_data': chemical
                        })

            # 如果没有找到UN编号，尝试名称搜索
            if not results:
                if verbose:
                    print(f"3. MySQL查询：执行 SELECT * FROM hazardous_chemicals_catalog WHERE chinese_name LIKE '%{query}%'，返回结构化数据。")

                # 首先尝试直接搜索
                chemicals = self.mysql_handler.search_by_name(query, limit=top_k)

                # 如果没有结果，尝试扩展关键词搜索
                if not chemicals:
                    expanded_queries = self._expand_search_terms(query)
                    for expanded_query in expanded_queries:
                        chemicals.extend(self.mysql_handler.search_by_name(expanded_query, limit=top_k))
                        if len(chemicals) >= top_k:
                            break

                for chemical in chemicals[:top_k]:
                    results.append({
                        'content': self._format_chemical_content(chemical),
                        'metadata': {
                            'source': 'mysql',
                            'doc_type': 'chemical',
                            'un_number': str(chemical['un_number']),
                            'search_type': 'exact_name'
                        },
                        'score': 0.9,
                        'chemical_data': chemical
                    })

            logger.info(f"精确搜索完成，返回 {len(results)} 个结果")
            return results[:top_k]

        except Exception as e:
            logger.error(f"精确搜索失败: {e}")
            return []
    
    def _semantic_search(self, query: str, top_k: int, verbose: bool = False) -> List[Dict[str, Any]]:
        """语义搜索（基于向量数据库）"""
        try:
            if verbose:
                print(f"3. 向量数据库查询：将输入文本嵌入向量，执行k-NN搜索（k=3-5），返回语义相关性最高的前A段落。")

            vector_results = self.vector_handler.semantic_search(query, top_k)

            results = []
            for result in vector_results:
                # 计算相似度分数（距离越小，相似度越高）
                distance = result.get('distance', 1.0)
                similarity_score = max(0, 1 - distance)

                # 只返回相似度超过阈值的结果
                if similarity_score >= self.config.get('similarity_threshold', 0.1):
                    results.append({
                        'content': result['content'],
                        'metadata': result['metadata'],
                        'score': similarity_score,
                        'search_type': 'semantic'
                    })

            if verbose and results:
                print(f"4. 结果整合：合并MySQL结果和向量搜索结果，格式化为LLM输入（如JSON）。")
                print(f"5. LLM处理：通过RAG框架（如LangChain）生成最终响应。")

            logger.info(f"语义搜索完成，返回 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []
    
    def _hybrid_search(self, query: str, top_k: int, verbose: bool = False) -> List[Dict[str, Any]]:
        """混合搜索（结合精确搜索和语义搜索）"""
        try:
            if verbose:
                print(f"3. 混合搜索策略：同时执行MySQL精确查询和向量语义搜索")

            # 分别进行精确搜索和语义搜索
            exact_results = self._exact_search(query, top_k // 2 + 1, False)
            semantic_results = self._semantic_search(query, top_k // 2 + 1, False)

            # 合并和排序结果
            combined_results = self._merge_results(exact_results, semantic_results)

            if verbose and combined_results:
                print(f"4. 结果整合：合并MySQL结果和向量搜索结果，格式化为LLM输入（如JSON）。")
                print(f"5. LLM处理：通过RAG框架（如LangChain）生成最终响应。")

            logger.info(f"混合搜索完成，返回 {len(combined_results[:top_k])} 个结果")
            return combined_results[:top_k]

        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return []
    
    def _merge_results(self, results1: List[Dict], results2: List[Dict]) -> List[Dict]:
        """合并搜索结果，去重并按分数排序"""
        try:
            # 使用字典去重（基于内容或UN编号）
            merged = {}
            
            for result in results1 + results2:
                # 生成唯一键
                if result.get('chemical_data'):
                    chemical = result['chemical_data']
                    # 使用UN编号+包装类别作为唯一键，确保不同包装类别的记录不会被去重
                    packaging_group = chemical.get('packaging_group', 'None')
                    key = f"un_{chemical['un_number']}_pkg_{packaging_group}"
                else:
                    key = result.get('metadata', {}).get('id', str(hash(result['content'])))
                
                # 保留分数更高的结果
                if key not in merged or result.get('score', 0) > merged[key].get('score', 0):
                    merged[key] = result
            
            # 按分数排序
            sorted_results = sorted(merged.values(), key=lambda x: x.get('score', 0), reverse=True)
            
            return sorted_results
            
        except Exception as e:
            logger.error(f"合并结果失败: {e}")
            return results1 + results2
    
    def _format_chemical_content(self, chemical: Dict[str, Any]) -> str:
        """格式化化学品内容为可读文本，显示所有指定列，缺失数据显示null"""
        try:
            # 定义要显示的字段及其对应的数据库字段名
            field_mappings = [
                ("联合国编号", "un_number"),
                ("名称和说明", "chinese_name"),
                ("英文名称和说明", "english_name"),
                ("类别或项别", "category"),
                ("次要危险性", "secondary_hazard"),
                ("包装类别", "packaging_group"),
                ("特殊规定", "special_provisions"),
                ("有限数量", "limited_quantity"),
                ("例外数量", "excepted_quantity"),
                ("包装和中型散装容器包装指南", "packaging_instruction"),
                ("包装和中型散装容器特殊包装规定", "packaging_special_provision"),
                ("可移动罐柜和散装容器指南", "portable_tank_instruction"),
                ("可移动罐柜和散装容器特殊规定", "portable_tank_special_provision")
            ]

            parts = []
            for display_name, field_name in field_mappings:
                value = chemical.get(field_name)
                if value is None or value == '' or str(value).strip() == '':
                    value = 'null'
                parts.append(f"{display_name}: {value}")

            return "\n".join(parts)

        except Exception as e:
            logger.error(f"格式化化学品内容失败: {e}")
            return str(chemical)
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """获取检索系统统计信息"""
        try:
            mysql_stats = self.mysql_handler.get_statistics()
            vector_stats = self.vector_handler.get_collection_stats()
            
            return {
                'mysql_stats': mysql_stats,
                'vector_stats': vector_stats,
                'config': self.config
            }

        except Exception as e:
            logger.error(f"获取检索统计信息失败: {e}")
            return {}

    def _build_structured_result(self, basic_results: List[Dict], query: str, verbose: bool = False) -> Dict[str, Any]:
        """构建结构化的查询结果"""
        try:
            # 分离化学品数据和法规数据
            chemical_data = []
            regulations = []

            for result in basic_results:
                if result.get('metadata', {}).get('doc_type') == 'chemical':
                    chemical_data.append(result)
                elif result.get('metadata', {}).get('doc_type') == 'regulation':
                    regulations.append(result)

            # 如果有化学品数据，查找相关法规
            if chemical_data and verbose:
                print(f"6. 法规关联：根据化学品信息查找相关的附录A规定")

            # 为化学品查找相关法规
            related_regulations = self._find_related_regulations(chemical_data, query)

            # 合并法规（去重）
            all_regulations = self._merge_regulations(regulations, related_regulations)

            return {
                'query': query,
                'chemical_data': chemical_data,
                'regulations': all_regulations,
                'total_chemicals': len(chemical_data),
                'total_regulations': len(all_regulations)
            }

        except Exception as e:
            logger.error(f"构建结构化结果失败: {e}")
            return {"chemical_data": [], "regulations": [], "query": query}

    def _find_related_regulations(self, chemical_data: List[Dict], query: str) -> List[Dict]:
        """为化学品数据查找相关法规"""
        try:
            related_regulations = []
            found_specific = False

            for chemical in chemical_data:
                chemical_info = chemical.get('chemical_data', {})

                # 优先搜索特殊规定编号（最精确的匹配）
                if chemical_info.get('special_provisions'):
                    provisions = str(chemical_info['special_provisions']).split()
                    for provision in provisions:
                        if provision.isdigit():
                            # 搜索特殊规定编号
                            regulations = self.vector_handler.semantic_search(provision, top_k=5)
                            for reg in regulations:
                                if (reg.get('metadata', {}).get('source') == 'appendix_a' and
                                    reg not in related_regulations):
                                    related_regulations.append(reg)
                                    found_specific = True

                # 如果通过特殊规定找到了法规，就不再进行通用搜索
                if found_specific:
                    continue

                # 搜索UN编号相关法规
                if chemical_info.get('un_number'):
                    un_number = str(chemical_info['un_number'])
                    regulations = self.vector_handler.semantic_search(un_number, top_k=3)
                    for reg in regulations:
                        if (reg.get('metadata', {}).get('source') == 'appendix_a' and
                            reg not in related_regulations):
                            related_regulations.append(reg)
                            found_specific = True

                # 搜索化学品名称关键词
                if not found_specific and chemical_info.get('chinese_name'):
                    name = chemical_info['chinese_name']
                    specific_terms = []

                    # 提取具体的化学品类型关键词
                    if '电池' in name:
                        specific_terms.extend(['电池', '锂电池', '锂离子'])
                    if '黏合剂' in name or '胶' in name:
                        specific_terms.extend(['黏合剂', '胶水', '胶'])
                    if '汽油' in name:
                        specific_terms.extend(['汽油', '燃料'])
                    if '乙醇' in name:
                        specific_terms.extend(['乙醇', '酒精'])

                    # 搜索具体关键词
                    for term in specific_terms[:3]:
                        regulations = self.vector_handler.semantic_search(term, top_k=3)
                        for reg in regulations:
                            if (reg.get('metadata', {}).get('source') == 'appendix_a' and
                                reg not in related_regulations):
                                related_regulations.append(reg)
                                found_specific = True

            # 只有在完全没有找到特定法规时，才使用通用搜索
            if not found_specific:
                # 根据危险类别搜索
                categories = set()
                for chemical in chemical_data:
                    chemical_info = chemical.get('chemical_data', {})
                    if chemical_info.get('category'):
                        categories.add(chemical_info['category'])

                for category in list(categories)[:2]:  # 最多搜索2个类别
                    category_terms = [f"第{category}类", f"类别{category}"]
                    for term in category_terms:
                        regulations = self.vector_handler.semantic_search(term, top_k=2)
                        for reg in regulations:
                            if (reg.get('metadata', {}).get('source') == 'appendix_a' and
                                reg not in related_regulations):
                                related_regulations.append(reg)

            # 按相似度排序并限制数量
            related_regulations.sort(key=lambda x: x.get('score', 0), reverse=True)
            return related_regulations[:3]  # 最多返回3个相关法规

        except Exception as e:
            logger.error(f"查找相关法规失败: {e}")
            return []

    def _merge_regulations(self, regulations1: List[Dict], regulations2: List[Dict]) -> List[Dict]:
        """合并法规列表，去重"""
        try:
            merged = {}

            for reg_list in [regulations1, regulations2]:
                for reg in reg_list:
                    reg_id = reg.get('metadata', {}).get('id', str(hash(reg['content'])))
                    if reg_id not in merged:
                        merged[reg_id] = reg

            # 按相似度分数排序
            sorted_regs = sorted(merged.values(), key=lambda x: x.get('score', 0), reverse=True)
            return sorted_regs

        except Exception as e:
            logger.error(f"合并法规失败: {e}")
            return regulations1 + regulations2

    def _fallback_search(self, query: str, top_k: int = 5, verbose: bool = False) -> Dict[str, Any]:
        """
        备用搜索：当主搜索没有结果时，尝试提取化学品名称进行搜索

        Args:
            query: 原始查询
            top_k: 返回结果数量
            verbose: 是否显示详细日志

        Returns:
            包含化学品数据和法规的字典
        """
        try:
            # 提取可能的化学品名称
            chemical_names = self._extract_chemical_names(query)

            if not chemical_names:
                return {"chemical_data": [], "regulations": [], "query": query}

            if verbose:
                print(f"   提取到的化学品名称: {chemical_names}")

            # 对每个提取的化学品名称进行搜索
            all_results = []
            for name in chemical_names:
                # 使用混合搜索策略
                results = self._hybrid_search(name, top_k, False)
                if results:
                    all_results.extend(results)

            if not all_results:
                return {"chemical_data": [], "regulations": [], "query": query}

            # 构建结构化结果
            structured_result = self._build_structured_result(all_results, query, verbose)

            if verbose and (structured_result.get('chemical_data') or structured_result.get('regulations')):
                print(f"   备用搜索成功，找到 {len(structured_result.get('chemical_data', []))} 条化学品数据")

            return structured_result

        except Exception as e:
            logger.error(f"备用搜索失败: {e}")
            return {"chemical_data": [], "regulations": [], "query": query}

    def _extract_chemical_names(self, query: str) -> List[str]:
        """
        从查询中提取可能的化学品名称

        Args:
            query: 查询字符串

        Returns:
            提取的化学品名称列表
        """
        try:
            chemical_names = []

            # 常见的查询模式和对应的化学品名称提取
            patterns = [
                # "XX存储要求" -> "XX"
                r'(.+?)存储要求',
                r'(.+?)储存要求',
                r'(.+?)保存要求',
                # "XX的存储要求" -> "XX"
                r'(.+?)的存储要求',
                r'(.+?)的储存要求',
                r'(.+?)的保存要求',
                # "XX运输要求" -> "XX"
                r'(.+?)运输要求',
                r'(.+?)的运输要求',
                # "XX安全要求" -> "XX"
                r'(.+?)安全要求',
                r'(.+?)的安全要求',
                # "XX包装要求" -> "XX"
                r'(.+?)包装要求',
                r'(.+?)的包装要求',
                # "XX危险性" -> "XX"
                r'(.+?)危险性',
                r'(.+?)的危险性',
                # "XX注意事项" -> "XX"
                r'(.+?)注意事项',
                r'(.+?)的注意事项',
                # "XX规定" -> "XX"
                r'(.+?)规定',
                r'(.+?)的规定',
            ]

            for pattern in patterns:
                import re
                match = re.search(pattern, query)
                if match:
                    name = match.group(1).strip()
                    # 过滤掉过短或包含特殊字符的名称
                    if len(name) >= 2 and not re.search(r'[0-9]{3,}', name):
                        chemical_names.append(name)

            # 去重并保持顺序
            seen = set()
            unique_names = []
            for name in chemical_names:
                if name not in seen:
                    seen.add(name)
                    unique_names.append(name)

            return unique_names[:3]  # 最多返回3个名称

        except Exception as e:
            logger.error(f"提取化学品名称失败: {e}")
            return []
