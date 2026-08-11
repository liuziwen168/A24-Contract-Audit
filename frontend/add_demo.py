import re

with open(r'D:\front\src\views\login\LoginView.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# Add demo button before closing </el-form>
demo_btn = '''
          <el-form-item class="submit-item" style="margin-top:12px">
            <el-button class="demo-btn" @click="handleDemoLogin">
              演示模式（跳过登录）
            </el-button>
          </el-form-item>'''

content = content.replace('</el-form>', demo_btn + '\n        </el-form>')

# Add demo style
demo_style = '''
.demo-btn {
  width: 100%;
  height: 40px;
  font-size: 14px;
  color: #1a6fc4;
  border: 1px dashed #1a6fc4;
  background: #fff;
  letter-spacing: 2px;
}
.demo-btn:hover {
  background: #ecf5ff;
}'''

content = content.replace('</style>', demo_style + '\n</style>')

# Add demo function
demo_func = '''
function handleDemoLogin() {
  localStorage.setItem('accessToken', 'demo-token')
  localStorage.setItem('userInfo', JSON.stringify({username:'张经理', role:'user'}))
  router.push('/user/contracts')
}'''

content = content.replace('async function handleLogin() {', demo_func + '\n\nasync function handleLogin() {')

# Need to import router
if 'import { useRouter }' not in content:
    content = content.replace("import { ref, reactive } from 'vue'", "import { ref, reactive } from 'vue'\nimport { useRouter } from 'vue-router'")
    content = content.replace('const formRef = ref<FormInstance>()', 'const router = useRouter()\nconst formRef = ref<FormInstance>()')

with open(r'D:\front\src\views\login\LoginView.vue', 'w', encoding='utf-8') as f:
    f.write(content)

print('Demo button added successfully')
