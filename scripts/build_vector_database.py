#!/usr/bin/env python3
"""
向量数据库构建脚本
将MySQL数据和Markdown文档导入向量数据库
"""

import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from loguru import logger
from src.database.mysql_handler import MySQLHandler
from src.vector_db.chroma_handler import VectorHandler
from config.settings import Settings


def setup_logging():
    """设置日志"""
    log_config = Settings.get_log_config()
    
    # 确保日志目录存在
    log_dir = Path(log_config['file']).parent
    log_dir.mkdir(exist_ok=True)
    
    # 配置loguru
    logger.remove()  # 移除默认处理器
    logger.add(
        sys.stdout,
        level=log_config['level'],
        format=log_config['format']
    )
    logger.add(
        log_config['file'],
        level=log_config['level'],
        format=log_config['format'],
        rotation="10 MB"
    )


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import faiss
        import sklearn
        import jieba
        import numpy
        logger.info("✅ 所有依赖包检查通过")
        return True
    except ImportError as e:
        logger.error(f"❌ 缺少依赖包: {e}")
        logger.error("请运行: pip install faiss-cpu scikit-learn jieba numpy")
        return False


def test_mysql_connection():
    """测试MySQL连接"""
    try:
        mysql_handler = MySQLHandler()
        stats = mysql_handler.get_statistics()
        logger.info(f"✅ MySQL连接成功，数据库中有 {stats.get('total_chemicals', 0)} 条化学品记录")
        return mysql_handler
    except Exception as e:
        logger.error(f"❌ MySQL连接失败: {e}")
        return None


def build_vector_database(reset_existing: bool = False):
    """构建向量数据库"""
    start_time = time.time()
    
    try:
        logger.info("🚀 开始构建向量数据库...")
        
        # 1. 检查依赖
        if not check_dependencies():
            return False
        
        # 2. 测试MySQL连接
        mysql_handler = test_mysql_connection()
        if not mysql_handler:
            return False
        
        # 3. 初始化向量数据库处理器
        logger.info("📊 初始化向量数据库处理器...")
        vector_handler = VectorHandler()
        
        # 4. 重置数据库（如果需要）
        if reset_existing:
            logger.warning("🔄 重置现有向量数据库...")
            vector_handler.reset_collection()

        # 5. 检查现有数据
        stats = vector_handler.get_collection_stats()
        existing_count = stats.get('total_documents', 0)

        if existing_count > 0 and not reset_existing:
            logger.info(f"📋 向量数据库中已有 {existing_count} 个文档")
            user_input = input("是否要重新构建？(y/N): ").strip().lower()
            if user_input == 'y':
                vector_handler.reset_collection()
            else:
                logger.info("跳过构建，使用现有数据")
                return True
        
        # 6. 导入MySQL数据
        logger.info("📥 开始导入MySQL化学品数据...")
        mysql_success = vector_handler.import_mysql_data(mysql_handler)
        
        if not mysql_success:
            logger.error("❌ MySQL数据导入失败")
            return False
        
        # 7. 导入Markdown文档
        markdown_file = project_root / "附录A.md"
        if markdown_file.exists():
            logger.info("📄 开始导入附录A文档...")
            markdown_success = vector_handler.import_markdown_data(str(markdown_file))
            
            if not markdown_success:
                logger.warning("⚠️ Markdown文档导入失败，但MySQL数据已成功导入")
        else:
            logger.warning(f"⚠️ 未找到附录A文档: {markdown_file}")
        
        # 8. 验证构建结果
        final_stats = vector_handler.get_collection_stats()
        total_docs = final_stats.get('total_documents', 0)
        
        if total_docs > 0:
            elapsed_time = time.time() - start_time
            logger.info(f"🎉 向量数据库构建完成！")
            logger.info(f"📊 总文档数: {total_docs}")
            logger.info(f"⏱️ 耗时: {elapsed_time:.2f} 秒")
            logger.info(f"📁 数据库路径: {Settings.VECTOR_DB_PATH}")
            
            # 显示详细统计
            logger.info("📈 详细统计信息:")
            for key, value in final_stats.items():
                logger.info(f"   {key}: {value}")
            
            return True
        else:
            logger.error("❌ 向量数据库构建失败，没有导入任何文档")
            return False
            
    except Exception as e:
        logger.error(f"❌ 构建向量数据库时发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_vector_database():
    """测试向量数据库功能"""
    try:
        logger.info("🧪 开始测试向量数据库功能...")
        
        from src.retrieval.hybrid_retriever import HybridRetriever
        
        retriever = HybridRetriever()
        
        # 测试查询
        test_queries = [
            "UN1133",
            "锂电池",
            "易燃液体的运输要求",
            "包装类别I的化学品"
        ]
        
        for query in test_queries:
            logger.info(f"🔍 测试查询: '{query}'")
            results = retriever.retrieve(query, strategy="auto", top_k=3)
            
            if results:
                logger.info(f"✅ 找到 {len(results)} 个结果")
                for i, result in enumerate(results, 1):
                    content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                    logger.info(f"   {i}. {content_preview}")
            else:
                logger.warning(f"⚠️ 没有找到相关结果")
        
        logger.info("🎉 向量数据库测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试向量数据库失败: {e}")
        return False


def main():
    """主函数"""
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("🏗️  危险化学品向量数据库构建工具")
    logger.info("=" * 60)
    
    # 解析命令行参数
    reset_existing = "--reset" in sys.argv or "-r" in sys.argv
    test_only = "--test" in sys.argv or "-t" in sys.argv
    
    if test_only:
        # 仅测试现有数据库
        success = test_vector_database()
    else:
        # 构建数据库
        success = build_vector_database(reset_existing)
        
        if success:
            # 构建成功后进行测试
            test_vector_database()
    
    if success:
        logger.info("🎊 所有操作完成！")
        logger.info("💡 现在您可以使用混合检索系统进行查询了")
    else:
        logger.error("💥 操作失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
