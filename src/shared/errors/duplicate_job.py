class DuplicateJobError(Exception):
    def __init__(self) -> None:
        super().__init__("A processing job for this report is already in progress")
