#!/bin/bash

# 首先获取新的访问令牌
echo "获取访问令牌..."
TOKEN_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin@123456"}' \
  http://localhost:8000/api/auth/token/)

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access":"[^"]*' | cut -d'"' -f4)

echo "开始测试所有数据源..."

# 获取所有爬虫配置的ID
echo "获取爬虫配置列表..."
CONFIGS=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  http://localhost:8000/api/crawler/configs)

# 解析配置ID并测试每个数据源
echo $CONFIGS | grep -o '"id":[0-9]*' | cut -d':' -f2 | while read -r id; do
  echo "测试配置 ID: $id"
  curl -v -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    http://localhost:8000/api/crawler/configs/$id/test/
  echo -e "\n"
  # 等待5秒再测试下一个，避免请求过于频繁
  sleep 5
done

echo "测试完成!" 