import aiosqlite as aiosql
import datetime

class ModerationDB:
    db_path = "bot/databases/mlbbmembers.db"
    
    async def create_tables(self) -> None:
        """Create all the tables needed"""

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

            await db.execute("""
                CREATE TABLE IF NOT EXISTS party_channels (
                        channel_id PRIMARY KEY
                        );""")

            await db.execute("""
                CREATE TABLE IF NOT EXISTS rank_roles (
                        role_id INTEGER PRIMARY KEY
                        );""")

            await db.execute("""
                CREATE TABLE IF NOT EXISTS detailed_modlogs (
                    case_no INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    log_type TEXT,
                    reason TEXT,
                    moderator TEXT,
                    date TEXT
                ); """)

    async def moderation_db_check(self, user_id: int) -> bool:
        async with aiosql.connect(self.db_path) as db:
            check = await db.execute(f"""
                SELECT * FROM userlogs WHERE user_id = ?
            """, (user_id,))
            check = await check.fetchall()
            return bool(check)

    async def insert_member(self, user_id: int) -> None:
        """Inserts data to the table"""
        
        async with aiosql.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO userlogs(user_id) VALUES (?);
            """, (user_id,))
            await db.commit()
            return

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
        return count[0] if count else 0

    async def view_modlogs(self, user_id: int) -> dict[str, str]:
        """View useds mod logs"""

        async with aiosql.connect(self.db_path) as db:
            user_logs = await db.execute("""
                SELECT * FROM userlogs WHERE user_id = ?;
            """, (user_id,))
            rows = await user_logs.fetchone()
            if not rows:
                return
            d = {
                "user_id": rows[0],
                "mute_count": rows[1],
                "warn_count": rows[2],
                "kick_count": rows[3],
                "ban_count": rows[4],
                "profanity_count": rows[5]
            }
            return d

    async def insert_whitelist(self, role_id: int) -> None:
        async with aiosql.connect(self.db_path) as db:
            await db.execute("""
                    INSERT INTO whitelisted (role_id) VALUES (?);
                """, (role_id,))
            await db.commit()

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

    async def view_whitelist(self) -> list[int]:
        """View whitelist"""
        
        async with aiosql.connect(self.db_path) as db:
            whitelists = await db.execute(f"""
                SELECT * FROM whitelisted;
            """)
            roles = await whitelists.fetchall()
            return roles

    async def add_party_channel(self, channel: int) -> None:
        """Adds party channel to database"""

        async with aiosql.connect(self.db_path) as db:
            await db.execute(f"""
                INSERT INTO party_channels VALUES (?);
            """, (channel,))
            await db.commit()

    async def add_rank_role(self, role_id: int) -> None:
        """Adds rank role to database"""

        async with aiosql.connect(self.db_path) as db:
            await db.execute(f"""
                INSERT INTO rank_roles VALUES (?);
            """, (role_id,))
            await db.commit()
    
    async def rank_roles_and_party_channels(self) -> tuple[list[tuple[int]], list[tuple[int]]]:
        async with aiosql.connect(self.db_path) as db:
            roles = await db.execute(f"""
                SELECT * FROM rank_roles;
            """)
            channels = await db.execute(f"""
                SELECT * FROM party_channels;
            """)
            roles = await roles.fetchall()
            channels = await channels.fetchall()
            return (roles, channels)

    async def insert_detailed_modlogs(self, user_id: int, log_type: str, reason: str, moderator: str) -> None:
        date = datetime.datetime.now()
        date = date.strftime("%B/%d/%Y")
        async with aiosql.connect(self.db_path) as db:
            await db.execute("""
                INsERT INTO detailed_modlogs (user_id, log_type, reason, moderator, date) VALUES (?, ?, ?, ?, ?)
            """, (user_id, log_type, reason, moderator, date))
            await db.commit()

    async def check_detailed_modlogs(self, user_id: int, offset: int) -> list[tuple]:
        async with aiosql.connect(self.db_path) as db:
            logs = await db.execute_fetchall("""
                SELECT * FROM detailed_modlogs WHERE user_id = ? LIMIT 5 OFFSET ?;
            """, (user_id, offset))
            lenght = await db.execute_fetchall("""
                SELECT * FROM detailed_modlogs WHERE user_id = ?
            """, (user_id,))
            return logs, len(lenght)