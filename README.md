# 危险化学品查询系统

## 📋 项目概述

危险化学品查询系统是一个基于混合检索技术的智能查询平台，专门用于查询危险化学品的详细信息和相关法规。系统集成了MySQL数据库、向量数据库和智能搜索算法，为用户提供准确、全面的化学品安全信息。

### 🎯 主要功能

- **多模式查询**：支持UN编号、化学品名称、自然语言查询
- **智能关键词扩展**：自动匹配相关词汇（如"锂电池"→"锂离子电池"、"锂金属电池"）
- **法规关联**：自动匹配附录A相关规定
- **分页显示**：智能处理大量搜索结果
- **混合检索**：结合精确搜索和语义搜索，提供最佳匹配结果

### 🏗️ 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户界面      │    │   检索引擎      │    │   数据存储      │
│                 │    │                 │    │                 │
│ • 交互式CLI     │◄──►│ • HybridRetriever│◄──►│ • MySQL数据库   │
│ • 查询输入      │    │ • 智能策略选择  │    │ • 向量数据库    │
│ • 结果展示      │    │ • 关键词扩展    │    │ • FAISS索引     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 安装和配置指南

### 环境要求

- **Python**: 3.8+
- **操作系统**: Windows 10+, Ubuntu 18.04+
- **内存**: 建议4GB以上
- **存储**: 至少2GB可用空间

### 依赖安装

#### 1. 克隆项目
```bash
git clone <repository-url>
cd danger-chemical-query-system
```

#### 2. 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 数据库配置

#### 1. MySQL配置和数据导入
```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE hazardous_chemicals;
EXIT;

# 使用提供的SQL脚本初始化数据库和导入数据
mysql -u root -p hazardous_chemicals < hazardous_chemicals_localhost-2025_08_21_22_25_59-dump.sql
```

#### 2. 环境变量配置
创建 `.env` 文件：
```env
# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=hazardous_chemicals

# 向量数据库配置
VECTOR_DB_PATH=./data/vector_db
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2

# 检索配置
RETRIEVAL_TOP_K=50
SIMILARITY_THRESHOLD=0.1
```

### 数据文件说明

#### 核心数据文件：hazardous_chemicals_catalog.csv

系统的核心数据文件位于 `data/raw/hazardous_chemicals_catalog.csv`，包含完整的危险化学品目录信息。

**文件特点**：
- **记录数量**: 2,593条危险化学品记录
- **数据来源**: 从MySQL数据库导出的标准化数据
- **更新时间**: 2025年8月18日
- **文件大小**: 约2MB

**主要字段**：
- `联合国编号`: UN编号（如1133、3480）
- `名称和说明`: 中文化学品名称
- `英文名称和说明`: 英文化学品名称
- `类别或项别`: 危险品分类（1-9类）
- `包装类别`: 包装分组（I、II、III）
- `特殊规定`: 特殊规定编号
- `有限数量`: 有限数量限制
- `包装指南`: 包装和运输指南

**使用方法**：
```bash
# Linux 使用SQL脚本导入数据到MySQL
mysql -u root -p hazardous_chemicals < hazardous_chemicals_localhost-2025_08_21_22_25_59-dump.sql

# Windows 使用SQL脚本导入数据到MySQL
mysql -u root -p hazardous_chemicals < "hazardous_chemicals_localhost-2025_08_21_22_25_59-dump.sql"
# 或者在MySQL命令行中执行：
# mysql> source hazardous_chemicals_localhost-2025_08_21_22_25_59-dump.sql;
```

详细的数据结构和使用说明请参考 [数据指南](docs/DATA_GUIDE.md)。

## 📖 使用说明

### 启动系统

```bash
python scripts/test_vector_system.py --interactive
```

### 查询类型

#### 1. UN编号查询
```
请输入查询内容: 1133
请输入查询内容: UN3480
```

#### 2. 化学品名称查询
```
请输入查询内容: 黏合剂
请输入查询内容: 锂电池
请输入查询内容: 汽油
```

#### 3. 自然语言查询
```
请输入查询内容: 锂电池安全运输
请输入查询内容: 易燃液体包装要求
请输入查询内容: 危险化学品运输
```

### 搜索结果解读

#### 化学品信息
```
📄 化学品 1 (分数: 1.000, 来源: mysql):
   联合国编号: 1133
   名称和说明: 黏合剂，含有易燃液体
   英文名称和说明: ADHESIVES containing flammable liquid
   类别或项别: 3
   包装类别: I
   特殊规定: 223
   有限数量: 500 mL
   例外数量: E3
   包装和中型散装容器包装指南: P001
```

