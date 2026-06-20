import pygame
import random
import sys
import math

# Setup environment dimensions
SIM_WIDTH, SIM_HEIGHT = 1270, 720
UI_WIDTH = 300
WIDTH = SIM_WIDTH + UI_WIDTH
HEIGHT = SIM_HEIGHT

DEPOT_POS = pygame.Vector2(SIM_WIDTH // 2, SIM_HEIGHT // 2)

class LogisticsSimulation:
    def __init__(self):
        self.paused = False
        self.num_houses = 10
        self.houses = []
        self.reset_houses()
        
        # Pheromone matrix: pheromone_matrix[i][j] stores scent between house i and house j
        # Index 0 is always the DEPOT (Home)
        self.pheromone_matrix = []
        self.reset_pheromones()
        
        # Parameters controlled by sliders
        self.evaporation_rate = 0.90
        self.alpha = 1.0  # Importance of pheromone
        self.beta = 2.0   # Importance of distance (greediness)
        
        self.ants_per_frame = 25
        self.best_distance = float('inf')
        self.best_path = []

    def reset_houses(self):
        self.houses = [DEPOT_POS]  # First element is always the depot
        for _ in range(self.num_houses):
            # Keep houses away from the very edges
            x = random.uniform(50, SIM_WIDTH - 50)
            y = random.uniform(50, SIM_HEIGHT - 50)
            self.houses.append(pygame.Vector2(x, y))
        self.reset_pheromones()
        self.best_distance = float('inf')
        self.best_path = []

    def reset_pheromones(self):
        n = len(self.houses)
        # Initialize all paths with a tiny baseline of pheromone so ants can start exploring
        self.pheromone_matrix = [[0.1 for _ in range(n)] for _ in range(n)]

    def update(self):
        if self.paused or len(self.houses) <= 1:
            return

        n = len(self.houses)
        
        # 1. Evaporation Phase
        for i in range(n):
            for j in range(n):
                self.pheromone_matrix[i][j] *= self.evaporation_rate
                if self.pheromone_matrix[i][j] < 0.05:
                    self.pheromone_matrix[i][j] = 0.05

        # 2. Virtual Ants Journey (Clipboard Math)
        # Array to hold how much pheromone needs to be added to each path at the end of the frame
        pheromone_deposit = [[0.0 for _ in range(n)] for _ in range(n)]

        for _ in range(self.ants_per_frame):
            path = [0]  # Start at Depot (Index 0)
            unvisited = list(range(1, n))

            while unvisited:
                current = path[-1]
                
                # Calculate probabilities for picking the next house
                probabilities = []
                total_weight = 0.0
                
                for idx in unvisited:
                    dist = self.houses[current].distance_to(self.houses[idx])
                    if dist == 0: dist = 0.1
                    
                    # Core ACO formula components:
                    # Scent pull = (pheromone strength)^alpha
                    # Distance pull = (1 / distance)^beta  [Closer is better]
                    pheromone_attr = math.pow(self.pheromone_matrix[current][idx], self.alpha)
                    distance_attr = math.pow(1.0 / dist, self.beta)
                    
                    weight = pheromone_attr * distance_attr
                    probabilities.append((idx, weight))
                    total_weight += weight

                # Roulette Wheel selection to pick the next house based on weights
                if total_weight == 0:
                    next_house = random.choice(unvisited)
                else:
                    r = random.uniform(0, total_weight)
                    running_sum = 0
                    next_house = unvisited[0]
                    for idx, weight in probabilities:
                        running_sum += weight
                        if running_sum >= r:
                            next_house = idx
                            break
                
                path.append(next_house)
                unvisited.remove(next_house)
            
            path.append(0)  # Return back to Depot

            # Calculate total mileage of this complete circuit
            total_distance = 0.0
            for k in range(len(path) - 1):
                total_distance += self.houses[path[k]].distance_to(self.houses[path[k+1]])

            # Keep track of the all-time absolute best path found
            if total_distance < self.best_distance:
                self.best_distance = total_distance
                self.best_path = path

            # Retroactive calculation: Determine pheromone deposit strength based on total route quality
            # Formula: Deposit = Q / Total Distance (Shorter loops get exponentially brighter coats)
            deposit_strength = 2000.0 / total_distance
            
            for k in range(len(path) - 1):
                u, v = path[k], path[k+1]
                pheromone_deposit[u][v] += deposit_strength
                pheromone_deposit[v][u] += deposit_strength

        # 3. Add all retroactive deposits onto the global map matrix
        for i in range(n):
            for j in range(n):
                self.pheromone_matrix[i][j] += pheromone_deposit[i][j]


    def draw(self, screen, font):
        n = len(self.houses)
        
        # Draw Pheromone Streets (Connecting roads)
        for i in range(n):
            for j in range(i + 1, n):
                val = self.pheromone_matrix[i][j]
                if val > 0.15:
                    # Turn intensity into line thickness and brightness
                    thickness = min(6, int(val * 0.7) + 1)
                    brightness = min(255, int(val * 15))
                    color = (int(brightness * 0.4), int(brightness * 0.1), brightness)
                    pygame.draw.line(screen, color, self.houses[i], self.houses[j], thickness)

        # Draw All-Time Best Route (Thin golden guiding line)
        if len(self.best_path) > 1:
            for k in range(len(self.best_path) - 1):
                pygame.draw.line(screen, (240, 190, 60), self.houses[self.best_path[k]], self.houses[self.best_path[k+1]], 1)

        # Draw Delivery Destinations (Houses)
        for idx, house in enumerate(self.houses):
            if idx == 0:
                continue # Skip Depot for now to layer it on top
            pygame.draw.circle(screen, (230, 90, 40), (int(house.x), int(house.y)), 7)
            pygame.draw.circle(screen, (255, 140, 100), (int(house.x), int(house.y)), 7, 1)
            
        # Draw Depot Headquarters (Home base)
        pygame.draw.circle(screen, (0, 110, 255), (int(DEPOT_POS.x), int(DEPOT_POS.y)), 14)
        pygame.draw.circle(screen, (100, 180, 255), (int(DEPOT_POS.x), int(DEPOT_POS.y)), 14, 2)
        home_txt = font.render("HQ", True, (255, 255, 255))
        screen.blit(home_txt, (DEPOT_POS.x - 8, DEPOT_POS.y - 7))


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
    def __init__(self, x, y, w, min_val, max_val, start_val, label, is_int=False):
        self.rect = pygame.Rect(x, y, w, 10)
        self.min_val = min_val
        self.max_val = max_val
        self.value = start_val
        self.default_val = start_val
        self.label = label
        self.is_int = is_int
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
        val_str = f"{int(self.value)}" if self.is_int else f"{self.value:.3f}"
        text_surf = font.render(f"{self.label}: {val_str}", True, (200, 210, 230))
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
        if self.is_int:
            self.value = round(self.value)
        self.handle_x = mouse_x


# --- MAIN ENGINE ENTRY ---

def main():
    pygame.init()
    pygame.font.init()
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Swarm Intelligence: ACO Logistics Optimizer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 14)
    title_font = pygame.font.SysFont("Arial", 16, bold=True)

    sim = LogisticsSimulation()
    ui_left = SIM_WIDTH + 20

    # Setup Sliders
    sliders = {
        "houses":      Slider(ui_left, 190, 250, 4, 45, 12, "Number of Houses", is_int=True),
        "evaporation": Slider(ui_left, 260, 250, 0.70, 0.99, 0.90, "Pheromone Retention Rate"),
        "alpha":       Slider(ui_left, 360, 250, 0.0, 5.0, 1.0, "Scent Weight (Pheromone Alpha)"),
        "beta":        Slider(ui_left, 430, 250, 0.0, 5.0, 2.5, "Greed Weight (Distance Beta)"),
        "ants":        Slider(ui_left, 530, 250, 5, 100, 25, "Virtual Ants per Frame", is_int=True)
    }

    def reset_all_sliders():
        for slider in sliders.values():
            slider.reset_to_default()
        sim.num_houses = int(sliders["houses"].value)
        sim.reset_houses()

    def toggle_pause():
        sim.paused = not sim.paused
        btn_pause.text = "START" if sim.paused else "PAUSE"

    def trigger_randomize():
        sim.num_houses = int(sliders["houses"].value)
        sim.reset_houses()

    # Setup Controls
    btn_pause = Button(ui_left, 50, 115, 35, "PAUSE", toggle_pause)
    btn_random = Button(ui_left + 135, 50, 115, 35, "RANDOMIZE", trigger_randomize)
    btn_defaults = Button(ui_left, 95, 250, 35, "RESET DEFAULTS", reset_all_sliders)
    buttons = [btn_pause, btn_random, btn_defaults]

    while True:
        # 1. Capture Inputs
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            for btn in buttons:
                btn.handle_event(event)
            for slider in sliders.values():
                slider.handle_event(event)

        # Check if the "number of houses" slider was changed while interacting
        if int(sliders["houses"].value) != sim.num_houses:
            sim.num_houses = int(sliders["houses"].value)
            sim.reset_houses()

        # 2. Sync Parameters From Sliders
        sim.evaporation_rate = sliders["evaporation"].value
        sim.alpha = sliders["alpha"].value
        sim.beta = sliders["beta"].value
        sim.ants_per_frame = int(sliders["ants"].value)

        # 3. Compute Optimization Loop
        sim.update()

        # 4. Render
        screen.fill((20, 24, 33))

        # Render Core Simulation Space
        sim.draw(screen, font)

        # Render UI Background Partition
        pygame.draw.rect(screen, (28, 33, 45), (SIM_WIDTH, 0, UI_WIDTH, HEIGHT))
        pygame.draw.line(screen, (45, 55, 75), (SIM_WIDTH, 0), (SIM_WIDTH, HEIGHT), 2)

        # Render Interface Labels
        title_surf = title_font.render("SIMULATION CONTROLS", True, (100, 150, 255))
        screen.blit(title_surf, (ui_left, 15))
        
        math_surf = title_font.render("ACO ALGORITHM BALANCING", True, (100, 150, 255))
        screen.blit(math_surf, (ui_left, 315))
        
        perf_surf = title_font.render("ENGINE SETTINGS", True, (100, 150, 255))
        screen.blit(perf_surf, (ui_left, 485))

        # Draw the Best Score Found Live
        score_text = "Best Distance: " + (f"{sim.best_distance:.1f} km" if sim.best_distance != float('inf') else "Calculating...")
        score_surf = title_font.render(score_text, True, (240, 190, 60))
        screen.blit(score_surf, (ui_left, HEIGHT - 35))

        # MAP LEGENDS
        legend_y = HEIGHT - 35
        
        # 1. Depot Indicator
        pygame.draw.circle(screen, (0, 110, 255), (40, legend_y + 7), 8)
        depot_lbl = font.render("HQ / Depot", True, (200, 210, 230))
        screen.blit(depot_lbl, (55, legend_y))
        
        # 2. House Indicator
        pygame.draw.circle(screen, (230, 90, 40), (160, legend_y + 7), 5)
        house_lbl = font.render("Delivery House", True, (200, 210, 230))
        screen.blit(house_lbl, (175, legend_y))
        
        # 3. Pheromone Highway Indicator
        pygame.draw.line(screen, (100, 25, 255), (300, legend_y + 7), (330, legend_y + 7), 4)
        trail_lbl = font.render("Active Pheromone Path", True, (200, 210, 230))
        screen.blit(trail_lbl, (340, legend_y))
        
        # 4. Record Shortcut Indicator
        pygame.draw.line(screen, (240, 190, 60), (510, legend_y + 7), (540, legend_y + 7), 1)
        record_lbl = font.render("All-Time Best Route Discovered", True, (200, 210, 230))
        screen.blit(record_lbl, (550, legend_y))

        # Final Draw for controls
        for btn in buttons:
            btn.draw(screen, font)
        for slider in sliders.values():
            slider.draw(screen, font)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()