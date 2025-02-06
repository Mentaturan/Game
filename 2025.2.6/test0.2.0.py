import random
import tkinter as tk
from enum import Enum


# 定义卡牌属性
class Attribute(Enum):
    YIN = "阴"
    DARK = "暗"
    LIGHT = "光"
    BLANK = "空白"

# 定义卡牌类
class Card:
    def __init__(self, name, attribute, value, cost, effects=None):
        self.name = name
        self.attribute = attribute
        self.value = value
        self.cost = cost
        self.effects = effects or {}

    def __repr__(self):
        return f"{self.name} ({self.attribute.value})"

# 定义牌堆类
class Deck:
    def __init__(self, cards):
        self.draw_pile = cards.copy()
        self.discard_pile = []
        random.shuffle(self.draw_pile)
    
    def draw(self, num):
        drawn = []
        for _ in range(num):
            if not self.draw_pile:
                self.draw_pile = self.discard_pile
                self.discard_pile = []
                random.shuffle(self.draw_pile)
                if not self.draw_pile:
                    break
            drawn.append(self.draw_pile.pop())
        return drawn
    
    def discard_card(self, card):
        self.discard_pile.append(card)
    
    def reinsert_card(self, card):
        """将打出的卡牌重新放入牌堆"""
        self.draw_pile.append(card)
        random.shuffle(self.draw_pile)  # 打乱牌堆，增加随机性

# 定义玩家类
class Player:
    def __init__(self, name, max_health=30, max_energy=10, energy_per_turn=3):
        self.name = name
        self.max_health = max_health
        self.health = max_health
        self.energy = 0
        self.max_energy = max_energy
        self.energy_per_turn = energy_per_turn
        self.deck = None
        self.hand = []

    def start_turn(self):
        self.energy = min(self.energy + self.energy_per_turn, self.max_energy)
    
    def play_card(self, index):
        if 0 <= index < len(self.hand):
            card = self.hand.pop(index)
            if self.energy >= card.cost:
                self.energy -= card.cost
                self.deck.reinsert_card(card)  # 打出卡牌后重新放入牌堆
                return card
            self.hand.insert(index, card)
        return None
    
    def draw_card(self):
        card = self.deck.draw(1)
        self.hand.append(card[0])

class NPC(Player):
    def choose_card(self):
        valid_indices = [i for i, card in enumerate(self.hand) if card.cost <= self.energy]
        return random.choice(valid_indices) if valid_indices else None
    
    def play_card(self, index):
        if 0 <= index < len(self.hand):
            card = self.hand.pop(index)
            if self.energy >= card.cost:
                self.energy -= card.cost
                self.deck.reinsert_card(card)  # 打出卡牌后重新放入牌堆
                return card
        return None

# 定义游戏类
class Game:
    RESTRAINT = {
        Attribute.YIN: Attribute.DARK,
        Attribute.DARK: Attribute.LIGHT,
        Attribute.LIGHT: Attribute.YIN,
        Attribute.BLANK: None
    }

    def __init__(self, player_deck, npc_deck):
        self.player = Player("玩家")
        self.npc = NPC("NPC")
        self.player.deck = Deck(player_deck)
        self.npc.deck = Deck(npc_deck)
        self.init_draw()

        # 创建 Tkinter 界面
        self.root = tk.Tk()
        self.root.title("卡牌游戏")

        # 状态信息
        self.status_label = tk.Label(self.root, text="", font=("Arial", 14))
        self.status_label.pack()

        # 上回合结果
        self.result_label = tk.Label(self.root, text="上回合结果：", font=("Arial", 12))
        self.result_label.pack()

        # 玩家手牌按钮
        self.card_buttons = []
        self.update_hand_buttons()

        # 启动游戏
        self.start_turn()

    def init_draw(self):
        self.player.hand = self.player.deck.draw(4)
        self.npc.hand = self.npc.deck.draw(4)

    def calculate_restraint(self, a1, a2):
        if self.RESTRAINT[a1] == a2:
            return 1  # a1克制a2
        if self.RESTRAINT[a2] == a1:
            return -1  # a2克制a1
        return 0

    def battle(self, player_card, npc_card):
        restraint = self.calculate_restraint(player_card.attribute, npc_card.attribute)
        pv, nv = player_card.value, npc_card.value
        
        if restraint == 1:
            nv = nv // 2
        elif restraint == -1:
            pv = pv // 2
        
        pv += player_card.effects.get('damage_boost', 0)
        nv += npc_card.effects.get('damage_boost', 0)
        
        return pv, nv

    def display_status(self):
        return f"🏥 玩家血量：{self.player.health}/{self.player.max_health}  🔋 能量：{self.player.energy}/{self.player.max_energy}\n" \
               f"🏥 NPC血量：{self.npc.health}/{self.npc.max_health}  🔋 能量：{self.npc.energy}/{self.npc.max_energy}"

    def update_hand_buttons(self):
        for button in self.card_buttons:
            button.destroy()
        self.card_buttons.clear()

        for i, card in enumerate(self.player.hand):
            button = tk.Button(self.root, text=f"{card.name} ({card.cost})", width=20, command=lambda i=i: self.play_card(i))
            button.pack(pady=5)
            self.card_buttons.append(button)

    def play_card(self, index):
        player_card = self.player.play_card(index)
        if player_card:
            self.npc_turn(player_card)

    def npc_turn(self, player_card):
        npc_choice = self.npc.choose_card()
        npc_card = self.npc.play_card(npc_choice) if npc_choice is not None else None

        if npc_card:
            pv, nv = self.battle(player_card, npc_card)
            result_text = f"玩家出牌：{player_card.name}（{pv})\nNPC出牌：{npc_card.name}（{nv})"
            if pv > nv:
                self.npc.health -= pv - nv
                result_text += "\n🎉 玩家胜出！"
            elif nv > pv:
                self.player.health -= nv - pv
                result_text += "\n💀 NPC胜出！"
            else:
                result_text += "\n⚖️ 平局！"
        else:
            self.npc.health -= 5
            result_text = "🤖 NPC无法出牌，玩家自动获胜！"

        self.update_result(result_text)
        self.start_turn()

    def start_turn(self):
        self.player.start_turn()
        self.npc.start_turn()

        # 玩家和 NPC 抽卡
        self.player.draw_card()
        self.npc.draw_card()

        self.update_game_status()
        self.update_hand_buttons()

    def update_game_status(self):
        self.status_label.config(text=self.display_status())

    def update_result(self, result):
        self.result_label.config(text=f"上回合结果：\n{result}")

    def start_gui(self):
        self.root.mainloop()

# 卡牌配置
base_cards = [
    Card("阴之爪", Attribute.YIN, 8, 3, {'damage_boost': 2}),
    Card("暗影球", Attribute.DARK, 6, 2, {'heal': 3}),
    Card("光之矛", Attribute.LIGHT, 7, 4, {'energy_gain': 2}),
    Card("虚无盾", Attribute.BLANK, 5, 1),
    Card("阴阳玉", Attribute.YIN, 6, 3, {'damage_boost': 1}),
    Card("暗夜突袭", Attribute.DARK, 9, 5),
    Card("圣光治愈", Attribute.LIGHT, 4, 2, {'heal': 5}),
    Card("空白屏障", Attribute.BLANK, 7, 3),
]

# 生成玩家和NPC的牌组
player_deck = random.sample(base_cards * 2, 10)
npc_deck = random.sample(base_cards * 2, 10)

# 启动游戏
game = Game(player_deck, npc_deck)
game.start_gui()
