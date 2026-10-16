"""
自媒体写作场景演练脚本：
演示同一套内容策划流水线，在面对【年轻人逃离大厂】这一主题时，
分别挂载“毒舌锐评”与“温情治愈”插件，产出截然相反但极具传播力的两种爆款文案。
"""

import sys
import json
from pathlib import Path

# 将项目根目录加入 sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

# 适配 Windows 控制台 UTF-8 输出
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from core.engine import PluggableSkillEngine


def main():
    base_dir = Path(__file__).parent
    pipeline_json = base_dir / "pipeline.json"
    plugins_dir = base_dir / "plugins"

    topic = "年轻人选择裸辞并逃离大厂"
    print("=" * 65)
    print(f"✍️ 自媒体文案可插拔演练：【{topic}】")
    print("=" * 65)

    # 方案 A：毒舌锐评
    print("\n👉 [方案 A 装配中]：毒舌辛辣锐评插件...")
    engine_a = PluggableSkillEngine(str(pipeline_json))
    engine_a.mount_plugin(str(plugins_dir / "plugin_sharp_critic.md"))
    result_a = engine_a.run_pipeline(topic)
    print("\n🔥 方案 A 产出：")
    print(json.dumps(result_a, ensure_ascii=False, indent=2))

    # 方案 B：温情治愈
    print("\n" + "-" * 65)
    print("👉 [方案 B 装配中]：温情治愈深度插件...")
    engine_b = PluggableSkillEngine(str(pipeline_json))
    engine_b.mount_plugin(str(plugins_dir / "plugin_warm_story.md"))
    result_b = engine_b.run_pipeline(topic)
    print("\n☕ 方案 B 产出：")
    print(json.dumps(result_b, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
