import html
import re
from typing import Dict, Any

class DataCleaningService:
    """数据清洗服务"""

    def clean_article(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗文章数据
        :param data: 原始数据
        :return: 清洗后的数据
        """
        cleaned_data = {}
        
        # 清洗标题
        if "title" in data:
            cleaned_data["title"] = self._clean_text(data["title"])
            
        # 清洗内容
        if "content" in data:
            cleaned_data["content"] = self._clean_text(data["content"])
            
        # 清洗作者
        if "author" in data:
            cleaned_data["author"] = self._clean_text(data["author"])
            
        # 清洗来源
        if "source" in data:
            cleaned_data["source"] = self._clean_text(data["source"])
            
        # 清洗URL
        if "url" in data:
            cleaned_data["url"] = data["url"].strip()
            
        # 清洗标签
        if "tags" in data:
            cleaned_data["tags"] = [
                self._clean_text(tag) for tag in data["tags"]
                if self._clean_text(tag)
            ]
            
        # 保留其他字段
        for key, value in data.items():
            if key not in cleaned_data:
                cleaned_data[key] = value
                
        return cleaned_data
        
    def _clean_text(self, text: str) -> str:
        """
        清洗文本
        :param text: 原始文本
        :return: 清洗后的文本
        """
        if not text:
            return ""
            
        # 解码HTML实体
        text = html.unescape(text)
        
        # 移除HTML标签
        text = re.sub(r"<[^>]+>", "", text)
        
        # 移除多余空白字符
        text = re.sub(r"\s+", " ", text)
        
        return text.strip() 