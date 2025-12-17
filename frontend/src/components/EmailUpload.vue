<template>
  <el-card class="upload-card">
    <template #header>
      <div class="card-header">
        <span>邮件上传</span>
      </div>
    </template>
    
    <el-tabs v-model="activeTab">
      <el-tab-pane label="文件上传" name="file">
        <el-upload
          class="upload-dragger"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
          accept=".eml"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将邮件文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .eml 格式的邮件文件
            </div>
          </template>
        </el-upload>
        
        <el-button 
          type="primary" 
          @click="handleUpload"
          :loading="uploading"
          :disabled="!selectedFile"
          style="margin-top: 20px; width: 100%"
        >
          上传并检测
        </el-button>
      </el-tab-pane>
      
      <el-tab-pane label="文本输入" name="text">
        <el-input
          v-model="emailText"
          type="textarea"
          :rows="15"
          placeholder="请粘贴邮件原始文本..."
          style="margin-bottom: 20px"
        />
        
        <el-button 
          type="primary" 
          @click="handleTextUpload"
          :loading="uploading"
          :disabled="!emailText.trim()"
          style="width: 100%"
        >
          上传并检测
        </el-button>
      </el-tab-pane>
    </el-tabs>
    
    <el-alert
      v-if="uploadSuccess"
      title="上传成功"
      type="success"
      :description="`任务ID: ${jobId}`"
      show-icon
      :closable="false"
      style="margin-top: 20px"
    />
  </el-card>
</template>

<script>
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadEmail } from '../services/api'

export default {
  name: 'EmailUpload',
  components: {
    UploadFilled
  },
  emits: ['upload-success'],
  data() {
    return {
      activeTab: 'file',
      fileList: [],
      selectedFile: null,
      emailText: '',
      uploading: false,
      uploadSuccess: false,
      jobId: ''
    }
  },
  methods: {
    handleFileChange(file) {
      this.selectedFile = file.raw
    },
    
    async handleUpload() {
      if (!this.selectedFile) {
        this.$message.warning('请选择文件')
        return
      }
      
      this.uploading = true
      try {
        const response = await uploadEmail(this.selectedFile, null)
        this.jobId = response.job_id
        this.uploadSuccess = true
        this.$message.success('上传成功')
        this.$emit('upload-success', this.jobId)
      } catch (error) {
        this.$message.error('上传失败: ' + (error.message || '未知错误'))
      } finally {
        this.uploading = false
      }
    },
    
    async handleTextUpload() {
      if (!this.emailText.trim()) {
        this.$message.warning('请输入邮件文本')
        return
      }
      
      this.uploading = true
      try {
        const response = await uploadEmail(null, this.emailText)
        this.jobId = response.job_id
        this.uploadSuccess = true
        this.$message.success('上传成功')
        this.$emit('upload-success', this.jobId)
      } catch (error) {
        this.$message.error('上传失败: ' + (error.message || '未知错误'))
      } finally {
        this.uploading = false
      }
    }
  }
}
</script>

<style scoped>
.upload-card {
  margin-bottom: 20px;
}

.upload-dragger {
  width: 100%;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}
</style>

