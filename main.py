import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import os
import json
from datetime import datetime

# =======================
# BEÁLLÍTÁSOK
# =======================
TOKEN = os.getenv("TOKEN")

API_URL = (
    "https://jizdnirady.pmdp.cz/signalr/connect?transport=serverSentEvents&clientProtocol=2.1&"
    "messageId=d-ADF24C49-B%2C175%7CEo%2C18%7CEp%2C1&clientProtocol=2.1&"
    "connectionToken=IpN05fbwsjNZfLZsFvlK13nn9JPhRGeA%2BwXPgnKVMjod5lRNxLQ%2BdxrHgbVSxUN18mDyvd0sdognlnUXE2CJ%2FQQbjytRLAfqUJZ%2FUPLHGDNphmaq0KbX9OK4RSQAYyh4&"
    "connectionData=%5B%7B"name"%3A"provozhub"%7D%5D&tid=8"
)

intents = discord.Intents.default()
intents.message_content = True  # szükséges, hogy a bot lássa a parancsokat

bot = commands.Bot(command_prefix=".", intents=intents)

# =======================
# SEGÉDFÜGGVÉNYEK
# =======================
def is_villamos(reg):
    try:
        n = int(reg)
        return 1000 <= n <= 1999
    except:
        return False

def is_troli(reg):
    try:
        n = int(reg)
        return 2000 <= n <= 2999
    except:
        return False
    
def is_busz(reg):
    try:
        n = int(reg)
        return 3000 <= n <= 3999
    except:
        return False

def is_24tr(reg):
    try:
        n = int(reg)
        return 2514 <= n <= 2519
    except:
        return False
    
def is_25tr(reg):
    try:
        n = int(reg)
        return 2520 <= n <= 2524
    except:
        return False
    
def is_26tr_III(reg):
    try:
        n = int(reg)
        return (2531 <= n <= 2534) or (2545 <= n <= 2582)
    except:
        return False

def is_26tr_IV(reg):
    try:
        n = int(reg)
        return (2591 <= n <= 2617) or (2622 <= n <= 2626)
    except:
        return False

def is_27tr_III(reg):
    try:
        n = int(reg)
        return (2525 <= n <= 2530) or (2535 <= n <= 2544)
    except:
        return False

def is_27tr_IV(reg):
    try:
        n = int(reg)
        return (2583 <= n <= 2590) or (2601 <= n <= 2604) or (2618 <= n <= 2621)
    except:
        return False
    
def is_urb18_IV(reg):
    try:
        n = int(reg)
        return (3599 == n) or (3605 <= n <= 3625) or (3638 <= n <= 3642) or (3645 <= n <= 3647) or (3652 <= 3657) or (3663 <= n <= 3665)
    except:
        return False
    
def is_sornb12(reg):
    try:
        n = int(reg)
        return (3532 <= n <= 3533) or (3534 == n) or (3538 == n) or (3549 <= n <= 3550) or (3553 <= n <= 3559) or (3567 == n) or (3569 <= n <= 3588) or (3597 == n) or (3600 <= n <= 3604)
    except:
        return False

def is_urb18_III(reg):
    try:
        n = int(reg)
        return (3515 == n) or (3522 <= n <= 3524) or (3531 == n) or (3542 <= n <= 3548) or (3560 <= n <= 3566) or (3589 <= n <= 3593)
    except:
        return False
    
def is_sorns12(reg):
    try:
        n = int(reg)
        return (3626 <= n <= 3637) or (3648 <= n <= 3651) or (3659 <= n <= 3662) or (3669 <= n <= 3675)
    except:
        return False

def is_sorns18(reg):
    try:
        n = int(reg)
        return 3666 <= n <= 3668
    except:
        return False
    
def is_isuzu(reg):
    try:
        n = int(reg)
        return (3643 <= n <= 3644) or (3658 == n)
    except:
        return False
    
def is_rosero(reg):
    try:
        n = int(reg)
        return 3634 <= n <= 3635
    except:
        return False

def is_evo2(reg):
    try:
        n = int(reg)
        return 1369 <= n <= 1384
    except:
        return False
    
def is_40T(reg):
    try:
        n = int(reg)
        return 1385 <= n <= 1406
    except:
        return False
    
def is_49T(reg):
    try:
        n = int(reg)
        return 1122 == n
    except:
        return False
    
def is_kt8(reg):
    try:
        n = int(reg)
        return 1288 <= n <= 1299
    except:
        return False
    
