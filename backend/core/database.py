from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool
from fastapi import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from core.config import settings
import logging

logger = logging.getLogger(__name__)

# 判断是否为 SQLite
is_sqlite = settings.database_url.startswith("sqlite")

# 配置连接池参数
if is_sqlite:
    # SQLite 使用 StaticPool 或 NullPool，避免连接泄漏
    # 对于 SQLite，使用 StaticPool 并设置 check_same_thread=False
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},  # SQLite 需要
        poolclass=StaticPool,  # SQLite 使用静态连接池
        pool_pre_ping=True,  # 连接前检查连接是否有效
        echo=False,  # 生产环境关闭 SQL 日志
    )
else:
    # 其他数据库使用 QueuePool
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=10,  # 连接池大小
        max_overflow=20,  # 最大溢出连接数
        pool_pre_ping=True,  # 连接前检查连接是否有效
        pool_recycle=3600,  # 连接回收时间（秒）
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

if is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            pass


def get_db():
    """数据库依赖注入"""
    db = SessionLocal()
    try:
        yield db
    except (HTTPException, StarletteHTTPException):
        # HTTPException 是 FastAPI 正常返回给客户端的异常，不需要记录数据库异常日志
        db.rollback()
        raise
    except Exception as e:
        # 其他异常发生时回滚
        db.rollback()
        logger.error(f"数据库会话异常: {e}", exc_info=True)
        raise
    finally:
        # 确保连接被关闭
        try:
            db.close()
        except Exception as e:
            logger.error(f"关闭数据库会话失败: {e}", exc_info=True)


def close_db_connections():
    """关闭所有数据库连接"""
    try:
        engine.dispose()
        logger.info("数据库连接池已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接池失败: {e}", exc_info=True)
