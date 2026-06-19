import pygame
import random
import sys
import math

# Setup environment dimensions
SIM_WIDTH, SIM_HEIGHT = 1270, 720
UI_WIDTH = 300
WIDTH = SIM_WIDTH + UI_WIDTH
HEIGHT = SIM_HEIGHT

NUM_ANTS = 250
COLONY_POS = pygame.Vector2(SIM_WIDTH // 2, SIM_HEIGHT // 2)
FOOD_POSITIONS = [
    pygame.Vector2(200, 200),
    pygame.Vector2(1000, 150),
    pygame.Vector2(300, 550),
    pygame.Vector2(950, 580)
]
FOOD_RADIUS = 25

class Ant:
    def __init__(self):
        self.position = pygame.Vector2(COLONY_POS.x, COLONY_POS.y)
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = 2.5
        self.has_food = False
        
        # Adjustable parameters via sliders
        self.sensor_angle = 45 * (math.pi / 180) # Angle of left/right sensors
        self.sensor_dist = 25.0                 # How far ahead they smell
        self.wander_strength = 0.25             # Random jitter strength

    def update(self, pheromone_grid):
        if not self.has_food:
            # Look for food nearby
            for food in FOOD_POSITIONS:
                if self.position.distance_to(food) < FOOD_RADIUS:
                    self.has_food = True
                    self.angle += math.pi # Turn back toward home
                    return

            # Smell around for pheromones
            self.steer_towards_pheromones(pheromone_grid)
            
            # Add random wander jitter
            self.angle += random.uniform(-self.wander_strength, self.wander_strength)
            
            # Move forward
            self.position.x += math.cos(self.angle) * self.speed
            self.position.y += math.sin(self.angle) * self.speed
            
            # Constrain to simulation boundaries
            self.boundaries()
        else:
            # Heading straight back to colony (simplified homing instinct)
            to_colony = COLONY_POS - self.position
            if to_colony.length() < 15:
                self.has_food = False
                self.angle += math.pi # Head back out for food
            else:
                to_colony = to_colony.normalize()
                self.angle = math.atan2(to_colony.y, to_colony.x)
                self.position += to_colony * self.speed
                
                # Deposit pheromone trail on the way back home
                grid_x = int(self.position.x // 10)
                grid_y = int(self.position.y // 10)
                if 0 <= grid_x < SIM_WIDTH // 10 and 0 <= grid_y < SIM_HEIGHT // 10:
                    pheromone_grid[grid_x][grid_y] = min(255, pheromone_grid[grid_x][grid_y] + 35)

    def steer_towards_pheromones(self, pheromone_grid):
        # Calculate positions of 3 forward-facing smell sensors (Left, Center, Right)
        center_sensor = self.position + pygame.Vector2(math.cos(self.angle), math.sin(self.angle)) * self.sensor_dist
        left_sensor = self.position + pygame.Vector2(math.cos(self.angle - self.sensor_angle), math.sin(self.angle - self.sensor_angle)) * self.sensor_dist
        right_sensor = self.position + pygame.Vector2(math.cos(self.angle + self.sensor_angle), math.sin(self.angle + self.sensor_angle)) * self.sensor_dist
        
        # Helper to read pheromone value at a specific screen coordinate
        def get_pheromone_value(pos):
            gx, gy = int(pos.x // 10), int(pos.y // 10)
            if 0 <= gx < SIM_WIDTH // 10 and 0 <= gy < SIM_HEIGHT // 10:
                return pheromone_grid[gx][gy]
            return 0

        w_center = get_pheromone_value(center_sensor)
        w_left = get_pheromone_value(left_sensor)
        w_right = get_pheromone_value(right_sensor)

        # Steer towards the strongest scent
        if w_center > w_left and w_center > w_right:
            pass # Keep going straight
        elif w_left > w_right:
            self.angle -= 0.1  # Turn left gently
        elif w_right > w_left:
            self.angle += 0.1  # Turn right gently

    def boundaries(self):
        if self.position.x < 10 or self.position.x > SIM_WIDTH - 10:
            self.angle = math.pi - self.angle
            self.position.x = max(10, min(self.position.x, SIM_WIDTH - 10))
        if self.position.y < 10 or self.position.y > SIM_HEIGHT - 10:
            self.angle = -self.angle
            self.position.y = max(10, min(self.position.y, SIM_HEIGHT - 10))

    def draw(self, screen):
        # Draw ant as a small dot (Green if carrying food, reddish-white if looking)
        color = (50, 255, 100) if self.has_food else (200, 200, 220)
        pygame.draw.circle(screen, color, (int(self.position.x), int(self.position.y)), 3)


# --- UI COMPONENTS ---

class Button:
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.color = (50, 70, 100)
        self.hover_color = (70, 95, 130)

    def draw(self, screen, font):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (100, 150, 255), self.rect, width=1, border_radius=5)
        
        txt_surf = font.render(self.text, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()


class Slider:
    def __init__(self, x, y, w, min_val, max_val, start_val, label):
        self.rect = pygame.Rect(x, y, w, 10)
        self.min_val = min_val
        self.max_val = max_val
        self.value = start_val
        self.default_val = start_val
        self.label = label
        self.handle_radius = 8
        self.dragging = False
        self.update_handle_pos()

    def update_handle_pos(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.handle_x = self.rect.x + int(ratio * self.rect.width)

    def reset_to_default(self):
        self.value = self.default_val
        self.update_handle_pos()

    def draw(self, screen, font):
        text_surf = font.render(f"{self.label}: {self.value:.2f}", True, (200, 210, 230))
        screen.blit(text_surf, (self.rect.x, self.rect.y - 20))
        
        pygame.draw.rect(screen, (40, 50, 65), self.rect, border_radius=3)
        filled_rect = pygame.Rect(self.rect.x, self.rect.y, self.handle_x - self.rect.x, self.rect.height)
        pygame.draw.rect(screen, (100, 150, 255), filled_rect, border_radius=3)
        
        mouse_pos = pygame.mouse.get_pos()
        handle_rect = pygame.Rect(self.handle_x - self.handle_radius, self.rect.y + 5 - self.handle_radius, self.handle_radius*2, self.handle_radius*2)
        color = (140, 180, 255) if handle_rect.collidepoint(mouse_pos) or self.dragging else (100, 150, 255)
        pygame.draw.circle(screen, color, (self.handle_x, self.rect.y + 5), self.handle_radius)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_rect = pygame.Rect(self.handle_x - self.handle_radius, self.rect.y + 5 - self.handle_radius, self.handle_radius*2, self.handle_radius*2)
            if handle_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_value(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_value(event.pos[0])

    def update_value(self, mouse_x):
        mouse_x = max(self.rect.x, min(mouse_x, self.rect.x + self.rect.width))
        ratio = (mouse_x - self.rect.x) / self.rect.width
        self.value = self.min_val + ratio * (self.max_val - self.min_val)
        self.handle_x = mouse_x


# --- SIMULATION STATE MANAGEMENT ---

class SimulationController:
    def __init__(self):
        self.paused = False
        self.colony = [Ant() for _ in range(NUM_ANTS)]
        # Grid to hold pheromone values (scaled down by 10 for performance)
        self.pheromone_grid = [[0.0 for _ in range(SIM_HEIGHT // 10)] for _ in range(SIM_WIDTH // 10)]
        self.evaporation_rate = 0.995

    def toggle_pause(self, btn):
        self.paused = not self.paused
        btn.text = "START" if self.paused else "PAUSE"

    def reset_simulation(self):
        self.colony = [Ant() for _ in range(NUM_ANTS)]
        self.pheromone_grid = [[0.0 for _ in range(SIM_HEIGHT // 10)] for _ in range(SIM_WIDTH // 10)]


def main():
    pygame.init()
    pygame.font.init()
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Swarm Intelligence: Interactive Ant Colony Optimization")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 14)
    title_font = pygame.font.SysFont("Arial", 16, bold=True)

    controller = SimulationController()
    ui_left = SIM_WIDTH + 20

    # Setup Sliders
    sliders = {
        "speed":        Slider(ui_left, 190, 250, 1.0, 5.0, 2.5, "Ant Speed"),
        "wander":       Slider(ui_left, 260, 250, 0.1, 1.5, 0.25, "Wander Randomness (Jitter)"),
        "sensor_dist":  Slider(ui_left, 330, 250, 10.0, 60.0, 25.0, "Sensor Distance"),
        "sensor_angle": Slider(ui_left, 430, 250, 15.0, 90.0, 45.0, "Sensor Spread Angle"),
        "evaporation":  Slider(ui_left, 500, 250, 0.95, 0.999, 0.995, "Pheromone Retention Rate")
    }

    def reset_all_sliders():
        for slider in sliders.values():
            slider.reset_to_default()

    # Setup Controls
    btn_pause = Button(ui_left, 50, 115, 35, "PAUSE", lambda: controller.toggle_pause(btn_pause))
    btn_reset = Button(ui_left + 135, 50, 115, 35, "RESET", controller.reset_simulation)
    btn_defaults = Button(ui_left, 95, 250, 35, "RESET DEFAULTS", reset_all_sliders)
    buttons = [btn_pause, btn_reset, btn_defaults]

    while True:
        # 1. Events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            for btn in buttons:
                btn.handle_event(event)
            for slider in sliders.values():
                slider.handle_event(event)

        # 2. Sync Sliders with Simulation Parameters
        controller.evaporation_rate = sliders["evaporation"].value
        for ant in controller.colony:
            ant.speed = sliders["speed"].value
            ant.wander_strength = sliders["wander"].value
            ant.sensor_dist = sliders["sensor_dist"].value
            ant.sensor_angle = sliders["sensor_angle"].value * (math.pi / 180)

        # 3. Physics / Rules Updates
        if not controller.paused:
            # Evaporate pheromones over time
            for x in range(SIM_WIDTH // 10):
                for y in range(SIM_HEIGHT // 10):
                    controller.pheromone_grid[x][y] *= controller.evaporation_rate

            # Update ants
            for ant in controller.colony:
                ant.update(controller.pheromone_grid)

        # 4. Rendering Pass
        screen.fill((20, 24, 33)) # Background space

        # Draw Pheromone Trails (Rendered as glowing purple grids)
        for x in range(SIM_WIDTH // 10):
            for y in range(SIM_HEIGHT // 10):
                val = controller.pheromone_grid[x][y]
                if val > 1:
                    # Map pheromone intensity to an Alpha/Color shade
                    alpha_color = (int(val * 0.4), int(val * 0.1), int(val))
                    pygame.draw.rect(screen, alpha_color, (x * 10, y * 10, 10, 10))

        # Draw Home Colony Base
        pygame.draw.circle(screen, (0, 110, 255), (int(COLONY_POS.x), int(COLONY_POS.y)), 18)
        pygame.draw.circle(screen, (100, 180, 255), (int(COLONY_POS.x), int(COLONY_POS.y)), 18, 2)
        home_txt = font.render("HOME", True, (255, 255, 255))
        screen.blit(home_txt, (COLONY_POS.x - 17, COLONY_POS.y - 7))

        # Draw Food Patches
        for food in FOOD_POSITIONS:
            pygame.draw.circle(screen, (230, 170, 40), (int(food.x), int(food.y)), FOOD_RADIUS)
            food_txt = font.render("FOOD", True, (20, 24, 33))
            screen.blit(food_txt, (food.x - 17, food.y - 7))

        # Draw Ants
        for ant in controller.colony:
            ant.draw(screen)

        # Draw Sidebar UI Partition
        pygame.draw.rect(screen, (28, 33, 45), (SIM_WIDTH, 0, UI_WIDTH, HEIGHT))
        pygame.draw.line(screen, (45, 55, 75), (SIM_WIDTH, 0), (SIM_WIDTH, HEIGHT), 2)

        # Draw Sidebar Labels
        title_surf = title_font.render("SIMULATION CONTROLS", True, (100, 150, 255))
        screen.blit(title_surf, (ui_left, 15))
        
        sensor_surf = title_font.render("ANT SENSOR SETTINGS", True, (100, 150, 255))
        screen.blit(sensor_surf, (ui_left, 385))

        # Render UI Buttons & Sliders
        for btn in buttons:
            btn.draw(screen, font)
        for slider in sliders.values():
            slider.draw(screen, font)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()