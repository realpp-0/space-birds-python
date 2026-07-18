import pygame

pygame.font.init()

TITLE_FONT = pygame.font.SysFont("bahnschrift", 34, bold=True)
TEXT_FONT = pygame.font.SysFont("bahnschrift", 24)
OTHER_FONT = pygame.font.SysFont("bahnschrift", 16)

def draw_text(screen, text, position, font=TEXT_FONT, color=(255, 255, 255)):
    shadow = font.render(text, True, (0, 0, 0))
    text_surface = font.render(text, True, color)
    screen.blit(shadow, (position[0] + 2, position[1] + 2))
    screen.blit(text_surface, position)

def draw_hud(screen, level, birds_left, pigs_left, score):
    # Draw the level number
    draw_text(screen, f"Level: {level}", (20, 20), font=TITLE_FONT, color=(255, 255, 255))

    # Draw the number of birds left
    draw_text(screen, f"Birds Left: {birds_left}", (20, 60), font=TEXT_FONT, color=(255, 255, 255))

    # Draw the score
    draw_text(screen, f"Score: {score}", (20, 120), font=TEXT_FONT, color=(255, 255, 255))

    # Draw the number of pigs left
    draw_text(screen, f"Pigs Left: {pigs_left}", (20, 90), font=TEXT_FONT, color=(255, 255, 255))

    # Draw the instructions for the player
    draw_text(screen, "Press 'R' to Restart Level", (screen.get_width() - 200, 20), font=OTHER_FONT, color=(255, 255, 255))
