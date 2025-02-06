import random
import tkinter as tk
from enum import Enum
import time

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
        self.draw_pile.append(card)
        random.shuffle(self.draw_pile)

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
    
    def can_play_any(self):
        return any(card.cost <= self.energy for card in self.hand)
    
    def play_card(self, index):
        if 0 <= index < len(self.hand):
            card = self.hand.pop(index)
            if self.energy >= card.cost:
                self.energy -= card.cost
                self.deck.reinsert_card(card)
                return card
            self.hand.insert(index, card)
        return None
    
    def draw_card(self):
        card = self.deck.draw(1)
        if card:
            self.hand.append(card[0])

class NPC(Player):
    def choose_card(self):
        valid_indices = [i for i, card in enumerate(self.hand) if card.cost <= self.energy]
        return random.choice(valid_indices) if valid_indices else None

# 定义游戏类
class Game:
    RESTRAINT = {
        Attribute.YIN: Attribute.DARK,
        Attribute.DARK: Attribute.LIGHT,
        Attribute.LIGHT: Attribute.YIN,
        Attribute.BLANK: None
    }

    def __init__(self):
        self.player = Player("玩家")
        self.npc = NPC("NPC")
        self.player.deck = Deck(self.generate_random_deck())
        self.npc.deck = Deck(self.generate_random_deck())
        self.init_draw()

        self.root = tk.Tk()
        self.root.title("卡牌游戏")
        self.turn_delay = 200  # 0.2秒延迟

        # GUI组件
        self.status_label = tk.Label(self.root, text="", font=("Arial", 14))
        self.status_label.pack()
        
        self.result_label = tk.Label(self.root, text="上回合结果：", font=("Arial", 12))
        self.result_label.pack()
        
        self.skip_button = tk.Button(self.root, text="跳过回合", command=self.skip_turn)
        self.skip_button.pack(pady=5)
        
        self.card_buttons = []
        self.update_hand_buttons()
        self.start_turn()

    def generate_random_deck(self):
        """生成包含平衡卡牌的随机牌组"""
        balanced_cards = [
            Card("阴之爪", Attribute.YIN, 8, 3, {'damage_boost': 2}),
            Card("暗影球", Attribute.DARK, 6, 2, {'heal': 3}),
            Card("光之矛", Attribute.LIGHT, 7, 4, {'energy_gain': 2}),
            Card("虚无盾", Attribute.BLANK, 5, 1),
            Card("阴阳玉", Attribute.YIN, 6, 3, {'damage_boost': 1}),
            Card("暗夜突袭", Attribute.DARK, 9, 5),
            Card("圣光治愈", Attribute.LIGHT, 4, 2, {'heal': 5}),
            Card("空白屏障", Attribute.BLANK, 7, 3),
            # 新增平衡卡牌
            Card("暗影步", Attribute.DARK, 5, 2, {'energy_gain': 1}),
            Card("光明祝福", Attribute.LIGHT, 6, 3, {'heal': 4}),
            Card("阴云笼罩", Attribute.YIN, 7, 4, {'damage_boost': 3}),
            Card("虚空吞噬", Attribute.BLANK, 8, 5),
        ]
        return random.sample(balanced_cards * 2, 15)

    def init_draw(self):
        self.player.hand = self.player.deck.draw(4)
        self.npc.hand = self.npc.deck.draw(4)

    def calculate_restraint(self, a1, a2):
        if self.RESTRAINT[a1] == a2:
            return 1
        if self.RESTRAINT[a2] == a1:
            return -1
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

    def update_hand_buttons(self):
        for btn in self.card_buttons:
            btn.destroy()
        self.card_buttons.clear()

        for i, card in enumerate(self.player.hand):
            state = tk.NORMAL if card.cost <= self.player.energy else tk.DISABLED
            btn = tk.Button(
                self.root, 
                text=f"{card.name} (费:{card.cost} 攻:{card.value})",
                width=25,
                state=state,
                command=lambda i=i: self.play_card(i)
            )
            btn.pack(pady=2)
            self.card_buttons.append(btn)

    def play_card(self, index):
        self.toggle_buttons(False)
        player_card = self.player.play_card(index)
        if player_card:
            self.root.after(200, lambda: self.npc_turn(player_card))
        else:
            self.toggle_buttons(True)

    def npc_turn(self, player_card):
        npc_choice = self.npc.choose_card()
        npc_card = self.npc.play_card(npc_choice) if npc_choice is not None else None

        result_text = ""
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
            self.npc.health -= 3
            result_text = "🤖 NPC无法出牌，扣除3点生命值"

        self.update_result(result_text)
        self.check_game_over()
        self.root.after(self.turn_delay, self.start_turn)

    def skip_turn(self):
        self.toggle_buttons(False)
        self.update_result("玩家跳过回合")
        self.root.after(200, self.npc_auto_play)

    def npc_auto_play(self):
        if self.npc.can_play_any():
            npc_choice = self.npc.choose_card()
            npc_card = self.npc.play_card(npc_choice)
            if npc_card:
                self.player.health -= npc_card.value
                self.update_result(f"NPC自动出牌：{npc_card.name}（{npc_card.value}伤害）")
        else:
            self.update_result("NPC跳过回合")
        self.check_game_over()
        self.root.after(self.turn_delay, self.start_turn)

    def toggle_buttons(self, enable):
        state = tk.NORMAL if enable else tk.DISABLED
        for btn in self.card_buttons:
            btn.config(state=state)
        self.skip_button.config(state=state)

    def start_turn(self):
        self.player.start_turn()
        self.npc.start_turn()
        
        self.player.draw_card()
        self.npc.draw_card()
        
        self.update_status()
        self.update_hand_buttons()
        self.toggle_buttons(True)
        
        if not self.player.can_play_any():
            self.skip_button.config(text="跳过回合（无法出牌）", state=tk.DISABLED)
        else:
            self.skip_button.config(text="跳过回合", state=tk.NORMAL)

    def update_status(self):
        status = f"🏥 玩家：{self.player.health}  🔋 {self.player.energy}/{self.player.max_energy}\n"
        status += f"🏥 NPC：{self.npc.health}  🔋 {self.npc.energy}/{self.npc.max_energy}"
        self.status_label.config(text=status)

    def update_result(self, text):
        self.result_label.config(text=f"上回合结果：\n{text}")

    def check_game_over(self):
        if self.player.health <= 0 or self.npc.health <= 0:
            winner = "玩家" if self.npc.health <= 0 else "NPC"
            self.status_label.config(text=f"游戏结束！{winner}获胜！")
            self.toggle_buttons(False)
            self.skip_button.config(state=tk.DISABLED)

    def start_gui(self):
        self.root.mainloop()

if __name__ == "__main__":
    game = Game()
    game.start_gui()
