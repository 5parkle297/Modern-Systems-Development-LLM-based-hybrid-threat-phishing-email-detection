# 基于LLM的混合威胁钓鱼邮件检测系统

## 项目简介

本项目整合了多个GitHub开源仓库，构建了一个完整的基于LLM（大语言模型）的混合威胁钓鱼邮件检测系统。系统能够检测传统钓鱼攻击、LLM生成的钓鱼攻击以及混合攻击链。

## 功能特性

### 核心功能

1. **邮件上传功能**
   - 支持.eml文件上传
   - 支持原始邮件文本输入
   - 自动解析邮件内容

2. **特征提取功能**
   - 文本特征提取（TF-IDF、embedding）
   - URL特征分析
   - Header特征提取
   - 统计特征计算

3. **恶意检测功能**
   - 规则引擎检测（URL黑名单、可疑短语、SPF/DKIM/DMARC验证）
   - LLM检测（支持OpenAI、Anthropic、Google Gemini）
   - RAG检索增强检测
   - 多模态检测（图像和网页分析）

4. **结果展示功能**
   - 检测结果可视化
   - 详细的特征分析
   - 解释性报告
   - 操作建议

## 技术架构

### 后端技术栈
- **FastAPI**: Python Web框架
- **LLM API**: OpenAI / Anthropic / Google Gemini
- **特征提取**: SentenceTransformers, scikit-learn
- **RAG**: LangChain, FAISS
- **邮件解析**: email, mailparser

### 前端技术栈
- **Vue.js 3**: 前端框架
- **Element Plus**: UI组件库
- **Vite**: 构建工具
- **Axios**: HTTP客户端

## 项目结构

```
Pnishing/
├── repositories/              # 克隆的原始仓库
│   ├── llm-email-spam-detection/
│   ├── Email-phishing-detection/
│   ├── Phishing-Detection-System-with-RAG-and-LLM-Integration/
│   ├── sample-fine-tuned-llama-phishing-classifier/
│   ├── Multimodal_LLM_Phishing_Detection/
│   └── PhishLLM/
├── backend/                   # FastAPI后端
│   ├── app/
│   │   ├── api/              # API路由
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务逻辑
│   │   └── main.py          # 应用入口
│   ├── requirements.txt
│   └── config.py
├── frontend/                  # Vue.js前端
│   ├── src/
│   │   ├── components/       # 组件
│   │   ├── views/           # 视图
│   │   └── services/        # API服务
│   └── package.json
└── data/                      # 数据存储
    ├── emails/               # 上传的邮件
    ├── models/               # 模型文件
    └── knowledge_base/       # RAG知识库
```

## 安装和运行

### 环境要求

- Python 3.8+
- Node.js 16+
- LLM API密钥（OpenAI/Anthropic/Google）

### 后端安装

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
创建 `.env` 文件：
```env
OPENAI_API_KEY=your_openai_api_key
# 或
ANTHROPIC_API_KEY=your_anthropic_api_key
# 或
GOOGLE_API_KEY=your_google_api_key

LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
```

5. 启动后端服务
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 前端安装

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 启动开发服务器
```bash
npm run dev
```

4. 访问应用
打开浏览器访问 `http://localhost:5173`

## 使用说明

### 1. 上传邮件

- **方式一**: 上传.eml文件
  - 点击"文件上传"标签
  - 拖拽或选择.eml文件
  - 点击"上传并检测"

- **方式二**: 输入邮件文本
  - 点击"文本输入"标签
  - 粘贴邮件原始文本
  - 点击"上传并检测"

### 2. 执行检测

上传成功后，点击"开始检测"按钮，系统将：
1. 解析邮件内容
2. 提取特征
3. 执行多模块检测
4. 融合结果并生成报告

### 3. 查看结果

检测完成后，可以查看：
- 总体评分和置信度
- LLM检测结果和理由
- 规则引擎匹配的规则
- RAG检索到的相似模板
- 多模态检测结果（如果有）
- 操作建议

## API文档

启动后端服务后，访问 `http://localhost:8000/docs` 查看完整的API文档。

### 主要API端点

- `POST /api/v1/upload/` - 上传邮件
- `POST /api/v1/detect/{job_id}` - 执行检测
- `GET /api/v1/detect/{job_id}` - 获取检测结果
- `GET /api/v1/results/` - 获取检测历史

## 参考仓库

本项目整合了以下开源仓库的代码和思路：

1. **jpmorganchase/llm-email-spam-detection**
   - 文本embedding和特征提取方法

2. **CCiprian1/Email-phishing-detection**
   - Llama模型集成和混合检测方案

3. **CnRagnor/Phishing-Detection-System-with-RAG-and-LLM-Integration**
   - RAG检索增强生成实现

4. **aws-samples/sample-fine-tuned-llama-phishing-classifier**
   - 模型微调和推理代码

5. **JehLeeKR/Multimodal_LLM_Phishing_Detection**
   - 多模态LLM检测方法

6. **code-philia/PhishLLM**
   - 视觉语言模型检测框架

## 注意事项

1. **API密钥安全**: 请妥善保管LLM API密钥，不要提交到代码仓库
2. **数据隐私**: 上传的邮件数据仅用于检测，不会泄露给第三方
3. **检测准确性**: 系统检测结果仅供参考，重要决策请结合人工判断
4. **资源消耗**: LLM API调用会产生费用，请注意控制使用量

## 许可证

本项目整合了多个开源仓库，请参考各仓库的LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请通过GitHub Issues联系。

