# 服装展示提示词生成器

一个专为电商短视频创作者设计的桌面应用程序，帮助快速生成高转化率的服装展示拍摄脚本。

![应用界面](assets/screenshot.png)

## 项目架构

本项目采用模块化设计，分离业务逻辑与UI界面：
- **core.py**: 核心业务逻辑，处理动作库、模板替换等
- **gui.py**: CustomTkinter实现的GUI界面
- **main.py**: 程序入口点
- **assets/**: 静态资源文件（图标、截图等）

## 功能特点

- 🎨 **现代化UI**: 使用CustomTkinter打造美观、响应式的界面
- ⚡ **一键生成**: 单击按钮生成专业拍摄脚本
- 💾 **数据持久化**: 支持上传自定义动作库Excel文件
- ✏️ **完全自定义**: 自由编辑模板、选择氛围风格
- 📋 **便捷操作**: 一键复制到剪贴板或保存为文件
- 🔄 **灵活重生成**: 快速尝试不同动作组合

## 安装指南

### 前提条件
- Python 3.8 或更高版本
- pip 包管理工具

### 1. 克隆项目
```bash
git clone https://github.com/yourusername/fashion-prompt-generator.git
cd fashion-prompt-generator