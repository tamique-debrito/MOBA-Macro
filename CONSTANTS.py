# Simulator


SIM_STEPS_PER_SECOND = 5

# Map Distance Thresholds
PRESENCE_THRESHOLD = 30  # General distance threshold for things such as gold reward, xp, etc.
COMBAT_START_THRESHOLD = 30 # Threshold to engage combat
COMBAT_INCLUDE_THRESHOLD = 45 # Threshold to include entities in combat
WAVE_COMBINE_THRESHOLD = 15 # threshold for waves to be combined into one
TARGET_LOC_THRESHOLD = 3 # threshold for being considered as arriving at a target location

# Simulation step periods, intervals, and timers
DAMAGE_APPLY_INTERVAL = 1  # time per damage tick in seconds
DISENGAGE_TIME = 2 # seconds to disengage from combat
RECALL_TIME = 8 # seconds for player to recall to spawn point
RESPAWN_TIME = 10 # How many seconds before player respawn
VISION_RECALCULATE_PERIOD = 1 # seconds between vision recalculation

# Misc.
PLAYER_ATTACK_MISS_PROBABILITY = 0.2

DEFAULT_WAVE_REWARD: int = 100
TURRET_REWARD: int = 500


