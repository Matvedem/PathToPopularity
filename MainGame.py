import math
import pygame
from random import randint

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()


# Определение классов для игрока, охранника, стены, цели (выхода) и шкафа
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=5, sprint_speed=10, max_stamina=100, stamina_regen_rate=1):
        super().__init__()
        self.image = pygame.Surface((32, 64))
        self.image.fill((255, 0, 0))  # Красный цвет для игрока
        self.rect = self.image.get_rect(center=(x, y))
        self.normal_speed = speed  # Обычная скорость игрока
        self.sprint_speed = sprint_speed  # Скорость бега
        self.max_stamina = max_stamina  # Максимальная выносливость
        self.stamina = max_stamina  # Текущая выносливость
        self.stamina_regen_rate = stamina_regen_rate  # Скорость восстановления выносливости
        self.is_sprinting = False  # Флаг спринта
        self.speed = self.normal_speed  # Начальная скорость
        self.in_closet = False  # Флаг нахождения в шкафу

    def update(self):
        keys = pygame.key.get_pressed()

        # Сохраняем текущую позицию игрока перед перемещением
        old_pos = self.rect.copy()

        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed

        # Управление спринтом
        if keys[pygame.K_LSHIFT] and self.stamina > 0:
            self.start_sprint()
        else:
            self.stop_sprint()

        # Проверка столкновения со стенами
        hit_wall = pygame.sprite.spritecollideany(self, walls)
        if hit_wall:
            # Если произошло столкновение, возвращаемся к предыдущей позиции
            self.rect = old_pos

        # Ограничение движения по экрану
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > 800:
            self.rect.right = 800
        if self.rect.top < 0:
            self.rect.top = 0
        elif self.rect.bottom > 600:
            self.rect.bottom = 600

        # Восстанавливаем выносливость, если она меньше максимальной
        if self.stamina < self.max_stamina:
            self.stamina += self.stamina_regen_rate
            if self.stamina > self.max_stamina:
                self.stamina = self.max_stamina

    def start_sprint(self):
        if self.stamina > 0:
            self.is_sprinting = True
            self.speed = self.sprint_speed
            self.stamina -= 1

    def stop_sprint(self):
        self.is_sprinting = False
        self.speed = self.normal_speed

    def get_stamina_percentage(self):
        return self.stamina / self.max_stamina * 100


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill((127, 127, 127))  # Серый цвет для стен
        self.rect = self.image.get_rect(topleft=(x, y))


