from abc import ABC, abstractmethod

class Base(ABC):
    db_path = "bot/databases/mlbbmembers.db"

    @abstractmethod
    async def create_tables(self):
        pass

    @abstractmethod
    async def insert_member(self):
        pass