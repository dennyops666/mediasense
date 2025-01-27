class CrawlerError(Exception):
    """爬虫异常基类"""
    pass

class ConfigError(CrawlerError):
    """配置错误"""
    pass

class FetchError(CrawlerError):
    """获取数据错误"""
    pass

class ParseError(CrawlerError):
    """解析数据错误"""
    pass 