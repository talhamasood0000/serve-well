from enum import Enum

class SentimentChoices(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    
    @classmethod
    def get_mapping(cls):
        """
        Returns a dictionary mapping sentiment strings to their enum values
        """
        return {
            'positive': cls.POSITIVE.value,
            'negative': cls.NEGATIVE.value,
            'neutral': cls.NEUTRAL.value,
        }

class SentimentScoreChoices(Enum):
    POSITIVE = 1.0
    NEGATIVE = -1.0
    NEUTRAL = 0.0
    
    @classmethod
    def get_mapping(cls):
        """
        Returns a dictionary mapping sentiment strings to their score values
        """
        return {
            'positive': cls.POSITIVE.value,
            'negative': cls.NEGATIVE.value,
            'neutral': cls.NEUTRAL.value,
        }
