#!/usr/bin/env python3
"""
向量数据库系统测试脚本
测试各种查询功能和性能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from loguru import logger
from src.retrieval.hybrid_retriever import HybridRetriever


def test_retrieval_strategies():
    """测试不同的检索策略"""
    logger.info("🧪 测试不同检索策略...")
    
    retriever = HybridRetriever()
    
    test_cases = [
        {
            'query': 'UN1133',
            'description': 'UN编号精确查询',
            'expected_strategy': 'exact'
        },
        {
            'query': '锂电池安全运输',
            'description': '自然语言查询',
            'expected_strategy': 'semantic'
        },
        {
            'query': '易燃液体包装要求',
            'description': '混合查询',
            'expected_strategy': 'hybrid'
        },
        {
            'query': '黏合剂',
            'description': '名称搜索',
            'expected_strategy': 'hybrid'
        }
    ]
    
    strategies = ['auto', 'exact', 'semantic', 'hybrid']
    
    for test_case in test_cases:
        logger.info(f"\n📋 测试用例: {test_case['description']}")
        logger.info(f"🔍 查询: '{test_case['query']}'")
        
        for strategy in strategies:
            start_time = time.time()
            result = retriever.retrieve(test_case['query'], strategy=strategy, top_k=3)
            elapsed_time = time.time() - start_time

            # 计算总结果数
            total_results = len(result.get('chemical_data', [])) + len(result.get('regulations', []))
            logger.info(f"   {strategy:>8} 策略: {total_results:2d} 个结果, {elapsed_time:.3f}s")

            # 显示第一个结果的预览
            chemical_data = result.get('chemical_data', [])
            if chemical_data:
                first_result = chemical_data[0]
                content_preview = first_result['content'][:80] + "..." if len(first_result['content']) > 80 else first_result['content']
                score = first_result.get('score', 0)
                logger.info(f"            首个结果 (分数: {score:.3f}): {content_preview}")


def test_query_performance():
    """测试查询性能"""
    logger.info("\n⚡ 测试查询性能...")
    
    retriever = HybridRetriever()
    
    # 准备测试查询
    test_queries = [
        "UN1133", "UN3480", "UN1410",
        "锂电池", "易燃液体", "腐蚀性物质",
        "包装类别I", "特殊规定188", "有限数量",
        "危险化学品运输", "安全包装要求", "标签规定"
    ]
    
    total_time = 0
    total_results = 0
    
    for query in test_queries:
        start_time = time.time()
        result = retriever.retrieve(query, strategy="auto", top_k=5)
        elapsed_time = time.time() - start_time

        # 计算总结果数
        query_results = len(result.get('chemical_data', [])) + len(result.get('regulations', []))

        total_time += elapsed_time
        total_results += query_results

        logger.info(f"'{query:20}' -> {query_results:2d} 结果, {elapsed_time:.3f}s")
    
    avg_time = total_time / len(test_queries)
    avg_results = total_results / len(test_queries)
    
    logger.info(f"\n📊 性能统计:")
    logger.info(f"   平均查询时间: {avg_time:.3f}s")
    logger.info(f"   平均结果数量: {avg_results:.1f}")
    logger.info(f"   总查询时间: {total_time:.3f}s")


def test_edge_cases():
    """测试边界情况"""
    logger.info("\n🔬 测试边界情况...")
    
    retriever = HybridRetriever()
    
    edge_cases = [
        ("", "空查询"),
        ("xyz123", "无意义查询"),
        ("UN99999", "不存在的UN编号"),
        ("a" * 1000, "超长查询"),
        ("特殊符号!@#$%^&*()", "特殊字符查询"),
        ("English query about chemicals", "英文查询"),
        ("UN1133 锂电池 易燃", "混合关键词查询")
    ]
    
    for query, description in edge_cases:
        try:
            start_time = time.time()
            result = retriever.retrieve(query, strategy="auto", top_k=3)
            elapsed_time = time.time() - start_time

            # 计算总结果数
            total_results = len(result.get('chemical_data', [])) + len(result.get('regulations', []))

            logger.info(f"✅ {description:20} -> {total_results:2d} 结果, {elapsed_time:.3f}s")

        except Exception as e:
            logger.error(f"❌ {description:20} -> 错误: {e}")


def test_system_stats():
    """测试系统统计信息"""
    logger.info("\n📈 获取系统统计信息...")
    
    try:
        retriever = HybridRetriever()
        stats = retriever.get_retrieval_stats()
        
        logger.info("📊 MySQL统计:")
        mysql_stats = stats.get('mysql_stats', {})
        for key, value in mysql_stats.items():
            logger.info(f"   {key}: {value}")
        
        logger.info("\n📊 向量数据库统计:")
        vector_stats = stats.get('vector_stats', {})
        for key, value in vector_stats.items():
            logger.info(f"   {key}: {value}")
        
        logger.info("\n⚙️ 配置信息:")
        config = stats.get('config', {})
        for key, value in config.items():
            logger.info(f"   {key}: {value}")
            
    except Exception as e:
        logger.error(f"❌ 获取统计信息失败: {e}")


def interactive_test():
    """简化的交互式测试"""
    # 在交互模式下，降低日志级别，只显示ERROR级别的日志
    logger.remove()
    logger.add(sys.stdout, level="ERROR", format="{time:HH:mm:ss} | {level} | {message}")

    print("🎮 危险化学品查询系统")
    print("输入 'quit' 退出")

    retriever = HybridRetriever()

    while True:
        try:
            query = input("\n请输入查询内容: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 退出系统")
                break

            if not query:
                continue

            # 使用默认设置：auto策略，返回更多结果，不显示详细流程
            result = retriever.retrieve(query, strategy='auto', top_k=50, verbose=False)

            # 处理结构化结果格式
            chemical_data = result.get('chemical_data', [])
            regulations = result.get('regulations', [])

            # 显示化学品数据
            if chemical_data:
                total_chemicals = len(chemical_data)
                print(f"\n📊 1. 从数据库中查找到的数据 ({total_chemicals} 条):")
                print("-" * 60)

                # 如果结果过多，询问用户是否要查看全部
                display_limit = 10  # 默认显示前10条
                show_all = False

                if total_chemicals > display_limit:
                    print(f"\n⚠️  找到 {total_chemicals} 条记录，默认显示前 {display_limit} 条。")
                    user_choice = input("是否查看全部结果？(y/n，默认n): ").strip().lower()
                    if user_choice in ['y', 'yes', '是']:
                        show_all = True
                        display_limit = total_chemicals
                    print()
                else:
                    show_all = True
                    display_limit = total_chemicals

                # 显示化学品记录
                for i, chem in enumerate(chemical_data[:display_limit], 1):
                    score = chem.get('score', 0)
                    source = chem.get('metadata', {}).get('source', 'unknown')

                    print(f"\n📄 化学品 {i} (分数: {score:.3f}, 来源: {source}):")

                    # 显示格式化的化学品信息
                    if chem.get('chemical_data'):
                        # 使用格式化后的内容，按行显示
                        formatted_content = chem['content']
                        for line in formatted_content.split('\n'):
                            if line.strip():
                                print(f"   {line}")
                    else:
                        # 如果没有化学品数据，显示内容预览
                        content_preview = chem['content'][:150] + "..." if len(chem['content']) > 150 else chem['content']
                        print(f"   {content_preview}")

                # 如果有更多结果未显示，提示用户
                if not show_all and total_chemicals > display_limit:
                    remaining = total_chemicals - display_limit
                    print(f"\n📝 还有 {remaining} 条记录未显示。如需查看全部，请重新搜索并选择查看全部结果。")

            # 显示相关法规
            if regulations:
                print(f"\n� 2. 附录A的相关规定 ({len(regulations)} 条):")
                print("-" * 60)

                for i, reg in enumerate(regulations, 1):
                    score = reg.get('score', 0)
                    content_preview = reg['content'][:200] + "..." if len(reg['content']) > 200 else reg['content']

                    print(f"\n📜 法规 {i} (相关度: {score:.3f}):")
                    print(f"   {content_preview}")

            if not chemical_data and not regulations:
                print("❌ 没有找到相关结果")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ 查询失败: {e}")

    print("👋 退出交互式测试")


def main():
    """主函数"""
    # 检查是否是交互模式
    if "--interactive" in sys.argv or "-i" in sys.argv:
        # 交互模式直接启动，不显示其他测试日志
        interactive_test()
        return

    # 非交互模式才显示详细测试日志
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

    logger.info("=" * 60)
    logger.info("🧪 向量数据库系统测试工具")
    logger.info("=" * 60)

    try:
        # 基础功能测试
        test_retrieval_strategies()

        # 性能测试
        test_query_performance()

        # 边界情况测试
        test_edge_cases()

        # 系统统计
        test_system_stats()
        
        logger.info("\n🎉 所有测试完成！")
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
