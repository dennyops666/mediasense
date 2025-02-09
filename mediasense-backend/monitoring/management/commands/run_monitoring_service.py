from django.core.management.base import BaseCommand
from monitoring.services import MonitoringService
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '运行监控服务，定期收集系统指标'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='收集指标的时间间隔（秒）'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        self.stdout.write(f'启动监控服务，收集间隔：{interval}秒')
        
        try:
            while True:
                try:
                    # 收集系统指标
                    MonitoringService.collect_system_metrics()
                    self.stdout.write('系统指标收集完成')
                    
                    # 检查告警规则
                    alerts = MonitoringService.check_alerts()
                    if alerts:
                        self.stdout.write(f'检测到{len(alerts)}个告警：')
                        for alert in alerts:
                            self.stdout.write(f"- {alert['rule_name']}: {alert['metric_type']} = {alert['current_value']}")
                    
                    # 等待下一次收集
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f'监控服务执行出错：{str(e)}')
                    time.sleep(5)  # 出错后等待5秒再重试
        except KeyboardInterrupt:
            self.stdout.write('监控服务已停止') 