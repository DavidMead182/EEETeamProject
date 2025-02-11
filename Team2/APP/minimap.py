from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsEllipseItem, QVBoxLayout, QWidget
from PyQt5.QtGui import QBrush
from PyQt5.QtCore import Qt, QEvent
from Assets.functions.imageToArray import floorplan_to_maze  # Ensure this function is correctly implemented

# Constants
TILE_SIZE = 1  # Size of each tile
PLAYER_SIZE = 10  # Size of red dot
TRAIL_SIZE = 5  # Number of steps to keep the trail

class FloorPlan(QWidget):
    def __init__(self, floor_plan_path, width=None, height=None, blur_effect=100, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.view = QGraphicsView()
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #self.view.setFrameStyle(0)
        self.layout.addWidget(self.view)

        # Set up the scene
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # Generate the floor plan
        floor_plan = floorplan_to_maze(floor_plan_path, width, height, blur_effect)
        self.view.setFixedSize(len(floor_plan[0]) * TILE_SIZE, len(floor_plan) * TILE_SIZE)

        # Store walls, players, and trail
        self.walls = []
        self.players = []
        self.trail = []

        # Load floor plan and draw
        self.load_floor_plan(floor_plan)

        # Install event filter to capture key events
        self.view.installEventFilter(self)

    def load_floor_plan(self, floor_plan):
        """Load and draw the floor plan with walls and player starting position."""
        for row in range(len(floor_plan)):
            for col in range(len(floor_plan[row])):
                x, y = col * TILE_SIZE, row * TILE_SIZE
                if floor_plan[row][col] == 1:  # Wall
                    wall = QGraphicsRectItem(x, y, TILE_SIZE, TILE_SIZE)
                    wall.setBrush(QBrush(Qt.black))
                    self.scene.addItem(wall)
                    self.walls.append(wall)
                else:  # Empty space
                    if not self.players:  # Add red dot at the first empty space
                        self.add_red_dot(x + TILE_SIZE // 4, y + TILE_SIZE // 4)

    def add_red_dot(self, x, y):
        """Add a red dot (player) at the specified coordinates."""
        player = QGraphicsEllipseItem(x, y, PLAYER_SIZE, PLAYER_SIZE)
        player.setBrush(QBrush(Qt.red))
        self.scene.addItem(player)
        self.players.append(player)

    def eventFilter(self, source, event):
        """Event filter to capture key press events."""
        if event.type() == QEvent.KeyPress and source is self.view:
            self.keyPressEvent(event)
            return True
        return super(FloorPlan, self).eventFilter(source, event)

    def keyPressEvent(self, event):
        """Handle key press events for player movement."""
        if not self.players:
            return

        player = self.players[0]  # Single player for now
        dx, dy = 0, 0

        if event.key() == Qt.Key_Left:
            dx = -PLAYER_SIZE
        elif event.key() == Qt.Key_Right:
            dx = PLAYER_SIZE
        elif event.key() == Qt.Key_Up:
            dy = -PLAYER_SIZE
        elif event.key() == Qt.Key_Down:
            dy = PLAYER_SIZE
        else:
            return  # Ignore other keys

        # Compute new position
        new_x = player.x() + dx
        new_y = player.y() + dy

        # Boundary check
        if new_x < 0 or new_x + PLAYER_SIZE > self.view.width() or new_y < 0 or new_y + PLAYER_SIZE > self.view.height():
            return  # Ignore movement that would leave the view

        # Collision check
        player_rect = player.sceneBoundingRect().translated(dx, dy)
        if not any(wall.sceneBoundingRect().intersects(player_rect) for wall in self.walls):
            # Add current position to trail
            trail_dot = QGraphicsEllipseItem(player.x(), player.y(), PLAYER_SIZE, PLAYER_SIZE)
            trail_dot.setBrush(QBrush(Qt.blue))
            self.scene.addItem(trail_dot)
            self.trail.append(trail_dot)

            # Remove old trail if it exceeds the limit
            if len(self.trail) > TRAIL_SIZE:
                old_trail_dot = self.trail.pop(0)
                self.scene.removeItem(old_trail_dot)

            # Move player
            player.setX(new_x)
            player.setY(new_y)