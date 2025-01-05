
show_buttons = False


running = True
while running:
    screen.fill((34, 139, 34)) 
    screen.blit(table_image, (112, 150))  


    for player in players:
        player.draw(screen)


    if show_buttons:
        for button in buttons:
            button.draw(screen)


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
          
            if players[-1].rect.collidepoint(pos): 
                show_buttons = True  
          
            for button in buttons:
                if button.is_clicked(pos) and show_buttons:
                    print(f"Button '{button.text}' clicked! Action: {button.action}")

    pygame.display.flip()

pygame.quit()