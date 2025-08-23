#!/usr/bin/env python3
"""
Excel文件转CSV工具
将xlsx文件转换为CSV格式，便于导入系统
"""

import pandas as pd
import sys
import os
import argparse

def convert_xlsx_to_csv(xlsx_file, csv_file=None, sheet_name=0):
    """
    将xlsx文件转换为CSV
    
    Args:
        xlsx_file: Excel文件路径
        csv_file: 输出CSV文件路径（可选）
        sheet_name: 工作表名称或索引（默认第一个）
    """
    try:
        print(f"正在读取Excel文件: {xlsx_file}")
        
        # 读取Excel文件
        df = pd.read_excel(xlsx_file, sheet_name=sheet_name)
        
        print(f"成功读取数据，共 {len(df)} 行，{len(df.columns)} 列")
        print("列名:", list(df.columns))
        
        # 如果没有指定输出文件，自动生成
        if csv_file is None:
            base_name = os.path.splitext(xlsx_file)[0]
            csv_file = f"{base_name}.csv"
        
        # 确保输出目录存在
        output_dir = os.path.dirname(csv_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存为CSV
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ 转换成功！CSV文件保存为: {csv_file}")
        
        # 显示前几行数据预览
        print("\n数据预览（前5行）:")
        print(df.head().to_string())
        
        return csv_file
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return None

def check_column_mapping(csv_file):
    """检查CSV文件的列名映射"""
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        
        print(f"\n=== 列名检查 ===")
        print("当前列名:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. {col}")
        
        # 建议的列名映射
        suggested_mapping = {
            'UN编号': ['UN编号', 'UN号', 'UN_NUMBER', 'UN Number'],
            '中文名称': ['中文名称', '名称', '化学品名称', 'Chinese Name'],
            '英文名称': ['英文名称', 'English Name', 'English'],
            '危险性类别': ['危险性类别', '危险类别', 'Hazard Class', 'Class'],
            '数量限制': ['数量限制', 'Quantity Limit', 'Limit'],
            '特殊规定': ['特殊规定', 'Special Provisions', 'Provisions']
        }
        
        print(f"\n=== 列名映射建议 ===")
        print("如果您的列名与以下标准不同，请手动修改CSV文件的列名:")
        
        for standard_name, alternatives in suggested_mapping.items():
            print(f"\n标准列名: {standard_name}")
            print(f"可接受的变体: {', '.join(alternatives)}")
            
            # 检查是否有匹配的列
            found_match = False
            for col in df.columns:
                if col in alternatives:
                    print(f"✅ 找到匹配列: {col}")
                    found_match = True
                    break
            
            if not found_match:
                print("⚠️  未找到匹配列，请检查列名")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查列名失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Excel转CSV工具')
    parser.add_argument('xlsx_file', help='Excel文件路径')
    parser.add_argument('--output', '-o', help='输出CSV文件路径')
    parser.add_argument('--sheet', '-s', default=0, help='工作表名称或索引（默认第一个）')
    parser.add_argument('--check', '-c', action='store_true', help='检查转换后的列名')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.xlsx_file):
        print(f"❌ 文件不存在: {args.xlsx_file}")
        return
    
    # 转换文件
    csv_file = convert_xlsx_to_csv(args.xlsx_file, args.output, args.sheet)
    
    if csv_file and args.check:
        check_column_mapping(csv_file)
    
    if csv_file:
        print(f"\n=== 下一步 ===")
        print(f"1. 检查CSV文件内容: {csv_file}")
        print(f"2. 如需要，调整列名以匹配系统要求")
        print(f"3. 运行导入命令:")
        print(f"   python scripts/import_data.py --csv {csv_file}")

if __name__ == "__main__":
    main()
