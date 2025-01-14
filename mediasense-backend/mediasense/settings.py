# OpenAI配置
OPENAI_API_KEY = env("OPENAI_API_KEY")
OPENAI_API_BASE = env("OPENAI_API_BASE", default="https://api.openai-proxy.com/v1")
OPENAI_MODEL = env("OPENAI_MODEL", default="gpt-4")
OPENAI_TEMPERATURE = float(env("OPENAI_TEMPERATURE", default=0.2))
OPENAI_MAX_TOKENS = int(env("OPENAI_MAX_TOKENS", default=2000))

# AI服务配置
AUTO_ANALYZE_NEWS = env.bool("AUTO_ANALYZE_NEWS", default=True)
GENERATE_SUMMARY = env.bool("GENERATE_SUMMARY", default=True)
