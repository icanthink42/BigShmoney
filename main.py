import os.path
import pickle

import discord

import data
from user import User, Stock

intents = discord.Intents.default()
data.bot = discord.Bot(intents=intents)

data.reload_config()

if not os.path.isdir(data.config["users_save_dir"]):
    os.mkdir(data.config["users_save_dir"])

user_files = os.listdir(data.config["users_save_dir"])
for user_file in user_files:
    with open(data.config["users_save_dir"] + "/" + user_file, "rb") as f:
        loaded_user = pickle.load(f)
        data.users[loaded_user.discord_id] = loaded_user


@data.bot.event
async def on_ready():
    print(f"We have logged in as {data.bot.user}")


@data.bot.slash_command(guild_ids=data.local_config["guilds"], description="Ping the bot")
async def ping(ctx):
    await ctx.respond(f"Pong! ({data.bot.latency * 100}ms)", ephemeral=True)


@data.bot.slash_command(guild_ids=data.local_config["guilds"], description="Start using the bot!")
async def start(ctx):
    if ctx.author.id in data.users:
        await ctx.respond("You have already ran /start", ephemeral=True)
        return
    new_user = User(ctx.author.id, data.config["starting_money"])
    data.users[ctx.author.id] = new_user
    new_user.save()
    await ctx.respond("Created your user! Now buy stocks with /buystock", ephemeral=True)


@data.bot.slash_command(guild_ids=data.local_config["guilds"], description="Buy some stocks")
async def buystock(ctx, symbol: str, amount: int):
    symbol = symbol.upper()
    if ctx.author.id not in data.users:
        await ctx.respond("You must run /start before buying stock!", ephemeral=True)
        return
    u: User = data.users[ctx.author.id]
    stock_v = data.stock_v(symbol)
    if stock_v is None:
        await ctx.respond(f"Stock symbol {symbol} not found!", ephemeral=True)
        return
    if amount < 1:
        await ctx.respond("You must buy at least 1 share!", ephemeral=True)
        return
    if u.money < stock_v * amount:
        await ctx.respond(f"Buying {amount} shares of {symbol} would cost {round(stock_v * amount, 2)}USD and you only have {round(u.money, 2)}USD!", ephemeral=True)
        return
    stock = Stock(symbol, stock_v * amount, amount)
    u.add_stock(stock)
    u.money -= stock_v * amount
    u.save()
    await ctx.respond(f"Bought {amount} shares of {symbol} for {round(stock_v * amount, 2)}USD!", ephemeral=True)


@data.bot.slash_command(guild_ids=data.local_config["guilds"], description="Sell some stocks")
async def sellstock(ctx, symbol: str, amount: int):
    symbol = symbol.upper()
    if ctx.author.id not in data.users:
        await ctx.respond("You must run /start before selling stock!", ephemeral=True)
        return
    u: User = data.users[ctx.author.id]
    stock_v = data.stock_v(symbol)
    if stock_v is None:
        await ctx.respond(f"Stock symbol {symbol} not found!", ephemeral=True)
        return
    if symbol not in u.stocks or u.stocks[symbol].amount == 0:
        await ctx.respond(f"You don't own any {symbol}!", ephemeral=True)
        return
    if amount < 1:
        await ctx.respond("You must sell at least 1 share!", ephemeral=True)
        return
    if u.stocks[symbol].amount < amount:
        await ctx.respond(f"You own {u.stocks[symbol].amount} {symbol} but are trying to sell {amount} {symbol}!", ephemeral=True)
        return
    u.remove_stock(symbol, amount)
    u.money += stock_v * amount
    u.save()
    await ctx.respond(f"Sold {amount} shares of {symbol} for {round(stock_v * amount, 2)}USD!", ephemeral=True)


@data.bot.slash_command(guild_ids=data.local_config["guilds"], description="View all your stocks")
async def stocks(ctx):
    if ctx.author.id not in data.users:
        await ctx.respond("You must run /start before viewing stock!", ephemeral=True)
        return
    u: User = data.users[ctx.author.id]
    if len(u.stocks) < 1:
        await ctx.respond("You don't own any stocks right now!", ephemeral=True)
        return
    embed = discord.Embed(
        title="Stocks",
        description="Information about your stocks and their value.",
        color=discord.Colour.blurple(),
    )
    for symbol in u.stocks:
        stock_v = data.stock_v(symbol)
        stock = u.stocks[symbol]
        v = f"Stock Value: {round(stock_v, 2)}\n"
        v += f"Owned shares: {stock.amount}\n"
        v += f"Owned shares value: {round(stock.amount * stock_v, 2)}USD\n"
        v += f"Change from buying price: {round(stock.amount * stock_v - stock.paid, 2)}USD\n"
        p_change = ((stock.amount * stock_v / stock.paid) - 1) * 100
        v += f"Percentage change: {round(p_change, 2)}%"
        embed.add_field(name=symbol, value=v, inline=False)
    await ctx.respond(embed=embed, ephemeral=True)


@data.bot.slash_command(guild_ids=data.local_config["guilds"], description="View balance")
async def bal(ctx, discord_u: discord.User):
    if discord_u is None:
        discord_u = ctx.author
    if discord_u.id not in data.users:
        await ctx.respond("That user has not ran /start!", ephemeral=True)
        return
    u: User = data.users[discord_u.id]
    embed = discord.Embed(
        title=f"{discord_u.display_name}'s Balance",
        description=f"Information about {discord_u.display_name}'s balance.",
        color=discord.Colour.blurple(),
    )
    stock_value = 0
    for symbol in u.stocks:
        stock_v = data.stock_v(symbol)
        stock = u.stocks[symbol]
        stock_value += stock_v * stock.amount

    embed.add_field(name="Liquid", value=str(u.money), inline=True)
    embed.add_field(name="Stock", value=str(stock_value), inline=True)
    embed.add_field(name="Total", value=str(u.money + stock_value), inline=True)
    await ctx.respond(embed=embed, ephemeral=True)


data.bot.run(data.local_config["token"])
