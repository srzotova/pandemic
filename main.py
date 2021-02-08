import csv
import pygame
import os
import sys
import queue
from random import shuffle
from pygame import draw

# параметры игровых механик
MAK_CONTAMINATION = 4
INFECTION_CARD_NAME = 'Усиление зарожаемости'
INFECTION_CARDS_COUNT = 6
HOW_TAKE = 2
MAX_OUTBREAKS_COUNT = 8
INFECTIVITY = [2, 2, 2, 3, 3, 4, 4]
VIRUS_COUNT = 4
VIRUS_UNITS_COUNT = 24
START_GROUPS_SIZE = 3
MAX_CARDS_IN_HAND = 7
PLAYER_ACTIONS = 4
START_PLAYERS_CARDS = 6
START = 'Атланта'
# параметры победителя
GAME_WIN = False
PLAYERS_WIN = True
# параметры рисовки
IMAGE_W = 1357
IMAGE_H = 628
PLAYER_COLORS = [(107, 142, 35), (255, 192, 203), (0, 206, 209), (192, 192, 192), (138, 43, 226), (255, 215, 0)]
PLAYERS_INDENT = [(-8, -10), (3, 1), (-8, 1), (3, -10)]
VIRUS_COLORS = [(10, 10, 10), (0, 10, 245), (255, 255, 0), (255, 0, 0)]
CONTAMINATION_COLOR = (0, 100, 0)
TEXT_COLOR = (0, 0, 0)
STATION_COLOR = (225, 255, 255)
CITY_RADIUS = 8
BACKGROUND_COLOR = (112, 146, 190)
BUTTONS_CORDS = [(50, 470), (122, 470), (50, 542), (122, 542), (225, 600)]
BUTTON_RADIUS = 35
# игровые роли
ROLE_DISPATCHER = 1
ROLE_DOCTOR = 2
ROLE_SCIENTIST = 3
ROLE_RESEARCHER = 4
ROLE_ENGINEER = 5
ROLE_QUARANTINE_SPECIALIST = 6
ROLES = ['Диспетчер', 'Доктор', 'Ученый', 'Исследователь', 'Инженер', 'Специалист по карантину']


