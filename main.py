import csv
import pygame
import os
import sys
import queue
from random import shuffle

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
# параметры победителя
GAME_WIN = False
PLAYERS_WIN = True
# параметры рисовки
IMAGE_W = 1357
IMAGE_H = 628
VIRUS_COLORS = [(10, 10, 10), (0, 0, 255), (255, 255, 0), (255, 0, 0)]
CITY_RADIUS = 10
# игровые роли
ROLE_DISPATCHER = 1
ROLE_DOCTOR = 2
ROLE_SCIENTIST = 3
ROLE_RESEARCHER = 4
ROLE_ENGINEER = 5
ROLE_QUARANTINE_SPECIALIST = 6


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


class Town:
    def __init__(self, num, name, cords, virus):
        self.num = num
        self.name = name
        self.cords = cords
        self.virus = virus

        self.players = set()
        self.station = False
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
        index = self.hand.index(card)
        if index == -1:
            return False
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
        self.players = players
        self.cities = dict()
        cities_list = load_cities()
        for city in cities_list:
            num, name, cords, virus = city
            self.cities[name] = Town(num, name, cords, virus)
        self.cities_graph = []
        for c_1, c_2 in load_cities_graph():
            name_1, name_2 = cities_list[c_1][1], cities_list[c_2][1]
            self.cities[name_1].add_neighbor(self.cities[name_2])
            self.cities[name_2].add_neighbor(self.cities[name_1])
            self.cities_graph.append((self.cities[name_1], self.cities[name_2]))

        cities_names = [city[1] for city in cities_list]
        cards = cities_names + [INFECTION_CARD_NAME] * INFECTION_CARDS_COUNT
        shuffle(cards)
        self.players_pack = iter(cards)
        cards = cities_names * (MAK_CONTAMINATION + 1)
        shuffle(cards)
        while len(set(cards[:3 * START_GROUPS_SIZE])) != 3 * START_GROUPS_SIZE:
            shuffle(cards)
        self.infection_pack = iter(cards)

        self.scale_outbreaks = 0
        self.scale_infectivity = 0
        self.vaccines = [False] * VIRUS_COUNT
        self.viruses_units = [VIRUS_UNITS_COUNT] * VIRUS_COUNT
        self.game_over = False
        self.winner = None

        for units_count in range(1, 4):
            for i in range(START_GROUPS_SIZE):
                card = self.open_infections_card()
                for _ in range(units_count):
                    self.infection(self.cities[card])

        self.remaining_actions = PLAYER_ACTIONS
        self.current_player = self.players[0]

    def take_cities_list(self):
        return self.cities.values()

    def take_cities_graph(self):
        return self.cities_graph

    def get_element(self, x, y):
        for city in self.cities.values():
            cords = city.take_cords()
            dist = ((cords[0] - x) ** 2 + (cords[1] - y) ** 2) ** 0.5
            if dist <= CITY_RADIUS:
                return city

    def infection(self, city):
        if self.viruses_units[city.take_virus()] == 0:
            return True
        if city.infection():
            self.viruses_units[city.take_virus()] -= 1
            if self.viruses_units[city.take_virus()] == 0:
                self.game_over = True
                self.winner = GAME_WIN
            return True
        return False

    def medication(self, player, city):
        if player.take_role() == ROLE_DOCTOR or self.vaccines[city.take_virus]:
            if city.take_contamination() > 0:
                self.viruses_units[city.take_virus()] += city.take_contamination()
                city.nullify_contamination()
                return True
            return False
        if city.medication():
            self.viruses_units[city.take_virus()] += 1
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
        if city in player.location().take_neighbors():
            self.move_player(player, city)
            return True
        return False

    def air_moving(self, player, city, card):
        if player.location().take_name() == card:
            self.move_player(player, city)
            player.del_card(card)
        elif city.take_name() == card:
            self.move_player(player, city)
            player.del_card(card)
        else:
            return False
        return True

    def work_moving(self, player, city):
        if player.location().is_station() and city.is_station():
            self.move_player(player, city)
            return True
        return False

    def build_station(self, player, card):
        if player.take_role() == ROLE_ENGINEER:
            if not player.location().is_station():
                player.location().build_station()
                return True
            return False
        if player.location().take_name() == card and not player.location().is_station():
            player.location().build_station()
            player.del_card(card)
            return True
        return False

    def fighting_virus(self, player):
        if player.location().take_contamination() > 0:
            player.location().medication()
            return True
        return False

    def action_with_city(self, player, city, card=None):
        if player.location() == city:
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
        if player.take_location() == card or city == card:
            self.move_player(player, city)
            self.current_player.del_card(card)
            return True
        return False

    def how_actions(self):
        return self.remaining_actions

    def take_current_player(self):
        return self.current_player

    def spending_action(self):
        self.remaining_actions -= 1

    def transfer_motion(self):
        self.remaining_actions = PLAYER_ACTIONS
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

    def is_game_over(self):
        return self.game_over

    def hwo_win(self):
        return self.winner
