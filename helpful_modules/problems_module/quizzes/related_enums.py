import enum

# This isn't really used, but it's licensed under GPLv3


class QuizIntensity(float, enum.Enum):
    IMPOSSIBLE =200 << 50
    ONLY_GENIUSES_CAN_SOLVE_THIS = 200 << 40
    EXTREMELY_CHALLENGING = 10000.0
    EXTREMELY_HARD = 5000.0
    VERY_HARD = 2000.0
    CHALLENGING = 1000.0
    HARD = 500.0
    MEDIUM_HARD = 400.0
    MEDIUM = 300.0
    BETWEEN_EASY_AND_MEDIUM = 200.0
    EASY = 100.0
    VERY_EASY = 50.0
    VERY_VERY_EASY = 25
    TRIVIAL = 0
    CUSTOM = -1
    TOO_EASY = -200<<40


class QuizTimeLimit(int, enum.Enum):
    CUSTOM = -1
    ONE_SECOND = 1
    THIRTY_SECONDS = 30
    FORTY_FIVE_SECONDS = 45
    ONE_MINUTE = 60
    FIVE_MINUTES = 300
    TEN_MINUTES = 600
    FIFTEEN_MINUTES = 900
    ONE_THOUSAND_SECONDS = 1000
    SEVENTEEN_MINUTES_AND_THIRTY_SECONDS = 1050
    TWENTY_MINUTES = 1200
    THIRTY_MINUTES = 1800
    TWO_THOUSAND_SECONDS = 2000
    TWO_THOUSAND_AND_TWENTY_TWO_SECONDS = 2022
    FORTY_MINUTES = 2400
    ONE_HOUR = 3600
    SEVENTY_FIVE_MINUTES = 4500
    ONE_AND_A_HALF_HOURS = 5400
    ONE_HUNDRED_FIVE_MINUTES = 6300
    TWO_HOURS = 7200
    TWO_AND_A_HALF_HOURS = 9000
    THREE_HOURS = 10800
    FOUR_HOURS = 14400
    ONE_DAY = 86400
    ONE_WEEK = 604800
    NO_LIMIT = 1 << 100
    UNLIMITED = 1 << 100


class QuizIntensity(float, enum.Enum):
    IMPOSSIBLE = float("inf")
    ONLY_GENIUSES_CAN_SOLVE_THIS = 200 << 100
    EXTREMELY_CHALLENGING = 10000.0
    EXTREMELY_HARD = 5000.0
    VERY_HARD = 2000.0
    CHALLENGING = 1000.0
    HARD = 500.0
    MEDIUM_HARD = 400.0
    MEDIUM = 300.0
    BETWEEN_EASY_AND_MEDIUM = 200.0
    EASY = 100.0
    VERY_EASY = 50.0
    VERY_VERY_EASY = 25
    TRIVIAL = 0
    CUSTOM = -1
    TOO_EASY = -float("inf")


class QuizTimeLimit(int, enum.Enum):
    CUSTOM = -1
    ONE_SECOND = 1
    THIRTY_SECONDS = 30
    FORTY_FIVE_SECONDS = 45
    ONE_MINUTE = 60
    FIVE_MINUTES = 300
    TEN_MINUTES = 600
    FIFTEEN_MINUTES = 900
    ONE_THOUSAND_SECONDS = 1000
    SEVENTEEN_MINUTES_AND_THIRTY_SECONDS = 1050
    TWENTY_MINUTES = 1200
    THIRTY_MINUTES = 1800
    TWO_THOUSAND_SECONDS = 2000
    TWO_THOUSAND_AND_TWENTY_TWO_SECONDS = 2022
    FORTY_MINUTES = 2400
    ONE_HOUR = 3600
    SEVENTY_FIVE_MINUTES = 4500
    ONE_AND_A_HALF_HOURS = 5400
    ONE_HUNDRED_FIVE_MINUTES = 6300
    TWO_HOURS = 7200
    TWO_AND_A_HALF_HOURS = 9000
    THREE_HOURS = 10800
    FOUR_HOURS = 14400
    ONE_DAY = 86400
    ONE_WEEK = 604800
    NO_LIMIT = 1 << 100
    UNLIMITED = 1 << 100
