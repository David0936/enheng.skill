#!/usr/bin/env python3
"""
version_manager.py — 版本存档与回滚

功能：
- 每次更新自动创建版本快照
- 支持查看历史版本列表
- 支持回滚到指定版本
- 自动清理旧版本（保留最近 N 个）

作者: David小鱼
X: @shark1996_
"""

import os
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('enheng-version')


class VersionManager:
    """版本管理器"""

    def __init__(self, slug: str, base_dir: str = "selves", versions_dir: str = "versions"):
        self.slug = slug
        self.base_dir = Path(base_dir) / slug
        self.versions_dir = Path(versions_dir) / slug
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def _get_current_version(self) -> str:
        """获取当前版本号"""
        config_file = self.base_dir / 'config.json'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('version', '1.0.0')
        return '1.0.0'

    def _bump_version(self, current: str, bump_type: str = 'patch') -> str:
        """版本号递增"""
        parts = current.split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if bump_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif bump_type == 'minor':
            minor += 1
            patch = 0
        else:
            patch += 1

        return f"{major}.{minor}.{patch}"

    def create_snapshot(self, bump_type: str = 'patch') -> str:
        """创建版本快照"""
        current_version = self._get_current_version()
        new_version = self._bump_version(current_version, bump_type)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version_name = f"v{new_version}_{timestamp}"
        version_dir = self.versions_dir / version_name
        version_dir.mkdir(exist_ok=True)

        # 复制当前文件到版本目录
        files_to_backup = ['self.md', 'persona.md', 'corrections.md', 'config.json']

        for filename in files_to_backup:
            src = self.base_dir / filename
            if src.exists():
                shutil.copy2(src, version_dir / filename)

        # 创建版本元数据
        metadata = {
            'version': new_version,
            'timestamp': timestamp,
            'created_at': datetime.now().isoformat(),
            'files_backed_up': files_to_backup,
            'previous_version': current_version
        }

        with open(version_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 更新当前版本号
        config_file = self.base_dir / 'config.json'
        config = {}
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

        config['version'] = new_version
        config['last_snapshot'] = version_name

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"创建版本快照: {version_name}")
        return version_name

    def list_versions(self) -> List[Dict]:
        """列出所有历史版本"""
        versions = []

        if not self.versions_dir.exists():
            return versions

        for version_dir in sorted(self.versions_dir.iterdir(), reverse=True):
            if version_dir.is_dir():
                metadata_file = version_dir / 'metadata.json'
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        metadata['version_name'] = version_dir.name
                        versions.append(metadata)

        return versions

    def rollback(self, version_name: str) -> bool:
        """回滚到指定版本"""
        version_dir = self.versions_dir / version_name
        if not version_dir.exists():
            logger.error(f"版本不存在: {version_name}")
            return False

        # 先创建当前状态的快照（防止丢失）
        emergency_snapshot = self.create_snapshot(bump_type='patch')
        logger.info(f"紧急快照: {emergency_snapshot}")

        # 回滚文件
        files_to_restore = ['self.md', 'persona.md', 'corrections.md']

        for filename in files_to_restore:
            src = version_dir / filename
            dst = self.base_dir / filename
            if src.exists():
                shutil.copy2(src, dst)
                logger.info(f"恢复: {filename}")

        # 读取版本元数据
        metadata_file = version_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 更新当前版本号
            config_file = self.base_dir / 'config.json'
            config = {}
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            config['version'] = metadata.get('version', 'unknown')
            config['rolled_back_from'] = emergency_snapshot
            config['rolled_back_to'] = version_name

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"回滚完成: {version_name}")
        return True

    def cleanup_old_versions(self, keep: int = 10):
        """清理旧版本，保留最近 N 个"""
        versions = self.list_versions()

        if len(versions) <= keep:
            logger.info(f"版本数 {len(versions)} <= 保留数 {keep}，无需清理")
            return

        versions_to_remove = versions[keep:]

        for version in versions_to_remove:
            version_dir = self.versions_dir / version['version_name']
            if version_dir.exists():
                shutil.rmtree(version_dir)
                logger.info(f"清理旧版本: {version['version_name']}")

        logger.info(f"清理完成，保留最近 {keep} 个版本")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='版本存档与回滚工具')
    parser.add_argument('--slug', default='enheng', help='数字副本代号')
    parser.add_argument('--snapshot', action='store_true', help='创建版本快照')
    parser.add_argument('--list', action='store_true', help='列出历史版本')
    parser.add_argument('--rollback', help='回滚到指定版本')
    parser.add_argument('--cleanup', type=int, help='清理旧版本，保留 N 个')

    args = parser.parse_args()

    manager = VersionManager(args.slug)

    if args.snapshot:
        version = manager.create_snapshot()
        print(f"✅ 快照创建: {version}")

    elif args.list:
        versions = manager.list_versions()
        print(f"\n📋 历史版本 ({len(versions)} 个):")
        for v in versions:
            print(f"   {v['version_name']} | v{v['version']} | {v['created_at']}")

    elif args.rollback:
        success = manager.rollback(args.rollback)
        if success:
            print(f"✅ 回滚完成: {args.rollback}")
        else:
            print(f"❌ 回滚失败")

    elif args.cleanup:
        manager.cleanup_old_versions(keep=args.cleanup)
        print(f"✅ 清理完成，保留最近 {args.cleanup} 个版本")

    else:
        print("用法:")
        print("   python version_manager.py --snapshot")
        print("   python version_manager.py --list")
        print("   python version_manager.py --rollback v1.0.1_20250423_143000")
        print("   python version_manager.py --cleanup 10")


if __name__ == '__main__':
    main()
