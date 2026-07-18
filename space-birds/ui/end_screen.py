import pygame

pygame.font.init()

TITLE_FONT = pygame.font.SysFont("bahnschrift", 74, bold=True)
TEXT_FONT = pygame.font.SysFont("bahnschrift", 48)
OTHER_FONT = pygame.font.SysFont("bahnschrift", 24)

def draw_text(screen, text, center, font=TEXT_FONT, color=(255, 255, 255)):

    shadow = font.render(text, True, (0, 0, 0))
    shadow_rect = shadow.get_rect(center= (center[0] + 2, center[1] + 2))

    text_surface = font.render(text, True, color)
    text_surface_rect = text_surface.get_rect(center=center)

    screen.blit(shadow, shadow_rect)
    screen.blit(text_surface, text_surface_rect)

def draw_end_screen(screen, level_won, birds_remaining, score):

    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # Semi-transparent black overlay
    screen.blit(overlay, (0, 0))

    rect = pygame.Rect(0, 0, 700, 600)
    rect.center = (screen.get_width() / 2, screen.get_height() / 2)
    pygame.draw.rect(screen, (50, 50, 50), rect, border_radius=10)

    if level_won:
        draw_text(screen, "LEVEL WON!", (screen.get_width() / 2, screen.get_height() / 2 - 200), font=TITLE_FONT, color=(55, 255, 55))
    else:
        draw_text(screen, "LEVEL FAILED!", (screen.get_width() / 2, screen.get_height() / 2 - 200), font=TITLE_FONT, color=(255, 55, 55))

    draw_text(screen, f"Birds Remaining: {birds_remaining}", (screen.get_width() / 2, screen.get_height() / 2 - 100), font=TEXT_FONT, color=(255, 255, 255))

    draw_text(screen, f"Score: {score}", (screen.get_width() / 2, screen.get_height() / 2 - 50), font=TEXT_FONT, color=(255, 255, 255))

    if level_won:

        draw_text(screen, "Press Enter to Continue", (screen.get_width() / 2, screen.get_height() / 2 + 75), font=OTHER_FONT, color=(255, 255, 255))

        draw_text(screen, "Press Esc to Exit", (screen.get_width() / 2, screen.get_height() / 2 + 275), font=OTHER_FONT, color=(255, 255, 255))

        draw_text(screen, "Press 'R' to Restart Level", (screen.get_width() / 2, screen.get_height() / 2 + 125), font=OTHER_FONT, color=(255, 255, 255))
    
    else:
        draw_text(screen, "Press 'R' to Retry", (screen.get_width() / 2, screen.get_height() / 2 + 75), font=OTHER_FONT, color=(255, 255, 255))

        draw_text(screen, "Press Esc to Exit", (screen.get_width() / 2, screen.get_height() / 2 + 275), font=OTHER_FONT, color=(255, 255, 255))

    pygame.display.flip()