def is_t3(reg):
    try:
        n = int(reg)
        return 1315 <= n <= 1332
    except:
        return False
    
def is_lf(reg):
    try:
        n = int(reg)
        return (1336 <= n <= 1337) or (1354 <= n <= 1355) or (1367 <= n <= 1368)
    except:
        return False
    
def is_lf2(reg):
    try:
        n = int(reg)
        return (1361 <= n <= 1363) or (1366 == n)
    except:
        return False
    
def is_lfr(reg):
    try:
        n = int(reg)
        return (1333 <= n <= 1335) or (1338 <= n <= 1353) or (1356 <= n <= 1360) or (1364 <= n <= 1365)
    except:
        return False

# =======================
# DISCORD BOT INIT
# =======================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)


# =======================
# LOGGER LOOP (opcionális)
# =======================
@tasks.loop(seconds=30)
async def logger_loop():
    vehicles_dict = {}  # VehicleNumber -> adat

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(API_URL, timeout=10) as resp:
                if resp.status != 200:
                    return
                text = await resp.text()
        except:
            return

    # Soronként feldolgozzuk az SSE adatokat
    for line in text.splitlines():
        if line.startswith("data: {"):
            json_part = line[6:]
            try:
                data = json.loads(json_part)
            except:
                continue

            for hub in data.get("M", []):
                for batch in hub.get("A", []):
                    for vehicle in batch:
                        try:
                            vnum = int(vehicle.get("VehicleNumber"))
                        except:
                            continue

                        line_name = str(vehicle.get("Line", {}).get("Name"))
                        last_stop = vehicle.get("LastStopName") or "N/A"
                        next_stop = vehicle.get("NextStopName") or "N/A"
                        delay = vehicle.get("DelayMin") or 0

                        # UTF-8 tisztítás az értelmetlen karakterek ellen
                        last_stop = last_stop.encode("utf-8", errors="replace").decode("utf-8")
                        next_stop = next_stop.encode("utf-8", errors="replace").decode("utf-8")

                        vehicles_dict[vnum] = {
                            "VehicleNumber": vnum,
                            "Line": line_name,
                            "LastStop": last_stop,
                            "NextStop": next_stop,
                            "Delay": delay
                        }
                        
async def fetch_sse():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(API_URL, timeout=15) as resp:
                async for line_bytes in resp.content:
                    line = line_bytes.decode("utf-8", errors="ignore").strip()
                    if line.startswith("data:"):
                        json_part = line[6:]
                        try:
                            data = json.loads(json_part)
                            # Itt dolgozd fel az adatot
                            print(data)
                        except Exception as e:
                            # Hibás JSON sorokat kihagyjuk
                            continue
        except Exception as e:
            print("❌ Hiba az API lekéréskor:", e)

asyncio.run(fetch_sse())        


# # =======================
# # Villamosok
# # =======================
# @bot.command()
# async def pmdpvillamostoday(ctx, date: str = None):
#     day = date or datetime.now().strftime("%Y-%m-%d")
#     veh_dir = "logs/veh"
#     trolis = {}

#     for fname in os.listdir(veh_dir):
#         if not fname.endswith(".txt"):
#             continue
#         reg = fname.replace(".txt", "")
#         if not is_villamos(reg):
#             continue

#         with open(os.path.join(veh_dir, fname), "r", encoding="utf-8") as f:
#             for line in f:
#                 if line.startswith(day):
#                     ts = line.split(" - ")[0]
#                     trip_id = line.split("ID ")[1].split(" ")[0]
#                     line_no = line.split("Vonal ")[1].split(" ")[0]
#                     trolis.setdefault(reg, []).append((ts, line_no, trip_id))

#     if not trolis:
#         return await ctx.send(f"🚫 {day} napon nem közlekedtek villamosok.")

#     out = [f"🚋 Villamosok – forgalomban ({day})"]
#     for reg in sorted(trolis):
#         first = min(trolis[reg], key=lambda x: x[0])
#         last = max(trolis[reg], key=lambda x: x[0])
#         out.append(f"{reg} — {first[0][11:16]} → {last[0][11:16]} (vonal {first[1]})")

#     msg = "\n".join(out)
#     for i in range(0, len(msg), 1900):
#         await ctx.send(msg[i:i+1900])

