import re
import asyncio
from discord import Member, Role, colour
from discord.ext.commands import Bot, Cog, Context, command
from utils.helper import send_to_modlog, embed_blueprint, parse


class Roles(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        super().__init__()

    async def cog_check(self, ctx: Context):
        return ctx.author.guild_permissions.administrator
    
    @command()
    async def role(self, ctx: Context, member: Member, role: Role):
        """Adds a role to a member"""

        embed = embed_blueprint()
        if member.get_role(role.id):
            embed.description = f"**{member} already has this role!**"
        else:
            embed.description = f"**Added {role} to {member}**"
            await member.add_roles(role)
            await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)
        await ctx.send(embed=embed)

    @command()
    async def temprole(self, ctx: Context, member: Member, role: Role, time: str):
        """Adds a role to a member temporarily"""

        time = await parse(time)
        embed = embed_blueprint()
        if member.get_role(role.id):
            embed.description = f"**{member} already has this role!**"
        else:
            embed.description = f"**Added {role} to {member} for {time[1]}**"
            await member.add_roles(role)
            await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)
        await ctx.send(embed=embed)
        await asyncio.sleep(time[0])
        await member.remove_roles(role)

    @command()
    async def roles(self, ctx: Context):
        """Check all roles in the server"""
        
        embed = embed_blueprint()
        embed.description = f"**Viewing all roles in {ctx.guild.name} - {len(ctx.guild.roles)} roles**\n\n"
        embed.description += "\n".join((role.mention for role in ctx.guild.roles))
        await ctx.send(embed=embed)

    @command()
    async def roleinfo(self, ctx: Context, role: Role):
        """Views info about a role"""

        embed = embed_blueprint()
        embed.description = f"**Role: {role.name}**"
        response_dict = {
            "ID": role.id,
            "Color": role.color,
            "Mention": f"`{role.mention}`",
            "Mentionable": "Yes" if role.mentionable else "No",
            "Hoisted": "Yes" if role.hoist else "No",
            "Position": role.position,
            "Managed": "Yes" if role.managed else "No",
            "Created at": role.created_at.strftime("%B/%d/%Y")
        }
        for info in response_dict.keys():
            embed.add_field(
                name=info,
                value=response_dict[info]
            )
        await ctx.send(embed=embed)

    @command()
    async def rolename(self, ctx: Context, role: Role, *, name: str):
        """Changes the name of a role"""
        
        embed = embed_blueprint()
        past_name = role.name
        await role.edit(name=name)
        embed.description = f"**Changed role name from \"{past_name}\" to \"{name}\"**"
        await ctx.send(embed=embed)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)

    @command()
    async def rolecolor(self, ctx: Context, role: Role, color: str):
        """Changes role color"""
        
        embed = embed_blueprint()
        if len(color) < 7:
            color = f"#{color}" 
        color_check = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color)
        if color_check:
            past_color = role.color
            await role.edit(color=colour.parse_hex_number(color[1:])) # remove the '#' for parsing
            embed.description = f"**Changed role color from {past_color} to {color}**"
        else:
            embed.description = f"**Could not read color hex.**"
        await ctx.send(embed=embed)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)

    @command()
    async def addrole(self, ctx: Context, *, name: str):
        """Creates a role 
        note: color_hex must start with #, leave empty if you don't want to put in a color
        """

        embed = embed_blueprint()
        name = name.split() # Converts it to a list of arguments
        possible_color = name[-1]
        if possible_color.isdigit() and len(possible_color) < 7:
            possible_color = f"#{possible_color}"
        color = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', possible_color)
        if not color:
            color = "000000"
        else:
            if color.string.startswith("#"):
                color = name[-1][1:]
            else:
                color = name[-1]
            name = name[:-1]
        name = " ".join(name)
        perms = ctx.guild.default_role.permissions
        await ctx.guild.create_role(name=name, color=colour.parse_hex_number(color), permissions=perms)
        embed.description = f"**Created role {name} ✅**"
        await ctx.send(embed=embed)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)

    @command()
    async def delrole(self, ctx: Context, role: Role):
        """Deletes a role"""

        embed = embed_blueprint()
        embed.description = f"**Deleted {role.name} ✅**"
        await role.delete()
        await ctx.send(embed=embed)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)



async def setup(bot: Bot):
    await bot.add_cog(Roles(bot))
