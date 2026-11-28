
import pygame
import math
import random
import sys

pygame.init()

# =====================================
#                 MECRAFT
# =====================================

screen = pygame.display.set_mode((960, 600), pygame.RESIZABLE)
pygame.display.set_caption("MeCraft")
clock = pygame.time.Clock()

font = pygame.font.Font(None, 23)
large = pygame.font.Font(None, 42)
small = pygame.font.Font(None, 17)

# GAME SETTINGS
RENDER_CHUNKS = 24
MAX_RAY_DISTANCE = 20
FOV = math.pi / 3
RAYS = 240
MOVE_SPEED = 3.0

# COLORS
SKY = (105, 175, 225)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)

# BLOCK DATABASE
BLOCKS = {
    "Grass": (80, 170, 65),
    "Dirt": (130, 85, 50),
    "Stone": (125, 130, 135),
    "Cobblestone": (105, 110, 115),
    "Wood": (140, 90, 45),
    "Planks": (180, 135, 80),
    "Sand": (220, 195, 120),
    "Leaves": (40, 125, 45),
    "Glass": (140, 210, 230),
    "Brick": (160, 75, 65),
    "Coal Ore": (75, 80, 85),
    "Iron Ore": (150, 125, 115),
    "Gold Ore": (210, 175, 55),
    "Diamond Ore": (40, 205, 210),
    "Obsidian": (65, 45, 100),
    "Crafting Table": (150, 105, 55),
    "Furnace": (95, 95, 95),
    "Bedrock": (45, 45, 45)
}

# INVENTORY
inventory = {name: 20 for name in BLOCKS}
inventory.update({
    "Wooden Sword": 1,
    "Bow": 1,
    "Arrow": 20,
    "Wooden Pickaxe": 1,
    "Wooden Axe": 1,
    "Stick": 10
})

HOTBAR = [
    "Grass", "Dirt", "Stone", "Cobblestone",
    "Wood", "Planks", "Crafting Table", "Wooden Sword"
]

selected = 0
weapon = "Wooden Sword"

# WORLD GENERATION
WORLD_SIZE = 48
world = {}

random.seed(20)

for x in range(WORLD_SIZE):
    for y in range(WORLD_SIZE):
        if x == 0 or y == 0 or x == WORLD_SIZE-1 or y == WORLD_SIZE-1:
            world[(x, y)] = "Bedrock"
        else:
            world[(x, y)] = "Grass"

# Random trees and stones
for _ in range(100):
    x = random.randint(3, WORLD_SIZE-4)
    y = random.randint(3, WORLD_SIZE-4)

    if 17 < x < 30 and 17 < y < 30:
        continue

    world[(x, y)] = random.choice([
        "Wood", "Stone", "Cobblestone", "Sand"
    ])

# PLAYER
px, py = 23.5, 23.5
angle = 0.0
pitch = 0
health = 20
hunger = 20

mode = "CREATIVE"
show_controls = True
inventory_open = False
craft_open = False

# MOBS
mobs = []

for i in range(12):
    mobs.append({
        "x": random.uniform(5, 42),
        "y": random.uniform(5, 42),
        "type": random.choice([
            "Cow", "Pig", "Sheep", "Zombie",
            "Skeleton", "Creeper", "Chicken"
        ]),
        "health": 3,
        "timer": random.random() * 3
    })

mob_colors = {
    "Cow": (100, 70, 45),
    "Pig": (240, 140, 155),
    "Sheep": (230, 230, 220),
    "Chicken": (245, 245, 230),
    "Zombie": (50, 145, 65),
    "Skeleton": (210, 210, 195),
    "Creeper": (40, 160, 50)
}

# INPUT
held = set()
look_touch = None
last_hit = None
weapon_timer = 0
message = "Welcome to MeCraft!"

def say(msg):
    global message
    message = msg

def txt(text, x, y, size=font, color=WHITE):
    screen.blit(size.render(str(text), True, color), (x, y))

def rect_button(rect, label, color=(55, 65, 75)):
    pygame.draw.rect(screen, color, rect, border_radius=9)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=9)
    img = font.render(label, True, WHITE)
    screen.blit(img, img.get_rect(center=rect.center))

def solid(x, y):
    return world.get((int(x), int(y)), "Bedrock") is not None

def move(dx, dy):
    global px, py

    nx = px + dx
    ny = py + dy

    if not solid(nx + 0.2, py) and not solid(nx - 0.2, py):
        px = nx

    if not solid(px, ny + 0.2) and not solid(px, ny - 0.2):
        py = ny