@bot.command()
async def pmdpvillamos(ctx):
    import ftfy
    import asyncio
    import aiohttp
    import json
    import discord

    active = {}

    async with aiohttp.ClientSession() as session:
        text = None

        # 🔁 retry
        for attempt in range(3):
            try:
                async with session.get(API_URL, timeout=aiohttp.ClientTimeout(total=60)) as r:
                    if r.status != 200:
                        return await ctx.send(f"❌ Hiba: HTTP {r.status}")

                    text = await r.text()
                    break

            except asyncio.TimeoutError:
                if attempt == 2:
                    return await ctx.send("❌ API timeout")
                await asyncio.sleep(1)

            except aiohttp.ClientError as e:
                if attempt == 2:
                    return await ctx.send(f"❌ Hálózati hiba: {e}")
                await asyncio.sleep(1)

            except Exception as e:
                if attempt == 2:
                    return await ctx.send(f"❌ Ismeretlen hiba: {e}")
                await asyncio.sleep(1)

        if not text:
            return await ctx.send("❌ Az API nem adott választ.")

        # 🔴 feldolgozás MÉG a session-en belül
        for line in text.splitlines():
            if not line.startswith("data: {"):
                continue
            try:
                data = json.loads(line[6:])
            except:
                continue

            for hub in data.get("M", []):
                for batch in hub.get("A", []):
                    for vehicle in batch:
                        vnum = vehicle.get("VehicleNumber")
                        if not vnum or not is_villamos(str(vnum)):
                            continue

                        reg_str = str(vnum)

                        # első szám levágása (pl 12514 → 2514 → 514)
                        real_reg = reg_str[1:]

                        # típus
                        if is_evo2(reg_str):
                            vehicle_type = "EVO 2"
                        elif is_40T(reg_str):
                            vehicle_type = "Škoda 40T ForCity Smart"
                        elif is_49T(reg_str):
                            vehicle_type = "Škoda 49T ForCity Classic"
                        elif is_kt8(reg_str):
                            vehicle_type = "Tatra KT8D5R.N2P"
                        elif is_t3(reg_str):
                            vehicle_type = "Tatra T3R.PLF"
                        elif is_lf(reg_str):
                            vehicle_type = "Vario LF+"
                        elif is_lf2(reg_str):
                            vehicle_type = "Vario LF2/2 IN"
                        elif is_lfr(reg_str):
                            vehicle_type = "Vario LFR.S"
                        else:
                            vehicle_type = "Ismeretlen villamos"

                        line_info = vehicle.get("Line", {})
                        line_name = str(line_info.get("Name", "Ismeretlen"))
                        internal_number = str(line_info.get("Number", "Ismeretlen"))

                        dest_name = ftfy.fix_text(str(vehicle.get("DestinationName") or "Ismeretlen"))
                        next_stop = ftfy.fix_text(str(vehicle.get("NextStopName") or "Ismeretlen"))
                        delay = vehicle.get("DelayMin", 0)

                        active[real_reg] = {
                            "line": line_name,
                            "internal": internal_number,
                            "dest": dest_name,
                            "next": next_stop,
                            "delay": delay,
                            "type": vehicle_type
                        }

    if not active:
        return await ctx.send("🚫 Nincs aktív villamos.")

    # 📦 embedek (limit kezeléssel)
    embeds = []
    embed = discord.Embed(title="🚋 Aktív villamosok", color=0xffff00)

    char_count = 0
    FIELD_LIMIT = 25
    CHAR_LIMIT = 5500  # biztonságos limit (Discord ~6000)

    for reg, info in sorted(active.items(), key=lambda x: int(x[0])):
        value_text = (
            f"Vonal: {info['line']}\n"
            f"Cél: {info['dest']}\n"
            f"Következő megálló: {info['next']}\n"
            f"Késés: {info['delay']} perc\n"
            f"Típus: {info['type']}"
        )

        # ha túlcsordul → új embed
        if len(embed.fields) >= FIELD_LIMIT or char_count + len(value_text) > CHAR_LIMIT:
            embeds.append(embed)
            embed = discord.Embed(title="🚋 Aktív villamosok (folytatás)", color=0xffff00)
            char_count = 0

        embed.add_field(name=str(reg), value=value_text, inline=False)
        char_count += len(value_text)

    if embed.fields:
        embeds.append(embed)

    for e in embeds:
        await ctx.send(embed=e)
        
