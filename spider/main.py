"""
AI技术文章爬虫主程序
"""
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

from spiders.csdn.csdn_spider import CSDNSpider
from spiders.juejin.juejin_spider import JuejinSpider
from utils import logger, sqlite_storage
from config.settings import WEBSITES


class SpiderManager:
    """爬虫管理器"""

    def __init__(self):
        self.spiders = {
            'csdn': CSDNSpider(),
            'juejin': JuejinSpider()
        }

    async def crawl_site(self, site_name: str, keywords: list = None, max_pages: int = 3):
        """爬取指定网站"""
        if site_name not in self.spiders:
            logger.error(f"不支持的网站: {site_name}")
            return 0

        spider = self.spiders[site_name]
        config = WEBSITES.get(site_name, {})

        if not config.get('enabled', True):
            logger.info(f"网站 {site_name} 已禁用")
            return 0

        logger.info(f"开始爬取 {config['name']}...")

        try:
            if hasattr(spider, 'crawl_articles'):
                if asyncio.iscoroutinefunction(spider.crawl_articles):
                    count = await spider.crawl_articles(keywords, max_pages)
                else:
                    count = spider.crawl_articles(keywords, max_pages)
            else:
                logger.error(f"爬虫 {site_name} 没有crawl_articles方法")
                return 0

            logger.info(f"{config['name']} 爬取完成，共 {count} 篇文章")
            return count

        except Exception as e:
            logger.error(f"爬取 {site_name} 失败: {e}")
            return 0

    async def crawl_all_sites(self, keywords: list = None, max_pages: int = 3):
        """爬取所有启用的网站"""
        total_count = 0
        enabled_sites = [name for name, config in WEBSITES.items() if config.get('enabled', True)]

        logger.info(f"开始爬取所有网站，共 {len(enabled_sites)} 个站点")

        for site_name in enabled_sites:
            try:
                count = await self.crawl_site(site_name, keywords, max_pages)
                total_count += count

                # 站点间延迟
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"爬取 {site_name} 时出错: {e}")
                continue

        logger.info(f"所有网站爬取完成，总共 {total_count} 篇文章")
        return total_count

    def show_statistics(self):
        """显示统计信息"""
        print("\n" + "="*50)
        print("爬虫统计信息")
        print("="*50)

        # 总文章数
        total_articles = sqlite_storage.get_article_count()
        print(f"总文章数: {total_articles}")

        # 各网站文章数
        for site_name, config in WEBSITES.items():
            if config.get('enabled', True):
                count = sqlite_storage.get_article_count(site_name)
                print(f"{config['name']}: {count} 篇")

        print("="*50)

    def export_data(self, format_type: str = 'json', source: str = None):
        """导出数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type.lower() == 'json':
            filename = f"articles_{source or 'all'}_{timestamp}.json"
            filepath = Path("data/processed") / filename
            sqlite_storage.export_to_json(filepath, source)
        elif format_type.lower() == 'csv':
            filename = f"articles_{source or 'all'}_{timestamp}.csv"
            filepath = Path("data/processed") / filename
            sqlite_storage.export_to_csv(filepath, source)
        else:
            logger.error(f"不支持的格式: {format_type}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI技术文章爬虫')
    parser.add_argument('--site', '-s', choices=['csdn', 'juejin', 'all'], default='all',
                        help='指定爬取的网站 (默认: all)')
    parser.add_argument('--keywords', '-k', nargs='+',
                        default=['人工智能', '机器学习', 'GPT', '深度学习'],
                        help='搜索关键词 (默认: AI相关)')
    parser.add_argument('--pages', '-p', type=int, default=3,
                        help='每个关键词爬取页数 (默认: 3)')
    parser.add_argument('--export', '-e', choices=['json', 'csv'],
                        help='导出数据格式')
    parser.add_argument('--stats', action='store_true',
                        help='显示统计信息')

    args = parser.parse_args()

    # 创建管理器
    manager = SpiderManager()

    try:
        if args.stats:
            manager.show_statistics()
            return

        # 开始爬取
        start_time = datetime.now()
        logger.info(f"爬虫任务开始: {start_time}")

        if args.site == 'all':
            total_count = await manager.crawl_all_sites(args.keywords, args.pages)
        else:
            total_count = await manager.crawl_site(args.site, args.keywords, args.pages)

        end_time = datetime.now()
        duration = end_time - start_time

        logger.info(f"爬虫任务完成！")
        logger.info(f"耗时: {duration}")
        logger.info(f"获取文章: {total_count} 篇")

        # 显示统计信息
        manager.show_statistics()

        # 导出数据
        if args.export:
            manager.export_data(args.export, args.site if args.site != 'all' else None)

    except KeyboardInterrupt:
        logger.info("用户中断爬虫任务")
    except Exception as e:
        logger.error(f"爬虫任务出错: {e}")
    finally:
        # 清理资源
        from utils import playwright_handler
        if playwright_handler.browser:
            await playwright_handler.close_browser()


if __name__ == "__main__":
    asyncio.run(main())