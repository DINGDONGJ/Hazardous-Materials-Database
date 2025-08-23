"""
MySQL数据库处理模块
负责危险化学品名录表的创建、数据操作和查询
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from typing import List, Dict, Any, Optional
from loguru import logger
import pandas as pd

from config.database import DatabaseConfig

Base = declarative_base()


class HazardousChemicalsCatalog(Base):
    """危险化学品名录表模型"""
    __tablename__ = 'hazardous_chemicals_catalog'

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='自增ID')

    # 使用实际数据库中的中文列名
    un_number = Column('联合国编号', Integer, nullable=False, comment='联合国编号')
    chinese_name = Column('名称和说明', Text, comment='中文名称和说明')
    english_name = Column('英文名称和说明', Text, comment='英文名称和说明')
    category = Column('类别或项别', String(100), comment='类别或项别')
    secondary_hazard = Column('次要危险性', String(100), comment='次要危险性')
    packaging_group = Column('包装类别', String(50), comment='包装类别')
    special_provisions = Column('特殊规定', String(200), comment='特殊规定')
    limited_quantity = Column('有限数量', String(50), comment='有限数量')
    excepted_quantity = Column('例外数量', String(50), comment='例外数量')
    packaging_instruction = Column('包装和中型散装容器包装指南', String(200), comment='包装和中型散装容器包装指南')
    packaging_special_provision = Column('包装和中型散装容器特殊包装规定', String(200), comment='包装和中型散装容器特殊包装规定')
    portable_tank_instruction = Column('可移动罐柜和散装容器指南', String(200), comment='可移动罐柜和散装容器指南')
    portable_tank_special_provision = Column('可移动罐柜和散装容器特殊规定', String(200), comment='可移动罐柜和散装容器特殊规定')

    # 时间戳
    created_at = Column('创建时间', TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column('更新时间', TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 索引
    __table_args__ = (
        Index('idx_un_number', '联合国编号'),
        Index('idx_chinese_name', '名称和说明'),
        Index('idx_category', '类别或项别'),
        Index('idx_packaging_group', '包装类别'),
    )


class MySQLHandler:
    """MySQL数据库处理器"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
        self.connect()
    
    def connect(self):
        """连接到MySQL数据库"""
        try:
            self.engine = create_engine(
                DatabaseConfig.get_mysql_url(),
                echo=False,  # 设置为True可以看到SQL语句
                pool_pre_ping=True,
                pool_recycle=3600
            )
            self.Session = sessionmaker(bind=self.engine)
            logger.info("MySQL数据库连接成功")
        except Exception as e:
            logger.error(f"MySQL数据库连接失败: {e}")
            raise
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    def drop_tables(self):
        """删除所有表（谨慎使用）"""
        try:
            Base.metadata.drop_all(self.engine)
            logger.warning("数据库表已删除")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
    
    def insert_chemical(self, chemical_data: Dict[str, Any]) -> bool:
        """插入单条化学品记录"""
        session = self.Session()
        try:
            chemical = HazardousChemicalsCatalog(**chemical_data)
            session.add(chemical)
            session.commit()
            logger.debug(f"插入化学品记录成功: UN{chemical_data.get('un_number')}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"插入化学品记录失败: {e}")
            return False
        finally:
            session.close()
    
    def batch_insert_chemicals(self, chemicals_data: List[Dict[str, Any]]) -> int:
        """批量插入化学品记录"""
        session = self.Session()
        success_count = 0
        
        try:
            for chemical_data in chemicals_data:
                try:
                    chemical = HazardousChemicalsCatalog(**chemical_data)
                    session.add(chemical)
                    success_count += 1
                except Exception as e:
                    logger.warning(f"跳过无效记录: {chemical_data.get('un_number')}, 错误: {e}")
                    continue
            
            session.commit()
            logger.info(f"批量插入完成，成功插入 {success_count} 条记录")
            return success_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"批量插入失败: {e}")
            return 0
        finally:
            session.close()
    
    def query_by_un_number(self, un_number: int) -> List[Dict[str, Any]]:
        """根据UN编号查询化学品（返回所有匹配的记录）"""
        session = self.Session()
        try:
            chemicals = session.query(HazardousChemicalsCatalog).filter(
                HazardousChemicalsCatalog.un_number == un_number
            ).all()

            if chemicals:
                return [self._chemical_to_dict(chemical) for chemical in chemicals]
            return []

        except Exception as e:
            logger.error(f"查询UN编号 {un_number} 失败: {e}")
            return []
        finally:
            session.close()
    
    def search_by_name(self, name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """根据名称搜索化学品"""
        session = self.Session()
        try:
            chemicals = session.query(HazardousChemicalsCatalog).filter(
                HazardousChemicalsCatalog.chinese_name.like(f'%{name}%')
            ).limit(limit).all()

            return [self._chemical_to_dict(chemical) for chemical in chemicals]

        except Exception as e:
            logger.error(f"按名称搜索失败: {e}")
            return []
        finally:
            session.close()
    
    def get_all_chemicals(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有化学品记录"""
        session = self.Session()
        try:
            query = session.query(HazardousChemicalsCatalog)
            if limit:
                query = query.limit(limit)
            
            chemicals = query.all()
            return [self._chemical_to_dict(chemical) for chemical in chemicals]
            
        except Exception as e:
            logger.error(f"获取所有化学品记录失败: {e}")
            return []
        finally:
            session.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        session = self.Session()
        try:
            total_count = session.query(HazardousChemicalsCatalog).count()

            # 按类别统计
            category_stats = session.query(
                HazardousChemicalsCatalog.category,
                func.count(HazardousChemicalsCatalog.un_number)
            ).group_by(HazardousChemicalsCatalog.category).all()

            # 按包装类别统计
            packaging_stats = session.query(
                HazardousChemicalsCatalog.packaging_group,
                func.count(HazardousChemicalsCatalog.un_number)
            ).group_by(HazardousChemicalsCatalog.packaging_group).all()

            return {
                'total_chemicals': total_count,
                'category_distribution': dict(category_stats),
                'packaging_group_distribution': dict(packaging_stats)
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
        finally:
            session.close()
    
    def _chemical_to_dict(self, chemical: HazardousChemicalsCatalog) -> Dict[str, Any]:
        """将化学品对象转换为字典"""
        return {
            'id': chemical.id,
            'un_number': chemical.un_number,
            'chinese_name': chemical.chinese_name,
            'english_name': chemical.english_name,
            'category': chemical.category,
            'secondary_hazard': chemical.secondary_hazard,
            'packaging_group': chemical.packaging_group,
            'special_provisions': chemical.special_provisions,
            'limited_quantity': chemical.limited_quantity,
            'excepted_quantity': chemical.excepted_quantity,
            'packaging_instruction': chemical.packaging_instruction,
            'packaging_special_provision': chemical.packaging_special_provision,
            'portable_tank_instruction': chemical.portable_tank_instruction,
            'portable_tank_special_provision': chemical.portable_tank_special_provision,
            'created_at': chemical.created_at.isoformat() if chemical.created_at else None,
            'updated_at': chemical.updated_at.isoformat() if chemical.updated_at else None
        }
