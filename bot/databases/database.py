import aiosqlite as aiosql
import discord

class ModerationDB:
    db_path = "bot/databases/mlbbmembers.db"
    def __init__(self):
        pass

    async def create_tables(self) -> None:
        async with aiosql.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS userlogs (
                    user_id INTEGER PRIMARY KEY,
                    mute_count INTEGER DEFAULT 0 NOT NULL,
                    warn_count INTEGER DEFAULT 0 NOT NULL,
                    kick_count INTEGER DEFAULT 0 NOT NULL,
                    ban_count INTEGER DEFAULT 0 NOT NULL,
                    profanity_count INTEGER DEFAULT 0 NOT NULL);
                """)
            await db.execute("""
             CREATE TABLE IF NOT EXISTS whitelisted (
                    role_id INTEGER PRIMARY KEY
                    );""")

    async def check_if_exists(self, table, column, _id: int) -> bool:
        async with aiosql.connect(self.db_path) as db:
            check = await db.execute(f"""
                SELECT * FROM {table} WHERE {column} = ?
            """, (_id,))
            check = await check.fetchall()
            return bool(check)

    async def insert_member(self, user_id: discord.Member.id) -> None:
        """Inserts data to the table"""
        
        async with aiosql.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO userlogs(user_id) VALUES (?);
            """, (user_id,))
            await db.commit()
            return

    async def insert_whitelist(self, role_id: int) -> None:
        async with aiosql.connect(self.db_path) as db:
            await db.execute("""
                    INSERT INTO whitelisted (role_id) VALUES (?);
                """, (role_id,))
            await db.commit()

    async def update_db(self, column: str, user_id: int) -> None:
        """Updates user logs"""

        async with aiosql.connect(self.db_path) as db:
            await db.execute(f"""
                UPDATE userlogs SET {column} = {column} + 1 WHERE user_id = ?;
            """, (user_id,))
            await db.commit()

    async def profanity_counter(self, user_id: str) -> int:
        """Counts profanity words sent by user"""

        async with aiosql.connect(self.db_path) as db:
            count = await db.execute("""
            SELECT profanity_count FROM userlogs WHERE user_id = ?;
        """, (user_id,))
            count = await count.fetchone()
        return count[0]

    async def view_modlogs(self, user_id: int) -> dict[str, str]:
        """View useds mod logs"""

        async with aiosql.connect(self.db_path) as db:
            user_logs = await db.execute("""
                SELECT * FROM userlogs WHERE user_id = ?;
            """, (user_id,))
            rows = await user_logs.fetchone()
            d = {
                "user_id": rows[0],
                "mute_count": rows[1],
                "warn_count": rows[2],
                "kick_count": rows[3],
                "ban_count": rows[4],
                "profanity_count": rows[5]
            }
            return d

    async def in_whilelist(self, role_id: int) -> bool:
        """Check if role is in whitelist"""
        async with aiosql.connect(self.db_path) as db:
            count = await db.execute("""
                SELECT * FROM whitelisted WHERE role_id = ?;
            """, (role_id,))
            count = await count.fetchone()
            if count:
                return True
            return False

    async def remove_whitelist(self, role_id: int) -> None:
        """Removes role in whitelist database"""

        async with aiosql.connect(self.db_path) as db:
            await db.execute(f"""
                DELETE FROM whitelisted WHERE role_id = ?;
            """, (role_id,))
            await db.commit()



