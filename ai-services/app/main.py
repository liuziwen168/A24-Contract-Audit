# app/main.py

import logging
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException

# 导入路由
from app.api.classify import router as classify_router
from app.api.extract import router as extract_router
from app.api.risk import router as risk_router
from app.api.review import router as review_router
from app.api.internal_review import router as internal_review_router
from app.api.parse import router as parse_router
from app.api.clause_compare import router as clause_compare_router

# 导入配置
from app.config import SERVER_HOST, SERVER_PORT, LOG_LEVEL, LOG_FILE

# 导入日志配置
from app.utils.logging_config import setup_logging, get_logger

# 导入异常处理器
from app.utils.exceptions import (
    BusinessException,
    business_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

# 导入中间件
from app.middleware.request_id import RequestIDMiddleware

# ============================================================
# 1. 初始化日志（最先执行）
# ============================================================
setup_logging(
    log_level=LOG_LEVEL,
    log_file=LOG_FILE,  # 如果为None则不写文件
    enable_colors=True
)

logger = get_logger(__name__)

# ============================================================
# 2. 创建FastAPI应用
# ============================================================
app = FastAPI(
    title="Contract AI Service",
    version="0.1.0",
    description="""
    ## 合同智能审核AI服务

    基于通义千问大模型，提供合同智能审核能力。

    ### 功能列表
    - **文档解析**：DOCX/PDF/图片解析，OCR识别，保留页码段落信息
    - **合同分类**：识别6类合同类型，返回置信度
    - **要素提取**：提取甲方、乙方、金额等6项要素（含置信度与位置）
    - **风险评估**：识别≥10类风险，给出等级、原文、位置、依据和建议
    - **标准条款比对**：与标准条款库比对，发现偏离和缺失
    - **完整审核**：一站式完成分类、提取、风险和条款比对

    ### 技术特性
    - ✅ 统一错误处理
    - ✅ 请求链路追踪（Request ID）
    - ✅ 结构化日志
    - ✅ AI输出清洗与验证
    - ✅ 自动重试机制（指数退避，最多3次）
    - ✅ 数据验证（Pydantic Schema + 自定义校验器）
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "文档解析",
            "description": "上传合同文档，返回结构化解析结果"
        },
        {
            "name": "合同分类",
            "description": "识别合同所属类型及置信度"
        },
        {
            "name": "合同要素提取",
            "description": "提取甲方、乙方、金额等6项关键要素（含置信度与位置）"
        },
        {
            "name": "合同风险评估",
            "description": "识别≥10类风险，输出等级、原文、位置、依据和建议"
        },
        {
            "name": "标准条款比对",
            "description": "与标准条款库比对，发现偏离条款和缺失条款"
        },
        {
            "name": "合同完整审核",
            "description": "一键完成分类、提取、风险和条款比对的全流程审核"
        },
        {
            "name": "internal",
            "description": "内部服务调用接口"
        }
    ]
)

# ============================================================
# 3. 添加中间件（顺序很重要）
# ============================================================

# 请求ID中间件 - 最先添加，最后执行
app.add_middleware(RequestIDMiddleware)

# 如果需要CORS，可以添加
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# ============================================================
# 4. 注册异常处理器
# ============================================================

# 业务异常
app.add_exception_handler(BusinessException, business_exception_handler)

# HTTP异常
app.add_exception_handler(HTTPException, http_exception_handler)

# 请求参数验证异常
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 全局异常捕获（兜底）
app.add_exception_handler(Exception, general_exception_handler)

# ============================================================
# 5. 注册路由
# ============================================================

# 合同分类
app.include_router(
    classify_router,
    prefix="/api/v1",
    tags=["合同分类"]
)

# 要素提取
app.include_router(
    extract_router,
    prefix="/api/v1",
    tags=["合同要素提取"]
)

# 风险评估
app.include_router(
    risk_router,
    prefix="/api/v1",
    tags=["合同风险评估"]
)

# 完整审核
app.include_router(
    review_router,
    prefix="/api/v1",
    tags=["合同完整审核"]
)

# 内部接口（保留原有路径）
app.include_router(
    internal_review_router,
    tags=["internal"]
)

# 文档解析
app.include_router(
    parse_router,
    prefix="/api/v1",
    tags=["文档解析"]
)

# 标准条款比对
app.include_router(
    clause_compare_router,
    prefix="/api/v1",
    tags=["标准条款比对"]
)

# ============================================================
# 6. 根路径和健康检查
# ============================================================

@app.get(
    "/",
    summary="健康检查",
    description="检查服务是否正常运行"
)
async def root():
    """根路径健康检查"""
    logger.info("健康检查请求")
    return {
        "code": 0,
        "message": "Contract AI Service Running",
        "data": {
            "version": "0.1.0",
            "status": "healthy",
            "service": "ai-services"
        }
    }


@app.get(
    "/health",
    summary="详细健康检查",
    description="检查服务及依赖的健康状态"
)
async def health_check():
    """详细健康检查"""
    import time
    
    health_status = {
        "code": 0,
        "message": "healthy",
        "data": {
            "service": "ai-services",
            "version": "0.1.0",
            "timestamp": time.time(),
            "dependencies": {
                "qwen": {
                    "status": "ready",
                    "model": "qwen-plus"
                }
            }
        }
    }
    
    # 检查API Key是否配置
    from app.config import DASHSCOPE_API_KEY
    if not DASHSCOPE_API_KEY:
        health_status["data"]["dependencies"]["qwen"]["status"] = "warning"
        health_status["data"]["dependencies"]["qwen"]["message"] = "API Key未配置"
        logger.warning("DASHSCOPE_API_KEY 未配置")
    
    logger.info("健康检查完成")
    return health_status


# ============================================================
# 7. 启动/关闭事件
# ============================================================

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("=" * 60)
    logger.info("🚀 Contract AI Service 启动中...")
    logger.info(f"📖 API文档: http://{SERVER_HOST}:{SERVER_PORT}/docs")
    logger.info(f"📚 ReDoc文档: http://{SERVER_HOST}:{SERVER_PORT}/redoc")
    logger.info(f"💚 健康检查: http://{SERVER_HOST}:{SERVER_PORT}/health")
    logger.info("=" * 60)
    
    # 检查关键配置
    from app.config import DASHSCOPE_API_KEY, MODEL_NAME
    if not DASHSCOPE_API_KEY:
        logger.warning("⚠️ DASHSCOPE_API_KEY 未配置，AI服务将不可用")
    else:
        logger.info(f"✅ AI模型: {MODEL_NAME}")
        logger.info(f"✅ API Key已配置 (长度: {len(DASHSCOPE_API_KEY)})")
    
    logger.info("✅ 服务启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("=" * 60)
    logger.info("🛑 Contract AI Service 正在关闭...")
    logger.info("=" * 60)


# ============================================================
# 8. 直接运行入口
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"启动服务: {SERVER_HOST}:{SERVER_PORT}")
    
    uvicorn.run(
        "app.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower(),
        # 以下参数可选
        # workers=1,  # 生产环境可以增加worker数
        # access_log=False,  # 关闭uvicorn的access日志（已有自定义日志）
    )