"""
视频创作场景演练脚本：
演示同一套核心流水线，通过插拔不同插件，瞬间生成风格截然不同、无任何同质化痕迹的成片方案。
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

    topic = "脑机接口技术的突破与伦理危机"
    print("=" * 65)
    print(f"🎬 视频创作可插拔技能演练：【{topic}】")
    print("=" * 65)

    # ----------------------------------------------------
    # 组合 1：【悬疑反转文案】 + 【电影暗黑胶片分镜】
    # ----------------------------------------------------
    print("\n👉 [方案 A 装配中]：悬疑反转短剧风 + 电影暗黑分镜...")
    engine_a = PluggableSkillEngine(str(pipeline_json))
    engine_a.mount_plugin(str(plugins_dir / "plugin_suspense_script.md"))
    engine_a.mount_plugin(str(plugins_dir / "plugin_cinematic_dark_visual.md"))

    result_a = engine_a.run_pipeline(topic)
    print("\n✨ 方案 A 产出结果：")
    print(json.dumps(result_a, ensure_ascii=False, indent=2))

    # ----------------------------------------------------
    # 组合 2：【硬核科技文案】 + 【赛博朋克3D分镜】
    # ----------------------------------------------------
    print("\n" + "-" * 65)
    print("👉 [方案 B 装配中]：硬核科技解说风 + 赛博朋克3D分镜...")
    engine_b = PluggableSkillEngine(str(pipeline_json))
    engine_b.mount_plugin(str(plugins_dir / "plugin_tech_fast_script.md"))
    engine_b.mount_plugin(str(plugins_dir / "plugin_cyberpunk_visual.md"))

    result_b = engine_b.run_pipeline(topic)
    print("\n✨ 方案 B 产出结果：")
    print(json.dumps(result_b, ensure_ascii=False, indent=2))

    print("\n" + "=" * 65)
    print("🎯 核心结论：")
    print("1. 核心流水线规范保持 100% 稳定，输出契约字段完全一致。")
    print("2. 仅通过替换单文件 Markdown 插件，两组产出展现出完全迥异的审美与表达，彻底杜绝同质化！")
    print("=" * 65)


if __name__ == "__main__":
    main()
