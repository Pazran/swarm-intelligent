import pygame
import random
import sys

# Setup environment dimensions
WIDTH, HEIGHT = 1000, 700
NUM_BOIDS = 80

class Boid:
    def __init__(self):
        self.position = pygame.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
        self.velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * random.uniform(2, 4)
        self.acceleration = pygame.Vector2(0, 0)
        self.max_speed = 5
        self.max_force = 0.15
        self.perception = 60  # How far the boid can see

    def update(self):
        self.position += self.velocity
        self.velocity += self.acceleration
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)
        self.acceleration *= 0  # Reset for next frame

    def draw(self, screen):
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
        elif self.position.x > WIDTH - margin: self.acceleration.x -= turn_factor
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

        # Apply behaviors with fine-tuned weight multipliers
        self.acceleration += align_steering * 1.0
        self.acceleration += coh_steering * 1.0
        self.acceleration += sep_steering * 1.5

def main():
    pygame.init()
    screen = pygame.display.set_with = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Swarm Intelligence: Boids Simulation")
    clock = pygame.time.Clock()

    # Create the flock
    flock = [Boid() for _ in range(NUM_BOIDS)]

    while True:
        screen.fill((20, 24, 33))  # Deep dark space aesthetic
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Update and draw all agents
        for boid in flock:
            boid.boundaries()
            boid.apply_swarm_rules(flock)
            boid.update()
            boid.draw(screen)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()