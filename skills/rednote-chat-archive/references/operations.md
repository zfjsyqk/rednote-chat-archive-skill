# 运行、验证与交付

## 本地运行

在项目根目录执行 `python3 app.py`，访问 `http://127.0.0.1:8765/`。Python建议3.10及以上，使用标准库；附件转换需要PATH中的ffmpeg/ffprobe。无需Node启动服务，Node只用于JS语法检查。

发布版源路径统一通过contacts.SOURCE，由REDNOTE_SOURCE_DB或唯一容器发现配置。使用前核对当前Mac容器，不硬套历史UUID。读取被拒绝时区分运行沙箱与macOS文件隐私权限；实际请求对应权限，不尝试关闭系统保护。

前端改动刷新；后端改动重启本人启动的服务。重启使内存cookie会话失效，用户需重新输入已有密码。不要自动移除密码以便验证。

## 脚本

```sh
python3 app.py
python3 export_rednote.py --user '<小红书号或内部ID>'
python3 media.py
python3 convert_videos.py
```

export要求显式--user，不预设会话。media会扫描所有已备份真实原始消息，跳过已缓存文件，并重试失败文件。失败报告在media/report.json，现有total与cached可能口径不同（cached包含头像和表情），不能仅做两个数相减判断完整性。


## 测试

```sh
python3 test_contacts.py
python3 test_ai_chat.py
python3 test_providers.py
python3 test_app.py
python3 -m py_compile app.py contacts.py export_rednote.py media.py security.py sync_job.py ai_chat.py
node --check static/app.js
```

- contacts：虚构源库，多身份导出/注册和未知身份失败。
- ai_chat：临时AI库、保存期限、隔离、删除并发、超时，模拟接口。
- providers：两家HTTP路由、配置保留、密钥不回传。
- app：临时HTTP端口，密码接口保护、游标、日期、另存为不覆盖；可能需要本机监听权限。
- verify_media：连接实际8765验证Range与媒体格式；密码已设置时无cookie会失败，不能解除真实密码来跑它。


## GitHub准备


1. 忽略整个data、临时文件、字节码、日志、.env和操作系统文件。
2. 不把真实聊天、源快照、附件、头像、配置、API Key或密码散列作为示例提交。
4. 仅增加.gitignore不会删除已提交内容。检查git ls-files与暂存清单；密钥若曾泄露应由用户撤销/更换，再按其授权处理历史。
5. 本项目读取并保存第三方App内容，表情资源和附件不随源码分发。不要擅自添加用户未选择的开源许可证；没有LICENSE时不能宣称已有开源许可。
6. README提供运行条件、实际能力与缺口，不写“任意账号完整一键导出”“端到端加密”或“完整克隆真人”。

## 常见错误

- 找不到公开小红书号：本地缺明确映射。先打开App主页/聊天；再用含内部ID的主页链接。
- 无法读取容器：检查路径、登录状态和系统文件权限。
- 附件失败：报告具体失败数，重试失败文件；已失效链接可能无法恢复。
- AI持续等待：检查provider、密钥、模型、网络、额度，确认超时和UIfinally正常。
- OpenAI余额错误：检查API账单/限制，Plus会员不抵扣普通API Key费用。
- DeepSeek 401/402/429/503：分别对应密钥、余额、限流/繁忙等情况；按实际响应判断。
- 锁定后UI或媒体仍可读：检查后端接口保护和no-store，不能只修锁屏样式。

发布版test_contacts使用合成schema；维护中英文README及参考文档。
