from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
                            QGraphicsRectItem, QGraphicsEllipseItem)
from PyQt5.QtGui import QBrush
from PyQt5.QtCore import Qt, QEvent
from controllers.imageToArray import floorplan_to_maze

class FloorPlan(QWidget):
    def __init__(self, floor_plan_path, width=None, height=None, blur_effect=100, 
                 player_size=10, tile_size=1, trail_size=5, parent=None):
        super().__init__(parent)
        self.player_size = player_size
        self.tile_size = tile_size
        self.trail_size = trail_size
        
        self.layout = QVBoxLayout(self)
        self.view = QGraphicsView()
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.view)

        # Set up the scene
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # Store walls, players, and trail
        self.walls = []
        self.players = []
        self.trail = []

        # Generate and load the floor plan
        self.floor_plan = floorplan_to_maze(floor_plan_path, width, height, blur_effect)
        self.load_floor_plan()

        # Install event filter to capture key events
        self.view.installEventFilter(self)

        # Resize the view to fit the window
        self.view.setFixedSize(width, height)
        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setLayout(self.layout)

    def load_floor_plan(self):
        """Load and draw the floor plan with walls and player starting position."""
        self.scene.clear()  # Clear existing items
        self.walls = []
        self.players = []
        self.trail = []

        for row in range(len(self.floor_plan)):
            for col in range(len(self.floor_plan[row])):
                x, y = col * self.tile_size, row * self.tile_size
                if self.floor_plan[row][col] == 1:  # Wall
                    wall = QGraphicsRectItem(x, y, self.tile_size, self.tile_size)
                    wall.setBrush(QBrush(Qt.black))
                    self.scene.addItem(wall)
                    self.walls.append(wall)
                else:  # Empty space
                    if not self.players:  # Add player at first empty space
                        self.add_player(x + self.tile_size // 2 - self.player_size // 2, 
                                       y + self.tile_size // 2 - self.player_size // 2)

    def add_player(self, x, y):
        """Add a player at the specified coordinates."""
        player = QGraphicsEllipseItem(x, y, self.player_size, self.player_size)
        player.setBrush(QBrush(Qt.red))
        self.scene.addItem(player)
        self.players.append(player)

    def eventFilter(self, source, event):
        """Event filter to capture key press events."""
        if event.type() == QEvent.KeyPress and source is self.view:
            self.keyPressEvent(event)
            return True
        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
        """Handle key press events for player movement."""
        if not self.players:
            return

        player = self.players[0]
        dx, dy = 0, 0

        if event.key() == Qt.Key_Left:
            dx = -self.player_size
        elif event.key() == Qt.Key_Right:
            dx = self.player_size
        elif event.key() == Qt.Key_Up:
            dy = -self.player_size
        elif event.key() == Qt.Key_Down:
            dy = self.player_size
        else:
            return

        # Compute new position
        new_x = player.x() + dx
        new_y = player.y() + dy

        # Boundary check
        if (new_x < 0 or new_x + self.player_size > self.view.width() or 
            new_y < 0 or new_y + self.player_size > self.view.height()):
            return

        # Collision check
        player_rect = player.sceneBoundingRect().translated(dx, dy)
        if not any(wall.sceneBoundingRect().intersects(player_rect) for wall in self.walls):
            # Add current position to trail
            trail_dot = QGraphicsEllipseItem(player.x(), player.y(), 
                                           self.player_size, self.player_size)
            trail_dot.setBrush(QBrush(Qt.blue))
            self.scene.addItem(trail_dot)
            self.trail.append(trail_dot)

            # Remove old trail if it exceeds the limit
            if len(self.trail) > self.trail_size:
                old_trail_dot = self.trail.pop(0)
                self.scene.removeItem(old_trail_dot)

            # Move player
            player.setX(new_x)
            player.setY(new_y)