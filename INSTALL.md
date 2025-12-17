# 安装指南

## 快速开始

### 1. 后端安装

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置环境变量

在 `backend` 目录下创建 `.env` 文件：

```env
OPENAI_API_KEY=your_key_here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
```

### 3. 启动后端

```bash
python run.py
```

后端将在 `http://localhost:8000` 运行

### 4. 前端安装

```bash
cd frontend
npm install
```

### 5. 启动前端

```bash
npm run dev
```

前端将在 `http://localhost:5173` 运行

## Windows快速启动

双击运行：
- `start_backend.bat` - 启动后端
- `start_frontend.bat` - 启动前端

## 注意事项

1. 确保已安装 Python 3.8+ 和 Node.js 16+
2. 需要配置LLM API密钥才能使用检测功能
3. 首次运行需要下载模型文件，可能需要一些时间

