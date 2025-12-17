<template>
  <el-card class="results-card" v-if="result">
    <template #header>
      <div class="card-header">
        <span>检测结果</span>
        <el-tag :type="getLabelType(result.label)" size="large">
          {{ getLabelText(result.label) }}
        </el-tag>
      </div>
    </template>
    
    <!-- 总体评分 -->
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="12">
        <el-statistic title="总体评分" :value="(result.overall_score * 100).toFixed(1)" suffix="%" />
      </el-col>
      <el-col :span="12">
        <el-statistic title="置信度" :value="(result.confidence * 100).toFixed(1)" suffix="%" />
      </el-col>
    </el-row>
    
    <!-- 评分进度条 -->
    <el-progress 
      :percentage="result.overall_score * 100" 
      :color="getProgressColor(result.overall_score)"
      :stroke-width="20"
      style="margin-bottom: 20px"
    />
    
    <!-- 检测详情 -->
    <el-collapse v-model="activeNames">
      <el-collapse-item title="LLM检测结果" name="llm">
        <div>
          <p><strong>判断:</strong> {{ getLabelText(result.llm_detection.label) }}</p>
          <p><strong>置信度:</strong> {{ (result.llm_detection.confidence * 100).toFixed(1) }}%</p>
          <p><strong>理由:</strong> {{ result.llm_detection.reasoning }}</p>
          <p><strong>提供商:</strong> {{ result.llm_detection.provider }}</p>
        </div>
      </el-collapse-item>
      
      <el-collapse-item title="规则引擎结果" name="rule">
        <div>
          <p><strong>评分:</strong> {{ (result.rule_engine.score * 100).toFixed(1) }}%</p>
          <p><strong>匹配规则:</strong></p>
          <ul>
            <li v-for="rule in result.rule_engine.matched_rules" :key="rule">{{ rule }}</li>
          </ul>
          <p><strong>SPF状态:</strong> {{ result.rule_engine.spf_status || '未检测' }}</p>
          <p><strong>DKIM状态:</strong> {{ result.rule_engine.dkim_status }}</p>
        </div>
      </el-collapse-item>
      
      <el-collapse-item title="RAG检索结果" name="rag" v-if="result.rag_result">
        <div>
          <p><strong>证据:</strong> {{ result.rag_result.evidence }}</p>
          <p v-if="result.rag_result.matched_templates.length > 0"><strong>匹配模板:</strong></p>
          <ul v-if="result.rag_result.matched_templates.length > 0">
            <li v-for="(template, index) in result.rag_result.matched_templates" :key="index">
              {{ template.name }} (相似度: {{ (result.rag_result.similarity_scores[index] * 100).toFixed(1) }}%)
            </li>
          </ul>
        </div>
      </el-collapse-item>
      
      <el-collapse-item title="多模态检测结果" name="multimodal" v-if="result.multimodal_result">
        <div>
          <p><strong>包含图像:</strong> {{ result.multimodal_result.has_images ? '是' : '否' }}</p>
          <div v-if="result.multimodal_result.image_analysis.length > 0">
            <p><strong>图像分析:</strong></p>
            <ul>
              <li v-for="(analysis, index) in result.multimodal_result.image_analysis" :key="index">
                {{ analysis.filename }}: {{ analysis.analysis }}
              </li>
            </ul>
          </div>
        </div>
      </el-collapse-item>
      
      <el-collapse-item title="特征信息" name="features">
        <div>
          <p><strong>文本特征:</strong></p>
          <ul>
            <li>长度: {{ result.features.text_features.length }}</li>
            <li>词数: {{ result.features.text_features.word_count }}</li>
            <li>URL数量: {{ result.features.text_features.url_count }}</li>
            <li>可疑短语: {{ result.features.text_features.suspicious_phrase_count }}</li>
          </ul>
        </div>
      </el-collapse-item>
    </el-collapse>
    
    <!-- 解释和建议 -->
    <el-alert
      :title="result.explanation"
      type="info"
      :closable="false"
      style="margin-top: 20px"
    />
    
    <el-card style="margin-top: 20px">
      <template #header>
        <span>建议操作</span>
      </template>
      <ul>
        <li v-for="(rec, index) in result.recommendations" :key="index">{{ rec }}</li>
      </ul>
    </el-card>
  </el-card>
  
  <el-empty v-else description="暂无检测结果" />
</template>

<script>
export default {
  name: 'DetectionResults',
  props: {
    result: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      activeNames: ['llm', 'rule']
    }
  },
  methods: {
    getLabelType(label) {
      const types = {
        'phishing': 'danger',
        'suspicious': 'warning',
        'benign': 'success'
      }
      return types[label] || 'info'
    },
    
    getLabelText(label) {
      const texts = {
        'phishing': '钓鱼邮件',
        'suspicious': '可疑邮件',
        'benign': '正常邮件'
      }
      return texts[label] || label
    },
    
    getProgressColor(score) {
      if (score >= 0.7) return '#f56c6c'
      if (score >= 0.4) return '#e6a23c'
      return '#67c23a'
    }
  }
}
</script>

<style scoped>
.results-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
}
</style>