@bot.command()
async def pmdptatra(ctx):
    import ftfy
    import asyncio
    import aiohttp
    import json
    import discord

    active = {}

    async with aiohttp.ClientSession() as session:
        text = None

        # 🔁 retry
        for attempt in range(3):
            try:
                async with session.get(API_URL, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status != 200:
                        return await ctx.send(f"❌ Hiba: HTTP {r.status}")

                    text = await r.text()
                    break

            except asyncio.TimeoutError:
                if attempt == 2:
                    return await ctx.send("❌ API timeout")
                await asyncio.sleep(1)

            except aiohttp.ClientError as e:
                if attempt == 2:
                    return await ctx.send(f"❌ Hálózati hiba: {e}")
                await asyncio.sleep(1)

            except Exception as e:
                if attempt == 2:
                    return await ctx.send(f"❌ Ismeretlen hiba: {e}")
                await asyncio.sleep(1)

        if not text:
            return await ctx.send("❌ Az API nem adott választ.")

        # 🔴 feldolgozás MÉG a session-en belül
        for line in text.splitlines():
            if not line.startswith("data: {"):
                continue
            try:
                data = json.loads(line[6:])
            except:
                continue

            for hub in data.get("M", []):
                for batch in hub.get("A", []):
                    for vehicle in batch:
                        vnum = vehicle.get("VehicleNumber")
                        if not vnum or not is_villamos(str(vnum)):
                            continue

                        reg_str = str(vnum)

                        # csak Tatra típusok
                        if not (is_t3(reg_str) or is_kt8(reg_str)):
                            continue

                        # első szám levágása (pl 12514 → 2514 → 514)
                        real_reg = reg_str[1:]

                        # típus
                        if is_kt8(reg_str):
                            vehicle_type = "Tatra KT8D5R.N2P"
                        elif is_t3(reg_str):
                            vehicle_type = "Tatra T3R.PLF"

                        line_info = vehicle.get("Line", {})
                        line_name = str(line_info.get("Name", "Ismeretlen"))
                        internal_number = str(line_info.get("Number", "Ismeretlen"))

                        dest_name = ftfy.fix_text(str(vehicle.get("DestinationName") or "Ismeretlen"))
                        next_stop = ftfy.fix_text(str(vehicle.get("NextStopName") or "Ismeretlen"))
                        delay = vehicle.get("DelayMin", 0)

                        active[real_reg] = {
                            "line": line_name,
                            "internal": internal_number,
                            "dest": dest_name,
                            "next": next_stop,
                            "delay": delay,
                            "type": vehicle_type
                        }

    if not active:
        return await ctx.send("🚫 Nincs aktív Tatra villamos.")

    # 📦 embedek (limit kezeléssel)
    embeds = []
    embed = discord.Embed(title="🚋 Aktív Tatra villamosok", color=0xffff00)

    char_count = 0
    FIELD_LIMIT = 25
    CHAR_LIMIT = 5500  # biztonságos limit (Discord ~6000)

    for reg, info in sorted(active.items(), key=lambda x: int(x[0])):
        value_text = (
            f"Vonal: {info['line']}\n"
            f"Cél: {info['dest']}\n"
            f"Következő megálló: {info['next']}\n"
            f"Késés: {info['delay']} perc\n"
            f"Típus: {info['type']}"
        )

        # ha túlcsordul → új embed
        if len(embed.fields) >= FIELD_LIMIT or char_count + len(value_text) > CHAR_LIMIT:
            embeds.append(embed)
            embed = discord.Embed(title="🚋 Aktív Tatra villamosok (folytatás)", color=0xffff00)
            char_count = 0

        embed.add_field(name=str(reg), value=value_text, inline=False)
        char_count += len(value_text)

    if embed.fields:
        embeds.append(embed)

    for e in embeds:
        await ctx.send(embed=e)

# =======================
# Trolibuszok
# =======================
    
# @bot.command()
# async def pmdptrolitoday(ctx, date: str = None):
#     day = date or datetime.now().strftime("%Y-%m-%d")
#     veh_dir = "logs/veh"
#     trolis = {}

#     for fname in os.listdir(veh_dir):
#         if not fname.endswith(".txt"):
#             continue
#         reg = fname.replace(".txt", "")
#         if not is_troli(reg):
#             continue

#         with open(os.path.join(veh_dir, fname), "r", encoding="utf-8") as f:
#             for line in f:
#                 if line.startswith(day):
#                     ts = line.split(" - ")[0]
#                     trip_id = line.split("ID ")[1].split(" ")[0]
#                     line_no = line.split("Vonal ")[1].split(" ")[0]
#                     trolis.setdefault(reg, []).append((ts, line_no, trip_id))

#     if not trolis:
#         return await ctx.send(f"🚫 {day} napon nem közlekedtek trolibuszok.")

#     out = [f"🚎 Trolibuszok – forgalomban ({day})"]
#     for reg in sorted(trolis):
#         first = min(trolis[reg], key=lambda x: x[0])
#         last = max(trolis[reg], key=lambda x: x[0])
#         out.append(f"{reg} — {first[0][11:16]} → {last[0][11:16]} (vonal {first[1]})")

#     msg = "\n".join(out)
#     for i in range(0, len(msg), 1900):
#         await ctx.send(msg[i:i+1900])

@bot.command()
async def pmdptroli(ctx):
    import ftfy
    import asyncio
    import aiohttp
    import json

    active = {}

    async with aiohttp.ClientSession() as session:
        text = None

        # 🔁 retry
        for attempt in range(3):
            try:
                async with session.get(API_URL, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status != 200:
                        return await ctx.send(f"❌ Hiba az API lekéréskor: HTTP {r.status}")

                    text = await r.text()
                    break

            except asyncio.TimeoutError:
                if attempt == 2:
                    return await ctx.send("❌ Hiba: API timeout")
                await asyncio.sleep(1)

            except aiohttp.ClientError as e:
                if attempt == 2:
                    return await ctx.send(f"❌ Hálózati hiba: {e}")
                await asyncio.sleep(1)

            except Exception as e:
                if attempt == 2:
                    return await ctx.send(f"❌ Ismeretlen hiba: {e}")
                await asyncio.sleep(1)

        if not text:
            return await ctx.send("❌ Az API nem adott választ.")

        # 🔴 feldolgozás itt marad
        for line in text.splitlines():
            if not line.startswith("data: {"):
                continue
            try:
                data = json.loads(line[6:])
            except Exception:
                continue

            for hub in data.get("M", []):
                for batch in hub.get("A", []):
                    for vehicle in batch:
                        vnum = vehicle.get("VehicleNumber")
                        if not vnum or not is_troli(str(vnum)):
                            continue

                        reg_str = str(vnum)
                        real_reg = reg_str[1:]  # 🔥 első karakter levágása

                        # Típus meghatározása
                        if is_24tr(reg_str):
                            vehicle_type = "Irisbus Citelis Škoda 24Tr"
                        elif is_25tr(reg_str):
                            vehicle_type = "Irisbus Citelis Škoda 25Tr"
                        elif is_26tr_III(reg_str):
                            vehicle_type = "Solars-Škoda 26Tr gen. III"
                        elif is_26tr_IV(reg_str):
                            vehicle_type = "Solars-Škoda 26Tr gen. IV"
                        elif is_27tr_III(reg_str):
                            vehicle_type = "Solars-Škoda 27Tr gen. III"
                        elif is_27tr_IV(reg_str):
                            vehicle_type = "Solars-Škoda 27Tr gen. IV"
                        else:
                            vehicle_type = "Ismeretlen trolibusz"

                        line_info = vehicle.get("Line", {})
                        line_name = str(line_info.get("Name", "Ismeretlen"))
                        internal_number = str(line_info.get("Number", "Ismeretlen"))
                        start_name = ftfy.fix_text(str(vehicle.get("StartName") or "Ismeretlen"))
                        dest_name = ftfy.fix_text(str(vehicle.get("DestinationName") or "Ismeretlen"))
                        last_stop = ftfy.fix_text(str(vehicle.get("LastStopName") or "Ismeretlen"))
                        next_stop = ftfy.fix_text(str(vehicle.get("NextStopName") or "Ismeretlen"))
                        delay = vehicle.get("DelayMin", 0)

                        active[real_reg] = {
                            "line": line_name,
                            "internal": internal_number,
                            "start": start_name,
                            "dest": dest_name,
                            "last": last_stop,
                            "next": next_stop,
                            "delay": delay,
                            "type": vehicle_type
                        }

    if not active:
        return await ctx.send("🚫 Nincs aktív trolibusz a megadott típusokból.")

    # ⬇️ EMBED RÉSZHEZ NEM NYÚLTAM
    embeds = []
    embed = discord.Embed(title="🚎 Aktív trolibuszok", color=0x006400)
    field_count = 0
    MAX_FIELDS = 20

    for reg, info in sorted(active.items(), key=lambda x: int(x[0])):
        value_text = (
            f"Vonal: {info['line']}\n"
            f"Cél: {info['dest']}\n"
            f"Következő megálló: {info['next']}\n"
            f"Késés: {info['delay']} perc\n"
            f"Típus: {info['type']}"
        )
        embed.add_field(name=str(reg), value=value_text, inline=False)
        field_count += 1

        if field_count >= MAX_FIELDS:
            embeds.append(embed)
            embed = discord.Embed(title="🚎 Aktív trolibuszok (folytatás)", color=0x006400)
            field_count = 0

    if embed.fields:
        embeds.append(embed)

    for e in embeds:
        await ctx.send(embed=e)
        
@bot.command()
async def pmdpirisbus(ctx):
    import ftfy
    import asyncio
    import aiohttp
    import json
    import discord

    active = {}

    async with aiohttp.ClientSession() as session:
        text = None

        # 🔁 retry
        for attempt in range(3):
            try:
                async with session.get(API_URL, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status != 200:
                        return await ctx.send(f"❌ Hiba az API lekéréskor: HTTP {r.status}")

                    text = await r.text()
                    break

            except asyncio.TimeoutError:
                if attempt == 2:
                    return await ctx.send("❌ API timeout")
                await asyncio.sleep(1)

            except aiohttp.ClientError as e:
                if attempt == 2:
                    return await ctx.send(f"❌ Hálózati hiba: {e}")
                await asyncio.sleep(1)

            except Exception as e:
                if attempt == 2:
                    return await ctx.send(f"❌ Ismeretlen hiba: {e}")
                await asyncio.sleep(1)

        if not text:
            return await ctx.send("❌ Az API nem adott választ.")

        # 🔴 feldolgozás
        for line in text.splitlines():
            if not line.startswith("data: {"):
                continue
            try:
                data = json.loads(line[6:])
            except Exception:
                continue

            for hub in data.get("M", []):
                for batch in hub.get("A", []):
                    for vehicle in batch:
                        vnum = vehicle.get("VehicleNumber")
                        if not vnum or not is_troli(str(vnum)):
                            continue

                        reg_str = str(vnum)

                        # csak Irisbus trolik
                        if not (is_24tr(reg_str) or is_25tr(reg_str)):
                            continue

                        real_reg = reg_str[1:]  # első karakter levágása

                        # típus
                        if is_24tr(reg_str):
                            vehicle_type = "Irisbus Citelis Škoda 24Tr"
                        elif is_25tr(reg_str):
                            vehicle_type = "Irisbus Citelis Škoda 25Tr"

                        line_info = vehicle.get("Line", {})
                        line_name = str(line_info.get("Name", "Ismeretlen"))
                        internal_number = str(line_info.get("Number", "Ismeretlen"))
                        start_name = ftfy.fix_text(str(vehicle.get("StartName") or "Ismeretlen"))
                        dest_name = ftfy.fix_text(str(vehicle.get("DestinationName") or "Ismeretlen"))
                        last_stop = ftfy.fix_text(str(vehicle.get("LastStopName") or "Ismeretlen"))
                        next_stop = ftfy.fix_text(str(vehicle.get("NextStopName") or "Ismeretlen"))
                        delay = vehicle.get("DelayMin", 0)

                        active[real_reg] = {
                            "line": line_name,
                            "internal": internal_number,
                            "start": start_name,
                            "dest": dest_name,
                            "last": last_stop,
                            "next": next_stop,
                            "delay": delay,
                            "type": vehicle_type
                        }

    if not active:
        return await ctx.send("🚫 Nincs aktív Irisbus trolibusz.")

    # ⬇️ EMBED RÉSZHEZ NEM NYÚLTAM
    embeds = []
    embed = discord.Embed(title="🚎 Aktív Irisbus trolibuszok", color=0x006400)
    field_count = 0
    MAX_FIELDS = 20

    for reg, info in sorted(active.items(), key=lambda x: int(x[0])):
        value_text = (
            f"Vonal: {info['line']}\n"
            f"Cél: {info['dest']}\n"
            f"Következő megálló: {info['next']}\n"
            f"Késés: {info['delay']} perc\n"
            f"Típus: {info['type']}"
        )
        embed.add_field(name=str(reg), value=value_text, inline=False)
        field_count += 1

        if field_count >= MAX_FIELDS:
            embeds.append(embed)
            embed = discord.Embed(title="🚎 Aktív Irisbus trolibuszok (folytatás)", color=0x006400)
            field_count = 0

    if embed.fields:
        embeds.append(embed)

    for e in embeds:
        await ctx.send(embed=e)

# =======================
# Buszok
# =======================
# @bot.command()
# async def pmdpbusztoday(ctx, date: str = None):
#     import os
#     from datetime import datetime

#     day = date or datetime.now().strftime("%Y-%m-%d")
#     veh_dir = "logs/veh"
#     trolis = {}

#     # Ha nincs a mappa, létrehozza
#     os.makedirs(veh_dir, exist_ok=True)

#     # ha nincs fájl benne → üres lesz a lista
#     for fname in os.listdir(veh_dir):
#         if not fname.endswith(".txt"):
#             continue

#         reg = fname.replace(".txt", "")
#         if not is_busz(reg):
#             continue

#         with open(os.path.join(veh_dir, fname), "r", encoding="utf-8") as f:
#             for line in f:
#                 if line.startswith(day):
#                     ts = line.split(" - ")[0]
#                     trip_id = line.split("ID ")[1].split(" ")[0]
#                     line_no = line.split("Vonal ")[1].split(" ")[0]
#                     trolis.setdefault(reg, []).append((ts, line_no, trip_id))

#     if not trolis:
#         return await ctx.send(f"🚫 {day} napon nem közlekedtek buszok, vagy nincs még naplófájl a logs/veh mappában.")

#     out = [f"🚌 Buszok – forgalomban ({day})"]
#     for reg in sorted(trolis):
#         first = min(trolis[reg], key=lambda x: x[0])
#         last = max(trolis[reg], key=lambda x: x[0])
#         out.append(f"{reg} — {first[0][11:16]} → {last[0][11:16]} (vonal {first[1]})")

#     msg = "\n".join(out)
#     for i in range(0, len(msg), 1900):
#         await ctx.send(msg[i:i+1900])

@bot.command()
async def pmdpbusz(ctx):
    import ftfy
    import asyncio
    import aiohttp
    import json

    active = {}

    async with aiohttp.ClientSession() as session:
        text = None

        # 🔁 retry
        for attempt in range(3):
            try:
                async with session.get(API_URL, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status != 200:
                        return await ctx.send(f"❌ Hiba az API lekéréskor: HTTP {r.status}")

                    text = await r.text()
                    break

            except asyncio.TimeoutError:
                if attempt == 2:
                    return await ctx.send("❌ Hiba: API timeout")
                await asyncio.sleep(1)

            except aiohttp.ClientError as e:
                if attempt == 2:
                    return await ctx.send(f"❌ Hálózati hiba: {e}")
                await asyncio.sleep(1)

            except Exception as e:
                if attempt == 2:
                    return await ctx.send(f"❌ Ismeretlen hiba: {e}")
                await asyncio.sleep(1)

        if not text:
            return await ctx.send("❌ Az API nem adott választ.")

        # 🔴 feldolgozás itt
        for line in text.splitlines():
            if not line.startswith("data: {"):
                continue
            try:
                data = json.loads(line[6:])
            except Exception:
                continue

            for hub in data.get("M", []):
                for batch in hub.get("A", []):
                    for vehicle in batch:
                        vnum = vehicle.get("VehicleNumber")
                        if not vnum or not is_busz(str(vnum)):
                            continue

                        reg_str = str(vnum)
                        real_reg = reg_str[1:]  # 🔥 első számjegy levágása

                        # Típus meghatározása
                        if is_urb18_III(reg_str):
                            vehicle_type = "Solaris Urbino 18 gen. III"
                        elif is_urb18_IV(reg_str):
                            vehicle_type = "Solaris Urbino 18 gen. IV"
                        elif is_sornb12(reg_str):
                            vehicle_type = "SOR NB 12"
                        elif is_sorns12(reg_str):
                            vehicle_type = "SOR NS 12"
                        elif is_sorns18(reg_str):
                            vehicle_type = "SOR NS 18"
                        elif is_isuzu(reg_str):
                            vehicle_type = "Anadolu Isuzu Novociti Life Class I"
                        elif is_rosero(reg_str):
                            vehicle_type = "Rošero-P First FCLLI"
                        else:
                            vehicle_type = "Ismeretlen busz"

                        line_info = vehicle.get("Line", {})
                        line_name = str(line_info.get("Name", "Ismeretlen"))
                        internal_number = str(line_info.get("Number", "Ismeretlen"))
                        start_name = ftfy.fix_text(str(vehicle.get("StartName") or "Ismeretlen"))
                        dest_name = ftfy.fix_text(str(vehicle.get("DestinationName") or "Ismeretlen"))
                        last_stop = ftfy.fix_text(str(vehicle.get("LastStopName") or "Ismeretlen"))
                        next_stop = ftfy.fix_text(str(vehicle.get("NextStopName") or "Ismeretlen"))
                        delay = vehicle.get("DelayMin", 0)

                        active[real_reg] = {
                            "line": line_name,
                            "internal": internal_number,
                            "start": start_name,
                            "dest": dest_name,
                            "last": last_stop,
                            "next": next_stop,
                            "delay": delay,
                            "type": vehicle_type
                        }

    if not active:
        return await ctx.send("🚫 Nincs aktív trolibusz a megadott típusokból.")

    # ⬇️ EMBED RÉSZHEZ NEM NYÚLTAM
    embeds = []
    embed = discord.Embed(title="🚌 Aktív buszok", color=0xff0000)
    field_count = 0
    MAX_FIELDS = 20

    for reg, info in sorted(active.items(), key=lambda x: int(x[0])):
        value_text = (
            f"Vonal: {info['line']}\n"
            f"Cél: {info['dest']}\n"
            f"Következő megálló: {info['next']}\n"
            f"Késés: {info['delay']} perc\n"
            f"Típus: {info['type']}"
        )
        embed.add_field(name=str(reg), value=value_text, inline=False)
        field_count += 1

        if field_count >= MAX_FIELDS:
            embeds.append(embed)
            embed = discord.Embed(title="🚌 Aktív buszok (folytatás)", color=0xff0000)
            field_count = 0

    if embed.fields:
        embeds.append(embed)

    for e in embeds:
        await ctx.send(embed=e)
        
        
@bot.command()
async def vehhist(ctx, vehicle: str, date: str = None):
    import os
    from datetime import datetime

    # Segédfüggvény a dátum feloldásához
    def resolve_date(date_str):
        if not date_str:
            return datetime.now()
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

    day = resolve_date(date)
    if day is None:
        return await ctx.send("❌ Hibás dátumformátum. Használd így: `YYYY-MM-DD`")

    day_str = day.strftime("%Y-%m-%d")
    veh_dir = "logs/veh"
    os.makedirs(veh_dir, exist_ok=True)
    veh_file = os.path.join(veh_dir, f"{vehicle}.txt")

    if not os.path.exists(veh_file):
        return await ctx.send("❌ Nincs ilyen jármű a naplóban, vagy még nem készült naplófájl.")

    entries = []
    with open(veh_file, "r", encoding="utf-8") as f:
        for l in f:
            if not l.startswith(day_str):
                continue
            try:
                ts, rest = l.strip().split(" - ", 1)
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                trip_id = rest.split("ID ")[1].split(" ")[0]
                line = rest.split("Vonal ")[1].split(" ")[0]
                dest = rest.split(" - ")[-1]
                entries.append((dt, line, trip_id, dest))
            except Exception:
                continue

    if not entries:
        return await ctx.send(f"❌ {vehicle} nem közlekedett ezen a napon ({day_str}).")

    entries.sort(key=lambda x: x[0])

    runs = []
    current = None

    for dt, line, trip_id, dest in entries:
        if not current or trip_id != current["trip_id"] or line != current["line"]:
            if current:
                runs.append(current)
            current = {
                "line": line,
                "trip_id": trip_id,
                "start": dt,
                "end": dt,
                "dest": dest
            }
        else:
            current["end"] = dt

    if current:
        runs.append(current)

    lines = [f"🚎 {vehicle} – vehhist ({day_str})"]
    for r in runs:
        lines.append(f"{r['start'].strftime('%H:%M')} – {r['line']} / {r['trip_id']} – {r['dest']}")

    msg = "\n".join(lines)
    for i in range(0, len(msg), 1900):
        await ctx.send(msg[i:i + 1900])

# =======================
# BOT INDÍTÁS
# =======================
@bot.event
async def on_ready():
    print(f"Bot csatlakozva: {bot.user}")
    logger_loop.start()  # ha szeretnéd logolni is folyamatosan

bot.run(TOKEN)
