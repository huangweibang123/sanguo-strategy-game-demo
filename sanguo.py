# -*- coding: utf-8 -*-
"""
================================================================================
  三国志 · 霸王的大陆（简化复刻版）  ——  Python + Pygame
================================================================================
  本游戏为经典 FC 游戏《三国志·霸王的大陆》的简化复刻，纯单机、无网络、
  无第三方资源文件（武将、城池、数值全部由 config.json 驱动）。

  ----------------------------------------------------------------------------
  【运行步骤】
  1. 安装 Python 3.8 及以上版本（勾选 Add python to PATH）。
  2. 打开命令行（cmd / PowerShell），执行：
         pip install pygame
  3. 把本文件 sanguo.py 与 config.json 放在同一目录。
  4. 在该目录下执行：
         python sanguo.py
  5. 首次运行若提示找不到中文字体，请把 config.json 同级目录放入一款
     中文 ttf/ttc 字体（如 msyh.ttc / simhei.ttf），代码会自动尝试加载。

  ----------------------------------------------------------------------------
  【玩法介绍】
  · 开局在曹操 / 刘备 / 孙权 三大势力中选择君主，其余两方由 AI 控制。
  · 游戏在一张 12 城网格地图上进行，目标是占领全部城池统一天下。
  · 每座城池有：兵力（troops）、粮草（food）、驻守武将列表、潜伏武将（hidden）。
  · 每个城池指令都会消耗 1 个回合；一回合结束后所有城池自动消耗粮草，
    粮草为负则兵力持续衰减。
  · 城池指令（在城市菜单按数字键选择）：
        1 征兵   —— 消耗粮草补充兵力（每 1000 兵耗 200 粮，档位 1000/2000/3000）
        2 搜索   —— 概率发现本城潜伏武将，发现后自动加入我方
        3 调兵   —— 把本城兵力调动到相邻己方城池
        4 调粮   —— 把本城粮草调动到相邻己方城池（支援前线）
        5 进攻   —— 出兵攻打相邻的敌方 / 中立城池
        6 返回   —— 回到大地图
  · 攻城战进入战斗界面，4 种战法：
        1 交战   —— 双方按武力差互扣兵力
        2 斗将   —— 双方出战武力最高武将单挑，胜者重创敌军
        3 火攻   —— 依主将智力判定成功率，成功则敌军大乱，失败则自损
        4 撤退   —— 保留约七成兵力退回本城
  · 胜利：占领地图内全部城池。
  · 失败：己方所有城池全部失守（君主下野）。

  ----------------------------------------------------------------------------
  【按键说明】
  标题界面      ：按 1 / 2 / 3 选择君主
  大地图         ：← / →  在己方城池间移动光标
                       回车      进入选中城池的管理菜单
                       E         结束我方回合（立即结算 + AI 行动）
  菜单界面      ：数字键 1 ~ 9 / 0  按提示选择选项
  战斗界面      ：数字键 1 ~ 4  选择战法
  任意界面      ：Esc  返回上一级；Q  退出游戏

  ----------------------------------------------------------------------------
  【字体加载说明（重要）】
  本项目严格遵守“禁用 pygame.font.SysFont”的约束，统一使用
  pygame.font.Font(字体文件路径, size) 的方式加载字体。代码内置了
  一组常见中文字体路径候选（Windows 微软雅黑 / 黑体 / 宋体，macOS
  苹方，Linux 文泉驿），会按顺序探测并加载第一个存在的字体文件，
  从而避免中文显示为方框。
================================================================================
"""

import os
import sys
import json
import random
import pygame

# ============================================================================
# 一、全局配置与字体（强制使用 pygame.font.Font(文件路径, size)，禁止 SysFont）
# ============================================================================

