# 架构与数据

## 代码分工

| 文件 | 职责 |
| --- | --- |
| `app.py` | 本机 HTTP 服务、真实记录查询、导入导出、附件Range、另存为、认证和功能接口 |
| `contacts.py` | 身份解析、会话注册；原始用户/会话表、HTTP数据库及磁盘缓存映射、主页短链接首次跳转解析 |
| `export_rednote.py` | 源数据库只读快照、目标会话筛选、真实消息归一化、原始字段导出、头像 |
| `media.py` | 原消息媒体链接抽取、增量下载、语音/视频兼容转换、附件登记 |
| `convert_videos.py` | 已缓存旧视频的补充转换 |
| `sync_job.py` | 全局单任务线程，串行执行会话导出和媒体下载 |
| `security.py` | 密码散列、内存会话、失败次数限制 |
| `ai_chat.py` | 独立AI存储、保存时效、模型请求、风格样本和删除竞态保护 |
| `static/` | 页面、交互脚本和样式 |

## 数据文件

整个 `data/` 为私有运行数据，不提交 Git。

- `chats.sqlite3`：真实归一化消息、原始消息、附件登记、已配置会话。
- `source-backups/`：小红书数据库一致快照；可能包含其他会话，不能当作仅目标联系人的导出公开。
- `exports/`：每会话 `.json`、`.raw.json`、`.report.json`。
- `media/`：本地附件，以URL SHA-256命名；转换后附 `.m4a`/`.mp4`；报告。
- `profiles.json`：头像和表情本地URL映射。
- `security.json`：访问密码的salt/hash，非明文。
- `ai_chats.sqlite3`：AI消息、保存天数、删除代数。
- `ai_config.json`：当前服务、每服务模型/密钥；权限0600。

备份数据库应停止服务后复制，或使用 SQLite backup API。完整媒体档案需同时保存数据库、附件、导出文件和映射；JSON本身不包含附件二进制。

## 真实库的关键表

- `messages(id,contact,sender,time,content,source_id)`：原生导出按source_id唯一；一般导入在source_id为空时按contact/sender/time/content去重。不能删除source_id逻辑，否则相同文字及时间的两条真实消息会丢失。
- `rednote_raw(source_id,contact,payload)`：保留源消息全部字段，供消息类型、多媒体和未来解析使用。
- `media_assets(url,path,mime,error)`：只通过登记过的路径提供附件，不能开放任意文件读取。
- `rednote_contacts(public_id,peer_id,owner_id,local_id,nickname,avatar_url,contact)`：联系人来源与身份关联。

## 小红书原始表及字段

当前适配的 Mac iOS版小红书将私信保存在 `PrivateMessage.db`。源目录位于应用容器下：

```text
~/Library/Containers/<UUID>/Data/Documents/XYStorageCoreRoot/Common/
  storage.common.defaultDataBase/Files/PrivateMessage.db
```

核心表：

- `XYPMMessageUserModel`：`user_id,nickname,avatar,local_user_id,accountName,record_id`。
- `XYPMMessageChatModel`：`chat_id,local_chat_user_id,ownerUserId,nickname`。
- `XYPMMessageMessageModel`：`message_id,uuid,local_message_id,local_chat_user_id,sender_id,receiver_id,create_time,store_id,content_type,content`。

`local_chat_user_id`一般为 `<peer内部ID>@<本人内部ID>`；筛选此字段防止混入其他账号会话。时间戳是毫秒，转为Asia/Shanghai，保留毫秒。源字段随版本可能变化，应检查schema再适配。

| content_type | 当前解释 |
| --- | --- |
| 0 | 空/未知，不要擅自判断为系统消息 |
| 1 | 普通文字 |
| 2 | 图片；imageDataMap IM_ORG / link |
| 3 | 分享；title、cover/image、user、noteType、link |
| 4 | 系统消息 |
| 9 | 语音；link、duration等 |
| 10 | 撤回提示 |
| 11 | 视频；originalVideoLink/videoLink及封面 |
| 13 | 互动表情；emojiKey、image等 |
| 16 | 自定义表情；url/thumb、width/height |
| 17 | 通话；senderContent/receiverContent，根据发送方与本人身份选显示文字 |

已撤回消息只展示源记录允许的内容，不尝试恢复已删除文本。分享的 `xhsdiscover:` 链接是App深链接，前端仅允许已知安全协议。

## 接口地图

认证状态公开，其余 `/api/`、`/media/` 都需通过密码锁（未设置密码视为允许）。POST要求JSON，检查Host及Origin。

- 认证：GET `/api/auth/status`；POST `/api/auth/login`、`/api/auth/password`、`/api/auth/lock`。
- 真实记录：GET `/api/contacts`、`/api/messages`、`/api/timeline`、`/api/export`、`/api/config`。
- 备份：POST `/api/add-contact`、`/api/sync`；GET `/api/sync-status`、`/api/media-status`。
- 文件：POST `/api/import`、`/api/save`；GET `/media/<registered-name>`。
- AI：GET `/api/ai/settings`、`/api/ai/messages?contact=...`；POST `/api/ai/settings`、`/api/ai/send`、`/api/ai/delete`。

真实消息参数：`contact,q,page,start,end,at,before_time,before_id`。响应包含消息、总数、游标及has_more；at定位额外返回target_id、target_day，以目标消息排序排名计算精确offset并保证该消息在返回批次内。AI历史目前独立读取，在页面末尾分区显示。

## 已知工程缺口

源路径由REDNOTE_SOURCE_DB或唯一容器发现统一配置，发布版无初始会话身份。同步任务目前依据脚本退出码报告完成，附件脚本即使部分下载失败也可能退出0，因此同时核对附件错误数。自动识别数值小红书号依赖缓存，并非总能成功。头像映射共享JSON有并发更新风险；修改相关流程时考虑原子写入，但不要宣称当前已有完整多进程安全保障。

每个会话更多菜单提供红色“删除备份”：输入当前访问密码二次确认（未设置密码需先设置），删除该会话的真实消息、原始元数据、AI记录、会话注册、项目导出及专属附件，并清理项目源数据库快照中的相关身份行。保留其他会话及共用附件；不修改小红书客户端源数据库，不删除外部另存文件。备份进行中禁止删除，密码错误不执行删除。删除无法撤销；重新添加会重新读取客户端仍保留的记录。
