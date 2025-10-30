# 快速开始指南

## 前置准备

### 1. 检查输入项目

确保输入项目存在：
```bash
ls input/01-Primary
```

### 2. 配置 API 密钥

创建 `.env` 文件（如果还没有）：
```bash
cd cstarx
cat > .env << EOF
CSTARX_MODEL_PROVIDER=openai
CSTARX_MODEL_NAME=deepseek-chat
CSTARX_API_KEY=sk-d1c3ee0a9f304a368e15a67eae7db1c2
CSTARX_BASE_URL=https://api.deepseek.com
CSTARX_TEMPERATURE=0.7
CSTARX_TOP_P=0.9
CSTARX_MAX_TOKENS=8192
CSTARX_OUTPUT_DIR=output
CSTARX_RETRY_ATTEMPTS=3
EOF
```

### 3. 安装依赖（如果需要）

```bash
pip install -r requirements.txt
# 或者
pip install loguru typer rich pydantic openai python-dotenv
```

## 开始翻译

### 方法 1：使用 CLI 命令（推荐）

```bash
# 基本翻译命令
python -m src.cli translate input/01-Primary

# 指定输出目录
python -m src.cli translate input/01-Primary --output output/01-Primary

# 查看详细信息（verbose模式）
python -m src.cli translate input/01-Primary --verbose
```

### 方法 2：使用 Python 代码

```python
import asyncio
from src.core.translator import Translator
from src.models.config import Config

async def main():
    # 加载配置
    config = Config.from_env()
    
    # 创建翻译器
    translator = Translator(config)
    
    try:
        # 开始翻译
        project = await translator.translate_project(
            'input/01-Primary',
            output_path='output/01-Primary'
        )
        
        print(f"翻译完成：{project.translated_files}/{project.total_files} 文件")
    finally:
        await translator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## 查看翻译进度

### 在另一个终端查看实时进度

```bash
# 查看所有项目摘要
python -m src.cli status --all

# 查看特定项目的详细信息
python -m src.cli status --name "01-Primary"

# 使用项目ID查看
python -m src.cli status --id "project-uuid"
```

### 直接使用进度查看工具

```bash
# 查看所有项目
python -m src.utils.progress_viewer --all

# 查看特定项目
python -m src.utils.progress_viewer "01-Primary"
```

## 翻译流程说明

### 阶段 1：项目分析
- 扫描项目文件
- 分析依赖关系
- 创建依赖图
- 确定翻译顺序

### 阶段 2：翻译执行
- 并行翻译多个文件（默认 5 个并发）
- 每个文件会：
  1. 分析复杂度
  2. 选择合适的翻译策略
  3. 使用 LLM 进行翻译
  4. 进行质量检查
  5. 保存翻译结果

### 阶段 3：结果生成
- 生成 Rust 文件到输出目录
- 保持原始目录结构
- 自动生成 `Cargo.toml`
- 保存状态到 `output/state/`

## 输出结果

翻译完成后，结果会在以下位置：

```
output/
├── 01-Primary/              # 翻译后的 Rust 项目
│   ├── src/
│   │   ├── arraylist.rs     # 翻译后的文件
│   │   └── ...
│   ├── Cargo.toml           # 自动生成的 Cargo 配置
│   └── .gitignore
└── state/
    └── project_{id}.json    # 项目状态文件（包含所有详细信息）
```

## 常见问题

### Q: 翻译速度很慢怎么办？

A: 
1. 检查 API 是否正常：确保 API 密钥正确，网络连接正常
2. 调整并发数：在 `.env` 中设置 `CSTARX_MAX_PARALLEL_WORKERS=10`（默认是 5）
3. 查看日志：使用 `--verbose` 查看详细日志

### Q: 翻译中断了怎么办？

A: 
状态会自动保存到 `output/state/`，可以：
1. 重新运行相同的翻译命令，系统会尝试恢复
2. 或者使用 `resume` 命令：
   ```bash
   python -m src.cli resume input/01-Primary
   ```

### Q: 如何查看翻译日志？

A:
```bash
# 使用 verbose 模式
python -m src.cli translate input/01-Primary --verbose

# 日志会显示：
# - 每个文件的翻译状态
# - API 调用情况
# - 错误信息
```

### Q: 翻译失败了怎么办？

A:
1. 检查 `.env` 配置是否正确
2. 检查 API 密钥是否有效
3. 查看错误日志
4. 检查输入项目是否有语法错误

### Q: 如何修改翻译策略？

A:
编辑 `.env` 文件：
```bash
# 调整温度参数（0.0-2.0）
CSTARX_TEMPERATURE=0.7

# 调整重试次数
CSTARX_RETRY_ATTEMPTS=3

# 调整并发数
CSTARX_MAX_PARALLEL_WORKERS=5
```

## 完整的示例命令

```bash
# 1. 进入项目目录
cd cstarx

# 2. 确保配置正确
cat .env

# 3. 开始翻译
python -m src.cli translate input/01-Primary --output output/01-Primary --verbose

# 4. 在另一个终端查看进度（可以多次运行）
python -m src.cli status --name "01-Primary"

# 5. 翻译完成后检查结果
ls -lh output/01-Primary/
cat output/01-Primary/Cargo.toml
```

## 下一步

- 查看 `PROGRESS_VIEWING.md` 了解如何查看详细进度
- 查看 `STATE_DIRECTORY.md` 了解状态文件的作用
- 查看 `COMPARISON.md` 了解 CStarX 的优势

