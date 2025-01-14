import io
from typing import Any, Dict, List, Tuple

import pandas as pd
from django.utils import timezone

from .serializers import NewsArticleImportSerializer


class NewsImportExportHelper:
    """新闻导入导出助手"""

    EXCEL_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    CSV_CONTENT_TYPE = "text/csv"

    REQUIRED_COLUMNS = ["title", "content", "category"]
    OPTIONAL_COLUMNS = ["summary", "source", "author", "url", "tags", "publish_time"]
    ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

    @classmethod
    def read_file(cls, file) -> pd.DataFrame:
        """读取文件内容"""
        content_type = getattr(file, "content_type", "")

        try:
            if content_type == cls.EXCEL_CONTENT_TYPE:
                return pd.read_excel(file)
            elif content_type == cls.CSV_CONTENT_TYPE:
                return pd.read_csv(file)
            else:
                raise ValueError("不支持的文件格式，仅支持Excel和CSV文件")
        except Exception as e:
            raise ValueError(f"文件读取失败：{str(e)}")

    @classmethod
    def validate_dataframe(cls, df: pd.DataFrame) -> None:
        """验证数据框架的格式"""
        # 检查必填列
        missing_columns = [col for col in cls.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise ValueError(f'缺少必填列：{", ".join(missing_columns)}')

        # 移除未知列
        unknown_columns = [col for col in df.columns if col not in cls.ALL_COLUMNS]
        if unknown_columns:
            df.drop(columns=unknown_columns, inplace=True)

    @classmethod
    def process_row(cls, row: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """处理单行数据"""
        try:
            # 清理数据
            data = {k: v for k, v in row.items() if pd.notna(v)}

            # 验证并转换数据
            serializer = NewsArticleImportSerializer(data=data)
            if serializer.is_valid():
                return True, serializer.validated_data, ""
            else:
                return False, {}, str(serializer.errors)

        except Exception as e:
            return False, {}, str(e)

    @classmethod
    def import_data(cls, file) -> Dict[str, Any]:
        """导入数据"""
        try:
            # 读取文件
            df = cls.read_file(file)

            # 验证格式
            cls.validate_dataframe(df)

            # 处理数据
            total = len(df)
            success = 0
            failed = 0
            errors = []

            # 转换为字典列表
            records = df.to_dict("records")

            # 处理每一行
            for index, row in enumerate(records, start=1):
                is_valid, data, error = cls.process_row(row)

                if is_valid:
                    try:
                        serializer = NewsArticleImportSerializer()
                        serializer.create(data)
                        success += 1
                    except Exception as e:
                        failed += 1
                        errors.append({"row": index, "error": str(e), "data": row})
                else:
                    failed += 1
                    errors.append({"row": index, "error": error, "data": row})

            return {"total": total, "success": success, "failed": failed, "errors": errors}

        except Exception as e:
            raise ValueError(f"导入失败：{str(e)}")

    @classmethod
    def export_data(cls, queryset, file_type: str) -> Tuple[bytes, str]:
        """导出数据"""
        try:
            # 准备数据
            data = []
            for article in queryset:
                row = {
                    "title": article.title,
                    "content": article.content,
                    "summary": article.summary,
                    "source": article.source,
                    "author": article.author,
                    "url": article.url,
                    "category": article.category.name if article.category else "",
                    "tags": ",".join(article.tags) if article.tags else "",
                    "status": article.get_status_display(),
                    "publish_time": article.publish_time,
                    "created_at": article.created_at,
                }
                data.append(row)

            # 创建DataFrame
            df = pd.DataFrame(data)

            # 导出文件
            output = io.BytesIO()

            if file_type == "excel":
                df.to_excel(output, index=False, engine="openpyxl")
                content_type = cls.EXCEL_CONTENT_TYPE
                file_ext = ".xlsx"
            else:  # csv
                df.to_csv(output, index=False)
                content_type = cls.CSV_CONTENT_TYPE
                file_ext = ".csv"

            output.seek(0)
            return output.getvalue(), content_type, file_ext

        except Exception as e:
            raise ValueError(f"导出失败：{str(e)}")
