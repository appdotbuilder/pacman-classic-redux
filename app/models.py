from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from decimal import Decimal


# Enums for game constants
class GameState(str, Enum):
    READY = "ready"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    LEVEL_COMPLETE = "level_complete"


class GhostType(str, Enum):
    BLINKY = "blinky"  # Red ghost - aggressive chaser
    PINKY = "pinky"  # Pink ghost - ambush predator
    INKY = "inky"  # Cyan ghost - patrol behavior
    CLYDE = "clyde"  # Orange ghost - random movement


class GhostMode(str, Enum):
    NORMAL = "normal"
    VULNERABLE = "vulnerable"
    EATEN = "eaten"
    RETURNING = "returning"


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    NONE = "none"


class CellType(str, Enum):
    EMPTY = "empty"
    WALL = "wall"
    DOT = "dot"
    POWER_PELLET = "power_pellet"
    TUNNEL = "tunnel"
    GHOST_HOUSE = "ghost_house"


# Persistent models (stored in database)
class Game(SQLModel, table=True):
    """Represents a complete game session with score and statistics"""

    __tablename__ = "games"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    player_name: str = Field(max_length=50, default="Player")
    final_score: int = Field(default=0, ge=0)
    level_reached: int = Field(default=1, ge=1)
    lives_remaining: int = Field(default=0, ge=0)
    dots_eaten: int = Field(default=0, ge=0)
    ghosts_eaten: int = Field(default=0, ge=0)
    power_pellets_eaten: int = Field(default=0, ge=0)
    duration_seconds: int = Field(default=0, ge=0)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = Field(default=None)

    game_statistics: List["GameStatistic"] = Relationship(back_populates="game")


class GameStatistic(SQLModel, table=True):
    """Detailed statistics for each level within a game"""

    __tablename__ = "game_statistics"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="games.id")
    level: int = Field(ge=1)
    score_gained: int = Field(default=0, ge=0)
    dots_eaten_in_level: int = Field(default=0, ge=0)
    ghosts_eaten_in_level: int = Field(default=0, ge=0)
    power_pellets_eaten_in_level: int = Field(default=0, ge=0)
    lives_lost_in_level: int = Field(default=0, ge=0)
    level_duration_seconds: int = Field(default=0, ge=0)
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    game: Game = Relationship(back_populates="game_statistics")


class HighScore(SQLModel, table=True):
    """High scores leaderboard"""

    __tablename__ = "high_scores"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    player_name: str = Field(max_length=50)
    score: int = Field(ge=0)
    level_reached: int = Field(ge=1)
    achieved_at: datetime = Field(default_factory=datetime.utcnow)


class GameSettings(SQLModel, table=True):
    """Configurable game settings and preferences"""

    __tablename__ = "game_settings"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    setting_name: str = Field(unique=True, max_length=100)
    setting_value: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    description: str = Field(default="", max_length=500)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for game state management and validation)
class Position(SQLModel, table=False):
    """2D position coordinates"""

    x: int = Field(ge=0)
    y: int = Field(ge=0)


class PacmanState(SQLModel, table=False):
    """Current state of Pacman character"""

    position: Position
    direction: Direction = Direction.NONE
    next_direction: Direction = Direction.NONE
    speed: Decimal = Field(default=Decimal("1.0"))
    lives: int = Field(default=3, ge=0, le=5)
    invulnerable_until: Optional[datetime] = None


class GhostStateModel(SQLModel, table=False):
    """Current state of a ghost character"""

    ghost_type: GhostType
    position: Position
    direction: Direction = Direction.UP
    state: GhostMode = GhostMode.NORMAL
    target_position: Optional[Position] = None
    speed: Decimal = Field(default=Decimal("0.8"))
    vulnerable_until: Optional[datetime] = None
    house_exit_time: Optional[datetime] = None


class MazeCell(SQLModel, table=False):
    """Individual cell in the game maze"""

    position: Position
    cell_type: CellType
    has_dot: bool = False
    has_power_pellet: bool = False
    is_tunnel_entrance: bool = False


