import csv
import pygame
import os
import sys
import queue
from random import shuffle

# параметры игровых механик
MAK_CONTAMINATION = 4
INFECTION_CARD_NAME = 'Заражение'
INFECTION_CARDS_COUNT = 6
HOW_TAKE = 2
# параметры рисовки
IMAGE_W = 1357
IMAGE_H = 628
VIRUS_COLORS = [(10, 10, 10), (0, 0, 255), (255, 255, 0), (255, 0, 0)]
CITY_RADIUS = 10


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


class Game:
    def __init__(self, players):
        self.players = players
        self.cities = dict()
        cities_list = load_cities()
        for city in cities_list:
            num, name, cords, virus = city
            self.cities[name] = Town(num, name, cords, virus)
        for c_1, c_2 in load_cities_graph():
            name_1, name_2 = cities_list[c_1][1], cities_list[c_2][1]
            self.cities[name_1].add_neighbor(self.cities[name_2])
            self.cities[name_2].add_neighbor(self.cities[name_1])

        cities_names = [city[1] for city in cities_list]
        cards = cities_names + [INFECTION_CARD_NAME] * INFECTION_CARDS_COUNT
        shuffle(cards)
        self.players_pack = iter(cards)
        cards = cities_names * (MAK_CONTAMINATION + 1)
        shuffle(cards)
        self.infection_pack = iter(cards)

    def get_element(self, x, y):
        for city in self.cities.values():
            cords = city.take_cords()
            dist = ((cords[0] - x) ** 2 + (cords[1] - y) ** 2) ** 0.5
            if dist <= CITY_RADIUS:
                return city

    def outbreak(self, start_city):
        infected = queue.Queue()
        infected.put(start_city)
        used = [False] * len(self.cities.values())
        used[start_city.take_num()] = True
        while not infected.empty():
            city = infected.get()
            for neig in city.take_neighbors():
                if not used[neig.take_num()]:
                    used[neig.take_num()] = True
                    if not neig.infection():
                        infected.put(neig)

    def move_player(self, player, city):
        player.take_location().del_player(player)
        city.add_player(player)
        player.set_location(city)

    def open_players_card(self):
        return next(self.players_pack)

    def open_infections_card(self):
        return next(self.infection_pack)

    def receiving_cards(self, player):
        for _ in range(HOW_TAKE):
            player.add_card(self.open_players_card())

    def transfer_card(self, player_from, player_to, card):
        if player_from.del_card(card):
            player_to.add_card(card)
