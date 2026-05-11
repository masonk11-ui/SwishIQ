from matplotlib.patches import Circle, Rectangle, Arc

def draw_court(ax, color="white", lw=1.5):
    # Hoop
    ax.add_patch(Circle((0, 0), 7.5, linewidth=lw, color=color, fill=False))

    # Backboard
    ax.add_patch(Rectangle((-30, -7.5), 60, -1, linewidth=lw, color=color))

    # Paint
    ax.add_patch(Rectangle((-80, -47.5), 160, 190, linewidth=lw, color=color, fill=False))
    ax.add_patch(Rectangle((-60, -47.5), 120, 190, linewidth=lw, color=color, fill=False))

    # Free throw arc
    ax.add_patch(Arc((0, 142.5), 120, 120, theta1=0, theta2=180, linewidth=lw, color=color))
    ax.add_patch(Arc((0, 142.5), 120, 120, theta1=180, theta2=360, linewidth=lw, color=color))

    # Restricted area
    ax.add_patch(Arc((0, 0), 80, 80, theta1=0, theta2=180, linewidth=lw, color=color))

    # Corner 3
    ax.add_patch(Rectangle((-220, -47.5), 0, 140, linewidth=lw, color=color))
    ax.add_patch(Rectangle((220, -47.5), 0, 140, linewidth=lw, color=color))

    # 3PT arc
    ax.add_patch(Arc((0, 0), 475, 475, theta1=22, theta2=158, linewidth=lw, color=color))

    # Center arc (top of half court)
    ax.add_patch(Arc((0, 422.5), 120, 120, theta1=180, theta2=0, linewidth=lw, color=color))