def raycast(ray_angle):
    dx = math.cos(ray_angle)
    dy = math.sin(ray_angle)

    distance = 0.05
    previous = None

    while distance < MAX_RAY_DISTANCE:
        x = px + dx * distance
        y = py + dy * distance

        cell = (int(x), int(y))

        if cell in world:
            return distance, cell, previous

        previous = cell
        distance += 0.035

    return MAX_RAY_DISTANCE, None, previous

def target():
    return raycast(angle)

def break_block():
    distance, cell, previous = target()

    if cell is None:
        return

    block = world[cell]

    if block == "Bedrock":
        say("Bedrock cannot be broken!")
        return

    del world[cell]

    if block in inventory:
        inventory[block] += 1

    if mode == "SURVIVAL":
        inventory[block] = max(0, inventory[block])

    say("Broken: " + block)

def place_block():
    distance, cell, previous = target()

    if cell is None or previous is None:
        return

    block = HOTBAR[selected]

    if block not in BLOCKS:
        return

    if previous not in world:
        if mode == "CREATIVE" or inventory[block] > 0:
            world[previous] = block

            if mode == "SURVIVAL":
                inventory[block] -= 1

            say("Placed: " + block)

def attack():
    global mobs, weapon_timer

    weapon_timer = 0.25

    if weapon == "Bow" and inventory["Arrow"] <= 0:
        say("No arrows!")
        return

    if weapon == "Bow":
        inventory["Arrow"] -= 1

    for mob in mobs[:]:
        dx = mob["x"] - px
        dy = mob["y"] - py
        distance = math.hypot(dx, dy)

        direction = math.atan2(dy, dx)
        difference = (direction-angle+math.pi) % (2*math.pi)-math.pi

        if distance < 4 and abs(difference) < 0.22:
            mob["health"] -= 2

            if mob["health"] <= 0:
                mobs.remove(mob)
                say(mob["type"] + " defeated!")
            else:
                say("Hit " + mob["type"])

            return

    say("Missed!")

def craft(item):
    recipes = {
        "Planks": ("Wood", 1, 4),
        "Stick": ("Planks", 2, 4),
        "Wooden Sword": ("Planks", 2, 1),
        "Wooden Pickaxe": ("Planks", 3, 1),
        "Wooden Axe": ("Planks", 3, 1),
        "Crafting Table": ("Planks", 4, 1)
    }

    if item not in recipes:
        return

    material, cost, amount = recipes[item]

    if inventory[material] >= cost:
        inventory[material] -= cost
        inventory[item] = inventory.get(item, 0) + amount
        say("Crafted " + item)
    else:
        say("Not enough " + material)

# TEXTURES
def texture_color(block, side, wx, wy):
    base = BLOCKS[block]

    # Pixel-like random pattern
    seed = int(wx*73 + wy*131 + side*997)
    rng = random.Random(seed)

    variation = rng.randint(-18, 18)

    if block == "Grass" and side == 0:
        base = (75, 175, 60)

    if block == "Grass" and side != 0:
        base = (130, 85, 48)

    if block == "Wood":
        variation += int(math.sin(wy*8)*12)

    if block == "Cobblestone":
        variation += int(math.sin(wx*13+wy*7)*15)

    if block == "Crafting Table":
        variation += int(math.sin(wx*10)*15)

    return tuple(
        max(0, min(255, c+variation))
        for c in base
    )

# FIRST PERSON RENDERER
depth_buffer = []

