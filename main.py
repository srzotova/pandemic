import csv
import pygame
import os
import sys
import queue
from random import shuffle
from pygame import draw

# параметры игровых механик
MAK_CONTAMINATION = 4
INFECTION_CARD_NAME = 'Заражение'
INFECTION_CARDS_COUNT = 6
HOW_TAKE = 2
# параметры рисовки
IMAGE_W = 1357
IMAGE_H = 628
VIRUS_COLORS = [(10, 10, 10), (0, 0, 255), (255, 255, 0), (255, 0, 0)]
VIRUS_COLORS = [(10, 10, 10), (0, 10, 245), (255, 255, 0), (255, 0, 0)]
CONTAMINATION_COLOR = (0, 100, 0)
TEXT_COLOR = (80, 80, 80)
STATION_COLOR = (225, 255, 255)
CITY_RADIUS = 8



def load_cities():
    cities = []
    with open('cities.csv', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for record in reader:
            num = int(record[0]) - 1
            name = record[1]
            cords = (int(record[2]), int(record[3]))
            virus = int(record[4]) - 1
            cities.append(Town(num, name, cords, virus))
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


def new_map(screen, image, cities, graph):
    screen.blit(image, (0, 0))
    exceptions = [graph[-1], graph[-2], graph[-3]]
    # Отрисовка ребер между городами
    for city in cities:
        for neighbor in city.take_neighbors():
            for c in cities:
                if c.take_num() == neighbor:
                    # Если ребро должно выходить за пределы карты и входить с другой стороны
                    if (city.take_num(), neighbor) in exceptions:
                        x1, y1 = city.take_cords()
                        x2, y2 = c.take_cords()
                        if x1 > x2:
                            x1, y1 = x2, y2
                        draw.line(screen, (220, 220, 220), (x1, y1), (0, (y1+y2)//2), width=3)
                        draw.line(screen, (220, 220, 220), (x2, y2), (IMAGE_W, (y1 + y2) // 2), width=3)
                        font = pygame.font.Font(None, 20)
                        text = font.render(c.take_name(), True, TEXT_COLOR)
                        screen.blit(text, (0, (y1+y2)//2))
                        font = pygame.font.Font(None, 20)
                        text = font.render(city.take_name(), True, TEXT_COLOR)
                        screen.blit(text, (IMAGE_W-105, (y1 + y2) // 2))
                    elif (neighbor, city.take_num()) not in exceptions:
                        draw.line(screen, (220, 220, 220), city.take_cords(), c.take_cords(), width=3)
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
        if city.take_name() == 'Нью-Дели' or city.take_name() == 'Лос-Анджелес':
            screen.blit(text, (x-15, y-25))
        else:
            screen.blit(text, (x - 5, y + 7))


def main():
    pygame.init()
    size = IMAGE_W, IMAGE_H
    screen = pygame.display.set_mode(size)
    image = load_image('map.png')
    screen.blit(image, (0, 0))
    pygame.display.flip()
    cities = load_cities()
    graph = load_cities_graph()
    for c1, c2 in graph:
        for city in cities:
            if city.take_num() == c1:
                city.add_neighbor(c2)
            if city.take_num() == c2:
                city.add_neighbor(c1)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        new_map(screen, image, cities, graph)
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
