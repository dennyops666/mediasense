#!/bin/bash

curl -v -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM4Mzg3MDM5LCJpYXQiOjE3MzgzODY3MzksImp0aSI6IjIyYzA5ZmYyOTdiMzQ1MjViNTk4YmVkNWU3ODFjOWMyIiwidXNlcl9pZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsImVtYWlsIjoiYWRtaW5AZXhhbXBsZS5jb20iLCJpc19zdGFmZiI6dHJ1ZX0.uUVUW0J4qlWAtA87s8M2OQenaikz-X4z1OkrEBysFgY" \
  -d '[{
    "name": "科学网新闻",
    "description": "科学网科技新闻RSS源",
    "source_url": "http://www.sciencenet.cn/xml/news.aspx?di=0",
    "crawler_type": 1,
    "config_data": {
      "title_path": "title",
      "content_path": "description",
      "link_path": "link",
      "pub_date_path": "pubDate"
    },
    "headers": {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    },
    "interval": 3600,
    "max_retries": 3,
    "retry_delay": 300,
    "status": 1,
    "is_active": true
  }]' \
  http://localhost:8000/api/crawler/configs/bulk-create/ 