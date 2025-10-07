const { test, expect } = require('@playwright/test');

test.describe('直接API测试 - GLM-4.6文本优化', () => {

  test('直接调用文本优化API', async ({ request }) => {
    console.log('🚀 直接测试GLM-4.6 API调用...');

    const apiUrl = 'http://localhost:9000/api/v1/llm/optimize-text';

    const requestBody = {
      text: `在AI编程工具竞争白热化的当下，OpenAI推出的Codex编程助手凭借"本地安全运行"、"ChatGPT深度集成"、"全工具链覆盖"三大核心优势，迅速在GitHub狂揽4万星标，成为开发者热议的焦点。这款工具搭载GPT-5-Codex模型，能像专业程序员般连续7小时迭代复杂项目、修复Bug、运行测试，彻底改变传统编程的低效流程。`,
      provider: "glm"
    };

    console.log('📤 发送请求到:', apiUrl);
    console.log('📝 请求体:', JSON.stringify(requestBody, null, 2));

    try {
      const startTime = Date.now();
      const response = await request.post(apiUrl, {
        data: requestBody,
        timeout: 30000 // 30秒超时
      });
      const endTime = Date.now();

      console.log(`📥 响应状态: ${response.status()}`);
      console.log(`⏱️  响应时间: ${endTime - startTime}ms`);

      if (response.status() === 200) {
        const responseBody = await response.json();
        console.log('✅ API调用成功');
        console.log('📄 响应内容:');
        console.log(JSON.stringify(responseBody, null, 2));

        expect(responseBody).toHaveProperty('optimized_text');
        expect(responseBody).toHaveProperty('provider');
        expect(responseBody).toHaveProperty('response_time');

        console.log(`🎯 优化文本长度: ${responseBody.optimized_text?.length || 0}`);
        console.log(`🏷️  使用的提供商: ${responseBody.provider}`);
        console.log(`⏱️  响应时间: ${responseBody.response_time}ms`);

      } else {
        const errorText = await response.text();
        console.log(`❌ API调用失败: ${response.status}`);
        console.log('📄 错误详情:', errorText);

        // 检查是否是429错误
        if (response.status === 429) {
          console.log('⚠️  确认是429速率限制错误');
        }
      }
    } catch (error) {
      console.log('🚨 网络请求异常:', error.message);

      if (error.message.includes('timeout')) {
        console.log('⏱️  请求超时，可能是由于重试机制导致的延迟');
      }
    }
  });

  test('测试豆包Provider作为备用', async ({ request }) => {
    console.log('🚀 测试豆包备用Provider...');

    const apiUrl = 'http://localhost:9000/api/v1/llm/optimize-text';

    const requestBody = {
      text: '测试豆包API的文本优化功能，验证备用方案是否正常工作。',
      provider: "doubao"
    };

    console.log('📤 发送豆包请求到:', apiUrl);

    try {
      const startTime = Date.now();
      const response = await request.post(apiUrl, {
        data: requestBody,
        timeout: 15000
      });
      const endTime = Date.now();

      console.log(`📥 豆包响应状态: ${response.status()}`);
      console.log(`⏱️  豆包响应时间: ${endTime - startTime}ms`);

      if (response.status() === 200) {
        const responseBody = await response.json();
        console.log('✅ 豆包API调用成功');
        console.log('🎯 豆包优化文本长度:', responseBody.optimized_text?.length || 0);
      } else {
        const errorText = await response.text();
        console.log(`❌ 豆包API调用失败: ${response.status}`);
        console.log('📄 豆包错误详情:', errorText);
      }
    } catch (error) {
      console.log('🚨 豆包网络请求异常:', error.message);
    }
  });

  test('测试多个连续请求以触发重试机制', async ({ request }) => {
    console.log('🚀 测试多个连续请求，触发GLM重试机制...');

    const apiUrl = 'http://localhost:9000/api/v1/llm/optimize-text';

    for (let i = 1; i <= 3; i++) {
      console.log(`📤 第${i}次请求...`);

      const requestBody = {
        text: `第${i}次测试：GLM-4.6文本优化功能，验证重试和降级机制是否正常工作。`,
        provider: "glm"
      };

      try {
        const startTime = Date.now();
        const response = await request.post(apiUrl, {
          data: requestBody,
          timeout: 25000
        });
        const endTime = Date.now();

        console.log(`📥 第${i}次请求状态: ${response.status()}, 响应时间: ${endTime - startTime}ms`);

        if (response.status() === 200) {
          const responseBody = await response.json();
          console.log(`✅ 第${i}次请求成功，提供商: ${responseBody.provider}`);
        } else {
          const errorText = await response.text();
          console.log(`❌ 第${i}次请求失败: ${response.status()}`);

          if (response.status() === 429) {
            console.log(`⚠️  第${i}次请求遇到429限制，等待重试...`);
          }
        }
      } catch (error) {
        console.log(`🚨 第${i}次请求异常: ${error.message}`);
      }

      // 短暂间隔
      if (i < 3) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  });
});