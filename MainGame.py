import math
import pygame

pygame.init()
screen = pygame.display.set_mode((1200, 800))
clock = pygame.time.Clock()
pygame.display.set_caption('Path To popularity')

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=5, sprint_speed=10, max_stamina=100, stamina_regen_rate=1):
        super().__init__()
        self.image = pygame.Surface((32, 64))
        self.image.fill((255, 0, 0))  # красный цвет для игрока
        self.rect = self.image.get_rect(center=(x, y))
        self.normal_speed = speed  # обычная скорость игрока
        self.sprint_speed = sprint_speed  # скорость бега
        self.max_stamina = max_stamina  # максимальная выносливость
        self.stamina = max_stamina  # текущая выносливость
        self.stamina_regen_rate = stamina_regen_rate  # скорость восстановления выносливости
        self.is_sprinting = False  # флаг спринта
        self.speed = self.normal_speed  # начальная скорость
        self.in_closet = False  # флаг нахождения в шкафу
        self.sprint_timer = 0  # время, оставшееся до конца спринта
        self.regen_timer = 0  # время, оставшееся до начала восстановления

    def update(self):
        keys = pygame.key.get_pressed()

        # сохраняем текущую позицию игрока перед перемещением
        old_pos = self.rect.copy()

        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed

        # управление спринтом
        if keys[pygame.K_LSHIFT] and self.stamina > 0 and self.regen_timer <= 0:
            self.start_sprint()

        # проверка столкновения со стенами
        hit_wall = pygame.sprite.spritecollideany(self, walls)
        if hit_wall:
            # если произошло столкновение, возвращаемся к предыдущей позиции
            self.rect = old_pos

        # ограничение движения по экрану
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > 1200:
            self.rect.right = 1200
        if self.rect.top < 0:
            self.rect.top = 0
        elif self.rect.bottom > 800:
            self.rect.bottom = 800

        # обновление таймера спринта
        if self.sprint_timer > 0:
            self.sprint_timer -= 1
            if self.sprint_timer == 0:
                self.stop_sprint()
                self.regen_timer = 120  # 2 секунды восстановления
        elif self.regen_timer > 0:
            self.regen_timer -= 1

        # восстанавливаем выносливость, если она меньше максимальной
        if self.stamina < self.max_stamina and self.regen_timer <= 0:
            self.stamina += self.stamina_regen_rate
            if self.stamina > self.max_stamina:
                self.stamina = self.max_stamina

    def start_sprint(self):
        if self.stamina > 0:
            self.is_sprinting = True
            self.speed = self.sprint_speed
            self.stamina -= 1
            self.sprint_timer = 60  # 1,5 секунды спринта

    def stop_sprint(self):
        self.is_sprinting = False
        self.speed = self.normal_speed
        if self.sprint_timer > 0:
            self.sprint_timer = 0
            self.regen_timer = 120  # 2 секунды восстановления

    def get_stamina_percentage(self):
        return self.stamina / self.max_stamina * 100


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill((127, 127, 127))  # серый цвет для стен
        self.rect = self.image.get_rect(topleft=(x, y))


