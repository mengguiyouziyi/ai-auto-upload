import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAccountStore = defineStore('account', () => {
  // 存储所有账号信息
  const accounts = ref([])
  
  // 平台类型映射
  const platformTypes = {
    1: '小红书',
    2: '视频号',
    3: '抖音',
    4: '快手'
  }
  
  // 设置账号列表
  const setAccounts = (accountsData) => {
    // 转换后端返回的数据格式为前端使用的格式
    accounts.value = accountsData.map(item => {
      // 处理两种可能的数据格式：数组格式（原始项目）和对象格式（当前实现）
      if (Array.isArray(item)) {
        // 原始项目的数组格式：[id, type, filePath, userName, status]
        return {
          id: item[0],
          type: item[1],
          filePath: item[2],
          name: item[3],
          userName: item[3],
          status: item[4] === 1 ? '正常' : '异常',
          platform: platformTypes[item[1]] || '未知',
          avatar: '/vite.svg'
        }
      } else {
        // 当前实现的对象格式
        return {
          id: item.id,
          type: item.type,
          filePath: item.filePath,
          name: item.name || item.userName,
          userName: item.userName || item.name,
          status: (item.status === 1 || item.status === '正常') ? '正常' : '异常',
          platform: item.platform || platformTypes[item.type] || '未知',
          avatar: item.avatar || '/vite.svg'
        }
      }
    })
  }
  
  // 添加账号
  const addAccount = (account) => {
    accounts.value.push(account)
  }
  
  // 更新账号
  const updateAccount = (id, updatedAccount) => {
    const index = accounts.value.findIndex(acc => acc.id === id)
    if (index !== -1) {
      accounts.value[index] = { ...accounts.value[index], ...updatedAccount }
    }
  }
  
  // 删除账号
  const deleteAccount = (id) => {
    accounts.value = accounts.value.filter(acc => acc.id !== id)
  }
  
  // 根据平台获取账号
  const getAccountsByPlatform = (platform) => {
    return accounts.value.filter(acc => acc.platform === platform)
  }
  
  return {
    accounts,
    setAccounts,
    addAccount,
    updateAccount,
    deleteAccount,
    getAccountsByPlatform
  }
})