#### 法规信息
```
📜 法规 1 (相关度: 0.243):
   223 本条目所包括的物质, 如其化学或物理性质在试验时不符合表 1 中"类别或项别"一栏所列的类别或项别, 或者任何其他类别或项别的定义标准, 不受本文件限制。
```

### 分页显示功能

当搜索结果超过10条时，系统会提示：
```
⚠️  找到 50 条记录，默认显示前 10 条。
是否查看全部结果？(y/n，默认n): 
```

- 输入 `y` 或 `yes` 查看全部结果
- 输入 `n` 或直接回车只显示前10条

## 🔧 API文档

### HybridRetriever 类

主要的检索引擎类，提供多种搜索策略。

```python
from src.retrieval.hybrid_retriever import HybridRetriever

retriever = HybridRetriever()
result = retriever.retrieve(query="锂电池", strategy="auto", top_k=50)
```

#### 方法说明

##### `retrieve(query, strategy="auto", top_k=50, verbose=False)`

**参数**：
- `query` (str): 查询内容
- `strategy` (str): 搜索策略 ("auto", "exact", "semantic", "hybrid")
- `top_k` (int): 返回结果数量上限
- `verbose` (bool): 是否显示详细日志

**返回值**：
```python
{
    'chemical_data': [
        {
            'content': '格式化的化学品信息',
            'metadata': {'source': 'mysql', 'un_number': '1133'},
            'score': 1.0,
            'chemical_data': {...}  # 原始数据
        }
    ],
    'regulations': [
        {
            'content': '法规内容',
            'metadata': {'source': 'appendix_a'},
            'score': 0.8
        }
    ]
}
```

### MySQLHandler 类

MySQL数据库操作类。

```python
from src.database.mysql_handler import MySQLHandler

handler = MySQLHandler()
handler.connect()
chemicals = handler.search_by_name("锂电池", limit=50)
```

#### 主要方法

- `query_by_un_number(un_number)`: 根据UN编号查询
- `search_by_name(name, limit=50)`: 根据名称搜索
- `get_statistics()`: 获取数据库统计信息

### VectorHandler 类

向量数据库操作类。

```python
from src.vector_db.chroma_handler import VectorHandler

handler = VectorHandler()
results = handler.semantic_search("锂电池", top_k=10)
```

#### 主要方法

- `semantic_search(query, top_k=10)`: 语义搜索
- `add_documents(documents, metadata)`: 添加文档
- `get_stats()`: 获取统计信息

## ⭐ 系统特性

### 1. 智能关键词扩展

系统能够自动扩展搜索关键词，提高搜索准确性：

```python
# 用户输入: "锂电池"
# 系统自动扩展为: ["锂离子电池", "锂金属电池", "锂合金电池"]

# 用户输入: "易燃"  
# 系统自动扩展为: ["易燃液体", "易燃固体", "易燃气体"]
```

### 2. 法规关联功能

系统会自动匹配相关的附录A法规：

1. **优先匹配特殊规定编号**：如384、388、405等
2. **化学品类型关键词匹配**：如"电池"、"易燃"等
3. **相关度评分**：显示法规与化学品的相关程度

### 3. 分页显示功能

- **默认显示**：前10条记录
- **智能提示**：超过10条时询问用户
- **性能保护**：最大限制50条记录
- **用户友好**：避免信息过载

## 📊 性能指标

基于当前测试数据的性能统计：

```
📊 性能统计:
   平均查询时间: 0.012s
   平均结果数量: 2.2
   总查询时间: 0.142s
   
📊 数据库统计:
   化学品总数: 2593
   法规总数: 265
   向量文档总数: 2858
```

## 🔍 故障排除

### 常见问题

#### 1. 数据库连接失败
```
错误: MySQL连接失败
解决: 检查.env文件中的数据库配置，确保MySQL服务正在运行
```

#### 2. 向量数据库加载失败
```
错误: 向量索引加载失败
解决: 运行 python scripts/build_vector_database.py 重新构建向量数据库
```

#### 3. 搜索结果为空
```
错误: 没有找到相关结果
解决: 
- 检查查询关键词拼写
- 尝试使用UN编号查询
- 检查数据库是否正确初始化
```

#### 4. 性能问题
```
错误: 查询速度慢
解决:
- 减少top_k参数值
- 检查数据库索引
- 确保有足够的内存
```

### 日志调试

启用详细日志：
```python
result = retriever.retrieve(query, verbose=True)
```

查看日志文件：
```bash
tail -f logs/system.log
```

## 🖥️ 跨平台支持

### Windows 运行

```cmd
# 安装依赖
pip install -r requirements.txt

# 启动系统
python scripts\test_vector_system.py --interactive
```

