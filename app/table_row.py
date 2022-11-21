from typing import Tuple


class TableRow:

    def to_database_representation(self) -> Tuple:
        raise NotImplementedError
