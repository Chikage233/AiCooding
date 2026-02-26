# api/management/commands/simple_scrape.py
import json
from django.core.management.base import BaseCommand
from simple_scraper import run_simple_scraper

class Command(BaseCommand):
    help = '简化版爬取LeetCode题目（只获取基础信息）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=200,
            help='爬取题目数量限制 (默认: 200)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write(
            self.style.SUCCESS(f'开始简化版爬取LeetCode题目，数量限制: {limit}')
        )

        try:
            result = run_simple_scraper(limit=limit)

            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(result['message'])
                )
                self.stdout.write(
                    f"总共处理: {result['total']} 道题目"
                )
                self.stdout.write(
                    f"成功保存: {result['success_count']} 道题目"
                )
                self.stdout.write(
                    f"失败数量: {result['fail_count']} 道题目"
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"爬取失败: {result['message']}")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'执行过程中发生错误: {str(e)}')
            )