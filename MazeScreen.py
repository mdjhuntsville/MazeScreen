import pygame
import math
import random

# =============================
# Maze Generation: Recursive Backtracking
# =============================
def generate_maze(width, height):
    """
    Generate a maze represented as a 2D grid.
    0: corridor
    1: wall (initial placeholder; later converted to a color index)
    """
    maze = [[1 for _ in range(width)] for _ in range(height)]
    start_x, start_y = 1, 1
    maze[start_y][start_x] = 0
    stack = [(start_x, start_y)]
    while stack:
        x, y = stack[-1]
        neighbors = []
        for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
            nx, ny = x + dx, y + dy
            if 0 < nx < width - 1 and 0 < ny < height - 1 and maze[ny][nx] == 1:
                neighbors.append((nx, ny))
        if neighbors:
            nx, ny = random.choice(neighbors)
            maze[ny][nx] = 0
            # Remove the wall between current and neighbor:
            maze[y + (ny - y) // 2][x + (nx - x) // 2] = 0
            stack.append((nx, ny))
        else:
            stack.pop()
    return maze

# =============================
# Wall Color Definitions
# =============================
# We'll treat the numbers 1, 2, 3, and 4 as indices for our wall colors.
WALL_COLORS = {
    1: (0, 0, 255),    # Blue
    2: (255, 0, 0),    # Red
    3: (0, 255, 0),    # Green
    4: (255, 255, 0)   # Yellow
}

# =============================
# Main Function: Raycasting + Keyboard Control
# =============================
def main():
    pygame.init()
    screen_width = 640
    screen_height = 480
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Maze Screensaver - Keyboard Control")
    clock = pygame.time.Clock()

    # Maze dimensions must be odd numbers.
    maze_width, maze_height = 21, 21
    maze = generate_maze(maze_width, maze_height)

    # Post-process the maze: assign a random color index (from 1 to 4) to every wall cell.
    for y in range(maze_height):
        for x in range(maze_width):
            if maze[y][x] != 0:
                maze[y][x] = random.choice([1, 2, 3, 4])

    # Initial camera/player position and orientation.
    posX, posY = 1.5, 1.5      # Starting at (1.5, 1.5) for sub-cell precision.
    dirX, dirY = 1.0, 0.0      # Initially facing east.
    # The camera plane (perpendicular to the direction vector) controls the FOV.
    planeX, planeY = 0.0, 0.66

    move_speed = 0.05  # Movement speed per frame.
    rot_speed = 0.04   # Rotation speed (radians per frame).

    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Keyboard Input for Movement ---
        keys = pygame.key.get_pressed()
        # Forward: E key
        if keys[pygame.K_e]:
            newX = posX + dirX * move_speed
            newY = posY + dirY * move_speed
            if maze[int(posY)][int(newX)] == 0:
                posX = newX
            if maze[int(newY)][int(posX)] == 0:
                posY = newY
        # Backward: D key
        if keys[pygame.K_d]:
            newX = posX - dirX * move_speed
            newY = posY - dirY * move_speed
            if maze[int(posY)][int(newX)] == 0:
                posX = newX
            if maze[int(newY)][int(posX)] == 0:
                posY = newY
        # Rotate left: F key
        if keys[pygame.K_f]:
            angle = rot_speed  # Rotate counter-clockwise.
            oldDirX = dirX
            dirX = dirX * math.cos(angle) - dirY * math.sin(angle)
            dirY = oldDirX * math.sin(angle) + dirY * math.cos(angle)
            oldPlaneX = planeX
            planeX = planeX * math.cos(angle) - planeY * math.sin(angle)
            planeY = oldPlaneX * math.sin(angle) + planeY * math.cos(angle)
        # Rotate right: S key
        if keys[pygame.K_s]:
            angle = -rot_speed  # Rotate clockwise.
            oldDirX = dirX
            dirX = dirX * math.cos(angle) - dirY * math.sin(angle)
            dirY = oldDirX * math.sin(angle) + dirY * math.cos(angle)
            oldPlaneX = planeX
            planeX = planeX * math.cos(angle) - planeY * math.sin(angle)
            planeY = oldPlaneX * math.sin(angle) + planeY * math.cos(angle)

        # --- Raycasting Rendering ---
        # Fill background (a neutral gray for floor/ceiling).
        screen.fill((100, 100, 100))

        # For every vertical stripe on the screen...
        for x in range(screen_width):
            # Calculate ray position and direction.
            cameraX = 2 * x / screen_width - 1  # X-coordinate in camera space.
            rayDirX = dirX + planeX * cameraX
            rayDirY = dirY + planeY * cameraX

            # Map square the ray is in.
            mapX = int(posX)
            mapY = int(posY)

            # Length of ray from one x or y-side to next.
            deltaDistX = abs(1 / rayDirX) if rayDirX != 0 else 1e30
            deltaDistY = abs(1 / rayDirY) if rayDirY != 0 else 1e30

            # Calculate step and initial sideDist.
            if rayDirX < 0:
                stepX = -1
                sideDistX = (posX - mapX) * deltaDistX
            else:
                stepX = 1
                sideDistX = (mapX + 1.0 - posX) * deltaDistX
            if rayDirY < 0:
                stepY = -1
                sideDistY = (posY - mapY) * deltaDistY
            else:
                stepY = 1
                sideDistY = (mapY + 1.0 - posY) * deltaDistY

            # Perform DDA (Digital Differential Analysis)
            hit = False
            side = None
            while not hit:
                # Jump to next map square, either in x-direction or y-direction.
                if sideDistX < sideDistY:
                    sideDistX += deltaDistX
                    mapX += stepX
                    side = 0
                else:
                    sideDistY += deltaDistY
                    mapY += stepY
                    side = 1
                # Check if ray is outside bounds.
                if mapX < 0 or mapX >= maze_width or mapY < 0 or mapY >= maze_height:
                    hit = True
                    break
                # A hit occurs if the map cell is non-zero.
                if maze[mapY][mapX] != 0:
                    hit = True

            # Calculate the perpendicular distance to the wall.
            if side == 0:
                perpWallDist = (mapX - posX + (1 - stepX) / 2) / rayDirX
            else:
                perpWallDist = (mapY - posY + (1 - stepY) / 2) / rayDirY

            # Calculate the height of the wall slice to draw.
            lineHeight = int(screen_height / (perpWallDist + 0.0001))
            drawStart = max(-lineHeight // 2 + screen_height // 2, 0)
            drawEnd = min(lineHeight // 2 + screen_height // 2, screen_height - 1)

            # Determine the wall's color based on the maze cell.
            # If out-of-bounds, fall back to white.
            if mapX < 0 or mapX >= maze_width or mapY < 0 or mapY >= maze_height:
                wall_color = (255, 255, 255)
            else:
                wall_type = maze[mapY][mapX]
                wall_color = WALL_COLORS.get(wall_type, (255, 255, 255))

            # Shade the wall a bit darker if we hit a y-side.
            if side == 1:
                wall_color = tuple(int(c * 0.8) for c in wall_color)

            # Draw the vertical line for this stripe.
            pygame.draw.line(screen, wall_color, (x, drawStart), (x, drawEnd))

        pygame.display.flip()
        clock.tick(60)  # Limit to 60 FPS.

    pygame.quit()

if __name__ == "__main__":
    main()
