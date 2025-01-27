import logging

logger = logging.getLogger(__name__)

def _get_field_value(item, path):
    """
    从字典中获取指定路径的值
    :param item: 字典数据
    :param path: 字段路径，例如 'a.b.c'
    :return: 字段值
    """
    try:
        if not path:
            logger.debug('字段路径为空')
            return None
            
        logger.debug(f'获取字段值: path={path}, item={item}')
        keys = path.split('.')
        value = item
        for key in keys:
            if not isinstance(value, dict):
                logger.error(f'无效的字段路径: {path}, 当前值不是字典: {value}')
                return None
                
            # 检查键是否存在
            if key not in value:
                # 尝试直接从item中获取值
                if key in item:
                    logger.debug(f'从根级别获取字段值: {key}')
                    return item[key]
                logger.error(f'字段不存在: {key}, 在路径: {path}, 当前值: {value}')
                return None
                
            value = value[key]
            logger.debug(f'当前字段值: key={key}, value={value}')
            
        return value
    except Exception as e:
        logger.error(f'获取字段值失败: {path}, 错误: {str(e)}')
        return None

def format_datetime(dt_str, input_format=None):
    """
    将日期时间字符串转换为标准格式
    :param dt_str: 日期时间字符串
    :param input_format: 输入格式，如果为None则尝试自动解析
    :return: 标准格式的日期时间字符串 (YYYY-MM-DD HH:MM:SS)
    """
    from datetime import datetime
    import pytz
    from dateutil import parser

    try:
        if not dt_str:
            return None
            
        # 如果提供了输入格式，使用strptime解析
        if input_format:
            dt = datetime.strptime(dt_str, input_format)
        else:
            # 否则使用dateutil解析
            dt = parser.parse(dt_str)
            
        # 如果时区信息缺失，假定为UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
            
        # 转换为UTC时间
        dt = dt.astimezone(pytz.UTC)
        
        # 返回标准格式字符串
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f'日期时间格式化失败: {dt_str}, 错误: {str(e)}')
        return None 