# UML Diagrams

All diagrams are written in [Mermaid](https://mermaid.js.org/). GitHub and GitLab draw them automatically when you open this file.

| # | Diagram | Shows |
| --- | --- | --- |
| 1 | Layers overview | The big blocks of the project and who uses whom |
| 2 | UI classes | Screens, input and renderers |
| 3 | Game logic classes | Engine, entities and ghost AI |
| 4 | Data classes | Config, highscores and maze |
| 5 | Screen navigation | How the player moves between screens |
| 6 | Engine states | The life cycle of a game |
| 7 | Sequence: one frame | What happens 60 times per second |
| 8 | Sequence: end of a game | From game over to the highscore table |

---

## 1. Layers overview

The game logic never imports pygame. The screens talk to the engine only through the public properties of `PlayEngine`.

```mermaid
flowchart TD
    App["pac_man.py<br/>PacmanApp (main loop)"]

    subgraph UI["User interface (src/ui and screens)"]
        Input["InputHandler<br/>InputCommand"]
        GSM["GameStateManager"]
        Screens["MainMenuScreen<br/>PlayScreen<br/>HighscoreScreen<br/>InstructionsScreen"]
        Rend["Renderer<br/>RenderMaze, RenderConsumables<br/>RenderPlayer, RenderGhost"]
    end

    subgraph Logic["Game logic"]
        Engine["GameEngine<br/>(PlayEngine)"]
        Entities["PacMan, Ghost"]
        AI["Ghost strategies"]
        Cons["Consumables"]
        LogSys["WarningManager<br/>(logger.py)"]
    end

    subgraph Data["Data, Persistence and Platform"]
        Config["Config / LevelConfig"]
        Maze["MazeAdapter<br/>(A-Maze-ing)"]
        HS["HighscoreManager"]
        DDir["data_dir.py<br/>(platformdirs)"]
        Files[("config.json<br/>DATA_DIR/highscores.json<br/>DATA_DIR/pacman_states.json<br/>LOGS_DIR/logs.txt")]
    end

    App --> Input
    App --> GSM
    App --> Rend
    App --> LogSys
    GSM --> Screens
    Screens --> Rend
    Screens --> Engine
    Screens --> HS
    Engine --> Entities
    Engine --> Cons
    Engine --> Maze
    Engine --> Config
    Engine --> LogSys
    Entities --> AI
    Config --> Files
    HS --> DDir
    DDir --> Files
    HS --> Files
    Engine --> Files
    LogSys --> Files
```

---

## 2. UI classes

```mermaid
classDiagram
    class PacmanApp {
        +is_running bool
        +run() None
        +quit() None
    }

    class InputHandler {
        +handle_events() InputCommand
        +clean() None
    }

    class InputCommand {
        <<dataclass>>
        +direction Direction
        +mouse_clicked bool
        +play bool
        +pause bool
        +restart bool
        +back bool
        +quit bool
        +show_highscores bool
        +show_instructions bool
        +continue_game bool
        +toggle_cheats bool
        +cheat int
        +change_style bool
        +backspace bool
        +text str
    }

    class GameStateManager {
        -screens dict
        -active_screen Screen
        +handle_input(command) None
        +update(dt) None
        +render(renderer) None
        +change_state(name) None
        +save_game() None
    }

    class Screen {
        <<abstract>>
        +door_w float
        +screen_w int
        +screen_h int
        +door_closed bool
        +handle_input(command)*
        +update(dt)*
        +render(renderer)*
    }

    class MainMenuScreen {
        +show_message(text) None
    }
    class PlayScreen {
        +loaded bool
        +save_game() bool
    }
    class HighscoreScreen
    class InstructionsScreen

    class Renderer {
        +HUD_WIDTH int
        +render_maze(maze, change_style) None
        +render_entities(player, ghosts) None
        +render_hub(score, lives, level, max_level, time_left) None
        +draw_text(font, text, color, pos) None
        +draw_door(x, door_w) None
        +blit_window(surface, coord) None
        +clear() None
        +update_display() None
    }

    class RenderMaze {
        +tile int
        +off_x int
        +off_y int
        +prepare(maze) None
        +render(change_style) None
    }
    class RenderConsumables {
        +prepare(maze_render) None
        +render(maze, change_style) None
    }
    class RenderPlayer {
        +prepare(maze_render) None
        +render(player) None
    }
    class RenderGhost {
        +prepare(maze_render) None
        +render(ghosts) None
    }

    PacmanApp *-- InputHandler
    PacmanApp *-- Renderer
    PacmanApp *-- GameStateManager
    InputHandler ..> InputCommand : creates
    GameStateManager o-- Screen
    Screen <|-- MainMenuScreen
    Screen <|-- PlayScreen
    Screen <|-- HighscoreScreen
    Screen <|-- InstructionsScreen
    Screen ..> InputCommand : reads
    Screen ..> Renderer : draws with
    Renderer *-- RenderMaze
    Renderer *-- RenderConsumables
    Renderer *-- RenderPlayer
    Renderer *-- RenderGhost
    RenderConsumables ..> RenderMaze : tile size and offset
    RenderPlayer ..> RenderMaze : tile size and offset
    RenderGhost ..> RenderMaze : tile size and offset
```

---

## 3. Game logic classes

```mermaid
classDiagram
    class GameEngine {
        -score int
        -cur_level int
        -state EngineState
        +state EngineState
        +score int
        +tick(dt, direction) None
        +add_score(points) None
        +activate_cheat(cheat) None
        +trigger_frightened_mode(duration) None
        +stop() None
        +resume() None
    }

    class PlayEngine {
        +is_level_loaded bool
        +grid
        +pacman PacMan
        +ghosts list
        +lives int
        +level int
        +max_level int
        +time_left float
        +save() bool
        +load_to_resume() bool
        +delete_save() None
    }

    class EngineState {
        <<enumeration>>
        PLAYING
        RESPAWNING
        GAME_OVER
        GAME_WON
        STOPPED
    }

    class Cheat {
        <<enumeration>>
        INVINCIBILITY
        LEVEL_SKIP
        GHOST_FREEZE
        EXTRA_LIVES
        INCREASE_SPEED
    }

    class Entity {
        <<abstract>>
        +name str
        +x float
        +y float
        +speed float
        +tile tuple
        +cur_direction Direction
        +is_invincible bool
        +can_move(direction) bool
        +activate_effect(effect, duration) None
        +has_effect(effect) bool
        +update_effects(dt) None
        +respawn()*
        +update(dt)*
    }

    class PacMan {
        +lives int
        +is_alive bool
        +lose_life() None
        +add_life() None
        +request_direction(direction) None
        +can_eat_ghost(ghost) bool
    }

    class Ghost {
        +state GhostState
        +is_frozen bool
        +is_frighten bool
        +frightened_duration float
        +switch_state(state) None
        +active_frighten_mode(duration) None
        +can_eat_pacman() bool
    }

    class Direction {
        <<enumeration>>
        UP
        DOWN
        LEFT
        RIGHT
        NONE
    }
    class GhostState {
        <<enumeration>>
        CHASE
        FRIGHTENED
        WANDER
        DIED
    }
    class EntityEffect {
        <<enumeration>>
        INVINCIBILITY
        SPEED_BUFF
        SPEED_DEBUFF
        FREEZE
    }

    class GhostStrategy {
        <<abstract>>
        +compute_next_move(ghost, pacman, maze, blinky)*
    }
    class BlinkyStrategy
    class PinkyStrategy
    class InkyStrategy
    class ClydeStrategy

    class Consumable {
        +effect(engine) None
        +reset_counter()$ None
        +still_any_consumables()$ bool
    }
    class PacGum
    class SuperPacGum

    GameEngine <|-- PlayEngine
    GameEngine --> EngineState
    GameEngine ..> Cheat
    GameEngine *-- PacMan : 1
    GameEngine *-- Ghost : 4
    Entity <|-- PacMan
    Entity <|-- Ghost
    Entity --> Direction
    Entity ..> EntityEffect
    Ghost --> GhostState
    Ghost o-- GhostStrategy
    Ghost ..> PacMan : chases
    GhostStrategy <|-- BlinkyStrategy
    GhostStrategy <|-- PinkyStrategy
    GhostStrategy <|-- InkyStrategy
    GhostStrategy <|-- ClydeStrategy
    Consumable <|-- PacGum
    Consumable <|-- SuperPacGum
    GameEngine ..> Consumable : applies effects
```

---

## 4. Data classes

```mermaid
classDiagram
    class Config {
        <<frozen dataclass>>
        +width int
        +height int
        +lives int
        +points_per_pacgum int
        +points_per_super_pacgum int
        +points_per_ghost int
        +frightened_duration float
        +ghost_speed float
        +pacman_speed float
        +seed int
        +level_max_time int
        +from_file(path)$ Config
        +generate_level(level) LevelConfig
    }

    class LevelConfig {
        <<frozen dataclass>>
        +level int
        +level_max_time int
        +frightened_duration float
        +ghost_speed float
        +seed int
    }

    class MazeAdapter {
        +set_maze_size(size)$ None
        +generate_maze(levelconfig) Grid
    }

    class Grid {
        +width int
        +height int
        +grid list
        +is_wall(x, y) bool
        +get_cell(x, y) Cell
        +find_nearest_corridor(coord) tuple
    }

    class Cell {
        +x int
        +y int
        +is_wall bool
        +cell_type CellType
        +consumes list
        +add_consumable(item) None
        +remove_consumables() None
    }

    class CellType {
        <<enumeration>>
        LOGO
        ...
    }

    class HighscoreManager {
        -scores dict
        +has_scores bool
        +get_top_scores(limit) list
        +save(name, score) tuple
    }

    class LogType {
        <<enumeration>>
        INFO
        WARNING
        +ansi() str
        +text() str
    }

    class WarningManager {
        -lock Lock
        -tables deque
        -logs_file TextIO
        +log_path Path
        +start() None
        +stop() None
        +log(msg, title, log_type) None
    }

    GameEngine ..> Config : reads rules
    Config ..> LevelConfig : creates
    Config ..> MazeAdapter : sets size
    GameEngine ..> MazeAdapter : asks for a maze
    MazeAdapter ..> Grid : returns
    Grid o-- Cell
    Cell --> CellType
    PlayScreen ..> HighscoreManager : saves score
    HighscoreScreen ..> HighscoreManager : shows top 10
    GameEngine ..> WarningManager : logs events
    HighscoreManager ..> WarningManager : logs warnings
    WarningManager --> LogType
```

> `Grid` and `Cell` are the names used in this document for the maze grid and its cells. Use the real class names from `maze_adapter.py` if they are different.

---

## 5. Screen navigation

```mermaid
stateDiagram-v2
    [*] --> MainMenu

    MainMenu --> Play : click Play (new game)
    MainMenu --> Play : click Resume (a save exists)
    MainMenu --> Highscores : click Highscores
    MainMenu --> Instructions : click Instructions
    MainMenu --> [*] : click Quit

    Play --> MainMenu : pause menu, Main Menu (game is saved)
    Play --> Highscores : game over, type a name, click Save
    Play --> [*] : close the window (asks to save)

    Highscores --> MainMenu : click anywhere
    Instructions --> MainMenu : click anywhere
```

---

## 6. Engine states

```mermaid
stateDiagram-v2
    [*] --> RESPAWNING : new game

    RESPAWNING --> PLAYING : 3 second countdown ends
    PLAYING --> RESPAWNING : Pac-Man loses a life
    PLAYING --> RESPAWNING : level completed (next level)
    PLAYING --> STOPPED : pause
    STOPPED --> PLAYING : resume (previous state restored)
    PLAYING --> GAME_OVER : no lives left or time is up
    PLAYING --> GAME_WON : level 10 completed

    GAME_OVER --> [*]
    GAME_WON --> [*]
```

---

## 7. Sequence: one frame of the game

This repeats 60 times per second in `PacmanApp.run`.

```mermaid
sequenceDiagram
    participant App as PacmanApp
    participant In as InputHandler
    participant GSM as GameStateManager
    participant Scr as Active Screen
    participant Eng as PlayEngine
    participant Rend as Renderer

    App->>In: handle_events()
    In-->>App: InputCommand
    App->>GSM: handle_input(command)
    GSM->>Scr: handle_input(command)
    Note over Scr: sets flags on the command<br/>(play, back, show_highscores...)
    App->>GSM: change_state(...) if a flag is set
    App->>GSM: update(dt)
    GSM->>Scr: update(dt)
    Scr->>Eng: tick(dt, direction)
    Eng-->>Scr: new positions, score, state
    App->>GSM: render(renderer)
    GSM->>Scr: render(renderer)
    Scr->>Rend: render_maze / render_entities / render_hub
    App->>Rend: update_display()
```

---

## 8. Sequence: end of a game

```mermaid
sequenceDiagram
    actor P as Player
    participant Play as PlayScreen
    participant Eng as PlayEngine
    participant HS as HighscoreManager
    participant App as PacmanApp
    participant GSM as GameStateManager
    participant HScr as HighscoreScreen

    Eng->>Eng: state = GAME_OVER (no lives or time is up)
    Play->>Eng: delete_save() (a finished game cannot be resumed)
    Play->>P: show title, score and name box
    P->>Play: types a name
    P->>Play: clicks Save
    Play->>HS: save(name, score)
    alt name and score are valid
        HS-->>Play: (True, "")
        Play->>App: command.show_highscores = True
        App->>GSM: change_state("highscores")
        GSM->>HScr: becomes the active screen
        HScr->>HS: get_top_scores(10)
        HScr->>P: shows the top 10
    else refused (long name, bad characters, lower score)
        HS-->>Play: (False, reason)
        Play->>P: shows the reason, the player can try again
    end
```