def draw_world():
    global depth_buffer

    w, h = screen.get_size()

    screen.fill(SKY)

    pygame.draw.rect(
        screen, (75, 105, 65),
        (0, h//2, w, h//2)
    )

    depth_buffer = []

    for column in range(RAYS):
        ray_angle = angle-FOV/2 + FOV*column/RAYS

        distance, cell, previous = raycast(ray_angle)

        corrected = distance * math.cos(ray_angle-angle)
        corrected = max(0.1, corrected)

        wall_height = int(h*0.85/corrected)
        wall_height = min(h*3, wall_height)

        y1 = h//2-wall_height//2+pitch
        y2 = h//2+wall_height//2+pitch

        if cell:
            block = world[cell]
            color = texture_color(
                block, 0, cell[0], cell[1]
            )

            side = int(column % 4 == 0)
            shade = 1.0 if not side else 0.72

            color = tuple(int(c*shade) for c in color)

            stripe = w//RAYS+2
            x = column*w//RAYS

            pygame.draw.rect(
                screen, color,
                (x, y1, stripe, y2-y1)
            )

            # Pixel-like wall texture lines
            if column % 8 == 0:
                pygame.draw.line(
                    screen, (30, 35, 30),
                    (x, y1), (x, y2), 1
                )

        depth_buffer.append(corrected)

    # MOBS
    draw_mobs(w, h)

    # Crosshair
    cx, cy = w//2, h//2+pitch

    pygame.draw.line(
        screen, WHITE, (cx-8, cy), (cx+8, cy), 2
    )
    pygame.draw.line(
        screen, WHITE, (cx, cy-8), (cx, cy+8), 2
    )

def draw_mobs(w, h):
    visible = []

    for mob in mobs:
        dx = mob["x"]-px
        dy = mob["y"]-py

        distance = math.hypot(dx, dy)
        direction = math.atan2(dy, dx)

        difference = (direction-angle+math.pi) % (2*math.pi)-math.pi

        if abs(difference) < FOV/2 and distance > 0.3:
            visible.append((distance, difference, mob))

    visible.sort(reverse=True)

    for distance, difference, mob in visible:
        sx = int(w/2 + difference/FOV*w)

        wall_height = int(h*0.65/distance)
        sy = h//2+pitch

        if 0 <= sx < w:
            color = mob_colors[mob["type"]]
            bw = max(5, wall_height//3)
            bh = max(10, wall_height//2)

            if distance < depth_buffer[
                min(RAYS-1, max(0, sx*RAYS//w))
            ]:
                pygame.draw.rect(
                    screen, color,
                    (sx-bw//2, sy-bh//2, bw, bh),
                    border_radius=4
                )

                pygame.draw.circle(
                    screen, BLACK,
                    (sx-bw//5, sy-bh//5), 2
                )
                pygame.draw.circle(
                    screen, BLACK,
                    (sx+bw//5, sy-bh//5), 2
                )

                pygame.draw.rect(
                    screen, (40, 40, 40),
                    (sx-bw//2, sy-bh//2-8, bw, 4)
                )

                pygame.draw.rect(
                    screen, (70, 220, 70),
                    (sx-bw//2, sy-bh//2-8,
                     int(bw*mob["health"]/3), 4)
                )

# WEAPON VIEW
def draw_weapon(w, h):
    global weapon_timer

    if weapon_timer > 0:
        weapon_timer -= 1/30

    if weapon == "Bow":
        color = (135, 85, 40)
        pygame.draw.arc(
            screen, color,
            (w-145, h-190, 100, 160),
            -1.5, 1.5, 9
        )
        pygame.draw.line(
            screen, WHITE,
            (w-100, h-175), (w-100, h-40), 2
        )
    else:
        color = (170, 175, 185)

        if weapon in ("Wooden Axe", "Wooden Pickaxe"):
            color = (135, 90, 45)

        offset = 45 if weapon_timer > 0 else 0

        points = [
            (w-105, h-45+offset),
            (w-80, h-75+offset),
            (w-20, h-240+offset),
            (w-2, h-230+offset),
            (w-50, h-55+offset)
        ]

        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, BLACK, points, 2)

# HOTBAR
def draw_hotbar(w, h):
    size = min(54, w//10)
    start = (w-size*9)//2
    y = h-size-8

    for i, block in enumerate(HOTBAR):
        r = pygame.Rect(start+i*size, y, size-3, size-3)

        pygame.draw.rect(
            screen, (65, 65, 65), r,
            border_radius=5
        )

        if i == selected:
            pygame.draw.rect(
                screen, (255, 215, 40), r, 3,
                border_radius=5
            )

        color = BLOCKS.get(block, (190, 190, 190))

        pygame.draw.rect(
            screen, color,
            (r.x+12, r.y+8, size-27, size-27)
        )

        txt(str(i+1), r.x+5, r.y+35, small)

    txt("9 = INVENTORY", start, y-19, small)

# TOUCH CONTROL LAYOUT
def controls(w, h):
    s = min(65, max(43, w//13))

    return {
        "UP": pygame.Rect(25, h-190, s, s),
        "DOWN": pygame.Rect(25, h-75, s, s),
        "LEFT": pygame.Rect(-20, h-132, s, s),
        "RIGHT": pygame.Rect(75, h-132, s, s),
        "JUMP": pygame.Rect(w-s-20, h-195, s, s),
        "BREAK": pygame.Rect(w-s-20, h-125, s, s),
        "PLACE": pygame.Rect(w-2*s-30, h-125, s, s),
        "ATTACK": pygame.Rect(w-2*s-30, h-55, s, s),
        "CRAFT": pygame.Rect(w-3*s-40, 15, s, 35)
    }

def draw_controls(w, h):
    if not show_controls:
        return

    for name, r in controls(w, h).items():
        rect_button(r, name)

# INVENTORY MENU
def draw_inventory(w, h):
    pygame.draw.rect(
        screen, (35, 40, 50),
        (w//2-190, 35, 380, h-70),
        border_radius=12
    )

    txt("MECRAFT INVENTORY", w//2-130, 45, large)

    for i, name in enumerate(list(inventory)):
        col = i % 3
        row = i // 3

        x = w//2-165+col*110
        y = 105+row*45

        pygame.draw.rect(
            screen, BLOCKS.get(name, (150, 150, 150)),
            (x, y, 100, 37), border_radius=5
        )

        label = name[:11]
        txt(label, x+4, y+3, small)
        txt(inventory[name], x+4, y+19, small)

    rect_button(
        pygame.Rect(w//2-65, h-75, 130, 42),
        "CLOSE"
    )

# CRAFTING MENU
def draw_crafting(w, h):
    pygame.draw.rect(
        screen, (35, 40, 50),
        (w//2-200, 45, 400, h-90),
        border_radius=12
    )

    txt("CRAFTING TABLE", w//2-120, 55, large)
    txt("3 x 3 CRAFTING GRID", w//2-105, 105)

    # Nine slots
    for i in range(9):
        x = w//2-125+(i%3)*48
        y = 140+(i//3)*48

        pygame.draw.rect(
            screen, (90, 90, 90),
            (x, y, 42, 42), border_radius=4
        )

    txt("RECIPES", w//2+45, 125)

    recipes = [
        "Planks", "Stick", "Wooden Sword",
        "Wooden Pickaxe", "Wooden Axe",
        "Crafting Table"
    ]

    for i, name in enumerate(recipes):
        rect_button(
            pygame.Rect(w//2+25, 155+i*42, 155, 35),
            name
        )

    rect_button(
        pygame.Rect(w//2-65, h-80, 130, 40),
        "CLOSE"
    )

# UI ACTION
def handle_click(pos, w, h):
    global selected, inventory_open, craft_open
    global mode, show_controls, weapon

    x, y = pos
    ui = controls(w, h)

    if craft_open:
        if pygame.Rect(w//2-65, h-80, 130, 40).collidepoint(pos):
            craft_open = False
            return

        recipes = [
            "Planks", "Stick", "Wooden Sword",
            "Wooden Pickaxe", "Wooden Axe",
            "Crafting Table"
        ]

        for i, name in enumerate(recipes):
            if pygame.Rect(w//2+25, 155+i*42, 155, 35).collidepoint(pos):
                craft(name)
                return
        return

    if inventory_open:
        if pygame.Rect(w//2-65, h-75, 130, 42).collidepoint(pos):
            inventory_open = False
            return

        for i, name in enumerate(inventory):
            col, row = i%3, i//3
            r = pygame.Rect(
                w//2-165+col*110,
                105+row*45, 100, 37
            )

            if r.collidepoint(pos):
                if name in HOTBAR:
                    pass
                else:
                    HOTBAR[selected] = name if name in BLOCKS else HOTBAR[selected]
                    if name in ("Wooden Sword", "Bow",
                                "Wooden Axe", "Wooden Pickaxe"):
                        weapon = name
                inventory_open = False
                return
        return

    size = min(54, w//10)
    start = (w-size*9)//2
    bar_y = h-size-8

    if bar_y <= y <= bar_y+size:
        slot = (x-start)//size
        if 0 <= slot < 9:
            if slot == 8:
                inventory_open = True
            else:
                selected = slot
            return

    if ui["CRAFT"].collidepoint(pos):
        craft_open = True
        return

    if ui["BREAK"].collidepoint(pos):
        break_block()
        return

    if ui["PLACE"].collidepoint(pos):
        place_block()
        return

    if ui["ATTACK"].collidepoint(pos):
        attack()
        return

    if ui["JUMP"].collidepoint(pos):
        return

# MOB AI
def update_mobs(dt):
    global health, hunger

    for mob in mobs:
        mob["timer"] -= dt

        dx = px-mob["x"]
        dy = py-mob["y"]
        distance = math.hypot(dx, dy)

        if mob["type"] in ("Zombie", "Skeleton", "Creeper"):
            if distance < 7 and distance > 1.0:
                mob["x"] += dx/distance*dt*0.8
                mob["y"] += dy/distance*dt*0.8

            if distance < 1.0 and mob["timer"] <= 0:
                if mode == "SURVIVAL":
                    health = max(0, health-1)
                mob["timer"] = 1.5
        else:
            if mob["timer"] <= 0:
                mob["x"] += random.uniform(-0.5, 0.5)
                mob["y"] += random.uniform(-0.5, 0.5)
                mob["timer"] = random.uniform(1, 3)

# MAIN GAME
def main():
    global angle, pitch, running, selected
    global inventory_open, craft_open, mode
    global show_controls, weapon, px, py, health

    running = True
    last_time = pygame.time.get_ticks()

    while running:
        dt = min(clock.tick(30)/1000, 0.05)
        w, h = screen.get_size()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                held.add(event.key)

                if event.key == pygame.K_ESCAPE:
                    inventory_open = False
                    craft_open = False

                if event.key == pygame.K_9:
                    inventory_open = True

                if pygame.K_1 <= event.key <= pygame.K_8:
                    selected = event.key-pygame.K_1

                if event.key == pygame.K_f:
                    break_block()

                if event.key == pygame.K_g:
                    place_block()

                if event.key == pygame.K_SPACE:
                    pass

                if event.key == pygame.K_e:
                    inventory_open = not inventory_open

                if event.key == pygame.K_c:
                    craft_open = not craft_open

                if event.key == pygame.K_TAB:
                    mode = "SURVIVAL" if mode == "CREATIVE" else "CREATIVE"

                if event.key == pygame.K_v:
                    show_controls = not show_controls

                if event.key == pygame.K_q:
                    weapon = "Bow" if weapon != "Bow" else "Wooden Sword"

            elif event.type == pygame.KEYUP:
                held.discard(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    handle_click(event.pos, w, h)

            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0] and not inventory_open and not craft_open:
                    # Swipe camera
                    if event.rel[0] != 0:
                        angle += event.rel[0]*0.006
                    if event.rel[1] != 0:
                        pitch = max(-100, min(100,
                                     pitch-event.rel[1]*0.5))

            elif event.type == pygame.FINGERDOWN:
                pos = (int(event.x*w), int(event.y*h))
                handle_click(pos, w, h)

            elif event.type == pygame.FINGERMOTION:
                if not inventory_open and not craft_open:
                    angle += event.dx*2.5
                    pitch = max(-100, min(100,
                                 pitch-event.dy*200))

        # KEYBOARD MOVEMENT
        if not inventory_open and not craft_open:
            dx = 0
            dy = 0

            if pygame.K_w in held:
                dx += math.cos(angle)*MOVE_SPEED*dt
                dy += math.sin(angle)*MOVE_SPEED*dt
            if pygame.K_s in held:
                dx -= math.cos(angle)*MOVE_SPEED*dt
                dy -= math.sin(angle)*MOVE_SPEED*dt
            if pygame.K_a in held:
                dx += math.sin(angle)*MOVE_SPEED*dt
                dy -= math.cos(angle)*MOVE_SPEED*dt
            if pygame.K_d in held:
                dx -= math.sin(angle)*MOVE_SPEED*dt
                dy += math.cos(angle)*MOVE_SPEED*dt

            move(dx, dy)

            update_mobs(dt)

        # DRAW
        draw_world()
        draw_weapon(w, h)
        draw_hotbar(w, h)
        draw_controls(w, h)

        txt("MECRAFT", 12, 12, large)
        txt("MODE: "+mode, 12, 53)
        txt("HP: "+str(health), 12, 80)
        txt("HUNGER: "+str(hunger), 12, 106)
        txt("TARGET: 24 CHUNKS", 12, 132, small)
        txt("WEAPON: "+weapon, 12, 150, small)
        txt(message, 12, h-112, small)

        if health <= 0:
            txt("YOU DIED - RESTART GAME", w//2-110, h//2, large)

        if inventory_open:
            draw_inventory(w, h)

        if craft_open:
            draw_crafting(w, h)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

main()