class MazeLayout(SQLModel, table=False):
    """Complete maze layout definition"""

    width: int = Field(ge=10, le=50)
    height: int = Field(ge=10, le=50)
    cells: List[List[CellType]] = Field(default=[])
    pacman_start: Position
    ghost_house_center: Position
    ghost_spawn_positions: Dict[GhostType, Position]
    tunnel_positions: List[Tuple[Position, Position]] = Field(default=[])
    total_dots: int = Field(default=0, ge=0)
    total_power_pellets: int = Field(default=0, ge=0)


class GameScore(SQLModel, table=False):
    """Current game scoring information"""

    current_score: int = Field(default=0, ge=0)
    dots_eaten: int = Field(default=0, ge=0)
    power_pellets_eaten: int = Field(default=0, ge=0)
    ghosts_eaten: int = Field(default=0, ge=0)
    ghost_combo_multiplier: int = Field(default=1, ge=1, le=4)
    bonus_points: int = Field(default=0, ge=0)


class PowerPelletEffect(SQLModel, table=False):
    """State of power pellet effects"""

    is_active: bool = False
    started_at: Optional[datetime] = None
    duration_seconds: int = Field(default=10, ge=5, le=30)
    ghosts_eaten_during: int = Field(default=0, ge=0, le=4)


class GameSession(SQLModel, table=False):
    """Complete current game state (non-persistent)"""

    game_id: Optional[int] = None
    state: GameState = GameState.READY
    level: int = Field(default=1, ge=1)
    maze: MazeLayout
    pacman: PacmanState
    ghosts: Dict[GhostType, GhostStateModel]
    score: GameScore
    power_pellet_effect: PowerPelletEffect
    remaining_dots: int = Field(default=0, ge=0)
    remaining_power_pellets: int = Field(default=0, ge=0)
    level_start_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None


# Game configuration schemas
class DifficultySettings(SQLModel, table=False):
    """Difficulty configuration for game mechanics"""

    name: str = Field(max_length=20)
    pacman_speed: Decimal = Field(ge=0.5, le=2.0)
    ghost_speed: Decimal = Field(ge=0.3, le=1.8)
    power_pellet_duration: int = Field(ge=5, le=20)
    ghost_vulnerability_speed: Decimal = Field(ge=0.2, le=1.0)
    starting_lives: int = Field(ge=1, le=5)
    extra_life_threshold: int = Field(ge=5000, le=50000)


class ScoreValues(SQLModel, table=False):
    """Point values for different game events"""

    dot_points: int = Field(default=10, ge=1)
    power_pellet_points: int = Field(default=50, ge=10)
    ghost_base_points: int = Field(default=200, ge=100)
    bonus_fruit_points: Dict[str, int] = Field(
        default={
            "cherry": 100,
            "strawberry": 300,
            "orange": 500,
            "apple": 700,
            "melon": 1000,
            "galaxian": 2000,
            "bell": 3000,
            "key": 5000,
        }
    )


# Game creation and update schemas
class GameCreate(SQLModel, table=False):
    """Schema for creating a new game"""

    player_name: str = Field(max_length=50, default="Player")
    difficulty: str = Field(default="normal", max_length=20)


class GameUpdate(SQLModel, table=False):
    """Schema for updating game statistics"""

    final_score: Optional[int] = Field(default=None, ge=0)
    level_reached: Optional[int] = Field(default=None, ge=1)
    lives_remaining: Optional[int] = Field(default=None, ge=0)
    dots_eaten: Optional[int] = Field(default=None, ge=0)
    ghosts_eaten: Optional[int] = Field(default=None, ge=0)
    power_pellets_eaten: Optional[int] = Field(default=None, ge=0)
    duration_seconds: Optional[int] = Field(default=None, ge=0)
    completed: Optional[bool] = None
    finished_at: Optional[datetime] = None


class HighScoreCreate(SQLModel, table=False):
    """Schema for creating high score entries"""

    player_name: str = Field(max_length=50)
    score: int = Field(ge=0)
    level_reached: int = Field(ge=1)