class Guard(pygame.sprite.Sprite):
    def __init__(self, x, y, direction_x=0, direction_y=0,
                 patrol_speed=4, chase_speed=8, vision_angle=90, vision_range=200):
        super().__init__()
        self.image = pygame.Surface((32, 64))
        self.image.fill((0, 128, 0))  # зеленый цвет для охранника
        self.rect = self.image.get_rect(center=(x, y))
        self.direction_x = direction_x
        self.direction_y = direction_y
        self.patrol_speed = patrol_speed  # скорость патруля
        self.chase_speed = chase_speed  # скорость преследования
        self.speed = patrol_speed  # начальная скорость — патрулирование
        self.vision_angle = vision_angle  # угол обзора
        self.vision_range = vision_range  # дальность обзора
        self.facing_direction = math.atan2(direction_y, direction_x)  # Направление взгляда
        self.chasing = False  # флаг преследования

    def update(self, walls, player):
        if self.chasing:
            # охранник преследует игрока, если тот не в шкафу
            if not player.in_closet:
                self.move_towards_player(player)
            else:
                self.chasing = False  # прекращаем преследование, если игрок в шкафу
                self.speed = self.patrol_speed  # возвращаем обычную скорость патрулирования
        else:
            # обычное движение охранника
            self.rect.x += self.direction_x * self.speed
            self.rect.y += self.direction_y * self.speed

        # проверка столкновения со стенами
        for wall in walls:
            if pygame.sprite.collide_rect(self, wall):
                self.direction_x *= -1
                self.direction_y *= -1
                self.facing_direction = math.atan2(self.direction_y, self.direction_x)  # Обновить направление взгляда
                break

        # изменяем направление при достижении границ экрана
        if self.rect.left < 0 or self.rect.right > 1200:
            self.direction_x *= -1
            self.facing_direction = math.atan2(self.direction_y, self.direction_x)  # Обновить направление взгляда
        if self.rect.top < 0 or self.rect.bottom > 800:
            self.direction_y *= -1
            self.facing_direction = math.atan2(self.direction_y, self.direction_x)  # Обновить направление взгляда

        # проверка, видит ли охранник игрока
        if self.check_vision(player):
            self.chasing = True  # начинаем преследовать игрока
            self.speed = self.chase_speed  # устанавливаем скорость преследования

    def move_towards_player(self, player):
        # вычисляем вектор от охранника к игроку
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery

        # нормализуем этот вектор
        distance = math.hypot(dx, dy)
        if distance > 0:
            dx /= distance
            dy /= distance

        # перемещаем охранника в направлении игрока
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed

    def check_vision(self, player):
        # игрок скрыт, если он находится в шкафу
        if player.in_closet:
            return False

        # вычисляем угол между направлением взгляда охранника и игроком
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        angle_to_player = math.degrees(math.atan2(dy, dx)) % 360
        if angle_to_player > 180:
            angle_to_player -= 360

        # проверяем, находится ли игрок в пределах угла обзора
        if abs(angle_to_player - math.degrees(self.facing_direction)) <= self.vision_angle / 2:
            # проверяем расстояние до игрока
            distance = math.hypot(dx, dy)
            if distance <= self.vision_range:
                return True
        return False

    def draw_vision_cone(self, surface):
        # Рисуем конус обзора
        if not self.chasing:
            center = self.rect.center
            left_point = (
                center[0] + int(
                    self.vision_range * math.cos(self.facing_direction + math.radians(self.vision_angle / 2))),
                center[1] + int(
                    self.vision_range * math.sin(self.facing_direction + math.radians(self.vision_angle / 2))))
            right_point = (
                center[0] + int(
                    self.vision_range * math.cos(self.facing_direction - math.radians(self.vision_angle / 2))),
                center[1] + int(
                    self.vision_range * math.sin(self.facing_direction - math.radians(self.vision_angle / 2))))
            points = [center, left_point, right_point]
            pygame.draw.polygon(surface, (255, 0, 0, 20), points)
        else:
            pass


class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill((0, 191, 255))  # голубой цвет для выхода
        self.rect = self.image.get_rect(center=(x, y))


class Closet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((48, 96))
        self.image.fill((139, 69, 19))  # коричневый цвет для шкафа
        self.rect = self.image.get_rect(center=(x, y))


# создание спрайтов и групп
player = Player(50, 50, speed=4)  # увеличиваем скорость игрока
walls = [
    Wall(200, 100, 16, 400),  # левая стена
    Wall(584, 100, 16, 200),  # правая стена
    Wall(300, 100, 700, 16),  # верхняя стена
    Wall(200, 484, 605, 16),  # нижняя стена
    Wall(800, 300, 16, 200),
    Wall(1000, 100, 16, 600),
    Wall(200, 700, 816, 16),
    Wall(200, 500, 16, 200),

]
closets = [
    Closet(650, 200),
    Closet(950, 650)
]
guards = [
    Guard(300, 400, direction_x=3, direction_y=0, patrol_speed=1, chase_speed=6, vision_angle=60, vision_range=200),
    # горизонтальный патруль
    Guard(260, 250, direction_x=0, direction_y=3, patrol_speed=1, chase_speed=6, vision_angle=60, vision_range=200),
    # вертикальный патруль
    Guard(900, 250, direction_x=0, direction_y=3, patrol_speed=1, chase_speed=6, vision_angle=60, vision_range=200),

    Guard(900, 600, direction_x=3, direction_y=0, patrol_speed=1, chase_speed=6, vision_angle=60, vision_range=200),

]
exit = Exit(300, 600)

all_sprites = pygame.sprite.Group(player, *walls, *guards, exit, *closets)
show_hitboxes = False

# основной игровой цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            show_hitboxes = not show_hitboxes

    # обновление спрайтов
    player.update()
    for guard in guards:
        guard.update(walls, player)

    # проверка столкновения с выходом
    if pygame.sprite.collide_rect(player, exit):
        print("Вы дошли до выхода!")
        running = False

    # проверка столкновения с охранниками
    for guard in guards:
        if pygame.sprite.collide_rect(player, guard):
            print("Вас поймали!")
            running = False

    # проверка столкновения с шкафами
    closet_collided = pygame.sprite.spritecollideany(player, closets)
    if closet_collided:
        player.in_closet = True
    else:
        player.in_closet = False

    screen.fill((0, 0, 0))
    all_sprites.draw(screen)

    # отрисовка конусов обзора
    for guard in guards:
        guard.draw_vision_cone(screen)

    # отображение хитбоксов
    if show_hitboxes:
        for sprite in all_sprites:
            pygame.draw.rect(screen, (255, 255, 255), sprite.rect, 1)
    all_sprites.draw(screen)
    pygame.display.flip()
    clock.tick(30)
pygame.quit()