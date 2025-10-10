#!/usr/bin/env node

/**
 * 测试前端API调用是否修复了405错误
 */

const axios = require('axios');

// 前端API基础URL - 使用修复后的配置
const BASE_URL = 'http://localhost:9000'; // 修复：从9001改为9000

async function testSpiderAPI() {
    console.log('🕷️ 测试爬虫API调用');
    console.log('=' * 50);
    console.log(`API基础URL: ${BASE_URL}`);
    console.log('');

    try {
        // 测试爬虫API
        const spiderData = {
            url: 'http://blog.csdn.net/Tomdac/article/details/152162464?spm=1001.2014.3001.5502',
            mode: 'content',
            depth: 1,
            filters: ['ads', 'scripts'],
            delay: 1
        };

        console.log('1. 发送爬虫请求...');
        console.log(`URL: ${BASE_URL}/api/v1/spider/crawl`);
        console.log(`数据: ${JSON.stringify(spiderData, null, 2)}`);

        const response = await axios.post(`${BASE_URL}/api/v1/spider/crawl`, spiderData, {
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });

        console.log('✅ 请求成功!');
        console.log(`状态码: ${response.status}`);
        console.log('响应数据:');
        console.log(JSON.stringify(response.data, null, 2));

        // 检查响应内容
        if (response.data.success) {
            const data = response.data.data;
            console.log('');
            console.log('📊 爬虫结果摘要:');
            console.log(`标题: ${data.title}`);
            console.log(`字数: ${data.word_count || 0}`);
            console.log(`图片数: ${data.image_count || 0}`);
            console.log(`链接数: ${data.link_count || 0}`);
            console.log(`抓取时间: ${data.crawl_time}`);
            console.log('');
            console.log('🎉 前端API调用修复成功! 405错误已解决');
            return true;
        } else {
            console.log(`❌ API返回失败: ${response.data.message}`);
            return false;
        }

    } catch (error) {
        console.log('❌ 请求失败!');

        if (error.response) {
            console.log(`状态码: ${error.response.status}`);
            console.log(`状态文本: ${error.response.statusText}`);

            if (error.response.status === 405) {
                console.log('🚨 仍然存在405错误!');
            }

            try {
                console.log('错误响应:');
                console.log(JSON.stringify(error.response.data, null, 2));
            } catch (e) {
                console.log('错误响应:', error.response.data);
            }
        } else if (error.request) {
            console.log('网络连接错误:', error.message);
        } else {
            console.log('其他错误:', error.message);
        }

        return false;
    }
}

async function testOtherAPIs() {
    console.log('\n🔍 测试其他相关API');
    console.log('=' * 50);

    const tests = [
        { name: '健康检查', url: '/health', method: 'GET' },
        { name: '爬虫健康检查', url: '/api/v1/spider/health', method: 'GET' },
        { name: '获取推荐网站', url: '/api/v1/spider/recommend-sites', method: 'GET' },
        { name: '发布功能测试', url: '/publish/test', method: 'GET' }
    ];

    for (const test of tests) {
        try {
            console.log(`\n测试 ${test.name}...`);
            const response = await axios({
                method: test.method,
                url: `${BASE_URL}${test.url}`,
                timeout: 10000
            });

            console.log(`✅ ${test.name}: ${response.status} OK`);
        } catch (error) {
            console.log(`❌ ${test.name}: ${error.response?.status || 'NETWORK_ERROR'} ${error.response?.statusText || error.message}`);
        }
    }
}

async function main() {
    console.log('🚀 前端API修复验证测试');
    console.log(`测试时间: ${new Date().toLocaleString()}`);
    console.log('=' * 60);

    // 测试爬虫API
    const spiderSuccess = await testSpiderAPI();

    // 测试其他API
    await testOtherAPIs();

    console.log('\n' + '=' * 60);
    if (spiderSuccess) {
        console.log('🎉 测试结果: 前端API修复成功!');
        console.log('✅ 爬虫功能正常工作');
        console.log('✅ 405错误已解决');
        console.log('✅ 前端可以正常调用后端API');
    } else {
        console.log('❌ 测试结果: 仍存在问题');
        console.log('🔧 需要进一步检查修复');
    }
}

// 运行测试
main().catch(console.error);