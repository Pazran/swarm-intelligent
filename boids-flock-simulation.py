import pygame
import random
import sys

# Setup environment dimensions
SIM_WIDTH, SIM_HEIGHT = 1270, 720
UI_WIDTH = 300
WIDTH = SIM_WIDTH + UI_WIDTH
HEIGHT = SIM_HEIGHT
NUM_BOIDS = 200

# Global state for UI interaction
SHOW_PERCEPTION = False

class Boid:
    def __init__(self):
        self.position = pygame.Vector2(random.uniform(0, SIM_WIDTH), random.uniform(0, SIM_HEIGHT))
        self.velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * random.uniform(2, 4)
        self.acceleration = pygame.Vector2(0, 0)
        
        # Adjustable parameters (controlled by sliders)
        self.max_speed = 5.0
        self.max_force = 0.15
        self.perception = 60.0
        self.weight_align = 1.0
        self.weight_cohesion = 1.0
        self.weight_separation = 1.5

    def update(self):
        self.position += self.velocity
        self.velocity += self.acceleration
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)
        self.acceleration *= 0  # Reset for next frame

    def draw(self, screen):
        # Optional: draw perception circle for debugging/visualization
        if SHOW_PERCEPTION:
            pygame.draw.circle(screen, (40, 50, 70), (int(self.position.x), int(self.position.y)), int(self.perception), 1)
            
        # Draw a small circle representing the boid
        pygame.draw.circle(screen, (220, 220, 250), (int(self.position.x), int(self.position.y)), 4)
        # Draw a tiny line pointing in its current direction
        if self.velocity.length() > 0:
            direction = self.velocity.normalize() * 8
            pygame.draw.line(screen, (100, 150, 255), self.position, self.position + direction, 2)

    def boundaries(self):
        # Margins to gently turn away from screen edges instead of hard wrapping
        margin = 50
        turn_factor = 0.5
        if self.position.x < margin: self.acceleration.x += turn_factor
        elif self.position.x > SIM_WIDTH - margin: self.acceleration.x -= turn_factor
        if self.position.y < margin: self.acceleration.y += turn_factor
        elif self.position.y > HEIGHT - margin: self.acceleration.y -= turn_factor

    def apply_swarm_rules(self, boids):
        sep_steering = pygame.Vector2(0, 0)
        align_steering = pygame.Vector2(0, 0)
        coh_steering = pygame.Vector2(0, 0)
        
        sep_total = 0
        avg_vel = pygame.Vector2(0, 0)
        avg_pos = pygame.Vector2(0, 0)
        total = 0

        for other in boids:
            if other == self:
                continue
            
            distance = self.position.distance_to(other.position)
            
            if distance < self.perception:
                # Rule 1: Alignment Data
                avg_vel += other.velocity
                # Rule 2: Cohesion Data
                avg_pos += other.position
                total += 1
                
                # Rule 3: Separation Data (Closer items push harder)
                if distance < 25:
                    diff = self.position - other.position
                    if distance > 0:
                        diff /= distance  # Weight by distance
                    sep_steering += diff
                    sep_total += 1

        # Process Alignment
        if total > 0:
            avg_vel /= total
            if avg_vel.length() > 0:
                avg_vel = avg_vel.normalize() * self.max_speed
            align_steering = avg_vel - self.velocity
            if align_steering.length() > self.max_force:
                align_steering.scale_to_length(self.max_force)

            # Process Cohesion
            avg_pos /= total
            coh_desired = avg_pos - self.position
            if coh_desired.length() > 0:
                coh_desired = coh_desired.normalize() * self.max_speed
            coh_steering = coh_desired - self.velocity
            if coh_steering.length() > self.max_force:
                coh_steering.scale_to_length(self.max_force)

        # Process Separation
        if sep_total > 0:
            sep_steering /= sep_total
            if sep_steering.length() > 0:
                sep_steering = sep_steering.normalize() * self.max_speed
            sep_steering -= self.velocity
            if sep_steering.length() > self.max_force:
                sep_steering.scale_to_length(self.max_force)

        # Apply behaviors with dynamic weight multipliers from UI
        self.acceleration += align_steering * self.weight_align
        self.acceleration += coh_steering * self.weight_cohesion
        self.acceleration += sep_steering * self.weight_separation


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
        self.default_val = start_val  # Store default value
        self.label = label
        
        # Calculate initial handle position
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
        # Label and Value text
        text_surf = font.render(f"{self.label}: {self.value:.2f}", True, (200, 210, 230))
        screen.blit(text_surf, (self.rect.x, self.rect.y - 20))
        
        # Track
        pygame.draw.rect(screen, (40, 50, 65), self.rect, border_radius=3)
        # Filled track
        filled_rect = pygame.Rect(self.rect.x, self.rect.y, self.handle_x - self.rect.x, self.rect.height)
        pygame.draw.rect(screen, (100, 150, 255), filled_rect, border_radius=3)
        
        # Handle
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
        # Restrain mouse X to slider track
        mouse_x = max(self.rect.x, min(mouse_x, self.rect.x + self.rect.width))
        ratio = (mouse_x - self.rect.x) / self.rect.width
        self.value = self.min_val + ratio * (self.max_val - self.min_val)
        self.handle_x = mouse_x


