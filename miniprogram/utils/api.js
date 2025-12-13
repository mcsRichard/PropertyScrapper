//utils/api.js
function getAppInstance() {
  try {
    return getApp()
  } catch (err) {
    return null
  }
}

function getAuthToken() {
  const app = getAppInstance()
  if (app && app.globalData && app.globalData.authToken) {
    return app.globalData.authToken
  }
  try {
    return wx.getStorageSync('authToken')
  } catch (err) {
    console.warn('读取本地token失败', err)
    return ''
  }
}

/**
 * 请求封装
 */
function request(url, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    const app = getAppInstance()
    const baseUrl = app?.globalData?.apiBaseUrl || ''
    const apiUrl = `${baseUrl}${url}`
    const headers = {
      'content-type': 'application/json'
    }
    const token = getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    wx.request({
      url: apiUrl,
      method: method,
      data: data,
      header: headers,
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
          return
        }
        if (res.statusCode === 401) {
          if (app && typeof app.clearAuthData === 'function') {
            app.clearAuthData()
          }
          wx.showToast({
            title: (res.data && res.data.error) || '请先登录',
            icon: 'none'
          })
          reject(res.data)
        } else {
          reject(res.data)
        }
      },
      fail: (err) => {
        console.error('请求失败:', err)
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

/**
 * 获取房产列表
 */
function getProperties(page = 1, limit = 20, filters = {}) {
  let url = `/api/properties?page=${page}&limit=${limit}`
  
  // 添加筛选条件
  if (filters.minPrice !== null && filters.minPrice !== undefined && filters.minPrice !== '') {
    url += `&min_price=${filters.minPrice}`
  }
  if (filters.maxPrice !== null && filters.maxPrice !== undefined && filters.maxPrice !== '') {
    url += `&max_price=${filters.maxPrice}`
  }
  if (filters.propertyType) {
    url += `&property_type=${filters.propertyType}`
  }
  if (filters.bedrooms !== null && filters.bedrooms !== undefined && filters.bedrooms !== '') {
    url += `&bedrooms=${filters.bedrooms}`
  }
  if (filters.listingType) {
    url += `&listing_type=${filters.listingType}`
  }
  
  // 添加排序参数
  if (filters.sortBy) {
    url += `&sort_by=${filters.sortBy}`
  }
  if (filters.sortOrder) {
    url += `&sort_order=${filters.sortOrder}`
  }
  
  console.log('API请求URL:', url)
  return request(url)
}

/**
 * 获取房产详情
 */
function getPropertyDetail(id) {
  return request(`/api/properties/${id}`)
}

/**
 * 搜索房产
 */
function searchProperties(keyword, page = 1, limit = 20) {
  return request(`/api/properties/search?keyword=${keyword}&page=${page}&limit=${limit}`)
}

/**
 * AI对话式搜索房产
 * @param {string} query - 自然语言查询，例如："帝国理工大学附近2室一厅公寓4000镑以下"
 * @param {string} listingType - 默认listing_type，'for_sale'或'for_rent'
 * @param {number} page - 页码
 * @param {number} limit - 每页数量
 */
function aiSearchProperties(query, listingType = 'for_rent', page = 1, limit = 20) {
  return request('/api/properties/ai-search?page=' + page + '&limit=' + limit, 'POST', {
    query: query,
    listing_type: listingType
  })
}

function login(code, userInfo = {}) {
  return request('/api/auth/login', 'POST', {
    code,
    user_info: userInfo
  })
}

function getCurrentUser() {
  return request('/api/users/me', 'GET')
}

function requestContactLink(propertyId) {
  return request('/api/users/contact-link', 'POST', {
    property_id: propertyId
  })
}

module.exports = {
  getProperties,
  getPropertyDetail,
  searchProperties,
  aiSearchProperties,
  login,
  getCurrentUser,
  requestContactLink
}
