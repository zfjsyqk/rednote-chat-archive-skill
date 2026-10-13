# red_note 项目开发约定

## 功能变动必须同步文档

用户要求：每次新增、修改或移除功能，都在同一任务中自动更新：

- `README.md` 和 `README.en.md`：使用方法、实际功能、配置和实质限制。
- `skills/rednote-chat-archive/SKILL.md`：可复用维护规则、当前能力或简短维护摘要。
- `skills/rednote-chat-archive/references/` 中与变动有关的文档：产品交互、架构数据、AI逻辑、运行交付。

包括界面文案、样式及位置、交互流程、默认值、数据结构、服务配置和API行为变化。先修订已有描述，避免互相矛盾的追加；只记录已实现且已核对的最终行为。任务结束前核对代码和文档一致，不需再次询问是否更新。

维护本项目时按需读取 `skills/rednote-chat-archive/SKILL.md` 及相关参考。聊天、密钥及运行数据不进入文档或Git，整个 `data/` 保持忽略。真实聊天与AI数据必须分库；源小红书数据库保持只读。

同步更新英文Skill说明及references/*.en.md。
