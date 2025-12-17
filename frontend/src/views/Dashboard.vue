<template>
  <div class="dashboard">
    <EmailUpload @upload-success="handleUploadSuccess" />
    
    <el-button 
      v-if="currentJobId"
      type="primary" 
      @click="startDetection"
      :loading="detecting"
      style="margin-bottom: 20px; width: 100%"
    >
      开始检测
    </el-button>
    
    <DetectionResults v-if="detectionResult" :result="detectionResult" />
    
    <el-card v-if="history.length > 0" style="margin-top: 20px">
      <template #header>
        <span>检测历史</span>
      </template>
      <el-table :data="history" style="width: 100%">
        <el-table-column prop="job_id" label="任务ID" width="250" />
        <el-table-column prop="label" label="结果">
          <template #default="scope">
            <el-tag :type="getLabelType(scope.row.label)">
              {{ getLabelText(scope.row.label) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="评分">
          <template #default="scope">
            {{ (scope.row.score * 100).toFixed(1) }}%
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间" />
      </el-table>
    </el-card>
  </div>
</template>

<script>
import EmailUpload from '../components/EmailUpload.vue'
import DetectionResults from '../components/DetectionResults.vue'
import { detectEmail, getAllResults } from '../services/api'

export default {
  name: 'Dashboard',
  components: {
    EmailUpload,
    DetectionResults
  },
  data() {
    return {
      currentJobId: '',
      detecting: false,
      detectionResult: null,
      history: []
    }
  },
  mounted() {
    this.loadHistory()
  },
  methods: {
    handleUploadSuccess(jobId) {
      this.currentJobId = jobId
    },
    
    async startDetection() {
      if (!this.currentJobId) {
        this.$message.warning('请先上传邮件')
        return
      }
      
      this.detecting = true
      try {
        this.detectionResult = await detectEmail(this.currentJobId)
        this.$message.success('检测完成')
        this.loadHistory()
      } catch (error) {
        this.$message.error('检测失败: ' + (error.message || '未知错误'))
      } finally {
        this.detecting = false
      }
    },
    
    async loadHistory() {
      try {
        const response = await getAllResults(10, 0)
        this.history = response.items
      } catch (error) {
        console.error('加载历史失败:', error)
      }
    },
    
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
    }
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
</style>

