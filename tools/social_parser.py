#!/usr/bin/env python3
"""
social_parser.py — 社交媒体内容解析器

支持：
- 推特/X 推文解析（文本清洗、链接提取、媒体识别）
- TG频道消息解析
- 聊天记录解析（WeChatMsg / 留痕 / PyWxDump 格式）
- PDF/文档解析（预留接口）

作者: David小鱼
X: @shark1996_
"""

import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('enheng-parser')


class TweetParser:
    """推文解析器"""

    @staticmethod
    def clean_text(text: str) -> str:
        """清洗推文文本"""
        # 移除 t.co 短链接
        text = re.sub(r'https?://t\.co/\w+', '', text)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """提取 @提及"""
        return re.findall(r'@(\w+)', text)

    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """提取 #话题"""
        return re.findall(r'#(\w+)', text)

    @staticmethod
    def extract_tickers(text: str) -> List[str]:
        """提取 $代币符号"""
        return re.findall(r'\$([A-Za-z0-9]+)', text)

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """提取 URL"""
        return re.findall(r'https?://[^\s]+', text)

    @staticmethod
    def is_trade_related(text: str) -> bool:
        """判断是否与交易相关"""
        trade_keywords = [
            '交易', '买入', '卖出', '持仓', '仓位', '止盈', '止损',
            'BTC', 'ETH', 'BNB', '现货', '合约', '杠杆', '挖矿',
            'DeFi', 'Meme', '土狗', '空投', '质押', '流动性',
            'trade', 'buy', 'sell', 'hold', 'position', 'profit',
            'loss', 'stop', 'leverage', 'spot', 'futures'
        ]
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in trade_keywords)

    @staticmethod
    def is_emotional(text: str) -> Tuple[bool, str]:
        """判断情绪倾向"""
        positive = ['赚', '涨', '突破', '看好', '信仰', '收获', '赢', '利好']
        negative = ['亏', '跌', '砸盘', '恐慌', '焦虑', '害怕', '失望', '利空']
        excited = ['冲', '梭哈', 'All in', 'FOMO', '爆发', '火箭']
        calm = ['冷静', '稳健', '耐心', '等待', '观望', '拿住']

        text_lower = text.lower()
        scores = {
            'positive': sum(1 for w in positive if w in text_lower),
            'negative': sum(1 for w in negative if w in text_lower),
            'excited': sum(1 for w in excited if w in text_lower),
            'calm': sum(1 for w in calm if w in text_lower)
        }

        if scores['excited'] > 0:
            return True, 'excited'
        elif scores['calm'] > 0:
            return True, 'calm'
        elif scores['positive'] > scores['negative']:
            return True, 'positive'
        elif scores['negative'] > scores['positive']:
            return True, 'negative'

        return False, 'neutral'

    @classmethod
    def parse_tweet(cls, tweet: Dict) -> Dict:
        """完整解析单条推文"""
        text = tweet.get('text', '')
        cleaned = cls.clean_text(text)

        return {
            'id': tweet.get('id'),
            'raw_text': text,
            'cleaned_text': cleaned,
            'mentions': cls.extract_mentions(text),
            'hashtags': cls.extract_hashtags(text),
            'tickers': cls.extract_tickers(text),
            'urls': cls.extract_urls(text),
            'is_trade_related': cls.is_trade_related(text),
            'emotional': cls.is_emotional(text),
            'created_at': tweet.get('created_at'),
            'public_metrics': tweet.get('public_metrics', {}),
            'source': tweet.get('source', 'unknown')
        }


class ChatParser:
    """聊天记录解析器"""

    @staticmethod
    def parse_wechat_export(file_path: str) -> List[Dict]:
        """解析微信聊天记录导出文件"""
        # 支持 WeChatMsg / 留痕 / PyWxDump 格式
        # 实际实现需要适配具体导出格式
        logger.info(f"解析微信聊天记录: {file_path}")
        return []

    @staticmethod
    def parse_telegram_export(file_path: str) -> List[Dict]:
        """解析 TG 导出文件"""
        logger.info(f"解析 Telegram 记录: {file_path}")
        return []


class PDFParser:
    """PDF 解析器（预留接口）"""

    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """解析 PDF 为文本"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() + '\n'
                return text
        except ImportError:
            logger.warning("PyPDF2 未安装，无法解析 PDF")
            return ''
        except Exception as e:
            logger.error(f"PDF 解析失败: {e}")
            return ''


def parse_raw_file(input_path: str) -> List[Dict]:
    """通用解析入口"""
    input_file = Path(input_path)

    if not input_file.exists():
        logger.error(f"文件不存在: {input_path}")
        return []

    # 根据文件类型选择解析器
    suffix = input_file.suffix.lower()

    if suffix == '.json':
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tweets = data.get('tweets', [])
        parser = TweetParser()
        return [parser.parse_tweet(t) for t in tweets]

    elif suffix == '.pdf':
        parser = PDFParser()
        text = parser.parse_pdf(str(input_file))
        return [{'type': 'pdf', 'content': text}]

    elif suffix in ['.txt', '.md']:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        return [{'type': 'text', 'content': text}]

    else:
        logger.warning(f"不支持的文件类型: {suffix}")
        return []


def save_parsed(parsed_data: List[Dict], output_path: str):
    """保存解析结果"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)
    logger.info(f"解析结果已保存: {output_path}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='社交媒体内容解析器')
    parser.add_argument('--input', required=True, help='输入文件路径')
    parser.add_argument('--output', help='输出文件路径')

    args = parser.parse_args()

    results = parse_raw_file(args.input)

    if args.output:
        save_parsed(results, args.output)
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))