class Guard(pygame.sprite.Sprite):
    def __init__(self, x, y, direction_x=0, direction_y=0,
                 patrol_speed=4, chase_speed=8, vision_angle=90, vision_range=200):
        super().__init__()
        self.image = pygame.Surface((32, 64))
        self.image.fill((0, 128, 0))  # Зеленый цвет для охранника
        self.rect = self.image.get_rect(center=(x, y))
        self.direction_x = direction_x
        self.direction_y = direction_y
        self.patrol_speed = patrol_speed  # Скорость патруля
        self.chase_speed = chase_speed  # Скорость преследования
        self.speed = patrol_speed  # Начальная скорость — патрулирование
        self.vision_angle = vision_angle  # Угол обзора
        self.vision_range = vision_range  # Дальность обзора
        self.facing_direction = math.atan2(direction_y, direction_x)  # Направление взгляда
        self.chasing = False  # Флаг преследования

    def update(self, walls, player):
        if self.chasing:
            # Охранник преследует игрока, если тот не в шкафу
            if not player.in_closet:
                self.move_towards_player(player)
            else:
                self.chasing = False  # Прекращаем преследование, если игрок в шкафу
                self.speed = self.patrol_speed  # Возвращаем обычную скорость патрулирования
        else:
            # Обычное движение охранника
            self.rect.x += self.direction_x * self.speed
            self.rect.y += self.direction_y * self.speed

        # Проверка столкновения со стенами
        for wall in walls:
            if pygame.sprite.collide_rect(self, wall):
                self.direction_x *= -1
                self.direction_y *= -1
                self.facing_direction = math.atan2(self.direction_y, self.direction_x)  # Обновить направление взгляда
                break

        # Изменяем направление при достижении границ экрана
        if self.rect.left < 0 or self.rect.right > 800:
            self.direction_x *= -1
            self.facing_direction = math.atan2(self.direction_y, self.direction_x)  # Обновить направление взгляда
        if self.rect.top < 0 or self.rect.bottom > 600:
            self.direction_y *= -1
            self.facing_direction = math.atan2(self.direction_y, self.direction_x)  # Обновить направление взгляда

        # Проверка, видит ли охранник игрока
        if self.check_vision(player):
            self.chasing = True  # Начинаем преследовать игрока
            self.speed = self.chase_speed  # Устанавливаем скорость преследования

    def move_towards_player(self, player):
        # Вычисляем вектор от охранника к игроку
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery

        # Нормализуем этот вектор
        distance = math.hypot(dx, dy)
        if distance > 0:
            dx /= distance
            dy /= distance

        # Перемещаем охранника в направлении игрока
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed

    def check_vision(self, player):
        # Игрок скрыт, если он находится в шкафу
        if player.in_closet:
            return False

        # Вычисляем угол между направлением взгляда охранника и игроком
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        angle_to_player = math.degrees(math.atan2(dy, dx)) % 360
        if angle_to_player > 180:
            angle_to_player -= 360

        # Проверяем, находится ли игрок в пределах угла обзора
        if abs(angle_to_player - math.degrees(self.facing_direction)) <= self.vision_angle / 2:
            # Проверяем расстояние до игрока
            distance = math.hypot(dx, dy)
            if distance <= self.vision_range:
                return True
        return False

    def draw_vision_cone(self, surface):
        # Рисуем конус обзора
        if not self.chasing:
         center = self.rect.center
         left_point = (
            center[0] + int(self.vision_range * math.cos(self.facing_direction + math.radians(self.vision_angle / 2))),
            center[1] + int(self.vision_range * math.sin(self.facing_direction + math.radians(self.vision_angle / 2))))
         right_point = (
            center[0] + int(self.vision_range * math.cos(self.facing_direction - math.radians(self.vision_angle / 2))),
            center[1] + int(self.vision_range * math.sin(self.facing_direction - math.radians(self.vision_angle / 2))))
         points = [center, left_point, right_point]
         pygame.draw.polygon(surface, (255, 0, 0, 20), points)  # Полупрозрачный красный цвет
        else:
            pass


class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill((0, 191, 255))  # Голубой цвет для выхода
        self.rect = self.image.get_rect(center=(x, y))


class Closet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((48, 96))
        self.image.fill((139, 69, 19))  # Коричневый цвет для шкафа
        self.rect = self.image.get_rect(center=(x, y))


# Создание спрайтов и групп
player = Player(50, 50, speed=4)  # Увеличиваем скорость игрока
walls = [
    Wall(200, 100, 16, 400),  # Левая стена
    Wall(584, 100, 16, 200),  # Правая стена
    Wall(392, 100, 416, 16),  # Верхняя стена
    Wall(392, 484, 416, 16)  # Нижняя стена
]
closets = [
    Closet(750, 440),
    Closet(650, 50)
]
guards = [
    Guard(300, 150, direction_x=3, direction_y=0, patrol_speed=1, chase_speed=6, vision_angle=60, vision_range=200),  # Горизонтальный патруль
    Guard(450, 250, direction_x=0, direction_y=3, patrol_speed=1, chase_speed=6, vision_angle=60, vision_range=200)  # Вертикальный патруль
]
exit = Exit(700, 150)

all_sprites = pygame.sprite.Group(player, *walls, *guards, exit, *closets)
show_hitboxes = False

# Основной игровой цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            show_hitboxes = not show_hitboxes

    # Обновление спрайтов
    player.update()
    for guard in guards:
        guard.update(walls, player)

    # Проверка столкновения с выходом
    if pygame.sprite.collide_rect(player, exit):
        print("Вы дошли до выхода!")
        running = False

    # Проверка столкновения с охранниками
    for guard in guards:
        if pygame.sprite.collide_rect(player, guard):
            print("Вас поймали!")
            running = False

    # Проверка столкновения с шкафами
    closet_collided = pygame.sprite.spritecollideany(player, closets)
    if closet_collided:
        player.in_closet = True
    else:
        player.in_closet = False

    screen.fill((0, 0, 0))
    all_sprites.draw(screen)

    # Отрисовка конусов обзора
    for guard in guards:
        guard.draw_vision_cone(screen)

    # Отображение хитбоксов
    if show_hitboxes:
        for sprite in all_sprites:
            pygame.draw.rect(screen, (255, 255, 255), sprite.rect, 1)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()