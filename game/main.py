
def _run_executive_board(screen, lp_balance):
    """Displays the Executive Board screen for meta-progression."""
    # Basic background and LP display
    background_color = (30, 40, 35) # Dark, desaturated green/blue
    screen.fill(background_color)

    # LP Display
    f_med = pygame.font.SysFont("couriernew", 13, bold=True)
    lp_label = f_med.render(f"LEGACY POINTS: {lp_balance:,}", True, (0, 255, 204))
    screen.blit(lp_label, (10, 10))

    # Placeholder for Tech Tree Grid
    tech_tree_placeholder_text = pygame.font.SysFont("couriernew", 10).render("TECH TREE GRID AREA (TO BE IMPLEMENTED)", True, (100, 100, 100))
    screen.blit(tech_tree_placeholder_text, (100, 100))

    # Placeholder for Purchase Button (will need interaction logic)
    purchase_button_rect = pygame.Rect(screen.get_width() - 200, screen.get_height() - 50, 150, 40)
    pygame.draw.rect(screen, (0, 200, 120), purchase_button_rect) # Green "Purchase" button
    pygame.draw.rect(screen, (0, 50, 38), purchase_button_rect, 2) # Border
    btn_text = pygame.font.SysFont("couriernew", 12, bold=True).render("PURCHASE", True, (255, 255, 255))
    screen.blit(btn_text, (purchase_button_rect.centerx - btn_text.get_width() // 2, purchase_button_rect.centery - btn_text.get_height() // 2))

    # Back button
    back_button_rect = pygame.Rect(10, screen.get_height() - 50, 100, 40)
    pygame.draw.rect(screen, (180, 40, 40), back_button_rect) # Red "Back" button
    pygame.draw.rect(screen, (60, 0, 0), back_button_rect, 2) # Border
    back_text = pygame.font.SysFont("couriernew", 12, bold=True).render("BACK", True, (255, 255, 255))
    screen.blit(back_text, (back_button_rect.centerx - back_text.get_width() // 2, back_button_rect.centery - back_text.get_height() // 2))

# Note: This function needs to be called from the main game loop (e.g., from main() or _run_mission)
# and interaction logic for buttons/tech tree needs to be added.
