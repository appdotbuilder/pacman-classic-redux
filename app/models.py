from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal


# Enums for game entities
class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    NONE = "none"


class GameStatus(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    LEVEL_COMPLETE = "level_complete"
    PAUSED = "paused"


class GhostMode(str, Enum):
    SCATTER = "scatter"
    CHASE = "chase"
    FRIGHTENED = "frightened"
    EATEN = "eaten"


class GhostType(str, Enum):
    BLINKY = "blinky"  # Red ghost - aggressive chaser
    PINKY = "pinky"  # Pink ghost - ambush
    INKY = "inky"  # Blue ghost - patrol
    CLYDE = "clyde"  # Orange ghost - shy


class CellType(str, Enum):
    WALL = "wall"
    EMPTY = "empty"
    PELLET = "pellet"
    POWER_PELLET = "power_pellet"
    GHOST_HOUSE = "ghost_house"


# Persistent models (stored in database)
class Game(SQLModel, table=True):
    """Main game session tracking"""

    __tablename__ = "games"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    player_name: str = Field(max_length=100, default="Player")
    status: GameStatus = Field(default=GameStatus.WAITING)
    current_level: int = Field(default=1, ge=1)
    score: Decimal = Field(default=Decimal("0"), decimal_places=0)
    lives: int = Field(default=3, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    pacman: Optional["PacMan"] = Relationship(back_populates="game")
    ghosts: List["Ghost"] = Relationship(back_populates="game")
    maze: Optional["Maze"] = Relationship(back_populates="game")


class Maze(SQLModel, table=True):
    """Maze layout and structure"""

    __tablename__ = "mazes"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id")
    width: int = Field(ge=10)  # Maze width in cells
    height: int = Field(ge=10)  # Maze height in cells
    layout: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Grid layout as JSON
    pellet_positions: List[Dict[str, int]] = Field(default=[], sa_column=Column(JSON))  # [{"x": 1, "y": 2}]
    power_pellet_positions: List[Dict[str, int]] = Field(default=[], sa_column=Column(JSON))
    ghost_spawn_x: int = Field(ge=0)
    ghost_spawn_y: int = Field(ge=0)
    pacman_spawn_x: int = Field(ge=0)
    pacman_spawn_y: int = Field(ge=0)
    total_pellets: int = Field(default=0, ge=0)
    remaining_pellets: int = Field(default=0, ge=0)

    # Relationships
    game: Game = Relationship(back_populates="maze")


class PacMan(SQLModel, table=True):
    """Pac-Man player entity"""

    __tablename__ = "pacmen"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id")
    x: Decimal = Field(decimal_places=2)  # Position x coordinate
    y: Decimal = Field(decimal_places=2)  # Position y coordinate
    direction: Direction = Field(default=Direction.NONE)
    next_direction: Direction = Field(default=Direction.NONE)  # Queued direction change
    speed: Decimal = Field(default=Decimal("2.0"), decimal_places=2)
    is_powered: bool = Field(default=False)  # Has eaten power pellet
    power_time_remaining: Decimal = Field(default=Decimal("0"), decimal_places=2)  # Seconds of power left
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    game: Game = Relationship(back_populates="pacman")


class Ghost(SQLModel, table=True):
    """Ghost enemy entities"""

    __tablename__ = "ghosts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id")
    ghost_type: GhostType
    x: Decimal = Field(decimal_places=2)  # Position x coordinate
    y: Decimal = Field(decimal_places=2)  # Position y coordinate
    direction: Direction = Field(default=Direction.UP)
    mode: GhostMode = Field(default=GhostMode.SCATTER)
    target_x: Decimal = Field(decimal_places=2, default=Decimal("0"))  # Target position x
    target_y: Decimal = Field(decimal_places=2, default=Decimal("0"))  # Target position y
    speed: Decimal = Field(default=Decimal("1.8"), decimal_places=2)
    is_in_house: bool = Field(default=True)  # In ghost house at start
    mode_timer: Decimal = Field(default=Decimal("0"), decimal_places=2)  # Time in current mode
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    game: Game = Relationship(back_populates="ghosts")


class ScoreEvent(SQLModel, table=True):
    """Individual scoring events during gameplay"""

    __tablename__ = "score_events"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id")
    event_type: str = Field(max_length=50)  # "pellet", "power_pellet", "ghost", "fruit"
    points: Decimal = Field(decimal_places=0)
    x: Decimal = Field(decimal_places=2)  # Where the scoring event occurred
    y: Decimal = Field(decimal_places=2)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GameState(SQLModel, table=True):
    """Snapshot of game state for save/load functionality"""

    __tablename__ = "game_states"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id")
    state_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Complete game state
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class GameCreate(SQLModel, table=False):
    """Schema for creating a new game"""

    player_name: str = Field(max_length=100, default="Player")
    maze_width: int = Field(default=19, ge=10)
    maze_height: int = Field(default=21, ge=10)


class GameUpdate(SQLModel, table=False):
    """Schema for updating game state"""

    status: Optional[GameStatus] = Field(default=None)
    score: Optional[Decimal] = Field(default=None, decimal_places=0)
    lives: Optional[int] = Field(default=None, ge=0)
    current_level: Optional[int] = Field(default=None, ge=1)


class PacManMove(SQLModel, table=False):
    """Schema for Pac-Man movement commands"""

    direction: Direction
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GhostUpdate(SQLModel, table=False):
    """Schema for ghost state updates"""

    x: Decimal = Field(decimal_places=2)
    y: Decimal = Field(decimal_places=2)
    direction: Direction
    mode: GhostMode
    target_x: Optional[Decimal] = Field(default=None, decimal_places=2)
    target_y: Optional[Decimal] = Field(default=None, decimal_places=2)


class MazeCell(SQLModel, table=False):
    """Schema for individual maze cells"""

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    cell_type: CellType
    has_pellet: bool = Field(default=False)
    has_power_pellet: bool = Field(default=False)


class GameStats(SQLModel, table=False):
    """Schema for game statistics and leaderboard"""

    game_id: int
    player_name: str
    final_score: Decimal = Field(decimal_places=0)
    level_reached: int
    duration_seconds: int
    pellets_eaten: int
    ghosts_eaten: int
    completed_at: datetime
