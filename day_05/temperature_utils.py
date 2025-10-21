from typing import Optional


def clamp_temperature(value: float) -> float:
	"""
	Purpose: Clamp and normalize temperature value.
	Args:
		value: Raw temperature in [0.0, 2.0]
	Returns:
		Clamped value in [0.0, 1.5] rounded to 2 decimals
	Exceptions:
		ValueError: If value is None or outside [0.0, 2.0]
	Example:
		clamp_temperature(1.234) -> 1.23
	"""
	if value is None:
		raise ValueError("Temperature is required")
	if not (0.0 <= value <= 2.0):
		raise ValueError("Temperature must be within [0.0, 2.0]")
	value = min(max(value, 0.0), 1.5)
	return round(value, 2)


def resolve_effective_temperature(
	override: Optional[float],
	user_default: Optional[float],
	system_default: float = 0.7
) -> float:
	"""
	Purpose: Compute effective temperature with priority override > user_default > system_default.
	Args:
		override: One-off value for current message
		user_default: User's default value
		system_default: Fallback
	Returns:
		Effective temperature
	Exceptions:
		ValueError: From clamp_temperature
	Example:
		resolve_effective_temperature(1.2, None) -> 1.2
	"""
	raw = override if override is not None else (
		user_default if user_default is not None else system_default
	)
	return clamp_temperature(raw)


