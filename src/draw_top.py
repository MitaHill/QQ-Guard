from datetime import datetime


class RankingDrawer:
    def __init__(self):
        pass

    def create_ranking_text(self, violation_stats):
        """创建文字排行榜"""
        try:
            # 获取排序后的数据
            sorted_stats = sorted(violation_stats.items(), key=lambda x: x[1], reverse=True)[:10]

            if not sorted_stats:
                return "📊 违规排行榜\n\n❌ 暂无违规记录\n\n🕐 生成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 计算总违规数
            total_violations = sum(count for _, count in sorted_stats)

            # 构建排行榜文本
            ranking_text = "📊 违规排行榜\n"
            ranking_text += "=" * 30 + "\n\n"

            # 排行榜条目
            for i, (user_id, count) in enumerate(sorted_stats, 1):
                percentage = (count / total_violations * 100) if total_violations > 0 else 0

                # 排名图标
                if i == 1:
                    rank_icon = "🥇"
                elif i == 2:
                    rank_icon = "🥈"
                elif i == 3:
                    rank_icon = "🥉"
                else:
                    rank_icon = f"{i}️⃣"

                # 进度条
                bar_length = 10
                filled_length = int(bar_length * count / sorted_stats[0][1]) if sorted_stats[0][1] > 0 else 0
                progress_bar = "█" * filled_length + "░" * (bar_length - filled_length)

                ranking_text += f"{rank_icon} 第{i}名\n"
                ranking_text += f"👤 QQ号: {user_id}\n"
                ranking_text += f"⚠️ 违规次数: {count} 次\n"
                ranking_text += f"📈 违规率: {percentage:.1f}%\n"
                ranking_text += f"📊 {progress_bar}\n\n"

            # 统计信息
            ranking_text += "=" * 30 + "\n"
            ranking_text += f"📊 总违规数: {total_violations}\n"
            ranking_text += f"👥 活跃用户: {len(sorted_stats)}\n"
            ranking_text += f"🕐 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            return ranking_text

        except Exception as e:
            print(f"创建文字排行榜失败: {e}")
            return f"📊 Violation Leaderboard\n\n❌ Error generating ranking\n\n🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def create_ranking_image(self, violation_stats):
        """兼容性方法，返回文字排行榜"""
        return self.create_ranking_text(violation_stats)