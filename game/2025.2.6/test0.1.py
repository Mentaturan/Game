import random
from enum import Enum

class Attribute(Enum):
    YIN = "阴"
    DARK = "暗"
    LIGHT = "光"
    BLANK = "空白"

class Card:
    def __init__(self, name, attribute, value, cost, effects=None):
        self.name = name
        self.attribute = attribute
        self.value = value
        self.cost = cost
        self.effects = effects or {}

    def __repr__(self):
        return f"{self.name} ({self.attribute.value})"

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
            if self.draw_pile:
                drawn.append(self.draw_pile.pop())
        return drawn
    
    def discard_card(self, card):
        self.discard_pile.append(card)

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
                return card
            self.hand.insert(index, card)
        return None

class NPC(Player):
    def choose_card(self):
        valid_indices = [i for i, card in enumerate(self.hand) if card.cost <= self.energy]
        return random.choice(valid_indices) if valid_indices else None

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
    
    def init_draw(self):
        self.player.hand = self.player.deck.draw(4)
        self.npc.hand = self.npc.deck.draw(4)
    
    def calculate_restraint(self, a1, a2):
        if self.RESTRAINT[a1] == a2:
            return 1  # a1克制a2
        if self.RESTRAINT[a2] == a1:
            return -1  # a2克制a1
        return 0
    
    def apply_effects(self, card, target, opponent):
        # 应用卡牌效果
        if 'heal' in card.effects:
            target.health = min(target.max_health, target.health + card.effects['heal'])
        if 'energy_gain' in card.effects:
            target.energy = min(target.max_energy, target.energy + card.effects['energy_gain'])
        if 'damage_boost' in card.effects:
            pass  # 已在数值计算中处理
    
    def battle(self, player_card, npc_card):
        # 计算克制关系
        restraint = self.calculate_restraint(player_card.attribute, npc_card.attribute)
        pv, nv = player_card.value, npc_card.value
        
        # 处理克制
        if restraint == 1:
            nv = nv // 2
        elif restraint == -1:
            pv = pv // 2
        
        # 处理数值修正
        pv += player_card.effects.get('damage_boost', 0)
        nv += npc_card.effects.get('damage_boost', 0)
        
        return pv, nv
    
    def play_round(self):
        # 玩家出牌
        print("\n当前状态：")
        print(f"玩家血量：{self.player.health} 能量：{self.player.energy}/{self.player.max_energy}")
        print(f"NPC血量：{self.npc.health} 能量：{self.npc.energy}/{self.npc.max_energy}")
        
        # 玩家操作
        while True:
            print("\n你的手牌：")
            for i, card in enumerate(self.player.hand):
                print(f"{i}: {card.name} ({card.attribute.value}) 数值：{card.value} 消耗：{card.cost}")
            try:
                choice = int(input("请选择要出的卡牌："))
                player_card = self.player.play_card(choice)
                if player_card:
                    break
                print("无效选择或能量不足！")
            except (ValueError, IndexError):
                print("请输入有效数字！")
        
        # NPC出牌
        npc_choice = self.npc.choose_card()
        npc_card = self.npc.play_card(npc_choice) if npc_choice is not None else None
        
        # 处理出牌结果
        if npc_card:
            pv, nv = self.battle(player_card, npc_card)
            print(f"\n玩家出牌：{player_card.name} → 最终数值：{pv}")
            print(f"NPC出牌：{npc_card.name} → 最终数值：{nv}")
            
            # 计算伤害
            if pv > nv:
                damage = pv - nv
                self.npc.health -= damage
                print(f"玩家胜出！NPC受到{damage}点伤害")
            elif nv > pv:
                damage = nv - pv
                self.player.health -= damage
                print(f"NPC胜出！玩家受到{damage}点伤害")
            else:
                print("双方平局！")
            
            # 应用效果
            self.apply_effects(player_card, self.player, self.npc)
            self.apply_effects(npc_card, self.npc, self.player)
            
            # 弃牌
            self.player.deck.discard_card(player_card)
            self.npc.deck.discard_card(npc_card)
        else:
            print("NPC无法出牌！玩家自动获胜！")
            self.npc.health -= 5
        
        # 抽牌
        self.player.hand += self.player.deck.draw(1)
        self.npc.hand += self.npc.deck.draw(1)
    
    def check_winner(self):
        if self.player.health <= 0:
            print("游戏结束！NPC获胜！")
            return True
        if self.npc.health <= 0:
            print("游戏结束！玩家获胜！")
            return True
        return False
    
    def start(self):
        round_num = 1
        while True:
            print(f"\n===== 第 {round_num} 回合 =====")
            self.player.start_turn()
            self.npc.start_turn()
            self.play_round()
            if self.check_winner():
                break
            round_num += 1

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

if __name__ == "__main__":
    random.seed(42)
    player_deck = random.sample(base_cards * 2, 10)
    npc_deck = random.sample(base_cards * 2, 10)