# 当前文件所在目录，保证 sanguo.py 与 config.json 同目录即可运行
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 读取外部配置
with open(os.path.join(BASE_DIR, "config.json"), "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

# 内置候选中文字体路径（按优先级尝试，全部不存在时退化为默认字体）
# 这里就是“代码内置方式加载系统字体文件”的实现——不调用 SysFont，
# 而是直接把字体文件路径交给 pygame.font.Font。
FONT_CANDIDATES = [
    # Windows 常见中文字体
    "C:/Windows/Fonts/msyh.ttc",     # 微软雅黑
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",   # 黑体
    "C:/Windows/Fonts/simsun.ttc",   # 宋体
    # macOS 常见中文字体
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    # Linux 常见中文字体
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    # 同目录兜底（用户可自行放一个 ttf 进去）
    os.path.join(BASE_DIR, "font.ttf"),
    os.path.join(BASE_DIR, "msyh.ttc"),
]


def load_font(size):
    """加载指定大小的字体：依次尝试候选字体文件，全部失败再退回 Font(None)。"""
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                # 关键调用：pygame.font.Font(文件路径, size) —— 不使用 SysFont
                return pygame.font.Font(path, size)
            except Exception:
                # 个别 ttc 文件损坏或不被支持时，继续尝试下一个
                continue
    # 兜底：Pygame 默认字体（不支持中文，会显示方框，但保证程序不崩溃）
    print("[警告] 未找到中文字体文件，中文可能显示为方框。请放置一款中文 ttf/ttf 到游戏目录。",
          file=sys.stderr)
    return pygame.font.Font(None, size)


# ============================================================================
# 二、工具函数
# ============================================================================

def avg(nums):
    """求平均，空列表返回 0。"""
    return sum(nums) / len(nums) if nums else 0


def force_of(general):
    """取武将武力。"""
    return general.get("force", 0)


def intel_of(general):
    """取武将智力。"""
    return general.get("intel", 0)


# ============================================================================
# 三、游戏主类
# ============================================================================

class ThreeKingdoms:
    """简化版《三国志·霸王的大陆》主逻辑类。"""

    # 游戏状态枚举（用字符串便于打印调试）
    ST_TITLE   = "title"    # 标题 / 选君主
    ST_MAP     = "map"      # 大地图
    ST_CITY    = "city"     # 城市管理菜单
    ST_RECRUIT = "recruit"  # 征兵档位
    ST_SEARCH  = "search"   # 搜索结果
    ST_MOVE    = "move"     # 选择调兵目标
    ST_MOVE_AMT= "move_amt" # 输入调兵数量
    ST_MOVE_FOOD    = "move_food"     # 选择调粮目标
    ST_MOVE_FOOD_AMT= "move_food_amt" # 输入调粮数量
    ST_ATTACK  = "attack"   # 选择进攻目标
    ST_BATTLE  = "battle"   # 战斗战法选择
    ST_RESULT  = "result"   # 战斗 / 操作结果展示
    ST_GAMEOVER= "gameover" # 胜负结算

    def __init__(self):
        pygame.init()

        # 读取窗口与配色
        win = CONFIG["window"]
        self.W = win["width"]
        self.H = win["height"]
        self.colors = CONFIG["colors"]

        self.screen = pygame.display.set_mode((self.W, self.H))
        pygame.display.set_caption(win["title"])
        self.clock = pygame.time.Clock()

        # 加载不同字号的中文字体（全部走 load_font -> Font(文件路径, size)）
        self.font_big   = load_font(36)
        self.font_mid   = load_font(22)
        self.font_small = load_font(18)
        self.font_tiny  = load_font(15)

        # 读取平衡参数
        self.bal = CONFIG["balance"]

        # 初始化游戏数据（深拷贝配置，避免多次开档互相污染）
        self._setup_world()

        # 运行期状态
        self.state = self.ST_TITLE
        self.player_faction = None     # "cao" / "liu" / "sun"
        self.turn = 1                  # 当前回合数
        self.selected_idx = 0          # 大地图上光标选中的城池索引
        self.current_city_idx = None   # 当前正在管理的城池索引
        self.message = "按 1 / 2 / 3 选择你的君主，开始乱世征程！"
        self.battle = None             # 战斗上下文 dict
        self.after_state = None        # 结果展示后要回到的状态
        self.running = True

    # ------------------------------------------------------------------
    # 世界初始化
    # ------------------------------------------------------------------
    def _setup_world(self):
        """把 config.json 中的武将、城池装载到内存。"""
        # 武将按 id 索引，方便城池引用
        self.generals = {g["id"]: dict(g) for g in CONFIG["generals"]}
        # 城池列表（深拷贝，保证重开游戏时数据干净）
        self.cities = []
        for c in CONFIG["cities"]:
            city = dict(c)
            city["generals"] = list(c.get("generals", []))
            city["hidden"]   = list(c.get("hidden", []))
            # 预计算屏幕坐标（根据网格 gx, gy）
            city["px"] = 80 + city["gx"] * 175
            city["py"] = 110 + city["gy"] * 150
            self.cities.append(city)

    # ------------------------------------------------------------------
    # 工具：取城池颜色 / 玩家城池列表
    # ------------------------------------------------------------------
    def _color_of(self, city):
        """根据城池归属返回颜色。"""
        key = city["owner"]
        if key == "neutral":
            return self.colors["neutral"]
        return self.colors[CONFIG["factions"][key]["color_key"]]

    def _player_cities(self):
        """返回玩家拥有的城池索引列表。"""
        return [i for i, c in enumerate(self.cities) if c["owner"] == self.player_faction]

    def _general_objs(self, city):
        """返回城池里所有武将对象列表。"""
        return [self.generals[gid] for gid in city["generals"]]

    def _top_general(self, city):
        """返回城池中武力最高的武将（斗将用）。"""
        gens = self._general_objs(city)
        if not gens:
            return None
        return max(gens, key=lambda g: g["force"])

    def _smartest_general(self, city):
        """返回城池中智力最高的武将（火攻用）。"""
        gens = self._general_objs(city)
        if not gens:
            return None
        return max(gens, key=lambda g: g["intel"])

    def _adjacent(self, idx):
        """返回与 idx 城池网格相邻的所有城池索引。"""
        c = self.cities[idx]
        result = []
        for i, other in enumerate(self.cities):
            if i == idx:
                continue
            if abs(other["gx"] - c["gx"]) + abs(other["gy"] - c["gy"]) == 1:
                result.append(i)
        return result

    # ------------------------------------------------------------------
    # 君主选择
    # ------------------------------------------------------------------
    def choose_ruler(self, key_num):
        """玩家按 1/2/3 选择君主。"""
        mapping = {1: "cao", 2: "liu", 3: "sun"}
        if key_num not in mapping:
            return
        self.player_faction = mapping[key_num]
        self.state = self.ST_MAP
        name = CONFIG["factions"][self.player_faction]["name"]
        self.selected_idx = self._player_cities()[0]
        self.message = f"你选择了【{name}】势力。←/→ 选择己方城池，回车进入管理，E 结束回合。"

    # ------------------------------------------------------------------
    # 城市指令：征兵 / 搜索 / 调兵 / 进攻
    # ------------------------------------------------------------------
    def do_recruit(self, amount):
        """征兵：消耗粮草增加兵力。amount 为新增兵力数。"""
        city = self.cities[self.current_city_idx]
        # 正确公式：每 1000 兵耗 recruit_cost_per_1000 粮（默认 200）
        # 例：1000 兵 -> 200 粮；2000 兵 -> 400 粮；3000 兵 -> 600 粮
        cost = int(amount / 1000) * self.bal["recruit_cost_per_1000"]
        if city["food"] < cost:
            self.message = f"粮草不足！征兵 {amount} 需要 {cost} 粮，当前仅 {city['food']}。"
            return False
        city["food"]  -= cost
        city["troops"] += amount
        self.message = f"在【{city['name']}】征兵 {amount} 人，耗粮 {cost}。剩余兵力 {city['troops']}，粮 {city['food']}。"
        return True

    def do_move_food(self, target_idx, amount):
        """调粮：从当前城调动 amount 粮草到相邻己方城。"""
        src = self.cities[self.current_city_idx]
        dst = self.cities[target_idx]
        amount = min(amount, src["food"])
        if amount <= 0:
            self.message = "本城粮草不足，无法调动。"
            return False
        src["food"] -= amount
        dst["food"] += amount
        self.message = f"从【{src['name']}】调粮 {amount} 至【{dst['name']}】。"

    def do_search(self):
        """搜索：概率发现本城潜伏武将。"""
        city = self.cities[self.current_city_idx]
        if not city["hidden"]:
            self.message = f"【{city['name']}】已无可寻访之才。"
            return False
        # 搜索成功率
        if random.random() < self.bal["search_base_prob"]:
            gid = city["hidden"].pop(0)
            gen = self.generals[gid]
            city["generals"].append(gid)
            self.message = f"寻访成功！在【{city['name']}】发现大贤【{gen['name']}】（武{gen['force']} 智{gen['intel']}），已加入我方！"
        else:
            self.message = f"在【{city['name']}】寻访数日，未发现奇才。再接再厉！"
        return True

    def do_move(self, target_idx, amount):
        """调兵：从当前城调动 amount 兵力到 target_idx。"""
        src = self.cities[self.current_city_idx]
        dst = self.cities[target_idx]
        amount = min(amount, src["troops"] - 100)  # 至少留 100 兵守城
        if amount <= 0:
            self.message = "兵力不足，无法调动（至少需留 100 兵守城）。"
            return False
        src["troops"] -= amount
        dst["troops"] += amount
        self.message = f"从【{src['name']}】调兵 {amount} 至【{dst['name']}】。"
        return True

    # ------------------------------------------------------------------
    # 战斗系统
    # ------------------------------------------------------------------
    def start_battle(self, target_idx):
        """进入战斗：记录攻守双方信息。"""
        self.battle = {
            "attacker_idx": self.current_city_idx,
            "defender_idx": target_idx,
            "over": False,
            "log": [],
        }
        self.state = self.ST_BATTLE

    def _apply_battle_loss(self, attacker_loss, defender_loss, log_text):
        """扣减双方兵力并记录日志。"""
        atk = self.cities[self.battle["attacker_idx"]]
        dfn = self.cities[self.battle["defender_idx"]]
        atk["troops"] = max(0, atk["troops"] - attacker_loss)
        dfn["troops"] = max(0, dfn["troops"] - defender_loss)
        self.battle["log"].append(log_text)

    def battle_engage(self):
        """战法 1：交战 —— 双方按武力差互扣兵力。"""
        atk = self.cities[self.battle["attacker_idx"]]
        dfn = self.cities[self.battle["defender_idx"]]
        atk_gen = self._top_general(atk) or {"name": "无名小将", "force": 50}
        dfn_gen = self._top_general(dfn) or {"name": "无名守将", "force": 50}

        base = self.bal["battle_base_loss"]
        # 武力差影响杀伤：己方武力越高，对敌方杀伤越大
        atk_loss = int(dfn["troops"] * (base + dfn_gen["force"] / 400) * random.uniform(0.85, 1.15))
        dfn_loss = int(atk["troops"] * (base + atk_gen["force"] / 400) * random.uniform(0.85, 1.15))

        self._apply_battle_loss(atk_loss, dfn_loss,
            f"两军交锋！{atk['name']} 损 {atk_loss}，{dfn['name']} 损 {dfn_loss}。")

    def battle_duel(self):
        """战法 2：斗将 —— 双方出武力最高武将单挑，胜者重创敌军。"""
        atk = self.cities[self.battle["attacker_idx"]]
        dfn = self.cities[self.battle["defender_idx"]]
        atk_gen = self._top_general(atk) or {"name": "无名小将", "force": 50}
        dfn_gen = self._top_general(dfn) or {"name": "无名守将", "force": 50}

        atk_power = atk_gen["force"] * random.uniform(0.85, 1.15)
        dfn_power = dfn_gen["force"] * random.uniform(0.85, 1.15)

        if atk_power > dfn_power:
            # 攻方斗将胜：守方损失惨重
            loss = int(dfn["troops"] * random.uniform(0.45, 0.65))
            self._apply_battle_loss(0, loss,
                f"斗将！{atk_gen['name']} 力挫 {dfn_gen['name']}！{dfn['name']} 损兵 {loss}！")
        elif dfn_power > atk_power:
            loss = int(atk["troops"] * random.uniform(0.35, 0.55))
            self._apply_battle_loss(loss, 0,
                f"斗将！{dfn_gen['name']} 神勇！{atk['name']} 损兵 {loss}！")
        else:
            l1 = int(atk["troops"] * 0.15)
            l2 = int(dfn["troops"] * 0.15)
            self._apply_battle_loss(l1, l2,
                f"斗将！{atk_gen['name']} 与 {dfn_gen['name']} 大战百余合不分胜负，双方各损 {l1}。")

    def battle_fire(self):
        """战法 3：火攻 —— 智力决定成功率，成功则敌军大乱，失败则自损。"""
        atk = self.cities[self.battle["attacker_idx"]]
        dfn = self.cities[self.battle["defender_idx"]]
        gen = self._smartest_general(atk) or {"name": "无名谋士", "intel": 50}

        # 成功率 = 智力 / 120，封顶 90%
        success_rate = min(0.9, gen["intel"] / 120.0)
        if random.random() < success_rate:
            loss = int(dfn["troops"] * random.uniform(0.5, 0.7))
            self._apply_battle_loss(0, loss,
                f"火攻！{gen['name']} 借风纵火，{dfn['name']} 大火连绵，损兵 {loss}！")
        else:
            loss = int(atk["troops"] * random.uniform(0.2, 0.35))
            self._apply_battle_loss(loss, 0,
                f"火功失败！风向突变，{gen['name']} 自乱阵脚，损兵 {loss}。")

    def battle_retreat(self):
        """战法 4：撤退 —— 保留部分兵力回城。"""
        atk = self.cities[self.battle["attacker_idx"]]
        keep = int(atk["troops"] * self.bal["retention_on_retreat"])
        lost = atk["troops"] - keep
        atk["troops"] = keep
        self.battle["log"].append(f"我军闻鼓收兵，安然撤退，丢弃辎重损兵 {lost}。")
        self.battle["over"] = True  # 撤退直接结束战斗

    def battle_check_result(self):
        """每回合战斗后检查：是否破城 / 攻方是否溃败。"""
        atk = self.cities[self.battle["attacker_idx"]]
        dfn = self.cities[self.battle["defender_idx"]]

        if dfn["troops"] <= 0:
            # 攻破城池：归属转移，残兵进城驻守
            old_owner = dfn["owner"]
            dfn["owner"] = atk["owner"]
            # 破城后残兵驻守（攻方残兵进城，取剩余兵力 60%）
            survivor = int(atk["troops"] * 0.6)
            atk["troops"] -= survivor
            dfn["troops"] = survivor
            # 守将归降新主，继续驻守新城
            gen_names = "、".join(self.generals[g]["name"] for g in dfn["generals"]) or "无"
            old_name = CONFIG["factions"].get(old_owner, {"name": "中立"})["name"]
            self.battle["log"].append(
                f"城破！{atk['name']} 拿下 {dfn['name']}（原属 {old_name}），守将 {gen_names} 归降。")
            self.battle["over"] = True
        elif atk["troops"] <= 0:
            # 攻方全军覆没
            self.battle["log"].append(f"{atk['name']} 全军覆没！主将仅以身免。")
            atk["troops"] = 0
            self.battle["over"] = True

    def finish_battle_and_end_turn(self):
        """战斗结束：进入结果展示，然后结算回合 + AI 行动。"""
        self.state = self.ST_RESULT
        self.after_state = "post_battle"

    # ------------------------------------------------------------------
    # 回合结算与 AI
    # ------------------------------------------------------------------
    def end_turn(self):
        """结束一个玩家回合：扣粮、饿兵、AI 行动、判定胜负。"""
        # 1) 所有城池扣粮草
        for c in self.cities:
            cost = max(1, int(c["troops"] * self.bal["food_consume_per_100_troops"] / 100))
            c["food"] -= cost
            # 粮草耗尽：兵力持续衰减
            if c["food"] < 0:
                loss = int(c["troops"] * self.bal["starve_troop_loss_ratio"])
                c["troops"] = max(0, c["troops"] - loss)
                if c["troops"] <= 0:
                    # 城池无人驻守，变为中立，武将下野
                    self.battle_log_if_any(f"【{c['name']}】粮草断绝，军民离散，城池化为无主之地！")
                    c["owner"] = "neutral"
                    c["generals"] = []
                    c["food"] = 500

        # 2) AI 行动
        self.ai_act()

        # 3) 回合数 +1
        self.turn += 1

        # 4) 胜负判定
        self._check_game_over()

    def battle_log_if_any(self, text):
        """结果展示时若已有战斗日志则追加，否则作为全局消息。"""
        if self.state == self.ST_RESULT and self.battle:
            self.battle["log"].append(text)
        else:
            self.message = text

    def ai_act(self):
        """所有非玩家 AI 势力的简化回合行动。"""
        ai_factions = [f for f in CONFIG["factions"] if f != self.player_faction]
        for fac in ai_factions:
            # 每座 AI 城池：粮草充足则自动征兵
            for c in self.cities:
                if c["owner"] != fac:
                    continue
                if c["food"] >= 500 and c["troops"] < 8000:
                    add = random.choice([500, 1000, 1500])
                    c["food"] -= 200
                    c["troops"] += add
            # 随机挑一座 AI 城池进攻相邻弱小目标
            ai_cities = [i for i, c in enumerate(self.cities) if c["owner"] == fac]
            random.shuffle(ai_cities)
            for src_idx in ai_cities[:2]:
                src = self.cities[src_idx]
                if src["troops"] < 2000:
                    continue
                for tgt_idx in self._adjacent(src_idx):
                    tgt = self.cities[tgt_idx]
                    if tgt["owner"] == fac:
                        continue
                    # 兵力优势 >1.5 才进攻
                    if src["troops"] > tgt["troops"] * 1.5:
                        self._ai_battle(src_idx, tgt_idx)
                        break

    def _ai_battle(self, src_idx, tgt_idx):
        """AI 的简化交战。"""
        src = self.cities[src_idx]
        tgt = self.cities[tgt_idx]
        # 简化：直接按兵力比计算双方损失
        atk_loss = int(tgt["troops"] * random.uniform(0.25, 0.4))
        dfn_loss = int(src["troops"] * random.uniform(0.15, 0.3))
        src["troops"] = max(0, src["troops"] - atk_loss)
        tgt["troops"] = max(0, tgt["troops"] - dfn_loss)

        if tgt["troops"] <= 0:
            old_owner = tgt["owner"]
            tgt["owner"] = src["owner"]
            survivor = int(src["troops"] * 0.6)
            src["troops"] -= survivor
            tgt["troops"] = survivor
            # 守将归降新主，继续驻守新城（无需搬动）
            fac_name = CONFIG["factions"][src["owner"]]["name"]
            self.message = f"【{fac_name}】攻陷了 {tgt['name']}！"
        elif src["troops"] <= 0:
            src["troops"] = 0
            self.message = f"【{src['name']}】的进攻全军覆没。"

    def _check_game_over(self):
        """胜负判定。"""
        player_cities = self._player_cities()
        total = len(self.cities)
        if len(player_cities) == total:
            self.state = self.ST_GAMEOVER
            self.game_over_win = True
        elif len(player_cities) == 0:
            self.state = self.ST_GAMEOVER
            self.game_over_win = False

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False

        if event.type != pygame.KEYDOWN:
            return

        key = event.key

        # 全局退出
        if key == pygame.K_q:
            self.running = False
            return

        # ---------- 标题 / 选君主 ----------
        if self.state == self.ST_TITLE:
            if key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.choose_ruler(key - pygame.K_0)
            return

        # ---------- 游戏结束 ----------
        if self.state == self.ST_GAMEOVER:
            if key in (pygame.K_r, pygame.K_RETURN):
                # 重开一局
                self._setup_world()
                self.state = self.ST_TITLE
                self.player_faction = None
                self.turn = 1
                self.message = "按 1 / 2 / 3 选择你的君主，开始乱世征程！"
            return

        # ---------- 大地图 ----------
        if self.state == self.ST_MAP:
            own = self._player_cities()
            if key == pygame.K_LEFT:
                if own:
                    # 向左翻：在己方城池列表里前移
                    cur = self.selected_idx
                    if cur in own:
                        i = own.index(cur)
                        self.selected_idx = own[(i - 1) % len(own)]
                    else:
                        self.selected_idx = own[0]
            elif key == pygame.K_RIGHT:
                if own:
                    cur = self.selected_idx
                    if cur in own:
                        i = own.index(cur)
                        self.selected_idx = own[(i + 1) % len(own)]
                    else:
                        self.selected_idx = own[0]
            elif key == pygame.K_RETURN:
                if self.selected_idx in own:
                    self.current_city_idx = self.selected_idx
                    self.state = self.ST_CITY
            elif key == pygame.K_e:
                self.message = "—— 回合结算中 ——"
                self.end_turn()
                # 回到大地图
                own = self._player_cities()
                if own:
                    self.selected_idx = own[0]
            return

        # ---------- 城市管理菜单 ----------
        if self.state == self.ST_CITY:
            if key == pygame.K_1:
                self.state = self.ST_RECRUIT
            elif key == pygame.K_2:
                self.state = self.ST_SEARCH
            elif key == pygame.K_3:
                self.state = self.ST_MOVE
            elif key == pygame.K_4:
                self.state = self.ST_MOVE_FOOD
            elif key == pygame.K_5:
                self.state = self.ST_ATTACK
            elif key in (pygame.K_ESCAPE, pygame.K_6):
                self.state = self.ST_MAP
            return

        # ---------- 征兵档位 ----------
        if self.state == self.ST_RECRUIT:
            amounts = {pygame.K_1: 1000, pygame.K_2: 2000, pygame.K_3: 3000}
            if key in amounts:
                ok = self.do_recruit(amounts[key])
                if ok:
                    # 征兵消耗一回合
                    self.end_turn()
                self.state = self.ST_MAP
            elif key == pygame.K_ESCAPE:
                self.state = self.ST_CITY
            return

        # ---------- 搜索 ----------
        if self.state == self.ST_SEARCH:
            if key in (pygame.K_1, pygame.K_RETURN, pygame.K_y):
                self.do_search()
                self.end_turn()
                self.state = self.ST_MAP
            elif key == pygame.K_ESCAPE:
                self.state = self.ST_CITY
            return

        # ---------- 选择调兵目标 ----------
        if self.state == self.ST_MOVE:
            own = [i for i in self._adjacent(self.current_city_idx)
                   if self.cities[i]["owner"] == self.player_faction and i != self.current_city_idx]
            # 数字键 1..n 选择目标
            if pygame.K_1 <= key <= pygame.K_9:
                idx_num = key - pygame.K_1
                if idx_num < len(own):
                    self.move_target_idx = own[idx_num]
                    self.state = self.ST_MOVE_AMT
            elif key == pygame.K_ESCAPE:
                self.state = self.ST_CITY
            return

        # ---------- 输入调兵数量 ----------
        if self.state == self.ST_MOVE_AMT:
            amounts = {pygame.K_1: 1000, pygame.K_2: 2000, pygame.K_3: 3000,
                       pygame.K_4: 5000, pygame.K_5: 99999}
            if key in amounts:
                amt = amounts[key]
                self.do_move(self.move_target_idx, amt)
                self.end_turn()
                self.state = self.ST_MAP
            elif key == pygame.K_ESCAPE:
                self.state = self.ST_MOVE
            return

        # ---------- 选择调粮目标 ----------
        if self.state == self.ST_MOVE_FOOD:
            own = [i for i in self._adjacent(self.current_city_idx)
                   if self.cities[i]["owner"] == self.player_faction and i != self.current_city_idx]
            if pygame.K_1 <= key <= pygame.K_9:
                idx_num = key - pygame.K_1
                if idx_num < len(own):
                    self.move_target_idx = own[idx_num]
                    self.state = self.ST_MOVE_FOOD_AMT
            elif key == pygame.K_ESCAPE:
                self.state = self.ST_CITY
            return

        # ---------- 输入调粮数量 ----------
        if self.state == self.ST_MOVE_FOOD_AMT:
            amounts = {pygame.K_1: 1000, pygame.K_2: 2000, pygame.K_3: 3000,
                       pygame.K_4: 5000, pygame.K_5: 99999}
            if key in amounts:
                self.do_move_food(self.move_target_idx, amounts[key])
                self.end_turn()
                self.state = self.ST_MAP
            elif key == pygame.K_ESCAPE:
                self.state = self.ST_MOVE_FOOD
            return

        # ---------- 选择进攻目标 ----------
        if self.state == self.ST_ATTACK:
            targets = [i for i in self._adjacent(self.current_city_idx)
                       if self.cities[i]["owner"] != self.player_faction]
            if pygame.K_1 <= key <= pygame.K_9:
                idx_num = key - pygame.K_1
                if idx_num < len(targets):
                    self.start_battle(targets[idx_num])
            elif key == pygame.K_ESCAPE:
                self.state = self.ST_CITY
            return

        # ---------- 战斗战法 ----------
        if self.state == self.ST_BATTLE:
            if key == pygame.K_1:
                self.battle_engage()
                self.battle_check_result()
            elif key == pygame.K_2:
                self.battle_duel()
                self.battle_check_result()
            elif key == pygame.K_3:
                self.battle_fire()
                self.battle_check_result()
            elif key == pygame.K_4:
                self.battle_retreat()

            if self.battle["over"]:
                self.finish_battle_and_end_turn()
            return

        # ---------- 结果展示 ----------
        if self.state == self.ST_RESULT:
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                # 一回合结束（战斗本身就是一次操作）
                self.end_turn()
                own = self._player_cities()
                if own:
                    self.selected_idx = own[0]
                self.state = self.ST_MAP
                self.battle = None
            return

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def _draw_text(self, text, font, color, x, y, center=False):
        """绘制文字的小工具。"""
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surf, rect)
        return rect

    def draw(self):
        self.screen.fill(self.colors["bg"])

        if self.state == self.ST_TITLE:
            self._draw_title()
        elif self.state == self.ST_GAMEOVER:
            self._draw_map()
            self._draw_gameover()
        else:
            self._draw_map()
            self._draw_side_panel()
            self._draw_bottom_bar()

        pygame.display.flip()

    def _draw_title(self):
        """标题 / 选君主界面。"""
        c = self.colors
        self._draw_text("三国志 · 霸王的大陆", self.font_big, c["highlight"],
                        self.W // 2, 150, center=True)
        self._draw_text("—— 简化复刻版 ——", self.font_mid, c["dim"],
                        self.W // 2, 200, center=True)

        # 三个势力选项
        items = [
            ("1", "曹操", "挟天子以令诸侯，武将如云，谋士如雨"),
            ("2", "刘备", "仁德布于四海，关张辅佐，志在兴复汉室"),
            ("3", "孙权", "据江东以观成败，三世基业，水军雄踞"),
        ]
        y = 300
        for num, name, desc in items:
            self._draw_text(f"按 {num}  【{name}】", self.font_mid, c["highlight"],
                            self.W // 2, y, center=True)
            self._draw_text(desc, self.font_small, c["dim"],
                            self.W // 2, y + 28, center=True)
            y += 70

        self._draw_text("按 Q 退出游戏", self.font_tiny, c["dim"],
                        self.W // 2, self.H - 40, center=True)

    def _draw_map(self):
        """绘制大地图：城市、连线、归属色。"""
        c = self.colors
        # 画相邻连线
        for i, city in enumerate(self.cities):
            for j in self._adjacent(i):
                if j > i:  # 只画一次
                    a, b = self.cities[i], self.cities[j]
                    pygame.draw.line(self.screen, c["line"],
                                     (a["px"], a["py"]), (b["px"], b["py"]), 2)

        # 画城市
        for i, city in enumerate(self.cities):
            color = self._color_of(city)
            r = 34
            pygame.draw.circle(self.screen, color, (city["px"], city["py"]), r)
            # 选中高亮
            if i == self.selected_idx and city["owner"] == self.player_faction:
                pygame.draw.circle(self.screen, c["highlight"],
                                   (city["px"], city["py"]), r + 5, 3)
            # 城市名
            self._draw_text(city["name"], self.font_small, c["text"],
                            city["px"], city["py"] - r - 22, center=True)
            # 兵力
            self._draw_text(f"兵{city['troops']}", self.font_tiny, c["text"],
                            city["px"], city["py"] - 6, center=True)
            # 武将数
            n = len(city["generals"])
            self._draw_text(f"将{n}", self.font_tiny, c["text"],
                            city["px"], city["py"] + 12, center=True)

    def _draw_side_panel(self):
        """右侧信息面板：根据当前状态显示不同内容。"""
        c = self.colors
        panel_rect = pygame.Rect(640, 20, 300, 540)
        pygame.draw.rect(self.screen, c["panel"], panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, c["line"], panel_rect, 2, border_radius=8)

        if self.state == self.ST_MAP:
            self._draw_panel_map()
        elif self.state == self.ST_CITY:
            self._draw_panel_city_menu()
        elif self.state == self.ST_RECRUIT:
            self._draw_panel_recruit()
        elif self.state == self.ST_SEARCH:
            self._draw_panel_search()
        elif self.state == self.ST_MOVE:
            self._draw_panel_move()
        elif self.state == self.ST_MOVE_AMT:
            self._draw_panel_move_amt()
        elif self.state == self.ST_MOVE_FOOD:
            self._draw_panel_move_food()
        elif self.state == self.ST_MOVE_FOOD_AMT:
            self._draw_panel_move_food_amt()
        elif self.state == self.ST_ATTACK:
            self._draw_panel_attack()
        elif self.state == self.ST_BATTLE:
            self._draw_panel_battle()
        elif self.state == self.ST_RESULT:
            self._draw_panel_result()

    def _panel_title(self, text):
        self._draw_text(text, self.font_mid, self.colors["highlight"],
                        655, 35)

    def _draw_panel_map(self):
        """大地图面板：显示当前选中城市详情。"""
        c = self.colors
        city = self.cities[self.selected_idx]
        self._panel_title(f"第 {self.turn} 回合")
        self._draw_text(f"选中：{city['name']}", self.font_mid, c["text"], 655, 75)
        owner = city["owner"]
        owner_name = CONFIG["factions"][owner]["name"] if owner in CONFIG["factions"] else "中立"
        self._draw_text(f"归属：{owner_name}", self.font_small, c["dim"], 655, 105)
        self._draw_text(f"兵力：{city['troops']}", self.font_small, c["text"], 655, 130)
        self._draw_text(f"粮草：{city['food']}", self.font_small, c["text"], 655, 155)
        self._draw_text("武将：", self.font_small, c["text"], 655, 185)
        y = 210
        for gid in city["generals"]:
            g = self.generals[gid]
            self._draw_text(f"  {g['name']}  武{g['force']} 智{g['intel']}",
                            self.font_tiny, c["dim"], 655, y)
            y += 20
        if not city["generals"]:
            self._draw_text("  （无驻守武将）", self.font_tiny, c["dim"], 655, y)

        # 操作提示
        y = 380
        tips = [
            "← / →  切换己方城池",
            "回车    进入城池管理",
            "E       结束本回合",
            "",
            f"己方城池数：{len(self._player_cities())}",
            f"总城池数：{len(self.cities)}",
        ]
        for t in tips:
            self._draw_text(t, self.font_small, c["text"], 655, y)
            y += 26

    def _draw_panel_city_menu(self):
        """城市管理菜单。"""
        c = self.colors
        city = self.cities[self.current_city_idx]
        self._panel_title(f"{city['name']} · 管理")
        self._draw_text(f"兵 {city['troops']}   粮 {city['food']}",
                        self.font_small, c["text"], 655, 75)
        menu = [
            ("1", "征兵", "耗粮补兵（1000兵=200粮）"),
            ("2", "搜索", "寻访在野武将"),
            ("3", "调兵", "调兵至相邻己方城"),
            ("4", "调粮", "调粮至相邻己方城"),
            ("5", "进攻", "攻打相邻敌/中立城"),
            ("6", "返回", "回到大地图"),
        ]
        y = 115
        for num, name, desc in menu:
            self._draw_text(f"按 {num}  {name}", self.font_mid, c["highlight"], 655, y)
            self._draw_text(f"      {desc}", self.font_tiny, c["dim"], 655, y + 24)
            y += 52

    def _draw_panel_recruit(self):
        c = self.colors
        city = self.cities[self.current_city_idx]
        self._panel_title(f"{city['name']} · 征兵")
        self._draw_text(f"当前兵 {city['troops']}   粮 {city['food']}",
                        self.font_small, c["text"], 655, 75)
        options = [
            ("1", "征兵 1000", "耗粮 200"),
            ("2", "征兵 2000", "耗粮 400"),
            ("3", "征兵 3000", "耗粮 600"),
            ("Esc", "取消", ""),
        ]
        y = 130
        for num, name, desc in options:
            self._draw_text(f"按 {num}  {name}", self.font_mid, c["highlight"], 655, y)
            if desc:
                self._draw_text(f"      {desc}", self.font_tiny, c["dim"], 655, y + 26)
            y += 60

    def _draw_panel_search(self):
        c = self.colors
        city = self.cities[self.current_city_idx]
        self._panel_title(f"{city['name']} · 搜索")
        self._draw_text(f"城中潜伏人才：{len(city['hidden'])} 人",
                        self.font_small, c["text"], 655, 75)
        self._draw_text("搜索有概率发现武将。", self.font_small, c["dim"], 655, 110)
        self._draw_text("发现后将自动加入我方。", self.font_small, c["dim"], 655, 135)
        self._draw_text("按 1 开始搜索", self.font_mid, c["highlight"], 655, 190)
        self._draw_text("按 Esc 取消", self.font_small, c["dim"], 655, 230)

    def _draw_panel_move(self):
        c = self.colors
        city = self.cities[self.current_city_idx]
        self._panel_title(f"{city['name']} · 调兵")
        self._draw_text(f"当前兵 {city['troops']}", self.font_small, c["text"], 655, 75)
        own = [i for i in self._adjacent(self.current_city_idx)
               if self.cities[i]["owner"] == self.player_faction and i != self.current_city_idx]
        if not own:
            self._draw_text("没有相邻的己方城池可调。", self.font_small, c["danger"], 655, 120)
            self._draw_text("按 Esc 返回", self.font_small, c["dim"], 655, 160)
            return
        self._draw_text("选择目标城池：", self.font_small, c["dim"], 655, 115)
        y = 150
        for k, idx in enumerate(own):
            t = self.cities[idx]
            self._draw_text(f"按 {k+1}  {t['name']}（兵 {t['troops']}）",
                            self.font_small, c["highlight"], 655, y)
            y += 35
        self._draw_text("按 Esc 返回", self.font_small, c["dim"], 655, y + 10)

    def _draw_panel_move_amt(self):
        c = self.colors
        src = self.cities[self.current_city_idx]
        dst = self.cities[self.move_target_idx]
        self._panel_title(f"调兵至 {dst['name']}")
        self._draw_text(f"【{src['name']}】兵 {src['troops']}",
                        self.font_small, c["text"], 655, 75)
        options = [
            ("1", "调 1000 兵"),
            ("2", "调 2000 兵"),
            ("3", "调 3000 兵"),
            ("4", "调 5000 兵"),
            ("5", "调走所有可动之兵"),
            ("Esc", "取消"),
        ]
        y = 125
        for num, name in options:
            self._draw_text(f"按 {num}  {name}", self.font_mid, c["highlight"], 655, y)
            y += 40

    def _draw_panel_move_food(self):
        """调粮：选择相邻己方目标城。"""
        c = self.colors
        city = self.cities[self.current_city_idx]
        self._panel_title(f"{city['name']} · 调粮")
        self._draw_text(f"当前粮 {city['food']}", self.font_small, c["text"], 655, 75)
        own = [i for i in self._adjacent(self.current_city_idx)
               if self.cities[i]["owner"] == self.player_faction and i != self.current_city_idx]
        if not own:
            self._draw_text("没有相邻的己方城池可调。", self.font_small, c["danger"], 655, 120)
            self._draw_text("按 Esc 返回", self.font_small, c["dim"], 655, 160)
            return
        self._draw_text("选择目标城池：", self.font_small, c["dim"], 655, 115)
        y = 150
        for k, idx in enumerate(own):
            t = self.cities[idx]
            self._draw_text(f"按 {k+1}  {t['name']}（粮 {t['food']}）",
                            self.font_small, c["highlight"], 655, y)
            y += 35
        self._draw_text("按 Esc 返回", self.font_small, c["dim"], 655, y + 10)

    def _draw_panel_move_food_amt(self):
        """调粮数量选择。"""
        c = self.colors
        src = self.cities[self.current_city_idx]
        dst = self.cities[self.move_target_idx]
        self._panel_title(f"调粮至 {dst['name']}")
        self._draw_text(f"【{src['name']}】粮 {src['food']}",
                        self.font_small, c["text"], 655, 75)
        options = [
            ("1", "调 1000 粮"),
            ("2", "调 2000 粮"),
            ("3", "调 3000 粮"),
            ("4", "调 5000 粮"),
            ("5", "调走所有粮草"),
            ("Esc", "取消"),
        ]
        y = 125
        for num, name in options:
            self._draw_text(f"按 {num}  {name}", self.font_mid, c["highlight"], 655, y)
            y += 40

    def _draw_panel_attack(self):
        c = self.colors
        city = self.cities[self.current_city_idx]
        self._panel_title(f"{city['name']} · 进攻")
        self._draw_text(f"当前兵 {city['troops']}", self.font_small, c["text"], 655, 75)
        targets = [i for i in self._adjacent(self.current_city_idx)
                   if self.cities[i]["owner"] != self.player_faction]
        if not targets:
            self._draw_text("没有相邻的敌方/中立城池。", self.font_small, c["danger"], 655, 120)
            self._draw_text("按 Esc 返回", self.font_small, c["dim"], 655, 160)
            return
        self._draw_text("选择进攻目标：", self.font_small, c["dim"], 655, 115)
        y = 150
        for k, idx in enumerate(targets):
            t = self.cities[idx]
            owner_name = CONFIG["factions"][t["owner"]]["name"] if t["owner"] in CONFIG["factions"] else "中立"
            self._draw_text(f"按 {k+1}  {t['name']}（{owner_name}，兵 {t['troops']}）",
                            self.font_small, c["highlight"], 655, y)
            y += 35
        self._draw_text("按 Esc 返回", self.font_small, c["dim"], 655, y + 10)

    def _draw_panel_battle(self):
        """战斗面板。"""
        c = self.colors
        atk = self.cities[self.battle["attacker_idx"]]
        dfn = self.cities[self.battle["defender_idx"]]
        atk_gen = self._top_general(atk) or {"name": "无名", "force": 0, "intel": 0}
        dfn_gen = self._top_general(dfn) or {"name": "无名", "force": 0, "intel": 0}

        self._panel_title("—— 战 斗 ——")
        # 攻方
        self._draw_text(f"【攻】{atk['name']}", self.font_mid, self._color_of(atk), 655, 75)
        self._draw_text(f"  兵 {atk['troops']}   主将 {atk_gen['name']}",
                        self.font_small, c["text"], 655, 105)
        self._draw_text(f"  武{atk_gen['force']} 智{atk_gen['intel']}",
                        self.font_tiny, c["dim"], 655, 128)
        # 守方
        self._draw_text(f"【守】{dfn['name']}", self.font_mid, self._color_of(dfn), 655, 165)
        self._draw_text(f"  兵 {dfn['troops']}   主将 {dfn_gen['name']}",
                        self.font_small, c["text"], 655, 195)
        self._draw_text(f"  武{dfn_gen['force']} 智{dfn_gen['intel']}",
                        self.font_tiny, c["dim"], 655, 218)

        # 战法菜单
        menu = [
            ("1", "交战", "双方按武力互损"),
            ("2", "斗将", "主将单挑定胜败"),
            ("3", "火攻", "依智力，成功重创敌军"),
            ("4", "撤退", "保留七成兵力回城"),
        ]
        y = 260
        for num, name, desc in menu:
            self._draw_text(f"按 {num}  {name}", self.font_mid, c["highlight"], 655, y)
            self._draw_text(f"      {desc}", self.font_tiny, c["dim"], 655, y + 24)
            y += 50

        # 战斗日志（最近 3 条）
        log_y = 470
        self._draw_text("战报：", self.font_small, c["dim"], 655, log_y)
        for line in self.battle["log"][-2:]:
            self._draw_text(line, self.font_tiny, c["text"], 655, log_y + 22)
            log_y += 18

    def _draw_panel_result(self):
        """战斗结果面板。"""
        c = self.colors
        self._panel_title("—— 战 果 ——")
        y = 80
        for line in self.battle["log"]:
            # 长行简单截断
            text = line if len(line) < 28 else line[:27] + "…"
            self._draw_text(text, self.font_small, c["text"], 655, y)
            y += 28
            if y > 480:
                break
        self._draw_text("按 回车 继续…", self.font_mid, c["highlight"], 655, 510)

    def _draw_bottom_bar(self):
        """底部消息栏。"""
        c = self.colors
        rect = pygame.Rect(20, 575, 600, 50)
        pygame.draw.rect(self.screen, c["panel_dark"], rect, border_radius=6)
        # 长消息截断
        msg = self.message if len(self.message) < 50 else self.message[:48] + "…"
        self._draw_text(msg, self.font_small, c["text"], 30, 590)

    def _draw_gameover(self):
        """胜负结算浮层。"""
        c = self.colors
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        if getattr(self, "game_over_win", False):
            title = "★ 统一天下！你赢了！★"
            color = c["highlight"]
        else:
            title = "✗ 霸业成空，你失败了 ✗"
            color = c["danger"]
        self._draw_text(title, self.font_big, color, self.W // 2, self.H // 2 - 40, center=True)
        self._draw_text(f"共坚持 {self.turn} 回合", self.font_mid, c["text"],
                        self.W // 2, self.H // 2 + 20, center=True)
        self._draw_text("按 R 或 回车 重新开始", self.font_mid, c["dim"],
                        self.W // 2, self.H // 2 + 70, center=True)

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.draw()
            self.clock.tick(30)
        pygame.quit()


# ============================================================================
# 四、程序入口
# ============================================================================
if __name__ == "__main__":
    game = ThreeKingdoms()
    game.run()