def load_cities():
    cities = []
    with open('cities.csv', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for record in reader:
            num = int(record[0]) - 1
            name = record[1]
            cords = (int(record[2]), int(record[3]))
            virus = int(record[4]) - 1
            cities.append((num, name, cords, virus))
    return cities


def load_cities_graph():
    graph = []
    with open('graph.csv', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for record in reader:
            c_1 = int(record[0]) - 1
            c_2 = int(record[1]) - 1
            graph.append((c_1, c_2))
    return graph


def load_image(name, colorkey=None):
    if not os.path.isfile(name):
        print(f"Файл с изображением '{name}' не найден")
        sys.exit()
    image = pygame.image.load(name)
    return image


class Town:
    def __init__(self, num, name, cords, virus):
        self.num = num
        self.name = name
        self.cords = cords
        self.virus = virus

        self.players = set()
        self.station = False
        if name == START:
            self.station = True
        self.contamination = 0
        self.neighbors = set()

    def take_num(self):
        return self.num

    def take_name(self):
        return self.name

    def take_cords(self):
        return self.cords

    def take_virus(self):
        return self.virus

    def add_player(self, player):
        self.players.add(player)

    def del_player(self, player):
        self.players.discard(player)

    def is_station(self):
        return self.station

    def build_station(self):
        self.station = True

    def infection(self):
        if self.contamination == MAK_CONTAMINATION:
            return False
        self.contamination += 1
        return True

    def medication(self):
        if self.contamination == 0:
            return False
        self.contamination -= 1
        return True

    def nullify_contamination(self):
        self.contamination = 0

    def take_contamination(self):
        return self.contamination

    def take_players(self):
        return self.players

    def add_neighbor(self, city):
        self.neighbors.add(city)

    def take_neighbors(self):
        return self.neighbors


class Player:
    def __init__(self, num, role, location):
        self.num = num
        self.role = role
        self.location = location
        self.hand = []

    def take_location(self):
        return self.location

    def set_location(self, location):
        self.location = location

    def take_role(self):
        return self.role

    def take_num(self):
        return self.num

    def add_card(self, card):
        self.hand.append(card)

    def del_card(self, card):
        if card not in self.hand:
            return False
        index = self.hand.index(card)
        del self.hand[index]
        return True

    def take_hand(self):
        return self.hand

    def check_combination(self, cards):
        hand_copy = self.hand.copy()
        for card in cards:
            index = hand_copy.index(card)
            if index == -1:
                return False
            del hand_copy[index]
        return True


class Game:
    def __init__(self, players):
        self.players = []
        self.cities = dict()
        cities_list = load_cities()
        for city in cities_list:
            num, name, cords, virus = city
            self.cities[name] = Town(num, name, cords, virus)
        for i in range(len(players)):
            self.players.append(Player(i, players[i], self.cities[START]))
        self.cities_graph = []
        for c_1, c_2 in load_cities_graph():
            name_1, name_2 = cities_list[c_1][1], cities_list[c_2][1]
            self.cities[name_1].add_neighbor(self.cities[name_2])
            self.cities[name_2].add_neighbor(self.cities[name_1])
            self.cities_graph.append((self.cities[name_1], self.cities[name_2]))

        cities_names = [city[1] for city in cities_list]
        cards = cities_names.copy()
        shuffle(cards)
        start_cards = cards[:(START_PLAYERS_CARDS - len(self.players)) * len(players)]
        cards = cards[(START_PLAYERS_CARDS - len(self.players)) * len(players):]
        stack_len = len(cards) // INFECTION_CARDS_COUNT
        stacks = []
        for _ in range(INFECTION_CARDS_COUNT):
            stacks.append(cards[:stack_len])
            cards = cards[stack_len:]
        stacks[-1] += cards
        cards = start_cards
        for stack in stacks:
            stack.append(INFECTION_CARD_NAME)
            shuffle(stack)
            cards += stack
        self.players_pack = iter(cards.copy())
        cards = cities_names * (MAK_CONTAMINATION + 1)
        shuffle(cards)
        while len(set(cards[:3 * START_GROUPS_SIZE])) != 3 * START_GROUPS_SIZE:
            shuffle(cards)
        self.infection_pack = iter(cards.copy())
        self.complete_pack = cards

        for player in self.players:
            for _ in range(START_PLAYERS_CARDS - len(self.players)):
                player.add_card(self.open_players_card())

        self.scale_outbreaks = 0
        self.scale_infectivity = 0
        self.vaccines = [False] * VIRUS_COUNT
        self.viruses_units = [VIRUS_UNITS_COUNT] * VIRUS_COUNT
        self.victory_over_viruses = [False] * VIRUS_COUNT
        self.game_over = False
        self.winner = None
        self.last_infections = []

        for units_count in range(1, 4):
            for i in range(START_GROUPS_SIZE):
                card = self.open_infections_card()
                for _ in range(units_count):
                    self.last_infections.append(card)
                    self.infection(self.cities[card])

        self.remaining_actions = PLAYER_ACTIONS
        self.current_player = self.players[0]

    def take_cities_list(self):
        return self.cities.values()

    def take_cities_graph(self):
        return self.cities_graph

    def get_element(self, coord):
        x, y = coord
        for city in self.cities.values():
            cords = city.take_cords()
            dist = ((cords[0] - x) ** 2 + (cords[1] - y) ** 2) ** 0.5
            if dist <= CITY_RADIUS:
                return city

    def infection(self, city):
        if self.victory_over_viruses[city.take_virus()]:
            return True
        if self.viruses_units[city.take_virus()] == 0:
            return True
        quarantine_specialist = self.find_role(ROLE_QUARANTINE_SPECIALIST)
        if quarantine_specialist:
            if city == quarantine_specialist.take_location() or \
                    city in quarantine_specialist.take_neighbors():
                return True
        if city.infection():
            self.viruses_units[city.take_virus()] -= 1
            if self.viruses_units[city.take_virus()] == 0:
                self.game_over = True
                self.winner = GAME_WIN
            return True
        return False

    def medication(self, player, city):
        if player.take_role() == ROLE_DOCTOR or self.vaccines[city.take_virus()]:
            if city.take_contamination() > 0:
                self.viruses_units[city.take_virus()] += city.take_contamination()
                city.nullify_contamination()
                if self.vaccines[city.take_virus()] and \
                        self.viruses_units[city.take_virus()] == VIRUS_UNITS_COUNT:
                    self.victory_over_viruses[city.take_virus()] = True
                return True
            return False
        if city.medication():
            self.viruses_units[city.take_virus()] += 1
            if self.vaccines[city.take_virus()] and \
                    self.viruses_units[city.take_virus()] == VIRUS_UNITS_COUNT:
                self.victory_over_viruses[city.take_virus()] = True
            return True
        return False

    def outbreak(self, start_city):
        self.scale_outbreaks += 1
        infected = queue.Queue()
        infected.put(start_city)
        used = [False] * len(self.cities.values())
        used[start_city.take_num()] = True
        while not infected.empty():
            city = infected.get()
            for neig in city.take_neighbors():
                if not used[neig.take_num()]:
                    used[neig.take_num()] = True
                    if not self.infection(neig):
                        self.scale_outbreaks += 1
                        infected.put(neig)
        if self.scale_outbreaks >= MAX_OUTBREAKS_COUNT:
            self.game_over = True
            self.winner = GAME_WIN

    def move_player(self, player, city):
        player.take_location().del_player(player)
        city.add_player(player)
        player.set_location(city)
        if player.take_role == ROLE_DOCTOR and self.vaccines[city.take_virus()]:
            self.medication(player, city)

    def open_players_card(self):
        if self.players_pack:
            return next(self.players_pack)
        return None

    def open_infections_card(self):
        if self.infection_pack:
            return next(self.infection_pack)
        cards = self.complete_pack.copy()
        shuffle(cards)
        self.infection_pack = iter(cards)
        return next(self.infection_pack)

    def receiving_cards(self, player):
        for _ in range(HOW_TAKE):
            if len(player.take_hand()) == MAX_CARDS_IN_HAND:
                break
            card = self.open_players_card()
            if card is None:
                self.game_over = True
                self.winner = GAME_WIN
            if card == INFECTION_CARD_NAME:
                self.scale_infectivity += 1
            else:
                player.add_card(card)

    def transfer_card(self, player_from, player_to, card):
        if card not in player_from.take_hand():
            return False
        if player_to.take_location() == player_from.take_location() or \
                player_to.take_role() == ROLE_RESEARCHER or player_from.take_role() == ROLE_RESEARCHER:
            player_from.del_card(card)
            player_to.add_card(card)
            return True
        return False

    def create_vaccine(self, player, virus, cards):
        if self.vaccines[virus]:
            return False
        if INFECTION_CARD_NAME in cards:
            return False
        if player.take_role() == ROLE_SCIENTIST and len(cards) >= 4:
            cards = cards[:4]
        elif len(cards) >= 5:
            cards = cards[:5]
        else:
            return False
        if player.check_combination(cards) and \
                all(map(lambda card: self.cities[card].virus == virus, cards)):
            for card in cards:
                player.del_card(card)
            self.vaccines[virus] = True
            doctor = self.find_role(ROLE_DOCTOR)
            if doctor is not None:
                self.medication(doctor, doctor.take_location())
            return True
        return False

    def simple_moving(self, player, city):
        if city in player.take_location().take_neighbors():
            self.move_player(player, city)
            return True
        return False

    def air_moving(self, player, city, card):
        if player.take_location().take_name() == card:
            self.move_player(player, city)
            player.del_card(card)
        elif city.take_name() == card:
            self.move_player(player, city)
            player.del_card(card)
        else:
            return False
        return True

    def work_moving(self, player, city):
        if player.take_location().is_station() and city.is_station():
            self.move_player(player, city)
            return True
        return False

    def build_station(self, player, card):
        if player.take_role() == ROLE_ENGINEER:
            if not player.location().is_station():
                player.location().build_station()
                return True
            return False
        if player.take_location().take_name() == card.take_name() and not player.take_location().is_station():
            player.take_location().build_station()
            player.del_card(card)
            return True
        return False

    def fighting_virus(self, player):
        # print(player.take_location().take_contamination())
        if player.take_location().take_contamination() > 0:
            self.medication(player, player.take_location())
            return True
        return False

    def action_with_city(self, player, city, card=None):
        if player.take_location().take_cords() == city.take_cords():
            return self.fighting_virus(player)
        if self.simple_moving(player, city):
            return True
        if self.work_moving(player, city):
            return True
        if card is not None:
            return self.air_moving(player, city, card)
        return False

    def dispatcher_action(self, player, city, card=None):
        if self.current_player.take_role() != ROLE_DISPATCHER:
            return False
        if player.take_location() == city:
            return False
        if city.take_players():
            self.move_player(player, city)
            return True
        if self.work_moving(player, city):
            return True
        if player.take_location() == card or city.take_name() == card:
            self.move_player(player, city)
            self.current_player.del_card(card)
            return True
        return False

    def how_many_actions(self):
        return self.remaining_actions

    def take_current_player(self):
        return self.current_player

    def spending_action(self):
        self.remaining_actions -= 1
        if self.remaining_actions == 0:
            self.transfer_motion()

    def transfer_motion(self):
        self.remaining_actions = PLAYER_ACTIONS
        self.receiving_cards(self.take_current_player())
        self.last_infections.clear()
        for i in range(self.take_infectivity()):
            card = self.open_infections_card()
            self.infection(self.cities[card])
            self.last_infections.append(card)
        self.current_player = self.players[(self.current_player.take_num() + 1)
                                           % len(self.players)]

    def take_infectivity(self):
        return INFECTIVITY[self.scale_infectivity]

    def city_infection(self, card):
        city = self.cities[card]
        if not self.infection(city):
            self.outbreak(city)

    def find_role(self, role):
        for player in self.players:
            if player.take_role() == role:
                return player
        return None

    def take_players(self):
        return self.players

    def take_virus_units(self, virus):
        return self.viruses_units[virus]

    def take_scale_outbreaks(self):
        return self.scale_outbreaks

    def take_last_infections(self):
        return self.last_infections

    def is_game_over(self):
        return self.game_over

    def who_win(self):
        return self.winner

    def take_vaccines(self):
        return self.vaccines


def show_infectivity(screen, game):
    x, y = 50, 50
    draw.circle(screen, 'white', (x, y), 33)
    font = pygame.font.Font(None, 40)
    text = font.render(str(game.take_infectivity()), True, TEXT_COLOR)
    screen.blit(text, (x - 6, y - 24))
    font = pygame.font.Font(None, 15)
    text = font.render('Скорость', True, TEXT_COLOR)
    screen.blit(text, (x - 24, y))
    font = pygame.font.Font(None, 15)
    text = font.render('заражения', True, TEXT_COLOR)
    screen.blit(text, (x - 27, y + 8))


def show_scale_outbreaks(screen, game):
    x, y = 125, 50
    draw.circle(screen, 'white', (x, y), 33)
    font = pygame.font.Font(None, 40)
    text = font.render(str(game.take_scale_outbreaks()), True, TEXT_COLOR)
    screen.blit(text, (x - 6, y - 24))
    font = pygame.font.Font(None, 15)
    text = font.render('Количество', True, TEXT_COLOR)
    screen.blit(text, (x - 30, y))
    font = pygame.font.Font(None, 15)
    text = font.render('вспышек', True, TEXT_COLOR)
    screen.blit(text, (x - 25, y + 8))


def show_player(screen, coord, player):
    x, y = coord
    font = pygame.font.Font(None, 25)
    text = font.render(str(ROLES[player.take_role() - 1]), True, TEXT_COLOR)
    draw.rect(screen, PLAYER_COLORS[player.take_role() - 1], ((x, y), (250, 75)))
    draw.rect(screen, (220, 220, 220), ((x, y - 10), (text.get_width() + 2, text.get_height() + 2)))
    screen.blit(text, (x + 1, y - 9))
    dy = 15
    cities = player.take_hand()
    indent = 0
    for i in range(min(3, len(cities))):
        city = cities[i]
        font = pygame.font.Font(None, 20)
        text = font.render(str(city), True, TEXT_COLOR)
        # draw.rect(screen, (220, 220, 220), ((x+10, y+dy), (text.get_width() + 2, text.get_height() + 2)))
        screen.blit(text, (x + 10, y + dy))
        dy += 15
        if text.get_width() + 2 > indent:
            indent = text.get_width() + 2
    x += 125
    dy = 10
    for i in range(3, len(cities)):
        city = cities[i]
        font = pygame.font.Font(None, 20)
        text = font.render(str(city), True, TEXT_COLOR)
        # draw.rect(screen, (220, 220, 220), ((x, y+dy), (text.get_width() + 2, text.get_height() + 2)))
        screen.blit(text, (x, y + dy))
        dy += 15
    x, y = player.take_location().take_cords()
    dx, dy = PLAYERS_INDENT[player.take_num()]
    draw.circle(screen, PLAYER_COLORS[player.take_role() - 1], (x + dx, y + dy), 7)


def show_vaccines(screen, game):
    x, y = 900, 15
    vaccines = game.take_vaccines()
    draw.rect(screen, 'white', ((x - 75, y), (290, 60)))
    font = pygame.font.Font(None, 20)
    text = font.render('Вакцины', True, TEXT_COLOR)
    screen.blit(text, (x - 70, y + 25))
    for i in range(len(vaccines)):
        vaccine = vaccines[i]
        if vaccine:
            draw.circle(screen, VIRUS_COLORS[i], (x + i * 55 + 20, y + 30), 25)
        else:
            draw.circle(screen, VIRUS_COLORS[i], (x + i * 55 + 20, y + 30), 25, width=2)


def show_pack(screen, game):
    x, y = 1125, 15
    draw.rect(screen, 'white', ((x - 5, y), (230, 150)))
    font = pygame.font.Font(None, 20)
    text = font.render('Последними были заражены:', True, TEXT_COLOR)
    screen.blit(text, (x, y))
    dy = 15
    cities = game.take_last_infections()
    for i in range(min(len(cities), 9)):
        city = cities[i]
        text = font.render(city, True, TEXT_COLOR)
        screen.blit(text, (x, y + dy))
        dy += 15
    dy = 15
    for i in range(9, len(cities)):
        city = cities[i]
        text = font.render(city, True, TEXT_COLOR)
        screen.blit(text, (x + 110, y + dy))
        dy += 15


def show_current_information(screen, game):
    x, y = 1100, 600
    font = pygame.font.Font(None, 30)
    text = font.render('Ходит: ' + ROLES[game.take_current_player().take_role() - 1], True, TEXT_COLOR)
    screen.blit(text, (x, y))
    font = pygame.font.Font(None, 30)
    text = font.render('Осталось ходов: ' + str(game.how_many_actions()), True, TEXT_COLOR)
    screen.blit(text, (x, y + 20))


def new_map(screen, image, game):
    cities = game.take_cities_list()
    graph = game.take_cities_graph()
    screen.blit(image, (0, 0))
    exceptions = [(16, 38), (16, 45), (24, 47)]
    # Отрисовка ребер между городами
    for city in cities:
        for neighbor in city.take_neighbors():
            # Если ребро должно выходить за пределы карты и входить с другой стороны
            if (city.take_num(), neighbor.take_num()) in exceptions:
                x1, y1 = city.take_cords()
                x2, y2 = neighbor.take_cords()
                if x1 > x2:
                    x1, y1 = x2, y2
                draw.line(screen, (220, 220, 220), (x1, y1), (0, (y1 + y2) // 2), width=3)
                draw.line(screen, (220, 220, 220), (x2, y2), (IMAGE_W, (y1 + y2) // 2), width=3)
                font = pygame.font.Font(None, 20)
                text = font.render(neighbor.take_name(), True, TEXT_COLOR)
                screen.blit(text, (0, (y1 + y2) // 2))
                font = pygame.font.Font(None, 20)
                text = font.render(city.take_name(), True, TEXT_COLOR)
                screen.blit(text, (IMAGE_W - 105, (y1 + y2) // 2))
            elif (int(neighbor.take_num()), int(city.take_num())) not in exceptions:
                draw.line(screen, (220, 220, 220), city.take_cords(), neighbor.take_cords(), width=3)
    for city in cities:
        x, y = city.take_cords()
        draw.circle(screen, VIRUS_COLORS[city.take_virus()], (x, y), 15)
        if city.is_station():
            draw.polygon(screen, STATION_COLOR,
                         ((x + 5, y), (x + 5, y - 7), (x + 7 + 5, y - 14), (x + 19, y - 7), (x + 19, y)))
        draw.circle(screen, CONTAMINATION_COLOR, (x - 10 - 5, y + 8), 7)
        font = pygame.font.Font(None, 20)
        text = font.render(str(city.take_contamination()), True, (100, 255, 100))
        screen.blit(text, (x - 10 - 9, y + 2))
        font = pygame.font.Font(None, 18)
        text = font.render(city.take_name(), True, TEXT_COLOR)
        if city.take_name() == 'Нью-Дели' or city.take_name() == 'Лос-Анджелес' or city.take_name() == 'Монреаль':
            draw.rect(screen, 'white', ((x - 15, y - 25), (text.get_width(), text.get_height())))
            screen.blit(text, (x - 15, y - 25))
        else:
            draw.rect(screen, 'white', ((x - 5, y + 7), (text.get_width(), text.get_height())))
            screen.blit(text, (x - 5, y + 7))


def new_cadr(screen, image, game):
    new_map(screen, image, game)
    show_infectivity(screen, game)
    x = 20
    for player in game.take_players():
        show_player(screen, (x, 600), player)
        x += 270
    show_scale_outbreaks(screen, game)
    show_current_information(screen, game)
    show_vaccines(screen, game)
    buttons(screen, game)
    show_pack(screen, game)


def show_game_over(screen, game):
    if game.who_win():
        font = pygame.font.Font(None, 100)
        text = font.render('Вы выиграли!', True, TEXT_COLOR)
    else:
        font = pygame.font.Font(None, 100)
        text = font.render('Вы проиграли...', True, TEXT_COLOR)
    screen.blit(text, (100, 100))


def buttons(screen, game):
    x, y = BUTTONS_CORDS[0]
    draw.circle(screen, 'white', (x, y), BUTTON_RADIUS)
    font = pygame.font.Font(None, 17)
    text = font.render('Перейти в', True, TEXT_COLOR)
    screen.blit(text, (x - 33, y - 12))
    text = font.render('выбранный', True, TEXT_COLOR)
    screen.blit(text, (x - 33, y - 2))
    text = font.render('город', True, TEXT_COLOR)
    screen.blit(text, (x - 27, y + 8))

    x, y = BUTTONS_CORDS[1]
    draw.circle(screen, 'white', (x, y), BUTTON_RADIUS)
    font = pygame.font.Font(None, 17)
    text = font.render('Построить', True, TEXT_COLOR)
    screen.blit(text, (x - 33, y - 12))
    font = pygame.font.Font(None, 17)
    text = font.render('станцию', True, TEXT_COLOR)
    screen.blit(text, (x - 27, y - 2))

    x, y = BUTTONS_CORDS[2]
    draw.circle(screen, 'white', (x, y), BUTTON_RADIUS)
    font = pygame.font.Font(None, 17)
    text = font.render('Бороться с', True, TEXT_COLOR)
    screen.blit(text, (x - 33, y - 12))
    font = pygame.font.Font(None, 17)
    text = font.render('заражением', True, TEXT_COLOR)
    screen.blit(text, (x - 33, y - 2))

    x, y = BUTTONS_CORDS[3]
    draw.circle(screen, 'white', (x, y), BUTTON_RADIUS)
    font = pygame.font.Font(None, 17)
    text = font.render('Передать', True, TEXT_COLOR)
    screen.blit(text, (x - 27, y - 12))
    font = pygame.font.Font(None, 17)
    text = font.render('карту', True, TEXT_COLOR)
    screen.blit(text, (x - 25, y - 2))

    if game.take_current_player().take_role() == ROLE_DISPATCHER:
        x, y = BUTTONS_CORDS[4]
        draw.circle(screen, 'white', (x, y), BUTTON_RADIUS + 1)
        font = pygame.font.Font(None, 15)
        text = font.render('Организовать', True, TEXT_COLOR)
        screen.blit(text, (x - 35, y - 9))
        font = pygame.font.Font(None, 15)
        text = font.render('перелет', True, TEXT_COLOR)
        screen.blit(text, (x - 28, y))


def main():
    pygame.init()
    size = IMAGE_W, IMAGE_H + 100
    screen = pygame.display.set_mode(size)
    image = load_image('map.png')
    screen.fill(BACKGROUND_COLOR)
    screen.blit(image, (0, 0))
    pygame.display.flip()
    game = Game([1, 2, 3, 4])
    running = True
    chosen_city = []
    chosen_player = None
    chosen_player_cords = (-100, -100)
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                city = game.get_element(event.pos)
                if city:
                    if city not in chosen_city:
                        chosen_city.append(city)
                    else:
                        chosen_city.pop(chosen_city.index(city))
                else:
                    ex, ey = event.pos
                    for i in range(5):
                        x, y = BUTTONS_CORDS[i]
                        dist = ((x - ex) ** 2 + (y - ey) ** 2) ** 0.5
                        if dist <= BUTTON_RADIUS:
                            if i == 1:
                                if len(chosen_city) == 1:
                                    if game.build_station(game.take_current_player(), chosen_city[0]):
                                        game.spending_action()
                                        break
                            if i == 0:
                                if len(chosen_city) == 1:
                                    if chosen_city[0].take_name() in game.take_current_player().take_hand() or \
                                            chosen_city[0] in \
                                            game.take_current_player().take_location().take_neighbors():
                                        if game.action_with_city(game.take_current_player(),
                                                                 chosen_city[0], chosen_city[0].take_name()):
                                            game.spending_action()
                                            break
                            if i == 2:
                                if game.fighting_virus(game.take_current_player()):
                                    game.spending_action()
                                    break
                            if i == 3:
                                if chosen_player and len(chosen_city) == 1 and \
                                        game.transfer_card(game.take_current_player(),
                                                           chosen_player, chosen_city[0].take_name()):
                                    game.spending_action()
                                    chosen_player = None
                                    chosen_player_cords = (-100, -100)
                                    break
                            if i == 4:
                                if chosen_city[0].take_name() in game.take_current_player().take_hand():
                                    if chosen_player and len(chosen_city) == 1 and \
                                            game.dispatcher_action(chosen_player,
                                                                   chosen_city[0], chosen_city[0].take_name()):
                                        game.spending_action()
                                        chosen_player = None
                                        chosen_player_cords = (-100, -100)
                                        break
                                if chosen_city[0] in game.take_current_player().take_location().take_neighbors() or \
                                        len(chosen_city[0].take_players()) > 0:
                                    if chosen_player and len(chosen_city) == 1 and \
                                            game.dispatcher_action(chosen_player,
                                                                   chosen_city[0], None):
                                        game.spending_action()
                                        chosen_player = None
                                        chosen_player_cords = (-100, -100)
                                        break
                    for i in range(4):
                        x, y = 20 + i * 270, 600
                        dist = ((x - ex) ** 2 + (y - ey) ** 2) ** 0.5
                        if dist <= 32.5:
                            chosen_player = game.take_players()[i]
                            chosen_player_cords = (x + 100, y)
        show_game_over(screen, game)
        new_cadr(screen, image, game)
        for city in chosen_city:
            # print(city.take_name())
            draw.circle(screen, 'orange', city.take_cords(), CITY_RADIUS + 10)
        draw.circle(screen, 'orange', chosen_player_cords, CITY_RADIUS + 10)
        # print(chosen_player)
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