**注意事项**：
- 确保安装了Visual C++ Build Tools（用于编译某些依赖）
- 推荐使用Anaconda或Miniconda管理Python环境

### Linux 运行

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip mysql-server

# CentOS/RHEL
sudo yum install python3-pip mysql-server

# 安装依赖
pip3 install -r requirements.txt

# 启动系统
python3 scripts/test_vector_system.py --interactive
```

**注意事项**：
- 确保MySQL服务正在运行
- 可能需要配置防火墙规则

## 👨‍💻 开发者指南

### 项目结构

```
Hazardous-Materials-Database-main/
├── src/                          # 源代码目录
│   ├── database/                 # 数据库操作模块
│   │   └── mysql_handler.py      # MySQL数据库操作
│   ├── retrieval/                # 检索引擎模块
│   │   └── hybrid_retriever.py   # 混合检索引擎
│   ├── vector_db/                # 向量数据库模块
│   │   └── chroma_handler.py     # 向量数据库操作
│   ├── data_processing/          # 数据处理模块
│   │   └── text_processor.py     # 文本处理器
│   └── utils/                    # 工具函数
│       └── helpers.py            # 辅助函数
├── scripts/                      # 脚本工具
│   ├── build_vector_database.py  # 向量数据库构建
│   ├── convert_xlsx_to_csv.py    # Excel转CSV工具
│   └── test_vector_system.py     # 测试和交互界面
├── config/                       # 配置文件
│   ├── database.py               # 数据库配置
│   └── settings.py               # 系统设置
├── data/                         # 数据文件目录
│   ├── raw/                      # 原始数据文件
│   │   └── hazardous_chemicals_catalog.csv  # 核心数据文件
│   └── vector_db/                # 向量数据库文件
│       ├── documents.pkl         # 文档数据
│       ├── faiss_index.index     # FAISS向量索引
│       ├── metadata.json         # 元数据
│       └── vectorizer.pkl        # 向量化器
├── docs/                         # 文档目录
│   ├── DATA_GUIDE.md             # 数据指南
│   ├── API_EXAMPLES.md           # API示例
│   ├── INSTALL.md                # 安装指南
│   └── PERFORMANCE.md            # 性能报告
├── requirements.txt              # Python依赖列表
├── .env.example                  # 环境变量示例
├── hazardous_chemicals_localhost-2025_08_21_22_25_59-dump.sql  # 数据库初始化脚本
└── 附录A.md                      # 法规附录文档
```

### 扩展开发

#### 1. 添加新的搜索策略

```python
class HybridRetriever:
    def _custom_search(self, query: str, top_k: int) -> List[Dict]:
        """自定义搜索策略"""
        # 实现自定义搜索逻辑
        pass

    def retrieve(self, query: str, strategy: str = "auto", **kwargs):
        if strategy == "custom":
            return self._custom_search(query, kwargs.get('top_k', 5))
        # 其他策略...
```

#### 2. 添加新的数据源

```python
class NewDataHandler:
    def __init__(self):
        # 初始化新数据源连接
        pass

    def search(self, query: str) -> List[Dict]:
        # 实现搜索逻辑
        pass
```

#### 3. 自定义关键词扩展

```python
def _expand_search_terms(self, query: str) -> List[str]:
    """扩展搜索词"""
    expanded_terms = []

    # 添加自定义扩展规则
    if "新关键词" in query:
        expanded_terms.extend(["相关词1", "相关词2"])

    return expanded_terms
```

### 测试

运行单元测试：
```bash
python -m pytest tests/
```

运行性能测试：
```bash
python scripts/test_vector_system.py --performance
```

### 贡献指南

1. Fork项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 📚 文档索引

### 核心文档
- **[README.md](README.md)** - 项目主要文档（当前文档）
- **[数据指南](docs/DATA_GUIDE.md)** - 数据文件详细说明和使用指南
- **[安装指南](docs/INSTALL.md)** - 详细的安装和配置说明
- **[API示例](docs/API_EXAMPLES.md)** - 完整的API使用示例
- **[性能报告](docs/PERFORMANCE.md)** - 性能测试和优化指南

### 配置文件
- **[.env.example](.env.example)** - 环境变量配置示例
- **[requirements.txt](requirements.txt)** - Python依赖列表

### 法规文档
- **[附录A.md](附录A.md)** - 危险货物运输法规附录

## 🤝 支持

如有问题或建议，请：
- 提交Issue
- 查看相关文档：[docs/](docs/)

---

**版本**: 1.0.0
**最后更新**: 2025年8月
**维护者**: 开发团队
