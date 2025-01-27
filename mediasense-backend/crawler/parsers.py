def _parse_api(self, response_data):
    """
    解析API响应数据
    :param response_data: API响应数据
    :return: 解析后的新闻列表
    """
    try:
        logger.debug(f'开始解析API响应数据: {response_data}')
        data_path = self.config.config_data.get('data_path')
        if not data_path:
            logger.error('无效的数据路径配置')
            return []

        # 获取新闻列表数据
        news_list = self._get_field_value(response_data, data_path)
        if not news_list:
            logger.error(f'无效的数据路径: {data_path}, 当前值: {response_data}')
            return []

        if not isinstance(news_list, list):
            logger.error(f'数据格式错误，期望列表类型，当前类型: {type(news_list)}')
            return []

        parsed_items = []
        for item in news_list:
            logger.debug(f'开始解析新闻项: {item}')
            
            # 获取必要字段
            title = self._get_field_value(item, self.config.config_data.get('title_path', ''))
            url = self._get_field_value(item, self.config.config_data.get('link_path', ''))
            author = self._get_field_value(item, self.config.config_data.get('author_path', ''))
            source = self._get_field_value(item, self.config.config_data.get('source_path', ''))
            pub_date = self._get_field_value(item, self.config.config_data.get('pub_date_path', ''))
            
            logger.debug(f'字段解析结果: title={title}, url={url}, author={author}, source={source}, pub_date={pub_date}')
            logger.debug(f'配置路径: title_path={self.config.config_data.get("title_path")}, link_path={self.config.config_data.get("link_path")}, author_path={self.config.config_data.get("author_path")}, source_path={self.config.config_data.get("source_path")}, pub_date_path={self.config.config_data.get("pub_date_path")}')

            # 获取新闻详情
            content = ''
            description = ''
            if url:
                content, description = self._get_news_details(url)
                logger.debug(f'新闻详情: content长度={len(content)}, description长度={len(description)}')

            # 构造新闻数据
            news_data = {
                'title': title,
                'url': url,
                'author': author,
                'source': source,
                'content': content,
                'description': description,
                'pub_date': pub_date,
                'crawler': self.config
            }
            logger.debug(f'构造的新闻数据: {news_data}')
            parsed_items.append(news_data)

        return parsed_items
    except Exception as e:
        logger.error(f'解析API数据时发生错误: {str(e)}')
        return [] 