# AI聊天与风格学习

## 服务与配置

- OpenAI：`https://api.openai.com/v1/responses`，Responses API，`store:false`，默认 `gpt-4.1-mini`，文字回复上限400 tokens。
- DeepSeek：`https://api.deepseek.com/chat/completions`，Chat Completions，默认 `deepseek-flash`，非流式、关闭thinking，max_tokens400。
- 默认名称是当前代码配置，不保证任意账号都可调用；模型可在设置修改。变更接入时重新查服务商官方文档，不根据旧记忆猜API参数。
- `ai_config.json`当前服务字段为provider；openai/deepseek各有key、model。兼容早期顶层OpenAI key/model；不要把OpenAI密钥发送给DeepSeek。
- 环境变量支持 `OPENAI_API_KEY`、`DEEPSEEK_API_KEY`。界面GET只返回已配置布尔值与模型，不返回秘密。
- 用户选择服务并保存后，当前会话的部分历史样本和近期AI上下文会发送给该服务。未获授权时只能本地整理/模拟测试。

OpenAI官方文档：<https://developers.openai.com/api/docs/guides/text>。
DeepSeek官方文档：<https://api-docs.deepseek.com/api/create-chat-completion/>。
API余额、计费和ChatGPT会员分开；限流、余额、密钥和网络错误应分类，不把所有429都判为同一原因。

## 当前风格算法

1. 只读真实库中当前contact的普通文字，排除以 `[` 开头的类型占位文本。这是现有启发式，可能误排除用户自己以方括号开头的普通文字。
2. 本人 `sender=我` 的消息只作为previous_user背景；其余消息作为对方风格示例。
3. 本地统计对方全部可用文字：典型长度、20字以内比例、常见称呼/语气词、R表情、提问比例。
4. 单次发送近期70条、跨历史跨度约80条、相关接话最多35条；按(text,previous_user)去重，每段最多350字。
5. 中文匹配目前是简单两字片段，英语是词片段，不是语义检索。风格提升方向应由真实反馈驱动，例如优化话题匹配/连续轮次，不要把现有算法描述为全面理解本人。
6. 最近30条AI对话用于连续上下文；指令明确这些AI回复不是风格范例。

提示词应明确目标昵称、“我”与对方的角色，优先模仿对方实际短句节奏、称呼、反问/调侃和表情频率；避免泛泛客服式安慰和长分析。亲密程度要有历史依据，不能凭AI模型自行加重。

表情优先 `[名称R]`，使用原历史中出现的名称；前端用profiles映射显示原生图片，无资源时系统emoji回退。不能声称统计或样本等于完整训练，更不能承诺还原真人当前感情。

## 独立数据库

`ai_chats.sqlite3`内：

- `settings(id=1,days)`：1/7/30/60，0表示永久。
- `messages(id,contact,role,content,created)`：role为user/assistant，created为epoch秒；双方AI会话消息都与真实库隔离。
- `generations(contact,value)`：用于防止删除与生成并发后记录复活。

默认1天，从每条消息创建时间计算，不是自然日零点，也不是最后聊天时间。修改设置后立即按新天数清理。后台30秒轮询；读取时清理；服务关闭时不会运行，下一次启动时清理过期内容。`PRAGMA secure_delete=ON`覆盖删除页内容，但不构成对电脑备份、API服务商或已有文件副本的删除承诺。

删除只影响选定contact的AI记录。UI需确认，再提升generation。生成回复在写入前核对generation，若已删除则拒绝保存。真实库、附件、联系人不受影响。

## 请求生命周期

- 每contact只允许一个AI请求，BUSY必须在finally释放。
- 服务商网络读超时30秒；整体生成等待45秒；前端请求60秒兜底。
- 整体超时后生成线程可能继续运行，但不再保存该回复。不能自动无限重试，避免重复费用。
- 点击发送后前端立即显示本人消息，并先显示对方头像、名字-AI和“回复中…”占位；这些待发送节点不写入数据库。成功后用服务端返回的已保存记录替换，避免重复。
- 成功后才成对保存用户文字及AI回复；失败在占位气泡显示原因、恢复输入草稿，并标记发送未完成。删除当前AI记录也清除待回复占位。
- 切换会话、锁定或过期响应不能把内容插入错误会话。
- 前端模型选择、更改保存、用户发消息与API调用要分清；不能为了测试直接替用户输入或展示真实密钥。

## 验证标准

用临时文件和模拟HTTP响应验证服务路由、密钥隔离、OpenAI输出/DeepSeek choices解析、保存时效、会话隔离、真实库字节未变、删除竞态、超时后释放BUSY和迟到回复不保存。

没有密钥或额度时报告无法验证真实回复；运行中的模型测试需说明实际是否调用、是否包含历史。风格“更像”必须由用户反馈或明确评估判定，不能仅依据提示词变更就宣称完全复刻成功。
