"""OCR处理器 - 基于PaddleOCR的图片/扫描件文字识别"""
import logging
import os
from typing import Dict, Any, List

from app.core.config import settings
from app.core.exceptions import OCRFailedError
from app.utils.text_utils import clean_text

logger = logging.getLogger(__name__)


class OCRProcessor:
    """PaddleOCR处理器，对图片或扫描PDF进行文字识别"""

    def __init__(self):
        self._ocr = None
        self.language = settings.OCR_LANGUAGE
        self.use_gpu = settings.OCR_USE_GPU

    @property
    def ocr(self):
        """延迟初始化PaddleOCR"""
        if self._ocr is None:
            self._init_ocr()
        return self._ocr

    def _init_ocr(self):
        """初始化PaddleOCR引擎"""
        try:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.language,
                use_gpu=self.use_gpu,
                show_log=False,
            )
            logger.info(
                f"PaddleOCR初始化完成 - 语言: {self.language}, GPU: {self.use_gpu}"
            )
        except ImportError:
            logger.warning("PaddleOCR未安装，将使用模拟模式")
            self._ocr = None
        except Exception as e:
            logger.error(f"PaddleOCR初始化失败: {str(e)}")
            self._ocr = None

    def process(self, file_path: str) -> Dict[str, Any]:
        """
        OCR识别

        Args:
            file_path: 图片或扫描PDF文件路径

        Returns:
            {"text": "全文文本", "segments": [...], "warnings": [...]}
        """
        if not os.path.exists(file_path):
            raise OCRFailedError(f"文件不存在: {file_path}")

        # 获取所有图片路径
        image_paths = self._get_image_paths(file_path)

        if not image_paths:
            raise OCRFailedError(
                "未能提取到可识别的图片",
                detail={"file_path": file_path},
            )

        try:
            all_text_parts = []
            all_segments = []
            para_idx = 0

            for img_path in image_paths:
                page_texts, page_segments = self._ocr_image(img_path, para_idx)
                all_text_parts.extend(page_texts)
                all_segments.extend(page_segments)
                para_idx += len(page_segments)

            full_text = "\n\n".join(all_text_parts)
            full_text = clean_text(full_text)

            warnings = []
            if len(full_text) < 50:
                warnings.append("OCR识别结果文本量较少，请检查图片清晰度")
            if len(image_paths) > 50:
                warnings.append(
                    f"图片数量较多({len(image_paths)}张)，建议优化扫描质量"
                )

            return {
                "text": full_text,
                "segments": all_segments,
                "warnings": warnings,
            }

        except Exception as e:
            logger.error(f"OCR识别失败: {str(e)}")
            raise OCRFailedError(f"OCR识别失败: {str(e)}")

    def _get_image_paths(self, file_path: str) -> List[str]:
        """获取待OCR的图片路径列表"""
        ext = os.path.splitext(file_path)[1].lower()

        if ext in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif"}:
            return [file_path]

        if ext == ".pdf":
            return self._pdf_to_images(file_path)

        # 尝试作为图片处理
        return [file_path]

    def _pdf_to_images(self, file_path: str) -> List[str]:
        """将PDF转换为图片列表"""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            image_paths = []
            temp_dir = os.path.join(os.path.dirname(file_path), "_ocr_temp")

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # 渲染为图片
                pix = page.get_pixmap(dpi=300)
                img_path = os.path.join(temp_dir, f"page_{page_num + 1:04d}.png")
                os.makedirs(temp_dir, exist_ok=True)
                pix.save(img_path)
                image_paths.append(img_path)

            doc.close()
            return image_paths

        except ImportError:
            logger.warning("PyMuPDF(fitz)未安装，无法将PDF转为图片")
            # 尝试使用pdfplumber
            return self._pdf_fallback(file_path)

    def _pdf_fallback(self, file_path: str) -> List[str]:
        """PDF OCR回退方案"""
        try:
            import pdfplumber
            from PIL import Image
            import io

            image_paths = []
            temp_dir = os.path.join(os.path.dirname(file_path), "_ocr_temp")
            os.makedirs(temp_dir, exist_ok=True)

            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    img = page.to_image(resolution=300)
                    img_path = os.path.join(
                        temp_dir, f"page_{page_num:04d}.png"
                    )
                    # pdfplumber的to_image返回的是Image对象，需要保存
                    if hasattr(img, "save"):
                        img.save(img_path)
                        image_paths.append(img_path)
                    elif hasattr(img, "annotated"):
                        img.annotated.save(img_path)
                        image_paths.append(img_path)

            return image_paths

        except Exception as e:
            logger.error(f"PDF转图片失败: {str(e)}")
            return []

    def _ocr_image(
        self, img_path: str, start_para_idx: int = 0
    ) -> tuple:
        """对单张图片进行OCR"""
        if self._ocr is None:
            return self._mock_ocr(img_path, start_para_idx)

        try:
            result = self.ocr.ocr(img_path, cls=True)
            if not result or not result[0]:
                return [], []

            texts = []
            segments = []
            para_idx = start_para_idx

            # PaddleOCR result[0]是文字检测和识别结果列表
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0]  # 识别的文字
                    confidence = line[1][1]  # 置信度
                    bbox = line[0]  # 边界框坐标

                    if text.strip():
                        texts.append(text.strip())
                        # 从bbox计算粗略页码（假设每页约A4高度）
                        avg_y = sum(p[1] for p in bbox) / len(bbox)
                        page_est = max(1, int(avg_y // 1000) + 1)

                        segments.append({
                            "text": text.strip(),
                            "page": page_est if len(texts) > 10 else 1,
                            "paragraph_index": para_idx,
                            "confidence": float(confidence),
                        })
                        para_idx += 1

            return texts, segments

        except Exception as e:
            logger.error(f"OCR单张图片失败 {img_path}: {str(e)}")
            return [], []

    @staticmethod
    def _mock_ocr(img_path: str, start_para_idx: int = 0) -> tuple:
        """PaddleOCR未安装时的模拟回退"""
        logger.warning(f"使用模拟OCR模式处理: {img_path}")
        return (
            ["[OCR引擎未初始化，请安装PaddleOCR]"],
            [{
                "text": "[OCR引擎未初始化，请安装PaddleOCR]",
                "page": 1,
                "paragraph_index": start_para_idx,
                "confidence": 0.0,
            }],
        )
