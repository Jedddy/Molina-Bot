import asyncpg
import discord

class ModerationDB:
    def __init__(self, db: asyncpg.Pool):
        self.db = db

    async def create_tables(self) -> None:
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS userlogs (
                user_id BIGINT PRIMARY KEY,
                mute_count INT DEFAULT 0,
                warn_count INT DEFAULT 0,
                kick_count INT DEFAULT 0,
                ban_count INT DEFAULT 0,
                profanity_count INT DEFAULT 0);

            CREATE TABLE IF NOT EXISTS whitelisted (
                id SERIAL PRIMARY KEY,
                role_id BIGINT
                );
            """)

    async def check_if_exists(self, table, column, _id: int) -> bool:
        check = await self.db.execute(f"""
            SELECT * FROM {table} WHERE {column} = $1
        """, _id)
        return bool(int(check[7:]))

    async def insert_member(self, user_id: discord.Member.id) -> None:
        """Inserts data to the table"""
        conn = await self.db.acquire()
        async with conn.transaction():
            await self.db.execute("""
                INSERT INTO userlogs VALUES ($1)
            """, user_id)
        await self.db.release(conn)

    async def insert_whitelist(self, role_id: int) -> None:
        if not await self.check_if_exists("whitelisted", "role_id", role_id):
            conn = await self.db.acquire()
            async with conn.transaction():
                await self.db.execute("""
                    INSERT INTO whitelisted (role_id) VALUES ($1)
                """, role_id)
            await self.db.release(conn)

    async def update_db(self, column: str, user_id: int) -> None:
        """Updates user logs"""
        conn = await self.db.acquire()
        async with conn.transaction():
            await self.db.execute(f"""
                UPDATE userlogs SET {column} = {column} + 1 WHERE user_id = $1;
            """, user_id)
        await self.db.release(conn)

    async def profanity_counter(self, user_id: str) -> int:
        """Counts profanity words sent by user"""

        count = await self.db.fetchrow("""
            SELECT profanity_count FROM userlogs WHERE user_id = $1;
        """, user_id)
        return dict(count)["profanity_count"]

    async def view_modlogs(self, user_id: int) -> dict[str, str]:
        """View useds mod logs"""

        user_logs = await self.db.fetchrow("""
            SELECT * FROM userlogs WHERE user_id = $1;
        """, user_id)
        return dict(user_logs)

    async def in_whilelist(self, role_id: int) -> bool:
        """Check if role is in whitelist"""

        count = await self.db.fetchrow("""
            SELECT * FROM whitelisted WHERE role_id = $1;
        """, role_id)
        if count:
            return True
        return False

    async def remove_whitelist(self, role_id: int) -> None:
        """Removes role in whitelist database"""

        conn = await self.db.acquire()
        async with conn.transaction():
            await self.db.execute(f"""
                DELETE FROM whitelisted WHERE role_id = $1;
            """, role_id)
        await self.db.release(conn)

