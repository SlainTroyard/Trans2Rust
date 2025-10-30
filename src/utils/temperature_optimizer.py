"""
Temperature optimizer for adaptive translation
Optimized for DeepSeek API with recommended temperature values: 0.0, 1.0, 1.3, 1.5
"""

import random
from typing import List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class TranslationAttempt:
    """Represents a translation attempt with its result"""
    temperature: float
    success: bool
    confidence: float = 0.0
    error_message: Optional[str] = None
    translated_code: Optional[str] = None


class TemperatureOptimizer:
    """Temperature optimizer for adaptive translation
    
    Optimized for DeepSeek API with recommended temperature values.
    Uses DeepSeek's recommended values: 0.0, 1.0, 1.3, 1.5
    
    Args:
        initial_temp: Initial temperature value (default: 1.0 per DeepSeek recommendation)
        recommended_temps: List of recommended temperature values from DeepSeek
    """
    
    # DeepSeek recommended temperature values
    DEEPSEEK_RECOMMENDED_TEMPS = [0.0, 1.0, 1.3, 1.5]
    
    def __init__(
        self, 
        initial_temp: float = 1.0,
        recommended_temps: Optional[List[float]] = None
    ):
        self.recommended_temps = recommended_temps or self.DEEPSEEK_RECOMMENDED_TEMPS
        self.initial_temp = initial_temp
        self.min_temp = min(self.recommended_temps)
        self.max_temp = max(self.recommended_temps)
        
        # Start with initial temp, but ensure it's in recommended list or closest one
        if initial_temp in self.recommended_temps:
            self.current_temp = initial_temp
        else:
            # Find closest recommended temperature
            self.current_temp = min(self.recommended_temps, key=lambda x: abs(x - initial_temp))
        
        self.best_temp = self.current_temp
        self.best_score = 0.0
        self.attempt_history: List[TranslationAttempt] = []
    
    def sample(self, num_samples: int = 1) -> List[float]:
        """Sample temperature values from DeepSeek recommended values
        
        Uses DeepSeek's recommended temperature values: 0.0, 1.0, 1.3, 1.5
        Prioritizes values near current best temperature.
        """
        if num_samples >= len(self.recommended_temps):
            # Return all recommended temps if we need more than available
            return self.recommended_temps.copy()
        
        # Sort recommended temps by distance from current best
        sorted_temps = sorted(
            self.recommended_temps,
            key=lambda x: abs(x - self.best_temp)
        )
        
        # Return the closest num_samples temperatures
        samples = sorted_temps[:num_samples]
        
        # Shuffle to avoid always starting with the same order
        random.shuffle(samples)
        
        return samples
    
    def update_from_attempt(self, attempt: TranslationAttempt) -> float:
        """Update optimizer based on translation attempt result"""
        self.attempt_history.append(attempt)
        
        # Calculate score: success is weighted heavily, confidence adds bonus
        if attempt.success:
            score = 0.7 + (attempt.confidence * 0.3)  # Max 1.0
        else:
            score = 0.0
        
        # Update best if this is better
        if score > self.best_score:
            self.best_score = score
            self.best_temp = attempt.temperature
            logger.debug(f"New best temperature: {self.best_temp:.2f} (score: {self.best_score:.2f})")
        
        # Adaptive adjustment: move towards successful temperatures using recommended values
        if attempt.success:
            # Move current temp towards successful value by selecting closest recommended temp
            if attempt.temperature != self.current_temp:
                # Find closest recommended temperature to the successful one
                closest_temp = min(self.recommended_temps, key=lambda x: abs(x - attempt.temperature))
                # Move towards successful temperature (but use discrete recommended values)
                if abs(closest_temp - self.current_temp) < abs(self.current_temp - attempt.temperature):
                    self.current_temp = closest_temp
        else:
            # On failure, try a different recommended temperature
            if attempt.temperature == self.current_temp:
                # Try next lower recommended temperature
                sorted_temps = sorted(self.recommended_temps)
                current_idx = sorted_temps.index(self.current_temp) if self.current_temp in sorted_temps else 0
                if current_idx > 0:
                    self.current_temp = sorted_temps[current_idx - 1]
        
        # Ensure current_temp is in recommended list (snap to nearest)
        if self.current_temp not in self.recommended_temps:
            self.current_temp = min(self.recommended_temps, key=lambda x: abs(x - self.current_temp))
        
        return self.current_temp
    
    def get_adaptive_temperature(self, complexity: float = 0.5) -> float:
        """Get temperature adjusted for code complexity using DeepSeek recommended values
        
        Args:
            complexity: Code complexity score (0.0 to 1.0)
            
        Returns:
            Adjusted temperature value from DeepSeek recommended list
        """
        # Map complexity to DeepSeek recommended temperatures:
        # - Simple code (complexity < 0.3): 0.0 or 1.0 (more deterministic)
        # - Medium code (0.3 <= complexity < 0.7): 1.0 (default)
        # - Complex code (complexity >= 0.7): 1.3 or 1.5 (more exploration)
        
        if complexity < 0.3:
            # Simple code - prefer lower temperatures (0.0 or 1.0)
            candidates = [0.0, 1.0]
        elif complexity < 0.7:
            # Medium complexity - use default (1.0)
            return 1.0
        else:
            # Complex code - prefer higher temperatures (1.3 or 1.5)
            candidates = [1.3, 1.5]
        
        # Return closest to current best temperature
        if candidates:
            return min(candidates, key=lambda x: abs(x - self.best_temp))
        
        return self.current_temp
    
    def get_retry_temperatures(self, failed_temp: float, num_retries: int = 3) -> List[float]:
        """Get temperatures for retry attempts after failure using DeepSeek recommended values
        
        Provides diverse temperature values from DeepSeek's recommended list when translation fails.
        """
        retry_temps = []
        
        # Remove failed temperature from candidates
        candidates = [t for t in self.recommended_temps if t != failed_temp]
        
        # Strategy 1: Try different temperatures from recommended list
        # Prioritize temperatures different from failed one
        for temp in candidates:
            if len(retry_temps) >= num_retries:
                break
            if temp not in retry_temps:
                retry_temps.append(temp)
        
        # Strategy 2: If we need more, try temperatures closer to best known
        if len(retry_temps) < num_retries:
            remaining = self.recommended_temps.copy()
            remaining.sort(key=lambda x: abs(x - self.best_temp))
            for temp in remaining:
                if len(retry_temps) >= num_retries:
                    break
                if temp not in retry_temps:
                    retry_temps.append(temp)
        
        return retry_temps[:num_retries]
    
    def reset(self) -> None:
        """Reset optimizer to initial state"""
        if self.initial_temp in self.recommended_temps:
            self.current_temp = self.initial_temp
        else:
            self.current_temp = min(self.recommended_temps, key=lambda x: abs(x - self.initial_temp))
        self.best_temp = self.current_temp
        self.best_score = 0.0
        self.attempt_history.clear()