# --- MAIN CONTROL STATE ---

class SimulationController:
    def __init__(self):
        self.paused = False
        self.flock = [Boid() for _ in range(NUM_BOIDS)]
        
    def toggle_pause(self, btn):
        self.paused = not self.paused
        btn.text = "START" if self.paused else "PAUSE"

    def reset_flock(self):
        self.flock = [Boid() for _ in range(NUM_BOIDS)]


def main():
    global SHOW_PERCEPTION
    pygame.init()
    pygame.font.init()
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Swarm Intelligence: Interactive Boids Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 14)
    title_font = pygame.font.SysFont("Arial", 16, bold=True)

    controller = SimulationController()

    # --- UI Setup ---
    ui_left = SIM_WIDTH + 20

    # Setup interactive sliders first so buttons can refer to them
    sliders = {
        "max_speed":  Slider(ui_left, 190, 250, 1.0, 10.0, 5.0, "Max Speed"),
        "max_force":  Slider(ui_left, 260, 250, 0.01, 0.5, 0.15, "Max Force"),
        "perception": Slider(ui_left, 330, 250, 10.0, 150.0, 60.0, "Perception Radius"),
        "align":      Slider(ui_left, 430, 250, 0.0, 3.0, 1.0, "Alignment Weight"),
        "cohesion":   Slider(ui_left, 500, 250, 0.0, 3.0, 1.0, "Cohesion Weight"),
        "separation": Slider(ui_left, 570, 250, 0.0, 4.0, 1.5, "Separation Weight")
    }
    
    # Helper function to reset all sliders
    def reset_all_sliders():
        for slider in sliders.values():
            slider.reset_to_default()

    # Setup interactive buttons
    btn_pause = Button(ui_left, 50, 115, 35, "PAUSE", lambda: controller.toggle_pause(btn_pause))
    btn_reset = Button(ui_left + 135, 50, 115, 35, "RESET", controller.reset_flock)
    btn_defaults = Button(ui_left, 95, 250, 35, "RESET DEFAULTS", reset_all_sliders)
    
    buttons = [btn_pause, btn_reset, btn_defaults]

    while True:
        # 1. Handle Events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_v:
                    SHOW_PERCEPTION = not SHOW_PERCEPTION

            # Pass events down to UI controls
            for btn in buttons:
                btn.handle_event(event)
            for slider in sliders.values():
                slider.handle_event(event)

        # 2. Sync Boid properties dynamically with Sliders
        for boid in controller.flock:
            boid.max_speed = sliders["max_speed"].value
            boid.max_force = sliders["max_force"].value
            boid.perception = sliders["perception"].value
            boid.weight_align = sliders["align"].value
            boid.weight_cohesion = sliders["cohesion"].value
            boid.weight_separation = sliders["separation"].value

        # 3. Update Simulation (If not paused)
        if not controller.paused:
            for boid in controller.flock:
                boid.boundaries()
                boid.apply_swarm_rules(controller.flock)
                boid.update()

        # 4. Drawing Pass
        screen.fill((20, 24, 33))  # Dark simulation space

        # Draw Boids
        for boid in controller.flock:
            boid.draw(screen)

        # Draw UI Sidebar Partition
        pygame.draw.rect(screen, (28, 33, 45), (SIM_WIDTH, 0, UI_WIDTH, HEIGHT))
        pygame.draw.line(screen, (45, 55, 75), (SIM_WIDTH, 0), (SIM_WIDTH, HEIGHT), 2)

        # Draw Side Panel Text Headers
        title_surf = title_font.render("SIMULATION CONTROLS", True, (100, 150, 255))
        screen.blit(title_surf, (ui_left, 15))
        
        behavior_surf = title_font.render("BEHAVIOR WEIGHTS", True, (100, 150, 255))
        screen.blit(behavior_surf, (ui_left, 385))
        
        hotkey_surf = font.render("Press 'V' to toggle Perception Fields", True, (130, 145, 170))
        screen.blit(hotkey_surf, (ui_left, HEIGHT - 35))

        # Render UI components
        for btn in buttons:
            btn.draw(screen, font)
        for slider in sliders.values():
            slider.draw(screen, font)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()