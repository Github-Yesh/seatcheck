"""These setup codes describe a staged photo, not a fit verdict."""
# WHY: the photo counter and label saver need to accept the same setup codes.
SETUP_CODES = tuple(f"B{i}" for i in range(1, 11))+tuple(f"H{i}" for i in range(1, 10))
VALID_SETUPS = SETUP_CODES+("other",)
