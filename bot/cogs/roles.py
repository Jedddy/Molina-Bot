import discord
import re
from discord.ext import commands
from utils.helper import send_to_modlog
from utils.helper import embed_blueprint


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()
    
    @commands.command()
    async def role(self, ctx: commands.Context, member: discord.Member, role: discord.Role):
        """Adds a role to a member"""

        embed = embed_blueprint(ctx.guild)
        if member.get_role(role.id):
            embed.description = f"**{member} already has this role!**"
        else:
            embed.description = f"**Added {role} to {member}**"
            await member.add_roles(role)
        await ctx.send(embed=embed)

    @commands.command()
    async def roles(self, ctx: commands.Context):
        """Check all roles in the server"""
        
        embed = embed_blueprint(ctx.guild)
        embed.description = f"**Viewing all roles in {ctx.guild.name}**\n\n"
        embed.description += "\n".join((role.mention for role in ctx.guild.roles))
        await ctx.send(embed=embed)

    @commands.command()
    async def roleinfo(self, ctx: commands.Context, role: discord.Role):
        """Views info about a role"""

        embed = embed_blueprint(ctx.guild)
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

    @commands.command()
    async def rolename(self, ctx: commands.Context, role: discord.Role, *, name: str):
        """Changes the name of a role"""
        
        embed = embed_blueprint(ctx.guild)
        past_name = role.name
        await role.edit(name=name)
        embed.description = f"**Changed role name from \"{past_name}\" to \"{name}\"**"
        await ctx.send(embed=embed)

    @commands.command()
    async def rolecolor(self, ctx: commands.Context, role: discord.Role, color: str):
        """Changes role color"""
        
        embed = embed_blueprint(ctx.guild)
        if color.isdigit() and len(color) < 7:
            color = f"#{color}"
        color_check = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color)
        if color_check:
            past_color = role.color
            await role.edit(color=discord.colour.parse_hex_number(color[1:])) # remove the '#' for parsing
            embed.description = f"**Changed role color from {past_color} to {color}**"
        else:
            embed.description = f"**Could not read color hex.**"
        await ctx.send(embed=embed)

    @commands.command()
    async def addrole(self, ctx: commands.Context, *, name: str, color_hex = None):
        """Creates a role 
        note: color_hex must start with #, leave empty if you don't want to put in a color
        """

        embed = embed_blueprint(ctx.guild)
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
        await ctx.guild.create_role(name=name, color=discord.colour.parse_hex_number(color), permissions=perms)
        embed.description = f"**Created role {name} ✅**"
        await ctx.send(embed=embed)

    @commands.command()
    async def delrole(self, ctx: commands.Context, role: discord.Role):
        """Deletes a role"""

        embed = embed_blueprint(ctx.guild)
        if role.is_default:
            embed.description = "**Cannot delete this role!**"
        else:
            embed.description = f"**Deleted {role.name} ✅**"
            await role.delete()
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))