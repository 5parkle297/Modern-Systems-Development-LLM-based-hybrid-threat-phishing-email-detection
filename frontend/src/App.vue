<template>
  <div id="app">
    <el-container>
      <el-header>
        <h1>基于LLM的混合威胁钓鱼邮件检测系统</h1>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.el-header {
  background-color: #409EFF;
  color: white;
  text-align: center;
  line-height: 60px;
}

.el-header h1 {
  margin: 0;
  font-size: 24px;
}
</style>

