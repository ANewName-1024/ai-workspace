#!/usr/bin/env python3
"""
GitHub Skill 下载工具
安全地从 GitHub 下载并安装 OpenClaw skills
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path

WORKSPACE = os.getenv("OPENCLAW_WORKSPACE", "/root/.openclaw/workspace")
SKILLS_DIR = os.path.join(WORKSPACE, "skills")

def check_clawhub():
    """检查 clawhub 是否可用"""
    try:
        result = subprocess.run(
            ["clawhub", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def install_via_clawhub(slug: str) -> bool:
    """通过 clawhub 安装"""
    print(f"📦 通过 ClawHub 安装: {slug}")
    try:
        result = subprocess.run(
            ["clawhub", "install", slug],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f"✅ 安装成功: {slug}")
            return True
        else:
            print(f"❌ 安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def install_via_git(repo_url: str, skill_name: str = None) -> bool:
    """通过 git 安装"""
    # 解析 repo URL
    if repo_url.startswith("https://github.com/"):
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "")
        parts = repo_path.split("/")
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            skill_name = skill_name or repo.replace("-skill", "").replace("_skill", "")
    
    if not skill_name:
        print("❌ 无法解析 skill 名称")
        return False
    
    target_dir = os.path.join(SKILLS_DIR, skill_name)
    
    if os.path.exists(target_dir):
        print(f"⚠️ Skill 已存在: {skill_name}")
        return True
    
    print(f"📦 通过 GitHub 克隆: {repo_url}")
    try:
        result = subprocess.run(
            ["git", "clone", repo_url, target_dir],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f"✅ 克隆成功: {skill_name}")
            return True
        else:
            print(f"❌ 克隆失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def list_installed():
    """列出已安装的 skills"""
    if not os.path.exists(SKILLS_DIR):
        print("📁 没有已安装的 skills")
        return
    
    print(f"📁 Skills 目录: {SKILLS_DIR}\n")
    for item in os.listdir(SKILLS_DIR):
        item_path = os.path.join(SKILLS_DIR, item)
        if os.path.isdir(item_path) and item != "__pycache__":
            skill_file = os.path.join(item_path, "SKILL.md")
            if os.path.exists(skill_file):
                # 读取 skill 描述
                try:
                    with open(skill_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()[:5]
                        desc = ""
                        for line in lines:
                            if line.strip() and not line.startswith("#"):
                                desc = line.strip()[:60]
                                break
                        print(f"• {item}")
                        if desc:
                            print(f"  {desc}")
                except:
                    pass
    
    print(f"\n共 {len(os.listdir(SKILLS_DIR))} 个 skills")

def main():
    parser = argparse.ArgumentParser(description="GitHub Skill 下载工具")
    parser.add_argument("action", choices=["install", "list", "search"],
                       help="操作")
    parser.add_argument("target", nargs="?", help="Skill slug 或 GitHub URL")
    parser.add_argument("--name", help="自定义 skill 名称")
    
    args = parser.parse_args()
    
    os.makedirs(SKILLS_DIR, exist_ok=True)
    
    if args.action == "list":
        list_installed()
    
    elif args.action == "install":
        if not args.target:
            print("错误: 需要指定 skill")
            print("\n用法:")
            print("  # 通过 ClawHub 安装")
            print("  python github_skill.py install weather")
            print("")
            print("  # 通过 GitHub URL 安装")
            print("  python github_skill.py install https://github.com/owner/repo")
            return
        
        # 判断安装方式
        if args.target.startswith("http"):
            install_via_git(args.target, args.name)
        elif check_clawhub():
            install_via_clawhub(args.target)
        else:
            print("⚠️ ClawHub 不可用，请使用 GitHub URL")
            print(f"   python github_skill.py install {args.target} --name <skill-name>")
    
    elif args.action == "search":
        if check_clawhub():
            subprocess.run(["clawhub", "search", args.target or ""])
        else:
            print("请访问 https://clawhub.com 搜索 skills")

if __name__ == "__main__":
    main()
